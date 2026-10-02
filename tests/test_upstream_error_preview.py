"""Log-safe previews of upstream error bodies (why a provider refused)."""

from __future__ import annotations

import pytest

from horizon.proxy.handlers.streaming import upstream_error_preview


@pytest.mark.parametrize(
    "body, expected",
    [
        (
            b"<!DOCTYPE html><html><head><title>Just a moment...</title></head></html>",
            "html title='Just a moment...'",
        ),
        (b'{"detail":"Unauthorized"}', "detail='Unauthorized'"),
        (
            b'{"error":{"type":"invalid_request_error","code":"x","message":"Nope"}}',
            "type='invalid_request_error' code='x' message='Nope'",
        ),
        (b"plain   text\nerror", "plain text error"),
    ],
)
def test_preview_summarises_html_and_json(body: bytes, expected: str) -> None:
    assert upstream_error_preview(body) == expected


def test_preview_redacts_tokens_and_truncates() -> None:
    body = b'{"error":{"message":"Bearer abc.def.ghi sk-1234567890abcd eyJhbGciOiJIUzI1NiJ9.x"}}'
    out = upstream_error_preview(body)
    assert "abc.def" not in out and "sk-123" not in out and "eyJhbG" not in out
    assert len(upstream_error_preview(b"x" * 1000)) == 200
