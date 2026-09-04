# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
- `collectors/common.py`: config loading, hash-guard pattern, status.json writer, history log
- `collectors/scheduler.py`: per-collector interval scheduling
- Collectors: `pi_stats.py` and `github_repos.py` (fully implemented),
  `speedtest_collector.py` (implemented, logs history for future heatmap),
  `room_temp.py`, `ac_state.py`, `nas_images.py` (stubs pending hardware decisions)
- `frontend/`: static page (index.html, style.css, app.js) rendering status.json as cards,
  polling every 60s, dark-mode aware
- `.env.example` for Cloudflare Tunnel token and GitHub credentials
