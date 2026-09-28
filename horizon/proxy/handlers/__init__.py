"""Handler mixins for HorizonProxy.

Each mixin class contains methods extracted from HorizonProxy that handle
requests for a specific provider or concern. The mixins rely on HorizonProxy's
__init__ for all self.* attributes (duck typing).
"""

from horizon.proxy.handlers.anthropic import AnthropicHandlerMixin
from horizon.proxy.handlers.batch import BatchHandlerMixin
from horizon.proxy.handlers.bedrock import BedrockHandlerMixin
from horizon.proxy.handlers.gemini import GeminiHandlerMixin
from horizon.proxy.handlers.openai import OpenAIHandlerMixin
from horizon.proxy.handlers.streaming import StreamingMixin

__all__ = [
    "AnthropicHandlerMixin",
    "BatchHandlerMixin",
    "BedrockHandlerMixin",
    "GeminiHandlerMixin",
    "OpenAIHandlerMixin",
    "StreamingMixin",
]
