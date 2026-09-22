# status

A lightweight host status service and dashboard for physical and virtual machines (e.g. Rockchip RK3229 TV boxes running Armbian, Raspberry Pis, home servers). Distributed as a multi-architecture container via GitHub Container Registry (`ghcr.io/kreier/status`).

- 📖 **Documentation:** [kreier.github.io/status](https://kreier.github.io/status/)
- 🟢 **Example live page:** [rk3229.hv.io.vn/status/](https://rk3229.hv.io.vn/status/) or local [http://rk3229/status](http://rk3229/status)

## What it shows

```text
RK3229
────────────────────────
System       Armbian
Kernel       6.18.x
Architecture armhf
Uptime       14 days
System life  9d 05h 49m (9 starts)
System uptime 75.96%

Application  v0.1.0
Status       v0.1.0
Updater      v0.1.0

Updates available: YES

[Check]
[Update]
```

- **Host Metrics**: Host system OS (e.g. Armbian, Debian, Ubuntu), Linux kernel, architecture (`armhf`, `arm64`, `amd64`), and uptime.
- **Tuptime Statistics & Historical Analysis**: When `tuptime` is installed on the host and mounted, displays historical system life, startups, shutdowns (ok vs bad), and lifetime uptime percentage.
- **Tabbed Views**:
  - **Overview**: Clean, minimal monospace card for quick status inspection.
  - **Availability Grid**: GitHub-style 52-week annual heatmap showing daily availability, uptime hours, and incident stops with interactive hover tooltips.
  - **90-Day Timeline**: Continuous 90-day availability bar visualization (UptimeRobot-style) highlighting downtime and unexpected power-offs.
- **Component Versions**: Version tracking for host applications, status service, and updater.
- **Actions & API**: Interactive `[Check]` and `[Update]` buttons powered by an extensible `/status/api` REST endpoint.
- **Dual Routing**: Functions seamlessly at direct local URLs (`http://<host>/status`) and behind reverse proxies like Traefik (`https://<host>.hv.io.vn/status/`).

## Quick Start: Standalone (No Traefik Needed)

Works immediately out of the box on any Docker host with zero reverse proxy requirements:

```bash
# 1. Clone repository or create deployment folder
git clone https://github.com/kreier/status.git /srv/status
cd /srv/status

# 2. Create update trigger directory (optional for one-click updates)
sudo mkdir -p trigger && sudo chmod 777 trigger

# 3. Launch container
docker compose up -d
```

The default `docker-compose.yml` runs standalone on port **8000**:

```yaml
services:
  status:
    image: ghcr.io/kreier/status:latest
    container_name: status
    restart: unless-stopped
    ports:
      - "8000:8000"  # Direct access: http://<host>:8000/status
    volumes:
      - /etc/os-release:/host/etc/os-release:ro
      - /etc/hostname:/host/etc/hostname:ro
      - /proc:/host/proc:ro
      - /var/lib/tuptime:/host/var/lib/tuptime:ro
      - ./trigger:/host/trigger:rw
    environment:
      - MACHINE_NAME=RK3229 # Optional override (otherwise detected automatically)
```

Access the dashboard:
- Direct local URL: `http://<machine-ip-or-hostname>:8000/status` (or `http://<host>:8000/`)
- API endpoint: `http://<host>:8000/status/api/status`

*(Tip: If port 80 is free and unprivileged binding is enabled on your host, you can switch the port mapping to `"80:8000"` to access directly via `http://<host>/status`).*

---

## Deploying Behind Traefik Reverse Proxy (HTTPS + Let's Encrypt)

If you run a reverse proxy like Traefik to manage SSL certificates across containers, use `docker-compose.traefik.yml`:

1. Ensure Traefik is running and the shared network `traefik-net` exists (see [examples/traefik/](examples/traefik/) for full Traefik setup).
2. Start the status service using the Traefik compose configuration:

```bash
docker compose -f docker-compose.traefik.yml up -d
```

In `docker-compose.traefik.yml`:
- **No host port mapping:** Status connects directly to `traefik-net`, eliminating port 80 collisions.
- **Automatic Let's Encrypt TLS:** Traefik handles certificate provisioning and HTTPS routing.
- **Access URL:** `https://<your-domain>/status/`

See [examples/traefik/README.md](examples/traefik/README.md) for full setup instructions, DNS configuration, and security recommendations.

## Multi-Architecture Container Support

Images are packaged as lightweight multi-architecture containers (~11–15 MB compressed) published to `ghcr.io/kreier/status`:
- `linux/arm/v7`: 32-bit ARM (Rockchip RK3229 TV boxes, Raspberry Pi 2/3 32-bit)
- `linux/arm64`: 64-bit ARM (Raspberry Pi 4/5, Apple Silicon via Docker Desktop)
- `linux/amd64`: Standard x86_64 PCs, cloud servers, and Windows WSL2

*(Note: macOS and Windows WSL2 run Linux containers natively using the `linux/arm64` and `linux/amd64` images).*


## API Endpoints

- `GET /status/api` or `GET /status/api/status`: Returns JSON status object.
- `GET /status/api/history?days=90`: Returns daily uptime percentage and bad shutdown timeline (past 1 to 365 days).
- `GET /status/api/tuptime`: Returns raw & formatted boot records from `tuptime.db` as JSON.
- `POST /status/api/check`: Checks for updates against GitHub Releases.
- `POST /status/api/update`: Triggers update execution via Watchtower or host script.

## Update Mechanism & Setup

The service provides automated update checking and one-click container updating:
- Clicking **`[Check]`** compares semantic versions against GitHub Releases (`CHECK_REPO=kreier/status`).
- Clicking **`[Update]`** triggers automated container replacement via Watchtower or a host update script.

See [docs/UPDATES.md](docs/UPDATES.md) for full instructions on setting up Watchtower or host update scripts on your Linux machines.

## GHCR Package Maintenance & Cleanup

Because multi-architecture Docker images push individual architecture manifests by digest, untagged images can accumulate over time in GitHub Container Registry.

- **Automated Workflow**: An automated cleanup action [`.github/workflows/cleanup-packages.yml`](.github/workflows/cleanup-packages.yml) runs weekly and can be triggered on demand via GitHub Actions (**Actions > Cleanup Untagged GHCR Images > Run workflow**).
- **Manual CLI Cleanup**: Run the cleanup script locally with GitHub CLI:
  ```bash
  # Ensure scopes 'delete:packages' and 'read:packages' are authorized:
  gh auth refresh -s delete:packages,read:packages
  # Execute cleanup:
  ./scripts/cleanup-ghcr-untagged.sh kreier status
  ```

## License

MIT
