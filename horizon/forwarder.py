"""Loopback relay to a remote Horizon proxy.

``horizon forward start`` runs this app on the local machine: it listens on
loopback only, attaches the caller's per-user ``hz_...`` key from the OS
credential store (:mod:`horizon.vault`), and streams everything to the
remote Horizon proxy. The key therefore never appears in a plaintext config
file, and the wrapped client (Claude Code, Codex, ...) simply points at
``http://127.0.0.1:<port>``.

Streaming matters: LLM clients consume SSE responses incrementally, so the
relay pipes the upstream body through instead of buffering it.
"""

from __future__ import annotations

import ipaddress
import logging
from collections.abc import Callable

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse

logger = logging.getLogger(__name__)

#: Hop-by-hop headers (RFC 7230 section 6.1) - never relayed in either direction.
_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}

#: The proxy security gate reads the credential from this header.
CREDENTIAL_HEADER = "x-horizon-proxy-token"

_DEFAULT_TIMEOUT = httpx.Timeout(300.0, connect=15.0)


def _is_loopback(host: str) -> bool:
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return host in ("localhost", "localhost.localdomain")
    return addr.is_loopback


def build_app(
    remote_url: str,
    credential_provider: Callable[[], str],
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """Build the relay app.

    ``credential_provider`` is called once per request (not at startup) so a
    rotated key stored mid-session is picked up without a restart. It should
    return the raw ``hz_...`` key and may raise :class:`horizon.vault.VaultError`.
    ``transport`` exists for tests (inject ``httpx.MockTransport``).
    """

    base = remote_url.rstrip("/")
    app = FastAPI(title="Horizon Forwarder", docs_url=None, redoc_url=None, openapi_url=None)
    client = httpx.AsyncClient(
        base_url=base,
        timeout=_DEFAULT_TIMEOUT,
        follow_redirects=False,
        transport=transport,
    )

    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    )
    async def relay(path: str, request: Request) -> Response:
        headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() not in _HOP_BY_HOP
            and name.lower() != "host"
            and name.lower() != CREDENTIAL_HEADER
        }
        headers[CREDENTIAL_HEADER] = credential_provider()
        body = await request.body()

        url = f"/{path}" if path else "/"
        try:
            upstream = client.build_request(
                request.method,
                url,
                headers=headers,
                content=body if request.method not in ("GET", "HEAD") else None,
                params=request.query_params,
            )
            upstream_resp = await client.send(upstream, stream=True)
        except httpx.HTTPError as exc:
            logger.warning("forwarder upstream error path=%s: %s", path, exc)
            return Response(
                content=f"upstream error: {exc}\n",
                status_code=502,
                media_type="text/plain",
            )

        resp_headers = {
            name: value
            for name, value in upstream_resp.headers.items()
            if name.lower() not in _HOP_BY_HOP
        }

        async def stream_iter():
            try:
                if upstream_resp.is_stream_consumed:
                    # Fully-buffered upstream (test transports, some gateways
                    # hand back a materialized response): relay the buffer.
                    yield upstream_resp.content
                else:
                    async for chunk in upstream_resp.aiter_raw():
                        yield chunk
            finally:
                await upstream_resp.aclose()

        return StreamingResponse(
            stream_iter(),
            status_code=upstream_resp.status_code,
            headers=resp_headers,
        )

    return app


def run_forwarder(
    remote_url: str,
    port: int,
    host: str = "127.0.0.1",
    credential_provider: Callable[[], str] | None = None,
) -> None:
    """Run the relay (blocking). Binds loopback only.

    ``credential_provider`` defaults to reading the per-user key from the OS
    credential store. Startup fails fast when no credential is stored.
    """

    if not _is_loopback(host):
        raise ValueError(
            f"refusing to bind non-loopback address {host!r} - the relay "
            "exists to keep the key local"
        )

    if credential_provider is None:
        from horizon.vault import VaultError, get_credential

        try:
            get_credential()  # fail fast with the actionable vault message
        except VaultError as exc:
            raise ValueError(str(exc)) from exc

        credential_provider = get_credential

    import uvicorn

    app = build_app(remote_url=remote_url, credential_provider=credential_provider)
    uvicorn.run(app, host=host, port=port, log_level="info")
