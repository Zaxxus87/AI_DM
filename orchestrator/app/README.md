# Orchestrator App — vertical-slice CLI

A minimal terminal agent loop that proves the project's core seam: **Gemini (on Vertex
AI) calls an MCP dice tool through the `LLMClient` loop and narrates using the
deterministic result** — no value invented by the model.

- `mcp_dice.py` — MCP client (Streamable HTTP) to the `dice-mechanics` server: opens a
  session, lists tools as neutral `ToolSpec`s, dispatches calls.
- `cli.py` — the REPL loop: player input → system prompt (terse D&D 2024 DM that resolves
  all dice through tools) → `GeminiClient.generate` → dispatch any tool calls → loop to
  final narration. Every tool call (name, args, result) is logged; iterations are capped.

No persistence and no game state — just the dice tools and Gemini.

## Prerequisites

1. **Vertex auth (ADC):** `gcloud auth application-default login` (and a project with
   Gemini Pro preview access). The CLI reads `GCP_PROJECT`, `GEMINI_PRO_MODEL`, and
   `DICE_MCP_URL` from the repo-root `.env`.
2. Dependencies installed: `cd orchestrator; uv sync`.

## Run (two terminals)

Run each line separately (PowerShell 5.1 does not support `&&`):

**Terminal 1 — the dice server:**
```powershell
cd mcp-servers/mechanics
uv run python server.py        # http://localhost:8080/mcp
```

**Terminal 2 — the CLI:**
```powershell
cd orchestrator
uv run python -m app.cli
```

On startup the CLI prints the discovered tool names. Then try, e.g.:

```
you> the fighter swings at the goblin, +6 to hit, its AC is 14
  -> tool roll_attack(bonus=6, target_ac=14, advantage='none')
  <- {'d20': 5, 'total': 11, 'target_ac': 14, 'hit': False, ...}
DM: The fighter rolls a 5 (total 11) against AC 14 — the blade glances off. Miss.
```

Both processes load the same repo-root `.env`. An empty line or Ctrl-C quits.
