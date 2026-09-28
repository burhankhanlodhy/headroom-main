# Configuration

Horizon can be configured via the SDK, proxy command line, or per-request overrides.

## Runtime Rollout Channels

Rollout channels control behaviors in an already-installed artifact. They do
not install or select a Horizon release/version.

| Variable | Default | Purpose |
|----------|---------|---------|
| `HORIZON_ROLLOUT_CHANNEL` | `stable` | Selects `stable`, `beta`, `canary`, or `dev`. |
| `HORIZON_FEATURES` | unset | Comma-separated feature names to request explicitly. |
| `HORIZON_DISABLE_FEATURES` | unset | Comma-separated feature names to force off. Disable wins over every enable path. |
| `HORIZON_UNSAFE_ALLOW_UNSTABLE_FEATURES` | unset | Break-glass override for emergency mitigation only. |

Example:

```bash
export HORIZON_ROLLOUT_CHANNEL=canary
export HORIZON_FEATURES=tool_result_interceptors
horizon proxy --intercept-tool-results
```

## SDK Configuration

```python
from horizon import HorizonClient, OpenAIProvider
from openai import OpenAI

client = HorizonClient(
    original_client=OpenAI(),
    provider=OpenAIProvider(),
    # Mode: "audit" (observe only) or "optimize" (apply transforms)
    default_mode="optimize",
    # Enable provider-specific cache optimization
    enable_cache_optimizer=True,
    # Enable query-level semantic caching
    enable_semantic_cache=False,
    # Override default context limits per model
    model_context_limits={
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
    },
    # Database location (defaults to temp directory)
    # store_url="sqlite:////absolute/path/to/horizon.db",
)
```

## Proxy Configuration

### Command Line Options

```bash
horizon proxy \
  --port 8787 \              # Port to listen on
  --host 127.0.0.1 \         # Host to bind to
  --budget 10.00 \           # Daily budget limit in USD
  --log-file horizon.jsonl  # Log file path
```

### Feature Flags

```bash
# Disable optimization (passthrough mode)
horizon proxy --no-optimize

# Disable semantic caching
horizon proxy --no-cache

# Disable CCR entirely (no retrieval markers and no injected retrieve tool)
horizon proxy --no-ccr

# Disable proactive CCR expansion
horizon proxy --no-ccr-proactive-expansion

# (The earlier --llmlingua flag was retired in 0.9.x and replaced by
# Kompress (ModernBERT). See `wiki/transforms.md` for the current
# opt-in path via the `[ml]` extra.)
```

### All Options

```bash
horizon proxy --help
```

### Kompress backend selection

Kompress (the model-based compressor) can run on two engines:

- **ONNX Runtime** — lightweight, CPU-first. Installed with
  `pip install horizon-ai[proxy]`. Optionally uses the CoreML execution
  provider on macOS.
- **PyTorch** — heavier, supports CUDA and Apple-Silicon MPS
  acceleration. Installed with `pip install horizon-ai[ml]`. With
  `device=auto` it selects `cuda`, then `mps`, then `cpu`.

Select the backend via the `HORIZON_KOMPRESS_BACKEND` environment
variable:

| Value               | Behavior                                                               |
|---------------------|------------------------------------------------------------------------|
| `auto`              | Default. ONNX CPU first (stable, lightweight), PyTorch as fallback.    |
| `onnx` / `onnx_cpu` | Force ONNX Runtime on CPU.                                             |
| `onnx_coreml`       | Force ONNX Runtime with the CoreML provider (CPU fallback).            |
| `pytorch`           | Force PyTorch with automatic device selection (CUDA → MPS → CPU).      |
| `pytorch_mps`       | Force PyTorch on Apple-Silicon MPS; falls back to ONNX CPU on failure. |

Values are case-insensitive and hyphens are accepted (`onnx-cpu` ==
`onnx_cpu`). Shorthand aliases: `cpu` → `onnx_cpu`, `coreml` →
`onnx_coreml`, `mps` / `torch_mps` → `pytorch_mps`, `torch` →
`pytorch`. Unrecognized values log a warning and fall back to `auto`.

Example — opt in to MPS on an Apple-Silicon machine:

```bash
export HORIZON_KOMPRESS_BACKEND=mps
horizon proxy ...
```

The default deliberately stays on ONNX CPU so existing installs keep
their compression quality and performance characteristics; accelerator
backends are opt-in.

## Per-Request Overrides

