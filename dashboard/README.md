# ContextShrink — Dashboard

The app dashboard for ContextShrink (same answers, fewer tokens). Dark aurora
theme, glass panels, animated stats — built with Vite + React + TypeScript +
Tailwind v4 + Framer Motion + Recharts.

## Pages

| Route            | Page                                                    |
| ---------------- | ------------------------------------------------------- |
| `/`              | Profile — account hero, 14-day stats, recent sessions   |
| `/keys`          | API Keys — create, reveal, copy, revoke                 |
| `/usage`         | Usage — range toggle, traffic chart, model mix, funnel  |
| `/subscriptions` | Subscriptions — plan banner, quota rings, billing       |
| `/docs`          | Documentation — quickstarts, endpoints, wiring guide    |
| `/login`         | Sign in → redirects to the dashboard                    |
| `/signup`        | Create account → redirects to the dashboard             |
| `/signout`       | Sign out screen (clears the local session)              |

Auth is real: the dashboard talks to the control-plane API (`../api/`,
Postgres-backed) for signup, login, and sessions — see `src/lib/auth.ts` and
`src/lib/api.ts`. Point `VITE_API_URL` at the API (default
`http://127.0.0.1:8788`).

## Run

```powershell
cd dashboard
npm install
npm run dev        # http://127.0.0.1:5173
npm run build      # type-check + production bundle in dist/
```

## Cross-links with the landing page

`VITE_LANDING_URL` (default `http://127.0.0.1:5174`) is baked at build time
and drives the "Back to contextshrink.com" links on `/login` and `/signup`.
See `../landingpage/README.md` for the two-host deployment topology.

## Wiring live data

Usage metrics already flow through the control plane (`POST /ingest/usage` →
`usage_daily` → `GET /usage/summary`). The remaining dashboard pages read
from `src/data/mock.ts`, whose shapes mirror the API responses — swap the
mocks for fetches and the components keep working unchanged.
