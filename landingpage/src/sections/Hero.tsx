import { useEffect, useRef, useState } from "react";
import { animate, motion, useInView } from "framer-motion";
import { ArrowRight, Shrink, Zap } from "lucide-react";
import { DASHBOARD_URL, EASE, GhostButton, GradientButton } from "../components/ui";
import { fmtFull } from "../lib/utils";

const ORIGINAL = 12400;
const SHRUNK = 4480;

/** Token counter that rolls DOWN from `from` to `to` when scrolled into view. */
function ShrinkCounter({ from, to, delay }: { from: number; to: number; delay: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [v, setV] = useState(from);

  useEffect(() => {
    if (!inView) return;
    const controls = animate(from, to, {
      duration: 2.1,
      ease: EASE,
      delay,
      onUpdate: (x) => setV(Math.round(x)),
    });
    return () => controls.stop();
  }, [inView, from, to, delay]);

  return (
    <span ref={ref} className="tabular-nums">
      {fmtFull(v)} tok
    </span>
  );
}

/** The signature visual: a context block visibly compressing into a smaller one. */
function CompressionDemo() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 26, rotate: 1.5 }}
      animate={{ opacity: 1, y: 0, rotate: 0 }}
      transition={{ duration: 0.9, ease: EASE, delay: 0.35 }}
      className="glass hairline-top relative w-full max-w-md rounded-3xl p-6"
    >
      <div className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-cyan-400/15 blur-3xl" />

      {/* original block */}
      <div className="flex items-center justify-between text-[11px] text-slate-400">
        <span className="font-medium uppercase tracking-[0.14em]">Original context</span>
        <span className="font-mono">
          <ShrinkCounter from={ORIGINAL} to={ORIGINAL} delay={0} />
        </span>
      </div>
      <motion.div
        initial={{ width: "100%" }}
        whileInView={{ width: "100%" }}
        viewport={{ once: true }}
        className="mt-2 overflow-hidden rounded-xl border border-indigo-400/25 bg-gradient-to-r from-indigo-500/25 to-violet-500/10 p-3"
      >
        <div className="space-y-1.5">
          {[92, 78, 85, 64].map((w, i) => (
            <motion.div
              key={i}
              className="h-2 rounded-full bg-white/15"
              style={{ width: `${w}%` }}
              initial={{ opacity: 0.9 }}
            />
          ))}
        </div>
      </motion.div>

      {/* connector */}
      <div className="relative my-3 flex items-center justify-center">
        <motion.div
          className="absolute inset-x-6 h-px bg-gradient-to-r from-indigo-400/50 via-violet-400/50 to-cyan-300/60"
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: EASE, delay: 0.5 }}
        />
        <motion.div
          className="relative grid h-10 w-10 place-items-center rounded-xl border border-cyan-300/30 bg-ink-900"
          initial={{ scale: 0.6, rotate: -20 }}
          whileInView={{ scale: 1, rotate: 0 }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 260, damping: 15, delay: 0.7 }}
        >
          <Shrink size={17} className="text-cyan-300" />
          <motion.span
            className="absolute inset-0 rounded-xl border border-cyan-300/40"
            animate={{ scale: [1, 1.35], opacity: [0.7, 0] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeOut", delay: 1 }}
          />
        </motion.div>
      </div>

      {/* shrunk block */}
      <div className="flex items-center justify-between text-[11px]">
        <span className="font-medium uppercase tracking-[0.14em] text-cyan-200/90">
          Delivered to the model
        </span>
        <span className="font-mono text-cyan-200">
          <ShrinkCounter from={ORIGINAL} to={SHRUNK} delay={0.9} />
        </span>
      </div>
      <motion.div
        initial={{ width: "36%" }}
        whileInView={{ width: "36%" }}
        viewport={{ once: true }}
        className="mt-2 overflow-hidden rounded-xl border border-cyan-300/30 bg-gradient-to-r from-cyan-400/20 to-sky-500/10 p-3"
      >
        <div className="space-y-1.5">
          {[88, 70].map((w, i) => (
            <div key={i} className="h-2 rounded-full bg-white/20" style={{ width: `${w}%` }} />
          ))}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ type: "spring", stiffness: 240, damping: 16, delay: 1.8 }}
        className="mt-4 inline-flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-semibold text-emerald-300"
      >
        <Zap size={12} /> 63.8% smaller — answer unchanged
      </motion.div>
    </motion.div>
  );
}

export function Hero() {
  return (
    <section className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-4 pb-16 pt-16 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:pt-24">
      <div>
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: EASE }}
          className="inline-flex items-center gap-2 rounded-full border border-indigo-400/30 bg-indigo-500/10 px-3.5 py-1.5 text-xs font-medium text-indigo-200"
        >
          <span className="live-dot !h-1.5 !w-1.5" />
          Self-hosted context compression · v0.1
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: EASE, delay: 0.1 }}
          className="mt-5 font-display text-5xl font-bold leading-[1.04] tracking-tight text-white sm:text-6xl"
        >
          Your context,
          <br />
          <span className="text-gradient">shrunk.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: EASE, delay: 0.22 }}
          className="mt-5 max-w-xl text-lg leading-relaxed text-slate-400"
        >
          ContextShrink sits between your AI agent and the model — compressing bulky
          context, preserving prompt caches, and showing you every token you didn't
          pay for. Same answers. Dramatically smaller bills.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: EASE, delay: 0.34 }}
          className="mt-8 flex flex-wrap items-center gap-4"
        >
          <GradientButton href={`${DASHBOARD_URL}/signup`}>
            Get started free <ArrowRight size={15} />
          </GradientButton>
          <GhostButton href="#how-it-works">See how it works</GhostButton>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="mt-4 text-xs text-slate-500"
        >
          Runs on your own hardware — even a Raspberry Pi. Your code never leaves
          your network.
        </motion.p>
      </div>

      <div className="flex justify-center lg:justify-end">
        <CompressionDemo />
      </div>
    </section>
  );
}
