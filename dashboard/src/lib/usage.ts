import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, apiFetch } from "./api";

interface LedgerTotals {
  requests: number;
  tokens_saved: number;
  savings_usd: number;
  tokens_before: number;
  tokens_after: number;
}
interface UsageResponse {
  days: number;
  as_of: string;
  start: string;
  totals: LedgerTotals;
  previous: LedgerTotals;
  series: (LedgerTotals & { date: string })[];
  models: { name: string; requests: number }[];
  providers: { name: string }[];
  sessions: (LedgerTotals & {
    id: string;
    agent: string;
    minutes: number;
    started_at: string;
    last_activity: string;
  })[];
}
const colors = ["#c14d1b", "#5f7452", "#8b7f6f", "#4a4137"];
const mapped = (r?: LedgerTotals) => ({
  requests: Number(r?.requests ?? 0),
  tokensSaved: Number(r?.tokens_saved ?? 0),
  savingsUsd: Number(r?.savings_usd ?? 0),
  tokensBefore: Number(r?.tokens_before ?? 0),
  tokensAfter: Number(r?.tokens_after ?? 0),
});
export const pct = (current: number, previous: number) =>
  previous > 0 ? ((current - previous) / previous) * 100 : undefined;
export const compression = (t: {
  tokensBefore: number;
  tokensAfter: number;
}) =>
  t.tokensBefore > 0
    ? Math.max(0, ((t.tokensBefore - t.tokensAfter) / t.tokensBefore) * 100)
    : 0;

export function useUsage(days: number) {
  const [response, setResponse] = useState<UsageResponse | null>(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  useEffect(() => {
    const controller = new AbortController();
    let pending = false;
    setResponse(null);
    setError("");
    async function load() {
      if (pending) return;
      pending = true;
      try {
        const data = await apiFetch<UsageResponse>(
          `/usage/summary?days=${days}`,
          { signal: controller.signal },
        );
        if (!controller.signal.aborted) {
          setResponse(data);
          setError("");
        }
      } catch (e) {
        if (controller.signal.aborted) return;
        if (e instanceof ApiError && e.status === 401)
          navigate("/login", { replace: true });
        else
          setError(
            e instanceof Error ? e.message : "Unable to load account usage",
          );
      } finally {
        pending = false;
      }
    }
    void load();
    const timer = window.setInterval(() => {
      if (!document.hidden) void load();
    }, 10000);
    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, [days, navigate]);
  const data = response?.days === days ? response : null;
  return useMemo(() => {
    const t = mapped(data?.totals);
    const series = data
      ? Array.from({ length: days }, (_, i) => {
          const date = new Date(data.start);
          date.setUTCDate(date.getUTCDate() + i);
          const key = date.toISOString().slice(0, 10);
          return {
            date: key,
            ...mapped(data.series.find((row) => row.date === key)),
          };
        })
      : [];
    return {
      t,
      previous: mapped(data?.previous),
      series,
      pieData: (data?.models ?? []).map((m, i) => ({
        name: m.name,
        share: t.requests ? Number(m.requests) / t.requests : 0,
        color: colors[i % colors.length],
      })),
      providers: (data?.providers ?? []).map((p, i) => ({
        name: p.name,
        color: colors[i % colors.length],
      })),
      sessions: (data?.sessions ?? []).map((s) => ({
        id: s.id,
        agent: s.agent,
        requests: Number(s.requests),
        tokensSaved: Number(s.tokens_saved),
        minutes: Math.round(Number(s.minutes)),
        active: false,
      })),
      error,
      loaded: Boolean(data),
      loading: !data && !error,
    };
  }, [data, days, error]);
}
