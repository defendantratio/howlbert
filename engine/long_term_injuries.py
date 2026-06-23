"""Permanent marks after healing; limp, scars, chronic pain, fear triggers."""

from __future__ import annotations

import json
import random

import database as db

LONG_TERM_TYPES = {
    "limp": {
        "label": "Limp",
        "effect": "Movement speed −¼ (round down); −1 on Dexterity checks involving running.",
        "intimidate_bonus": 0,
    },
    "scarring": {
        "label": "Scarring",
        "effect": "Visible scars; **+1** on Intimidation when the scar is seen.",
        "intimidate_bonus": 1,
    },
    "chronic_pain": {
        "label": "Chronic Pain",
        "effect": "On cold or rainy days, disadvantage on the first Strength or Dexterity check.",
        "intimidate_bonus": 0,
    },
}

CURE_HERBS = frozenset({"wolfsbane", "swamp_milkweed"})

FEAR_TRIGGER_DC = 12

TRIGGER_CONTEXTS: dict[str, frozenset[str]] = {
    "water": frozenset({"river", "swamp", "water", "flood", "spring_river", "lake"}),
    "deep_water": frozenset({"river", "swamp", "water", "flood", "spring_river", "lake"}),
    "heights": frozenset({"mountain", "cliff", "height", "avalanche"}),
    "thunder": frozenset({"storm", "thunder", "lightning", "hail"}),
    "dark": frozenset({"dark", "cave", "night"}),
    "confined": frozenset({"cave", "den", "trap"}),
}


def parse_long_term_injuries(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data if x]
    except json.JSONDecodeError:
        pass
    return []


def format_long_term_injuries(user) -> str | None:
    entries = parse_long_term_injuries(
        user["long_term_injuries"] if "long_term_injuries" in user.keys() else None
    )
    if not entries:
        return None
    lines = []
    for entry in entries:
        if entry.startswith("fear:"):
            trigger = entry[5:].replace("_", " ").title()
            lines.append(f"**Fear of {trigger}**: Wisdom DC 12 or frightened 1 round when faced.")
            continue
        info = LONG_TERM_TYPES.get(entry)
        if info:
            lines.append(f"**{info['label']}**: {info['effect']}")
        else:
            lines.append(f"**{entry}**")
    return " · ".join(lines)


def add_long_term_injury(wolf_id: int, entry: str) -> None:
    wolf = db.get_user_by_id(wolf_id)
    if not wolf:
        return
    current = parse_long_term_injuries(
        wolf["long_term_injuries"] if "long_term_injuries" in wolf.keys() else None
    )
    if entry in current:
        return
    current.append(entry)
    db.update_user_by_id(wolf_id, long_term_injuries=json.dumps(current))


def add_fear_trigger(wolf_id: int, trigger: str) -> None:
    key = trigger.strip().lower().replace(" ", "_")
    add_long_term_injury(wolf_id, f"fear:{key}")


def matching_fear_triggers(
    user,
    *,
    fear_context: str | None,
    skill_key: str | None,
) -> list[str]:
    entries = parse_long_term_injuries(
        user["long_term_injuries"] if "long_term_injuries" in user.keys() else None
    )
    if not entries or not fear_context:
        return []
    ctx = fear_context.lower()
    matched: list[str] = []
    for entry in entries:
        if not entry.startswith("fear:"):
            continue
        trigger = entry[5:]
        if trigger == "fire":
            continue
        contexts = TRIGGER_CONTEXTS.get(trigger, frozenset({trigger}))
        if any(token in ctx for token in contexts):
            matched.append(trigger)
    return matched


def fear_trigger_check(
    user,
    *,
    fear_context: str | None,
    skill_key: str | None,
    game_day: int | None,
) -> tuple[bool, str]:
    """Roll Wisdom DC 12 when a fear:trigger matches; fail → disadvantage."""
    triggers = matching_fear_triggers(user, fear_context=fear_context, skill_key=skill_key)
    if not triggers:
        return False, ""
    from engine.character import attr_modifier
    from engine.rolls import roll_d20

    wis = int(user["attr_wis"]) if user and "attr_wis" in user.keys() else 3
    mod = attr_modifier(wis)
    die = roll_d20()
    total = die + mod
    if total >= FEAR_TRIGGER_DC:
        return False, ""
    label = triggers[0].replace("_", " ")
    return True, f"Fear of {label} (WIS {total} vs DC {FEAR_TRIGGER_DC})"


def clear_long_term_injuries(wolf_id: int) -> None:
    db.update_user_by_id(wolf_id, long_term_injuries="[]")


def try_cure_long_term(herb_key: str, user) -> tuple[bool, str]:
    if herb_key not in CURE_HERBS:
        return False, ""
    entries = parse_long_term_injuries(
        user["long_term_injuries"] if "long_term_injuries" in user.keys() else None
    )
    if not entries:
        return False, "No long-term injuries to lift."
    if herb_key == "wolfsbane":
        dmg = random.randint(2, 6)
        new_hp = max(0, int(user["hp"]) - dmg)
        db.set_user_conditions(user["discord_id"], hp=new_hp)
        clear_long_term_injuries(user["id"])
        return True, (
            f"Spirit curse broken; long-term marks fade. The patient takes **{dmg}** poison damage."
        )
    clear_long_term_injuries(user["id"])
    return True, "Marsh milk breaks the old curse; long-term injuries ease."


def check_adjustments(
    user,
    *,
    attr_keys: tuple[str, ...],
    skill_key: str | None,
    weather: str,
    day_number: int,
    first_physical_today: bool,
) -> tuple[int, bool, str]:
    """Returns (flat_mod, disadvantage, note)."""
    entries = parse_long_term_injuries(
        user["long_term_injuries"] if "long_term_injuries" in user.keys() else None
    )
    if not entries:
        return 0, False, ""

    mod = 0
    disadvantage = False
    notes: list[str] = []

    if "limp" in entries and "attr_dex" in attr_keys:
        mod -= 1
        notes.append("Limp (−1 Dex)")
    if "scarring" in entries and skill_key == "intimidation":
        mod += 1
        notes.append("Scars (+1 Intimidation)")
    if "chronic_pain" in entries and first_physical_today:
        if weather in ("rain", "sleet", "snow", "hail", "storm", "thunderstorm", "wind"):
            if "attr_str" in attr_keys or "attr_dex" in attr_keys:
                disadvantage = True
                notes.append("Chronic pain (disadvantage)")

    return mod, disadvantage, " · ".join(notes)
