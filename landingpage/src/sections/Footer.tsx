import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Brand } from "../components/Brand";
import { Card, DASHBOARD_URL, EASE, GhostButton, GradientButton } from "../components/ui";

export function Footer() {
  return (
    <footer className="mx-auto max-w-6xl px-4 pb-10 pt-8 sm:px-6">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.6, ease: EASE }}
      >
        <Card hairline className="relative overflow-hidden p-10 text-center">
          <div className="pointer-events-none absolute -top-24 left-1/2 h-56 w-[36rem] -translate-x-1/2 rounded-full bg-indigo-500/20 blur-3xl" />
          <h2 className="font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Stop paying for <span className="text-gradient">tokens you don't need.</span>
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-slate-400">
            Point your agent at ContextShrink and watch the savings ledger fill up.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-4">
            <GradientButton href={`${DASHBOARD_URL}/signup`}>
              Create your account <ArrowRight size={15} />
            </GradientButton>
            <GhostButton href={DASHBOARD_URL}>Open dashboard</GhostButton>
          </div>
        </Card>
      </motion.div>

      <div className="mt-10 flex flex-col items-center justify-between gap-6 border-t border-white/5 pt-8 md:flex-row">
        <Brand size={32} />
        <nav className="flex flex-wrap items-center justify-center gap-6 text-xs text-slate-500">
          <a href="#features" className="transition hover:text-slate-200">Features</a>
          <a href="#pricing" className="transition hover:text-slate-200">Pricing</a>
          <a href="#faq" className="transition hover:text-slate-200">FAQ</a>
          <a href={`${DASHBOARD_URL}/docs`} className="transition hover:text-slate-200">Documentation</a>
          <a href={`${DASHBOARD_URL}/login`} className="transition hover:text-slate-200">Sign in</a>
        </nav>
        <div className="text-xs text-slate-600">
          © 2026 ContextShrink · contextshrink.com
        </div>
      </div>
    </footer>
  );
}
