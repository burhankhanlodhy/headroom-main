import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Eye, EyeOff, KeyRound, Plus, Trash2 } from "lucide-react";
import {
  Badge,
  Card,
  CopyButton,
  GhostButton,
  GradientButton,
  Modal,
  SectionHeader,
} from "../components/ui";
import { initialKeys, type ApiKey } from "../data/mock";
import { cn, fmtCompact } from "../lib/utils";

const SCOPES = ["proxy:messages", "proxy:responses", "keys:manage", "stats:read"];

const inputCls =
  "w-full rounded-lg border border-ink/20 bg-ink/5 px-3.5 py-2.5 text-sm text-ink outline-none transition placeholder:text-ink-3 focus:border-ember/50";

export default function ApiKeys() {
  const [keys, setKeys] = useState<ApiKey[]>(initialKeys);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState<string[]>(["proxy:messages", "stats:read"]);
  const [revealed, setRevealed] = useState<Record<string, boolean>>({});

  const maxReq = Math.max(...keys.map((k) => k.requests), 1);

  const create = () => {
    const clean = name.trim();
    if (!clean) return;
    const suffix = Math.random().toString(36).slice(2, 6);
    const k: ApiKey = {
      id: `k_${suffix}`,
      name: clean,
      masked: `hz_live_${suffix.toUpperCase()}••••••••${suffix}`,
      createdAt: "Just now",
      lastUsed: null,
      requests: 0,
      revoked: false,
    };
    setKeys((ks) => [k, ...ks]);
    setName("");
    setOpen(false);
  };

  const revoke = (id: string) =>
    setKeys((ks) => ks.map((k) => (k.id === id ? { ...k, revoked: true } : k)));
  const remove = (id: string) => setKeys((ks) => ks.filter((k) => k.id !== id));

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-xl text-sm text-ink-3">
          Keys issue per-user credentials for the proxy. Loopback and tunnelled clients
          are trusted by default — keys matter when you expose Horizon beyond your
          machine.
        </p>
        <GradientButton onClick={() => setOpen(true)}>
          <Plus size={15} /> Create key
        </GradientButton>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <AnimatePresence initial={false}>
          {keys.map((k) => (
            <motion.div
              key={k.id}
              layout
              initial={{ opacity: 0, y: 16, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.94 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            >
              <Card hairline className={cn("p-5", k.revoked && "opacity-60")}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        "grid h-10 w-10 place-items-center rounded-lg border",
                        k.revoked
                          ? "border-ink/10 bg-ink/5 text-ink-3"
                          : "border-ember/30 bg-ember-soft text-ember",
                      )}
                    >
                      <KeyRound size={17} />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-ink">{k.name}</div>
                      <div className="mt-0.5 flex items-center gap-2 text-[11px] text-ink-3">
                        <span>created {k.createdAt}</span>
                        <span className="h-0.5 w-0.5 rounded-full bg-ink-3" />
                        <span>{k.lastUsed ? `last used ${k.lastUsed}` : "never used"}</span>
                      </div>
                    </div>
                  </div>
                  <Badge tone={k.revoked ? "red" : "green"}>{k.revoked ? "revoked" : "active"}</Badge>
                </div>

                <div className="mt-4 flex items-center gap-2">
                  <code className="min-w-0 flex-1 truncate rounded-lg border border-ink/10 bg-ink/5 px-3 py-2 font-mono text-xs text-ink-2">
                    {revealed[k.id] ? k.masked.replace("••••••••", "Xk29dMm4") : k.masked}
                  </code>
                  <button
                    onClick={() => setRevealed((r) => ({ ...r, [k.id]: !r[k.id] }))}
                    className="rounded-lg border border-ink/10 bg-ink/5 p-2 text-ink-3 transition hover:border-ember/40 hover:text-ink"
                    title={revealed[k.id] ? "Hide" : "Reveal"}
                  >
                    {revealed[k.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                  <CopyButton text={k.masked} />
                </div>

                <div className="mt-4">
                  <div className="mb-1 flex justify-between text-[11px] text-ink-3">
                    <span>{fmtCompact(k.requests)} requests</span>
                    <span>{Math.round((k.requests / maxReq) * 100)}% of busiest key</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-ink/5">
                    <motion.div
                      className={cn(
                        "h-full rounded-full",
                        k.revoked ? "bg-ink-3" : "bg-gradient-to-r from-ember to-sage",
                      )}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.max(3, (k.requests / maxReq) * 100)}%` }}
                      transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1], delay: 0.2 }}
                    />
                  </div>
                </div>

                <div className="mt-4 flex justify-end">
                  {!k.revoked ? (
                    <GhostButton
                      className="border-ember/20 px-3 py-1.5 text-xs text-ember hover:border-ember/50"
                      onClick={() => revoke(k.id)}
                    >
                      Revoke
                    </GhostButton>
                  ) : (
                    <GhostButton
                      className="px-3 py-1.5 text-xs text-ink-3"
                      onClick={() => remove(k.id)}
                    >
                      <Trash2 size={13} /> Delete
                    </GhostButton>
                  )}
                </div>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <Card className="p-6">
        <SectionHeader
          eyebrow="Access"
          title="Default trust model"
          action={<Badge tone="slate">loopback</Badge>}
        />
        <p className="text-sm leading-relaxed text-ink-3">
          Requests arriving over the SSH tunnel present as{" "}
          <code className="rounded bg-ink/5 px-1.5 py-0.5 font-mono text-xs text-ember">
            127.0.0.1
          </code>{" "}
          and pass the proxy's trust boundary without a token. API keys gate network
          exposure — pair them with TLS when the proxy leaves loopback.
        </p>
      </Card>

      <Modal open={open} onClose={() => setOpen(false)} title="Create API key">
        <label className="mb-1.5 block text-xs font-medium text-ink-3">Key name</label>
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. raspberrypi5-proxy"
          className={inputCls}
          onKeyDown={(e) => e.key === "Enter" && create()}
        />
        <label className="mb-2 mt-5 block text-xs font-medium text-ink-3">Scopes</label>
        <div className="flex flex-wrap gap-2">
          {SCOPES.map((s) => {
            const on = scopes.includes(s);
            return (
              <button
                key={s}
                onClick={() =>
                  setScopes((cur) => (on ? cur.filter((x) => x !== s) : [...cur, s]))
                }
                className={cn(
                  "rounded-full border px-3 py-1.5 font-mono text-[11px] transition",
                  on
                    ? "border-ember/50 bg-ember-soft text-ember"
                    : "border-ink/10 bg-ink/5 text-ink-3 hover:text-ink",
                )}
              >
                {s}
              </button>
            );
          })}
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <GhostButton onClick={() => setOpen(false)}>Cancel</GhostButton>
          <GradientButton onClick={create}>
            <KeyRound size={14} /> Create key
          </GradientButton>
        </div>
      </Modal>
    </div>
  );
}
