import { motion } from "framer-motion";
import {
  BookOpenCheck,
  Database,
  Gauge,
  GitBranch,
  Lock,
  Wrench,
} from "lucide-react";
import { Card, EASE } from "../components/ui";

const FEATURES = [
  {
    icon: Gauge,
    title: "Transparent compression",
    body: "Bulky tool output, logs, docs and diffs are compressed en route to the model. Your agent keeps its workflow — the context just gets smaller.",
    color: "#818cf8",
  },
  {
    icon: Database,
    title: "Cache-preserving by design",
    body: "Prefixes are frozen and breakpoints are managed so provider prompt caches stay warm. Compression that would nuke your cache hit rate doesn't ship.",
    color: "#22d3ee",
  },
  {
    icon: GitBranch,
    title: "Retrieve on demand",
    body: "Compressed content isn't lost — it's shelved. Every summary carries a marker; the original is one MCP tool call away (horizon_retrieve).",
    color: "#a78bfa",
  },
  {
    icon: Wrench,
    title: "Provider-agnostic",
    body: "Anthropic, OpenAI, Vertex, Bedrock, LiteLLM, GitHub Copilot subscriptions. One proxy, every upstream, zero agent rewrites.",
    color: "#34d399",
  },
  {
    icon: BookOpenCheck,
    title: "Savings you can audit",
    body: "A durable ledger records every request, token saved and dollar avoided — with Prometheus metrics and a live dashboard.",
    color: "#fbbf24",
  },
  {
    icon: Lock,
    title: "Yours, entirely",
    body: "Self-hosted on your box — a VPS or a Raspberry Pi. Loopback-only by default, SSH-tunnel first. No data leaves your network.",
    color: "#fb7185",
  },
];

export function Features() {
  return (
    <section id="features" className="mx-auto max-w-6xl scroll-mt-28 px-4 py-20 sm:px-6">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: EASE }}
        className="mx-auto max-w-2xl text-center"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-indigo-300/80">
          Features
        </p>
        <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Everything shrinks. <span className="text-gradient">Nothing breaks.</span>
        </h2>
        <p className="mt-3 text-slate-400">
          A proxy layer that respects how coding agents actually work — caches,
          tools, multi-turn state and all.
        </p>
      </motion.div>

      <div className="mt-12 grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f, i) => (
          <motion.div
            key={f.title}
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.55, ease: EASE, delay: (i % 3) * 0.09 }}
          >
            <Card className="glass-hover h-full p-6">
              <div
                className="grid h-11 w-11 place-items-center rounded-xl border"
                style={{
                  borderColor: `${f.color}44`,
                  background: `${f.color}14`,
                  boxShadow: `0 0 24px -8px ${f.color}66`,
                }}
              >
                <f.icon size={19} style={{ color: f.color }} />
              </div>
              <h3 className="mt-4 font-display text-[15px] font-semibold text-white">
                {f.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{f.body}</p>
            </Card>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
