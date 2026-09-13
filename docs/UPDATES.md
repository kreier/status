# Container Update Mechanism & Setup Guide

This guide explains how update checking and automatic/on-demand container updates work on Linux hosts (e.g. Raspberry Pi 4, Rockchip RK3229 TV boxes, or x86 servers), along with the security implications of each approach.

---

## 1. How It Works

### Version Checking (`[Check]` Button & API)
When you click **`[Check]`** or when `/status/api/check` is queried:
1. The status service inspects its current running version (e.g. `v0.1.0`).
2. It queries the GitHub Releases API for the configured repository (`CHECK_REPO=kreier/status` by default).
3. It parses semantic versions and compares them.
4. If a newer release is published on GitHub / GHCR:
   - `Updates available: YES` is displayed.
   - The UI displays the latest release tag (e.g. `v0.1.1`).
   - If up to date, it displays `Updates available: NO`.

---

## 2. Security Comparison of Update Methods

| Method | Where Update Runs | Container Privileges | Security Level | Best Used For |
| :--- | :--- | :--- | :--- | :--- |
| **Method B: Decoupled Host Trigger** | On the Host via `systemd.path` / inotify | **None** (zero host or Docker access) | 🟢 **High** | Safe on-demand updates from the web UI |
| **Method C: Scheduled Host Cron / Timer** | On the Host via scheduled timer | **None** (container is purely a monitor) | 🟢 **Highest** | Unattended, scheduled maintenance |
| **Method A: Watchtower** | Inside an auxiliary container via Docker socket | High (`/var/run/docker.sock` on updater) | 🟡 **Medium** | Environments accepting Docker socket mounts |

---

## 3. Method B: Decoupled Host Trigger (Recommended for UI Updates)

### Why this is the safest on-demand approach
The `status` container **never** has access to the Docker socket (`/var/run/docker.sock`) or host shell. 
Instead:
1. When you click **`[Update]`** in the UI, the container touches a trigger file: `/host/trigger/update`.
2. A lightweight native Linux **systemd path unit** on the host detects the file instantly via kernel `inotify` (zero CPU overhead).
3. Systemd runs `docker compose pull && docker compose up -d` on the host as a standard system service.
4. Systemd cleans up the trigger file once complete.

Even if an attacker completely compromises the web application, they can only create an empty file in that folder — they cannot escape the container or run arbitrary commands on your host.

---

### Recommended Setup: Method B (Decoupled Host Trigger)

We strongly recommend installing your status container in `/srv/status` (or `/src/status`), as standard server directories avoid user-specific path ambiguities and permission issues when `systemd` runs as `root`.

#### Overview of the Architecture

```
┌──────────────────────────────────────┐
│       Container (unprivileged)       │
│                                      │
│  User clicks [Update]                │
│       │                              │
│       ▼                              │
│  Writes /host/trigger/update         │
└──────────────────┬───────────────────┘
                   │ Mounted volume (- ./trigger:/host/trigger:rw)
                   ▼
┌──────────────────────────────────────┐
│           Host Filesystem            │
│                                      │
│  1. /srv/status/trigger/update       │
│       │ (Detected by inotify)        │
│       ▼                              │
│  2. status-updater.path              │
│       │ (Triggers)                   │
│       ▼                              │
│  3. status-updater.service           │
│       │ (Executes as root)           │
│       ▼                              │
│  4. /usr/local/bin/status-updater.sh │
│       │                              │
│       ├─► rm -f trigger/update       │
│       ├─► cd /srv/status             │
│       ├─► docker compose pull        │
│       └─► docker compose up -d       │
└──────────────────────────────────────┘
```

#### Step 1: Set up the recommended directory `/srv/status`

```bash
# Create the recommended directory structure
sudo mkdir -p /srv/status/trigger
sudo chmod 777 /srv/status/trigger
cd /srv/status
```

#### Step 2: Configure `docker-compose.yml`
Save `docker-compose.yml` in `/srv/status/`:

```yaml
services:
  status:
    image: ghcr.io/kreier/status:latest
    container_name: status
    restart: unless-stopped
    ports:
      - "80:8000"
    volumes:
      - /etc/os-release:/host/etc/os-release:ro
      - /etc/hostname:/host/etc/hostname:ro
      - /proc:/host/proc:ro
      - /var/lib/tuptime:/host/var/lib/tuptime:ro
      - ./trigger:/host/trigger:rw
    environment:
      - MACHINE_NAME=RK3229 # Or PI4
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.status.rule=(Host(`rk3229.hv.io.vn`) || Host(`rk3229`) || Host(`localhost`)) && PathPrefix(`/status`)"
      - "traefik.http.routers.status.entrypoints=web,websecure"
      - "traefik.http.routers.status.tls=true"
      - "traefik.http.services.status.loadbalancer.server.port=8000"
```

