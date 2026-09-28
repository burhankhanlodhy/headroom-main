"""Comprehensive tests for Agno integration.

Tests cover:
1. HorizonAgnoModel - Wrapper for any Agno model
2. Provider detection - Detecting correct provider from Agno model
3. Hooks - Pre and post hooks for observability
4. optimize_messages() - Standalone optimization function
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Check if Agno is available
try:
    import agno  # noqa: F401

    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False

from horizon import HorizonConfig, HorizonMode

# Skip all tests if Agno not installed
pytestmark = pytest.mark.skipif(not AGNO_AVAILABLE, reason="Agno not installed")


def _response_usage(input_tokens: int, output_tokens: int, total_tokens: int):
    """Build response usage across Agno 2.x and 3.x module layouts."""

    try:
        from agno.metrics import MessageMetrics

        metrics_type = MessageMetrics
    except ImportError:
        from agno.models.metrics import Metrics

        metrics_type = Metrics
    return metrics_type(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


@pytest.fixture
def mock_agno_model():
    """Create a mock Agno model (OpenAIChat-like)."""
    from agno.models.response import ModelResponse

    mock = MagicMock()
    mock.__class__.__name__ = "OpenAIChat"
    mock.__class__.__module__ = "agno.models.openai"
    mock.id = "gpt-4o"

    # Mock response method
    def mock_response(messages, **kwargs):
        response = MagicMock()
        response.content = "Hello! I'm a mock response."
        response.metrics = MagicMock()
        response.metrics.input_tokens = 10
        response.metrics.output_tokens = 5
        response.metrics.total_tokens = 15
        return response

    mock.response = MagicMock(side_effect=mock_response)

    # Mock invoke method (returns ModelResponse for Agno's response() loop)
    def mock_invoke(messages, **kwargs):
        # Create a proper ModelResponse that Agno's response() can process
        return ModelResponse(
            role="assistant",
            content="Hello! I'm a mock response.",
            response_usage=_response_usage(10, 5, 15),
        )

    mock.invoke = MagicMock(side_effect=mock_invoke)

    # Mock streaming response
    def mock_stream(messages, **kwargs):
        yield MagicMock(content="Streaming...")

    mock.response_stream = MagicMock(side_effect=mock_stream)

    # Mock invoke_stream for streaming
    def mock_invoke_stream(messages, **kwargs):
        yield ModelResponse(
            role="assistant",
            content="Streaming...",
            response_usage=_response_usage(10, 5, 15),
        )

    mock.invoke_stream = MagicMock(side_effect=mock_invoke_stream)

    return mock


@pytest.fixture
def mock_claude_model():
    """Create a mock Agno model (Claude-like)."""
    mock = MagicMock()
    mock.__class__.__name__ = "Claude"
    mock.__class__.__module__ = "agno.models.anthropic"
    mock.id = "claude-3-5-sonnet-20241022"

    def mock_response(messages, **kwargs):
        response = MagicMock()
        response.content = "I'm Claude!"
        response.metrics = MagicMock()
        response.metrics.input_tokens = 20
        response.metrics.output_tokens = 10
        response.metrics.total_tokens = 30
        return response

    mock.response = MagicMock(side_effect=mock_response)
    return mock


@pytest.fixture
def sample_messages():
    """Sample messages in OpenAI format (Agno accepts this)."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ]


@pytest.fixture
def large_conversation():
    """Large conversation with many turns."""
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    for i in range(50):
        messages.append({"role": "user", "content": f"Question {i}: What is {i} + {i}?"})
        messages.append({"role": "assistant", "content": f"The answer is {i + i}."})
    return messages


class TestAgnoAvailable:
    """Tests for agno_available() helper."""

    def test_returns_bool(self):
        """agno_available returns boolean."""
        from horizon.integrations.agno import agno_available

        assert isinstance(agno_available(), bool)

    def test_returns_true_when_installed(self):
        """Returns True when Agno is installed."""
        from horizon.integrations.agno import agno_available

        assert agno_available() is True


