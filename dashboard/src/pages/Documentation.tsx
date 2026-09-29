import { Badge, Card, CodeBlock, SectionHeader } from "../components/ui";

const ENDPOINTS = [
  { method: "GET", path: "/readyz", desc: "Traffic readiness probe" },
  { method: "GET", path: "/health", desc: "Aggregate health" },
  { method: "GET", path: "/stats", desc: "Live statistics + sessions" },
  { method: "GET", path: "/stats-history", desc: "Durable compression history" },
  { method: "GET", path: "/metrics", desc: "Prometheus metrics" },
  { method: "POST", path: "/v1/messages", desc: "Anthropic Messages + compression" },
  { method: "POST", path: "/v1/chat/completions", desc: "OpenAI-compatible completions" },
];

const QUICKSTART = `# 1 · tunnel to your Pi proxy
.\\connect-horizon-vps.ps1 -VpsHost user@<pi-ip> -LocalPort 18787

# 2 · launch Claude through it (base URL patched for the session)
claude`;

const OPENCODE = `.\\connect-horizon-vps-opencode.ps1 -VpsHost user@<pi-ip>

# under the hood: horizon wrap opencode --no-proxy --port 18787`;

const ENVVAR = `ANTHROPIC_BASE_URL=http://127.0.0.1:18787 claude`;

const WIRE = `// src/data/mock.ts → live proxy data
const res = await fetch("http://127.0.0.1:18787/stats-history");
const { lifetime, daily } = await res.json();`;

function MethodChip({ method }: { method: string }) {
  return (
    <span
      className={
        method === "GET"
          ? "inline-block rounded-md border border-emerald-400/25 bg-emerald-400/10 px-2 py-0.5 font-mono text-[10px] font-semibold text-emerald-300"
          : "inline-block rounded-md border border-indigo-400/25 bg-indigo-400/10 px-2 py-0.5 font-mono text-[10px] font-semibold text-indigo-300"
      }
    >
      {method}
    </span>
  );
}

export default function Documentation() {
  return (
    <div className="flex flex-col gap-6">
      <Card hairline className="p-7">
        <SectionHeader eyebrow="Docs" title="Point any agent at Horizon" />
        <p className="max-w-2xl text-sm leading-relaxed text-slate-400">
          Horizon sits between your agent and the provider: it compresses context,
          preserves cache prefixes, and records every token saved. The proxy binds to
          loopback only — the SSH tunnel is the security boundary, so no token is
          needed for tunneled clients.
        </p>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card hairline className="p-6">
          <SectionHeader eyebrow="Claude Code" title="Tunnel + launch" />
          <CodeBlock code={QUICKSTART} />
          <p className="mt-3 text-xs text-slate-500">
            The connect script opens the tunnel, patches{" "}
            <code className="font-mono text-indigo-200">settings.json</code> for the
            session, and restores it on exit.
          </p>
        </Card>
        <Card hairline className="p-6">
          <SectionHeader eyebrow="OpenCode" title="Tunnel + wrap" />
          <CodeBlock code={OPENCODE} />
          <p className="mt-3 text-xs text-slate-500">
            Wrap injects the Horizon provider, the{" "}
            <code className="font-mono text-indigo-200">horizon_retrieve</code> MCP and
            Serena into OpenCode's config — restored by unwrap.
          </p>
        </Card>
      </div>

      <Card className="p-6">
        <SectionHeader eyebrow="Fallback" title="Any Anthropic-compatible client" />
        <CodeBlock code={ENVVAR} className="max-w-2xl" />
        <p className="mt-3 text-xs text-slate-500">
          Process env alone isn't always picked up — for Claude Code, prefer the
          connect script (it routes through the user settings env block).
        </p>
      </Card>

      <Card className="overflow-hidden">
        <div className="px-6 pt-6">
          <SectionHeader
            eyebrow="Reference"
            title="Proxy endpoints"
            action={<Badge tone="slate">loopback · 8787</Badge>}
          />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-y border-white/5 text-[11px] uppercase tracking-wider text-slate-500">
                <th className="px-6 py-3 font-medium">Method</th>
                <th className="py-3 font-medium">Path</th>
                <th className="px-6 py-3 font-medium">Description</th>
              </tr>
            </thead>
            <tbody>
              {ENDPOINTS.map((e) => (
                <tr
                  key={e.path}
                  className="border-b border-white/5 transition last:border-0 hover:bg-white/[0.03]"
                >
                  <td className="px-6 py-3">
                    <MethodChip method={e.method} />
                  </td>
                  <td className="py-3 font-mono text-xs text-slate-200">{e.path}</td>
                  <td className="px-6 py-3 text-slate-400">{e.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="p-6">
        <SectionHeader eyebrow="Wiring" title="Connect this dashboard to live data" />
        <p className="mb-4 max-w-2xl text-sm leading-relaxed text-slate-400">
          Every page reads from{" "}
          <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-xs text-indigo-200">
            src/data/mock.ts
          </code>
          . Its shapes mirror the proxy's endpoints, so going live is a single-file
          swap — replace the mocks with fetches and the UI keeps working unchanged.
        </p>
        <CodeBlock code={WIRE} className="max-w-2xl" />
      </Card>
    </div>
  );
}
