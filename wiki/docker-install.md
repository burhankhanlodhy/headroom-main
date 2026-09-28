# Docker-Native Install

Run Horizon without installing Python or Node.js on the host. The install scripts add a native `horizon` wrapper that keeps **Horizon itself** in Docker while orchestrating the rest of your workflow on the host OS.

## One-line install

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/your-org/horizon/main/scripts/install.sh | bash
```

### macOS (bash 4.3+)

```bash
curl -fsSL https://raw.githubusercontent.com/your-org/horizon/main/scripts/install.sh | "$(brew --prefix bash)/bin/bash"
```

Stock `/bin/bash` on macOS is 3.2, so install a newer bash first (for example via Homebrew) and run the installer with that shell. The installed wrapper pins that same bash interpreter so later invocations stay on the supported runtime.

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/your-org/horizon/main/scripts/install.ps1 | iex
```

## What the installer does

1. Verifies Docker is installed and available.
2. Pulls `ghcr.io/your-org/horizon:latest` by default, or reuses / pulls `HORIZON_DOCKER_IMAGE` when you set a custom image override.
3. Installs a `horizon` wrapper into `~/.local/bin` or `~/bin`.
4. Updates shell startup files so the wrapper directory is on `PATH`.

The wrapper keeps Horizon inside Docker and mounts host state back into the container so native behavior stays consistent:

- project workspace -> `/workspace`
- `~/.horizon`
- `~/.claude`
- `~/.codex`
- `~/.gemini`

Port `8787` stays the default, so `http://localhost:8787` works the same way as a native install.

Published releases also push versioned GHCR tags such as `ghcr.io/your-org/horizon:0.35.0`, and those images are built with the same synced package version used for the matching PyPI and npm release.

## How the wrapper behaves

### Native Horizon commands

These run directly inside the container:

```bash
horizon proxy
horizon learn
horizon mcp install
horizon memory list
```

For `proxy`, the maintained wrapper always publishes the selected host port on
loopback. It passes `--host 0.0.0.0` inside the container so that the loopback
publication can reach the container, and it has no public-publication override.
For local-only use, no token is required:

```bash
docker run --rm -it \
  -p 127.0.0.1:8787:8787 \
  -v "$PWD:/workspace" \
  -w /workspace \
  ghcr.io/your-org/horizon:latest \
  --host 0.0.0.0 --port 8787
```

For deliberate public access, publish on an explicit public address and set
`HORIZON_PROXY_TOKEN`:

```bash
docker run --rm -p 0.0.0.0:8787:8787 \
  -e HORIZON_PROXY_TOKEN='replace-with-a-secret' \
  ghcr.io/your-org/horizon:latest --host 0.0.0.0 --port 8787
```

### `wrap` commands

`wrap` is host-oriented in Docker-native mode:

- the wrapper starts the Horizon proxy in Docker
- container-side prep writes Horizon config and memory into mounted host files
- the target CLI itself is launched on the host by the wrapper

Supported host wrap flows:

- `horizon wrap claude`
- `horizon wrap codex`
- `horizon wrap aider`
- `horizon wrap cursor`
- `horizon wrap openclaw`
- `horizon unwrap openclaw`

OpenClaw remains host-native in Docker-native mode:

- the host must already have the `openclaw` CLI installed
- `horizon wrap openclaw` installs/configures the Horizon plugin through the host `openclaw` CLI
- plugin auto-start still launches the installed host `horizon` wrapper from `PATH`, which then runs Horizon in Docker
- local plugin source mode (`--plugin-path`) is also supported, but it may require host `npm` when build steps are needed

## Persistent Docker lifecycle from the native wrapper

The Docker-native `horizon` wrapper now exposes the persistent Docker lifecycle directly:

```bash
horizon install apply --profile default --preset persistent-docker
horizon install status
horizon install restart
horizon install remove
```

In Docker-native mode this surface is intentionally scoped to **persistent-docker**:

