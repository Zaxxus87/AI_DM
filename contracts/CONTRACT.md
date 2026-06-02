# Project Contract

This document defines the shared contract for the Agentic Dungeon Master. `contracts/types.ts` is the canonical TypeScript source of truth, and the backend will mirror these types as Pydantic models later.

## a) MCP tool catalog

### `dice-mechanics`
- `roll(notation)`
- `roll_check(modifier, dc, advantage)`
- `roll_attack(bonus, target_ac, advantage)`
- `roll_save(modifier, dc, advantage)`
- `roll_initiative(modifiers)`

### `encounter`
- `start_encounter(combatants)`
- `get_combat_state()`
- `get_turn_order()`
- `next_turn()`
- `advance_round()`
- `apply_damage(combatant_id, amount)`
- `heal(combatant_id, amount)`
- `apply_condition(combatant_id, condition, duration)`
- `remove_condition(combatant_id, condition)`
- `set_position(combatant_id, x, y)`
- `end_encounter()`

### `game-state`
- `get_party()`
- `get_character(id)`
- `update_character(id, patch)`
- `get_scene()`
- `set_scene(location, description, present_npcs)`
- `add_inventory(id, item)`
- `spend_resource(id, resource, n)`

### `session-memory`
- `log_event(type, summary, details)`
- `recall(query, k)`
- `get_recent(n)`
- `start_session()`
- `end_session(recap)`

### `rules-rag`
- `search_rules(query, k)`
- `get_statblock(name)`
- `get_reference(name)`

### `world-lore`
- `create_lore(type, name, body)`
- `update_lore(id, patch)`
- `delete_lore(id)`
- `get_lore(id)`
- `search_lore(query)`
- `list_modules()`
- `get_module(id)`

## b) Orchestrator HTTP/SSE surface

The frontend client will use the following orchestrator endpoints. Live updates come from backend subscriptions or Firestore listeners in production.

- `POST /sessions/message` → SSE stream of `StreamEvent` (body: `{ text, mode, activeCharacterId }`)
- `GET /state/party`
- `GET /state/scene`
- `GET /state/encounter`
- `GET /state/events?n=`
- `GET /lore`
- `GET /maps`
- `GET /config`
- `GET /mode`

Combat action endpoints:
- `POST /combat/damage`
- `POST /combat/heal`
- `POST /combat/condition`
- `POST /combat/next-turn`
- `POST /combat/position`
- `POST /combat/start`
- `POST /combat/end`

Content and asset endpoints:
- `POST /maps` (upload)
- `POST /maps/{id}/activate`
- `POST /modules` (upload)
- `PATCH /config`
- `POST /mode`
- `POST /sessions/start`
- `POST /sessions/end` → recap
- `GET /sessions`

## c) Chat stream protocol

The chat stream is a sequence of `StreamEvent` objects.

- `token`: append text to the current narration bubble.
- `tool`: render an inline action card for the contained `GameEvent`.
- `state`: signal the client to refresh affected state entities.
- `done`: close the turn and conclude the current stream.

This lifecycle separates creative narration (`token`) from deterministic game-state signals (`tool`/`state`) and transaction completion (`done`).

## d) `DMClient` surface

The frontend consumes a live `DMClient` interface backed by the orchestrator.

```ts
export interface DMClient {
  subscribeParty(listener: (party: Character[]) => void): void;
  subscribeScene(listener: (scene: Scene) => void): void;
  subscribeEncounter(listener: (encounter: Encounter) => void): void;
  subscribeEvents(listener: (events: GameEvent[]) => void): void;
  subscribeLore(listener: (lore: LoreEntry[]) => void): void;
  subscribeMaps(listener: (maps: MapAsset[]) => void): void;
  subscribeConfig(listener: (config: DMConfig) => void): void;
  subscribeMode(listener: (mode: Mode) => void): void;

  sendMessage(payload: {
    text: string;
    mode: Mode;
    activeCharacterId?: string;
  }): AsyncIterable<StreamEvent>;

  applyDamage(combatantId: string, amount: number): Promise<void>;
  heal(combatantId: string, amount: number): Promise<void>;
  applyCondition(combatantId: string, condition: Condition, duration?: number): Promise<void>;
  removeCondition(combatantId: string, condition: Condition): Promise<void>;
  nextTurn(): Promise<void>;
  setPosition(combatantId: string, x: number, y: number): Promise<void>;
  startEncounter(combatants: Combatant[]): Promise<void>;
  endEncounter(): Promise<void>;

  uploadMap(file: File): Promise<MapAsset>;
  setActiveMap(mapId: string): Promise<void>;
  uploadModule(file: File): Promise<void>;
  updateDMConfig(patch: Partial<DMConfig>): Promise<void>;
  setMode(mode: Mode): Promise<void>;
  startSession(): Promise<void>;
  endSession(recap: string): Promise<void>;
  listSessions(): Promise<string[]>;
}
```

The backend will mirror `contracts/types.ts` as Pydantic models when the Python layer is implemented.
