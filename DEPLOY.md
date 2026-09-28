# Deploying Horizon on a VPS

This walkthrough puts a Horizon proxy on a VPS with TLS, issues per-user API
keys, and wires a local machine up to use it. Two connectivity paths are
supported — pick one:

- **Caddy TLS front** (recommended for daily use): the VPS serves
  `https://<your-domain>`; clients on any network reach it directly.
- **SSH tunnel** (zero extra surface): the proxy stays loopback-only on the
  VPS and you forward a local port over SSH. Use the bundled
  `connect-horizon-vps.ps1` / `disconnect-horizon-vps.ps1` scripts.

In both cases the data plane is gated by credentials: the operator master
token (`HORIZON_PROXY_TOKEN`) and/or per-user keys issued below.

## 1. Provision

1. A VPS with Docker + the Docker compose plugin.
2. A DNS A/AAAA record pointing at the VPS (TLS path only).
3. Ports open: `22` (SSH), and `80` + `443` (TLS path only).

## 2. Configure

```bash
cp .env.example .env
# HORIZON_PROXY_TOKEN: openssl rand -hex 32
# HORIZON_PUBLIC_DOMAIN: only needed for the TLS profile
$EDITOR .env
```

## 3. Run

```bash
docker compose up -d                          # loopback-only + SSH tunnel path
docker compose --profile tls up -d            # adds the Caddy TLS front
```

Caddy obtains and renews certificates automatically once
`HORIZON_PUBLIC_DOMAIN` resolves to the VPS.

## 4. Issue per-user keys

Keys are stored (hashed) in `keys.db` inside the `horizon_workspace` volume,
so issue them through the container:

```bash
docker compose exec horizon-proxy horizon keys issue alice
# hz_...  (shown exactly once — hand it to the user now)
docker compose exec horizon-proxy horizon keys list
docker compose exec horizon-proxy horizon keys revoke alice
```

A `hz_...` key authenticates the same request shapes as the master token,
with the key name recorded for per-key request stats (`/stats`).

## 5. Point clients at it

**TLS path** — from any machine:

```
ANTHROPIC_BASE_URL=https://<your-domain>
x-horizon-proxy-token: hz_...
```

**SSH tunnel path** — run `connect-horizon-vps.ps1`, then point the client at
`http://127.0.0.1:8787` with the same header.

**Local wrap flow (unchanged)** — `horizon wrap claude` on this machine still
manages its own loopback proxy; nothing on the VPS is involved unless you
explicitly opt in.
