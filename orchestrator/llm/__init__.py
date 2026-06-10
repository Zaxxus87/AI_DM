"""LLM adapter layer: the model-agnostic LLMClient interface and its implementations."""

from .base import LLMClient, LLMResult, Message, ToolCall, ToolSpec
from .gemini_client import GeminiClient

__all__ = [
    "LLMClient",
    "LLMResult",
    "Message",
    "ToolCall",
    "ToolSpec",
    "GeminiClient",
]
