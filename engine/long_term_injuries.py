"""Permanent marks after healing; limp, scars, chronic pain, fear triggers."""

from __future__ import annotations

import json
import random

import database as db

LONG_TERM_TYPES = {
    "limp": {
        "label": "Limp",
        "effect": "Movement speed −¼ (round down); −1 on Dexterity checks. Flares to disadvantage in cold/wet weather.",
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
    "bold_arrival": {
        "label": "Bold Arrival",
        "effect": "Walked into the den head-high; **+1** on Intimidation checks.",
        "intimidate_bonus": 1,
    },
    "quiet_arrival": {
        "label": "Quiet Arrival",
        "effect": "Slipped in without a sound; **+1** on Stealth checks.",
        "intimidate_bonus": 0,
    },
    "wary_arrival": {
        "label": "Wary Arrival",
        "effect": "Came in half-starved and watchful; **+1** on Survival checks.",
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
        if entry == "spirit_curse":
            from engine.supernatural import SPIRIT_CURSE_BLURB

            lines.append(f"**spirit curse**: {SPIRIT_CURSE_BLURB}")
            continue
        if entry.startswith("fear:"):
            trigger = entry[5:].replace("_", " ").title()
            lines.append(f"**fear of {trigger}**: wisdom dc 12 or frightened 1 round when faced.")
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


COMBAT_SCAR_CHANCE = 0.20


def roll_combat_scar(wolf_id: int | None) -> str | None:
    """
    Surviving a fight you lost (dropped to 0 HP) has a real chance of leaving
    a permanent scar — a lasting consequence beyond the HP bar, and a genuine
    +1 Intimidation bonus going forward (see LONG_TERM_TYPES["scarring"]).
    Returns a player-facing note, or None if no scar this time / already scarred.
    """
    if not wolf_id:
        return None
    wolf = db.get_user_by_id(wolf_id)
    if not wolf:
        return None
    current = parse_long_term_injuries(
        wolf["long_term_injuries"] if "long_term_injuries" in wolf.keys() else None
    )
    if "scarring" in current:
        return None
    if random.random() >= COMBAT_SCAR_CHANCE:
        return None
    add_long_term_injury(wolf_id, "scarring")
    return (
        f"**{wolf['wolf_name']}** carries a new scar out of this fight; "
        f"{LONG_TERM_TYPES['scarring']['effect']}"
    )


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
    return True, f"fear of {label} (wis {total} vs dc {FEAR_TRIGGER_DC})"


def clear_long_term_injuries(wolf_id: int) -> None:
    db.update_user_by_id(wolf_id, long_term_injuries="[]")


def try_cure_long_term(herb_key: str, user) -> tuple[bool, str]:
    if herb_key not in CURE_HERBS:
        return False, ""
    entries = parse_long_term_injuries(
        user["long_term_injuries"] if "long_term_injuries" in user.keys() else None
    )
    if not entries:
        return False, "no long-term injuries to lift."
    if herb_key == "wolfsbane":
        dmg = random.randint(2, 6)
        new_hp = max(0, int(user["hp"]) - dmg)
        db.set_user_conditions(user["discord_id"], hp=new_hp)
        clear_long_term_injuries(user["id"])
        return True, (
            f"spirit curse broken; long-term marks fade. the patient takes **{dmg}** poison damage."
        )
    clear_long_term_injuries(user["id"])
    return True, "marsh milk breaks the old curse; long-term injuries ease."


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
        if weather in ("rain", "sleet", "snow", "hail", "storm", "thunderstorm"):
            disadvantage = True
            notes.append("Old wound flares in the cold and wet (disadvantage)")
    if "scarring" in entries and skill_key == "intimidation":
        mod += 1
        notes.append("Scars (+1 Intimidation)")
    if "bold_arrival" in entries and skill_key == "intimidation":
        mod += 1
        notes.append("Bold arrival (+1 Intimidation)")
    if "quiet_arrival" in entries and skill_key == "stealth":
        mod += 1
        notes.append("Quiet arrival (+1 Stealth)")
    if "wary_arrival" in entries and skill_key == "survival":
        mod += 1
        notes.append("Wary arrival (+1 Survival)")
    if "chronic_pain" in entries and first_physical_today:
        from engine.herb_buffs import pain_relief_active

        day = day_number
        if pain_relief_active(user, day):
            notes.append("Pain relief (willow bark, poppy, etc.)")
        elif weather in ("rain", "sleet", "snow", "hail", "storm", "thunderstorm", "wind"):
            if "attr_str" in attr_keys or "attr_dex" in attr_keys:
                disadvantage = True
                notes.append("Chronic pain (disadvantage)")

    if "spirit_curse" in entries:
        from engine.supernatural import spirit_curse_check_adjustment

        sc_mod, sc_note = spirit_curse_check_adjustment(
            user, attr_keys=attr_keys, skill_key=skill_key
        )
        mod += sc_mod
        if sc_note:
            notes.append(sc_note)

    return mod, disadvantage, " · ".join(notes)
