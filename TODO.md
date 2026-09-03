# TODO

Rough phases, roughly in order. Not all details are decided — pick the next unchecked item.

## Phase 0 — foundations
- [x] Brainstorm architecture, write it up in this repo
- [ ] Decide license
- [ ] `.gitignore`: state/, config.yaml, *.env, any credentials file
- [ ] Fill in docs/HARDWARE.md with actual Pi/NAS/sensor specifics

## Phase 1 — infrastructure
- [ ] Install `cloudflared` on the Pi, authenticate, create tunnel
- [ ] Configure Cloudflare Tunnel public hostname: hv.io.vn → /status* → local port
- [ ] Set up local web server (Caddy or nginx) on the Pi
- [ ] (Optional) Cloudflare Access application in front of a future settings UI, GitHub OAuth
      restricted to own username

## Phase 2 — collector framework
- [ ] Shared helper module: `run_if_changed()` hash-guard pattern, state read/write
- [ ] `config.example.yaml` finalized, `config.yaml` loading logic
- [ ] Orchestrator (`run_all.py` or per-collector systemd timers) that respects each
      collector's own interval

## Phase 3 — collectors
- [ ] `pi_stats.py` — uptime, memory, load (1 min)
- [ ] `room_temp.py` — temperature sensor (1 min)
- [ ] `ac_state.py` — A/C on/off/mode (1 min)
- [ ] `speedtest.py` — download/upload/ping (2 hr), append to history table
- [ ] `nas_images.py` — image count, hash-guarded (24 hr)
- [ ] `github_repos.py` — repo list, stars, last updated, hash-guarded (24 hr)

## Phase 4 — frontend
- [ ] Static page that fetches status.json and renders cards
- [ ] Speedtest heatmap (day × hour grid) from history table
- [ ] Basic responsive layout

## Phase 5 — settings interface
- [ ] Decide: edit config.yaml directly vs. small local form
- [ ] If a form: single-page app, reads/writes config.yaml, behind Cloudflare Access
- [ ] Repo category assignment UI (dropdown per repo)

## Ideas / not committed yet
- [ ] Historical uptime graph, not just current value
- [ ] Alerting (e.g. push notification if A/C left on + nobody home)
- [ ] Dark mode for the status page
