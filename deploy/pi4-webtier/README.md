# Two-Pi Deployment — ContextShrink

```
                    Cloudflare (no port forwarding; home IP never exposed)
          ┌───────────────────────────┴───────────────────────────┐
  contextshrink.com, app.contextshrink.com        api.contextshrink.com, proxy.contextshrink.com
          │ tunnel "pi4-web"                               │ tunnel "pi5-proxy"
+---------v-------------------------+    +-----------------v------------------------------+
| Pi 4  192.168.0.64   WEB TIER     |    | Pi 5  192.168.0.71   DATA PLANE                |
| Caddy :80   -> landing (static)   |    | Caddy gateway (horizon-dashboard-gateway):     |
| Caddy :8080 -> dashboard (static) |    |   127.0.0.1:8791 api   -> public API routes    |
|   /dashboard -> Advanced Analytics|    |   127.0.0.1:8790 proxy -> provider operations  |
|   (static page)                   |    | control API (docker) 127.0.0.1:8788            |
|                                   |    | horizon proxy        127.0.0.1:8787            |
|                                   |    | Postgres (docker)    127.0.0.1:5432            |
+-----------------------------------+    +------------------------------------------------+
```

- **Pi 4** serves static files only and never connects to the Pi 5. The
  dashboard and the Advanced Analytics page call `https://api.contextshrink.com`
  from the browser (CORS allows `https://app.contextshrink.com`); tools and the
  desktop app use `https://proxy.contextshrink.com`.
- **Pi 5** runs everything with state. Every service listens on loopback; the
  only way in is its own Cloudflare Tunnel, which targets the gateway
  listeners, never the API or proxy directly. The gateway allowlists routes
  (no `/internal/*`, `/docs`, `/stats`, admin or settings) and strips
  Cloudflare/forwarding headers before provider calls.
- If the Pi 4 dies, the API and proxy keep working; redeploy the static
  bundles in minutes, nothing is lost.
- Desktop installers live in `/var/www/contextshrink/releases`, served at
  `/releases/` and listed on the dashboard's Downloads page from
  `releases/latest.json` (published by `desktop/publish-installer.ps1`).

## Build the bundles (PowerShell, not Git Bash)

Git Bash rewrites values like `/api` into Windows paths, so build in PowerShell.

```powershell
cd landingpage
$env:VITE_DASHBOARD_URL = "https://app.contextshrink.com"
npm run build

cd ..\dashboard
$env:VITE_LANDING_URL = "https://contextshrink.com"
$env:VITE_API_URL = "https://api.contextshrink.com"
npm run build   # also copies the Advanced Analytics page to dist\dashboard\
```

## Deploy to the Pi 4

Upload `dist` to a temp directory on the Pi 4 and install it with `sudo`
(swap the directory and keep the old one in `/var/backups/contextshrink/`).
`/etc/caddy/Caddyfile` comes from `deploy/pi4-webtier/Caddyfile`; validate it
with `caddy validate --adapter caddyfile` before `sudo systemctl reload caddy`.

## Pi 5 gateway

Managed by the `horizon-dashboard-gateway` Compose service (`dashboard`
profile), config in `deploy/pi5-webtier/Caddyfile`. The Caddyfile is a
single-file bind mount, so after `git pull` recreate the container:

```bash
docker compose --profile dashboard up -d --force-recreate horizon-dashboard-gateway
```
