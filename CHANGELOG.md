# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- Added missing `__init__.py` files in `core/` and `sources/<category>/` so dotted
  package imports in scheduler.py resolve.
- Fixed docker-compose.yml `build:` path (was `./collectors`, which doesn't exist) to
  point at the repo root where the Dockerfile lives.
- Moved frontend files (`index.html`, `app.js`, `style.css`) into a `frontend/`
  directory so the `./frontend:/srv:ro` volume mount resolves.
- Added `.dockerignore` to keep the collectors image lean (frontend, docs, git, secrets).
- Removed dead `common.py` (duplicate of `core/` helpers).
- Updated AGENTS.md, README.md, TODO.md and ARCHITECTURE.md to reflect the actual repo
  layout (`core/`, `sources/`, `scheduler.py`, `frontend/` at the root, not under
  `collectors/`).

### Changed
- Reorganized collectors/ from a flat file list into core/ (shared config, hash-guard,
  status.json writer) and sources/<category>/ (one collector per file, grouped by
  category: system, network, home, github)
- scheduler.py updated to import collectors from their new module paths

### Added
- Initial repo scaffold: README, AGENTS.md, TODO.md, this changelog
- ARCHITECTURE.md, HARDWARE.md, SCHEMA.md
- config.example.yaml
- Docker Compose setup: `collectors` + `web` (Caddy) + `cloudflared` services
- `core/`: config loading, hash-guard pattern, status.json writer, history log
- `scheduler.py`: per-collector interval scheduling
- Collectors: `pi_stats.py` and `github_repos.py` (fully implemented),
  `speedtest_collector.py` (implemented, logs history for future heatmap),
  `room_temp.py`, `ac_state.py`, `nas_images.py` (stubs pending hardware decisions)
- `frontend/`: static page (index.html, style.css, app.js) rendering status.json as cards,
  polling every 60s, dark-mode aware
- `.env.example` for Cloudflare Tunnel token and GitHub credentials