- supported: `apply`, `status`, `start`, `stop`, `restart`, `remove`
- supported flags: `--profile`, `--port`, `--backend`, `--anyllm-provider`, `--region`, `--mode`, `--memory`, `--no-telemetry`, `--image`
- not supported: `persistent-service`, `persistent-task`, or provider/user/system mutation flags such as `--scope`, `--providers`, and `--target`

Those broader lifecycle and config-mutation flows still belong to the Python-native `horizon install ...` command.

Persistent Docker deployments launched by the wrapper also tag the proxy process with deployment metadata, so `/health` reports the active `profile`, `preset`, `runtime`, `supervisor`, and `scope` the same way the Python install subsystem does.

## Docker Compose support

Use `docker/docker-compose.native.yml` when you want an explicit compose-managed proxy or CLI shell, or when you prefer compose over the native wrapper's `horizon install ...` surface.

### Persistent Docker runtime

The `proxy` service now uses `restart: unless-stopped`, so compose can act as the always-on Docker runtime for Horizon:

```bash
export HORIZON_HOST_HOME="$HOME"
export HORIZON_WORKSPACE="$PWD"
docker compose -f docker/docker-compose.native.yml up -d proxy
```

```powershell
$env:HORIZON_HOST_HOME = $HOME
$env:HORIZON_WORKSPACE = (Get-Location).Path
docker compose -f docker/docker-compose.native.yml up -d proxy
```

This remains a supported persistent-Docker path when you want the proxy managed explicitly through Compose instead of the installed wrapper.

#### `HORIZON_WORKSPACE` vs `HORIZON_WORKSPACE_DIR`

These are two different variables — both are set by the compose file,
and both are retained for backward compatibility:

- **`HORIZON_WORKSPACE`** (host-side) is the directory the compose file
  bind-mounts into the container as `/workspace`. It behaves like CWD
  in a native (non-Docker) run.
- **`HORIZON_WORKSPACE_DIR`** (inside-the-container) is the canonical
  Horizon state root — part of the [filesystem contract][fs]
  introduced in issue #175. The compose file sets it to
  `/tmp/horizon-home/.horizon` so the proxy resolves savings, logs,
  TOIN, and memory under the bind-mounted `${HOME}/.horizon`.

You do not need to set `HORIZON_WORKSPACE_DIR` manually when using the
shipped compose file — it is already in the `environment:` block.

[fs]: filesystem-contract.md

### macOS / Linux

```bash
export HORIZON_HOST_HOME="$HOME"
export HORIZON_WORKSPACE="$PWD"
docker compose -f docker/docker-compose.native.yml up proxy
```

### Windows PowerShell

```powershell
$env:HORIZON_HOST_HOME = $HOME
$env:HORIZON_WORKSPACE = (Get-Location).Path
docker compose -f docker/docker-compose.native.yml up proxy
```

You can also run one-off CLI commands through compose:

```bash
docker compose -f docker/docker-compose.native.yml run --rm cli learn
docker compose -f docker/docker-compose.native.yml run --rm cli mcp install
```

## Environment passthrough

The wrapper forwards Horizon and provider environment variables into the container, including common prefixes such as:

- `HORIZON_`
- `ANTHROPIC_`
- `OPENAI_`
- `GEMINI_`
- `AWS_`
- `GOOGLE_` / `GOOGLE_CLOUD_`
- `AZURE_`
- `OTEL_`

That keeps provider auth and runtime config working without maintaining a separate env file for the container.

## Notes

- Docker is the only required Horizon runtime dependency on the host.
- Wrapped tools like Claude Code, Codex CLI, Aider, and Cursor still run on the host when you use `horizon wrap ...`.
- The install scripts are idempotent: rerunning them refreshes the wrapper and image without duplicating shell profile blocks.
- For persistent service and task installs, use the Python-native `horizon install ...` workflow described in [Persistent Installs](persistent-installs.md).
- For Docker-native `horizon install ...`, the wrapper persists its profile manifest under `~/.horizon/deploy/<profile>/`.
