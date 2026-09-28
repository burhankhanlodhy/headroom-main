"""Tests for normalizing client-specific tool names."""

from __future__ import annotations

import pytest

from horizon.config import DEFAULT_EXCLUDE_TOOLS, is_tool_excluded


@pytest.mark.parametrize(
    "name",
    [
        "horizon_retrieve",
        "mcp__horizon__horizon_retrieve",
        "mcp_horizon_horizon_retrieve",
        "horizon_horizon_retrieve",
    ],
)
def test_retrieve_tool_aliases_are_excluded(name: str) -> None:
    assert is_tool_excluded(name, DEFAULT_EXCLUDE_TOOLS)


def test_unrelated_underscored_tool_names_are_not_excluded() -> None:
    assert not is_tool_excluded("my_horizon_retrieve", DEFAULT_EXCLUDE_TOOLS)
    assert not is_tool_excluded("other_Read", DEFAULT_EXCLUDE_TOOLS)
