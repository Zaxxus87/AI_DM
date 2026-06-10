"""The model-agnostic LLM adapter interface.

The agent loop talks only to ``LLMClient`` and these neutral dataclasses — never to a
specific vendor SDK. ``GeminiClient`` is the first implementation; a ``ClaudeClient``
(Claude on Vertex) can later drop in behind the same interface for A/B comparison
without touching the loop. This is the "one tool layer, many consumers / model-agnostic
orchestrator" principle from the blueprint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ToolSpec:
    """A vendor-neutral description of a callable tool.

    ``parameters`` is a JSON Schema object (taken straight from an MCP tool's
    ``inputSchema``). Each LLMClient is responsible for translating this into whatever
    its model's function-calling API expects.
    """

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class ToolCall:
    """A tool invocation the model asked us to perform.

    ``signature`` is opaque, provider-private continuation state that some models attach
    to a tool call and require echoed back verbatim on the next turn (Gemini 3's
    ``thought_signature`` is one such token). The loop treats it as a black box; only the
    issuing LLMClient interprets it.
    """

    name: str
    args: dict[str, Any]
    signature: Any = None


@dataclass
class LLMResult:
    """One model turn: final narration text and/or tool calls to dispatch.

    If ``tool_calls`` is non-empty the loop dispatches them and calls ``generate`` again
    with the results appended. When ``tool_calls`` is empty, ``text`` is the final
    narration and the turn ends.
    """

    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


# --- Neutral message schema shared by the loop and every LLMClient ---------------
#
# A conversation is a list[dict], each one of:
#   {"role": "user",  "text": str}                         player input
#   {"role": "model", "text": str}                         model narration
#   {"role": "model", "tool_calls": [ToolCall, ...]}       model requested tools
#   {"role": "tool",  "responses": [{"name": str, "result": dict}, ...]}  tool results
#
# Keeping the history in this neutral shape means no vendor SDK types leak into the
# agent loop; each LLMClient translates it to/from its own representation per call.

Message = dict[str, Any]


class LLMClient(Protocol):
    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSpec],
    ) -> LLMResult:
        """Run one model turn and return its narration text and/or tool calls."""
        ...