Override configuration for specific requests:

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    # Override mode for this request
    horizon_mode="audit",
    # Reserve more tokens for output
    horizon_output_buffer_tokens=8000,
    # Keep last N turns (don't compress)
    horizon_keep_turns=5,
    # Skip compression for specific tools
    horizon_tool_profiles={"important_tool": {"skip_compression": True}},
)
```

## Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `audit` | Observes and logs, no modifications | Production monitoring, baseline measurement |
| `optimize` | Applies safe, deterministic transforms | Production optimization |
| `simulate` | Returns plan without API call | Testing, cost estimation |

### Simulate Mode

Preview what would happen without making an API call:

```python
plan = client.chat.completions.simulate(
    model="gpt-4o",
    messages=large_conversation,
)

print(f"Would save {plan.tokens_saved} tokens")
print(f"Transforms: {plan.transforms}")
print(f"Estimated savings: {plan.estimated_savings}")
```

## SmartCrusher Configuration

Fine-tune JSON compression behavior:

```python
from horizon.transforms import SmartCrusherConfig

config = SmartCrusherConfig(
    # Maximum items to keep after compression
    max_items_after_crush=15,
    # Minimum tokens before applying compression
    min_tokens_to_crush=200,
    # Guarantee rows matching these patterns survive compression verbatim
    # (requires audit_safe=True; matched against each row's canonical JSON)
    audit_safe=True,
    protected_patterns=["error", "warning", "failure"],
)
# Error items and statistical anomalies (>2 std from mean) are always kept
# automatically. Relevance-scoring tier ("bm25"/"embedding"/"hybrid") is a
# separate `relevance_config` argument to SmartCrusher(), not a field here.
```

## Cache Aligner Configuration

Control prefix stabilization:

```python
from horizon import CacheAlignerConfig

config = CacheAlignerConfig(
    # Enable/disable cache alignment (disabled by default: prefix-stability
    # gains are marginal in practice -- see horizon/config.py:61)
    enabled=True,
    # Legacy pattern list (only used when use_dynamic_detector=False;
    # the field is `date_patterns`, not `dynamic_patterns`). Default mode
    # (use_dynamic_detector=True) auto-detects dates, UUIDs, tokens, etc.
    # via detection_tiers instead -- see horizon/config.py:68-79.
    use_dynamic_detector=False,
    date_patterns=[
        r"Today is \w+ \d+, \d{4}",
        r"Current time: .*",
    ],
)
```

## Context Management

Context management is handled automatically inside the pipeline
(live-zone-only compression) — there is nothing to configure. Horizon
**never** drops messages from the conversation history and does not do
position-based or score-based context management. It compresses only the
newest content blocks (the latest user message and the latest tool result /
tool output), type-aware and reversible via CCR. The cache hot zone — system
prompt, tools, and older turns — is never mutated, which preserves provider
prompt caching.

> The earlier `RollingWindowConfig`, `IntelligentContextConfig`, and
> `ScoringWeights` configuration classes (and the position-/score-based
> context managers they configured) have been removed and are no longer part
> of Horizon.

## Environment Variables

Some settings can be configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `HORIZON_MODEL_LIMITS` | Custom model config (JSON string or file path) | - |
| `HORIZON_CONFIG_DIR` | Canonical config (read-mostly) root. Derives `models.json` and per-plugin config paths when set. | `~/.horizon/config` |
| `HORIZON_WORKSPACE_DIR` | Canonical workspace (read-write state) root. Derives savings ledger, memory DB, logs, TOIN, subscription state, and more when set. | `~/.horizon` |
| `HORIZON_SAVINGS_PATH` | Full path to the proxy savings JSON ledger. Always wins when set. | derived from `${HORIZON_WORKSPACE_DIR}` |
| `HORIZON_TOIN_PATH` | Full path to the TOIN telemetry JSON file. Always wins when set. | derived from `${HORIZON_WORKSPACE_DIR}` |
| `HORIZON_SUBSCRIPTION_STATE_PATH` | Full path to the subscription tracker state. Always wins when set. | derived from `${HORIZON_WORKSPACE_DIR}` |
| `HORIZON_EMBEDDER_RUNTIME` | Set to `pytorch_mps` to run the memory embedder via the torch sentence-transformers backend on the Apple GPU (MPS). Only engages when Apple MPS is actually available; otherwise it logs a warning and uses the existing default embedder selection path. `pytorch_mps` is the only accepted value. Requires the `[pytorch-mps]` extra. See [Memory](memory.md#embedding-runtime--gpu-offload-apple-silicon). | default embedder selection |
| `HORIZON_BETA_HEADER_STICKY` | Controls per-session `anthropic-beta` / `OpenAI-Beta` re-echo. `enabled` (default): the proxy unions beta tokens across turns within a session — if the client sends a token in turn N and omits it in turn N+1, the proxy re-injects it to preserve prefix-cache stability. `disabled`: the client's value is forwarded verbatim with no accumulation. Any other value raises at request time. See [Session Beta Header Tracking](#session-beta-header-tracking). | `enabled` |
| `HORIZON_BETA_TRACKER_MAX_SESSIONS` | LRU capacity of the in-memory session beta tracker. Once full, the oldest session entry is evicted. | `1000` |
| `HORIZON_1M_MODEL` | Model id (the client-owned model setting) that `horizon wrap claude` upgrades with the `[1m]` suffix to request the 1M context tier. | `claude-opus-5` |

## Settings GUI

A web-based settings interface is available at `http://127.0.0.1:<port>/dashboard/settings` for configuring every safe `HORIZON_*` proxy knob without hand-exporting environment variables, plus an **Endpoints** group for custom Anthropic/OpenAI upstream base URLs (`ANTHROPIC_TARGET_API_URL` / `OPENAI_TARGET_API_URL`) and extra headers merged into (and overriding) forwarded requests -- e.g. for a corporate gateway or Azure Foundry deployment that needs a different endpoint plus one extra auth header. Fields are split into a **Settings** tab (commonly-tuned: compression ratio, budget, rate limits, verbosity) and an **Advanced** tab (everything else, including Endpoints). Third-party credentials such as `OPENAI_API_KEY`/`AWS_*` are never exposed here; the two extra-headers fields are the only secret-typed fields in the panel and render masked once set, with a "Clear stored value" action to remove them -- resaving the page without touching a masked field never overwrites the real stored value.

