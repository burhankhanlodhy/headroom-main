import { motion } from "framer-motion";
import { EASE } from "../components/ui";

const TOOLS = [
  "Claude Code",
  "OpenCode",
  "Codex",
  "Cursor",
  "Goose",
  "Hermes",
  "VS Code",
  "LangChain",
  "CrewAI",
  "MCP servers",
];

export function Compatibility() {
  return (
    <section aria-label="Compatible agents and SDKs" className="ticker border-y border-line bg-card py-4">
      <div className="ticker-track flex items-center">
        {[...TOOLS, ...TOOLS].map((t, i) => (
          <span
            key={i}
            className="flex items-center whitespace-nowrap font-mono text-[13px] uppercase tracking-[0.18em] text-ink-2"
          >
            <span className="px-6">{t}</span>
            <span className="text-ember" aria-hidden>
              ✳
            </span>
          </span>
        ))}
      </div>
    </section>
  );
}