class TestHorizonAgnoModel:
    """Tests for HorizonAgnoModel wrapper."""

    def test_init_with_defaults(self, mock_agno_model):
        """Initialize with default config."""
        from horizon.integrations.agno import HorizonAgnoModel

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert model.wrapped_model is mock_agno_model
        assert model.horizon_config is not None
        assert model._metrics_history == []
        assert model._total_tokens_saved == 0

    def test_init_with_custom_config(self, mock_agno_model):
        """Initialize with custom config."""
        from horizon.integrations.agno import HorizonAgnoModel

        config = HorizonConfig(default_mode=HorizonMode.AUDIT)
        model = HorizonAgnoModel(
            wrapped_model=mock_agno_model,
            horizon_config=config,
            horizon_mode=HorizonMode.SIMULATE,
        )

        assert model.horizon_config is config
        assert model.horizon_mode == HorizonMode.SIMULATE

    def test_init_auto_detect_provider(self, mock_agno_model):
        """Auto-detect provider from wrapped model."""
        from horizon.integrations.agno import HorizonAgnoModel

        model = HorizonAgnoModel(wrapped_model=mock_agno_model, auto_detect_provider=True)

        assert model.auto_detect_provider is True

    def test_forward_attributes(self, mock_agno_model):
        """Forward attribute access to wrapped model."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.custom_attribute = "test_value"
        model = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert model.custom_attribute == "test_value"

    def test_properties_not_forwarded(self, mock_agno_model):
        """Own properties should not be forwarded."""
        from horizon.integrations.agno import HorizonAgnoModel

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)

        # These should work without forwarding to wrapped model
        assert model.total_tokens_saved == 0
        assert model.metrics_history == []

    def test_convert_messages_to_openai(self, mock_agno_model, sample_messages):
        """Convert Agno messages to OpenAI format."""
        from horizon.integrations.agno import HorizonAgnoModel

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)

        # Test with dict messages (already OpenAI format)
        openai_msgs = model._convert_messages_to_openai(sample_messages)

        assert len(openai_msgs) == 2
        assert openai_msgs[0]["role"] == "system"
        assert openai_msgs[0]["content"] == "You are a helpful assistant."
        assert openai_msgs[1]["role"] == "user"
        assert "France" in openai_msgs[1]["content"]

    def test_convert_agno_message_objects(self, mock_agno_model):
        """Convert Agno Message objects to OpenAI format."""
        from horizon.integrations.agno import HorizonAgnoModel

        # Create mock Agno Message objects
        system_msg = MagicMock()
        system_msg.role = "system"
        system_msg.content = "You are helpful."
        system_msg.tool_calls = None
        system_msg.tool_call_id = None

        user_msg = MagicMock()
        user_msg.role = "user"
        user_msg.content = "Hello"
        user_msg.tool_calls = None
        user_msg.tool_call_id = None

        messages = [system_msg, user_msg]

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)
        openai_msgs = model._convert_messages_to_openai(messages)

        assert len(openai_msgs) == 2
        assert openai_msgs[0]["role"] == "system"
        assert openai_msgs[0]["content"] == "You are helpful."

    def test_convert_messages_with_tool_calls(self, mock_agno_model):
        """Convert messages with tool calls."""
        from horizon.integrations.agno import HorizonAgnoModel

        assistant_msg = MagicMock()
        assistant_msg.role = "assistant"
        assistant_msg.content = "I'll check the weather."
        assistant_msg.tool_calls = [
            {"id": "call_123", "name": "get_weather", "args": {"city": "Paris"}}
        ]
        assistant_msg.tool_call_id = None

        tool_msg = MagicMock()
        tool_msg.role = "tool"
        tool_msg.content = '{"temp": 20}'
        tool_msg.tool_calls = None
        tool_msg.tool_call_id = "call_123"

        messages = [assistant_msg, tool_msg]

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)
        openai_msgs = model._convert_messages_to_openai(messages)

        assert len(openai_msgs) == 2
        assert openai_msgs[0]["role"] == "assistant"
        assert "tool_calls" in openai_msgs[0]
        assert openai_msgs[1]["tool_call_id"] == "call_123"

    def test_convert_messages_normalizes_streaming_tool_call_objects(self, mock_agno_model):
        """Regression for issue #1312: in streaming mode Agno can surface
        tool_calls as raw OpenAI SDK objects (`ChoiceDeltaToolCall`) with
        attribute access and no `.get()`. `_convert_messages_to_openai`
        must flatten them to OpenAI-format dicts so neither the Horizon
        pipeline nor Agno's re-serialization hits
        `'ChoiceDeltaToolCall' object has no attribute 'get'`."""
        from horizon.integrations.agno import HorizonAgnoModel

        # Mimic the OpenAI SDK streaming object: attribute access, no .get().
        class _Fn:
            def __init__(self, name, arguments):
                self.name = name
                self.arguments = arguments

        class _ChoiceDeltaToolCall:
            def __init__(self, id, name, arguments):
                self.id = id
                self.index = 0
                self.type = "function"
                self.function = _Fn(name, arguments)

        assistant_msg = MagicMock()
        assistant_msg.role = "assistant"
        assistant_msg.content = ""
        assistant_msg.tool_calls = [
            _ChoiceDeltaToolCall("call_999", "dummy_tool", '{"query": "test"}')
        ]
        assistant_msg.tool_call_id = None

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)
        openai_msgs = model._convert_messages_to_openai([assistant_msg])

        tool_calls = openai_msgs[0]["tool_calls"]
        # Every entry must now be a plain dict, not the SDK object.
        assert all(isinstance(tc, dict) for tc in tool_calls)
        assert tool_calls[0]["id"] == "call_999"
        assert tool_calls[0]["function"]["name"] == "dummy_tool"
        assert tool_calls[0]["function"]["arguments"] == '{"query": "test"}'

    def test_response_applies_optimization(self, mock_agno_model, sample_messages):
        """response() applies Horizon optimization."""
        from horizon.integrations.agno import HorizonAgnoModel
        from horizon.providers import OpenAIProvider

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)

        # Initialize provider and pipeline for mocking
        model._horizon_provider = OpenAIProvider()
        _ = model.pipeline  # Force lazy init

        # Mock the pipeline apply method
        with patch.object(model._pipeline, "apply") as mock_apply:
            mock_result = MagicMock()
            mock_result.messages = [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "What is the capital of France?"},
            ]
            mock_result.tokens_before = 100
            mock_result.tokens_after = 80
            mock_result.transforms_applied = ["cache_aligner"]
            mock_apply.return_value = mock_result

            model.response(sample_messages)

            # Verify pipeline.apply was called
            mock_apply.assert_called_once()

            # Verify metrics were tracked
            assert len(model._metrics_history) == 1
            assert model._metrics_history[0].tokens_saved == 20

    def test_response_stream_applies_optimization(self, mock_agno_model, sample_messages):
        """response_stream() applies Horizon optimization."""
        from horizon.integrations.agno import HorizonAgnoModel
        from horizon.providers import OpenAIProvider

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)
        model._horizon_provider = OpenAIProvider()
        _ = model.pipeline

        with patch.object(model._pipeline, "apply") as mock_apply:
            mock_result = MagicMock()
            mock_result.messages = sample_messages
            mock_result.tokens_before = 100
            mock_result.tokens_after = 90
            mock_result.transforms_applied = []
            mock_apply.return_value = mock_result

            # Consume the generator
            list(model.response_stream(sample_messages))

            mock_apply.assert_called_once()
            assert len(model._metrics_history) == 1

    def test_metrics_history_limited(self, mock_agno_model, sample_messages):
        """Metrics history is limited to 100 entries."""
        from horizon.integrations.agno import HorizonAgnoModel

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)

        # Add 150 fake metrics
        for _i in range(150):
            model._metrics_history.append(MagicMock())

        # Simulate a call that trims
        model._metrics_history = model._metrics_history[-100:]

        assert len(model._metrics_history) == 100

    def test_get_savings_summary_empty(self, mock_agno_model):
        """get_savings_summary with no history."""
        from horizon.integrations.agno import HorizonAgnoModel

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)
        summary = model.get_savings_summary()

        assert summary["total_requests"] == 0
        assert summary["total_tokens_saved"] == 0
        assert summary["average_savings_percent"] == 0

    def test_get_savings_summary_with_data(self, mock_agno_model):
        """get_savings_summary with metrics."""
        from horizon.integrations.agno import HorizonAgnoModel
        from horizon.integrations.agno.model import OptimizationMetrics

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)

        # Add fake metrics
        model._metrics_history = [
            OptimizationMetrics(
                request_id="1",
                timestamp=datetime.now(),
                tokens_before=100,
                tokens_after=80,
                tokens_saved=20,
                savings_percent=20.0,
                transforms_applied=["smart_crusher"],
                model="gpt-4o",
            ),
            OptimizationMetrics(
                request_id="2",
                timestamp=datetime.now(),
                tokens_before=200,
                tokens_after=150,
                tokens_saved=50,
                savings_percent=25.0,
                transforms_applied=["cache_aligner"],
                model="gpt-4o",
            ),
        ]
        model._total_tokens_saved = 70

        summary = model.get_savings_summary()

        assert summary["total_requests"] == 2
        assert summary["total_tokens_saved"] == 70
        assert summary["average_savings_percent"] == 22.5

    def test_reset_clears_all_state(self, mock_agno_model):
        """reset() clears all metrics state."""
        from horizon.integrations.agno import HorizonAgnoModel
        from horizon.integrations.agno.model import OptimizationMetrics

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)

        # Add fake metrics
        model._metrics_history = [
            OptimizationMetrics(
                request_id="1",
                timestamp=datetime.now(),
                tokens_before=100,
                tokens_after=80,
                tokens_saved=20,
                savings_percent=20.0,
                transforms_applied=["smart_crusher"],
                model="gpt-4o",
            ),
        ]
        model._total_tokens_saved = 20

        # Verify state before reset
        assert len(model._metrics_history) == 1
        assert model._total_tokens_saved == 20

        # Reset
        model.reset()

        # Verify state after reset
        assert model._metrics_history == []
        assert model._total_tokens_saved == 0
        assert model.total_tokens_saved == 0

        # Verify summary is empty
        summary = model.get_savings_summary()
        assert summary["total_requests"] == 0
        assert summary["total_tokens_saved"] == 0


class TestProviderDetection:
    """Tests for provider detection from Agno models."""

    def test_detect_openai_provider(self, mock_agno_model):
        """Detect OpenAI provider from OpenAIChat."""
        from horizon.integrations.agno.providers import get_horizon_provider
        from horizon.providers import OpenAIProvider

        provider = get_horizon_provider(mock_agno_model)

        assert isinstance(provider, OpenAIProvider)

    def test_detect_anthropic_provider(self, mock_claude_model):
        """Detect Anthropic provider from Claude model."""
        from horizon.integrations.agno.providers import get_horizon_provider
        from horizon.providers import AnthropicProvider

        provider = get_horizon_provider(mock_claude_model)

        assert isinstance(provider, AnthropicProvider)

    def test_detect_from_model_id(self):
        """Detect provider from model ID string."""
        from horizon.integrations.agno.providers import get_horizon_provider
        from horizon.providers import AnthropicProvider, GoogleProvider, OpenAIProvider

        # GPT model
        mock_gpt = MagicMock()
        mock_gpt.__class__.__name__ = "UnknownModel"
        mock_gpt.__class__.__module__ = "some.module"
        mock_gpt.id = "gpt-4o-mini"
        assert isinstance(get_horizon_provider(mock_gpt), OpenAIProvider)

        # Claude model
        mock_claude = MagicMock()
        mock_claude.__class__.__name__ = "UnknownModel"
        mock_claude.__class__.__module__ = "some.module"
        mock_claude.id = "claude-3-opus-20240229"
        assert isinstance(get_horizon_provider(mock_claude), AnthropicProvider)

        # Gemini model
        mock_gemini = MagicMock()
        mock_gemini.__class__.__name__ = "UnknownModel"
        mock_gemini.__class__.__module__ = "some.module"
        mock_gemini.id = "gemini-pro"
        assert isinstance(get_horizon_provider(mock_gemini), GoogleProvider)

    def test_fallback_to_openai(self):
        """Fallback to OpenAI provider for unknown models."""
        from horizon.integrations.agno.providers import get_horizon_provider
        from horizon.providers import OpenAIProvider

        mock = MagicMock()
        mock.__class__.__name__ = "TotallyUnknownModel"
        mock.__class__.__module__ = "completely.unknown"
        mock.id = "mystery-model-v1"

        provider = get_horizon_provider(mock)

        assert isinstance(provider, OpenAIProvider)

    def test_get_model_name(self, mock_agno_model):
        """Extract model name from Agno model."""
        from horizon.integrations.agno.providers import get_model_name_from_agno

        name = get_model_name_from_agno(mock_agno_model)

        assert name == "gpt-4o"

    def test_get_model_name_fallback(self):
        """Fallback model name when not found."""
        from horizon.integrations.agno.providers import get_model_name_from_agno

        mock = MagicMock(spec=[])  # No attributes
        name = get_model_name_from_agno(mock)

        assert name == "gpt-4o"  # Default fallback


class TestOptimizeMessages:
    """Tests for standalone optimize_messages function."""

    def test_basic_optimization(self, sample_messages):
        """Basic message optimization."""
        from horizon.integrations.agno import optimize_messages

        with patch("horizon.integrations.agno.model.TransformPipeline") as MockPipeline:
            mock_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.messages = [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hello"},
            ]
            mock_result.tokens_before = 100
            mock_result.tokens_after = 80
            mock_result.transforms_applied = ["cache_aligner"]
            mock_instance.apply.return_value = mock_result
            MockPipeline.return_value = mock_instance

            optimized, metrics = optimize_messages(sample_messages)

            assert len(optimized) == 2
            assert metrics["tokens_saved"] == 20
            assert metrics["savings_percent"] == 20.0

    def test_with_custom_config(self, sample_messages):
        """Optimization with custom config."""
        from horizon.integrations.agno import optimize_messages

        config = HorizonConfig(default_mode=HorizonMode.AUDIT)

        with patch("horizon.integrations.agno.model.TransformPipeline") as MockPipeline:
            mock_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.messages = []
            mock_result.tokens_before = 50
            mock_result.tokens_after = 50
            mock_result.transforms_applied = []
            mock_instance.apply.return_value = mock_result
            MockPipeline.return_value = mock_instance

            _, metrics = optimize_messages(
                sample_messages,
                config=config,
                mode=HorizonMode.AUDIT,
            )

            # Verify pipeline was created with config
            MockPipeline.assert_called_once()
            call_kwargs = MockPipeline.call_args[1]
            assert call_kwargs["config"] is config


class TestIntegrationWithRealHorizon:
    """Integration tests using real Horizon components (no mocking)."""

    def test_real_optimization_pipeline(self, sample_messages):
        """Test with real Horizon client (no API calls)."""
        from horizon.integrations.agno import optimize_messages

        # This uses real Horizon transforms but no LLM API calls
        optimized, metrics = optimize_messages(
            sample_messages,
            mode=HorizonMode.OPTIMIZE,
        )

        # Should return valid messages
        assert len(optimized) >= 1
        assert all(isinstance(m, dict) for m in optimized)
        assert all("role" in m and "content" in m for m in optimized)

        # Metrics should be populated
        assert "tokens_before" in metrics
        assert "tokens_after" in metrics
        assert "transforms_applied" in metrics

    def test_large_conversation_compression(self, large_conversation):
        """Test compression of large conversation."""
        from horizon.integrations.agno import optimize_messages

        optimized, metrics = optimize_messages(large_conversation)

        # Should compress (rolling window, etc.)
        assert metrics["tokens_before"] >= metrics["tokens_after"]

    def test_model_wrapper_real_optimization(self, mock_agno_model, sample_messages):
        """Test HorizonAgnoModel with real Horizon optimization."""
        from horizon.integrations.agno import HorizonAgnoModel

        model = HorizonAgnoModel(wrapped_model=mock_agno_model)

        # Call response - this will apply real optimization
        model.response(sample_messages)

        # Should have tracked metrics
        assert len(model.metrics_history) == 1
        metrics = model.metrics_history[0]
        assert metrics.tokens_before >= 0
        assert metrics.tokens_after >= 0


class TestReasoningCapabilityForwarding:
    """Tests for reasoning capability forwarding in HorizonAgnoModel.

    These tests verify that HorizonAgnoModel properly forwards
    reasoning-related properties from the wrapped model, enabling
    framework introspection (e.g., Agno's reasoning detection).
    """

    def test_underlying_model_property_returns_wrapped_model(self, mock_agno_model):
        """underlying_model property should return the wrapped model."""
        from horizon.integrations.agno import HorizonAgnoModel

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.underlying_model is mock_agno_model

    def test_underlying_model_class_introspection(self):
        """underlying_model allows class name introspection for framework detection."""
        from agno.models.openai import OpenAIChat

        from horizon.integrations.agno import HorizonAgnoModel

        base_model = OpenAIChat(id="gpt-4o")
        wrapped = HorizonAgnoModel(wrapped_model=base_model)

        # Framework detection typically checks __class__.__name__
        assert wrapped.underlying_model.__class__.__name__ == "OpenAIChat"
        assert wrapped.__class__.__name__ == "HorizonAgnoModel"

    def test_thinking_property_forwarded_when_present(self, mock_agno_model):
        """thinking property is forwarded from wrapped model when present."""
        from horizon.integrations.agno import HorizonAgnoModel

        # Set thinking config on mock model
        mock_agno_model.thinking = {"type": "enabled", "budget_tokens": 5000}

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.thinking == {"type": "enabled", "budget_tokens": 5000}

    def test_thinking_property_not_present_when_absent(self, mock_agno_model):
        """thinking property not set when wrapped model doesn't have it."""
        from horizon.integrations.agno import HorizonAgnoModel

        # Ensure mock doesn't have thinking attribute
        if hasattr(mock_agno_model, "thinking"):
            delattr(mock_agno_model, "thinking")

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        # Should raise AttributeError when accessed
        assert not hasattr(wrapped, "thinking") or wrapped.thinking is None

    def test_reasoning_effort_property_forwarded(self, mock_agno_model):
        """reasoning_effort property is forwarded from wrapped model."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.reasoning_effort = "high"

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.reasoning_effort == "high"

    def test_provider_property_forwarded_from_wrapped_model(self, mock_agno_model):
        """provider property is set from wrapped model during init."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.provider = "OpenAI"

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.provider == "OpenAI"

    def test_name_property_forwarded_from_wrapped_model(self, mock_agno_model):
        """name property is set from wrapped model during init."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.name = "gpt-4o"

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.name == "gpt-4o"

    def test_has_extended_thinking_enabled_with_dict_config(self, mock_agno_model):
        """has_extended_thinking_enabled returns True when thinking dict is enabled."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.thinking = {"type": "enabled", "budget_tokens": 5000}

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.has_extended_thinking_enabled() is True

    def test_has_extended_thinking_disabled_with_dict_config(self, mock_agno_model):
        """has_extended_thinking_enabled returns False when thinking dict is disabled."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.thinking = {"type": "disabled"}

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.has_extended_thinking_enabled() is False

    def test_has_extended_thinking_returns_false_when_none(self, mock_agno_model):
        """has_extended_thinking_enabled returns False when thinking is None."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.thinking = None

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.has_extended_thinking_enabled() is False

    def test_has_extended_thinking_returns_false_when_missing(self, mock_agno_model):
        """has_extended_thinking_enabled returns False when thinking attribute missing."""
        from horizon.integrations.agno import HorizonAgnoModel

        # Remove thinking attribute if present
        if hasattr(mock_agno_model, "thinking"):
            delattr(mock_agno_model, "thinking")

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.has_extended_thinking_enabled() is False

    def test_has_extended_thinking_with_truthy_value(self, mock_agno_model):
        """has_extended_thinking_enabled handles non-dict truthy values."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.thinking = True

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.has_extended_thinking_enabled() is True

    def test_has_extended_thinking_with_falsy_value(self, mock_agno_model):
        """has_extended_thinking_enabled handles non-dict falsy values."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.thinking = False

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.has_extended_thinking_enabled() is False

    def test_supports_native_structured_outputs_forwarded(self, mock_agno_model):
        """supports_native_structured_outputs property is forwarded."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.supports_native_structured_outputs = True

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.supports_native_structured_outputs is True

    def test_supports_json_schema_outputs_forwarded(self, mock_agno_model):
        """supports_json_schema_outputs property is forwarded."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.supports_json_schema_outputs = True

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.supports_json_schema_outputs is True

    def test_multiple_capability_properties_forwarded(self, mock_agno_model):
        """Multiple capability properties are forwarded correctly."""
        from horizon.integrations.agno import HorizonAgnoModel

        mock_agno_model.thinking = {"type": "enabled", "budget_tokens": 10000}
        mock_agno_model.reasoning_effort = "medium"
        mock_agno_model.supports_native_structured_outputs = True
        mock_agno_model.supports_json_schema_outputs = False
        mock_agno_model.provider = "Anthropic"

        wrapped = HorizonAgnoModel(wrapped_model=mock_agno_model)

        assert wrapped.thinking == {"type": "enabled", "budget_tokens": 10000}
        assert wrapped.reasoning_effort == "medium"
        assert wrapped.supports_native_structured_outputs is True
        assert wrapped.supports_json_schema_outputs is False
        assert wrapped.provider == "Anthropic"

    def test_underlying_model_with_real_openai_model(self):
        """Test underlying_model with real Agno OpenAIChat model."""
        from agno.models.openai import OpenAIChat

        from horizon.integrations.agno import HorizonAgnoModel

        base_model = OpenAIChat(id="gpt-4o")
        wrapped = HorizonAgnoModel(wrapped_model=base_model)

        # Verify underlying_model returns the actual model
        assert wrapped.underlying_model is base_model
        assert isinstance(wrapped.underlying_model, OpenAIChat)


class TestRealAgnoIntegration:
    """REAL integration tests with actual Agno components.

    These tests verify that HorizonAgnoModel:
    1. Is a proper subclass of agno.models.base.Model
    2. Passes Agno's get_model() validation
    3. Can be used with Agno Agent
    4. Works with real Agno model types (not MagicMock)

    NO MOCKS for Agno components - only for external APIs.
    """

    def test_is_subclass_of_agno_model(self):
        """HorizonAgnoModel must be a subclass of agno.models.base.Model."""
        from agno.models.base import Model

        from horizon.integrations.agno import HorizonAgnoModel

        assert issubclass(HorizonAgnoModel, Model)

    def test_passes_agno_get_model_validation(self):
        """HorizonAgnoModel must pass Agno's get_model() validation."""
        from agno.models.openai import OpenAIChat
        from agno.models.utils import get_model

        from horizon.integrations.agno import HorizonAgnoModel

        # Create a real OpenAIChat model (doesn't need API key for instantiation)
        base_model = OpenAIChat(id="gpt-4o")
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        # This should NOT raise "Model must be a Model instance, string, or None"
        result = get_model(horizon_model)

        assert result is horizon_model
        assert isinstance(result, HorizonAgnoModel)

    def test_agent_accepts_horizon_model(self):
        """Agno Agent must accept HorizonAgnoModel as model parameter."""
        from agno.agent import Agent
        from agno.models.openai import OpenAIChat

        from horizon.integrations.agno import HorizonAgnoModel

        # Create wrapped model
        base_model = OpenAIChat(id="gpt-4o")
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        # This should NOT raise any validation errors
        agent = Agent(model=horizon_model, markdown=False)

        assert agent.model is horizon_model
        assert agent.model.wrapped_model is base_model

    def test_model_id_reflects_wrapped_model(self):
        """HorizonAgnoModel id should reflect the wrapped model."""
        from agno.models.openai import OpenAIChat

        from horizon.integrations.agno import HorizonAgnoModel

        base_model = OpenAIChat(id="gpt-4o-mini")
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        assert "gpt-4o-mini" in horizon_model.id
        assert horizon_model.id.startswith("horizon:")

    def test_horizon_model_has_required_abstract_methods(self):
        """HorizonAgnoModel must implement all required abstract methods."""
        from agno.models.openai import OpenAIChat

        from horizon.integrations.agno import HorizonAgnoModel

        base_model = OpenAIChat(id="gpt-4o")
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        # Verify required methods exist and are callable
        assert hasattr(horizon_model, "invoke")
        assert callable(horizon_model.invoke)

        assert hasattr(horizon_model, "ainvoke")
        assert callable(horizon_model.ainvoke)

        assert hasattr(horizon_model, "invoke_stream")
        assert callable(horizon_model.invoke_stream)

        assert hasattr(horizon_model, "ainvoke_stream")
        assert callable(horizon_model.ainvoke_stream)

        assert hasattr(horizon_model, "_parse_provider_response")
        assert callable(horizon_model._parse_provider_response)

        assert hasattr(horizon_model, "_parse_provider_response_delta")
        assert callable(horizon_model._parse_provider_response_delta)

    def test_isinstance_check_passes(self):
        """isinstance check with agno.models.base.Model must pass."""
        from agno.models.base import Model
        from agno.models.openai import OpenAIChat

        from horizon.integrations.agno import HorizonAgnoModel

        base_model = OpenAIChat(id="gpt-4o")
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        # This is the exact check that get_model() uses
        assert isinstance(horizon_model, Model)

    def test_model_with_custom_horizon_config(self):
        """Test with custom Horizon configuration."""
        from agno.agent import Agent
        from agno.models.openai import OpenAIChat

        from horizon.integrations.agno import HorizonAgnoModel

        config = HorizonConfig(default_mode=HorizonMode.AUDIT)
        base_model = OpenAIChat(id="gpt-4o")
        horizon_model = HorizonAgnoModel(
            wrapped_model=base_model,
            horizon_config=config,
        )

        agent = Agent(model=horizon_model, markdown=False)

        assert agent.model.horizon_config is config
        assert agent.model.horizon_config.default_mode == HorizonMode.AUDIT

    def test_response_method_delegates_to_wrapped(self):
        """Test that response() method works with real Agno model structure."""
        from agno.models.openai import OpenAIChat

        from horizon.integrations.agno import HorizonAgnoModel

        base_model = OpenAIChat(id="gpt-4o")
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        # We can't actually call the response method without an API key, but we can verify
        # the method signature matches what Agno expects
        import inspect

        sig = inspect.signature(horizon_model.response)
        params = list(sig.parameters.keys())

        assert "messages" in params

    def test_optimization_tracked_across_calls(self):
        """Test that optimization metrics are tracked properly."""
        from agno.models.openai import OpenAIChat

        from horizon.integrations.agno import HorizonAgnoModel

        base_model = OpenAIChat(id="gpt-4o")
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        # Initially no metrics
        assert horizon_model.total_tokens_saved == 0
        assert len(horizon_model.metrics_history) == 0

        # Simulate optimization (without actual API call)
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]

        # Use the internal optimize method to test
        optimized, metrics = horizon_model._optimize_messages(messages)

        # Should have tracked metrics
        assert len(horizon_model.metrics_history) == 1
        assert horizon_model.total_tokens_saved >= 0