- **Persistence**: Settings are saved to `~/.horizon/settings.json` (merged with existing values, not replaced) and loaded into the process environment at startup.
- **Precedence** (highest to lowest):
  - Explicit shell export (`export HORIZON_FOO=bar`)
  - Settings from `~/.horizon/settings.json`
  - Code default
- **Activation**: Click "Save" to persist without restarting, or "Apply & Restart" to persist and take effect immediately. Apply & Restart behavior depends on how the proxy is running:
  - **Service** (supervised launchd/systemd install): self-restarts in one click.
  - **Docker**: cannot self-restart from inside the container; the GUI surfaces the host-side `horizon install restart --profile <p>` command to run instead.
  - **Task** (Windows Task Scheduler / cron-managed install): `horizon install` does not support lifecycle operations for task deployments; the GUI shows an instruction to restart via the OS task scheduler or by stopping the process so it relaunches on its next trigger.
  - **Foreground** (plain `horizon proxy`): shows a manual-restart instruction.
- **Provenance / locking**: a field currently shadowed by an explicit environment variable export is rendered read-only with a tooltip, since editing it here would have no effect until the env var is unset. Manifest-baked settings (`HORIZON_PORT`, `HORIZON_HOST`) are similarly locked on supervised (Docker/Service) installs — managed by the install manifest, not the settings interface.
- **CSRF protection**: `/settings` and `/settings/apply` reject requests whose `Origin` header (when present) doesn't resolve to a loopback host, in addition to the existing loopback-only + Host-header DNS-rebinding guard shared by all admin endpoints.

## Session Beta Header Tracking

When running as a proxy, Horizon maintains a per-session union of `anthropic-beta` (and `OpenAI-Beta`) tokens via `SessionBetaTracker`. The session key is derived from the `x-horizon-session-id` header if present, otherwise from `md5(model + system_prompt[:500])[:16]` — stable across turns of the same conversation.

**Why:** clients such as Claude Code and Codex CLI may drop a beta token between consecutive turns. Because `anthropic-beta` is part of the request bytes that determine the upstream prefix-cache key, a dropped token would bust the cache mid-conversation. The tracker re-injects any token seen earlier in the session so the cache key stays stable.

**Trade-off:** once the proxy has seen a beta token in a session it will continue re-sending it for the rest of that session, even if the client stops including it. Stopping the token on the client side alone is not sufficient — the proxy re-injects it. Set `HORIZON_BETA_HEADER_STICKY=disabled` to pass the client's `anthropic-beta` value verbatim and bypass this accumulation.

```bash
# Disable sticky beta re-echo
export HORIZON_BETA_HEADER_STICKY=disabled
horizon proxy ...
```

Note: disabling sticky mode may reduce prefix-cache hit rates for clients that legitimately drop-and-re-add beta tokens across turns.

## Filesystem Contract

Horizon resolves every on-disk resource through a two-root model:

- `HORIZON_CONFIG_DIR` (default `~/.horizon/config`) — read-mostly
  configuration
