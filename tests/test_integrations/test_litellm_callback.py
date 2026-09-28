"""Tests for horizon.integrations.litellm_callback."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


def _import_callback() -> type:
    # Import the module directly to avoid triggering horizon/integrations/__init__.py
    # which pulls in langchain and the native .so extension.
    module_path = (
        Path(__file__).resolve().parents[2] / "horizon" / "integrations" / "litellm_callback.py"
    )
    spec = importlib.util.spec_from_file_location(
        "horizon.integrations.litellm_callback",
        module_path,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.HorizonCallback  # type: ignore[attr-defined]


HorizonCallback = _import_callback()


class TestHorizonCallbackPostCallSuccessHook:
    """async_post_call_success_hook must exist and return response unchanged."""

    def test_method_exists(self) -> None:
        cb = HorizonCallback()
        assert hasattr(cb, "async_post_call_success_hook"), (
            "HorizonCallback must define async_post_call_success_hook "
            "for LiteLLM proxy compatibility"
        )

    def test_method_is_coroutine(self) -> None:
        cb = HorizonCallback()
        assert inspect.iscoroutinefunction(cb.async_post_call_success_hook)

    @pytest.mark.asyncio
    async def test_returns_response_unchanged(self) -> None:
        cb = HorizonCallback()
        sentinel = object()
        result = await cb.async_post_call_success_hook(
            data={},
            user_api_key_dict=None,
            response=sentinel,
        )
        assert result is sentinel


class TestHorizonCallbackClientLifecycle:
    """Cloud client cleanup must be explicit and safe to repeat."""

    @pytest.mark.asyncio
    async def test_aclose_closes_and_clears_initialized_client(self) -> None:
        cb = HorizonCallback(api_key="hdr_test")
        client = MagicMock()
        client.aclose = AsyncMock()
        cb._client = client

        await cb.aclose()

        client.aclose.assert_awaited_once_with()
        assert cb._client is None

        await cb.aclose()
        client.aclose.assert_awaited_once_with()

    @pytest.mark.asyncio
    async def test_aclose_without_initialized_client_is_a_noop(self) -> None:
        cb = HorizonCallback(api_key="hdr_test")

        await cb.aclose()

        assert cb._client is None
