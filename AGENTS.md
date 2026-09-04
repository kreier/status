# AGENTS.md

Instructions for AI coding agents (Claude Code, Cursor, Copilot, etc.) working in this repo.
Read this before making changes. If something here conflicts with what a human asks for in
the moment, the human's instruction wins - but flag the conflict.

## What this project is

A status page at hv.io.vn/status, fed by collector scripts running in Docker on a Raspberry
Pi 4 on a home network, published via Cloudflare Tunnel. Full design context: README.md,
docs/ARCHITECTURE.md, docs/SCHEMA.md.

## Core design principles - don't violate these

1. **Collectors are independent and modular.** One module per data source, grouped by
   category under `collectors/sources/<category>/` (system, network, home, github, ...). A
   collector must never import another collector. Shared logic lives in `collectors/core/`
   (`config.py`, `state.py`, `status.py`), not copy-pasted.
2. **Cheap check before expensive work.** Any collector whose source rarely changes (GitHub
   repos, NAS image count) must hash a cheap fingerprint of the source first via
   `core.state.run_if_changed()` and only do the expensive fetch/process when the hash
   differs.
3. **Config is data, not code.** Repo categories, display names, collector intervals, and
   similar settings belong in config.yaml (git-ignored; config.example.yaml is the tracked
   template), never hardcoded in a collector.
4. **No secrets in this repo, ever.** No API tokens, no TUNNEL_TOKEN, no real .env, no real
   config.yaml, no NAS credentials. `.env.example` and `config.example.yaml` are the tracked
   templates - if a task seems to require committing a secret, stop and ask instead.
5. **Every collector output follows the shared schema** in docs/SCHEMA.md (id, category,
   label, value, status). Don't invent a new shape per collector.
6. **Respect the update cadence per source** (see docs/ARCHITECTURE.md) - don't "simplify"
   by running everything on one loop interval. Speedtest is expensive and slow; GitHub/NAS
   checks should be near-free when nothing changed.
7. **State lives in the `status-data` Docker volume, not in the image.** `docker compose up
   -d --build` rebuilds the image but never touches the volume - that's what makes state
   (status.json, hashes, speedtest history) survive redeploys. Only `docker compose down -v`
   deletes it. Never add volume contents to the image via COPY.

## Repo layout

- `collectors/core/` - shared infrastructure (config loading, hash-guard, status.json
  writer). Not a data source itself.
- `collectors/sources/<category>/<name>.py` - one collector per file, exposing a `collect()`
  function that returns its entries and also calls `core.status.write_entries()` itself.
- `collectors/scheduler.py` - entry point; maps collector name -> module path, runs each on
  its configured interval.
- `frontend/` - plain HTML/JS/CSS, no build step, served by Caddy. Fetches
  `data/status.json` client-side.
- `docs/` - GitHub Pages source (documentation about the project, built via mkdocs). Fully
  decoupled from what runs on the Pi - editing docs never requires touching deploy code.
- Root-level `docker-compose.yml`, `Caddyfile`, `.env.example`, `config.example.yaml` -
  what actually runs on the Pi. Keep these at root; a Pi `git pull` should never need a
  path change here.

## Adding a new collector

1. Pick (or create) a category folder under `collectors/sources/`.
2. Write `<name>.py` with a `collect()` function using `core.config`, `core.state`,
   `core.status` as needed.
3. Register it in `COLLECTOR_MODULES` in `collectors/scheduler.py`.
4. Add its interval under `collectors:` in `config.example.yaml`.
5. If its output shape is unusual (like `github_repos`' list-valued entry), note it in
   docs/SCHEMA.md.

## When you finish a task

- Update TODO.md: check off what's done, add anything new that surfaced.
- Add an entry under `Unreleased` in CHANGELOG.md.
- If you changed the shape of status.json or added a new collector, update docs/SCHEMA.md.
