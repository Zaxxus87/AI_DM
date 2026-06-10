# MCP Servers — Mechanics (`dice-mechanics`)

The stateless `dice-mechanics` MCP server: deterministic, side-effect-free dice
resolution for D&D 2024 (5.5e), served over MCP **Streamable HTTP** with FastMCP
(`stateless_http=True, json_response=True`). The orchestrator (and any MCP client) calls
these tools so dice results are exact and auditable rather than invented by the model.

## Tools (see `contracts/CONTRACT.md`)

| Tool | Signature | Returns |
|------|-----------|---------|
| `roll` | `roll(notation)` — e.g. `"2d6+3"`, `"d20"`, `"1d8-1"` | individual `rolls`, `modifier`, `total` |
| `roll_check` | `roll_check(modifier, dc, advantage="none")` | `d20`, `total`, `dc`, `success` |
| `roll_attack` | `roll_attack(bonus, target_ac, advantage="none")` | `d20`, `total`, `hit`, `critical_hit`, `critical_miss` |

- `advantage` is a string enum: `"none"` \| `"advantage"` \| `"disadvantage"` (rolls two
  d20s, keeping the higher / lower).
- Attack rules (2024): natural 20 auto-hits and crits; natural 1 auto-misses.
- Pure logic lives in `dice.py` (no MCP imports, unit-testable); `server.py` is the thin
  FastMCP wrapper.

## Run

Run each line separately (PowerShell 5.1 does not support `&&`):

```powershell
cd mcp-servers/mechanics
uv sync                  # first time only
uv run python server.py  # serves the URL in DICE_MCP_URL (default http://localhost:8080/mcp)
```

The server reads the repo-root `.env` and binds the port from `DICE_MCP_URL`, so the
server and the orchestrator client stay in sync from one source of truth.

## Quick sanity check (pure logic, no server)

```powershell
uv run python -c "import dice; print(dice.roll('2d6+3')); print(dice.roll_attack(6, 14))"
```
