# AGENTS.md

Instructions for AI coding agents (Claude Code, Cursor, Copilot, etc.) working in this repo.
Read this before making changes. If something here conflicts with what a human asks for in
the moment, the human's instruction wins — but flag the conflict.

## What this project is

A status page at hv.io.vn/status, fed by collector scripts running on a Raspberry Pi 4 on a
home network, published via Cloudflare Tunnel. Full design context: README.md,
docs/ARCHITECTURE.md, docs/SCHEMA.md.

## Core design principles — don't violate these

1. **Collectors are independent and modular.** One script per data source. A collector must
   never import or depend on another collector. Shared logic (hashing, state I/O) lives in a
   common helper module, not copy-pasted.
2. **Cheap check before expensive work.** Any collector whose source rarely changes (GitHub
   repos, NAS image count) must hash a cheap fingerprint of the source first and only do the
   expensive fetch/process when the hash differs. See docs/SCHEMA.md for the pattern.
3. **Config is data, not code.** Repo categories, display names, collector intervals, and
   similar settings belong in config.yaml (git-ignored; config.example.yaml is the tracked
   template), never hardcoded in a collector.
4. **No secrets in this repo, ever.** No API tokens, no Cloudflare Tunnel credentials file, no
   real config.yaml, no NAS credentials. If a task seems to require committing a secret, stop
   and ask instead.
5. **Every collector output follows the shared schema** in docs/SCHEMA.md. Don't invent a new
   shape per collector.
6. **Respect the update cadence per source** (see docs/ARCHITECTURE.md) — don't "simplify" by
   running everything on one 1-minute loop. Speedtest is expensive and slow; GitHub/NAS checks
   should be near-free when nothing changed.

## Conventions

- Language: Python 3 for collectors unless there's a strong reason otherwise (keep the
  environment on the Pi simple).
- One collector = one file in `collectors/`, named after its data source
  (e.g. `collectors/github_repos.py`).
- State (hashes, last-checked timestamps, speedtest history) lives under a `state/` directory,
  git-ignored, not committed.
- Frontend is plain HTML/JS/CSS — no build step, no framework, so it's easy to serve as static
  files from the Pi. Fetches `status.json` client-side.
- Keep dependencies minimal — this runs 24/7 on a Pi 4, not a beefy server.

## When you finish a task

- Update TODO.md: check off what's done, add anything new that surfaced.
- Add an entry under `Unreleased` in CHANGELOG.md.
- If you changed the shape of status.json or added a new collector, update docs/SCHEMA.md.
