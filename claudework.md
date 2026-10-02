# Claude work log

Sessions: 2026-10-01 to 2026-10-02. Review, deployment, domain/email setup, the Free
compression cap, Stripe billing, the Windows desktop launcher and the move to
per-Pi Cloudflare Tunnels for ContextShrink.
No credentials, tokens or passwords are recorded here.

## Current state

| Piece | Where | Status |
|---|---|---|
| Landing page | Pi 4, static | https://contextshrink.com |
| Customer dashboard + Advanced Analytics page | Pi 4, static | https://app.contextshrink.com |
| Control-plane API | Pi 5, loopback `127.0.0.1:8788` | https://api.contextshrink.com via the Pi 5 tunnel and gateway |
| Horizon proxy | Pi 5, loopback `127.0.0.1:8787` | https://proxy.contextshrink.com via the Pi 5 tunnel and gateway |
| Pi 5 gateway (Caddy) | Pi 5, loopback `:8790` proxy, `:8791` API | Allowlists routes, strips edge headers |
| Public access | Cloudflare Tunnels `pi4-web` (Pi 4) and `pi5-proxy` (Pi 5) | No port forwarding; home IP never exposed |
| DNS / SSL | Cloudflare (free plan) | HTTPS via Cloudflare certificates |
| Email | Cloudflare Email Routing | `support@contextshrink.com` forwards to the owner's inbox |
| Billing | Stripe sandbox (test mode) | Pro checkout, webhooks, savings fee, unpaid-fee handling |
| Desktop launcher | Windows installer (Tauri) | Claude Code and OpenCode through the proxy |

## Topology

```
contextshrink.com, app.contextshrink.com -> Cloudflare -> tunnel pi4-web (Pi 4)  -> Caddy: static files only
api.contextshrink.com                    -> Cloudflare -> tunnel pi5-proxy (Pi 5) -> gateway 127.0.0.1:8791 -> API 127.0.0.1:8788
proxy.contextshrink.com                  -> Cloudflare -> tunnel pi5-proxy (Pi 5) -> gateway 127.0.0.1:8790 -> proxy 127.0.0.1:8787
```

- The Pi 4 never connects to the Pi 5. The dashboard and the Advanced Analytics page
  call `api.contextshrink.com` from the browser; the API's CORS allows
  `https://app.contextshrink.com` (plus localhost dev origins).
- Every ContextShrink service on the Pi 5 listens on loopback only (proxy 8787, API
  8788, gateway 8790/8791, Postgres 5432). Verified unreachable from the LAN.
- Tunnels must target the gateway listeners, never the API or proxy directly: the
  gateway hides `/internal/*`, `/docs`, `/openapi.json`, `/stats`, admin and settings,
  and strips Cloudflare/forwarding headers (`CDN-Loop`, `CF-*`, `Via`,
  `X-Forwarded-*`) before provider calls.
- `app.contextshrink.com/proxy`, `/api` and `/account-api` are retired and answer 404
  with a message naming the new hostname.
- The owner's personal services on the Pi 5 (Hermes Agent dashboard, a Python web
  server, xrdp, rpcbind, SSH) stay LAN-reachable by choice; they are not part of
  ContextShrink and are not internet-exposed.

## Pricing model (as implemented)

| | Free | Pro | Team |
|---|---|---|---|
| Card | No | Yes (Stripe Checkout) | Coming soon |
| Compression | Until $20 saved per UTC month, then passthrough | Unlimited | — |
| Fee | $0 | $0 base + 5% of the whole month's savings when they exceed $20 | — |
| Advanced Analytics | No | Yes | — |

## What was done

### Infrastructure (2026-10-01)

1. **Code review** of the repo. Remaining findings are under "Deferred".
2. **Cloudflare DNS** and tunnel `pi4-web` for the landing page and dashboard.
3. **Email**: Cloudflare Email Routing `support@` -> owner's inbox; MX/SPF/DKIM verified.
   iCloud test mail is rejected by Cloudflare ("bare CR in DATA line"); other providers work.

### Free compression cap

- `/internal/proxy/authorize` returns `plan` and `compression_allowed`; Free (and any
  non-active paid plan) compresses until `FREE_SAVINGS_CAP_USD` ($20) is saved in the
  current UTC month, then gets passthrough on every provider path. Responses carry
  `X-ContextShrink-Compression: paused`; the dashboard shows a notice from 75%.

### Stripe billing (option A: app computes the fee, Stripe invoices it)

- `api/billing.py`: Checkout ($0/month Pro, card saved), Customer Portal, Renew,
  invoices, and a signature-verified, deduplicated webhook. Plan state is written only
  by webhooks, which re-read the subscription from Stripe.
- Savings fee: at each renewal the ended period's savings are summed from
  `metrics.proxy_events`; above $20 a separate 5% invoice is finalized.
  `billing.savings_fees` plus idempotency keys prevent double charges.
- Unpaid fee: 7-day grace (`FEE_GRACE_DAYS`) with a banner, then a background check
  cancels the subscription (tagged `cancel_reason=unpaid_savings_fee`, no extra final
  fee) and the account drops to Free; upgrading is blocked until the fee is paid.
- Fixes found in live testing: StripeObject is not a dict in stripe-python 16;
  the Customer Portal schedules cancellations with `cancel_at`.
- Webhook endpoint: `https://api.contextshrink.com/stripe/webhook`
  (`we_1ULtUHELD2bV0TgCnEZ9t8Hc`, 10 events). Sandbox product `prod_VMcjRMhAtLT65O`,
  price lookup key `contextshrink_pro_monthly`, portal config `bpc_1ULtUGELD2bV0TgChfFP043K`.
