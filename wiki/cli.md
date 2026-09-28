# CLI Reference

This page is the authoritative reference for the **Python Horizon CLI** exposed by the `horizon` console script.

> **Audit note (2026-09-02):** `horizon --help` on this branch lists 30 top-level
> commands; this page documents 15 of them and omits `agent-savings`,
> `audit-reads`, `capture`, `copilot-auth`, `dashboard`, `deploy`, `diff`,
> `doctor`, `init`, `loc`, `output-savings`, `recover`, `rollout`, `savings`,
> `sg`, `tools`, and `update` entirely. The `horizon proxy` and
> `horizon install apply` option tables below are similarly stale — `proxy
> --help` alone now runs to ~90 options vs. the ~30 documented here. Treat the
> command list and captured `--help` blocks in this file as historical
> snapshots, not current reference; verify against `horizon <cmd> --help`
> before relying on any option in this file. See the audit report for detail.

## Global behavior

### Entry points

- Console script: `horizon`
- Python module entrypoint: `python -m horizon.cli`

### Global options

| Option | Scope | Meaning |
|---|---|---|
| `--help`, `-?` | root, groups, commands | Show help and exit |
| `--version`, `-v` | root only | Show the Horizon version and exit |

> `-v` is a **root-level version alias**. Inside subcommands such as `horizon wrap claude -v`, `-v` keeps its subcommand meaning (`--verbose`), not version.

## Command index

| Command | Purpose | Docker-native parity |
|---|---|---|
| `horizon install ...` | Install and manage persistent deployments | **python-native; Docker-native wrapper supports `persistent-docker` lifecycle subset** |
| `horizon proxy` | Run the Horizon proxy server | **native in container** |
| `horizon learn` | Learn from past tool-call failures | **native in container** |
| `horizon perf` | Summarize recent proxy performance | **native in container** |
| `horizon inspect` | Show original vs compressed content for recent requests | **native in container** |
| `horizon evals ...` | Run memory evaluation workflows | **native in container** |
| `horizon memory ...` | Inspect and manage stored memories | **native in container** |
| `horizon mcp ...` | Install, inspect, remove, or serve MCP integration | **native in container** |
| `horizon wrap claude` | Start proxy and launch Claude Code | **host-bridged** |
| `horizon wrap copilot` | Start proxy and launch GitHub Copilot CLI | **python-native only** |
| `horizon wrap codex` | Start proxy and launch Codex CLI | **host-bridged** |
| `horizon wrap aider` | Start proxy and launch Aider | **host-bridged** |
| `horizon wrap cursor` | Start proxy and print Cursor config guidance | **host-bridged** |
| `horizon wrap openclaw` | Install and configure the OpenClaw plugin | **host-bridged** |
| `horizon unwrap openclaw` | Disable the Horizon OpenClaw plugin | **host-bridged** |

## Captured `--help` output

The sections below capture the current top-level help output from the live CLI.

### `horizon --help`

```text
Usage: horizon [OPTIONS] COMMAND [ARGS]...

  Horizon - The Context Optimization Layer for LLM Applications.

  Manage memories, run the optimization proxy, and analyze metrics.

  Examples:
      horizon proxy              Start the optimization proxy
      horizon memory list        List stored memories
      horizon memory stats       Show memory statistics
      horizon update             Update Horizon to the latest release

Options:
  -v, --version  Show the version and exit.
  -?, --help     Show this message and exit.

Commands:
  agent-savings   Render or verify Codex/Claude/Cursor token-savings...
  audit-reads     Audit Read-tool traffic for compression opportunities.
  capture         Capture and compare network traffic for Horizon...
  copilot-auth    Manage Horizon's GitHub Copilot OAuth token.
  dashboard       Open the Horizon savings dashboard in your browser.
  deploy          Deploy a turnkey local Horizon proxy and configure...
  diff            Run difftastic (structural diff).
  doctor          Check that the Horizon proxy and client routing are...
  evals           Evaluation commands (memory, compression robustness,...
  init            Install durable Horizon integrations for supported...
  inspect         Show original vs compressed content for recent proxy...
  install         Install and manage persistent Horizon deployments.
  learn           Learn from past tool call failures to prevent future ones.
  loc             Run scc (fast lines-of-code / repo-shape probe).
  mcp             MCP server for Claude Code integration.
  memory          Manage memories stored in Horizon.
  output-savings  Show estimated/measured output-token reduction from the...
  perf            Analyze proxy performance from logs.
  proxy           Start the optimization proxy server.
  recover         Recover agent state left in a temporary Horizon home.
  rollout         Inspect runtime feature-rollout policy (not package...
  savings         Show durable compression savings over time.
  sg              Run ast-grep (AST-aware structural search/replace).
  tools           Manage bundled CLI tool binaries (ast-grep, difft, scc).
  unwrap          Undo durable Horizon wrapping for supported tools.
  update          Update Horizon to the latest release.
  wrap            Wrap CLI tools to run through Horizon.
```

