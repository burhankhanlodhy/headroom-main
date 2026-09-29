import { motion } from "framer-motion";
import { Bot, Cloud, Shrink } from "lucide-react";
import { Card, CodeBlock, EASE } from "../components/ui";

function Node({
  icon: Icon,
  label,
  sub,
  accent,
  delay,
}: {
  icon: typeof Bot;
  label: string;
  sub: string;
  accent: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ type: "spring", stiffness: 220, damping: 18, delay }}
      className="flex flex-col items-center gap-2 text-center"
    >
      <div
        className="grid h-14 w-14 place-items-center rounded-2xl border sm:h-16 sm:w-16"
        style={{ borderColor: `${accent}44`, background: `${accent}14` }}
      >
        <Icon size={24} style={{ color: accent }} />
      </div>
      <div className="text-sm font-semibold text-white">{label}</div>
      <div className="text-[11px] text-slate-500">{sub}</div>
    </motion.div>
  );
}

function FlowLine({ delay, reverse = false }: { delay: number; reverse?: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      transition={{ delay }}
      className="relative mx-1 h-px flex-1 bg-gradient-to-r from-white/5 via-indigo-400/40 to-white/5 sm:mx-2"
    >
      <motion.span
        className="absolute top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-cyan-300 shadow-[0_0_10px_2px_rgba(34,211,238,0.7)]"
        animate={{ left: reverse ? ["100%", "0%"] : ["0%", "100%"] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut", repeatDelay: 0.4 }}
      />
    </motion.div>
  );
}

export function HowItWorks() {
  return (
    <section id="how-it-works" className="mx-auto max-w-6xl scroll-mt-28 px-4 py-20 sm:px-6">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: EASE }}
        className="mx-auto max-w-2xl text-center"
      >
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-indigo-300/80">
          How it works
        </p>
        <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
          One proxy. <span className="text-gradient">Three moving parts.</span>
        </h2>
      </motion.div>

      <Card hairline className="mt-12 p-8">
        <div className="flex flex-col items-stretch gap-6 sm:flex-row sm:items-center">
          <Node icon={Bot} label="Your agent" sub="Claude Code, OpenCode, Cursor…" accent="#818cf8" delay={0.1} />
          <FlowLine delay={0.3} />
          <Node icon={Shrink} label="ContextShrink" sub="compress · cache · ledger" accent="#22d3ee" delay={0.4} />
          <FlowLine delay={0.5} reverse />
          <Node icon={Cloud} label="Provider" sub="Anthropic, OpenAI, Vertex…" accent="#34d399" delay={0.6} />
        </div>
        <div className="mx-auto mt-8 max-w-2xl border-t border-white/5 pt-6 text-center text-sm text-slate-400">
          Requests flow through ContextShrink; bulky content is compressed and
          shelved, cache prefixes stay frozen, and the savings ledger records every
          token. Retrieve anything back with one MCP call.
        </div>
      </Card>

      <div className="mx-auto mt-8 grid max-w-4xl grid-cols-1 gap-5 md:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55, ease: EASE, delay: 0.15 }}
        >
          <Card className="h-full p-6">
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
              Step 1 · tunnel to your box
            </div>
            <CodeBlock code={".\\connect-horizon-vps.ps1 -VpsHost user@<pi-ip> -LocalPort 18787"} />
          </Card>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55, ease: EASE, delay: 0.25 }}
        >
          <Card className="h-full p-6">
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
              Step 2 · launch your agent
            </div>
            <CodeBlock code={"ANTHROPIC_BASE_URL=http://127.0.0.1:18787 claude"} />
          </Card>
        </motion.div>
      </div>
    </section>
  );
}
