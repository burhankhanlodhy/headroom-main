from __future__ import annotations

import base64
import importlib.util
import json
import sys
import types
from pathlib import Path

from click.testing import CliRunner

from horizon.capture.network_diff import (
    compare_captures,
    load_capture_file,
    render_markdown_report,
)
from horizon.cli.main import main


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def _body(payload: dict[str, object]) -> str:
    return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")


class _Headers(dict[str, str]):
    def items(self, multi: bool = False):
        return super().items()


def _load_capture_addon(
    monkeypatch,
    tmp_path: Path,
    lane: str,
    token: str | None,
    *,
    include_hosts: str = "api.anthropic.com",
    token_hosts: str = "horizon-proxy",
):
    fake_http = types.SimpleNamespace(HTTPFlow=object)
    fake_mitmproxy = types.ModuleType("mitmproxy")
    fake_mitmproxy.http = fake_http
    monkeypatch.setitem(sys.modules, "mitmproxy", fake_mitmproxy)
    monkeypatch.setenv("CAPTURE_LANE", lane)
    monkeypatch.setenv("CAPTURE_INCLUDE_HOSTS", include_hosts)
    monkeypatch.setenv("CAPTURE_PROXY_TOKEN_HOSTS", token_hosts)
    monkeypatch.setenv("CAPTURE_OUTPUT", str(tmp_path / f"{lane}.jsonl"))
    if token is None:
        monkeypatch.delenv("CAPTURE_PROXY_TOKEN", raising=False)
    else:
        monkeypatch.setenv("CAPTURE_PROXY_TOKEN", token)

    path = Path(__file__).parents[1] / "docker/differential-network-capture/mitm_capture.py"
    spec = importlib.util.spec_from_file_location(f"mitm_capture_{lane}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_network_capture_injects_token_only_on_included_horizon_client_lane(
    monkeypatch, tmp_path: Path
) -> None:
    token = "capture-secret"
    horizon_addon = _load_capture_addon(monkeypatch, tmp_path, "horizon-client", token)
    horizon_flow = types.SimpleNamespace(
        request=types.SimpleNamespace(
            headers=_Headers(),
            pretty_host="api.anthropic.com",
            pretty_url="https://api.anthropic.com/v1/messages",
            method="POST",
            raw_content=b"{}",
        ),
        server_conn=types.SimpleNamespace(address=("horizon-proxy", 8787)),
        response=types.SimpleNamespace(
            headers=_Headers({"X-Horizon-Proxy-Token": token}),
            raw_content=b"{}",
            status_code=200,
        ),
    )

    horizon_addon.request(horizon_flow)

    assert horizon_flow.request.headers == {"X-Horizon-Proxy-Token": token}
    horizon_addon.response(horizon_flow)
    record = json.loads((tmp_path / "horizon-client.jsonl").read_text(encoding="utf-8"))
    assert record["request_headers"]["X-Horizon-Proxy-Token"] == "<redacted>"
    assert record["response_headers"]["X-Horizon-Proxy-Token"] == "<redacted>"

    outside_flow = types.SimpleNamespace(
        request=types.SimpleNamespace(
            headers=_Headers(),
            pretty_host="other.example.com",
        ),
        server_conn=types.SimpleNamespace(address=("other.example.com", 443)),
    )

    horizon_addon.request(outside_flow)

    assert outside_flow.request.headers == {}

    direct_addon = _load_capture_addon(monkeypatch, tmp_path, "direct", token)
    direct_flow = types.SimpleNamespace(
        request=types.SimpleNamespace(
            headers=_Headers(),
            pretty_host="api.anthropic.com",
        ),
        server_conn=types.SimpleNamespace(address=("horizon-proxy", 8787)),
    )

    direct_addon.request(direct_flow)

    assert direct_flow.request.headers == {}


