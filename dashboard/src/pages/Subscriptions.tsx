import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
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
import {
  openPortal,
  renewSubscription,
  startCheckout,
  useBilling,
} from "../lib/billing";
import { useBillingEstimate } from "../lib/usage";
import { cn, fmtUsd } from "../lib/utils";

export default function Subscriptions() {
  const { plan, changePlan, reloadAccount, user } = useAccount();
  const { estimate, error: estimateError, loading: estimateLoading } =
    useBillingEstimate();
  const { info, invoices, reload: reloadBilling } = useBilling();
  const [params, setParams] = useSearchParams();
  const current = PLANS.find((p) => p.id === plan)!;
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<Plan>(plan);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  // Returning from Stripe Checkout: Pro is granted by the webhook, so poll
  // briefly until the account reflects it.
  const checkout = params.get("checkout");
  useEffect(() => {
    if (!checkout) return;
    setParams({}, { replace: true });
    if (checkout !== "success") {
      setNotice("Checkout cancelled. Your plan has not changed.");
      return;
    }
    setNotice("Payment method saved. Activating Pro…");
    let cancelled = false;
    void (async () => {
      for (let attempt = 0; attempt < 20 && !cancelled; attempt++) {
        const fresh = await reloadAccount().catch(() => null);
        if (fresh?.plan === "pro") {
          setNotice("You're on Pro: unlimited compression is active.");
          void reloadBilling();
          return;
        }
        await new Promise((r) => setTimeout(r, 3000));
      }
      if (!cancelled)
        setNotice(
          "Your payment method is saved. Pro activation is taking longer than usual; refresh in a minute.",
        );
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [checkout]);

  function manage(next: Plan = plan) {
    setSelected(next);
    setError("");
    setNotice("");
    setOpen(true);
  }
  const cancelDate = info?.cancel_at_period_end
    ? (info.cancel_at ?? info.current_period_end)
    : null;
  const cancelsOn = cancelDate
    ? new Date(cancelDate).toLocaleDateString()
    : null;
  // An unpaid savings fee must be paid before upgrading again.
  const unpaidFee = estimate?.payment_issue ?? null;
  const upgradeBlocked = plan !== "pro" && Boolean(unpaidFee);
  const upgrading = selected === "pro" && plan !== "pro" && !upgradeBlocked;
  const renewing = selected === plan && plan !== "free" && Boolean(cancelsOn);
  const cancelling =
    selected === "free" && Boolean(info?.has_subscription) && !cancelsOn;
  async function renew() {
    if (saving) return;
    setSaving(true);
    setError("");
    try {
      await renewSubscription();
      await reloadBilling();
      setOpen(false);
      setNotice(`${current.name} renewed. It will keep renewing each month.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to renew");
    } finally {
      setSaving(false);
    }
  }
  async function portal() {
    setError("");
    try {
      await openPortal();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to open billing");
    }
  }
  async function save() {
    if (renewing) return renew();
    if (saving) return;
    setSaving(true);
    setError("");
    try {
      if (selected === "team") {
        setError("Team is coming soon.");
        return;
      }
      if (selected === "free" && cancelsOn) {
        setError(`Already cancelled: ${current.name} ends on ${cancelsOn}.`);
        return;
      }
      if (upgrading) {
        await startCheckout("pro"); // leaves the page
        return;
      }
      if (cancelling) {
        await openPortal(); // cancellation bills the final savings fee
        return;
      }
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
              {cancelsOn && (
                <p className="mt-2 text-sm text-ember">
                  {current.name} ends on {cancelsOn}. Your final savings fee is
                  billed then.{" "}
                  <button
                    onClick={() => void renew()}
                    disabled={saving}
                    className="font-semibold underline underline-offset-2 hover:text-ember-2 disabled:opacity-60"
                  >
                    {saving ? "Renewing…" : `Renew ${current.name}`}
                  </button>
                </p>
              )}
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
            action={
              <Badge tone="slate">
                {invoices === null
                  ? "Loading…"
                  : `${invoices.length} invoice${invoices.length === 1 ? "" : "s"}`}
              </Badge>
            }
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
            {invoices && invoices.length > 0 ? (
              invoices.map((inv) => (
                <tr key={inv.id} className="border-b border-ink/5 last:border-0">
                  <td className="px-6 py-3.5 text-ink-2">
                    {new Date(inv.created).toLocaleDateString()}
                  </td>
                  <td className="py-3.5 text-ink">
                    {inv.url ? (
                      <a
                        href={inv.url}
                        target="_blank"
                        rel="noreferrer"
                        className="hover:text-ember"
                      >
                        {inv.description}
                      </a>
                    ) : (
                      inv.description
                    )}
                  </td>
                  <td className="py-3.5 text-right font-medium text-ink">
                    {fmtUsd(inv.total)}
                  </td>
                  <td className="px-6 py-3.5 text-right">
                    <Badge tone={inv.status === "paid" ? "green" : "slate"}>
                      {inv.status}
                    </Badge>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="px-6 py-3.5 text-ink-3">
                  {invoices === null
                    ? "Loading invoices…"
                    : "No invoices yet. Pro has no base fee; a savings fee invoice appears only for months where you save more than $20."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>

      {info?.has_billing_account && (
        <div className="flex justify-center">
          <GhostButton onClick={() => void portal()}>
            Payment method &amp; invoices <ArrowUpRight size={14} />
          </GhostButton>
        </div>
      )}
      <Modal
        open={open}
        onClose={() => {
          if (!saving) setOpen(false);
        }}
        title="Manage billing"
      >
        <p className="mb-4 text-sm text-ink-3">
          Free never needs a payment method. Pro has no base fee: you add a card
          in Stripe Checkout and are charged only 5% of a month's savings when
          they exceed $20. Cancel any time from the billing portal; Pro stays
          active until the end of the period.
        </p>
        {upgradeBlocked && unpaidFee && (
          <p className="mb-4 rounded-md border border-ember/30 bg-ember-soft px-3 py-2 text-sm text-ink">
            Pro is unavailable until your {fmtUsd(unpaidFee.amount_usd)}{" "}
            savings fee is paid.{" "}
            {unpaidFee.invoice_url && (
              <a
                href={unpaidFee.invoice_url}
                target="_blank"
                rel="noreferrer"
                className="font-semibold text-ember underline underline-offset-2"
              >
                Pay invoice
              </a>
            )}
          </p>
        )}
        {cancelsOn && (
          <p className="mb-4 rounded-md border border-ember/30 bg-ember-soft px-3 py-2 text-sm text-ink">
            {current.name} is cancelled and ends on {cancelsOn}. Keep{" "}
            {current.name} selected and choose Renew to keep it.
          </p>
        )}
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
            <option
              key={p.id}
              value={p.id}
              disabled={p.id === "team" || (p.id === "pro" && upgradeBlocked)}
            >
              {p.id === "team"
                ? `${p.name} (coming soon)`
                : p.id === "pro" && upgradeBlocked
                  ? `${p.name} (pay outstanding fee first)`
                  : p.name}
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
              (selected === plan &&
                user.subscription_status === "active" &&
                !renewing)
            }
            onClick={() => void save()}
          >
            {saving
              ? upgrading || cancelling
                ? "Opening Stripe…"
                : renewing
                  ? "Renewing…"
                  : "Saving…"
              : upgrading
                ? "Continue to checkout"
                : renewing
                  ? `Renew ${current.name}`
                  : cancelling
                    ? "Cancel in billing portal"
                    : "Save subscription"}
          </GradientButton>
        </div>
      </Modal>
    </div>
  );
}
