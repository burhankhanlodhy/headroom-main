import { motion } from "framer-motion";
import { Card, CountUp, EASE } from "../components/ui";

const STATS = [
  { value: 63.8, suffix: "%", label: "average context compression", color: "#818cf8" },
  { value: 222, suffix: "M+", label: "tokens saved in evals", color: "#22d3ee" },
  { value: 92.4, suffix: "%", label: "prompt cache hit rate kept", color: "#34d399" },
  { value: 4, suffix: "ms", label: "median proxy overhead", color: "#fbbf24" },
];

export function Metrics() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <Card hairline className="overflow-hidden">
        <div className="grid grid-cols-2 divide-white/5 lg:grid-cols-4 lg:divide-x">
          {STATS.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, ease: EASE, delay: i * 0.08 }}
              className="border-b border-white/5 p-7 text-center last:border-b-0 lg:border-b-0 [&:nth-child(odd)]:border-r lg:[&:nth-child(odd)]:border-r-0"
            >
              <div className="font-display text-4xl font-bold" style={{ color: s.color }}>
                <CountUp value={s.value} format={(v) => v.toFixed(1)} />
                {s.suffix}
              </div>
              <div className="mt-1.5 text-xs text-slate-500">{s.label}</div>
            </motion.div>
          ))}
        </div>
      </Card>
    </section>
  );
}
