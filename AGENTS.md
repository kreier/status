# AGENTS.md

Instructions for AI coding agents (Claude Code, Cursor, Copilot, Antigravity, etc.) working in this repo.
Read this before making changes. If something here conflicts with what a human asks for in
the moment, the human's instruction wins - but flag the conflict.

## What this project is

A self-hosted host status dashboard and service distributed as a multi-architecture Docker container via GitHub Container Registry (`ghcr.io/kreier/status`). It inspects the host machine it runs on (e.g. Rockchip RK3229 running Armbian, Raspberry Pi 4, x86 servers) and presents a clean status dashboard both locally (e.g. `http://<host>/status`) and behind reverse proxies like Traefik (`https://<host>.hv.io.vn/status/`), with an extensible `/status/api` endpoint and integrated update checking/triggering.

Full design context: `README.md`, `docs/ARCHITECTURE.md`, `docs/SCHEMA.md`, `docs/UPDATES.md`.

## Core design principles - don't violate these

1. **Lightweight & Multi-Architecture.** The container runs on low-power devices including 32-bit ARM (`linux/arm/v7` for RK3229), 64-bit ARM (`linux/arm64`), and x86_64 (`linux/amd64`). Keep dependencies pure Python where possible — avoid C-extensions that require heavy compilers on ARM.
2. **Safe Host Inspection.** The container inspects the host using standard read-only mounts (`/etc/os-release`, `/etc/hostname`, `/proc`) rather than requiring privileged root container access.
3. **Dual Routing & Subpath Resilience.** The service must always function at both `/` and `/status` (and `/status/`), and API endpoints at both `/api` and `/status/api`. Frontend assets must use relative paths or dynamic base path resolution (`getBaseUrl()`) so Traefik prefix-matching never breaks UI or API calls.
4. **No Cached 404s or Stale UI.** Always ensure `@app.after_request` provides cache-busting headers (`Cache-Control: no-cache, no-store, must-revalidate`) and asset references in `index.html` include query versioning (`style.css?v=...`, `app.js?v=...`).
5. **No secrets in this repo, ever.** No API tokens, no credentials, no real `.env` or `config.yaml`.
6. **Package frontend files in Docker image.** `.dockerignore` must NEVER exclude `frontend/` — the standalone container needs `frontend/index.html`, `style.css`, and `app.js` packaged inside.

## Repo layout

- `app.py` — Flask / WSGI web application serving dashboard and `/status/api`.
- `core/host_info.py` — Host metric extraction (distro, kernel, architecture, uptime), version tracking, GitHub release check, and updater triggering.
- `core/` — shared infrastructure (`config.py`, `state.py`, `status.py`, `host_info.py`).
- `frontend/` — static dashboard (`index.html`, `style.css`, `app.js`).
- `sources/` — optional modular collectors (`pi_stats.py`, etc.).
- `scheduler.py` — optional periodic background collector runner.
- `docker-compose.yml` — production compose file deploying `ghcr.io/kreier/status:latest` with host mounts and Traefik labels.
- `docker-compose.local.yml` — local development compose (`build: .`).
- `.github/workflows/docker.yml` — automated multi-arch image builder pushing to GHCR.
- `docs/` — documentation published via MkDocs (`ARCHITECTURE.md`, `SCHEMA.md`, `UPDATES.md`).

## When you finish a task

- Update `TODO.md`: check off what's done, add anything new that surfaced.
- Add an entry under `Unreleased` in `CHANGELOG.md`.
- If you changed the shape of API endpoints or status data, update `docs/SCHEMA.md`.
