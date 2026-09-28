"""Tests for CrewAI agent tool integration.

Tests cover:
1. ToolCompressionMetrics - Dataclass for tool compression metrics
2. ToolMetricsCollector - Collector for compression metrics
3. HorizonToolWrapper - Wrapper for CrewAI tools with compression
4. wrap_tools_with_horizon - Convenience function for wrapping multiple tools
5. get_tool_metrics / reset_tool_metrics - Global metrics access
"""

from datetime import datetime
from unittest.mock import patch

import pytest

try:
    from crewai.tools.base_tool import tool as crewai_tool

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not CREWAI_AVAILABLE, reason="CrewAI not installed")


def _make_large_output(n: int = 200) -> str:
    """Create a large JSON string to trigger compression."""
    import json

    return json.dumps({"items": [{"id": i, "data": "x" * 50} for i in range(n)]})


class TestToolCompressionMetrics:
    """Tests for ToolCompressionMetrics dataclass."""

    def test_create_metrics(self):
        from horizon.integrations.crewai.agents import ToolCompressionMetrics

        metrics = ToolCompressionMetrics(
            tool_name="search",
            timestamp=datetime.now(),
            chars_before=5000,
            chars_after=2000,
            chars_saved=3000,
            compression_ratio=0.4,
            was_compressed=True,
        )

        assert metrics.tool_name == "search"
        assert metrics.chars_before == 5000
        assert metrics.chars_saved == 3000
        assert metrics.was_compressed is True

    def test_metrics_all_fields_required(self):
        from horizon.integrations.crewai.agents import ToolCompressionMetrics

        with pytest.raises(TypeError):
            ToolCompressionMetrics()  # type: ignore[call-arg]


class TestToolMetricsCollector:
    """Tests for ToolMetricsCollector."""

    def test_empty_summary(self):
        from horizon.integrations.crewai.agents import ToolMetricsCollector

        collector = ToolMetricsCollector()
        summary = collector.get_summary()
        assert summary["total_invocations"] == 0
        assert summary["total_compressions"] == 0

    def test_add_and_summary(self):
        from horizon.integrations.crewai.agents import (
            ToolCompressionMetrics,
            ToolMetricsCollector,
        )

        collector = ToolMetricsCollector()
        collector.add(
            ToolCompressionMetrics(
                tool_name="search",
                timestamp=datetime.now(),
                chars_before=5000,
                chars_after=2000,
                chars_saved=3000,
                compression_ratio=0.4,
                was_compressed=True,
            )
        )

        summary = collector.get_summary()
        assert summary["total_invocations"] == 1
        assert summary["total_compressions"] == 1
        assert summary["total_chars_saved"] == 3000
        assert "search" in summary["by_tool"]

    def test_caps_at_1000(self):
        from horizon.integrations.crewai.agents import (
            ToolCompressionMetrics,
            ToolMetricsCollector,
        )

        collector = ToolMetricsCollector()
        for _i in range(1050):
            collector.add(
                ToolCompressionMetrics(
                    tool_name="t",
                    timestamp=datetime.now(),
                    chars_before=100,
                    chars_after=100,
                    chars_saved=0,
                    compression_ratio=1.0,
                    was_compressed=False,
                )
            )
        assert len(collector.metrics) == 1000


class TestGlobalMetrics:
    """Tests for global metrics functions."""

    def test_get_and_reset(self):
        from horizon.integrations.crewai.agents import get_tool_metrics, reset_tool_metrics

        metrics = get_tool_metrics()
        assert metrics is not None
        reset_tool_metrics()
        assert get_tool_metrics() is not metrics


class TestHorizonToolWrapper:
    """Tests for HorizonToolWrapper."""

    @patch("horizon.integrations.crewai.agents.compress_tool_result")
    def test_skips_short_output(self, mock_compress):
        from horizon.integrations.crewai.agents import HorizonToolWrapper, ToolMetricsCollector

        @crewai_tool
        def small_tool(query: str) -> str:
            """Return small output."""
            return "short"

        collector = ToolMetricsCollector()
        wrapper = HorizonToolWrapper(
            small_tool,
            min_chars_to_compress=1000,
            metrics_collector=collector,
        )

        result = wrapper.run(query="test")
        assert result == "short"
        mock_compress.assert_not_called()
        assert collector.get_summary()["total_compressions"] == 0

    @patch("horizon.integrations.crewai.agents.compress_tool_result")
    def test_compresses_large_output(self, mock_compress):
        from horizon.integrations.crewai.agents import HorizonToolWrapper, ToolMetricsCollector

        large = _make_large_output()
        mock_compress.return_value = "compressed"

        @crewai_tool
        def big_tool(query: str) -> str:
            """Return large output."""
            return large

        collector = ToolMetricsCollector()
        wrapper = HorizonToolWrapper(
            big_tool,
            min_chars_to_compress=100,
            metrics_collector=collector,
        )

        result = wrapper.run(query="test")
        assert result == "compressed"
        mock_compress.assert_called_once()
        assert collector.get_summary()["total_compressions"] == 1

    @patch(
        "horizon.integrations.crewai.agents.compress_tool_result",
        side_effect=RuntimeError("boom"),
    )
    def test_passes_through_on_error(self, mock_compress):
        from horizon.integrations.crewai.agents import HorizonToolWrapper, ToolMetricsCollector

        large = _make_large_output()

        @crewai_tool
        def flaky_tool(query: str) -> str:
            """Return large output."""
            return large

        collector = ToolMetricsCollector()
        wrapper = HorizonToolWrapper(
            flaky_tool,
            min_chars_to_compress=100,
            metrics_collector=collector,
        )

        result = wrapper.run(query="test")
        assert result == large
        assert collector.get_summary()["total_compressions"] == 0

    def test_preserves_tool_metadata(self):
        from horizon.integrations.crewai.agents import HorizonToolWrapper

        @crewai_tool
        def my_fn(x: int) -> str:
            """Do something useful."""
            return str(x)

        wrapper = HorizonToolWrapper(my_fn)
        assert wrapper.name == "my_fn"
        assert wrapper.description == "Do something useful."


class TestWrapToolsWithHorizon:
    """Tests for wrap_tools_with_horizon convenience function."""

    @patch("horizon.integrations.crewai.agents.compress_tool_result")
    def test_wraps_multiple_tools(self, mock_compress):
        from horizon.integrations.crewai.agents import wrap_tools_with_horizon

        @crewai_tool
        def tool_a(q: str) -> str:
            """Tool A."""
            return "a"

        @crewai_tool
        def tool_b(q: str) -> str:
            """Tool B."""
            return "b"

        wrapped = wrap_tools_with_horizon([tool_a, tool_b])
        assert len(wrapped) == 2
        assert wrapped[0].name == "tool_a"
        assert wrapped[1].name == "tool_b"

    @patch("horizon.integrations.crewai.agents.compress_tool_result")
    def test_shared_metrics(self, mock_compress):
        from horizon.integrations.crewai.agents import (
            ToolMetricsCollector,
            wrap_tools_with_horizon,
        )

        large = _make_large_output()
        mock_compress.return_value = "compressed"

        @crewai_tool
        def big(q: str) -> str:
            """Big tool."""
            return large

        collector = ToolMetricsCollector()
        wrapped = wrap_tools_with_horizon(
            [big],
            min_chars_to_compress=100,
            metrics_collector=collector,
        )

        wrapped[0].run(q="test")
        assert collector.get_summary()["total_invocations"] == 1
