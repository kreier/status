# AGENTS.md

Instructions for AI coding agents (Claude Code, Cursor, Copilot, etc.) working in this repo.
Read this before making changes. If something here conflicts with what a human asks for in
the moment, the human's instruction wins - but flag the conflict.

## What this project is

A status page at hv.io.vn/status, fed by collector scripts running in Docker on a Raspberry
Pi 4 on a home network, published via Cloudflare Tunnel. Full design context: README.md,
ARCHITECTURE.md, SCHEMA.md.

## Core design principles - don't violate these

1. **Collectors are independent and modular.** One script per data source in `collectors/`.
   A collector must never import or depend on another collector. Shared logic (hashing,
   state I/O, config loading) lives in `collectors/common.py`, not copy-pasted.
2. **Cheap check before expensive work.** Any collector whose source rarely changes (GitHub
   repos, NAS image count) must hash a cheap fingerprint of the source first via
   `common.run_if_changed()` and only do the expensive fetch/process when the hash differs.
3. **Config is data, not code.** Repo categories, display names, collector intervals, and
   similar settings belong in config.yaml (git-ignored; config.example.yaml is the tracked
   template), never hardcoded in a collector.
4. **No secrets in this repo, ever.** No API tokens, no TUNNEL_TOKEN, no real .env, no real
   config.yaml, no NAS credentials. `.env.example` and `config.example.yaml` are the tracked
   templates - if a task seems to require committing a secret, stop and ask instead.
5. **Every collector output follows the shared schema** in SCHEMA.md (id, category, label,
   value, status). Don't invent a new shape per collector.
6. **Respect the update cadence per source** (see ARCHITECTURE.md) - don't "simplify" by
   running everything on one loop interval. Speedtest is expensive and slow; GitHub/NAS
   checks should be near-free when nothing changed.

## Conventions

- Language: Python 3 for collectors (kept minimal - this runs 24/7 on a Pi 4).
- One collector = one file in `collectors/`, exposing a `collect()` function that returns
  its entries and also calls `common.write_entries()` itself.
- New collector checklist: add the module to `COLLECTOR_MODULES` in `scheduler.py`, add its
  interval under `collectors:` in `config.example.yaml`, document it in SCHEMA.md if its
  output shape is unusual.
- State (hashes, cached results, speedtest history) lives in the `status-data` Docker
  volume, not in the repo.
- Frontend is plain HTML/JS/CSS in `frontend/` - no build step, no framework, served
  directly by Caddy. Fetches `data/status.json` client-side.
- Three Docker Compose services: `collectors`, `web`, `cloudflared`. Don't add more services
  without a reason - this is meant to stay small.

## When you finish a task

- Update TODO.md: check off what's done, add anything new that surfaced.
- Add an entry under `Unreleased` in CHANGELOG.md.
- If you changed the shape of status.json or added a new collector, update SCHEMA.md.
