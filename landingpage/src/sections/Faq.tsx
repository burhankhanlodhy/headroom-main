import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { Card, EASE } from "../components/ui";
import { cn } from "../lib/utils";

const ITEMS = [
  {
    q: "Will compression change my agent's answers?",
    a: "ContextShrink is conservative by design: bulky, low-relevance content (logs, dumps, old tool output) is summarized and shelved with a marker; instructions, code you're editing and the live conversation stay intact. Anything compressed can be pulled back verbatim with one retrieve call.",
  },
  {
    q: "Doesn't compression destroy prompt caching?",
    a: "Not here. Cache preservation is a first-class constraint: stable prefixes are frozen, breakpoints are placed deliberately, and compression that would invalidate a warm cache is skipped. That's why the cache hit rate stays above 90% in our evals.",
  },
  {
    q: "Where does my code go?",
    a: "Nowhere. The proxy runs on hardware you own — a VPS, a home server, or a Raspberry Pi. It binds to loopback by default and is meant to be reached over an SSH tunnel. There is no cloud component in the OSS build.",
  },
  {
    q: "Which agents and SDKs are supported?",
    a: "Anything that speaks the Anthropic Messages API, the OpenAI Chat Completions API, or Google Vertex — plus first-class wrap scripts for Claude Code, OpenCode, Codex, Cursor and more. LangChain, CrewAI and MCP integrations are included.",
  },
  {
    q: "How do I know it's actually saving money?",
    a: "Every request lands in a durable savings ledger: original tokens, delivered tokens, cache savings and a counterfactual cost estimate. The dashboard and Prometheus metrics make the number impossible to ignore.",
  },
];

function Item({ q, a, open, onToggle }: { q: string; a: string; open: boolean; onToggle: () => void }) {
  return (
    <Card className={cn("overflow-hidden transition", open && "border-indigo-400/30")}>
      <button onClick={onToggle} className="flex w-full items-center gap-4 px-6 py-5 text-left">
        <span className="flex-1 font-display text-[15px] font-semibold text-white">{q}</span>
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.3, ease: EASE }}>
          <ChevronDown size={17} className="text-slate-400" />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.35, ease: EASE }}
          >
            <p className="px-6 pb-5 text-sm leading-relaxed text-slate-400">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

export function Faq() {
  const [openIdx, setOpenIdx] = useState<number>(0);
  return (
    <section id="faq" className="mx-auto max-w-3xl scroll-mt-28 px-4 py-20 sm:px-6">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: EASE }}
        className="text-center"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-indigo-300/80">
          FAQ
        </p>
        <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Fair questions, <span className="text-gradient">straight answers.</span>
        </h2>
      </motion.div>
      <div className="mt-10 flex flex-col gap-3">
        {ITEMS.map((item, i) => (
          <Item
            key={item.q}
            q={item.q}
            a={item.a}
            open={openIdx === i}
            onToggle={() => setOpenIdx(openIdx === i ? -1 : i)}
          />
        ))}
      </div>
    </section>
  );
}
