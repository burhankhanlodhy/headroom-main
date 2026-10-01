# Two-Pi Deployment — ContextShrink

```
            PC / agents (SSH tunnel)
                     |
                     v
+-------------------------------------------+
|  Pi 5  192.168.0.71        DATA PLANE     |
|  horizon proxy   127.0.0.1:8787           |
|  Postgres (docker) 127.0.0.1:5432         |
|  control API (docker) 0.0.0.0:8788        |
+-------------------------------------------+
                     ^  /api reverse_proxy
                     |
+-------------------------------------------+
|  Pi 4  192.168.0.64        WEB TIER       |
|  Caddy :80    -> landing (static)         |
|  Caddy :8080  -> dashboard (static)       |
|            /api -> 192.168.0.71:8788      |
+-------------------------------------------+
```

- **Pi 5** runs everything with state: the proxy, Postgres, and the control
  API. The API binds the LAN (`API_BIND=0.0.0.0` in `~/horizon/.env`) so only
  Caddy needs to reach it. Deployed and verified — see below.
- **Pi 4** is stateless: two static bundles served by Caddy. If it dies,
  redeploy in minutes; nothing is lost.

## Status

| Piece            | Host | Status |
| ---------------- | ---- | ------ |
| horizon proxy    | Pi 5 | loopback-only, with a LAN-scoped account-auth gateway |
| Postgres + API   | Pi 5 | deployed & verified (`/healthz`, signup + login over LAN on `:8788`) |
| Landing bundle   | PC   | built with `VITE_DASHBOARD_URL=http://192.168.0.64:8080` → `landingpage/dist` |
| Dashboard bundle | PC   | built with `VITE_API_URL=/api`, `VITE_LANDING_URL=http://192.168.0.64` → `dashboard/dist` |
| Caddy + bundles  | Pi 4 | **deployed & verified** — Caddy 2.6.2 on `:80`/`:8080`, enabled at boot |

**Live URLs:**

```
http://192.168.0.64            -> landing page
http://192.168.0.64:8080       -> dashboard (sign up! it hits the Pi 5 DB)
http://192.168.0.64:8080/api/healthz -> {"ok":true,...}
```

## Pi 4 deployment (done)

Bundles and Caddyfile live in `/var/www/contextshrink/{landing,dashboard}` and
`/etc/caddy/Caddyfile`; `caddy.service` is enabled (starts on boot).

### Rebuild & redeploy (from the PC)

```powershell
# rebuild the bundles with the env vars above, then:
ssh raspberrypi4@192.168.0.64 "mkdir -p /tmp/cs-landing /tmp/cs-dashboard"
scp -r landingpage\dist\* raspberrypi4@192.168.0.64:/tmp/cs-landing/
scp -r dashboard\dist\*  raspberrypi4@192.168.0.64:/tmp/cs-dashboard/
scp deploy\pi4-webtier\Caddyfile raspberrypi4@192.168.0.64:/tmp/cs-Caddyfile
ssh raspberrypi4@192.168.0.64 "sudo cp -r /tmp/cs-landing/* /var/www/contextshrink/landing/ && sudo cp -r /tmp/cs-dashboard/* /var/www/contextshrink/dashboard/ && sudo cp /tmp/cs-Caddyfile /etc/caddy/Caddyfile && sudo systemctl reload caddy"
```

### Advanced Analytics

The dashboard menu opens Horizon at `/dashboard` on the Pi 4 dashboard origin.
Pi 4 Caddy forwards only the Horizon UI and its read-only analytics paths to
Pi 5. A separate Caddy gateway on Pi 5 binds to `192.168.0.71:8787`, checks the
signed-in dashboard account against `/auth/me`, and forwards allowed requests
to Horizon on `127.0.0.1:8787`. The proxy data plane and its master token remain
private to Pi 5. The settings page is not exposed through this gateway.

The gateway is managed by the `horizon-dashboard-gateway` Compose service. It
uses the `dashboard` profile, so other installs keep the loopback-only default:

```bash
docker compose --profile dashboard up -d horizon-dashboard-gateway
```

## Domain day

Point `contextshrink.com` A record at Pi 4's public IP, `app.contextshrink.com`
at it too (or a VPS), swap the Caddyfile to the commented blocks in
`deploy/pi4-webtier/Caddyfile`, and rebuild both bundles with the HTTPS URLs.
Caddy handles certificates automatically. The API itself never needs to change.
