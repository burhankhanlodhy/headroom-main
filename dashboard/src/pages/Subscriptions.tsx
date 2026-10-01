import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowUpRight, Check, Sparkles } from "lucide-react";
import {
  Badge,
  Card,
  EASE,
  GhostButton,
  GradientButton,
  Modal,
  ProgressRing,
  SectionHeader,
} from "../components/ui";
import { PLANS, useAccount, type Plan } from "../lib/account";
import { useBillingEstimate } from "../lib/usage";
import { cn, fmtUsd } from "../lib/utils";

export default function Subscriptions() {
  const { plan, changePlan, user } = useAccount();
  const { estimate, error: estimateError, loading: estimateLoading } =
    useBillingEstimate();
  const current = PLANS.find((p) => p.id === plan)!;
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<Plan>(plan);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  function manage(next: Plan = plan) {
    setSelected(next);
    setError("");
    setNotice("");
    setOpen(true);
  }
  async function save() {
    if (saving) return;
    setSaving(true);
    setError("");
    try {
      await changePlan(selected);
      setOpen(false);
      setNotice(
        `Your subscription is now ${PLANS.find((p) => p.id === selected)!.name}.`,
      );
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Unable to change subscription",
      );
    } finally {
      setSaving(false);
    }
  }
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
                Horizon <span className="text-ember">{current.name}</span>
              </h2>
              <p className="mt-1.5 max-w-lg text-sm text-ink-3">
                {current.description}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {current.features.map((f) => (
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
                {current.name}
                <span className="text-base font-medium text-ink-3"> plan</span>
              </div>
              <GradientButton className="mt-4" onClick={() => manage()}>
                Manage billing <ArrowUpRight size={14} />
              </GradientButton>
            </div>
          </div>
        </Card>
      </motion.div>
      {notice && (
        <p role="status" className="text-sm text-sage">
          {notice}
        </p>
      )}

      <Card hairline className="p-6">
        <SectionHeader
          eyebrow="Billing cycle"
          title="Estimated bill"
          action={<Badge tone={estimateError ? "red" : estimate ? "green" : "slate"}>{estimateError ? "Unavailable" : estimate ? "Account estimate" : "Loading…"}</Badge>}
        />
        {estimate ? (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-lg border border-ink/10 bg-ink/5 p-4">
                <div className="text-xs text-ink-3">Est. savings this cycle</div>
                <div className="mt-1 font-display text-2xl font-bold text-ink">{fmtUsd(estimate.estimated_savings_usd)}</div>
              </div>
              <div className="rounded-lg border border-ink/10 bg-ink/5 p-4">
                <div className="text-xs text-ink-3">Current plan estimate · {current.name}</div>
                <div className="mt-1 font-display text-2xl font-bold text-ink">{fmtUsd(estimate.estimated_total_usd)}</div>
              </div>
              <div className="rounded-lg border border-ink/10 bg-ink/5 p-4">
                <div className="text-xs text-ink-3">Savings fee · Pro / Team</div>
                <div className="mt-1 font-display text-2xl font-bold text-ink">{fmtUsd(estimate.estimates.pro.savings_fee)}</div>
              </div>
              <div className="rounded-lg border border-ink/10 bg-ink/5 p-4">
                <div className="text-xs text-ink-3">Team seats · {estimate.seat_count} × $5</div>
                <div className="mt-1 font-display text-2xl font-bold text-ink">{fmtUsd(estimate.estimates.team.seat_fee)}</div>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-1 gap-2 text-sm text-ink-2 sm:grid-cols-3">
              {PLANS.map((p) => (
                <div key={p.id} className="flex items-center justify-between rounded-md border border-ink/10 px-3 py-2">
                  <span>Potential {p.name} bill</span>
                  <strong className="font-semibold text-ink">{fmtUsd(estimate.estimates[p.id].total)}</strong>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-ink-3">
              The 5% savings fee is waived when cycle savings are $20 or less. Above $20, it is 5% of the full estimated savings. Team also includes $5 per account seat each month. Estimates cover {new Date(estimate.period_start).toLocaleDateString()}–{new Date(estimate.period_end).toLocaleDateString()} and are billed at cycle end.
            </p>
          </>
        ) : (
          <p className="text-sm text-ink-3">{estimateError || (estimateLoading ? "Loading your account billing estimate…" : "Billing estimate unavailable.")}</p>
        )}
      </Card>

      {/* provider subscriptions */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {PLANS.map((s, i) => (
          <motion.div
            key={s.id}
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
                  {s.name.slice(0, 1)}
                </div>
                <Badge tone={s.id === plan ? "green" : "slate"}>
                  {s.id === plan
                    ? (user.subscription_status ?? "active")
                    : "available"}
                </Badge>
              </div>
              <div className="mt-4">
                <div className="text-sm font-semibold text-ink">
                  Horizon {s.name}
                </div>
                <div className="text-xs text-ink-3">{s.description}</div>
              </div>
              <div className="my-5 flex justify-center">
                <ProgressRing
                  key={`${s.id}-${plan}`}
                  pct={s.id === plan ? 100 : 0}
                  size={116}
                >
                  <div className="text-center">
                    <div className="font-display text-xl font-bold text-ink">
                      {s.name}
                    </div>
                    <div className="text-[9px] uppercase tracking-wider text-ink-3">
                      {s.id === plan ? "current" : "available"}
                    </div>
                  </div>
                </ProgressRing>
              </div>
              <div className="mt-auto flex items-center justify-between border-t border-ink/10 pt-4 text-xs text-ink-3">
                <span>
                  {s.id === "free" ? "Usage overview" : "Advanced Analytics"}
                </span>
                <button
                  onClick={() => manage(s.id)}
                  className="font-medium text-ember transition hover:text-ember-2"
                >
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
            action={<Badge tone="slate">0 payments</Badge>}
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
            <tr>
              <td colSpan={4} className="px-6 py-3.5 text-ink-3">
                No payments recorded. Plan selection does not collect payment; a
                payment processor is not connected.
              </td>
            </tr>
          </tbody>
        </table>
      </Card>

      <div className="flex justify-center">
        <GhostButton disabled className="text-ink-3">
          No invoices available
        </GhostButton>
      </div>
      <Modal
        open={open}
        onClose={() => {
          if (!saving) setOpen(false);
        }}
        title="Manage billing"
      >
        <p className="mb-4 text-sm text-ink-3">
          Free never requires a payment method. Upgrading to Pro or Team requires Stripe Checkout and a payment method. Paid checkout is not configured yet, so paid plan changes are unavailable until sandbox billing settings are added.
        </p>
        <label
          className="mb-2 block text-xs font-semibold text-ink-2"
          htmlFor="subscription-plan"
        >
          Subscription
        </label>
        <select
          id="subscription-plan"
          value={selected}
          disabled={saving}
          onChange={(e) => setSelected(e.target.value as Plan)}
          className="w-full rounded-lg border border-ink/20 bg-card px-3 py-2 text-sm text-ink"
        >
          {PLANS.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        {error && (
          <p role="alert" className="mt-3 text-sm text-ember">
            {error}
          </p>
        )}
        <div className="mt-5 flex justify-end gap-3">
          <GhostButton disabled={saving} onClick={() => setOpen(false)}>
            Cancel
          </GhostButton>
          <GradientButton
            disabled={
              saving ||
              (selected === plan && user.subscription_status === "active")
            }
            onClick={() => void save()}
          >
            {saving ? "Saving…" : "Save subscription"}
          </GradientButton>
        </div>
      </Modal>
    </div>
  );
}
