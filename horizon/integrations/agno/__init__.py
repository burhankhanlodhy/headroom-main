"""Agno integration for Horizon SDK.

This module provides seamless integration with Agno (formerly Phidata),
enabling automatic context optimization for Agno agents.

Components:
1. HorizonAgnoModel - Wraps any Agno model to apply Horizon transforms
2. create_horizon_hooks - Creates pre/post hooks for Agno agents
3. optimize_messages - Standalone function for manual optimization

Example:
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    from horizon.integrations.agno import HorizonAgnoModel

    # Wrap any Agno model
    model = OpenAIChat(id="gpt-4o")
    optimized_model = HorizonAgnoModel(model)

    # Use with agent
    agent = Agent(model=optimized_model)
    response = agent.run("Hello!")
"""

from .hooks import (
    HorizonPostHook,
    HorizonPreHook,
    HookMetrics,
    create_horizon_hooks,
)
from .model import (
    HorizonAgnoModel,
    OptimizationMetrics,
    agno_available,
    optimize_messages,
)
from .providers import get_horizon_provider, get_model_name_from_agno

__all__ = [
    # Model wrapper
    "HorizonAgnoModel",
    "OptimizationMetrics",
    "agno_available",
    "optimize_messages",
    # Hooks
    "create_horizon_hooks",
    "HorizonPreHook",
    "HorizonPostHook",
    "HookMetrics",
    # Provider detection
    "get_horizon_provider",
    "get_model_name_from_agno",
]
