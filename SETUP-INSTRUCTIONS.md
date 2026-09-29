# Horizon on Raspberry Pi + PC — Complete Setup Guide

This is the runbook for reproducing the current working deployment from zero:
**Horizon proxy runs in Docker on a Raspberry Pi; your PC's Claude Code reaches
it through an SSH tunnel.** Nothing is exposed to the network — the tunnel is
the security boundary.

```
┌─────────────── PC (Windows) ───────────────┐         ┌───── Raspberry Pi ──────────────────┐
│                                            │         │                                     │
│  claude ──> http://127.0.0.1:18787         │  SSH    │  horizon proxy (Docker, host net)   │
│  connect-horizon-vps.ps1 opens the tunnel  │ ──────> │  127.0.0.1:8787 (loopback only)     │
│  http://127.0.0.1:18787/dashboard          │         │  dashboard: http://127.0.0.1:8787   │
└────────────────────────────────────────────┘         └─────────────────────────────────────┘
```

- **Pi**: container binds `127.0.0.1:8787` with `network_mode: host`. Host
  networking is **required**: tunneled clients must present as loopback, or the
  proxy's auth gate treats them as untrusted and 401s every request.
- **PC**: `connect-horizon-vps.ps1` opens the tunnel, patches Claude's
  `settings.json` for the session, and launches Claude Code. Dashboard:
  `http://127.0.0.1:18787/dashboard`.

> Repo was renamed on GitHub from `headroom-main` to `horizon`. Old local clones
> should update their remote (Part B, step 3). The local **folder name does not
> matter** — both scripts locate themselves via `$PSScriptRoot`.

---

## Part A — New Raspberry Pi (one-time, ~30-60 min, mostly the build)

### A1. Base system

1. Flash **Raspberry Pi OS 64-bit** and enable SSH (Raspberry Pi Imager can
   preset user/password and SSH before first boot).
2. Note the address you can reach it at — `user@<pi-ip>` (or `user@<hostname>.local`).
   A static/reserved DHCP address is recommended; the connect script needs a
   stable `-VpsHost`.
3. From the PC, verify key-based SSH works (Part B step 4 sets the key up;
   do that step first if the PC is also new).

### A2. Install Docker

```bash
ssh user@<pi-ip>
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER    # log out/in once afterwards
docker compose version           # must print a version
```

### A3. Clone the repo

```bash
git clone https://github.com/burhankhanlodhy/horizon.git ~/horizon
cd ~/horizon
```

### A4. Configure the proxy token

The container refuses to start without a token configured (even though tunnel
clients never send one — loopback trust covers them):

```bash
cp .env.example .env
# generate a value and put it under HORIZON_PROXY_TOKEN= in .env
openssl rand -hex 32
nano .env
```

### A5. Build and start

```bash
docker compose build horizon-proxy   # slow: compiles the Rust extension on-device
docker compose up -d
```

`docker compose build` is the long step (15-45 min on a Pi 5). Watch for it to
finish without errors; the aarch64 build fixes are already in the repo.

### A6. Verify

```bash
curl -s http://127.0.0.1:8787/readyz     # -> {"ready":true,...}
docker compose ps                        # -> Up (healthy)
```

The compose file sets `restart: unless-stopped`, so the proxy comes back
automatically after Pi reboots.

If you deploy from a machine that already has a working `~/horizon/.env` and
want the same durable stats, copy that `.env` (and optionally the
`horizon_workspace` volume) instead of generating a fresh token.

---

## Part B — New PC (one-time)

### B1. Prerequisites

- **Git** — `winget install Git.Git`
- **Python 3.10+** — `winget install Python.Python.3.12`
- **Claude Code** — installed and working (`claude --version`)
- **Windows OpenSSH client** — built into Windows 10/11 (`ssh -V`)

### B2. Clone the repo

```powershell
cd $env:USERPROFILE\Desktop          # anywhere works
git clone https://github.com/burhankhanlodhy/horizon.git horizon
cd horizon
```

(The local folder name is irrelevant to the scripts.)

### B3. If this clone predates the GitHub rename

```powershell
git remote set-url origin https://github.com/burhankhanlodhy/horizon.git
git pull
```

### B4. SSH key for the Pi

The connect script opens the tunnel in a hidden window, so **password prompts
cannot appear — key auth is mandatory.**

```powershell
ssh-keygen -t ed25519                       # accept defaults (skip if you have one)
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh user@<pi-ip> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
ssh user@<pi-ip> exit                       # must connect without a password
```

### B5. Create the repo venv

