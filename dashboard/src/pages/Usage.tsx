import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge, Card, SectionHeader, StatCard } from "../components/ui";
import { dailySeries, modelShares, sessions, totals } from "../data/mock";
import { cn, dayLabel, fmtCompact, fmtUsd } from "../lib/utils";

const RANGES = [7, 14, 30] as const;

function ChartTip({ active, payload }: { active?: boolean; payload?: any[] }) {
  if (!active || !payload?.length) return null;
  const first = payload[0];
  const title = first?.payload?.date
    ? dayLabel(first.payload.date)
    : String(first?.payload?.name ?? first?.name ?? "");
  return (
    <div className="glass rounded-xl px-3.5 py-2.5 text-xs">
      <div className="mb-1.5 font-semibold text-slate-200">{title}</div>
      {payload.map((p: any, i: number) => {
        const key = String(p.dataKey ?? p.name ?? "");
        const isShare = key === "share";
        const name = isShare
          ? String(p.payload?.name ?? "share")
          : key === "tokensSaved"
            ? "tokens saved"
            : key;
        const value = isShare
          ? `${Math.round((Number(p.value) || 0) * 100)}%`
          : fmtCompact(Number(p.value) || 0);
        const color = p.stroke ?? p.payload?.color ?? p.fill ?? "#818cf8";
        return (
          <div key={i} className="flex items-center gap-2 py-0.5">
            <span className="h-2 w-2 rounded-full" style={{ background: color }} />
            <span className="text-slate-400">{name}</span>
            <span className="ml-auto pl-4 font-semibold text-white">{value}</span>
          </div>
        );
      })}
    </div>
  );
}