#### Step 3: Create `/usr/local/bin/status-updater.sh`
This script executes the update safely on the host when triggered:

```bash
sudo tee /usr/local/bin/status-updater.sh > /dev/null << 'EOF'
#!/bin/bash
set -e

# Target directory containing docker-compose.yml:
STATUS_DIR="/srv/status"
TRIGGER_FILE="$STATUS_DIR/trigger/update"

echo "[$(date)] Update triggered by status container."
rm -f "$TRIGGER_FILE"

if [ -d "$STATUS_DIR" ]; then
    cd "$STATUS_DIR"
    /usr/bin/docker compose pull
    /usr/bin/docker compose up -d --force-recreate
    echo "v0.1.0" > "$STATUS_DIR/trigger/updater_version"
    echo "[$(date)] Update complete."
else
    echo "ERROR: Status directory $STATUS_DIR not found!"
    exit 1
fi
EOF

sudo chmod +x /usr/local/bin/status-updater.sh
```

#### Step 4: Create `/etc/systemd/system/status-updater.service`
Defines the `systemd` one-shot service executing the updater script:

```bash
sudo tee /etc/systemd/system/status-updater.service > /dev/null << EOF
[Unit]
Description=Update Status Container
After=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/status-updater.sh

[Install]
WantedBy=multi-user.target
EOF
```

#### Step 5: Create `/etc/systemd/system/status-updater.path`
Monitors the trigger file for write events using Linux `inotify`:

```bash
sudo tee /etc/systemd/system/status-updater.path > /dev/null << EOF
[Unit]
Description=Monitor Status Trigger File

[Path]
PathModified=/srv/status/trigger/update
Unit=status-updater.service

[Install]
WantedBy=multi-user.target
EOF
```

#### Step 6: Enable and start the monitor
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now status-updater.path
```

Verify the monitor status:
```bash
sudo systemctl status status-updater.path
```
It should show: `Active: active (waiting)`.

#### Step 7: Troubleshooting and verification
- **Trigger an update manually to test:**
  ```bash
  sudo systemctl start status-updater.service
  ```
- **Inspect update logs:**
  ```bash
  journalctl -u status-updater.service -n 30 --no-pager
  ```

---

## 4. Method C: Automated Scheduled Updates (Cron / Timer)

If you prefer completely autonomous updates on a fixed schedule (e.g. every Sunday at 4:00 AM) without needing to click any buttons:

### Setup via Crontab:
Edit the root crontab on the host:
```bash
sudo crontab -e
```
Add:
```bash
0 4 * * 0 cd /srv/status && /usr/bin/docker compose pull && /usr/bin/docker compose up -d --remove-orphans
```

### Setup via Systemd Timer (Alternative to cron):
Create `/etc/systemd/system/status-weekly-update.timer`:
```ini
[Unit]
Description=Weekly Status Container Update

[Timer]
OnCalendar=Sun *-*-* 04:00:00
Persistent=true

[Install]
WantedBy=timers.target
```
And enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now status-weekly-update.timer
```

---

## 5. Method A: Watchtower (Container-based updater)

Watchtower runs as an auxiliary container connected to `/var/run/docker.sock`.

### Setup in `docker-compose.yml`:
```yaml
services:
  status:
    image: ghcr.io/kreier/status:latest
    container_name: status
    restart: unless-stopped
    volumes:
      - /etc/os-release:/host/etc/os-release:ro
      - /etc/hostname:/host/etc/hostname:ro
      - /proc:/host/proc:ro
    environment:
      - WATCHTOWER_URL=http://updater:8080/v1/update
      - WATCHTOWER_TOKEN=my-secret-token
    labels:
      - "com.centurylinklabs.watchtower.enable=true"

  updater:
    image: containrrr/watchtower
    container_name: status-updater
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_LABEL_ENABLE=true
      - WATCHTOWER_HTTP_API_UPDATE=true
      - WATCHTOWER_HTTP_API_TOKEN=my-secret-token
      - WATCHTOWER_POLL_INTERVAL=86400
    labels:
      - "traefik.enable=false"
```

> [!WARNING]
> Only use Method A if you accept mounting `/var/run/docker.sock`. Ensure `WATCHTOWER_LABEL_ENABLE=true` is set so Watchtower cannot accidentally restart other services on your machine (like Pi-hole or Traefik).
