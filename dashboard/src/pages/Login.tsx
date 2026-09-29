import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, LogIn } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { EASE, GradientButton } from "../components/ui";
import { signIn } from "../lib/auth";

const LANDING_URL =
  (import.meta.env.VITE_LANDING_URL as string | undefined) ?? "http://127.0.0.1:5174";

const inputCls =
  "w-full rounded-xl border border-white/10 bg-black/40 px-3.5 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-indigo-400/50 focus:ring-2 focus:ring-indigo-500/20";

const backLinkCls =
  "inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 transition hover:border-indigo-400/40 hover:text-white";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (busy) return;
    if (!email.trim() || !password) {
      setError("Enter your email and password.");
      return;
    }
    setError(null);
    setBusy(true);
    try {
      await signIn(email.trim(), password);
      navigate("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign in failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 18 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.5, ease: EASE }}
      className="glass w-[420px] max-w-full rounded-3xl p-9"
    >
      <motion.div
        initial={{ rotate: -10, scale: 0.7 }}
        animate={{ rotate: 0, scale: 1 }}
        transition={{ type: "spring", stiffness: 260, damping: 15, delay: 0.15 }}
        className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-indigo-500 via-violet-500 to-cyan-400 shadow-[0_0_28px_-6px_rgba(99,102,241,0.9)]"
      >
        <LogIn size={22} className="text-white" />
      </motion.div>

      <h1 className="mt-5 text-center font-display text-2xl font-bold text-white">
        Welcome back
      </h1>
      <p className="mt-1.5 text-center text-sm text-slate-400">
        Sign in to your ContextShrink dashboard.
      </p>

      <div className="mt-7 flex flex-col gap-4">
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-slate-400">Email</span>
          <input
            autoFocus
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@contextshrink.com"
            className={inputCls}
            onKeyDown={(e) => e.key === "Enter" && submit()}
          />
        </label>
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-slate-400">Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className={inputCls}
            onKeyDown={(e) => e.key === "Enter" && submit()}
          />
        </label>

        {error && (
          <motion.p
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg border border-rose-400/25 bg-rose-400/10 px-3 py-2 text-xs text-rose-300"
          >
            {error}
          </motion.p>
        )}

        <GradientButton onClick={submit} className="mt-1 w-full justify-center">
          {busy ? "Signing in…" : "Sign in"}
        </GradientButton>
      </div>

      <p className="mt-5 text-center text-xs text-slate-500">
        No account yet?{" "}
        <button
          onClick={() => navigate("/signup")}
          className="font-medium text-indigo-300 transition hover:text-indigo-200"
        >
          Create one
        </button>
      </p>

      <div className="mt-6 flex justify-center border-t border-white/5 pt-5">
        <a href={LANDING_URL} className={backLinkCls}>
          <ArrowLeft size={13} /> Back to contextshrink.com
        </a>
      </div>
    </motion.div>
  );
}
