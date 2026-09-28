"""LangChain integration for Horizon.

This package provides seamless integration with LangChain, including:
- HorizonChatModel: Drop-in wrapper for any LangChain chat model
- HorizonChatMessageHistory: Automatic conversation compression
- HorizonDocumentCompressor: Relevance-based document filtering
- HorizonToolWrapper: Tool output compression for agents
- StreamingMetricsTracker: Token counting during streaming
- HorizonLangSmithCallbackHandler: LangSmith trace enrichment
- compress_tool_messages: LangGraph pre-model hook for ToolMessage compression
- create_compress_tool_messages_node: LangGraph node factory

Example:
    from langchain_openai import ChatOpenAI
    from horizon.integrations.langchain import HorizonChatModel

    # Wrap any LangChain model
    llm = HorizonChatModel(ChatOpenAI(model="gpt-4o"))

    # Use like normal - optimization happens automatically
    response = llm.invoke("Hello!")

Install: pip install horizon[langchain]
"""

# Agent tool wrapping
from .agents import (
    HorizonToolWrapper,
    ToolCompressionMetrics,
    ToolMetricsCollector,
    get_tool_metrics,
    reset_tool_metrics,
    wrap_tools_with_horizon,
)

# Core chat model wrapper
from .chat_model import (
    HorizonCallbackHandler,
    HorizonChatModel,
    HorizonRunnable,
    OptimizationMetrics,
    langchain_available,
    optimize_messages,
)

# LangGraph integration
from .langgraph import (
    CompressToolMessagesConfig,
    CompressToolMessagesResult,
    ToolMessageCompressionMetrics,
    compress_tool_messages,
    create_compress_tool_messages_node,
)

# LangSmith integration
from .langsmith import (
    HorizonLangSmithCallbackHandler,
    is_langsmith_available,
    is_langsmith_tracing_enabled,
)

# Memory integration
from .memory import HorizonChatMessageHistory

# Provider auto-detection
from .providers import (
    detect_provider,
    get_horizon_provider,
    get_model_name_from_langchain,
)

# Retriever integration
from .retriever import CompressionMetrics, HorizonDocumentCompressor

# Streaming metrics
from .streaming import (
    StreamingMetrics,
    StreamingMetricsCallback,
    StreamingMetricsTracker,
    track_async_streaming_response,
    track_streaming_response,
)

__all__ = [
    # Core
    "HorizonChatModel",
    "HorizonCallbackHandler",
    "HorizonRunnable",
    "OptimizationMetrics",
    "optimize_messages",
    "langchain_available",
    # Provider Detection
    "detect_provider",
    "get_horizon_provider",
    "get_model_name_from_langchain",
    # Memory
    "HorizonChatMessageHistory",
    # Retrievers
    "HorizonDocumentCompressor",
    "CompressionMetrics",
    # Agents
    "HorizonToolWrapper",
    "ToolCompressionMetrics",
    "ToolMetricsCollector",
    "wrap_tools_with_horizon",
    "get_tool_metrics",
    "reset_tool_metrics",
    # LangGraph
    "compress_tool_messages",
    "create_compress_tool_messages_node",
    "CompressToolMessagesConfig",
    "CompressToolMessagesResult",
    "ToolMessageCompressionMetrics",
    # LangSmith
    "HorizonLangSmithCallbackHandler",
    "is_langsmith_available",
    "is_langsmith_tracing_enabled",
    # Streaming
    "StreamingMetricsTracker",
    "StreamingMetricsCallback",
    "StreamingMetrics",
    "track_streaming_response",
    "track_async_streaming_response",
]
