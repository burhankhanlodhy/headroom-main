import { motion } from "framer-motion";
import { ArrowUpRight, Check, Sparkles } from "lucide-react";
import {
  Badge,
  Card,
  EASE,
  GhostButton,
  GradientButton,
  ProgressRing,
  SectionHeader,
} from "../components/ui";
import { billingHistory, subscriptions } from "../data/mock";
import { cn } from "../lib/utils";

const FEATURES = [
  "Unlimited compression",
  "All providers",
  "Priority routing",
  "Team seats",
  "Audit log",
];

export default function Subscriptions() {
  return (
    <div className="flex flex-col gap-6">
      {/* plan banner */}
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: EASE }}
      >
        <Card hairline className="relative overflow-hidden p-7">
          <div className="pointer-events-none absolute -left-20 -top-24 h-64 w-64 rounded-full bg-violet-500/20 blur-3xl" />
          <div className="flex flex-wrap items-center gap-8">
            <div className="min-w-0 flex-1">
              <Badge tone="indigo" className="mb-3">
                <Sparkles size={11} /> current plan
              </Badge>
              <h2 className="font-display text-2xl font-bold text-white">
                Horizon <span className="text-gradient">Pro</span>
              </h2>
              <p className="mt-1.5 max-w-lg text-sm text-slate-400">
                Every compression feature unlocked, with priority routing and team
                sharing for your whole crew.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {FEATURES.map((f) => (
                  <span
                    key={f}
                    className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] text-slate-300"
                  >
                    <Check size={11} className="text-emerald-300" /> {f}
                  </span>
                ))}
              </div>
            </div>
            <div className="text-center">
              <div className="font-display text-4xl font-bold text-white">
                $20<span className="text-base font-medium text-slate-400">/mo</span>
              </div>
              <GradientButton className="mt-4">
                Manage billing <ArrowUpRight size={14} />
              </GradientButton>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* provider subscriptions */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {subscriptions.map((s, i) => (
          <motion.div
            key={s.provider}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: EASE, delay: 0.1 + i * 0.09 }}
          >
            <Card hairline className="glass-hover flex h-full flex-col p-6">
              <div className="flex items-start justify-between">
                <div
                  className={cn(
                    "grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br font-display text-sm font-bold text-white",
                    s.accent,
                  )}
                >
                  {s.provider.slice(0, 1)}
                </div>
                <Badge tone={s.status === "active" ? "green" : "amber"}>
                  {s.status === "active" ? "active" : "quota high"}
                </Badge>
              </div>
              <div className="mt-4">
                <div className="text-sm font-semibold text-white">{s.product}</div>
                <div className="text-xs text-slate-400">
                  {s.provider} · {s.plan}
                </div>
              </div>
              <div className="my-5 flex justify-center">
                <ProgressRing pct={s.usedPct} size={116}>
                  <div className="text-center">
                    <div className="font-display text-xl font-bold text-white">{s.usedPct}%</div>
                    <div className="text-[9px] uppercase tracking-wider text-slate-500">used</div>
                  </div>
                </ProgressRing>
              </div>
              <div className="mt-auto flex items-center justify-between border-t border-white/5 pt-4 text-xs text-slate-500">
                <span>renews {s.renews}</span>
                <button className="font-medium text-indigo-300 transition hover:text-indigo-200">
                  Manage →
                </button>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* billing history */}
      <Card className="overflow-hidden">
        <div className="px-6 pt-6">
          <SectionHeader
            eyebrow="Billing"
            title="Payment history"
            action={<Badge tone="slate">last 3</Badge>}
          />
        </div>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-y border-white/5 text-[11px] uppercase tracking-wider text-slate-500">
              <th className="px-6 py-3 font-medium">Date</th>
              <th className="py-3 font-medium">Item</th>
              <th className="py-3 text-right font-medium">Amount</th>
              <th className="px-6 py-3 text-right font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {billingHistory.map((b) => (
              <tr
                key={b.date}
                className="border-b border-white/5 transition last:border-0 hover:bg-white/[0.03]"
              >
                <td className="px-6 py-3.5 text-slate-400">{b.date}</td>
                <td className="py-3.5 text-slate-200">{b.item}</td>
                <td className="py-3.5 text-right font-semibold text-white">{b.amount}</td>
                <td className="px-6 py-3.5 text-right">
                  <Badge tone="green">{b.status}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <div className="flex justify-center">
        <GhostButton className="text-slate-400">Download all invoices</GhostButton>
      </div>
    </div>
  );
}
