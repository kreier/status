# Architecture

## Data flow

1. Collector scripts run on the Pi 4, each on its own schedule (cron or systemd timers).
2. Each collector writes its result into a shared `status.json` (or its own file, merged by
   an orchestrator — decide in Phase 2).
3. A local web server (Caddy or nginx) on the Pi serves the static frontend and `status.json`.
4. `cloudflared` runs as a systemd service on the Pi, holding an outbound connection to
   Cloudflare. No inbound port is opened on the home router.
5. Cloudflare Tunnel routes `hv.io.vn/status*` to the local web server via that connection.
6. A visitor's browser fetches the static page from Cloudflare's edge, then polls
   `status.json` client-side to update the cards.

## Why Cloudflare Tunnel over port forwarding

- No open inbound port on the home router — smaller attack surface.
- The Pi's home IP is never exposed.
- Cloudflare Access can be layered on top later (e.g. for a settings UI) without any extra
  network changes.

## Update cadence per source

Not everything should run on the same 1-minute loop — some things are cheap and change
constantly, others are expensive or rarely change.

| Source              | Interval    | Notes                                              |
|----------------------|-------------|-----------------------------------------------------|
| Pi uptime/memory/load | 1 min       | Cheap, local                                        |
| Room temperature       | 1 min       | Cheap, local sensor read                            |
| A/C state              | 1 min       | Cheap, local                                        |
| Internet speed         | 2 hr        | Expensive (uses real bandwidth); logged to history for a heatmap |
| NAS image count         | 24 hr       | Hash-guarded — cheap listing check first, full count only if changed |
| GitHub repos            | 24 hr       | Hash-guarded — cheap metadata check first, full fetch only if changed |

## Speedtest history / heatmap

Unlike the other sources, speedtest needs history, not just a latest value. Store each
sample (timestamp, download, upload, ping) in an append-only table (SQLite or CSV). The
frontend aggregates this into a day × hour grid for the heatmap. At a 2-hour interval this
fills in meaningfully within a couple of weeks.

## Settings

Settings (repo categories, display names, collector intervals) live in `config.yaml` on the
Pi, git-ignored. `config/config.example.yaml` in this repo is the tracked template. See
TODO.md Phase 5 for the planned settings interface.

## Open questions

- Reverse proxy in front of `cloudflared`, or point `cloudflared` straight at the frontend
  port? (Optional either way — only matters if the Pi serves more than this one thing.)
- Where config.yaml edits should be authoritative: local file on the Pi, or committed back to
  this repo via the GitHub API from a settings UI.
