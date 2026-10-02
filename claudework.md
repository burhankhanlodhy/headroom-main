# Claude work log

Sessions: 2026-10-01 to 2026-10-02. Review, deployment, domain/email setup, the Free
compression cap and Stripe billing for ContextShrink.
No credentials, tokens or passwords are recorded here.

## Current state

| Piece | Where | Status |
|---|---|---|
| Landing page | Pi 4 (Caddy `:80`) | Live at https://contextshrink.com |
| Customer dashboard | Pi 4 (Caddy `:8080`) | Live at https://app.contextshrink.com |
| Control-plane API | Pi 5 `:8788`, reached via Pi 4 `/api` | Healthy; Stripe billing live in **test mode** |
| Proxy + Horizon dashboard | Pi 5 | Running; Free compression cap enforced |
| Public access | Cloudflare Tunnel `pi4-web` on Pi 4 | Healthy, no port forwarding |
| DNS / SSL | Cloudflare (free plan) | Domain active, HTTPS via Cloudflare certificate |
| Email | Cloudflare Email Routing | `support@contextshrink.com` forwards to the owner's inbox |
| Billing | Stripe sandbox | Pro checkout, webhooks, savings fee, unpaid-fee handling |

## Pricing model (as implemented)

| | Free | Pro | Team |
|---|---|---|---|
| Card | No | Yes (Stripe Checkout) | Coming soon |
| Compression | Until $20 saved per UTC month, then passthrough | Unlimited | — |
| Fee | $0 | $0 base + 5% of the whole month's savings when they exceed $20 | — |
| Advanced Analytics | No | Yes | — |

## What was done

### Infrastructure (2026-10-01)

1. **Code review** of the repo. Findings are listed under "Deferred" below.
2. **Cloudflare DNS**: domain on Cloudflare nameservers; two leftover AWS `A` records deleted.
3. **Cloudflare Tunnel** `pi4-web` on Pi 4 (`cloudflared` systemd service):
   `contextshrink.com` -> `http://localhost:80`, `app.contextshrink.com` -> `http://localhost:8080`.
4. **Bundles rebuilt** with production URLs (fixed links that pointed to `127.0.0.1`).
5. **Horizon account page** links made relative instead of `http://192.168.0.64:8080/...`.
6. **Email**: Cloudflare Email Routing `support@` -> owner's inbox; MX/SPF/DKIM verified.
   iCloud test mail is rejected by Cloudflare ("bare CR in DATA line"); other providers work.

### Free compression cap

- `/internal/proxy/authorize` returns `plan` and `compression_allowed`. Free (and any
  non-active paid plan) may compress until `FREE_SAVINGS_CAP_USD` ($20) is saved in the
  current UTC month.
- The proxy treats a capped account as full passthrough in `_horizon_bypass_enabled`, so
  every provider path honours it; decisions are tagged `plan_cap_reached` and responses
  carry `X-ContextShrink-Compression: paused`.
- Dashboard notice from 75% of the cap and when paused.

### Stripe billing (option A: app computes the fee, Stripe invoices it)

- `api/billing.py`: `POST /billing/checkout` ($0/month Pro subscription, card saved),
  `POST /billing/portal`, `POST /billing/renew`, `GET /billing/invoices`,
  `POST /stripe/webhook` (signature-verified, deduplicated in `billing.stripe_events`).
- Plan state is written only by webhooks, which re-read the subscription from Stripe.
- **Savings fee**: on each renewal invoice the ended period's savings are summed from
  `metrics.proxy_events`; above $20 a separate invoice for 5% is finalized. When a
  subscription ends normally, the final partial period is billed the same way.
  `billing.savings_fees` (one row per account per period) plus idempotency keys prevent
  double charges.
- **Cancellation** via the Customer Portal (at period end, recorded from `cancel_at`);
  **Renew Pro** undoes it from the dashboard.
- **Unpaid fee**: 7-day grace (`FEE_GRACE_DAYS`) with a "payment failed" banner; after
  that a background check (every 10 min) cancels the Stripe subscription, tagged
  `cancel_reason=unpaid_savings_fee` so no extra final fee is billed, and the account
  drops to Free. Upgrading is blocked until the fee is paid; paying clears the banner.
- `api/stripe_setup.py` creates the Pro product/price, portal settings and the webhook
  endpoint idempotently. The webhook secret was piped straight into the Pi 5 `.env`.
