# Orchestrator LLM Adapter

The model-agnostic LLM layer. The agent loop talks only to the `LLMClient` interface and
the neutral dataclasses here, never to a vendor SDK — so a `ClaudeClient` (Claude on
Vertex) can later drop in for A/B comparison without touching the loop.

- `base.py` — `LLMClient` Protocol plus the neutral `LLMResult` / `ToolCall` / `ToolSpec`
  types and the neutral message schema shared by the loop and every implementation.
- `gemini_client.py` — `GeminiClient`, the first implementation: wraps the google-genai
  SDK against Vertex, translates `ToolSpec`s into Gemini function declarations
  (sanitizing the JSON Schema to the subset the declaration API accepts), and normalizes
  responses back into `LLMResult`. It captures and re-attaches each call's Gemini 3
  `thought_signature` across turns (required, or Vertex rejects the echoed history).

## Endpoint split (do not "simplify")

`GeminiClient` constructs **two** Vertex clients on purpose:

- **`location="global"`** for the **Pro** model — `gemini-3.1-pro-preview` serves *only*
  on the global endpoint; a regional Pro client 404s.
- **`location=VERTEX_REGION`** (e.g. `us-central1`) kept for the models/services that
  need a region later — Flash, text embeddings, Firestore, Cloud Storage.

Model IDs come from `.env` (`GEMINI_PRO_MODEL`, `GEMINI_FLASH_MODEL`). The slice defaults
every turn to Pro; per-turn Pro/Flash tiering is a future change behind this same
interface.
