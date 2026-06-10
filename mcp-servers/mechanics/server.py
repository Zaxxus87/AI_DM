"""dice-mechanics MCP server.

Exposes the deterministic dice tools from ``dice.py`` over MCP Streamable HTTP using
FastMCP. Stateless and side-effect-free: every tool is a pure roll resolver. The model
(via the orchestrator) calls these so dice results are exact and auditable rather than
invented in the model's head — the core "determinism where it matters" rule.

Run:  uv run python server.py   (serves http://localhost:<port>/mcp)
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

import dice

# Load the repo-root .env so the server's port stays in sync with DICE_MCP_URL,
# the single source the orchestrator client also reads.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


def _port_from_env(default: int = 8080) -> int:
    url = os.getenv("DICE_MCP_URL")
    if not url:
        return default
    parsed = urlparse(url)
    return parsed.port or default


# stateless_http + json_response keep each tool call a self-contained request/response,
# which is what scales cleanly on Cloud Run later (no long-lived per-client session state).
mcp = FastMCP(
    "dice-mechanics",
    stateless_http=True,
    json_response=True,
    host="127.0.0.1",
    port=_port_from_env(),
)


@mcp.tool()
def roll(notation: str) -> dict:
    """Roll standard dice notation such as "2d6+3", "d20", or "1d8-1".

    Returns the individual dice rolled, the flat modifier, and the total.
    """
    return dice.roll(notation)


@mcp.tool()
def roll_check(modifier: int, dc: int, advantage: str = "none") -> dict:
    """Resolve a D&D 2024 ability or skill check against a difficulty class (DC).

    advantage: "none", "advantage", or "disadvantage".
    Returns the d20 result, total (d20 + modifier), the DC, and whether it succeeded.
    """
    return dice.roll_check(modifier=modifier, dc=dc, advantage=advantage)


@mcp.tool()
def roll_attack(bonus: int, target_ac: int, advantage: str = "none") -> dict:
    """Resolve a D&D 2024 attack roll against a target's Armor Class (AC).

    advantage: "none", "advantage", or "disadvantage".
    Natural 20 always hits and is a critical hit; natural 1 always misses. Returns the
    d20, total, target AC, and hit / critical_hit / critical_miss flags.
    """
    return dice.roll_attack(bonus=bonus, target_ac=target_ac, advantage=advantage)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
