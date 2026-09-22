# Traefik Reverse Proxy Setup Guide

This guide explains how to set up Traefik as a reverse proxy for your services (including `status`), with automatic HTTPS certificate generation via Let's Encrypt.

## Architecture Overview

```text
               Internet / LAN
                     │
          ┌──────────┴──────────┐
          │     Port 80 / 443   │
          ▼                     ▼
┌──────────────────────────────────────┐
│           Traefik Proxy              │
│       (examples/traefik/compose)     │
└──────────────────┬───────────────────┘
                   │  Docker Network: 'traefik-net'
                   ▼
┌──────────────────────────────────────┐
│           Status Service             │
│     (docker-compose.traefik.yml)     │
│             Port 8000                │
└──────────────────────────────────────┘
```

## Step 1: Prepare the Traefik Directory and Permissions

1. Choose a folder for Traefik (e.g. `~/traefik` or `/srv/traefik`):
   ```bash
   mkdir -p ~/traefik/letsencrypt
   cd ~/traefik
   ```

2. **Crucial Permissions:** Traefik requires strict `600` permissions on the `acme.json` file where certificates are saved, or it will refuse to start:
   ```bash
   touch letsencrypt/acme.json
   chmod 600 letsencrypt/acme.json
   chmod 600 letsencrypt
   ```

3. Copy `examples/traefik/docker-compose.yml` into your `~/traefik/` directory.

4. Open `docker-compose.yml` and replace:
   ```yaml
   - "--certificatesresolvers.letsencrypt.acme.email=you@example.com"
   ```
   with your real email address. Let's Encrypt uses this email for urgent renewal and security notifications.

## Step 2: Start Traefik

Start the Traefik container:
```bash
docker compose up -d
```

This creates the shared Docker network `traefik-net` and binds ports 80 and 443 on the host.

## Step 3: Deploy the Status Service Behind Traefik

In your `status` repository directory:

1. Inspect `docker-compose.traefik.yml`. Notice:
   - **No host port mapping:** Traefik forwards traffic internally across `traefik-net` to port 8000, eliminating port 80 conflicts.
   - **Network:** Connected to `traefik-net` (`external: true`).
   - **Host Rule:** Replace `rk3229.hv.io.vn` with your actual Fully Qualified Domain Name (FQDN).

2. Start the status service:
   ```bash
   docker compose -f docker-compose.traefik.yml up -d
   ```

3. Visit your status page:
   ```text
   https://<your-fqdn>/status/
   ```

---

## Important Configuration Notes

### 1. DNS Resolution & Let's Encrypt Requirements
- **Public FQDN:** For Let's Encrypt TLS challenge to succeed, your domain (e.g. `rk3229.hv.io.vn`) must resolve to your host's public IP address so Let's Encrypt servers can reach it over port 80/443.
- **Localhost and LAN hostnames:** Let's Encrypt **cannot** issue certificates for bare hostnames (e.g. `http://rk3229` or `http://localhost`). If you want local access without SSL warnings alongside your public domain:
  - Keep the public router with `certresolver=letsencrypt` on `websecure` (HTTPS).
  - Add a second local router on `web` (HTTP) without `tls.certresolver` for local/LAN hostnames.

### 2. PathPrefix and Subpath Routing (`stripprefix`)
- Most web applications only run at the root path (`/`) and break if placed behind `/status`.
- **Status is designed for dual routing:** It natively serves dashboard and API routes under both `/` and `/status` (and `/status/`).
- Therefore, the `stripprefix` middleware is **not required**.
- If you prefer stripping `/status` before forwarding to the container, the status service will still work because it also handles `/` directly.

### 3. Traefik Dashboard Security
- The Traefik dashboard is disabled by default in `examples/traefik/docker-compose.yml`.
- **Security Warning:** Never set `--api.insecure=true` on a server exposed to the public internet!
- If you wish to enable the Traefik dashboard:
  - Expose it via an authenticated router with Traefik's `basicauth` middleware or forward-auth rather than `--api.insecure`.
