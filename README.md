# status

A self-hosted status page for [hv.io.vn/status](https://hv.io.vn/status), published from a
Raspberry Pi 4 on a home network via Cloudflare Tunnel.

It shows:

- Pi 4 uptime, memory, load
- Internet speed (sampled every 2h, rendered as a heatmap)
- Room temperature
- A/C state
- Number of images on the home NAS
- GitHub repositories: category, stars, last updated

## Status

🚧 Design phase. No code running yet. See [TODO.md](TODO.md) for what's next and
[CHANGELOG.md](CHANGELOG.md) for what's shipped.

## How it works (short version)

Small **collector** scripts run on the Pi on their own schedules, write into a shared
`status.json`, and a static frontend polls that file. Cloudflare Tunnel exposes the page
at `hv.io.vn/status` without opening any port on the home router. Full details in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repo layout

```
status/
├── AGENTS.md              # instructions for AI coding agents working in this repo
├── TODO.md                # task list / roadmap
├── CHANGELOG.md           # what's shipped, Keep a Changelog format
├── docs/
│   ├── ARCHITECTURE.md    # data flow, Cloudflare Tunnel setup, update cadences
│   ├── HARDWARE.md        # what's actually running on the Pi (inventory)
│   └── SCHEMA.md          # status.json / collector output schema
├── config/
│   └── config.example.yaml
├── collectors/            # one script per data source (not yet written)
└── frontend/               # static page that renders status.json (not yet written)
```

## Explicitly not in this repo

- Secrets: API tokens, Cloudflare Tunnel credentials, `config.yaml` (only `config.example.yaml`
  is tracked). See `.gitignore`.
- Anything that reveals exact home address / network topology beyond "a home network."

## License

Not yet decided — pick one before the first real code lands.
