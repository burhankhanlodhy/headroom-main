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
| horizon proxy    | Pi 5 | was already running |
| Postgres + API   | Pi 5 | deployed & verified (`/healthz`, signup + login over LAN) |
| Landing bundle   | PC   | built with `VITE_DASHBOARD_URL=http://192.168.0.64:8080` → `landingpage/dist` |
| Dashboard bundle | PC   | built with `VITE_API_URL=/api`, `VITE_LANDING_URL=http://192.168.0.64` → `dashboard/dist` |
| Caddy + bundles  | Pi 4 | **pending — needs one-time SSH key setup** |

## Finish the Pi 4 deployment

### Step 1 — one-time: let this PC manage Pi 4 (type the Pi 4 password once)

```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh raspberrypi4@192.168.0.64 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

(If that file doesn't exist, use `id_rsa.pub` — or generate a key first with
`ssh-keygen -t ed25519`.) Then say "continue" and the agent finishes the rest.

### Step 2 — ship the bundles (from the PC)

```powershell
ssh raspberrypi4@192.168.0.64 "mkdir -p /tmp/cs-landing /tmp/cs-dashboard"
scp -r landingpage\dist\* raspberrypi4@192.168.0.64:/tmp/cs-landing/
scp -r dashboard\dist\*  raspberrypi4@192.168.0.64:/tmp/cs-dashboard/
scp deploy\pi4-webtier\Caddyfile raspberrypi4@192.168.0.64:/tmp/cs-Caddyfile
```

### Step 3 — install & start Caddy (on Pi 4)

```bash
sudo apt update && sudo apt install -y caddy
sudo mkdir -p /var/www/contextshrink/landing /var/www/contextshrink/dashboard
sudo cp -r /tmp/cs-landing/*   /var/www/contextshrink/landing/
sudo cp -r /tmp/cs-dashboard/* /var/www/contextshrink/dashboard/
sudo cp /tmp/cs-Caddyfile      /etc/caddy/Caddyfile
sudo systemctl enable --now caddy
sudo systemctl reload caddy
```

(Debian 12 / Raspberry Pi OS Bookworm ships Caddy 2.6+; for the latest
version use the official cloudsmith repo instead.)

### Step 4 — verify (from the PC)

```
http://192.168.0.64            -> landing page
http://192.168.0.64:8080       -> dashboard (sign up! it hits the Pi 5 DB)
http://192.168.0.64:8080/api/healthz -> {"ok":true,...}
```

## Re-deploying new builds later

Rebuild with the same env vars (see "Status" above), re-run steps 2 + 3's
copy lines, `sudo systemctl reload caddy`. Consider a tiny script — it's
three commands.

## Domain day

Point `contextshrink.com` A record at Pi 4's public IP, `app.contextshrink.com`
at it too (or a VPS), swap the Caddyfile to the commented blocks in
`deploy/pi4-webtier/Caddyfile`, and rebuild both bundles with the HTTPS URLs.
Caddy handles certificates automatically. The API itself never needs to change.
