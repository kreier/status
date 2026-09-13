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
- **Tuptime Statistics**: When `tuptime` is installed on the host and mounted, displays historical system life, startups, shutdowns (ok vs bad), and lifetime uptime percentage.
- **Component Versions**: Version tracking for host applications, status service, and updater.
- **Actions & API**: Interactive `[Check]` and `[Update]` buttons powered by an extensible `/status/api` REST endpoint.
- **Dual Routing**: Functions seamlessly at direct local URLs (`http://<host>/status`) and behind reverse proxies like Traefik (`https://<host>.hv.io.vn/status/`).

## Quick Start (Docker Compose)

We recommend deploying in `/srv/status` (or `/src/status`) to provide a clean, predictable location for `systemd` automation:

```bash
sudo mkdir -p /srv/status/trigger && sudo chmod 777 /srv/status/trigger
cd /srv/status
```

Create `docker-compose.yml`:

```yaml
services:
  status:
    image: ghcr.io/kreier/status:latest
    container_name: status
    restart: unless-stopped
    ports:
      - "80:8000"
    volumes:
      # Read-only mounts to inspect host metrics
      - /etc/os-release:/host/etc/os-release:ro
      - /etc/hostname:/host/etc/hostname:ro
      - /proc:/host/proc:ro
      # Optional: mount host tuptime database if tuptime is installed
      - /var/lib/tuptime:/host/var/lib/tuptime:ro
      # Mount trigger directory for one-click updates (Method B)
      - ./trigger:/host/trigger:rw
    environment:
      - MACHINE_NAME=RK3229 # Optional override (otherwise detected automatically)
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.status.rule=(Host(`rk3229.hv.io.vn`) || Host(`rk3229`) || Host(`localhost`)) && PathPrefix(`/status`)"
      - "traefik.http.routers.status.entrypoints=web,websecure"
      - "traefik.http.routers.status.tls=true"
      - "traefik.http.services.status.loadbalancer.server.port=8000"
```

Start the container:

```bash
docker compose up -d
```

Access the dashboard:
- Locally: `http://<machine-ip-or-hostname>/status`
- Reverse proxy (Traefik): `https://rk3229.hv.io.vn/status/`
- API endpoint: `http://<host>/status/api/status`

## Multi-Architecture Container Support

Images are packaged as lightweight multi-architecture containers (~11–15 MB compressed) published to `ghcr.io/kreier/status`:
- `linux/arm/v7`: 32-bit ARM (Rockchip RK3229 TV boxes, Raspberry Pi 2/3 32-bit)
- `linux/arm64`: 64-bit ARM (Raspberry Pi 4/5, Apple Silicon via Docker Desktop)
- `linux/amd64`: Standard x86_64 PCs, cloud servers, and Windows WSL2

*(Note: macOS and Windows WSL2 run Linux containers natively using the `linux/arm64` and `linux/amd64` images).*


## API Endpoints

- `GET /status/api` or `GET /status/api/status`: Returns JSON status object.
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
