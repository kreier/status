# TODO

Rough phases, roughly in order. Not all details are decided - pick the next unchecked item.

## Phase 0 - foundations
- [x] Brainstorm architecture, write it up in this repo
- [x] Decide license (MIT)
- [x] `.gitignore`: state/, config.yaml, .env, credentials
- [ ] Fill in HARDWARE.md with actual Pi/NAS/sensor specifics

## Phase 1 - infrastructure & host status container
- [x] Host inspection utility (`core/host_info.py`)
- [x] Host `tuptime` historical uptime inspection (startups, shutdowns, life, % uptime)
- [x] Web server and extensible API (`app.py`, `/status/api`)
- [x] Status card UI with interactive Check and Update actions
- [x] Multi-architecture Docker image publishing (`ghcr.io/kreier/status` with `armhf`/`arm64`/`amd64`)
- [x] Standard `docker-compose.yml` supporting host mounts, local direct access, and Traefik reverse proxy
- [x] Deploy to RK3229 and Pi 4 with Docker Compose and Traefik
- [x] Automated update checking against GitHub Releases
- [x] On-demand container updater integration (Watchtower / host script)
- [x] Automated and CLI-based GHCR untagged package cleanup
- [ ] Create Cloudflare Tunnel (Docker connector) in the Zero Trust dashboard, get token
- [ ] Add public hostname route: hv.io.vn -> /status* -> http://web:80

- [ ] (Optional) Cloudflare Access application in front of a future settings UI, GitHub OAuth
      restricted to own username

## Phase 2 - collector framework
- [x] Shared helper module: `run_if_changed()` hash-guard pattern, state read/write
      (core/)
- [x] config.example.yaml finalized, config.yaml loading logic
- [x] Scheduler (`scheduler.py`) respecting each collector's own interval

## Phase 3 - collectors
- [x] `pi_stats.py` - uptime, memory, load (1 min)
- [ ] `room_temp.py` - currently a stub, needs sensor decision (see HARDWARE.md)
- [ ] `ac_state.py` - currently a stub, needs integration decision (see HARDWARE.md)
- [x] `speedtest_collector.py` - download/upload/ping (2 hr), appends to history file
- [ ] `nas_images.py` - hash-guard scaffolding in place, needs NAS access wired up (24 hr)
- [x] `github_repos.py` - repo list, stars, last updated, hash-guarded (24 hr)

## Phase 4 - frontend
- [x] Static page that fetches status.json and renders cards
- [ ] Speedtest heatmap (day x hour grid) from speedtest_history.jsonl
- [ ] Basic responsive layout polish

## Phase 5 - settings interface
- [ ] Decide: edit config.yaml directly vs. small local form
- [ ] If a form: single-page app, reads/writes config.yaml, behind Cloudflare Access
- [ ] Repo category assignment UI (dropdown per repo)

## Ideas / not committed yet
- [x] Historical uptime graph, not just current value (52-week heatmap & 90-day timeline in v0.3.0)
- [ ] Alerting (e.g. push notification if A/C left on + nobody home)
- [ ] Dark mode for the status page (frontend already follows prefers-color-scheme)