Captured from `horizon --help` on this branch, 2026-09-02 (`horizon/cli/main.py`,
per-command modules under `horizon/cli/`). None of `agent-savings`,
`audit-reads`, `capture`, `copilot-auth`, `dashboard`, `deploy`, `diff`,
`doctor`, `init`, `loc`, `output-savings`, `recover`, `rollout`, `savings`,
`sg`, `tools`, or `update` is documented elsewhere in this file.

### Top-level command help snapshots

<details>
<summary><code>horizon proxy --help</code></summary>

```text
Usage: horizon proxy [OPTIONS]

  Start the optimization proxy server.

  Examples:
      horizon proxy                    Start proxy on port 8787
      horizon proxy --port 8080        Start proxy on port 8080
      horizon proxy --no-optimize      Passthrough mode (no optimization)

  Usage with Claude Code:
      ANTHROPIC_BASE_URL=http://localhost:8787 claude

  Usage with OpenAI-compatible clients:
      OPENAI_BASE_URL=http://localhost:8787/v1 your-app
```

</details>

<details>
<summary><code>horizon learn --help</code></summary>

```text
Usage: horizon learn [OPTIONS]

  Learn from past tool call failures to prevent future ones.
```

</details>

<details>
<summary><code>horizon perf --help</code></summary>

```text
Usage: horizon perf [OPTIONS]

  Analyze proxy performance from logs.
```

</details>

<details>
<summary><code>horizon evals --help</code></summary>

```text
Usage: horizon evals [OPTIONS] COMMAND [ARGS]...

  Memory evaluation commands.

Commands:
  memory     Run LoCoMo memory evaluation benchmark.
  memory-v2  Run LoCoMo V2 evaluation with LLM-controlled memory tools.
```

</details>

<details>
<summary><code>horizon memory --help</code></summary>

```text
Usage: horizon memory [OPTIONS] COMMAND [ARGS]...

  Manage memories stored in Horizon.

Commands:
  delete  Delete one or more memories by ID.
  edit    Edit a memory's content or importance.
  export  Export all memories to JSON.
  import  Import memories from a JSON file.
  list    List stored memories with optional filters.
  prune   Prune memories matching specified criteria.
  purge   Delete ALL memories from the database.
  show    Show full details of a single memory.
  stats   Show memory store statistics.
```

</details>

<details>
<summary><code>horizon mcp --help</code></summary>

```text
Usage: horizon mcp [OPTIONS] COMMAND [ARGS]...

  MCP server for Claude Code integration.

Commands:
  install    Install Horizon MCP server into Claude Code config.
  serve      Start the MCP server (called by Claude Code).
  status     Check Horizon MCP configuration status.
  uninstall  Remove Horizon MCP server from Claude Code config.
```

</details>

<details>
<summary><code>horizon install --help</code></summary>

```text
Usage: horizon install [OPTIONS] COMMAND [ARGS]...

  Install and manage persistent Horizon deployments.

Options:
  -?, --help  Show this message and exit.

Commands:
  apply    Install a persistent Horizon deployment.
  remove   Remove a persistent deployment and undo managed config.
  restart  Restart a persistent deployment.
  start    Start a persistent deployment.
  status   Show persistent deployment status.
  stop     Stop a persistent deployment.
```

</details>

<details>
<summary><code>horizon wrap --help</code></summary>

```text
Usage: horizon wrap [OPTIONS] COMMAND [ARGS]...

  Wrap CLI tools to run through Horizon.

Commands:
  aider     Launch aider through Horizon proxy.
  claude    Launch Claude Code through Horizon proxy.
  copilot   Launch GitHub Copilot CLI through Horizon proxy.
  codex     Launch OpenAI Codex CLI through Horizon proxy.
  cursor    Start Horizon proxy for use with Cursor.
  openclaw  Install and configure Horizon OpenClaw plugin in one command.
```

</details>

<details>
<summary><code>horizon unwrap --help</code></summary>

```text
Usage: horizon unwrap [OPTIONS] COMMAND [ARGS]...

  Undo durable Horizon wrapping for supported tools.

Commands:
  openclaw  Disable the Horizon OpenClaw plugin and restore the legacy engine slot.
```

</details>

## `horizon proxy`

Start the optimization proxy server.