function FunnelBar({
  label,
  sub,
  width,
  gradient,
  delay,
}: {
  label: string;
  sub: string;
  width: number;
  gradient: string;
  delay: number;
}) {
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between gap-4 text-xs">
        <span className="font-medium text-slate-300">{label}</span>
        <span className="truncate text-slate-500">{sub}</span>
      </div>
      <div className="h-9 overflow-hidden rounded-xl border border-white/5 bg-white/[0.03]">
        <motion.div
          className={cn("flex h-full items-center rounded-xl bg-gradient-to-r px-3", gradient)}
          initial={{ width: 0 }}
          whileInView={{ width: `${width}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1.3, ease: [0.22, 1, 0.36, 1], delay }}
        >
          <span className="whitespace-nowrap text-sm font-bold text-white">{width}%</span>
        </motion.div>
      </div>
    </div>
  );
}

export default function Usage() {
  const [range, setRange] = useState<(typeof RANGES)[number]>(14);
  const series = useMemo(() => dailySeries(range), [range]);
  const t = useMemo(() => totals(series), [series]);
  const prevHalf = useMemo(() => totals(series.slice(0, Math.floor(range / 2))), [series, range]);
  const pct = (a: number, b: number) => (b === 0 ? 0 : ((a - b) / b) * 100);

  const pieData = modelShares;

  return (
    <div className="flex flex-col gap-6">
      {/* range toggle */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="glass inline-flex rounded-xl p-1">
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={cn(
                "relative rounded-lg px-4 py-1.5 text-xs font-semibold transition",
                range === r ? "text-white" : "text-slate-400 hover:text-slate-200",
              )}
            >
              {range === r && (
                <motion.span
                  layoutId="range-pill"
                  className="absolute inset-0 rounded-lg bg-gradient-to-r from-indigo-500/60 to-violet-500/60"
                  transition={{ type: "spring", stiffness: 400, damping: 32 }}
                />
              )}
              <span className="relative z-10">{r}d</span>
            </button>
          ))}
        </div>
        <Badge tone="green">
          <span className="live-dot !h-1.5 !w-1.5" /> streaming live
        </Badge>
      </div>

      {/* stat row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label={`Requests · ${range}d`}
          value={t.requests}
          delta={pct(t.requests, prevHalf.requests)}
          spark={series.map((d) => d.requests)}
        />
        <StatCard
          label="Tokens saved"
          value={t.tokensSaved}
          format={fmtCompact}
          delta={pct(t.tokensSaved, prevHalf.tokensSaved)}
          spark={series.map((d) => d.tokensSaved)}
          color="#22d3ee"
        />
        <StatCard
          label="Est. savings"
          value={t.savingsUsd}
          format={fmtUsd}
          delta={pct(t.savingsUsd, prevHalf.savingsUsd)}
          spark={series.map((d) => d.savingsUsd)}
          color="#34d399"
        />
        <StatCard
          label="Avg saved / request"
          value={Math.round(t.tokensSaved / Math.max(1, t.requests))}
          format={fmtCompact}
          spark={series.map((d) => Math.round(d.tokensSaved / Math.max(1, d.requests)))}
          color="#a78bfa"
        />
      </div>

      {/* chart + donut */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.7fr_1fr]">
        <Card hairline className="p-6">
          <SectionHeader eyebrow="Traffic" title="Requests & tokens saved" />
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={series} margin={{ top: 8, right: 8, bottom: 0, left: -14 }}>
                <defs>
                  <linearGradient id="reqFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#818cf8" stopOpacity={0.45} />
                    <stop offset="100%" stopColor="#818cf8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="tokFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#22d3ee" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={dayLabel}
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  minTickGap={28}
                />
                <YAxis
                  yAxisId="req"
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v: number) => fmtCompact(v)}
                />
                <YAxis
                  yAxisId="tok"
                  orientation="right"
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v: number) => fmtCompact(v)}
                />
                <Tooltip content={<ChartTip />} cursor={{ stroke: "rgba(255,255,255,0.15)" }} />
                <Area
                  yAxisId="tok"
                  type="monotone"
                  dataKey="tokensSaved"
                  stroke="#22d3ee"
                  strokeWidth={2}
                  fill="url(#tokFill)"
                  animationDuration={1200}
                />
                <Area
                  yAxisId="req"
                  type="monotone"
                  dataKey="requests"
                  stroke="#818cf8"
                  strokeWidth={2.5}
                  fill="url(#reqFill)"
                  animationDuration={1400}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card hairline className="p-6">
          <SectionHeader eyebrow="Mix" title="Traffic by model" />
          <div className="relative mx-auto h-[210px] w-[210px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Tooltip content={<ChartTip />} />
                <Pie
                  data={pieData}
                  dataKey="share"
                  nameKey="name"
                  innerRadius={64}
                  outerRadius={92}
                  paddingAngle={4}
                  cornerRadius={6}
                  strokeWidth={0}
                  animationDuration={1300}
                >
                  {pieData.map((m) => (
                    <Cell key={m.name} fill={m.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
              <div>
                <div className="font-display text-xl font-bold text-white">
                  {fmtCompact(t.requests)}
                </div>
                <div className="text-[10px] uppercase tracking-wider text-slate-500">requests</div>
              </div>
            </div>
          </div>
          <div className="mt-4 flex flex-col gap-2.5">
            {modelShares.map((m) => (
              <div key={m.name} className="flex items-center gap-2.5 text-xs">
                <span className="h-2.5 w-2.5 rounded-[4px]" style={{ background: m.color }} />
                <span className="text-slate-300">{m.name}</span>
                <span className="ml-auto font-semibold text-white">{Math.round(m.share * 100)}%</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* funnel */}
      <Card className="p-6">
        <SectionHeader eyebrow="Savings" title="Where every request lands" />
        <div className="flex flex-col gap-4">
          <FunnelBar
            label="Original context"
            sub="what the model would have read"
            width={100}
            gradient="from-indigo-500/70 to-violet-500/40"
            delay={0}
          />
          <FunnelBar
            label="Delivered to model"
            sub={`${fmtCompact(t.tokensSaved)} tokens after compression`}
            width={36.2}
            gradient="from-cyan-500/70 to-sky-500/40"
            delay={0.15}
          />
          <FunnelBar
            label="Saved by Horizon"
            sub={`${fmtUsd(t.savingsUsd)} est. cost avoided`}
            width={63.8}
            gradient="from-emerald-500/70 to-teal-500/40"
            delay={0.3}
          />
        </div>
      </Card>

      {/* sessions table */}
      <Card className="overflow-hidden">
        <div className="px-6 pb-1 pt-6">
          <SectionHeader
            eyebrow="Sessions"
            title="Recent proxy sessions"
            action={<Badge tone="slate">{sessions.length} recent</Badge>}
          />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-y border-white/5 text-[11px] uppercase tracking-wider text-slate-500">
                <th className="px-6 py-3 font-medium">Session</th>
                <th className="py-3 font-medium">Agent</th>
                <th className="py-3 text-right font-medium">Requests</th>
                <th className="py-3 text-right font-medium">Tokens saved</th>
                <th className="px-6 py-3 text-right font-medium">Duration</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr
                  key={s.id}
                  className="border-b border-white/5 transition last:border-0 hover:bg-white/[0.03]"
                >
                  <td className="px-6 py-3.5 font-mono text-xs text-slate-400">{s.id}</td>
                  <td className="py-3.5">
                    <Badge tone={s.agent === "Claude Code" ? "indigo" : "slate"}>{s.agent}</Badge>
                  </td>
                  <td className="py-3.5 text-right tabular-nums text-slate-300">
                    {fmtCompact(s.requests)}
                  </td>
                  <td className="py-3.5 text-right font-semibold tabular-nums text-emerald-300">
                    {fmtCompact(s.tokensSaved)}
                  </td>
                  <td className="px-6 py-3.5 text-right text-slate-400">
                    {s.minutes}m
                    {s.active && (
                      <span className="live-dot ml-2 inline-block !h-1.5 !w-1.5 align-middle" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
