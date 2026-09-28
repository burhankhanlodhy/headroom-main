# Getting Started with Horizon

This guide will help you get up and running with Horizon in under 5 minutes.

## Installation

**CLI on macOS Apple Silicon/Linux with uv:**

```bash
uv tool install --python 3.13 "horizon-ai[all]"
horizon --version
```

Use `uv tool update-shell` if the install succeeds but `horizon` is not on
`PATH`.

**Python project / virtualenv:**

```bash
# Core package (minimal dependencies)
pip install horizon-ai

# With proxy server
pip install "horizon-ai[proxy]"

# With semantic relevance (for smarter compression)
pip install "horizon-ai[relevance]"

# Everything
pip install "horizon-ai[all]"
```

**TypeScript / Node.js:**

```bash
npm install horizon-ai
```

**Docker-native:**

```bash
curl -fsSL https://raw.githubusercontent.com/your-org/horizon/main/scripts/install.sh | bash
```

PowerShell:

```powershell
irm https://raw.githubusercontent.com/your-org/horizon/main/scripts/install.ps1 | iex
```

See [Docker-native install](docker-install.md) for wrapper behavior, compose usage, and host-integrated `wrap` flows.

If you want Horizon to stay up in the background and automatically serve supported tools, use [Persistent Installs](persistent-installs.md):

```bash
horizon install apply --preset persistent-service --providers auto
```

## Quick Start: Proxy Mode (Recommended)

The easiest way to use Horizon is as a proxy server:

```bash
# Start the proxy
horizon proxy --port 8787
```

Then point your LLM client at it:

```bash
# Claude Code
ANTHROPIC_BASE_URL=http://localhost:8787 claude

# GitHub Copilot CLI (default Anthropic-style proxy route)
horizon wrap copilot -- --model claude-sonnet-4-20250514

# OpenAI-compatible clients
OPENAI_BASE_URL=http://localhost:8787/v1 your-app
```

That's it! All your requests now go through Horizon and get optimized automatically.

## Quick Start: Python SDK

If you want programmatic control:

```python
from horizon import HorizonClient
from openai import OpenAI

# Create a wrapped client
client = HorizonClient(
    original_client=OpenAI(),
    default_mode="optimize",
)

# Use exactly like the original
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)
```

## Modes

### Audit Mode

Observe without modifying:

```python
client = HorizonClient(
    original_client=OpenAI(),
    default_mode="audit",
)
# Logs metrics but doesn't change requests
```

### Optimize Mode

Apply transforms to reduce tokens:

```python
client = HorizonClient(
    original_client=OpenAI(),
    default_mode="optimize",
)
# Compresses tool outputs, aligns cache prefixes, etc.
```

### Simulate Mode

Preview what optimizations would do:

```python
plan = client.chat.completions.simulate(
    model="gpt-4o",
    messages=[...],
)
print(f"Would save {plan.tokens_saved} tokens")
print(f"Transforms: {plan.transforms}")
```

## Next Steps

- [Proxy Server Documentation](proxy.md) - Configure the proxy
- [Transforms Reference](transforms.md) - Understand each transform
- [API Reference](api.md) - Full API documentation
