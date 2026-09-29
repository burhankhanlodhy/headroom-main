import { useEffect, useRef, useState, type ReactNode } from "react";
import { animate, motion, useInView } from "framer-motion";
import { Check, Copy } from "lucide-react";
import { cn, fmtFull } from "../lib/utils";

export const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];

/** Dashboard app URL — baked at build time, overridable for the two-host deploy. */
export const DASHBOARD_URL: string =
  (import.meta.env.VITE_DASHBOARD_URL as string | undefined) ?? "http://127.0.0.1:5173";

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

export function GradientButton({
  children,
  href,
  onClick,
  className,
}: {
  children: ReactNode;
  href?: string;
  onClick?: () => void;
  className?: string;
}) {
  if (href) {
    return (
      <motion.a
        href={href}
        whileHover={{ scale: 1.04 }}
        whileTap={{ scale: 0.97 }}
        className={cn(
          "inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 via-violet-500 to-cyan-400 px-5 py-2.5 text-sm font-semibold text-white shadow-[0_8px_30px_-10px_rgba(99,102,241,0.8)] transition hover:brightness-110",
          className,
        )}
      >
        {children}
      </motion.a>
    );
  }
  return (
    <motion.button
      whileHover={{ scale: 1.04 }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 via-violet-500 to-cyan-400 px-5 py-2.5 text-sm font-semibold text-white shadow-[0_8px_30px_-10px_rgba(99,102,241,0.8)] transition hover:brightness-110",
        className,
      )}
    >
      {children}
    </motion.button>
  );
}

export function GhostButton({
  children,
  href,
  onClick,
  className,
}: {
  children: ReactNode;
  href?: string;
  onClick?: () => void;
  className?: string;
}) {
  const cls = cn(
    "inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-medium text-slate-200 transition hover:border-indigo-400/40 hover:bg-white/10",
    className,
  );
  if (href) {
    return (
      <motion.a whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }} href={href} className={cls}>
        {children}
      </motion.a>
    );
  }
  return (
    <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }} onClick={onClick} className={cls}>
      {children}
    </motion.button>
  );
}

export function CountUp({
  value,
  format = fmtFull,
  className,
  duration = 1.6,
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

export function CopyButton({ text, className }: { text: string; className?: string }) {
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
      {copied ? <Check size={13} className="text-emerald-300" /> : <Copy size={13} />}
    </button>
  );
}

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
