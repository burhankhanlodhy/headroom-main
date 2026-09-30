import { useEffect } from "react";
import { motion } from "framer-motion";
import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { EASE, GhostButton, GradientButton } from "../components/ui";
import { logout } from "../lib/auth";

export default function SignOut() {
  const navigate = useNavigate();

  useEffect(() => {
    logout();
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.94, y: 16 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.5, ease: EASE }}
      className="ink-card w-[420px] max-w-full rounded-lg p-10 text-center"
    >
      <motion.div
        initial={{ rotate: -14, scale: 0.6 }}
        animate={{ rotate: 0, scale: 1 }}
        transition={{ type: "spring", stiffness: 260, damping: 15, delay: 0.15 }}
        className="mx-auto grid h-16 w-16 place-items-center rounded-lg border border-ember/30 bg-ember-soft"
      >
        <LogOut size={26} className="text-ember" />
      </motion.div>
      <h2 className="mt-5 font-display text-2xl font-semibold text-ink">You're signed out</h2>
      <p className="mt-2 text-sm leading-relaxed text-ink-3">
        Your session was closed and the agent's base URL was restored to its default.
        The proxy on your box keeps running.
      </p>
      <div className="mt-6 flex justify-center gap-3">
        <GradientButton onClick={() => navigate("/login")}>Sign back in</GradientButton>
        <GhostButton onClick={() => navigate("/docs")}>View docs</GhostButton>
      </div>
    </motion.div>
  );
}
