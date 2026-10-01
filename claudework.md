# Claude work log

Session date: 2026-10-01. Summary of the review, deployment and email setup done for ContextShrink.
No credentials, tokens or passwords are recorded here.

## Current state

| Piece | Where | Status |
|---|---|---|
| Landing page | Pi 4 (Caddy `:80`) | Live at https://contextshrink.com |
| Customer dashboard | Pi 4 (Caddy `:8080`) | Live at https://app.contextshrink.com |
| Control-plane API | Pi 5 `:8788`, reached via Pi 4 `/api` | Healthy (`/api/healthz` returns ok) |
| Proxy + Horizon dashboard | Pi 5 | Running; account page fix not yet deployed (see below) |
| Public access | Cloudflare Tunnel `pi4-web` on Pi 4 | Healthy, no port forwarding |
| DNS / SSL | Cloudflare (free plan) | Domain active, HTTPS via Cloudflare certificate |
| Email | Cloudflare Email Routing | `support@contextshrink.com` forwards to the owner's inbox |

## What was done

1. **Code review** of the repo (control-plane API, dashboard, Caddy configs, proxy account middleware).
   Static review only: no tests were run and the Pis were not inspected. Findings are listed under "Deferred" below.
2. **Cloudflare DNS**: domain moved to Cloudflare nameservers and activated. Two leftover AWS `A` records from the registrar were deleted.
3. **Cloudflare Tunnel** `pi4-web` installed on Pi 4 as a systemd service (`cloudflared`). Published routes:
   - `contextshrink.com` -> `http://localhost:80`
   - `app.contextshrink.com` -> `http://localhost:8080`
   No Caddyfile change was needed.
4. **Bundles rebuilt and deployed** to Pi 4 with production URLs:
   - Landing: `VITE_DASHBOARD_URL=https://app.contextshrink.com`
   - Dashboard: `VITE_LANDING_URL=https://contextshrink.com`, `VITE_API_URL=/api`
   - This fixed "Back to contextshrink.com" on the login page, which had pointed to `http://127.0.0.1:5174`.
   - Previous site backed up on Pi 4 at `/var/backups/contextshrink/web-20261001-173559.tgz`.
   - Deployed over SSH using the PC's existing key (key-based login, no password).
5. **Code change**: `horizon/dashboard/templates/account_dashboard.html` had four hardcoded `http://192.168.0.64:8080/...` links. They are now relative (`/`, `/login?next=%2Fdashboard`, `/subscriptions`).
6. **Email**: Cloudflare Email Routing enabled with rule `support@` -> owner's inbox. The MX, SPF and DKIM records were verified live from public resolvers. The catch-all is disabled (mail to other addresses is dropped). A test from iCloud failed with "bare CR in DATA line" (an iCloud sending quirk, not a configuration problem); a test from another provider arrived.

## Rebuild and redeploy the Pi 4 web tier

Run from the project root on the PC (PowerShell). Requires the SSH key to be authorised on Pi 4.

```powershell
cd landingpage
$env:VITE_DASHBOARD_URL = "https://app.contextshrink.com"
npm run build

cd ..\dashboard
$env:VITE_LANDING_URL = "https://contextshrink.com"
$env:VITE_API_URL = "/api"
npm run build

cd ..
ssh raspberrypi4@192.168.0.64 "rm -rf /tmp/cs-landing /tmp/cs-dashboard && mkdir -p /tmp/cs-landing /tmp/cs-dashboard"
scp -r landingpage\dist\* raspberrypi4@192.168.0.64:/tmp/cs-landing/
scp -r dashboard\dist\* raspberrypi4@192.168.0.64:/tmp/cs-dashboard/
ssh raspberrypi4@192.168.0.64 "sudo rm -rf /var/www/contextshrink/landing/* /var/www/contextshrink/dashboard/* && sudo cp -r /tmp/cs-landing/* /var/www/contextshrink/landing/ && sudo cp -r /tmp/cs-dashboard/* /var/www/contextshrink/dashboard/"
```

Caddy serves from disk, so no reload is needed. Hard-refresh the browser afterwards.

## Pending / next steps

- **Rebuild the proxy image on Pi 5** so the `account_dashboard.html` link fix takes effect:
  `cd ~/horizon && docker compose build horizon-proxy && docker compose up -d horizon-proxy`
  Until then, Advanced Analytics redirects (logged-out or Free plan) still go to the old LAN address.
- **Stripe**: use `support@contextshrink.com` as the business email. The landing page needs a visible contact address plus Terms, Privacy and Refund pages for Stripe's review. Stripe keys belong in the API environment only (`STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`), never in frontend variables or Git.
- Optional: add a DMARC TXT record (`_dmarc`, `v=DMARC1; p=none; rua=mailto:support@contextshrink.com`).
- Optional: Gmail "Send mail as" for replying from `support@`, or move to a paid mailbox (Zoho Mail Lite / Google Workspace) when regular outbound mail is needed. The free Zoho business-domain plan was not available.

## Deferred (bug fixing comes after deploy testing)

Highest priority from the review:

1. Plain HTTP on the LAN carries passwords, session tokens and provider keys. Public traffic is now HTTPS through Cloudflare; the Pi 4 -> Pi 5 hop and any LAN clients are still HTTP.
2. Control-plane API is published on `0.0.0.0:8788` (Pi 5), exposing `/internal/*` to the LAN behind one static token. Bind to the Pi 5 LAN IP and firewall it (use the `DOCKER-USER` chain; Docker bypasses `ufw`).
3. argon2 hashing runs on the event loop in `api/main.py` (signup and login), and there is no rate limiting on `/auth/*`.
4. The proxy and the dashboard share one origin (`app.contextshrink.com`) and the session token is in `localStorage`. Consider a separate origin for the data plane, a CSP, and HttpOnly cookies.
5. Traffic through the Pi 5 gateway arrives as loopback and skips `HORIZON_PROXY_TOKEN`; only the Caddy allowlist and `AccountMiddleware` protect it. Add gateway tests for `/admin/*`, `/stats`, `/settings` and encoded-path variants.

Other items: a database write on every authenticated request and every proxy authorize call; per-event ownership query in ingest and unbounded integer fields; no purge of expired sessions; `period_source` reports "subscription" after the fallback to the calendar month (`api/main.py:120`); schema drift on `seat_count` CHECK; hardcoded legacy partitions through Nov 2026; API container runs as root with no healthcheck; rotate the Pi passwords and switch to SSH keys only.

## Notes

- The Pi passwords were shared in chat during this session and should be rotated.
- Untracked in git: `.agents/` and `skills-lock.json` (decide whether to commit or ignore).
