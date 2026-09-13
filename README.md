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

Application  v0.4.2
Status       v0.2.0
Updater      v0.1.1

Updates available: YES

[Check]
[Update]
```

- **Host Metrics**: Host system OS (e.g. Armbian), Linux kernel, architecture (`armhf`, `arm64`, `amd64`), and uptime.
- **Component Versions**: Version tracking for host applications, status service, and updater.
- **Actions & API**: Interactive `[Check]` and `[Update]` buttons powered by an extensible `/status/api` REST endpoint.
- **Dual Routing**: Functions seamlessly at direct local URLs (`http://<host>/status`) and behind reverse proxies like Traefik (`https://<host>.hv.io.vn/status/`).

## Quick Start (Docker Compose)

Create a directory on your machine (e.g. `mkdir -p ~/status && cd ~/status`) with the following `docker-compose.yml`:

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
    environment:
      - MACHINE_NAME=RK3229 # Optional override (otherwise detected automatically)
      - APPLICATION_VERSION=v0.4.2
      - UPDATER_VERSION=v0.1.1
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.status.rule=Host(`rk3229.hv.io.vn`) && PathPrefix(`/status`)"
      - "traefik.http.routers.status.entrypoints=websecure"
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

Images are automatically built and published via GitHub Actions to `ghcr.io/kreier/status` for:
- `linux/arm/v7` (32-bit ARM, e.g. Rockchip RK3229 TV boxes, Raspberry Pi 2/3 32-bit)
- `linux/arm64` (64-bit ARM, e.g. Raspberry Pi 4/5, Apple Silicon)
- `linux/amd64` (Standard x86_64 servers and PCs)

## API Endpoints

- `GET /status/api` or `GET /status/api/status`: Returns JSON status object.
- `POST /status/api/check`: Triggers update check.
- `POST /status/api/update`: Triggers update execution.

## License

MIT