- Stripe sandbox objects: product `prod_VMcjRMhAtLT65O`, price lookup key
  `contextshrink_pro_monthly`, portal config `bpc_1ULtUGELD2bV0TgChfFP043K`,
  webhook endpoint `we_1ULtUHELD2bV0TgCnEZ9t8Hc` -> `https://app.contextshrink.com/api/stripe/webhook`.

### Billing scenarios tested live (sandbox, test clocks)

| Scenario | Result |
|---|---|
| Upgrade via Checkout | Pro granted by webhook |
| Cancel at period end, then renew | End date shown; renew clears it |
| $20.00 savings | No fee invoice |
| $20.01 savings | $1.00 invoice, paid |
| Fee declined | 7-day grace with banner, account stays Pro |
| Grace expired | Subscription cancelled, account Free, upgrade blocked, no extra fee |
| Fee paid | Banner cleared, upgrade unblocked |

All test clocks and test data were removed afterwards. The `test1@contextshrink.com`
account was kept as a clean Free account for future testing.

Tests: `api/tests/test_billing.py` (29 tests, run with the API requirements installed:
`python -m pytest api/tests`) and `tests/test_account_compression_cap.py` (proxy cap).

## Deploying

### Pi 5 (API and proxy)

```bash
cd ~/horizon && git pull --ff-only origin main
docker compose -f docker-compose.controlplane.yml up -d --build api   # control-plane API
docker compose build horizon-proxy && docker compose up -d horizon-proxy   # proxy
```

The API applies `api/schema.sql` on startup (idempotent migrations).

### Pi 4 (dashboard / landing)

Build in **PowerShell**, not Git Bash: Git Bash rewrites `VITE_API_URL=/api` into
`C:/Program Files/Git/api`, which breaks every API call. Check the bundle contains `"/api"`.

```powershell
cd dashboard
$env:VITE_LANDING_URL = "https://contextshrink.com"
$env:VITE_API_URL = "/api"
npm run build
```

Upload `dist/` to a temp directory on Pi 4, point `SRC=` in `/tmp/cs-deploy-dashboard.sh`
at it, then run (sudo prompts for the Pi password):

```powershell
ssh -t raspberrypi4@192.168.0.64 /tmp/cs-deploy-dashboard.sh
```

The script swaps the new build into `/var/www/contextshrink/dashboard` and keeps the old
one in `/var/backups/contextshrink/`. Landing builds use
`VITE_DASHBOARD_URL=https://app.contextshrink.com`.

## Pending / next steps

- **Before live payments**: create live-mode keys, rerun `stripe_setup.py` in live mode,
  and review **Stripe Tax** (no tax is collected until registrations exist).
- Stripe dashboard settings (owner's choice): customer emails for failed payments
  (Settings -> Billing -> Subscriptions and emails) and Smart Retries.
- Landing page needs a visible contact address plus Terms, Privacy and Refund pages for
  Stripe's account review.
- Delete `~/stripe_temp/keys.txt` on Pi 5 now that the keys live in `.env`.
- **Team plan**: organisations, invitations, combined analytics and per-seat billing.
- Optional: DMARC record; a real mailbox (Zoho Mail Lite / Google Workspace) for outbound mail.
- Optional: a narrow passwordless sudo rule on Pi 4 for the deploy script.

## Deferred (bug fixing comes after deploy testing)

1. The Pi 4 -> Pi 5 hop and any LAN clients are still plain HTTP.
2. Control-plane API is published on `0.0.0.0:8788` (Pi 5), exposing `/internal/*` to the
   LAN behind one static token. Bind to the Pi 5 LAN IP and firewall it (`DOCKER-USER`
   chain; Docker bypasses `ufw`).
3. argon2 hashing runs on the event loop (signup and login); no rate limiting on `/auth/*`.
4. Proxy and dashboard share one origin and the session token is in `localStorage`.
   Consider a separate data-plane origin, a CSP and HttpOnly cookies.
5. Traffic through the Pi 5 gateway arrives as loopback and skips `HORIZON_PROXY_TOKEN`;
   add gateway tests for `/admin/*`, `/stats`, `/settings` and encoded paths.

Other items: a database write on every authenticated request and proxy authorize call;
per-event ownership query in ingest and unbounded integer fields; no purge of expired
sessions; schema drift on the `seat_count` CHECK; hardcoded legacy partitions through
Nov 2026; API container runs as root with no healthcheck.

## Notes

- The Pi password was shared in chat several times and should be rotated; switch both
  Pis to SSH key-only login.
