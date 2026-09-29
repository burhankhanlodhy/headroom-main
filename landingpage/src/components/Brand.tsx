import { motion } from "framer-motion";
import { Shrink } from "lucide-react";
import { cn } from "../lib/utils";
import { EASE } from "./ui";

/** The ContextShrink mark: gradient tile + Shrink glyph. */
export function LogoMark({ size = 38 }: { size?: number }) {
  return (
    <motion.div
      whileHover={{ rotate: -8, scale: 1.08 }}
      transition={{ type: "spring", stiffness: 300, damping: 15 }}
      className="grid shrink-0 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-cyan-400 shadow-[0_0_28px_-6px_rgba(99,102,241,0.9)]"
      style={{ width: size, height: size }}
    >
      <Shrink size={size * 0.5} className="text-white" strokeWidth={2.4} />
    </motion.div>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("font-display text-lg font-bold tracking-tight text-white", className)}>
      Context<span className="text-gradient">Shrink</span>
    </span>
  );
}

/** Full lockup used in nav + footer. */
export function Brand({ href = "#", size = 38 }: { href?: string; size?: number }) {
  return (
    <motion.a
      href={href}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: EASE }}
      className="flex items-center gap-3"
    >
      <LogoMark size={size} />
      <div className="leading-tight">
        <Wordmark />
        <div className="text-[10.5px] font-medium tracking-wide text-slate-400">
          same answers, fewer tokens
        </div>
      </div>
    </motion.a>
  );
}

/** Same aurora backdrop as the dashboard — one brand, one atmosphere. */
export function AuroraBackground() {
  return (
    <div className="aurora" aria-hidden>
      <div className="blob blob-1" />
      <div className="blob blob-2" />
      <div className="blob blob-3" />
    </div>
  );
}
