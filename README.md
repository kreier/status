# status

Source and documentation for [hv.io.vn/status](https://hv.io.vn/status) — a self-hosted
status page published from a Raspberry Pi 4 on a home network via Cloudflare Tunnel.

- 📖 **Documentation:** [kreier.github.io/status](https://kreier.github.io/status/) — how
  this is designed and deployed
- 🟢 **Live page:** [hv.io.vn/status](https://hv.io.vn/status) — the actual status page

This repository is *not* the status page — it's the code and docs that build it.

## What the live page shows

- Pi 4 uptime, memory, load
- Internet speed (sampled every 2h, rendered as a heatmap)
- Room temperature and A/C state
- Number of images on the home NAS
- GitHub repositories: category, stars, last updated

## Repo layout

```
status/
├── docker-compose.yml     # what actually runs on the Pi
├── Caddyfile
├── .env.example
├── config.example.yaml
├── core/                  # shared config, hash-guard, status.json writer
├── sources/               # one collector per file, grouped by category
│   ├── system/            #   pi_stats.py
│   ├── network/           #   speedtest_collector.py
│   ├── home/              #   room_temp.py, ac_state.py, nas_images.py
│   └── github/            #   github_repos.py
├── scheduler.py           # entry point, per-collector intervals
├── frontend/              # static page that renders status.json
│
├── docs/                  # GitHub Pages source — documentation, not code
│   ├── index.md
│   ├── ARCHITECTURE.md
│   ├── HARDWARE.md
│   └── SCHEMA.md
├── mkdocs.yml
├── .github/workflows/docs.yml
│
├── AGENTS.md               # for AI coding agents working in this repo
├── TODO.md
├── CHANGELOG.md
```

The `docs/` build (via `mkdocs`) is entirely separate from the deploy path — updating the
Pi is just `git pull && docker compose up -d --build` at the repo root; nothing under
`docs/` affects it.

## Explicitly not in this repo

- Secrets: API tokens, Cloudflare Tunnel token, `.env`, `config.yaml` (only the `.example`
  versions are tracked — see `.gitignore`)
- Anything that reveals exact home address / network topology beyond "a home network"

## License

MIT
