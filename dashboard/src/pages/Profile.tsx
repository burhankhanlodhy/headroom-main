import { motion } from "framer-motion";
import { CalendarDays, Clock, Mail, Pencil, UserPlus } from "lucide-react";
import {
  Badge,
  Card,
  CopyButton,
  EASE,
  GhostButton,
  GradientButton,
  SectionHeader,
  StatCard,
} from "../components/ui";
import { dailySeries, profile, sessions, totals } from "../data/mock";
import { cn, fmtCompact, fmtUsd } from "../lib/utils";

const series = dailySeries(14);
const t = totals(series);
const prevWeek = totals(series.slice(0, 7));
const pct = (a: number, b: number) => (b === 0 ? 0 : ((a - b) / b) * 100);

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
};
const item = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: EASE } },
};

export default function Profile() {
  return (
    <motion.div variants={container} initial="hidden" animate="show" className="flex flex-col gap-6">
      {/* hero */}
      <motion.div variants={item}>
        <Card hairline className="glass-hover relative overflow-hidden p-7">
          <div className="pointer-events-none absolute -right-24 -top-28 h-72 w-72 rounded-full bg-indigo-500/25 blur-3xl" />
          <div className="flex flex-wrap items-center gap-6">
            <div className="relative h-20 w-20 shrink-0">
              <div className="absolute -inset-1 rounded-full bg-[conic-gradient(from_120deg,#6366f1,#8b5cf6,#22d3ee,#6366f1)] opacity-70 blur-[6px]" />
              <div className="relative grid h-full w-full place-items-center rounded-full border border-white/15 bg-ink-900 font-display text-2xl font-bold text-white">
                BK
              </div>
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="font-display text-2xl font-bold text-white">{profile.name}</h2>
                <Badge tone="indigo">✦ {profile.plan}</Badge>
              </div>
              <div className="mt-1.5 flex items-center gap-1.5 text-sm text-slate-400">
                <Mail size={13} /> {profile.email}
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-slate-500">
                <span className="inline-flex items-center gap-1.5">
                  <CalendarDays size={12} /> Member since {profile.memberSince}
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <Clock size={12} /> {profile.timezone}
                </span>
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-4">
                {profile.providers.map((p) => (
                  <span
                    key={p.name}
                    className="inline-flex items-center gap-1.5 text-xs text-slate-300"
                  >
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ background: p.color, boxShadow: `0 0 8px 1px ${p.color}66` }}
                    />
                    {p.name}
                  </span>
                ))}
              </div>
            </div>
            <div className="ml-auto flex gap-3">
              <GhostButton>
                <Pencil size={14} /> Edit profile
              </GhostButton>
              <GradientButton>
                <UserPlus size={14} /> Invite teammate
              </GradientButton>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Requests · 14d"
          value={t.requests}
          delta={pct(t.requests, prevWeek.requests)}
          spark={series.map((d) => d.requests)}
        />
        <StatCard
          label="Tokens saved"
          value={t.tokensSaved}
          format={fmtCompact}
          delta={pct(t.tokensSaved, prevWeek.tokensSaved)}
          spark={series.map((d) => d.tokensSaved)}
          color="#22d3ee"
        />
        <StatCard
          label="Est. savings"
          value={t.savingsUsd}
          format={fmtUsd}
          delta={pct(t.savingsUsd, prevWeek.savingsUsd)}
          spark={series.map((d) => d.savingsUsd)}
          color="#34d399"
        />
        <StatCard
          label="Avg compression"
          value={63.8}
          format={(v) => `${v.toFixed(1)}%`}
          delta={1.4}
          spark={[58, 60, 59, 62, 61, 63, 62, 64, 63, 65, 64, 63, 64, 64]}
          color="#a78bfa"
        />
      </div>

      {/* sessions + account */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.6fr_1fr]">
        <motion.div variants={item} className="min-w-0">
          <Card className="h-full p-6">
            <SectionHeader
              eyebrow="Activity"
              title="Recent sessions"
              action={
                <Badge tone="green">
                  <span className="live-dot !h-1.5 !w-1.5" /> 2 live
                </Badge>
              }
            />
            <div className="flex flex-col gap-2.5">
              {sessions.map((s, i) => (
                <motion.div
                  key={s.id}
                  initial={{ opacity: 0, x: -14 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.15 + i * 0.06, duration: 0.45, ease: EASE }}
                  className="flex items-center gap-4 rounded-xl border border-white/5 bg-white/[0.03] px-4 py-3"
                >
                  <span
                    className={cn(
                      "h-2 w-2 shrink-0 rounded-full",
                      s.active
                        ? "bg-emerald-400 shadow-[0_0_10px_2px_rgba(52,211,153,0.6)]"
                        : "bg-slate-600",
                    )}
                  />
                  <div className="w-24 shrink-0 font-mono text-xs text-slate-400">{s.id}</div>
                  <Badge tone={s.agent === "Claude Code" ? "indigo" : "slate"}>{s.agent}</Badge>
                  <div className="ml-auto flex items-center gap-5 text-right">
                    <div>
                      <div className="text-sm font-semibold text-white">
                        {fmtCompact(s.requests)}
                      </div>
                      <div className="text-[10px] text-slate-500">requests</div>
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-emerald-300">
                        {fmtCompact(s.tokensSaved)}
                      </div>
                      <div className="text-[10px] text-slate-500">tokens saved</div>
                    </div>
                    <div className="w-10 text-right text-xs text-slate-500">{s.minutes}m</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </Card>
        </motion.div>

        <motion.div variants={item}>
          <Card className="h-full p-6">
            <SectionHeader eyebrow="Account" title="Details" />
            <dl className="space-y-4 text-sm">
              <div className="flex items-center justify-between gap-3 border-b border-white/5 pb-4">
                <dt className="text-slate-400">Username</dt>
                <dd className="font-mono text-xs text-slate-200">{profile.handle}</dd>
              </div>
              <div className="flex items-center justify-between gap-3 border-b border-white/5 pb-4">
                <dt className="text-slate-400">Dashboard</dt>
                <dd>
                  <CopyButton text="http://127.0.0.1:18787/dashboard" label="127.0.0.1:18787" />
                </dd>
              </div>
              <div className="flex items-center justify-between gap-3 border-b border-white/5 pb-4">
                <dt className="text-slate-400">Timezone</dt>
                <dd className="text-slate-200">{profile.timezone}</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-400">Plan</dt>
                <dd>
                  <Badge tone="indigo">{profile.plan}</Badge>
                </dd>
              </div>
            </dl>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}
