"""HorizonBundle — single-helper MCP wiring for a Strands Agent.

The cleanest production setup for Strands is the same kit
``horizon wrap claude`` installs for Claude Code, restated as
Strands-native primitives:

* **Horizon MCP** (``horizon mcp serve``) — exposes
  ``horizon_retrieve`` / ``horizon_compress`` / ``horizon_stats``
  via stdio. The proxy emits ``Retrieve original: hash=...`` markers
  in compressed content; the LLM calls ``horizon_retrieve`` when it
  needs the original; Strands' MCP dispatcher resolves it via this
  server. Works identically in streaming and non-streaming.

* **Serena MCP** — the coding-task compressor (symbol search,
  references, call chains, impact analysis) so the agent queries
  the code graph instead of reading whole files. Auto-installed via
  ``uvx`` on first launch. On by default; disable with
  ``enable_serena_mcp=False``.

* **HorizonHookProvider** — the in-process tool-output compressor
  for Strands. Compresses tool outputs in-place via ``AfterToolCallEvent`` so
  verbose JSON / log / search outputs are shrunk before they
  pollute the agent's context.

Pattern
-------

.. code-block:: python

    from strands import Agent
    from strands.models.openai import OpenAIModel
    from horizon.integrations.strands import HorizonBundle

    model = OpenAIModel(
        model_id="bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        client_args={"base_url": "http://127.0.0.1:8787/v1", "api_key": "x"},
    )

    bundle = HorizonBundle(proxy_url="http://127.0.0.1:8787")
    agent = Agent(
        model=model,
        tools=bundle.tools,    # Strands starts the MCP subprocesses on first use
        hooks=bundle.hooks,
    )
    response = agent("Search the codebase for the auth middleware.")

Lifecycle
---------

The bundle does **not** start the MCP subprocesses itself —
:class:`strands.tools.mcp.MCPClient` is lazily started by Strands'
``Agent`` when it loads tools, and stopped when the agent is torn
down. Construct the bundle, hand its ``tools`` / ``hooks`` to the
agent, and let Strands own the lifecycle. This matches Strands'
contract: MCP clients passed via ``tools=[...]`` MUST be unstarted.

The bundle does **not** start the proxy either — it connects to one.
Production deploys run the proxy as a long-lived service
(ECS / k8s / EC2); local-dev users start it manually with
``horizon proxy``. This keeps the bundle stateless and lets the
proxy scale independently of the agent fleet.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import partial
from typing import Any

# Strands + MCP SDK imports are required dependencies of this bundle —
# fail loud on import so a missing dep surfaces at construction time,
# not three frames deep inside an Agent call.
from mcp import StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402
from strands.tools.mcp import MCPClient  # noqa: E402

from horizon import HorizonConfig
from horizon.mcp_registry.install import (
    DEFAULT_PROXY_URL,
    build_horizon_spec,
    build_serena_spec,
)

from .hooks import HorizonHookProvider

logger = logging.getLogger(__name__)

#: Default Serena context — see https://github.com/oraios/serena for the
#: full context catalog. ``ide-assistant`` is the closest match for a
#: code-aware agent loop (the same context ``horizon wrap claude`` uses).
DEFAULT_SERENA_CONTEXT = "ide-assistant"


def _client_for(spec: Any) -> MCPClient:
    params = StdioServerParameters(
        command=spec.command,
        args=list(spec.args),
        env=dict(spec.env) if spec.env else None,
    )
    # `partial` (not lambda) so mypy can infer the callable's signature.
    return MCPClient(partial(stdio_client, params))


def _make_horizon_client(proxy_url: str) -> MCPClient:
    return _client_for(build_horizon_spec(proxy_url))


def _make_serena_client(context: str) -> MCPClient:
    return _client_for(build_serena_spec(context))


@dataclass
class HorizonBundle:
    """Single helper that hands a Strands Agent every Horizon integration.

    Attributes:
        proxy_url: HTTP URL the Horizon MCP server should contact for
            retrieval. Default :data:`DEFAULT_PROXY_URL`
            (``http://127.0.0.1:8787``).
        serena_context: Serena context label. Default ``"ide-assistant"``.
        enable_horizon_mcp: Include the Horizon MCP server. Default True.
        enable_serena_mcp: Include the Serena MCP server — the coding-task
            compressor. Default True. Adds a ``uvx`` first-launch download.
        enable_hooks: Include :class:`HorizonHookProvider` for in-place
            tool-output compression. Default True.
        config: Optional :class:`HorizonConfig` passed to
            :class:`HorizonHookProvider`. Default uses framework
            defaults.

    The bundle is **stateless** w.r.t. subprocess management — Strands'
    ``Agent`` owns the MCP subprocess lifecycle once you pass
    ``bundle.tools`` to it. Constructing a bundle is cheap; the
    subprocesses don't start until ``Agent`` calls ``load_tools``.
    """

    proxy_url: str = DEFAULT_PROXY_URL
    serena_context: str = DEFAULT_SERENA_CONTEXT
    enable_horizon_mcp: bool = True
    # Serena is the coding-task compressor (symbol-level code navigation).
    enable_serena_mcp: bool = True
    # The proxy is the single source of truth for compression — it sees
    # the full message list, owns CompressionPolicy, owns PrefixCacheTracker,
    # and places `cache_control` breakpoints. The in-process hook
    # (HorizonHookProvider) is an optimisation for memory/network when
    # Strands runs on a different host or holds very long conversations.
    # Default is OFF so the bundle stays "one helper, just the proxy
    # does the work" for the typical case. Flip on for long-running or
    # cross-host deploys.
    enable_hooks: bool = False
    config: HorizonConfig | None = None

    _horizon_mcp: MCPClient | None = field(default=None, init=False, repr=False, compare=False)
    _serena_mcp: MCPClient | None = field(default=None, init=False, repr=False, compare=False)
    _hook: HorizonHookProvider | None = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.enable_horizon_mcp:
            self._horizon_mcp = _make_horizon_client(self.proxy_url)
            logger.info(
                "HorizonBundle: Horizon MCP client constructed (proxy_url=%s)",
                self.proxy_url,
            )
        if self.enable_serena_mcp:
            self._serena_mcp = _make_serena_client(self.serena_context)
            logger.info(
                "HorizonBundle: Serena MCP client constructed (code memory, context=%s)",
                self.serena_context,
            )
        if self.enable_hooks:
            self._hook = HorizonHookProvider(config=self.config)
            logger.info("HorizonBundle: HorizonHookProvider attached")

    @property
    def tools(self) -> list[Any]:
        """MCP clients to hand to ``Agent(tools=...)``.

        Returned MCPClient instances are **unstarted** — Strands' Agent
        starts them on first use and stops them on teardown.
        """
        out: list[Any] = []
        if self._horizon_mcp is not None:
            out.append(self._horizon_mcp)
        if self._serena_mcp is not None:
            out.append(self._serena_mcp)
        return out

    @property
    def hooks(self) -> list[Any]:
        """Hook providers to hand to ``Agent(hooks=...)``."""
        return [self._hook] if self._hook is not None else []

    @property
    def horizon_mcp(self) -> MCPClient | None:
        """Direct handle to the Horizon MCPClient (for advanced callers)."""
        return self._horizon_mcp

    @property
    def serena_mcp(self) -> MCPClient | None:
        """Direct handle to the Serena MCPClient (for advanced callers)."""
        return self._serena_mcp
