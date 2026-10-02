# ContextShrink desktop launcher (Windows)

A Tauri app users download from the dashboard to run their own coding tools
through the hosted ContextShrink proxy. Supported tools: Claude Code and OpenCode.

## How it works

1. The user signs in with their ContextShrink email and password.
2. The app creates a proxy key for this computer (`POST /api/keys`, named
   `Desktop: <COMPUTERNAME>`) and hands it to the bundled Horizon client
   (`horizon vault set --stdin`), which keeps it in Windows Credential Manager.
   No key is embedded in the installer. Signing out revokes the device key; a
   key revoked from the dashboard is replaced automatically at next start.
3. The app runs the Horizon forwarder in the background on `127.0.0.1:18788`.
   It adds `X-Horizon-Proxy-Token` to every request and relays it to
   `https://app.contextshrink.com/proxy`.
4. **Launch** opens a console in the chosen project folder running the tool's
   `horizon wrap` command against the forwarder, then `horizon unwrap` when the
   tool exits, restoring the tool's own config:
   - Claude Code: `wrap claude --no-proxy --no-mcp --code-memory none` (base URL
     in the project's `.claude/settings.local.json` for the session; unwrap uses
     `--keep-mcp` so the user's own MCP registrations are never removed).
   - OpenCode: `wrap opencode --no-proxy --no-mcp --no-serena`, plus the bundled
     transport plugin, which reroutes every provider. The forwarder sends model
     calls to the proxy and everything else (sign-in, catalogues) direct.

The installer ships only ContextShrink's own pieces: the app and a frozen
Horizon client (Python runtime included). The tools it launches, such as
OpenCode, are never bundled; the app detects them on `PATH` and links to their
install page when missing.

## Layout

| Path | What |
|---|---|
| `client/horizon_client.py`, `client/build-client.ps1` | Frozen Horizon CLI (PyInstaller, one-folder) |
| `app/src-tauri/src/api.rs` | Control-plane API calls (login, device key, account) |
| `app/src-tauri/src/secrets.rs` | Session token and device-key ID in Credential Manager |
| `app/src-tauri/src/client.rs` | Bundled client: vault, forwarder, tool registry and launch |
| `app/src/App.tsx` | Sign-in and home screens |

Adding a tool: add an entry to `TOOLS` in `client.rs` with its `horizon wrap`
and `unwrap` arguments.

## Build

Requires the repo `.venv` (with PyInstaller), Rust, the MSVC build tools and
Node.js. From PowerShell (not Git Bash):

```powershell
.\desktop\build-installer.ps1
```

Development run (uses the frozen client from `client\dist`):

```powershell
.\desktop\client\build-client.ps1
cd desktop\app; npm install; npx tauri dev
```

Set `CONTEXTSHRINK_APP_URL` to point the app at a different dashboard origin.