The disconnect script's cleanup step (`horizon unwrap ...`) runs Horizon's CLI
from the repo venv at `.venv\Scripts\python.exe`.

```powershell
.\scripts\bootstrap-windows-dev.ps1         # creates .venv and installs dependencies
```

If you only want the minimal setup: `python -m venv .venv` then
`.\.venv\Scripts\pip install -e .` (needs the Rust toolchain for the native
extension; the bootstrap script handles that).

---

## Part C — Daily use

**Start (each session):**

```powershell
cd <path\to>\horizon
.\connect-horizon-vps.ps1 -VpsHost user@<pi-ip> -LocalPort 18787
```

What it does: reuses the tunnel if one is already up, otherwise opens
`127.0.0.1:18787 -> Pi:8787`, verifies the proxy answers, patches
`~\.claude\settings.json`'s `env` block (`ANTHROPIC_BASE_URL` +
`ENABLE_TOOL_SEARCH`) for the session, and launches Claude Code as a direct
child of that console.

**End (each session):** exit Claude normally (`/exit` or Ctrl+C twice — do not
close the window with the X; the script's cleanup needs to run) and then:

```powershell
.\disconnect-horizon-vps.ps1
```

That stops the tunnel and restores your original Claude settings. If you forget,
nothing breaks — but Claude would keep pointing at the dead tunnel until the
settings are restored.

**Dashboard:** `http://127.0.0.1:18787/dashboard` while the tunnel is up.

**Tunnel-only mode** (no Claude, e.g. just to peek at the dashboard):
`.\connect-horizon-vps.ps1 -VpsHost user@<pi-ip> -LocalPort 18787 -NoLaunch`

---

## Updating Horizon

```powershell
# PC side
git pull

# Pi side
ssh user@<pi-ip>
cd ~/horizon && git pull
docker compose build horizon-proxy && docker compose up -d
```

---

## Troubleshooting — the lessons already paid for

| Symptom | Cause & fix |
| --- | --- |
| `Local port 18787 is already in use` | A tunnel is still running. Run `.\disconnect-horizon-vps.ps1`, or pick another port with `-LocalPort`. |
| Claude fails with connection refused / API errors | The tunnel is down but Claude is still patched to `127.0.0.1:18787`. Re-run the connect script (or disconnect to restore settings). |
| Dashboard loads but every counter stays 0 | Claude was launched **outside** the connect script, so it goes direct to Anthropic. The settings patch is per-session — always launch via the script. |
| Dashboard "Failed" climbing while prompts work fine | Real upstream `429 rate_limit` errors on Claude Code's tiny background calls. Honest accounting; prompts are unaffected. |
| Every tunneled request 401s | The container lost `network_mode: host` (bridge DNAT makes peers non-loopback and the auth gate rejects them). Restore host networking and `docker compose up -d`. |
| Proxy down after Pi reboot | Older compose without `restart: unless-stopped`. `git pull`, then `docker compose up -d` once; afterwards it self-starts. |
| Metrics all zero despite real traffic, image built before 2026-09-29 | The beacon-shim fix (`82b08e8`) is missing from the image — rebuild from a current `main`. |
| SSH asks for a password and the tunnel dies silently | Key auth not set up. The hidden-window tunnel cannot answer password prompts — complete Part B step 4. |
| Want to verify end-to-end quickly | `claude --debug -p "Reply with exactly: OK"` prints the resolved endpoint URL — it must show `127.0.0.1:18787`. Then the dashboard should tick. |

---

## Quick reference

```powershell
# ---- PC: start ----
cd <path\to>\horizon
.\connect-horizon-vps.ps1 -VpsHost user@<pi-ip> -LocalPort 18787

# ---- PC: stop ----
.\disconnect-horizon-vps.ps1

# ---- Pi: status ----
ssh user@<pi-ip> "cd ~/horizon && docker compose ps && curl -s http://127.0.0.1:8787/readyz"

# ---- Pi: rebuild after git pull ----
ssh user@<pi-ip> "cd ~/horizon && git pull && docker compose build horizon-proxy && docker compose up -d"
```

State files and paths worth knowing:

- Tunnel state: `%USERPROFILE%\.horizon\vps-tunnel-state.json` (records the SSH
  PID + ports; connect reuses it, disconnect kills by it)
- Claude settings patched for the session: `%USERPROFILE%\.claude\settings.json`
- Pi proxy data (ledger, keys, logs): named Docker volume `horizon_workspace`
  mounted at `/home/nonroot/.horizon`
- Pi proxy logs: inside the container at
  `/home/nonroot/.horizon/logs/proxy-8787.log`
