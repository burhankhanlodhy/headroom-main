import { lastDays, seeded } from "../lib/utils";

/**
 * Mock data layer. Shapes intentionally mirror what the Horizon proxy exposes
 * (`/stats`, `/stats-history`, `/metrics`) so this file can later be swapped
 * for real fetches without touching the components.
 */

export interface DayPoint {
  date: string;
  requests: number;
  tokensSaved: number;
  savingsUsd: number;
}

export interface ModelShare {
  name: string;
  share: number; // 0..1
  color: string;
}

export interface SessionRow {
  id: string;
  agent: "Claude Code" | "OpenCode" | "Codex" | "Cursor";
  requests: number;
  tokensSaved: number;
  minutes: number;
  active: boolean;
}

export interface ApiKey {
  id: string;
  name: string;
  masked: string;
  createdAt: string;
  lastUsed: string | null;
  requests: number;
  revoked: boolean;
}

export interface Subscription {
  provider: string;
  product: string;
  plan: string;
  status: "active" | "attention";
  usedPct: number;
  renews: string;
  accent: string; // gradient classes
}

export const profile = {
  name: "Burhan Khan",
  handle: "burhankhanlodhy",
  email: "burhan@horizon.dev",
  plan: "Horizon Pro",
  memberSince: "March 2025",
  timezone: "Europe/London",
  providers: [
    { name: "Anthropic", color: "#d97757", connected: true },
    { name: "OpenAI", color: "#10a37f", connected: true },
    { name: "GitHub Copilot", color: "#a371f7", connected: true },
  ],
};

/** Deterministic daily series for the last `n` days. */
export function dailySeries(n: number): DayPoint[] {
  const days = lastDays(n);
  return days.map((date, i) => {
    const rnd = seeded(date);
    const wave = 1 + 0.35 * Math.sin((i / n) * Math.PI * 3);
    const weekend = [0, 6].includes(new Date(date + "T00:00:00").getDay()) ? 0.55 : 1;
    const requests = Math.round((420 + rnd() * 520) * wave * weekend);
    const tokensSaved = Math.round(requests * (1650 + rnd() * 900));
    const savingsUsd = +(tokensSaved * 0.0000031 * (3 + rnd() * 2)).toFixed(2);
    return { date, requests, tokensSaved, savingsUsd };
  });
}

export function totals(series: DayPoint[]) {
  return series.reduce(
    (acc, d) => ({
      requests: acc.requests + d.requests,
      tokensSaved: acc.tokensSaved + d.tokensSaved,
      savingsUsd: +(acc.savingsUsd + d.savingsUsd).toFixed(2),
    }),
    { requests: 0, tokensSaved: 0, savingsUsd: 0 },
  );
}

export const modelShares: ModelShare[] = [
  { name: "claude-sonnet-4.5", share: 0.52, color: "#818cf8" },
  { name: "claude-haiku-4.5", share: 0.24, color: "#22d3ee" },
  { name: "gpt-4o", share: 0.15, color: "#a78bfa" },
  { name: "codex / other", share: 0.09, color: "#34d399" },
];

export const sessions: SessionRow[] = [
  { id: "hr_9f3a2c", agent: "Claude Code", requests: 412, tokensSaved: 986400, minutes: 74, active: true },
  { id: "hr_71b8de", agent: "OpenCode", requests: 233, tokensSaved: 512050, minutes: 41, active: true },
  { id: "hr_44c0a9", agent: "Claude Code", requests: 189, tokensSaved: 402310, minutes: 33, active: false },
  { id: "hr_e2d5f1", agent: "Cursor", requests: 96, tokensSaved: 158220, minutes: 18, active: false },
  { id: "hr_08a3b7", agent: "Codex", requests: 54, tokensSaved: 87640, minutes: 12, active: false },
];

export const initialKeys: ApiKey[] = [
  {
    id: "k_pi_main",
    name: "raspberrypi5-proxy",
    masked: "hz_live_A3f9XXXXXXXX7Qx2",
    createdAt: "Sep 12, 2026",
    lastUsed: "2 min ago",
    requests: 18402,
    revoked: false,
  },
  {
    id: "k_laptop",
    name: "work-laptop",
    masked: "hz_live_B7e1XXXXXXXX9Md4",
    createdAt: "Aug 30, 2026",
    lastUsed: "1 hr ago",
    requests: 6377,
    revoked: false,
  },
  {
    id: "k_ci",
    name: "ci-evals",
    masked: "hz_test_C2c8XXXXXXXX1Kp7",
    createdAt: "Aug 21, 2026",
    lastUsed: "3 days ago",
    requests: 1245,
    revoked: false,
  },
  {
    id: "k_old",
    name: "vps-trial",
    masked: "hz_live_D9a0XXXXXXXX4Rt8",
    createdAt: "Jul 02, 2026",
    lastUsed: "Jul 19, 2026",
    requests: 302,
    revoked: true,
  },
];

export const subscriptions: Subscription[] = [
  {
    provider: "Anthropic",
    product: "Claude",
    plan: "Max 5x",
    status: "active",
    usedPct: 64,
    renews: "Oct 14, 2026",
    accent: "from-[#d97757] to-[#b45309]",
  },
  {
    provider: "OpenAI",
    product: "ChatGPT / API",
    plan: "Plus + Tier 3",
    status: "active",
    usedPct: 31,
    renews: "Oct 03, 2026",
    accent: "from-[#10a37f] to-[#047857]",
  },
  {
    provider: "GitHub",
    product: "Copilot",
    plan: "Business",
    status: "attention",
    usedPct: 88,
    renews: "Nov 01, 2026",
    accent: "from-[#a371f7] to-[#6d28d9]",
  },
];

export const billingHistory = [
  { date: "Sep 14, 2026", item: "Horizon Pro - monthly", amount: "$20.00", status: "paid" },
  { date: "Aug 14, 2026", item: "Horizon Pro - monthly", amount: "$20.00", status: "paid" },
  { date: "Jul 14, 2026", item: "Horizon Pro - monthly", amount: "$20.00", status: "paid" },
];