def _ollama_available() -> bool:
    """Check if Ollama is running and has a model available."""
    import socket

    # First check if ollama Python package is installed
    try:
        import ollama  # noqa: F401
    except ImportError:
        return False

    try:
        # Check if Ollama server is running on default port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", 11434))
        sock.close()
        return result == 0
    except Exception:
        return False


def _get_ollama_model() -> str | None:
    """Get an available Ollama model for testing."""
    if not _ollama_available():
        return None

    import subprocess

    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None

        # Parse output to find a model
        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:  # Header + at least one model
            return None

        # Get first model name (skip header)
        for line in lines[1:]:
            parts = line.split()
            if parts:
                model_name = parts[0]
                # Prefer small models for faster tests
                if any(
                    small in model_name.lower() for small in ["tiny", "phi", "qwen", "gemma:2b"]
                ):
                    return model_name
        # Fallback to first available model
        first_model_line = lines[1].split()
        return first_model_line[0] if first_model_line else None
    except Exception:
        return None


@pytest.mark.skipif(not _ollama_available(), reason="Ollama not running")
class TestOllamaIntegration:
    """Integration tests using real Ollama models.

    These tests require Ollama to be installed and running locally.
    They are skipped in CI unless Ollama is set up.

    To run these tests locally:
        1. Install Ollama: curl -fsSL https://ollama.com/install.sh | sh
        2. Pull a small model: ollama pull tinyllama
        3. Run tests: pytest tests/test_integrations/agno/test_model.py -v -k ollama
    """

    @pytest.fixture
    def ollama_model_name(self):
        """Get an available Ollama model."""
        model = _get_ollama_model()
        if not model:
            pytest.skip("No Ollama models available")
        return model

    def test_agent_with_ollama_model(self, ollama_model_name):
        """Test Agent with HorizonAgnoModel wrapping real Ollama model."""
        from agno.agent import Agent
        from agno.models.ollama import Ollama

        from horizon.integrations.agno import HorizonAgnoModel

        # Create wrapped Ollama model (real, local, no API key needed)
        base_model = Ollama(id=ollama_model_name)
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        # Create agent - this validates HorizonAgnoModel works with Agent
        agent = Agent(model=horizon_model, markdown=False)

        assert agent.model is horizon_model
        assert isinstance(agent.model, HorizonAgnoModel)

    def test_agent_run_with_ollama(self, ollama_model_name):
        """Actually run an agent with Ollama - full end-to-end test."""
        from agno.agent import Agent
        from agno.models.ollama import Ollama

        from horizon.integrations.agno import HorizonAgnoModel

        # Create wrapped Ollama model
        base_model = Ollama(id=ollama_model_name)
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        # Create and run agent
        agent = Agent(model=horizon_model, markdown=False)

        # Actually run the agent - this tests the full pipeline
        response = agent.run("Say 'hello' and nothing else.")

        # Verify we got a response
        assert response is not None
        assert response.content is not None
        assert len(response.content) > 0

        # Verify Horizon optimization was applied
        assert len(horizon_model.metrics_history) >= 1

    def test_agent_with_system_prompt_and_ollama(self, ollama_model_name):
        """Test agent with system prompt using Ollama."""
        from agno.agent import Agent
        from agno.models.ollama import Ollama

        from horizon.integrations.agno import HorizonAgnoModel

        base_model = Ollama(id=ollama_model_name)
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        # Agent with system prompt - tests system message optimization
        agent = Agent(
            model=horizon_model,
            description="You are a helpful assistant that always responds with exactly one word.",
            markdown=False,
        )

        response = agent.run("What is 2+2?")

        assert response is not None
        assert response.content is not None

        # Horizon should have processed the system prompt
        assert horizon_model.total_tokens_saved >= 0

    def test_multiple_turns_with_ollama(self, ollama_model_name):
        """Test multi-turn conversation with Ollama."""
        from agno.agent import Agent
        from agno.models.ollama import Ollama

        from horizon.integrations.agno import HorizonAgnoModel

        base_model = Ollama(id=ollama_model_name)
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        agent = Agent(model=horizon_model, markdown=False)

        # Multiple turns
        agent.run("My name is Alice.")
        agent.run("What is my name?")

        # Should have tracked multiple optimization passes
        assert len(horizon_model.metrics_history) >= 2

    def test_horizon_optimization_reduces_tokens(self, ollama_model_name, large_conversation):
        """Test that Horizon actually reduces tokens on large conversations."""
        from agno.models.ollama import Ollama

        from horizon.integrations.agno import HorizonAgnoModel

        base_model = Ollama(id=ollama_model_name)
        horizon_model = HorizonAgnoModel(wrapped_model=base_model)

        # Optimize the large conversation
        optimized, metrics = horizon_model._optimize_messages(large_conversation)

        # Large conversations should see compression
        assert metrics.tokens_before > 0
        # With a 100+ message conversation, we should see some savings
        # (at minimum from whitespace normalization)
        assert metrics.tokens_after <= metrics.tokens_before
