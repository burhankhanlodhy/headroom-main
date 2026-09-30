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
          <div className="flex flex-wrap items-center gap-8">
            <div className="min-w-0 flex-1">
              <Badge tone="indigo" className="mb-3">
                <Sparkles size={11} /> current plan
              </Badge>
              <h2 className="font-display text-2xl font-bold text-ink">
                Horizon <span className="text-ember">Pro</span>
              </h2>
              <p className="mt-1.5 max-w-lg text-sm text-ink-3">
                Every compression feature unlocked, with priority routing and team
                sharing for your whole crew.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {FEATURES.map((f) => (
                  <span
                    key={f}
                    className="inline-flex items-center gap-1.5 rounded-full border border-ink/10 bg-ink/5 px-3 py-1 text-[11px] text-ink-2"
                  >
                    <Check size={11} className="text-sage" /> {f}
                  </span>
                ))}
              </div>
            </div>
            <div className="text-center">
              <div className="font-display text-4xl font-bold text-ink">
                $20<span className="text-base font-medium text-ink-3">/mo</span>
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
            <Card hairline className="flex h-full flex-col p-6">
              <div className="flex items-start justify-between">
                <div
                  className={cn(
                    "grid h-11 w-11 place-items-center rounded-lg bg-gradient-to-br font-display text-sm font-bold text-paper",
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
                <div className="text-sm font-semibold text-ink">{s.product}</div>
                <div className="text-xs text-ink-3">
                  {s.provider} · {s.plan}
                </div>
              </div>
              <div className="my-5 flex justify-center">
                <ProgressRing pct={s.usedPct} size={116}>
                  <div className="text-center">
                    <div className="font-display text-xl font-bold text-ink">{s.usedPct}%</div>
                    <div className="text-[9px] uppercase tracking-wider text-ink-3">used</div>
                  </div>
                </ProgressRing>
              </div>
              <div className="mt-auto flex items-center justify-between border-t border-ink/10 pt-4 text-xs text-ink-3">
                <span>renews {s.renews}</span>
                <button className="font-medium text-ember transition hover:text-ember-2">
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
            <tr className="border-y border-ink/10 text-[11px] uppercase tracking-wider text-ink-3">
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
                className="border-b border-ink/10 transition last:border-0 hover:bg-ink/5"
              >
                <td className="px-6 py-3.5 text-ink-3">{b.date}</td>
                <td className="py-3.5 text-ink-2">{b.item}</td>
                <td className="py-3.5 text-right font-semibold text-ink">{b.amount}</td>
                <td className="px-6 py-3.5 text-right">
                  <Badge tone="green">{b.status}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <div className="flex justify-center">
        <GhostButton className="text-ink-3">Download all invoices</GhostButton>
      </div>
    </div>
  );
}
