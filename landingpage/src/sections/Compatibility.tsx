import { motion } from "framer-motion";
import { EASE } from "../components/ui";

const TOOLS = [
  "Claude Code",
  "OpenCode",
  "Codex",
  "Cursor",
  "Goose",
  "LangChain",
  "CrewAI",
  "MCP servers",
];

export function Compatibility() {
  return (
    <section className="mx-auto mt-14 max-w-6xl px-4 sm:px-6">
      <p className="text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        Works with the agents you already use
      </p>
      <div className="mt-5 flex flex-wrap items-center justify-center gap-2.5">
        {TOOLS.map((t, i) => (
          <motion.span
            key={t}
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, ease: EASE, delay: i * 0.05 }}
            className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-1.5 text-xs font-medium text-slate-300"
          >
            {t}
          </motion.span>
        ))}
      </div>
    </section>
  );
}
