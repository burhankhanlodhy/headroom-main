import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { Card, DASHBOARD_URL, EASE, GradientButton, GhostButton } from "../components/ui";
import { cn } from "../lib/utils";

const PLANS = [
  {
    name: "Open Source",
    price: "$0",
    per: "forever",
    blurb: "The full proxy, self-hosted. For personal boxes and tinkering.",
    features: [
      "Unlimited compression",
      "All provider backends",
      "Savings ledger + dashboard",
      "Community support",
    ],
    cta: "Self-host it",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$20",
    per: "/mo",
    blurb: "For daily drivers who want the polish and the priority.",
    features: [
      "Everything in Open Source",
      "Priority routing + warm cache tuning",
      "Advanced savings analytics",
      "Email support",
    ],
    cta: "Start Pro",
    highlight: true,
  },
  {
    name: "Team",
    price: "$99",
    per: "/mo",
    blurb: "Shared proxy, shared savings, shared visibility.",
    features: [
      "Everything in Pro",
      "Team seats + shared keys",
      "Audit log & SSO-ready auth",
      "Priority support",
    ],
    cta: "Talk to us",
    highlight: false,
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="mx-auto max-w-6xl scroll-mt-28 px-4 py-20 sm:px-6">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: EASE }}
        className="mx-auto max-w-2xl text-center"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-indigo-300/80">
          Pricing
        </p>
        <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Pays for itself. <span className="text-gradient">Usually in week one.</span>
        </h2>
      </motion.div>

      <div className="mt-12 grid grid-cols-1 gap-5 md:grid-cols-3">
        {PLANS.map((p, i) => (
          <motion.div
            key={p.name}
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.55, ease: EASE, delay: i * 0.1 }}
            className={cn(p.highlight && "lg:-mt-4 lg:mb-4")}
          >
            <Card
              hairline
              className={cn(
                "glass-hover flex h-full flex-col p-7",
                p.highlight && "ring-gradient",
              )}
            >
              {p.highlight && (
                <span className="mb-3 inline-flex w-fit rounded-full bg-gradient-to-r from-indigo-500 to-cyan-400 px-3 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white">
                  Most popular
                </span>
              )}
              <div className="font-display text-sm font-semibold uppercase tracking-wider text-slate-300">
                {p.name}
              </div>
              <div className="mt-3 font-display text-4xl font-bold text-white">
                {p.price}
                <span className="text-base font-medium text-slate-400"> {p.per}</span>
              </div>
              <p className="mt-2 text-sm text-slate-400">{p.blurb}</p>
              <ul className="mt-6 flex flex-1 flex-col gap-2.5">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-slate-300">
                    <Check size={15} className="mt-0.5 shrink-0 text-emerald-300" />
                    {f}
                  </li>
                ))}
              </ul>
              <div className="mt-7">
                {p.highlight ? (
                  <GradientButton href={`${DASHBOARD_URL}/signup`} className="w-full justify-center">
                    {p.cta}
                  </GradientButton>
                ) : (
                  <GhostButton href={`${DASHBOARD_URL}/signup`} className="w-full justify-center">
                    {p.cta}
                  </GhostButton>
                )}
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
