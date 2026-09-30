import { useState, type ReactNode } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  BarChart3,
  BookOpen,
  CreditCard,
  KeyRound,
  LogOut,
  Menu,
  Shrink,
  UserRound,
  X,
} from "lucide-react";
import { cn } from "../lib/utils";
import { EASE } from "./ui";

export function AuroraBackground() {
  return <div className="paper-grid fixed inset-0" aria-hidden />;
}

const nav = [
  { to: "/", label: "Profile", icon: UserRound },
  { to: "/keys", label: "API Keys", icon: KeyRound },
  { to: "/usage", label: "Usage", icon: BarChart3 },
  { to: "/subscriptions", label: "Subscriptions", icon: CreditCard },
  { to: "/docs", label: "Documentation", icon: BookOpen },
];

const pageMeta: Record<string, { title: string; subtitle: string }> = {
  "/": { title: "Profile", subtitle: "Your account and session overview" },
  "/keys": { title: "API Keys", subtitle: "Credentials that route through your proxy" },
  "/usage": { title: "Usage", subtitle: "Requests, compression and savings over time" },
  "/subscriptions": { title: "Subscriptions", subtitle: "Providers, quotas and billing" },
  "/docs": { title: "Documentation", subtitle: "Quickstarts, endpoints and wiring guides" },
  "/signout": { title: "Sign out", subtitle: "" },
};

function Logo() {
  return (
    <div className="flex items-center gap-3 px-2">
      <motion.div
        className="grid h-10 w-10 place-items-center rounded-lg bg-ink text-paper shadow-[4px_4px_0_0_rgba(29,23,18,0.9)]"
        whileHover={{ rotate: -8, scale: 1.06 }}
        transition={{ type: "spring", stiffness: 300, damping: 15 }}
      >
        <Shrink size={19} className="text-paper" strokeWidth={2.4} />
      </motion.div>
      <div>
        <div className="font-display text-[15px] font-bold tracking-tight text-ink">
          Context<span className="text-ember">Shrink</span>
        </div>
        <div className="text-[10.5px] font-medium tracking-wide text-ink-3">
          same answers, fewer tokens
        </div>
      </div>
    </div>
  );
}

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="mt-8 flex flex-1 flex-col gap-1">
      {nav.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} end={to === "/"} onClick={onNavigate}>
          {({ isActive }) => (
            <div
              className={cn(
                "relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive ? "text-ink" : "text-ink-3 hover:text-ink",
              )}
            >
              {isActive && (
                <motion.span
                  layoutId="nav-pill"
                  className="absolute inset-0 rounded-lg border border-ink/20 bg-ember-soft"
                  transition={{ type: "spring", stiffness: 380, damping: 32 }}
                />
              )}
              <Icon
                size={17}
                className={cn("relative z-10", isActive && "text-ember")}
              />
              <span className="relative z-10">{label}</span>
              {isActive && (
                <motion.span
                  layoutId="nav-dot"
                  className="relative z-10 ml-auto h-1.5 w-1.5 rounded-full bg-ember"
                />
              )}
            </div>
          )}
        </NavLink>
      ))}
      <NavLink to="/signout" onClick={onNavigate}>
        {({ isActive }) => (
          <div
            className={cn(
              "relative mt-auto flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
              isActive ? "text-ember" : "text-ink-3 hover:text-ember",
            )}
          >
            <LogOut size={17} />
            Sign out
          </div>
        )}
      </NavLink>
    </nav>
  );
}

function ProxyStatus() {
  return (
    <div className="paper-panel flex items-center gap-3 rounded-lg px-3 py-2.5">
      <span className="live-dot" />
      <div className="text-[11px] leading-tight">
        <div className="font-semibold text-ink">Proxy live</div>
        <div className="text-ink-3">loopback · 8787</div>
      </div>
    </div>
  );
}

export function Shell() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const meta = pageMeta[location.pathname] ?? { title: "ContextShrink", subtitle: "" };

  return (
    <div className="relative z-10 flex h-screen">
      {/* desktop sidebar */}
      <aside className="paper-panel hidden w-[250px] shrink-0 flex-col rounded-none border-y-0 border-l-0 px-4 py-6 lg:flex">
        <Logo />
        <NavItems />
        <ProxyStatus />
      </aside>

      {/* mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            className="fixed inset-0 z-40 bg-ink/60 backdrop-blur-sm lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMobileOpen(false)}
          >
            <motion.aside
              className="paper-panel h-full w-[260px] rounded-none border-y-0 border-l-0 px-4 py-6"
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.3, ease: EASE }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between">
                <Logo />
                <button
                  className="rounded-lg p-2 text-ink-3 hover:bg-ink/10"
                  onClick={() => setMobileOpen(false)}
                >
                  <X size={18} />
                </button>
              </div>
              <NavItems onNavigate={() => setMobileOpen(false)} />
              <ProxyStatus />
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>

      {/* main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-4 px-6 pt-6 lg:px-10">
          <button
            className="paper-panel rounded-lg p-2.5 text-ink-3 lg:hidden"
            onClick={() => setMobileOpen(true)}
          >
            <Menu size={18} />
          </button>
          <div className="min-w-0 flex-1">
            <motion.h1
              key={meta.title}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease: EASE }}
              className="font-display text-[22px] font-semibold text-ink"
            >
              {meta.title}
            </motion.h1>
            {meta.subtitle && <p className="text-[13px] text-ink-3">{meta.subtitle}</p>}
          </div>
          <div className="paper-panel hidden items-center gap-2 rounded-lg px-3 py-2 text-xs text-ink-3 md:flex">
            <svg
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="7" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            Search
            <kbd className="ml-4 rounded-md border border-ink/20 bg-ink/5 px-1.5 py-0.5 font-mono text-[10px] text-ink-3">
              ⌘K
            </kbd>
          </div>
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="grid h-10 w-10 cursor-pointer place-items-center rounded-full bg-ink text-[13px] font-bold text-paper"
          >
            BK
          </motion.div>
        </header>

        <main className="min-h-0 flex-1 overflow-y-auto px-6 pb-10 pt-6 lg:px-10">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.32, ease: EASE }}
              className="mx-auto max-w-[1180px]"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

export function FullPageCenter({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  return (
    <div className="relative z-10 grid h-screen place-items-center px-6">
      <button
        className="btn-ghost absolute right-6 top-6 rounded-lg px-4 py-2 text-sm"
        onClick={() => navigate("/")}
      >
        ← Back to dashboard
      </button>
      {children}
    </div>
  );
}
