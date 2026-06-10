"""Minimal terminal agent loop — the vertical-slice proof.

Read a line of player input, run the loop (system prompt -> Gemini -> dispatch any tool
calls to the dice MCP server -> feed results back -> repeat until final narration), and
print it. Every tool call is logged so the seam is visibly working. No persistence and
no game state: just the dice tools and Gemini.

Run (with the dice server already up in another terminal):
    uv run python -m app.cli
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

from app.mcp_dice import call_tool, dice_session, list_tool_specs
from llm import GeminiClient, ToolCall

# Cap the tool<->model round-trips per player turn so a misbehaving model can't loop
# forever. A normal turn resolves in 1-2 iterations.
MAX_ITERATIONS = 6

SYSTEM_PROMPT = (
    "You are the Dungeon Master for a solo game of Dungeons & Dragons 2024 (5.5e), "
    "where one player controls the whole party and you voice the world and its NPCs.\n\n"
    "HARD RULE: you never invent dice results, hit/miss outcomes, totals, or DCs in your "
    "head. Every die roll, ability check, and attack MUST be resolved by calling the "
    "provided tools, and your narration MUST use the exact numbers the tools return. If "
    "an action needs a roll, call the tool first, then narrate the result.\n\n"
    "Keep narration terse and concrete — a sentence or two. State the mechanical outcome "
    "(the roll, the total, hit or miss) alongside the fiction."
)


def _fmt_args(args: dict) -> str:
    return ", ".join(f"{k}={v!r}" for k, v in args.items())


async def run_turn(client: GeminiClient, session, tool_specs, messages: list) -> None:
    """Drive one player turn to a final narration, logging every tool call."""
    for _ in range(MAX_ITERATIONS):
        # GeminiClient.generate is a blocking SDK call; run it off the event loop so the
        # MCP transport stays responsive.
        result = await asyncio.to_thread(
            client.generate, SYSTEM_PROMPT, messages, tool_specs
        )

        if not result.tool_calls:
            text = result.text or "(no narration returned)"
            print(f"\nDM: {text}\n")
            messages.append({"role": "model", "text": text})
            return

        messages.append({"role": "model", "tool_calls": result.tool_calls})

        responses = []
        for tc in result.tool_calls:
            print(f"  -> tool {tc.name}({_fmt_args(tc.args)})")
            tool_result = await call_tool(session, tc.name, tc.args)
            print(f"  <- {tool_result}")
            responses.append({"name": tc.name, "result": tool_result})

        messages.append({"role": "tool", "responses": responses})

    print(
        f"\n[stopped: hit the {MAX_ITERATIONS}-iteration cap without a final narration]\n"
    )


async def main() -> None:
    # Gemini narration routinely contains non-ASCII (em-dashes, smart quotes); force
    # UTF-8 so printing it doesn't crash on a legacy Windows console codepage.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    # Load the repo-root .env (GCP_PROJECT, GEMINI_PRO_MODEL, DICE_MCP_URL, ...).
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

    dice_url = os.getenv("DICE_MCP_URL", "http://localhost:8080/mcp")
    print(f"Connecting to dice-mechanics MCP server at {dice_url} ...")

    async with dice_session(dice_url) as session:
        tool_specs = await list_tool_specs(session)
        print("Connected. Tools available: " + ", ".join(s.name for s in tool_specs))

        client = GeminiClient()
        print(
            "DM ready (Gemini via Vertex). Describe an action; rolls resolve through the "
            "dice tools. Ctrl-C or empty line + Enter to quit.\n"
        )

        messages: list = []
        while True:
            try:
                line = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                return
            if not line:
                print("Goodbye.")
                return

            messages.append({"role": "user", "text": line})
            try:
                await run_turn(client, session, tool_specs, messages)
            except Exception as exc:  # keep the REPL alive on a bad turn
                print(f"\n[turn failed: {type(exc).__name__}: {exc}]\n")


if __name__ == "__main__":
    asyncio.run(main())