```bash
horizon proxy
horizon proxy --port 8787
horizon proxy --mode cache
```

| Option | Default | Meaning |
|---|---|---|
| `--host` | `127.0.0.1` | Host interface to bind |
| `--port`, `-p` | `8787` | Port to bind |
| `--mode` | runtime default | Optimization mode: `token`, `cache`, `token_mode`, `cache_mode`, `token_savings`, `cost_savings`, `token_horizon` |
| `--no-optimize` | off | Disable optimization and operate in passthrough mode |
| `--no-cache` | off | Disable semantic caching |
| `--no-rate-limit` | off | Disable rate limiting |
| `--retry-max-attempts` | runtime default `3` | Maximum upstream retry attempts |
| `--request-timeout-seconds` | runtime default `300` | Request timeout in seconds |
| `--connect-timeout-seconds` | runtime default `10` | Upstream connection timeout |
| `--anthropic-pre-upstream-concurrency` | auto `max(2, min(8, cpu_count))` | Cap simultaneous pre-upstream work on `/v1/messages` (body read, deep copy, first compression stage, memory-context lookup, upstream connect). `0` or negative disables (unbounded); any positive integer is honoured verbatim. Prevents cold-start replay storms from starving `/livez`, `/readyz`, and new Codex WS opens. |
| `--anthropic-pre-upstream-acquire-timeout-seconds` | `15.0` | Fail fast when the Anthropic pre-upstream queue is saturated. Requests that wait longer return `503` with `Retry-After` instead of parking indefinitely. |
| `--anthropic-pre-upstream-memory-context-timeout-seconds` | `2.0` | Fail-open timeout for Anthropic memory-context lookup while the request still holds a pre-upstream slot. |
| `--log-file` | unset | JSONL log output path |
| `--budget` | unset | Daily USD budget limit |
| `--no-code-aware` | off | Disable AST-aware code compression |
| `--code-aware` | off | Enable code-aware compression in the proxy (env: HORIZON_CODE_AWARE_ENABLED) |
| `--no-read-lifecycle` | off | Disable stale/superseded read compression |
| `--no-ccr` | off | Disable CCR entirely — no retrieval markers in content and no injected `horizon_retrieve` tool (lossy, no recovery path) |
| `--no-ccr-proactive-expansion` | off | Disable proactive CCR context expansion |
| `--memory` | off | Enable persistent user memory |
| `--memory-db-path` | `""` | Override memory DB path (help text: `{cwd}/.horizon/memory.db`) |
| `--no-memory-tools` | off | Disable automatic memory tool injection |
| `--no-memory-context` | off | Disable automatic memory context injection |
| `--memory-top-k` | `10` | Number of memories to inject |
| `--learn` | off | Enable live traffic learning |
| `--no-learn` | off | Explicitly disable traffic learning |
| `--backend` | `anthropic` | Backend: `anthropic`, `bedrock`, `openrouter`, `anyllm`, or `litellm-*` |
| `--anyllm-provider` | `openai` | Provider name for `anyllm` |
| `--anthropic-api-url` | unset | Custom Anthropic passthrough API URL |
| `--openai-api-url` | unset | Custom OpenAI passthrough API URL |
| `--anthropic-extra-headers` | unset | JSON object of extra headers merged into (and overriding) forwarded Anthropic requests |
| `--openai-extra-headers` | unset | JSON object of extra headers merged into (and overriding) forwarded OpenAI requests |
| `--gemini-api-url` | unset | Custom Gemini passthrough API URL |
| `--region` | `us-west-2` | Cloud region for Bedrock / Vertex / related backends |
| `--bedrock-region` | unset | Deprecated Bedrock region override |
| `--bedrock-profile` | unset | AWS profile name for Bedrock |
| `--telemetry` | off | Opt in to anonymous usage telemetry (off by default) |
| `--no-telemetry` | off | Force anonymous usage telemetry off (already the default) |

Notes:

- `--learn` implies memory unless `--no-learn` is also set.
- Proxy startup can also read environment variables such as `HORIZON_HOST`, `HORIZON_PORT`, `HORIZON_BUDGET`, `HORIZON_MODE`, `HORIZON_ANYLLM_PROVIDER`, `HORIZON_ANTHROPIC_PRE_UPSTREAM_CONCURRENCY`, `HORIZON_ANTHROPIC_PRE_UPSTREAM_ACQUIRE_TIMEOUT_SECONDS`, `HORIZON_REQUEST_TIMEOUT`, `HORIZON_ANTHROPIC_PRE_UPSTREAM_MEMORY_CONTEXT_TIMEOUT_SECONDS`, `ANTHROPIC_TARGET_API_URL`, `OPENAI_TARGET_API_URL`, `GEMINI_TARGET_API_URL`, `ANTHROPIC_TARGET_API_HEADERS`, and `OPENAI_TARGET_API_HEADERS`. CLI flags take precedence over environment variables.
- The default Anthropic pre-upstream cap is intentionally conservative for CPU/ONNX-heavy work. Larger containers may want to raise it after checking the resolved runtime values on `/readyz` or `/debug/warmup`.

