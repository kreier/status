# Architecture

## Data flow

1. Collector scripts run on the Pi 4, each on its own schedule, orchestrated by
   `scheduler.py`.
2. Each collector writes its entries into a shared `status.json` (merged by id - see
   `core.status.write_entries`).
3. A Caddy web server serves the static frontend and `status.json`.
4. `cloudflared` runs as its own container, holding an outbound connection to Cloudflare.
   No inbound port is opened on the home router.
5. Cloudflare Tunnel routes `hv.io.vn/status*` to the Caddy container.
6. A visitor's browser loads the static page, then polls `data/status.json` client-side
   every 60s to update the cards.

## Why Cloudflare Tunnel over port forwarding

- No open inbound port on the home router - smaller attack surface.
- The Pi's home IP is never exposed.
- Cloudflare Access can be layered on top later (e.g. for a settings UI) without any extra
  network changes.

## Docker Compose deployment

Three containers, one `docker-compose.yml`:

| Service       | Image / build         | Role                                             |
|---------------|------------------------|---------------------------------------------------|
| `collectors`  | built from repo root   | runs `scheduler.py`, writes to a shared volume  |
| `web`         | `caddy:2-alpine`       | serves `frontend/` + the shared volume's `status.json` |
| `cloudflared` | `cloudflare/cloudflared` | tunnels `web` out to `hv.io.vn/status`         |

Shared state (`status.json`, speedtest history, per-collector hash cache) lives in a named
Docker volume (`status-data`), mounted read-write in `collectors` and read-only in `web`.

Setup:

1. Create a tunnel in the Cloudflare Zero Trust dashboard, connector type "Docker", copy the
   token it gives you.
2. In the tunnel's **Public Hostname** settings, add a route: `hv.io.vn`, path `/status*`,
   service `http://web:80` (the Docker service name, resolved over the compose network -
   no IP or port-forwarding involved).
3. Copy `.env.example` to `.env`, fill in `TUNNEL_TOKEN` and `GITHUB_USERNAME`
   (`GITHUB_TOKEN` optional).
4. Copy `config.example.yaml` to `config.yaml`, set repo categories.
5. `docker compose up -d --build`.

Both `.env` and `config.yaml` are git-ignored - only the `.example` versions are tracked.

## Update cadence per source

| Source              | Interval    | Notes                                              |
|----------------------|-------------|-----------------------------------------------------|
| Pi uptime/memory/load | 1 min       | Cheap, local                                        |
| Room temperature       | 1 min       | Cheap, local sensor read (stubbed - see HARDWARE.md) |
| A/C state              | 1 min       | Cheap, local (stubbed - see HARDWARE.md)            |
| Internet speed         | 2 hr        | Expensive (uses real bandwidth); logged to history for a heatmap |
| NAS image count         | 24 hr       | Hash-guarded, stubbed until NAS access is wired up  |
| GitHub repos            | 24 hr       | Hash-guarded - implemented                          |

Intervals are set in `config.yaml` under `collectors:`, read by `scheduler.py`.

## Speedtest history / heatmap

`speedtest_collector.py` appends each reading (timestamp, download, upload, ping) to
`speedtest_history.jsonl` in the shared volume. The frontend heatmap (day x hour grid) that
reads this file is not yet built - see TODO.md.

## Settings

Settings (repo categories, display names, collector intervals) live in `config.yaml`,
git-ignored. `config.example.yaml` is the tracked template. A dedicated settings UI is
future work (TODO.md Phase 5) - for now, edit `config.yaml` on the Pi directly and the next
collector cycle picks it up.

## Open questions

- Where config.yaml edits should be authoritative long-term: local file on the Pi, or
  committed back to this repo via the GitHub API from a settings UI.
