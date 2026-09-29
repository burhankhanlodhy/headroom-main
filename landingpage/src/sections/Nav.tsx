import { useState } from "react";
import { motion } from "framer-motion";
import { Menu, X } from "lucide-react";
import { Brand } from "../components/Brand";
import { DASHBOARD_URL, GhostButton, GradientButton } from "../components/ui";

const LINKS = [
  { label: "Features", href: "#features" },
  { label: "How it works", href: "#how-it-works" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
];

export function Nav() {
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-40 px-4 pt-4 sm:px-6">
      <motion.div
        initial={{ opacity: 0, y: -14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="glass mx-auto flex max-w-6xl items-center gap-4 rounded-2xl px-4 py-3 sm:px-6"
      >
        <Brand />
        <nav className="ml-6 hidden items-center gap-6 md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm text-slate-400 transition hover:text-white"
            >
              {l.label}
            </a>
          ))}
        </nav>
        <div className="ml-auto hidden items-center gap-3 md:flex">
          <GhostButton href={`${DASHBOARD_URL}/login`}>Sign in</GhostButton>
          <GradientButton href={DASHBOARD_URL}>Open dashboard</GradientButton>
        </div>
        <button
          className="ml-auto rounded-lg p-2 text-slate-300 md:hidden"
          onClick={() => setOpen((o) => !o)}
        >
          {open ? <X size={18} /> : <Menu size={18} />}
        </button>
      </motion.div>
      {open && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass mx-auto mt-2 flex max-w-6xl flex-col gap-1 rounded-2xl p-3 md:hidden"
        >
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-white/5"
            >
              {l.label}
            </a>
          ))}
          <div className="mt-2 flex gap-2">
            <GhostButton href={`${DASHBOARD_URL}/login`} className="flex-1 justify-center">
              Sign in
            </GhostButton>
            <GradientButton href={DASHBOARD_URL} className="flex-1 justify-center">
              Dashboard
            </GradientButton>
          </div>
        </motion.div>
      )}
    </header>
  );
}