See also: [Proxy Server](proxy.md), [Configuration](configuration.md)

## `horizon learn`

Learn from past tool-call failures and produce agent guidance.

```bash
horizon learn
horizon learn --apply
horizon learn --agent codex --all
```

| Option | Default | Meaning |
|---|---|---|
| `--project` | current project resolution | Target project path |
| `--all` | off | Analyze all discovered projects |
| `--apply` | off | Write recommendations instead of dry-run output |
| `--agent` | `auto` | Agent source: `auto`, built-ins (`claude`, `codex`, `gemini`), or plugin-provided names |
| `--model` | auto-detect | LLM model used for analysis |

Notes:

- `--agent auto` scans all detected agent data sources.
- If `--project` is omitted, Horizon resolves from the current directory upward.
- External agent integrations register through the `horizon.learn_plugin` entry point.

See also: [Failure Learning](learn.md)

## `horizon perf`

Summarize recent proxy performance from the local proxy log.

```bash
horizon perf
horizon perf --hours 24
horizon perf --raw
```

| Option | Default | Meaning |
|---|---|---|
| `--hours` | `168.0` | Time window in hours |
| `--raw` | off | Print raw PERF records instead of the summarized report |

The command reads each per-port runtime log
`${HORIZON_WORKSPACE_DIR}/logs/proxy-<port>.log` (defaults to
`~/.horizon/logs/`) plus PID-qualified files from multi-worker deployments,
aggregating them while still reading a legacy `proxy.log` when present — see the
[Filesystem Contract](filesystem-contract.md)).

## `horizon inspect`

Show the original vs compressed content for recent requests so you can *see*
what the compressor changed (not just the token counts). Useful for building
trust in compression and debugging quality regressions.

```bash
horizon inspect                 # inspect the most recent request
horizon inspect --last 5        # inspect the 5 most recent requests
horizon inspect --full          # include unchanged messages
horizon inspect --format json   # raw feed for piping into another tool
```

| Option | Default | Meaning |
|---|---|---|
| `--port` / `-p` | `8787` | Proxy port to query (env: `HORIZON_PORT`) |
| `--last` | `1` | Number of most-recent requests to show |
| `--format` | `text` | `text` renders a highlighted diff; `json` emits the raw feed |
| `--full` | off | Include messages the compressor left unchanged |

`inspect` queries the running proxy's loopback `/transformations/feed` endpoint,
so the proxy must be started with `--log-messages` (or `--log-file`) for the
pre/post-compression snapshots to be captured.

## `horizon evals`

Memory evaluation command group.

### `horizon evals memory`

Run the LoCoMo memory evaluation benchmark.

```bash
horizon evals memory -n 3
horizon evals memory --answer-model gpt-4o --llm-judge
```

| Option | Default | Meaning |
|---|---|---|
| `--n-conversations`, `-n` | all available | Number of conversations to evaluate |
| `--categories` | benchmark default | Comma-separated categories |
| `--include-adversarial` | off | Include category 5 / unanswerable questions |
| `--top-k` | `10` | Memories retrieved per question |
| `--f1-threshold` | `0.5` | Threshold for correctness |
| `--answer-model` | unset | Model for answer generation |
| `--llm-judge` | off | Use LLM-as-judge scoring |
| `--judge-provider` | `litellm` | Judge provider: `openai`, `anthropic`, `litellm`, `simple` |
| `--judge-model` | `gpt-4o` | Judge model |
| `--output`, `-o` | unset | Save JSON results to a path |
| `--no-extract` | off | Disable LLM memory extraction |
| `--extraction-model` | `gpt-4o-mini` | Memory extraction model |
| `--pass-all` | off | Require all checks to pass |
| `--parallel` | `10` | Parallel worker count |
| `--debug` | off | Enable debug output |

### `horizon evals memory-v2`

Run the V2 memory evaluation flow with LLM-controlled tools.

```bash
horizon evals memory-v2
horizon evals memory-v2 --save-model gpt-4o-mini --llm-judge
```

