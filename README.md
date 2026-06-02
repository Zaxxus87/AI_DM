# Agentic Dungeon Master

A solo-player D&D 2024 (5.5e) application where one human runs the whole party and a Gemini-powered DM narrates, runs combat, and tracks game state. This repository contains the foundations for the final architecture: a React frontend, a FastAPI orchestrator, MCP servers for deterministic game mechanics, and shared contracts that every layer implements.

## Planned build order

1. **Foundations** — repository skeleton, project conventions, shared contract, and infrastructure placeholders.
2. **Vertical slice** — a minimal orchestrator loop and one MCP tool path to prove the model-to-tools flow.
3. **Frontend against mock** — UI built against a mocked `DMClient` / SSE interface before the backend exists.
4. **Backend breadth** — implement MCP servers for dice, encounter, game state, memory, rules, and lore.
5. **Integration** — wire the real orchestrator to Gemini, MCP servers, and the browser client.
6. **CI/CD** — add GitHub workflows, GCP deployment automation, and runtime configuration.

## How this repo is organized

- `orchestrator/` — orchestrator service code and the LLM adapter layer.
- `mcp-servers/` — tool servers for mechanics, game state, and rules lookup.
- `ingestion/` — reference ingestion and embedding pipeline placeholders.
- `web/` — frontend application placeholder for the Vite + React + TypeScript UI.
- `infra/` — infrastructure and deployment manifests.
- `contracts/` — the single source of truth for shared domain types and API contracts.

## Running later

When implementation begins, the intended workflow is:

- `cd web` and run the frontend with Vite.
- `cd orchestrator` and run the FastAPI backend with Uvicorn.
- `cd mcp-servers/*` to run individual MCP tool servers.
- Use `.env.example` as the starting point for environment configuration.

> `contracts/` is the authoritative contract layer. The frontend imports domain types from `contracts/types.ts`, and the backend mirrors them with Pydantic models.
