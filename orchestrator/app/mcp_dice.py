"""MCP client for the dice-mechanics server.

The orchestrator holds the MCP client session itself (Streamable HTTP) and dispatches
tool calls explicitly — the translate-and-dispatch path the production loop will use.
This module is the thin seam between an open ``ClientSession`` and the neutral ToolSpec
/ result-dict shapes the agent loop works in.
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from llm import ToolSpec


@asynccontextmanager
async def dice_session(url: str):
    """Open an initialized MCP ClientSession against the dice server at ``url``."""
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def list_tool_specs(session: ClientSession) -> list[ToolSpec]:
    """Discover the server's tools and map them to vendor-neutral ToolSpecs."""
    listed = await session.list_tools()
    return [
        ToolSpec(
            name=tool.name,
            description=tool.description or "",
            parameters=tool.inputSchema or {"type": "object", "properties": {}},
        )
        for tool in listed.tools
    ]


async def call_tool(session: ClientSession, name: str, args: dict[str, Any]) -> dict:
    """Dispatch one tool call and return its result as a plain dict.

    Prefers ``structuredContent`` (the JSON the tool returned); falls back to parsing
    the text content block if a server doesn't provide structured output.
    """
    result = await session.call_tool(name, args)

    if result.structuredContent is not None:
        return result.structuredContent

    for block in result.content:
        text = getattr(block, "text", None)
        if text is None:
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"result": text}

    return {"result": None}