| Option | Default | Meaning |
|---|---|---|
| `--n-conversations`, `-n` | all available | Number of conversations to evaluate |
| `--categories` | benchmark default | Comma-separated categories |
| `--include-adversarial` | off | Include adversarial questions |
| `--f1-threshold` | `0.5` | Threshold for correctness |
| `--save-model` | `gpt-4o-mini` | Model used when persisting memories |
| `--answer-model` | `gpt-4o` | Answer model |
| `--max-results` | `10` | Maximum tool results |
| `--no-graph` | off | Disable graph usage |
| `--llm-judge` | off | Use LLM-as-judge scoring |
| `--judge-model` | `gpt-4o` | Judge model |
| `--output`, `-o` | unset | Save JSON results |
| `--parallel` | `5` | Parallel worker count |
| `--debug` | off | Enable debug output |

Hidden compatibility shims exist for older command paths:

- `horizon memory-eval`
- `horizon memory-eval-v2`

These are intentionally omitted from normal usage docs.

## `horizon memory`

Memory management command group. This group is only registered when the optional memory dependencies import successfully.

### `horizon memory list`

```bash
horizon memory list
horizon memory list --scope USER --since 7d
horizon memory list -q "budget"
```

| Option | Default | Meaning |
|---|---|---|
| `--db-path` | `./.horizon/memory.db` if present, else `~/.horizon/memory.db` | Memory database path |
| `--limit`, `-n` | `50` | Maximum memories to show |
| `--session`, `-s` | unset | Filter by session ID |
| `--scope` | unset | `USER`, `SESSION`, `AGENT`, or `TURN` |
| `--since` | unset | Age filter using duration syntax such as `7d`, `2w`, `1m` |
| `--search`, `-q` | unset | Content search query |

### `horizon memory show <memory_id>`

```bash
horizon memory show 1234abcd
horizon memory show 1234abcd --json
```

| Argument / option | Default | Meaning |
|---|---|---|
| `memory_id` | required | Full or partial memory ID |
| `--db-path` | `./.horizon/memory.db` if present, else `~/.horizon/memory.db` | Memory database path |
| `--json` | off | Emit raw JSON |

### `horizon memory stats`

```bash
horizon memory stats
```

| Option | Default | Meaning |
|---|---|---|
| `--db-path` | `./.horizon/memory.db` if present, else `~/.horizon/memory.db` | Memory database path |

### `horizon memory edit <memory_id>`

```bash
horizon memory edit 1234abcd --content "Updated note"
horizon memory edit 1234abcd --importance 0.9
```

| Argument / option | Default | Meaning |
|---|---|---|
| `memory_id` | required | Full or partial memory ID |
| `--db-path` | `./.horizon/memory.db` if present, else `~/.horizon/memory.db` | Memory database path |
| `--content`, `-c` | unset | New memory content |
| `--importance`, `-i` | unset | New importance score (`0.0` to `1.0`) |

At least one of `--content` or `--importance` is required.

### `horizon memory delete <memory_ids...>`

```bash
horizon memory delete 1234abcd 5678efgh
horizon memory delete 1234abcd --force
```

| Argument / option | Default | Meaning |
|---|---|---|
| `memory_ids...` | required | One or more memory IDs |
| `--db-path` | `./.horizon/memory.db` if present, else `~/.horizon/memory.db` | Memory database path |
| `--force`, `-f` | off | Skip confirmation |

### `horizon memory prune`

```bash
horizon memory prune --older-than 30d --dry-run
horizon memory prune --scope SESSION --force
```

| Option | Default | Meaning |
|---|---|---|
| `--db-path` | `./.horizon/memory.db` if present, else `~/.horizon/memory.db` | Memory database path |
| `--older-than` | unset | Age threshold |
| `--scope` | unset | Scope filter: `USER`, `SESSION`, `AGENT`, `TURN` |
| `--low-importance` | unset | Importance cutoff |
| `--session`, `-s` | unset | Session ID filter |
| `--dry-run` | off | Show what would be removed |
| `--force`, `-f` | off | Skip confirmation |

At least one filter is required. Filters combine with **AND** semantics.

### `horizon memory purge`

```bash
horizon memory purge --confirm
```

| Option | Default | Meaning |
|---|---|---|
| `--db-path` | `./.horizon/memory.db` if present, else `~/.horizon/memory.db` | Memory database path |
| `--confirm` | off | Required confirmation flag |

### `horizon memory export`

```bash
horizon memory export
horizon memory export --output export.json
```

| Option | Default | Meaning |
|---|---|---|
| `--db-path` | `./.horizon/memory.db` if present, else `~/.horizon/memory.db` | Memory database path |
| `--output`, `-o` | stdout | Output path |