- `HORIZON_WORKSPACE_DIR` (default `~/.horizon`) — read-write state

Precedence for each resource is: explicit argument > per-resource env
var > derived from canonical root > default. Every legacy env var
continues to work unchanged.

See **[Filesystem Contract](filesystem-contract.md)** for the full
bucket table, plugin-author guidance, and the Docker naming overlap
note (`HORIZON_WORKSPACE` is *not* the same as `HORIZON_WORKSPACE_DIR`).

---

## Custom Model Configuration

Configure context limits and pricing for new or custom models. Useful when:
- A new model is released before Horizon is updated
- You're using fine-tuned or custom models
- You want to override built-in limits

### Configuration Methods

Settings are resolved in this order (later overrides earlier):
1. Built-in defaults
2. `${HORIZON_CONFIG_DIR}/models.json` (defaults to
   `~/.horizon/config/models.json`); falls back to the legacy location
   `~/.horizon/models.json` when the canonical file is absent
3. `HORIZON_MODEL_LIMITS` environment variable
4. SDK constructor arguments

### Config File Format

Create `~/.horizon/models.json`:

```json
{
  "anthropic": {
    "context_limits": {
      "claude-4-opus-20250301": 200000,
      "claude-custom-finetune": 128000
    },
    "pricing": {
      "claude-4-opus-20250301": {
        "input": 15.00,
        "output": 75.00,
        "cached_input": 1.50
      }
    }
  },
  "openai": {
    "context_limits": {
      "gpt-5": 256000,
      "ft:gpt-4o:my-org": 128000
    },
    "pricing": {
      "gpt-5": [5.00, 15.00]
    }
  }
}
```

### Environment Variable

Set `HORIZON_MODEL_LIMITS` as a JSON string or file path:

```bash
# JSON string
export HORIZON_MODEL_LIMITS='{"anthropic":{"context_limits":{"claude-new":200000}}}'

# File path
export HORIZON_MODEL_LIMITS=/path/to/models.json
```

### Pattern-Based Inference

Unknown models are automatically inferred from naming patterns:

| Pattern | Inferred Settings |
|---------|-------------------|
| `*opus*` | 200K context, Opus-tier pricing |
| `*sonnet*` | 200K context, Sonnet-tier pricing |
| `*haiku*` | 200K context, Haiku-tier pricing |
| `gpt-4o*` | 128K context, GPT-4o pricing |
| `o1*`, `o3*` | 200K context, reasoning model pricing |

This means new models like `claude-4-sonnet-20251201` will work automatically with Sonnet-tier defaults.

### SDK Override

Override in code for specific models:

```python
from horizon import HorizonClient, AnthropicProvider

client = HorizonClient(
    original_client=Anthropic(),
    provider=AnthropicProvider(
        context_limits={
            "claude-new-model": 300000,
        }
    ),
)
```

## Provider-Specific Settings

### OpenAI

```python
from horizon import OpenAIProvider

provider = OpenAIProvider(
    # Enable automatic prefix caching
    enable_prefix_caching=True,
)
```

### Anthropic

```python
from horizon import AnthropicProvider

provider = AnthropicProvider(
    # Enable cache_control blocks
    enable_cache_control=True,
)
```

### Google

```python
from horizon import GoogleProvider

provider = GoogleProvider(
    # Enable context caching
    enable_context_caching=True,
)
```

## Configuration Precedence

Settings are applied in this order (later overrides earlier):

1. Default values
2. Environment variables
3. SDK constructor arguments
4. Per-request overrides

## Validation

Validate your configuration:

```python
result = client.validate_setup()

if not result["valid"]:
    print("Configuration issues:")
    for issue in result["issues"]:
        print(f"  - {issue}")
```

---

## TypeScript SDK Configuration

The TypeScript SDK is configured via environment variables or constructor options.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HORIZON_BASE_URL` | Base URL of the Horizon proxy | `http://localhost:8787` |
| `HORIZON_API_KEY` | Optional API key for authenticated Horizon endpoints | - |

### Usage

```bash
export HORIZON_BASE_URL=http://localhost:8787
export HORIZON_API_KEY=your-api-key
```

```typescript
import { HorizonClient } from 'horizon-ai';

// Reads from HORIZON_BASE_URL and HORIZON_API_KEY automatically
const client = new HorizonClient();

// Or configure explicitly
const client = new HorizonClient({
  baseUrl: 'http://localhost:8787',
  apiKey: 'your-api-key',
});
```

See the [TypeScript SDK Guide](typescript-sdk.md) for full configuration options.
