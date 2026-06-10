"""GeminiClient — the first LLMClient implementation (Gemini on Vertex AI).

Wraps the google-genai SDK against Vertex, translates neutral ToolSpecs into Gemini
function declarations, and normalizes the response back into the neutral LLMResult. The
explicit translate-and-dispatch design (rather than the SDK's experimental MCP
auto-calling) is deliberate: it's version-proof and it's exactly what the production
orchestrator loop will use.
"""

from __future__ import annotations

import os
from typing import Any

from google import genai
from google.genai import types

from .base import LLMClient, LLMResult, Message, ToolCall, ToolSpec

# JSON Schema keys that Gemini's FunctionDeclaration schema accepts. MCP/pydantic emit
# extras like "title", "$schema", "additionalProperties", "$defs" that the declaration
# validator rejects, so we keep only this whitelist and recurse into nested objects.
_SCHEMA_OBJECT_KEYS = ("type", "properties", "required", "enum", "items", "description")
_SCHEMA_LEAF_KEYS = ("type", "description", "enum", "format", "items")


def _sanitize_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Strip JSON Schema down to the subset Gemini function declarations accept."""
    if not isinstance(schema, dict):
        return {}

    out: dict[str, Any] = {}
    for key in _SCHEMA_OBJECT_KEYS:
        if key not in schema:
            continue
        if key == "properties":
            out["properties"] = {
                prop: _sanitize_property(spec) for prop, spec in schema["properties"].items()
            }
        elif key == "items":
            out["items"] = _sanitize_schema(schema["items"])
        else:
            out[key] = schema[key]
    # Gemini wants an object schema even when a tool takes no parameters.
    out.setdefault("type", "object")
    return out


def _sanitize_property(spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict):
        return {}
    out = {k: spec[k] for k in _SCHEMA_LEAF_KEYS if k in spec}
    if spec.get("type") == "object" and "properties" in spec:
        return _sanitize_schema(spec)
    if "items" in spec:
        out["items"] = _sanitize_schema(spec["items"])
    return out


class GeminiClient(LLMClient):
    def __init__(self) -> None:
        project = os.environ["GCP_PROJECT"]
        region = os.getenv("VERTEX_REGION", "us-central1")

        # IMPORTANT — endpoint split, do NOT "simplify" this into one regional client:
        # gemini-3.1-pro-preview serves ONLY on the GLOBAL endpoint, so the Pro client
        # MUST use location="global" or every call 404s. A separate regional client
        # (VERTEX_REGION, e.g. us-central1) is kept for the models/services that need a
        # region later — Flash, text embeddings, Firestore, Cloud Storage. The slice
        # itself only uses the Pro client; the regional one is wired now so the split is
        # explicit and survives future edits.
        self._pro = genai.Client(vertexai=True, project=project, location="global")
        self._regional = genai.Client(vertexai=True, project=project, location=region)

        self._pro_model = os.environ["GEMINI_PRO_MODEL"]
        self._flash_model = os.getenv("GEMINI_FLASH_MODEL", "")

    def generate(
        self,
        system: str,
        messages: list[Message],
        tools: list[ToolSpec],
    ) -> LLMResult:
        gemini_tools = self._to_gemini_tools(tools)
        contents = self._to_contents(messages)

        # Slice defaults to Pro for every turn (hard DM reasoning). Per-turn Pro/Flash
        # tiering is a future optimization that lives behind this same interface.
        response = self._pro.models.generate_content(
            model=self._pro_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                tools=gemini_tools,
            ),
        )

        # Iterate the candidate parts (not response.function_calls) so we can capture
        # each call's thought_signature, which lives on the Part and MUST be echoed back
        # on the next turn or Gemini 3 rejects the request with 400 INVALID_ARGUMENT.
        tool_calls: list[ToolCall] = []
        text_chunks: list[str] = []
        candidates = response.candidates or []
        parts = candidates[0].content.parts if candidates and candidates[0].content else []
        for part in parts or []:
            if part.function_call is not None:
                fc = part.function_call
                tool_calls.append(
                    ToolCall(
                        name=fc.name,
                        args=dict(fc.args or {}),
                        signature=part.thought_signature,
                    )
                )
            elif part.text:
                text_chunks.append(part.text)

        text = None if tool_calls else ("".join(text_chunks) or None)
        return LLMResult(text=text, tool_calls=tool_calls)

    # --- translation helpers -----------------------------------------------------

    @staticmethod
    def _to_gemini_tools(tools: list[ToolSpec]) -> list[types.Tool]:
        if not tools:
            return []
        declarations = [
            types.FunctionDeclaration(
                name=spec.name,
                description=spec.description,
                parameters=_sanitize_schema(spec.parameters),
            )
            for spec in tools
        ]
        return [types.Tool(function_declarations=declarations)]

    @staticmethod
    def _to_contents(messages: list[Message]) -> list[types.Content]:
        contents: list[types.Content] = []
        for msg in messages:
            role = msg["role"]
            if role == "user":
                contents.append(
                    types.Content(role="user", parts=[types.Part(text=msg["text"])])
                )
            elif role == "model" and "tool_calls" in msg:
                # Re-attach each call's thought_signature so Gemini 3 accepts the echoed
                # history (see generate()).
                parts = [
                    types.Part(
                        function_call=types.FunctionCall(name=tc.name, args=tc.args),
                        thought_signature=tc.signature,
                    )
                    for tc in msg["tool_calls"]
                ]
                contents.append(types.Content(role="model", parts=parts))
            elif role == "model":
                contents.append(
                    types.Content(role="model", parts=[types.Part(text=msg["text"])])
                )
            elif role == "tool":
                parts = [
                    types.Part.from_function_response(
                        name=r["name"], response=r["result"]
                    )
                    for r in msg["responses"]
                ]
                contents.append(types.Content(role="tool", parts=parts))
            else:  # pragma: no cover - defensive
                raise ValueError(f"unknown message shape: {msg!r}")
        return contents