- Scenarios tested on test clocks: upgrade, cancel/renew, $20.00 (no fee) vs $20.01
  ($1.00), declined fee with grace, grace expiry downgrade, fee paid. Test data removed;
  `test1@contextshrink.com` kept as a clean Free account.

### Desktop launcher (`desktop/`)

- Tauri app, Windows first, per-user NSIS installer (~65 MB). Ships only ContextShrink's
  own pieces: the app plus a frozen Horizon client (PyInstaller, Python runtime and
  package data included). Wrapped tools (Claude Code, OpenCode) are never bundled; the
  app detects them on PATH and links to their install pages.
- Sign-in with email/password creates a per-device proxy key (`Desktop: <PC name>`),
  stored via `horizon vault set --stdin` in Windows Credential Manager. Sign-out revokes
  it; a key revoked from the dashboard is replaced on next start.
- A background forwarder (`127.0.0.1:18788`) adds the device key to model calls and
  relays them to `proxy.contextshrink.com`. Requests rerouted by the OpenCode transport
  plugin that are not model calls (sign-in, catalogues) go straight to their real
  destination without the key.
- Launch opens a console in the chosen project folder running `horizon wrap ... --no-proxy`
  and `horizon unwrap` on exit:
  - Claude Code: `--no-mcp --code-memory none`; unwrap with `--keep-mcp` so the user's
    own MCP registrations are never removed.
  - OpenCode: `--no-mcp --no-serena` plus the bundled transport plugin, so custom
    providers (e.g. OneProvider) are routed too.
- Fixes found while testing: Tauri's `\\?\` paths broke `cmd.exe`; PyInstaller omitted
  the plugin `.js`; a frozen client must call itself in hooks (`resolve_horizon_command`);
  Cloudflare/forwarding headers made Cloudflare-fronted providers (chatgpt.com) refuse
  requests with an HTML 403. The proxy now logs a redacted preview of upstream error
  bodies.

### Per-Pi tunnels and LAN lockdown (2026-10-02)

- Tunnel `pi5-proxy` on the Pi 5 with hostnames `proxy` (-> 127.0.0.1:8790) and `api`
  (-> 127.0.0.1:8791). The proxy no longer depends on the Pi 4 or shares the dashboard
  origin.
- The Advanced Analytics page is shipped with the dashboard build
  (`dashboard/scripts/copy-analytics-page.mjs`) and served statically by the Pi 4.
- The Pi 4 Caddyfile serves static files only; the Pi 5 gateway LAN listener was
  removed and the API bound to loopback (`API_BIND=127.0.0.1`).

## Deploying

### Pi 5 (API, proxy, gateway)

```bash
cd ~/horizon && git pull --ff-only origin main
docker compose -f docker-compose.controlplane.yml up -d --build api
docker compose build horizon-proxy && docker compose up -d horizon-proxy
# The gateway Caddyfile is a single-file bind mount: recreate after a pull.
docker compose --profile dashboard up -d --force-recreate horizon-dashboard-gateway
```

### Pi 4 (landing, dashboard)

Build in **PowerShell**, not Git Bash (Git Bash rewrites `/api`-style values into
Windows paths). Check the bundle contains the expected URLs.

```powershell
cd dashboard
$env:VITE_LANDING_URL = "https://contextshrink.com"
$env:VITE_API_URL = "https://api.contextshrink.com"
npm run build   # also copies the Advanced Analytics page to dist\dashboard\
```

Upload `dist` to a temp directory on the Pi 4 and install with `sudo` (swap the
directory, keep the old one in `/var/backups/contextshrink/`). `sudo` on the Pi 4 needs
the owner's password, so the owner runs the final command.

### Desktop installer

```powershell
.\desktop\build-installer.ps1
```

Output: `desktop\app\src-tauri\target\release\bundle\nsis\ContextShrink_<version>_x64-setup.exe`.

## Pending / next steps

- **Before live payments**: live-mode Stripe keys, rerun `stripe_setup.py` in live mode,
  decide on **Stripe Tax**, and enable Stripe's failed-payment customer emails.
- Landing page: contact address plus Terms, Privacy and Refund pages for Stripe review.
- Delete `~/stripe_temp/keys.txt` on the Pi 5 (keys live in `.env`).
- Desktop app: Downloads page on the dashboard, hosting (GitHub Releases),
  auto-update, code signing (SmartScreen warns on the unsigned installer), more tools.
- **Team plan**: organisations, invitations, combined analytics, per-seat billing.
- Rotate the Pi password (it was shared in chat) and move both Pis to SSH key-only login.

## Deferred (from the original review)

Resolved: plain HTTP between the Pis (removed), API reachable on the LAN (loopback only),
proxy/dashboard shared origin (separate hostnames), period_source bug.

Still open:
1. argon2 hashing runs on the event loop (signup and login); no rate limiting on `/auth/*`.
2. The dashboard session token is in `localStorage`; consider a CSP and HttpOnly cookies.
3. Gateway route tests for `/admin/*`, `/stats`, `/settings` and encoded paths.
4. A database write on every authenticated request and proxy authorize call;
   per-event ownership query in ingest and unbounded integer fields; no purge of
   expired sessions; schema drift on the `seat_count` CHECK; hardcoded legacy partitions
   through Nov 2026; API container runs as root with no healthcheck.
