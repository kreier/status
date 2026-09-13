# Update Mechanism & Setup Guide

This guide explains how update checking and automatic/on-demand container updates work on Linux hosts (e.g. Raspberry Pi 4, Rockchip RK3229, or x86 servers).

---

## 1. How It Works

### Version Checking (`[Check]` Button & API)
When you click **`[Check]`** or when `/status/api/check` is called:
1. The status service inspects its current running version (e.g. `v0.1.0`).
2. It queries the GitHub Releases API for the configured repository (`CHECK_REPO=kreier/status` by default).
3. It parses semantic versions and compares them.
4. If a newer release is published on GitHub / GHCR:
   - `Updates available: YES` is displayed.
   - The UI displays the latest release tag (e.g. `v0.1.1`).
   - If up to date, it displays `Updates available: NO`.

---

## 2. Update Methods

### Method A: Watchtower (Recommended — In-Container / On-Demand)

[Watchtower](https://containrrr.dev/watchtower/) can watch for new images on `ghcr.io` and automatically or on-demand update your containers.

#### Setup in `docker-compose.yml`:
Uncomment or add the `updater` service:

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
      - WATCHTOWER_TOKEN=status-secret-token
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.status.rule=PathPrefix(`/status`)"
      - "traefik.http.services.status.loadbalancer.server.port=8000"
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
      - WATCHTOWER_HTTP_API_TOKEN=status-secret-token
      - WATCHTOWER_POLL_INTERVAL=86400 # Polls daily, or triggers instantly on button click
    labels:
      - "traefik.enable=false"
```

When you click **`[Update]`** in the status UI:
- The status container sends an authorized HTTP POST to `http://updater:8080/v1/update`.
- Watchtower immediately pulls the latest `ghcr.io/kreier/status:latest` image, recreates the status container with zero downtime, and removes the old image.

---

### Method B: Host Update Script (`update.sh`)

If you prefer keeping full control on the host without giving Docker socket access:

1. Create an `update.sh` script in your status directory (`~/status/update.sh`):
   ```bash
   #!/usr/bin/env bash
   set -e
   cd "$(dirname "$0")"
   echo "Pulling latest image..."
   docker compose pull
   echo "Recreating container..."
   docker compose up -d
   ```
2. Make it executable:
   ```bash
   chmod +x ~/status/update.sh
   ```
3. Mount the script read-only in `docker-compose.yml`:
   ```yaml
   volumes:
     - /etc/os-release:/host/etc/os-release:ro
     - /etc/hostname:/host/etc/hostname:ro
     - /proc:/host/proc:ro
     - ./update.sh:/host/update.sh:ro
   ```

When **`[Update]`** is clicked, the service executes `/host/update.sh`.

---

### Method C: Automated Cron / Systemd Timer

To update unattended on a schedule (e.g. every Sunday at 3 AM):

Edit your crontab on the host (`crontab -e`):
```bash
0 3 * * 0 cd /srv/status && docker compose pull && docker compose up -d --remove-orphans
```
