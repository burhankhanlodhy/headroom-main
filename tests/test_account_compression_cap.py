"""Free-plan compression cap: the control plane decides, the proxy honours it.

Once ``/internal/proxy/authorize`` reports ``compression_allowed: false`` the
verified account must be served as full passthrough on every compression
path (they all consult ``_horizon_bypass_enabled``), the decision must say
why, and responses must tell the client compression is paused.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from horizon.proxy.account_analytics import (
    AccountContext,
    AccountMiddleware,
    _account,
    compression_paused,
)
from horizon.proxy.compression_decision import CompressionDecision
from horizon.proxy.helpers import _horizon_bypass_enabled


def _context(*, allowed: bool) -> AccountContext:
    service = SimpleNamespace(runtime_id=str(uuid4()), _enqueue=lambda event: None)
    return AccountContext(str(uuid4()), str(uuid4()), service, compression_allowed=allowed)


def _decide(headers: dict[str, str] | None = None, *, optimize: bool = True) -> CompressionDecision:
    return CompressionDecision.decide(
        headers=headers or {},
        config=SimpleNamespace(optimize=optimize),
        usage_reporter=None,
        messages=[{"role": "user", "content": "hi"}],
    )


def _with_account(allowed: bool, fn):
    token = _account.set(_context(allowed=allowed))
    try:
        return fn()
    finally:
        _account.reset(token)


# ── Policy helpers ────────────────────────────────────────────────────


def test_no_account_context_never_pauses() -> None:
    assert compression_paused() is False
    assert _horizon_bypass_enabled({}) is False
    assert _decide().should_compress is True


def test_capped_account_is_passthrough_everywhere() -> None:
    assert _with_account(False, compression_paused) is True
    assert _with_account(False, lambda: _horizon_bypass_enabled({})) is True


def test_uncapped_account_still_compresses() -> None:
    assert _with_account(True, lambda: _horizon_bypass_enabled({})) is False
    assert _with_account(True, _decide).should_compress is True


def test_decision_reports_plan_cap_not_bypass_header() -> None:
    d = _with_account(False, _decide)
    assert d.should_compress is False
    assert d.passthrough_reason == "plan_cap_reached"
    assert d.plan_cap_reached is True
    assert d.bypass_header_set is False


def test_explicit_bypass_header_outranks_plan_cap() -> None:
    d = _with_account(False, lambda: _decide({"x-horizon-bypass": "true"}))
    assert d.passthrough_reason == "bypass_header"
    assert d.plan_cap_reached is True


def test_operator_kill_switch_outranks_plan_cap() -> None:
    d = _with_account(False, lambda: _decide(optimize=False))
    assert d.passthrough_reason == "compression_disabled"


# ── Middleware wiring ─────────────────────────────────────────────────


class _Service:
    enabled = True

    def __init__(self, authorize_data: dict[str, Any]):
        self.runtime_id = str(uuid4())
        self.events: list[dict[str, Any]] = []
        self._data = authorize_data

    async def authorize(self, key: str, scope: str):
        return 200, self._data

    def _enqueue(self, event: dict[str, Any]) -> None:
        self.events.append(event)


def _run_request(authorize_data: dict[str, Any]) -> tuple[dict[str, Any], list[tuple[bytes, bytes]]]:
    seen: dict[str, Any] = {}
    sent: list[dict[str, Any]] = []

    async def app(scope, receive, send):
        seen["paused"] = compression_paused()
        seen["bypass"] = _horizon_bypass_enabled({})
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    async def receive():
        return {"type": "http.request", "body": b"{}", "more_body": False}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/messages",
        "headers": [(b"x-horizon-proxy-token", b"cs_live_test")],
    }
    middleware = AccountMiddleware(app, _Service(authorize_data))
    asyncio.run(middleware(scope, receive, send))
    start = next(m for m in sent if m["type"] == "http.response.start")
    return seen, start["headers"]


def _ids() -> dict[str, str]:
    return {"user_id": str(uuid4()), "key_id": str(uuid4())}


def test_middleware_pauses_and_labels_capped_account() -> None:
    seen, headers = _run_request({**_ids(), "compression_allowed": False})
    assert seen == {"paused": True, "bypass": True}
    assert (b"x-contextshrink-compression", b"paused") in headers


def test_middleware_leaves_entitled_account_alone() -> None:
    seen, headers = _run_request({**_ids(), "compression_allowed": True})
    assert seen == {"paused": False, "bypass": False}
    assert all(name != b"x-contextshrink-compression" for name, _ in headers)


def test_middleware_defaults_to_allowed_for_older_control_plane() -> None:
    seen, _ = _run_request(_ids())
    assert seen["paused"] is False