### `horizon memory import <file>`

```bash
horizon memory import export.json
horizon memory import export.json --force
```

| Argument / option | Default | Meaning |
|---|---|---|
| `file` | required | JSON file containing exported memories |
| `--db-path` | `./.horizon/memory.db` if present, else `~/.horizon/memory.db` | Memory database path |
| `--force`, `-f` | off | Skip confirmation |

The import expects a JSON array. Malformed entries are skipped.

## `horizon mcp`

Manage the Horizon MCP server integration.

### `horizon mcp install`

```bash
horizon mcp install
horizon mcp install --proxy-url http://127.0.0.1:9000
```

| Option | Default | Meaning |
|---|---|---|
| `--proxy-url` | `http://127.0.0.1:8787` | Proxy URL written into MCP config |
| `--force` | off | Overwrite an existing Horizon MCP config |

### `horizon mcp uninstall`

```bash
horizon mcp uninstall
```

This removes the Horizon MCP server entry from the Claude configuration.

### `horizon mcp status`

```bash
horizon mcp status
```

This inspects MCP SDK availability, Claude config state, and proxy reachability.

### `horizon mcp serve`

```bash
horizon mcp serve
horizon mcp serve --proxy-url http://127.0.0.1:9000 --debug
```

| Option | Default | Meaning |
|---|---|---|
| `--proxy-url` | `http://127.0.0.1:8787` | Proxy URL (also reads `HORIZON_PROXY_URL`) |
| `--direct` | off | Disable stdio transport wrapping |
| `--debug` | off | Enable debug logging |

`serve` is part of the public CLI, but it is usually consumed by MCP host tooling rather than by humans directly.

See also: [MCP Tools](mcp.md)

## `horizon install`

Install and manage persistent local Horizon deployments.

### `horizon install apply --help`

```text
Usage: horizon install apply [OPTIONS]

  Install a persistent Horizon deployment.

Options:
  --preset [persistent-service|persistent-task|persistent-docker]
                                  Persistent runtime preset to install.
                                  [default: persistent-service]
  --runtime [python|docker]       Runtime used to execute Horizon for
                                  service/task modes.  [default: python]
  --scope [provider|user|system]  Where to apply persistent configuration.
                                  [default: user]
  --providers [auto|all|manual]   Target selection mode for direct tool
                                  configuration.  [default: auto]
  --target [claude|copilot|codex|aider|cursor|openclaw]
                                  Tool target to configure when --providers
                                  manual is used.
  --profile TEXT                  Deployment profile name.  [default: default]
  -p, --port INTEGER              Persistent proxy port.  [default: 8787]
  --backend TEXT                  Proxy backend for the persistent runtime.
                                  [default: anthropic]
  --anyllm-provider TEXT          Provider for any-llm backends when --backend
                                  anyllm is used.
  --region TEXT                   Cloud region for Bedrock / Vertex style
                                  backends.
  --mode TEXT                     Proxy optimization mode.  [default: token]
  --memory                        Enable persistent memory in the proxy runtime.
  --telemetry                     Opt in to anonymous telemetry in the runtime
                                  (off by default).
  --no-telemetry                  Force anonymous telemetry off in the runtime
                                  (already the default).
  --image TEXT                    Docker image to use when runtime=docker or
                                  preset=persistent-docker.  [default:
                                  ghcr.io/your-org/horizon:latest]
  -?, --help                      Show this message and exit.
```

### `horizon install apply`

```bash
horizon install apply --preset persistent-service --providers auto
horizon install apply --preset persistent-task --providers manual --target claude --target codex
horizon install apply --preset persistent-docker --scope user
```

| Option | Default | Meaning |
|---|---|---|
| `--preset` | `persistent-service` | Lifecycle preset: `persistent-service`, `persistent-task`, or `persistent-docker` |
| `--runtime` | `python` | Runtime used for service/task installs: `python` or `docker` |
| `--scope` | `user` | Config scope: `provider`, `user`, or `system` |
| `--providers` | `auto` | Target selection mode: `auto`, `all`, or `manual` |
| `--target` | repeatable | Tool target used with `--providers manual` |
| `--profile` | `default` | Deployment profile name |
| `--port`, `-p` | `8787` | Persistent proxy port |
| `--backend` | `anthropic` | Backend for the managed runtime |
| `--anyllm-provider` | unset | Provider name used with `--backend anyllm` |
| `--region` | unset | Cloud region override |
| `--mode` | `token` | Proxy optimization mode |
| `--memory` | off | Enable persistent memory in the managed runtime |
| `--telemetry` | off | Opt in to anonymous telemetry (off by default) |
| `--no-telemetry` | off | Force anonymous telemetry off (already the default) |
| `--image` | `ghcr.io/your-org/horizon:latest` | Docker image for Docker-backed installs |