def test_network_capture_token_destination_allowlist_is_independent_of_logging_filter(
    monkeypatch, tmp_path: Path
) -> None:
    addon = _load_capture_addon(
        monkeypatch,
        tmp_path,
        "horizon-client",
        "capture-secret",
        include_hosts="other.example.com",
    )
    flow = types.SimpleNamespace(
        request=types.SimpleNamespace(headers=_Headers(), pretty_host="api.anthropic.com"),
        server_conn=types.SimpleNamespace(address=("horizon-proxy", 8787)),
    )
    addon.request(flow)
    assert flow.request.headers == {"X-Horizon-Proxy-Token": "capture-secret"}

    empty_allowlist = _load_capture_addon(
        monkeypatch, tmp_path, "horizon-client", "capture-secret", token_hosts=""
    )
    empty_flow = types.SimpleNamespace(
        request=types.SimpleNamespace(headers=_Headers(), pretty_host="api.anthropic.com"),
        server_conn=types.SimpleNamespace(address=("horizon-proxy", 8787)),
    )
    empty_allowlist.request(empty_flow)
    assert empty_flow.request.headers == {}


def test_network_diff_redacts_and_reports_body_json_deltas(tmp_path: Path) -> None:
    direct_path = tmp_path / "direct.jsonl"
    horizon_path = tmp_path / "horizon.jsonl"
    _write_jsonl(
        direct_path,
        [
            {
                "lane": "direct",
                "method": "POST",
                "url": "https://api.anthropic.com/v1/messages?api_key=secret",
                "request_headers": {
                    "authorization": "Bearer secret",
                    "anthropic-version": "2023-06-01",
                    "anthropic-beta": "deferred-tools",
                },
                "request_body_b64": _body(
                    {"model": "claude", "messages": [{"content": "hi"}], "tools": []}
                ),
                "response_status": 200,
            }
        ],
    )
    _write_jsonl(
        horizon_path,
        [
            {
                "lane": "horizon",
                "method": "POST",
                "url": "https://api.anthropic.com/v1/messages?api_key=secret",
                "request_headers": {
                    "authorization": "Bearer other",
                    "anthropic-version": "2023-06-01",
                    "x-horizon-mode": "optimize",
                },
                "request_body_b64": _body(
                    {
                        "model": "claude",
                        "messages": [{"content": "hello"}],
                        "metadata": {},
                        "tools": [{"name": "ctx_execute", "input_schema": {"type": "object"}}],
                    }
                ),
                "response_status": 200,
            }
        ],
    )

    direct = load_capture_file(direct_path, fallback_lane="direct")
    horizon = load_capture_file(horizon_path, fallback_lane="horizon")

    assert direct[0].url == "https://api.anthropic.com/v1/messages?api_key=%3Credacted%3E"
    assert direct[0].request_headers["authorization"] == "<redacted>"

    diff = compare_captures(direct, horizon)
    assert diff.direct_count == 1
    assert diff.horizon_count == 1
    paired = diff.paired[0]
    assert paired["headers"]["only_horizon"] == ["x-horizon-mode"]
    assert "$.metadata" in paired["json"]["only_horizon"]
    assert "$.messages[0].content" in paired["json"]["changed"]
    assert paired["anthropic"]["direct"]["tools_count"] == 0
    assert paired["anthropic"]["horizon"]["tools_count"] == 1

    markdown = render_markdown_report(diff)
    assert "Differential Network Capture Report" in markdown
    assert "POST api.anthropic.com/v1/messages?api_key=%3Credacted%3E" in markdown
    assert "tools=0->1" in markdown


def test_network_diff_cli_writes_markdown_and_json(tmp_path: Path) -> None:
    direct_path = tmp_path / "direct.jsonl"
    horizon_path = tmp_path / "horizon.jsonl"
    markdown_path = tmp_path / "report.md"
    json_path = tmp_path / "report.json"
    record = {
        "method": "POST",
        "url": "https://api.anthropic.com/v1/messages",
        "request_headers": {},
        "request_body_b64": _body({"model": "claude"}),
        "response_status": 200,
    }
    _write_jsonl(direct_path, [record])
    _write_jsonl(horizon_path, [record])

    result = CliRunner().invoke(
        main,
        [
            "capture",
            "network-diff",
            "--direct",
            str(direct_path),
            "--horizon",
            str(horizon_path),
            "--output",
            str(markdown_path),
            "--json-output",
            str(json_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Wrote Markdown report" in result.output
    assert "Differential Network Capture Report" in markdown_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["direct_count"] == 1
    assert payload["horizon_count"] == 1
