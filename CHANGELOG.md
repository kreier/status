# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.0] - 2026-09-14

### Added
- Historical uptime statistics inspection via `tuptime` SQLite database (`/host/var/lib/tuptime/tuptime.db`), displaying system life, startups, shutdowns (ok vs bad), and lifetime uptime rate.
- Automated cleanup workflow `.github/workflows/cleanup-packages.yml` and CLI script `scripts/cleanup-ghcr-untagged.sh` to safely purge untagged multi-arch image versions from GitHub Container Registry (GHCR).
- Mount `/var/lib/tuptime:/host/var/lib/tuptime:ro` in `docker-compose.yml` and `docker-compose.local.yml`.
- Automated update checking in `core/host_info.py` using web release redirect and fallback to GitHub Releases API.
- On-demand update trigger integration with Watchtower HTTP API (`WATCHTOWER_URL`) and host update script (`/host/update.sh`).
- Complete Linux machine update setup guide in `docs/UPDATES.md` covering Watchtower, host scripts, and cron automation.
- Watchtower updater service profile and check repository configuration in `docker-compose.yml`.

### Fixed
- Fixed unauthenticated GitHub API rate limiting (403 Forbidden) by resolving latest releases via HTML redirect before querying REST API.
- Fixed missing `frontend/` directory in Docker image by removing `frontend/` exclusion from `.dockerignore`.
- Fixed `/status` and `/status/` 404 routing by setting `strict_slashes=False` and ensuring index fallback.
- Added cache-busting headers (`Cache-Control: no-cache, no-store, must-revalidate`) and asset version query strings (`?v=...`) to prevent stale browser caching.
- Fixed `app.js` initialization race condition by checking `document.readyState` so `loadStatus()` always executes under HTTP/2.
- Removed `psutil` dependency from `requirements.txt` and `pi_stats.py` to ensure fast, pure-Python builds on 32-bit ARM (`armhf`).

## [0.1.0] - 2026-09-13

### Added
- Host inspection engine (`core/host_info.py`) detecting machine name, OS distro, kernel release, architecture (`armhf`, `arm64`, `amd64`), host uptime, component versions (`Application`, `Status`, `Updater`), and update status.
- Unified web server & API (`app.py`) supporting direct local access (`/status`) and reverse proxy subpath routing (`/status/api`).
- Monospace/terminal styled responsive status dashboard card in `frontend/` matching single-host status requirements with interactive `[Check]` and `[Update]` buttons.
- Multi-architecture Docker publishing GitHub Actions workflow (`.github/workflows/docker.yml`) for `linux/arm/v7` (32-bit ARM for RK3229), `linux/arm64`, and `linux/amd64` to `ghcr.io/kreier/status`.
- Streamlined `docker-compose.yml` configured for GHCR image deployment with host volume mounts and Traefik router/service labels.
- `docker-compose.local.yml` for local container building and development.
- Unit test suites `test_status.py` and `test_app.py`.
- Shared core infrastructure: config loading, hash-guard pattern, and status history.
