export type Mode = 'adventure' | 'collaboration';

export type Condition =
  | 'blinded'
  | 'charmed'
  | 'deafened'
  | 'exhausted'
  | 'frightened'
  | 'grappled'
  | 'incapacitated'
  | 'invisible'
  | 'paralyzed'
  | 'petrified'
  | 'poisoned'
  | 'prone'
  | 'restrained'
  | 'stunned'
  | 'unconscious';

export interface Resource {
  name: string;
  current: number;
  max?: number;
}

export interface InventoryItem {
  id: string;
  name: string;
  quantity: number;
  description?: string;
}

export interface Character {
  id: string;
  name: string;
  className: string;
  level: number;
  hp: {
    current: number;
    max: number;
    temp?: number;
  };
  ac: number;
  conditions: Condition[];
  exhaustion: 0 | 1 | 2 | 3 | 4 | 5 | 6;
  resources: Resource[];
  inventory: InventoryItem[];
}

export interface Scene {
  location: string;
  description: string;
  presentNpcs: string[];
  activeMapId: string | null;
}

export interface Position {
  x: number;
  y: number;
}

export interface Combatant {
  id: string;
  name: string;
  side: 'pc' | 'npc';
  hp: {
    current: number;
    max: number;
    temp?: number;
  };
  conditions: Condition[];
  initiative: number;
  position: Position | null;
}

export interface Encounter {
  id: string;
  active: boolean;
  round: number;
  turnIndex: number;
  combatants: Combatant[];
}

export interface GameEvent {
  id: string;
  ts: string;
  type: string;
  summary: string;
}

export interface LoreEntry {
  id: string;
  type: string;
  name: string;
  body: string;
  moduleId?: string;
  tags?: string[];
}

export interface MapAsset {
  id: string;
  name: string;
  url: string;
  gridW: number;
  gridH: number;
  sceneTag: string;
  isActive: boolean;
}

export type Tone = 'gritty' | 'heroic' | 'comedic' | 'horror' | 'cinematic';
export type RulesStrictness = 'raw' | 'balanced' | 'rule_of_cool';
export type Lethality = 'forgiving' | 'standard' | 'deadly';
export type DiceTransparency = 'open' | 'dm_screen';
export type NarrationLength = 'terse' | 'medium' | 'cinematic';
export type Pacing = 'sandbox' | 'guided' | 'structured';
export type NPCVoice = 'distinct' | 'plain' | 'characterful';
export type CombatDetail = 'narrative' | 'tactical';
export type Agency = 'low' | 'medium' | 'high';

export interface DMConfig {
  tone: Tone;
  rulesStrictness: RulesStrictness;
  lethality: Lethality;
  diceTransparency: DiceTransparency;
  narrationLength: NarrationLength;
  pacing: Pacing;
  npcVoice: NPCVoice;
  combatDetail: CombatDetail;
  agency: Agency;
  contentBoundaries: string;
  houseRules: string[];
  directives: string[];
}

export type StreamEvent =
  | { kind: 'token'; text: string }
  | { kind: 'tool'; event: GameEvent }
  | { kind: 'state' }
  | { kind: 'done' };
