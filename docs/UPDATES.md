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

### Setup Instructions for Method B on Your Machine (Pi 4 / RK3229)

#### Step 1: Create the trigger folder
In your status directory on the machine (e.g. `/srv/status` or `~/status`):
```bash
mkdir -p /srv/status/trigger
chmod 777 /srv/status/trigger
```

#### Step 2: Add the trigger volume mount to `docker-compose.yml`
Ensure `./trigger:/host/trigger:rw` is mounted into the `status` container:

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
      - ./trigger:/host/trigger:rw
    # ... your ports or traefik labels ...
```

#### Step 3: Create the systemd service on the host
Create `/etc/systemd/system/status-updater.service`:
```bash
sudo nano /etc/systemd/system/status-updater.service
```
Paste:
```ini
[Unit]
Description=Host Status Container Updater
After=docker.service

[Service]
Type=oneshot
WorkingDirectory=/srv/status
ExecStartPre=/bin/sh -c 'echo "v0.1.0" > /srv/status/trigger/updater_version'
ExecStartPre=/bin/sleep 2
ExecStart=/usr/bin/docker compose pull
ExecStart=/usr/bin/docker compose up -d --remove-orphans
ExecStopPost=/bin/rm -f /srv/status/trigger/update
User=root
```
*(Note: If your status directory is `~/status`, adjust `WorkingDirectory` and `trigger` path accordingly).*

#### Step 4: Create the systemd path monitor on the host
Create `/etc/systemd/system/status-updater.path`:
```bash
sudo nano /etc/systemd/system/status-updater.path
```
Paste:
```ini
[Unit]
Description=Monitor /srv/status/trigger/update for update triggers

[Path]
PathExists=/srv/status/trigger/update
Unit=status-updater.service

[Install]
WantedBy=multi-user.target
```

#### Step 5: Enable and start the monitor
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now status-updater.path
```

Verify it is active:
```bash
sudo systemctl status status-updater.path
```
It will show `Active: active (waiting)`.

Now, whenever you click **`[Update]`** in the UI:
1. The container writes the trigger.
2. Systemd executes the update on the host.
3. You can monitor the logs anytime on the host with:
   ```bash
   journalctl -u status-updater.service -f
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
