# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **Dedicated Traefik Configuration (`docker-compose.traefik.yml`)**: Clean deployment configuration for running status behind Traefik reverse proxy on internal network `traefik-net` without exposing host ports.
- **Traefik Stack Example & Guide (`examples/traefik/`)**: Complete turnkey Traefik reverse proxy stack (`examples/traefik/docker-compose.yml`) and setup guide (`examples/traefik/README.md`) covering Let's Encrypt TLS challenge, strict `acme.json` permissions (`chmod 600`), DNS requirements, and dashboard security.

### Changed
- **Decoupled Standalone Deployment (`docker-compose.yml`)**: Default compose configuration now works immediately out of the box on port `8000:8000` (with `80:8000` option) without requiring Traefik or reverse proxy configurations.
- **Documentation**: Updated `README.md`, `docs/ARCHITECTURE.md`, and `docs/UPDATES.md` with standalone out-of-the-box instructions and reverse proxy integration options.

### Fixed
- Replaced `actions/delete-package-versions` in `.github/workflows/cleanup-packages.yml` with `dataaxiom/ghcr-cleanup-action@v1`. The previous action deleted child platform manifests of multi-architecture container images (`amd64`, `arm64`, `arm/v7`), resulting in missing manifest errors (404) during Docker pulls on target devices.

## [0.3.3] - 2026-09-14

### Added
- **Day Cell Restart & Bad Stop Indicators**: Added orange (`#f97316`) indicator for restarts and red (`#ef4444`) indicator for bad shutdowns on both the Annual Availability Heatmap and 90-Day Timeline.
- **Dedicated Restarts Metric Row**: Moved restarts into a distinct `Restarts` row showing startup count and shutdown breakdown (e.g. `12 (10 ok, 2 bad)`), leaving `System life` clean and uncombined.

### Changed
- **Top View Toggle Buttons**: Positioned `[Heatmap]` and `[90-day Timeline]` toggle buttons at the top of the card above System info, styled with a distinct green theme (`rgba(16, 185, 129, 0.08)`) and vibrant solid green active state with glow.
- **Full Annual Heatmap Width**: Expanded container and extra-card max-width from 680px to 840px so the complete 53-week annual calendar grid displays without requiring horizontal scrolling.

### Fixed
- Fixed container crash on startup (`NameError: name 'Union' is not defined`) in Python 3.12 environments by importing `Union` and adding `from __future__ import annotations` to `core/host_info.py` and `app.py`.

## [0.3.1] - 2026-09-14

### Added
- **Multi-Year Annual Grids**: Availability grid now queries and renders all concerned years recorded in `tuptime.db` (e.g. 2024, 2025, 2026), generating 365-day heatmaps for each year with tracked, future, and unrecorded states.
- **Decoupled Togglable Cards**: Main status badge is a centered floating rectangle card. Availability Grid and 90-Day Timeline open as separate rectangular card boxes below the main card when toggled.
- **Tuptime Records API**: Added `GET /api/tuptime` and `GET /status/api/tuptime` returning all boot records from `tuptime.db` as JSON for diagnostics and inspection.
- **Multi-Year History API**: Enhanced `/status/api/history` to accept `?year=all` or `?year=YYYY` returning full yearly matrices.

### Changed
- **System Life Link Styling**: Removed underlines from "System life" and "System uptime" links, rendering them in clean blue (`#60a5fa`) with hover effect.

## [0.3.0] - 2026-09-14

### Added
- **Interactive Tab Navigation**: Added top-level tab bar switching between **Overview** (classic minimal card), **Availability Grid** (GitHub-style 52-week annual heatmap), and **90-Day Timeline** (continuous daily operational bars).
- **Tuptime Daily Historical Analysis**: Real-time interval intersection engine in `core/host_info.py` (`get_uptime_history(days)`) calculating precise daily uptime percentages, bad stops, and continuous availability from SQLite database (`/var/lib/tuptime/tuptime.db`).
- **REST API Endpoint**: Added `GET /api/history` and `GET /status/api/history` accepting optional `?days=N` (default 90, max 365).
- **Pure CSS/SVG-Free Visualizations**: Zero external JavaScript chart libraries used, maintaining ultra-lightweight footprint (<15 MB container) and native responsiveness. Smooth container width expansion (`440px` to `620px`) when switching to history views.
- **Client-Side In-Memory Cache**: Cached history responses in `frontend/app.js` to avoid repeated queries when toggling tabs.

### Documentation
- Updated `docs/UPDATES.md` and `README.md` with complete architecture diagram and setup guide recommending `/srv/status` (or `/src/status`) for the decoupled host updater.
- Documented `/status/api/history` response structure and parameter schema in `docs/SCHEMA.md`.

## [0.2.1] - 2026-09-14

### Added
- Multi-year formatting support for `tuptime` system life (e.g. `2yr 222d 4h 14m 24s`).
- Explicit `System life: not available` display with informative tooltip reason when host `/var/lib/tuptime` is unmounted.

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