`apply` stores a manifest under
`${HORIZON_WORKSPACE_DIR}/deploy/<profile>/manifest.json` (default
`~/.horizon/deploy/<profile>/manifest.json`), applies managed tool
configuration, starts the chosen runtime, and waits for `readyz`.

Docker-native host wrappers expose a narrower `horizon install` subset for `persistent-docker` only: `apply`, `status`, `start`, `stop`, `restart`, and `remove`. Those wrapper flows preserve the same port and manifest behavior, but they intentionally reject `persistent-service`, `persistent-task`, and provider mutation flags like `--scope`, `--providers`, and `--target`.

### `horizon install status`

```bash
horizon install status
horizon install status --profile default
```

Shows the stored profile, preset, runtime, supervisor kind, scope, port, runtime status, readiness, and backend from `/health`.

### `horizon install start`

```bash
horizon install start
horizon install start --profile default
```

Starts a previously installed deployment profile without reapplying mutations.

### `horizon install stop`

```bash
horizon install stop
```

Stops the managed runtime for an installed deployment profile.

### `horizon install restart`

```bash
horizon install restart
```

Stops and starts the selected deployment profile.

### `horizon install remove`

```bash
horizon install remove
```

Stops the runtime, removes installed supervisor artifacts, reverts managed configuration changes, and deletes the stored manifest.

See also: [Persistent Installs](persistent-installs.md)

## `horizon wrap`

Wrap external coding tools so their traffic flows through Horizon.

### Shared semantics

- `--port`, when available, defaults to `8787`
- `--no-proxy` skips proxy startup and assumes an existing proxy
- `--learn` enables live traffic learning
- `-v`, `--verbose` means **verbose output**
- Hidden `--prepare-only` exists for internal Docker-native bridge flows and is intentionally omitted from normal usage

### `horizon wrap claude`

```bash
horizon wrap claude
horizon wrap claude --resume <session-id>
horizon wrap claude --port 9999
```

| Option / arg | Default | Meaning |
|---|---|---|
| `--port`, `-p` | `8787` | Proxy port |
| `--no-proxy` | off | Reuse an existing proxy |
| `--learn` | off | Enable live traffic learning |
| `--verbose`, `-v` | off | Verbose output |
| `claude_args...` | passthrough | Additional Claude Code arguments |

Requires the `claude` binary on the host.

### `horizon wrap codex`

```bash
horizon wrap codex
horizon wrap codex -- "fix the bug"
horizon wrap codex --backend anyllm --anyllm-provider groq
```

| Option / arg | Default | Meaning |
|---|---|---|
| `--port`, `-p` | `8787` | Proxy port |
| `--no-proxy` | off | Reuse an existing proxy |
| `--learn` | off | Enable live traffic learning |
| `--backend` | unset | Proxy backend override |
| `--anyllm-provider` | unset | `anyllm` provider override |
| `--region` | unset | Cloud region override |
| `--verbose`, `-v` | off | Verbose output |
| `codex_args...` | passthrough | Additional Codex CLI arguments |

Requires the `codex` binary on the host.

### `horizon wrap copilot`

```bash
horizon wrap copilot -- --model claude-sonnet-4-20250514
horizon wrap copilot --backend anyllm --anyllm-provider groq -- --model gpt-4o
```

| Option / arg | Default | Meaning |
|---|---|---|
| `--port`, `-p` | `8787` | Proxy port |
| `--no-proxy` | off | Reuse an existing proxy |
| `--learn` | off | Enable live traffic learning |
| `--backend` | unset | Proxy backend override |
| `--anyllm-provider` | unset | `anyllm` provider override |
| `--region` | unset | Cloud region override |
| `--provider-type` | `auto` | Force Copilot BYOK provider type (`anthropic` or `openai`) |
| `--wire-api` | unset | OpenAI wire API override for OpenAI-style backends |
| `--verbose`, `-v` | off | Verbose output |
| `copilot_args...` | passthrough | Additional Copilot CLI arguments |

Requires the `copilot` binary on the host. When a matching persistent deployment exists on the requested port, `wrap copilot` reuses or recovers it before falling back to an ephemeral proxy.

### `horizon wrap aider`

```bash
horizon wrap aider
horizon wrap aider -- --model gpt-4o
horizon wrap aider --backend litellm-vertex --region us-central1
```

