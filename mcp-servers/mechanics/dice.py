"""Pure, deterministic dice logic for the dice-mechanics MCP server.

No MCP imports and no side effects beyond reading the RNG — every function here is a
plain input -> output transformation that is trivially unit-testable. The MCP tool
wrappers in ``server.py`` import these and expose them as tools.

Ruleset: D&D 2024 (5.5e). Advantage/disadvantage is modeled as a string enum
("none" | "advantage" | "disadvantage") so it reads cleanly as a Gemini function
parameter and is unambiguous to the model.
"""

from __future__ import annotations

import random
import re

# Guard rails so a malformed or adversarial model call can't ask us to roll a
# billion dice and hang the server. These are far above anything D&D needs.
MAX_DICE = 1000
MAX_SIDES = 1000

ADVANTAGE_VALUES = ("none", "advantage", "disadvantage")

# Matches "2d6+3", "d20", "1d8-1", "4d6" — optional count, required dXX, optional +/-K.
_NOTATION_RE = re.compile(r"^\s*(\d*)\s*d\s*(\d+)\s*([+-]\s*\d+)?\s*$", re.IGNORECASE)


def _validate_advantage(advantage: str) -> str:
    adv = (advantage or "none").strip().lower()
    if adv not in ADVANTAGE_VALUES:
        raise ValueError(
            f"advantage must be one of {ADVANTAGE_VALUES}, got {advantage!r}"
        )
    return adv


def roll(notation: str) -> dict:
    """Roll standard dice notation like "2d6+3".

    Returns the individual dice, the flat modifier, and the total.
    """
    match = _NOTATION_RE.match(notation or "")
    if not match:
        raise ValueError(
            f"invalid dice notation {notation!r}; expected forms like '2d6+3', 'd20', '1d8-1'"
        )

    count_str, sides_str, mod_str = match.groups()
    count = int(count_str) if count_str else 1
    sides = int(sides_str)
    modifier = int(mod_str.replace(" ", "")) if mod_str else 0

    if count < 1 or count > MAX_DICE:
        raise ValueError(f"dice count must be between 1 and {MAX_DICE}, got {count}")
    if sides < 1 or sides > MAX_SIDES:
        raise ValueError(f"die sides must be between 1 and {MAX_SIDES}, got {sides}")

    rolls = [random.randint(1, sides) for _ in range(count)]
    return {
        "notation": notation,
        "rolls": rolls,
        "modifier": modifier,
        "total": sum(rolls) + modifier,
    }


def _d20(advantage: str = "none") -> dict:
    """Roll a d20, applying advantage/disadvantage.

    Returns the kept value plus both raw dice (when two were rolled) so callers can
    surface the full picture for transparency.
    """
    adv = _validate_advantage(advantage)
    if adv == "none":
        die = random.randint(1, 20)
        return {"d20": die, "dice": [die], "advantage": adv}

    dice = [random.randint(1, 20), random.randint(1, 20)]
    kept = max(dice) if adv == "advantage" else min(dice)
    return {"d20": kept, "dice": dice, "advantage": adv}


def roll_check(modifier: int, dc: int, advantage: str = "none") -> dict:
    """Resolve an ability/skill check against a DC."""
    d = _d20(advantage)
    total = d["d20"] + modifier
    return {
        "d20": d["d20"],
        "dice": d["dice"],
        "advantage": d["advantage"],
        "modifier": modifier,
        "total": total,
        "dc": dc,
        "success": total >= dc,
    }


def roll_attack(bonus: int, target_ac: int, advantage: str = "none") -> dict:
    """Resolve an attack roll against a target AC.

    D&D 2024: a natural 20 is an automatic hit and a critical hit; a natural 1 is an
    automatic miss. Otherwise hit if (d20 + bonus) >= target AC.
    """
    d = _d20(advantage)
    nat = d["d20"]
    total = nat + bonus

    critical_hit = nat == 20
    critical_miss = nat == 1
    if critical_hit:
        hit = True
    elif critical_miss:
        hit = False
    else:
        hit = total >= target_ac

    return {
        "d20": nat,
        "dice": d["dice"],
        "advantage": d["advantage"],
        "bonus": bonus,
        "total": total,
        "target_ac": target_ac,
        "hit": hit,
        "critical_hit": critical_hit,
        "critical_miss": critical_miss,
    }
