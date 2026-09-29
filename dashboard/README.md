# Horizon Dashboard

The modern dashboard for the Horizon proxy. Dark aurora theme, glass panels,
animated stats — built with Vite + React + TypeScript + Tailwind v4 +
Framer Motion + Recharts.

## Pages

| Route            | Page                                                    |
| ---------------- | ------------------------------------------------------- |
| `/`              | Profile — account hero, 14-day stats, recent sessions   |
| `/keys`          | API Keys — create, reveal, copy, revoke                 |
| `/usage`         | Usage — range toggle, traffic chart, model mix, funnel  |
| `/subscriptions` | Subscriptions — plan banner, quota rings, billing       |
| `/docs`          | Documentation — quickstarts, endpoints, wiring guide    |
| `/signout`       | Sign out screen                                         |

## Run

```powershell
cd dashboard
npm install
npm run dev        # http://127.0.0.1:5173
npm run build      # type-check + production bundle in dist/
```

## Wiring live data

Every page reads from `src/data/mock.ts`. The shapes intentionally mirror what
the proxy exposes, so going live is a one-file swap:

| Mock export      | Proxy source                          |
| ---------------- | ------------------------------------- |
| `dailySeries`    | `GET /stats-history` (daily buckets)  |
| `sessions`       | `GET /stats` (active sessions)        |
| `totals`         | `GET /stats-history` `.lifetime`      |
| `initialKeys`    | `horizon keys list` / keys store      |
| `subscriptions`  | subscription tracker (Copilot etc.)   |

Replace the mocks with fetches (the proxy binds to loopback, so the dashboard
can call it directly with no token) and the components keep working unchanged.
