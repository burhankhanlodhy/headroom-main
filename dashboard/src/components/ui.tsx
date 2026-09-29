import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { animate, AnimatePresence, motion, useInView } from "framer-motion";
import { Area, AreaChart, ResponsiveContainer } from "recharts";
import { Check, Copy, X } from "lucide-react";
import { cn, fmtFull } from "../lib/utils";

export const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];

/* ------------------------------------------------------------------ Card */

export function Card({
  className,
  children,
  hairline = false,
}: {
  className?: string;
  children: ReactNode;
  hairline?: boolean;
}) {
  return (
    <div className={cn("glass rounded-2xl", hairline && "hairline-top", className)}>{children}</div>
  );
}

export function SectionHeader({
  eyebrow,
  title,
  action,
}: {
  eyebrow?: string;
  title: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-4 flex items-end justify-between gap-4">
      <div>
        {eyebrow && (
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-indigo-300/80">
            {eyebrow}
          </div>
        )}
        <h2 className="font-display text-lg font-semibold text-slate-100">{title}</h2>
      </div>
      {action}
    </div>
  );
}

/* --------------------------------------------------------------- CountUp */

export function CountUp({
  value,
  format = fmtFull,
  className,
  duration = 1.5,
}: {
  value: number;
  format?: (n: number) => string;
  className?: string;
  duration?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [display, setDisplay] = useState("0");

  useEffect(() => {
    if (!inView) return;
    const controls = animate(0, value, {
      duration,
      ease: EASE,
      onUpdate: (v) => setDisplay(format(v)),
    });
    return () => controls.stop();
  }, [inView, value, duration, format]);

  return (
    <span ref={ref} className={cn("tabular-nums", className)}>
      {display}
    </span>
  );
}

/* ------------------------------------------------------------------ Badge */

const badgeTones: Record<string, string> = {
  green: "bg-emerald-400/10 text-emerald-300 border-emerald-400/25",
  red: "bg-rose-400/10 text-rose-300 border-rose-400/25",
  amber: "bg-amber-400/10 text-amber-300 border-amber-400/25",
  indigo: "bg-indigo-400/10 text-indigo-300 border-indigo-400/25",
  slate: "bg-white/5 text-slate-300 border-white/10",
};

export function Badge({
  tone = "slate",
  children,
  className,
}: {
  tone?: keyof typeof badgeTones;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium",
        badgeTones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

/* -------------------------------------------------------------- Sparkline */

export function Spark({
  data,
  color = "#818cf8",
  height = 44,
}: {
  data: number[];
  color?: string;
  height?: number;
}) {
  const gid = useId();
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data.map((v, i) => ({ i, v }))} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.4} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={2}
          fill={`url(#${gid})`}
          isAnimationActive
          animationDuration={1400}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

/* -------------------------------------------------------------- StatCard */

export function StatCard({
  label,
  value,
  format,
  delta,
  spark,
  color = "#818cf8",
  className,
}: {
  label: string;
  value: number;
  format?: (n: number) => string;
  delta?: number;
  spark?: number[];
  color?: string;
  className?: string;
}) {
  const up = (delta ?? 0) >= 0;
  return (
    <Card hairline className={cn("glass-hover p-5", className)}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
          {label}
        </span>
        {delta !== undefined && (
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
              up ? "bg-emerald-400/10 text-emerald-300" : "bg-rose-400/10 text-rose-300",
            )}
          >
            {up ? "▲" : "▼"} {Math.abs(delta).toFixed(1)}%
          </span>
        )}
      </div>
      <div className="mt-2 font-display text-[26px] font-semibold text-white">
        <CountUp value={value} format={format} />
      </div>
      {spark && (
        <div className="-mx-1 mt-3">
          <Spark data={spark} color={color} height={40} />
        </div>
      )}
    </Card>
  );
}

/* ----------------------------------------------------------- ProgressRing */

export function ProgressRing({
  pct,
  size = 116,
  stroke = 9,
  from = "#818cf8",
  to = "#22d3ee",
  children,
}: {
  pct: number;
  size?: number;
  stroke?: number;
  from?: string;
  to?: string;
  children?: ReactNode;
}) {
  const gid = useId();
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={from} />
            <stop offset="100%" stopColor={to} />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={`url(#${gid})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          whileInView={{ strokeDashoffset: c * (1 - pct / 100) }}
          viewport={{ once: true }}
          transition={{ duration: 1.6, ease: EASE, delay: 0.25 }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">{children}</div>
    </div>
  );
}

/* ------------------------------------------------------------- CopyButton */

export function CopyButton({
  text,
  className,
  label,
}: {
  text: string;
  className?: string;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
        } catch {
          /* clipboard unavailable — visual feedback only */
        }
        setCopied(true);
        setTimeout(() => setCopied(false), 1600);
      }}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-slate-300 transition hover:border-indigo-400/40 hover:text-white",
        className,
      )}
    >
      {copied ? (
        <motion.span key="ok" initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
          <Check size={13} className="text-emerald-300" />
        </motion.span>
      ) : (
        <Copy size={13} />
      )}
      {label !== undefined && <span>{copied ? "Copied" : label}</span>}
    </button>
  );
}

/* --------------------------------------------------------------- CodeBlock */

export function CodeBlock({ code, className }: { code: string; className?: string }) {
  return (
    <div className={cn("codeblock relative", className)}>
      <CopyButton text={code} className="absolute right-3 top-3" />
      <pre className="overflow-x-auto p-4 pr-14 text-[12.5px] leading-relaxed text-slate-300">
        {code}
      </pre>
    </div>
  );
}

/* ------------------------------------------------------------------- Modal */

export function Modal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 grid place-items-center bg-black/60 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="ring-gradient w-[440px] max-w-[92vw] rounded-2xl p-6"
            initial={{ scale: 0.92, y: 18, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.95, y: 8, opacity: 0 }}
            transition={{ duration: 0.32, ease: EASE }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-display text-lg font-semibold text-white">{title}</h3>
              <button
                onClick={onClose}
                className="rounded-lg p-1.5 text-slate-400 transition hover:bg-white/10 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/* --------------------------------------------------------------- Buttons */

export function GradientButton({
  children,
  onClick,
  className,
}: {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <motion.button
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 via-violet-500 to-cyan-400 px-4 py-2 text-sm font-semibold text-white shadow-[0_8px_30px_-10px_rgba(99,102,241,0.8)] transition hover:brightness-110",
        className,
      )}
    >
      {children}
    </motion.button>
  );
}

export function GhostButton({
  children,
  onClick,
  className,
}: {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-indigo-400/40 hover:bg-white/10",
        className,
      )}
    >
      {children}
    </button>
  );
}
