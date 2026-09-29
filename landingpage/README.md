# ContextShrink — Landing Page

The marketing site: hero with a live compression demo, feature grid,
how-it-works flow diagram, animated metrics band, pricing and FAQ. Same
aurora/glass design system as the dashboard.

## Run

```powershell
cd landingpage
npm install
npm run dev        # http://127.0.0.1:5174
npm run build      # static bundle in dist/
```

## Two-host deployment (landing ≠ dashboard)

Requirement: the landing page and the dashboard run on **different machines**
and are reached via different hostnames.

```
contextshrink.com            → Pi #2 (landing)      static files, nginx/Caddy
app.contextshrink.com        → Pi #1 (dashboard)    SPA + (future) API
```

### 1. Build with the right cross-links

The two apps link to each other. The URLs are baked at build time via env vars:

```powershell
# build the landing page, pointing CTAs at the dashboard host
cd landingpage
$env:VITE_DASHBOARD_URL = "https://app.contextshrink.com"
npm run build

# build the dashboard, pointing "Back to site" links at the landing host
cd ..\dashboard
$env:VITE_LANDING_URL = "https://contextshrink.com"
npm run build
```

Defaults (no env vars): landing → `http://127.0.0.1:5173`, dashboard →
`http://127.0.0.1:5174` — i.e. local dev just works.

### 2. Serve the landing bundle on Pi #2

`dist/` is fully static. Either:

**Caddy** (recommended — automatic HTTPS):

```
# /etc/caddy/Caddyfile on Pi #2
contextshrink.com {
    root * /var/www/contextshrink
    file_server
}
```

**nginx:**

```nginx
server {
    listen 80;
    server_name contextshrink.com;
    root /var/www/contextshrink;
    location / { try_files $uri $uri/ /index.html; }
}
```

### 3. Serve the dashboard on Pi #1

Same pattern under `app.contextshrink.com` (or keep it tunnel-only and point
the DNS record at a reverse proxy that forwards to the SSH tunnel / proxy
host). The dashboard is an SPA — make sure unknown paths fall back to
`index.html` (`try_files ... /index.html`).

### 4. DNS

Two `A` records at your registrar:

| Record                   | Points to |
| ------------------------ | --------- |
| `contextshrink.com`      | Pi #2 IP  |
| `app.contextshrink.com`  | Pi #1 IP  |

Caddy obtains certificates automatically for both once DNS resolves.