| Option / arg | Default | Meaning |
|---|---|---|
| `--port`, `-p` | `8787` | Proxy port |
| `--no-proxy` | off | Reuse an existing proxy |
| `--learn` | off | Enable live traffic learning |
| `--backend` | unset | Proxy backend override |
| `--anyllm-provider` | unset | `anyllm` provider override |
| `--region` | unset | Cloud region override |
| `--verbose`, `-v` | off | Verbose output |
| `aider_args...` | passthrough | Additional Aider arguments |

Requires the `aider` binary on the host.

### `horizon wrap cursor`

```bash
horizon wrap cursor
horizon wrap cursor --port 9999
```

| Option | Default | Meaning |
|---|---|---|
| `--port`, `-p` | `8787` | Proxy port |
| `--no-proxy` | off | Reuse an existing proxy |
| `--learn` | off | Enable live traffic learning |
| `--verbose`, `-v` | off | Verbose output |

This command prints Cursor configuration instructions and waits while the proxy stays up. It does **not** launch Cursor directly.

### `horizon wrap openclaw`

```bash
horizon wrap openclaw
horizon wrap openclaw --plugin-path ./plugins/openclaw
```

| Option | Default | Meaning |
|---|---|---|
| `--plugin-path` | unset | Local plugin source directory |
| `--plugin-spec` | `horizon-ai/openclaw` | NPM plugin spec |
| `--skip-build` | off | Skip local `npm install` / build steps |
| `--copy` | off | Copy plugin instead of linked install |
| `--proxy-port` | `8787` | Horizon proxy port |
| `--startup-timeout-ms` | `20000` | Proxy startup timeout |
| `--gateway-provider-id` | repeatable | OpenClaw provider IDs routed through Horizon |
| `--python-path` | unset | Python launcher override |
| `--no-auto-start` | off | Disable plugin auto-start behavior |
| `--no-restart` | off | Do not restart the OpenClaw gateway |
| `--verbose`, `-v` | off | Verbose output |

Requires the `openclaw` binary on the host, and local-source mode may also require `npm`. In Docker-native mode, the installed host wrapper drives the host `openclaw` CLI while the plugin auto-starts the host `horizon` wrapper from `PATH`.

## `horizon unwrap`

Undo durable wrapping for supported tools.

### `horizon unwrap openclaw`

```bash
horizon unwrap openclaw
horizon unwrap openclaw --no-restart
```

| Option | Default | Meaning |
|---|---|---|
| `--no-restart` | off | Do not restart the OpenClaw gateway |
| `--verbose`, `-v` | off | Verbose output |

This disables the Horizon OpenClaw plugin and restores the legacy context engine slot.

## Docker-native parity matrix

This matrix compares the **Python CLI contract** to the Docker-native host wrapper added in this branch.

Legend:

- **native in container** — the command runs entirely inside the Horizon container
- **host-bridged** — Horizon runs in Docker, but the wrapped external tool still runs on the host

| Command path | Python CLI | Docker-native wrapper | Parity |
|---|---|---|---|
| `horizon proxy` | native | native in container | full |
| `horizon learn` | native | native in container | full |
| `horizon perf` | native | native in container | full |
| `horizon evals memory` | native | native in container | full |
| `horizon evals memory-v2` | native | native in container | full |
| `horizon memory ...` | native (when memory deps are available) | native in container | full |
| `horizon mcp install` | native | native in container | full |
| `horizon mcp uninstall` | native | native in container | full |
| `horizon mcp status` | native | native in container | full |
| `horizon mcp serve` | native | native in container | full |
| `horizon install apply|status|start|stop|restart|remove` | native | Docker-native wrapper for `persistent-docker`; compose remains an alternative | partial |
| `horizon wrap claude` | native | host-bridged | partial |
| `horizon wrap copilot` | native | not implemented in Docker-native wrapper | none |
| `horizon wrap codex` | native | host-bridged | partial |
| `horizon wrap aider` | native | host-bridged | partial |
| `horizon wrap cursor` | native | host-bridged | partial |
| `horizon wrap openclaw` | native | host-bridged | partial |
| `horizon unwrap openclaw` | native | host-bridged | partial |

For the Docker-native execution model itself, see [Docker-Native Install](docker-install.md). For persistent service/task/docker lifecycle management, see [Persistent Installs](persistent-installs.md).

## Hidden and compatibility-only command paths

These exist in code but are intentionally excluded from normal user docs:

- `horizon memory-eval`
- `horizon memory-eval-v2`
- hidden internal `--prepare-only` flags on `wrap` subcommands

If you are documenting operational behavior or debugging internal wrapper flows, refer to the implementation in `horizon/cli/wrap.py`.
