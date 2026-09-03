# Hardware & network inventory

What's actually running, for future reference (and for an AI agent to know what it's working
with). Fill in the blanks — keep this file free of secrets (no IPs you consider sensitive,
no credentials, no exact street-level location).

## Raspberry Pi 4

- Model / RAM: _e.g. Pi 4 Model B, 4GB_
- OS: _e.g. Raspberry Pi OS Lite (64-bit), version_
- Role: runs collectors, local web server, cloudflared
- Always-on: yes, 24/7

## Sensors

- Room temperature: _sensor model / how it's read (GPIO, I2C, smart plug API, etc.)_
- A/C state: _how state is determined — smart plug, IR blaster + Home Assistant, direct API_

## NAS

- Model / OS: _e.g. Synology DS920+, DSM version_
- How the Pi reaches it: _SMB mount, API, SSH_
- What "image count" means here: _entire NAS, one photo library share, etc._

## Network

- Router: _model, if relevant to troubleshooting_
- Pi network role: _static local IP / DHCP reservation_
- Internet connection: _ISP / plan tier, if relevant to interpreting speedtest results_

## Domain / DNS

- Domain: hv.io.vn, managed via Cloudflare
- Tunnel name: _fill in once created_
