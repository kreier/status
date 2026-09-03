# hv.io.vn/status — documentation

This site documents **how** [hv.io.vn/status](https://hv.io.vn/status) is designed and
deployed. It is documentation about the project — not the status page itself.

[Go to the live status page →](https://hv.io.vn/status){ .md-button .md-button--primary }

## What's here

- **[Architecture](ARCHITECTURE.md)** — data flow, Docker Compose layout, Cloudflare Tunnel
  setup, update cadence per data source
- **[Hardware](HARDWARE.md)** — what's actually running on the Pi: sensors, NAS, network
- **[Schema](SCHEMA.md)** — the status.json shape and the hash-guard collector pattern

## Source code

The collectors, frontend, and `docker-compose.yml` that actually run the page live at the
repository root: [github.com/kreier/status](https://github.com/kreier/status). See
[AGENTS.md](https://github.com/kreier/status/blob/main/AGENTS.md) there if you're an AI
agent picking up work on this project, or
[TODO.md](https://github.com/kreier/status/blob/main/TODO.md) for the current roadmap.
