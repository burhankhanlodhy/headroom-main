import { useState } from "react";
import { Menu, X } from "lucide-react";
import { Btn, DASHBOARD_URL, LogoMark, Wordmark } from "../components/ui";

const LINKS = [
  { label: "Features", href: "#features" },
  { label: "How it works", href: "#how-it-works" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
];

export function Nav() {
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/90 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-[96rem] items-center gap-8 px-4 sm:px-8">
        <a href="#" className="flex items-center gap-2.5">
          <LogoMark size={28} />
          <div className="leading-tight">
            <Wordmark />
            <div className="font-mono text-[10px] tracking-wide text-ink-3">
              same answers, fewer tokens
            </div>
          </div>
        </a>
        <nav className="hidden items-center gap-7 md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm text-ink-2 underline-offset-4 transition hover:text-ink hover:underline hover:decoration-ember hover:decoration-2"
            >
              {l.label}
            </a>
          ))}
        </nav>
        <div className="ml-auto hidden items-center gap-3 md:flex">
          <Btn variant="ghost" href={`${DASHBOARD_URL}/login`}>
            Sign in
          </Btn>
          <Btn variant="ink" href={DASHBOARD_URL}>
            Open dashboard
          </Btn>
        </div>
        <button
          aria-label="Toggle menu"
          className="ml-auto rounded-md p-2 text-ink md:hidden"
          onClick={() => setOpen((o) => !o)}
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>
      {open && (
        <nav className="border-t border-line md:hidden">
          <div className="flex flex-col gap-1 px-4 py-3">
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="rounded-sm px-3 py-2 text-sm text-ink-2 hover:bg-card"
              >
                {l.label}
              </a>
            ))}
            <div className="mt-2 flex gap-2 pb-1">
              <Btn variant="ghost" href={`${DASHBOARD_URL}/login`} className="flex-1 !justify-center">
                Sign in
              </Btn>
              <Btn variant="ink" href={DASHBOARD_URL} className="flex-1 !justify-center">
                Dashboard
              </Btn>
            </div>
          </div>
        </nav>
      )}
    </header>
  );
}
