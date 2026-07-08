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
        "effect": "Visible scars; **+1** Intimidation and **+1** Deception in confrontational contexts.",
        "intimidate_bonus": 1,
        "deception_bonus": 1,
    },
    "chronic_pain": {
        "label": "Bone-Ache",
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
    "winter_survivor": {
        "label": "Winter Survivor",
        "effect": "Lived through a full winter; **+1** on Survival or Constitution checks in cold/wet weather, and immune to chronic-pain weather flares.",
        "intimidate_bonus": 0,
    },
    "runt": {
        "label": "Runt of the Litter",
        "effect": "Smallest of a large litter; one attribute permanently weaker.",
        "intimidate_bonus": 0,
    },
    "battle_hardened": {
        "label": "Battle-Hardened",
        "effect": "Survived five or more serious fights; **+1** on attack rolls. Immune to winded state and round-count fatigue penalties in combat.",
        "intimidate_bonus": 1,
    },
    "scarred_hide": {
        "label": "Scarred Hide",
        "effect": "Took three or more serious wounds in a single fight; hide toughened by damage; **+1 max HP** permanently, **+1 CHA** (battle-worn authority). Stacks with scarring.",
        "intimidate_bonus": 0,
        "max_hp_bonus": 1,
        "cha_bonus": 1,
    },
    "healer_instinct": {
        "label": "Healer's Instinct",
        "effect": "Performed 20+ successful treatments; deepened knowledge of the body; **+1 WIS** permanently.",
        "intimidate_bonus": 0,
        "wis_bonus": 1,
    },
    "arthritis": {
        "label": "Joint-Rot",
        "effect": "chronic joint stiffness; **-1** on Dexterity checks always; **disadvantage** on Dexterity checks in cold or wet weather. daisy or willow bark eases pain for 1 sunrise.",
        "intimidate_bonus": 0,
    },
    # cumulative organ damage from prolonged internal herb overuse (see
    # engine.herb_side_effects). permanent; the price of leaning on one draught.
    "low_potassium": {
        "label": "Weak-Heart",
        "effect": "potassium wasted by overused diuretic herbs; **-1** on Strength and Constitution checks; the heart tires easily.",
    },
    "kidney_damage": {
        "label": "Rot-Kidney",
        "effect": "kidneys scarred by overused herbs; **-1** on Constitution checks; thirst bites harder.",
    },
    "liver_damage": {
        "label": "Bile-Rot",
        "effect": "liver scarred by repeated toxins; **-1** on Constitution checks and on saves against disease and poison.",
    },
    "thiamine_deficiency": {
        "label": "The Trembles",
        "effect": "nerve damage from herbs that leach thiamine; **-1** on Dexterity and Wisdom checks.",
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


def apply_winter_survivor_trait_on_rollover(conn) -> int:
    """
    Called once when winter ends (old_season == 'winter', new_season !=
    'winter'). Grants the permanent winter_survivor trait to every living,
    non-pup wolf; operates on the rollover's own connection so it never
    opens a second one (would deadlock against the rollover transaction).
    """
    from config import PUP_MAX_MOONS

    rows = conn.execute(
        """
        SELECT id, long_term_injuries FROM users
        WHERE condition != 'dead' AND age_months >= ?
        """,
        (PUP_MAX_MOONS,),
    ).fetchall()
    granted = 0
    for row in rows:
        current = parse_long_term_injuries(row["long_term_injuries"])
        if "winter_survivor" in current:
            continue
        current.append("winter_survivor")
        conn.execute(
            "UPDATE users SET long_term_injuries = ? WHERE id = ?",
            (json.dumps(current), row["id"]),
        )
        granted += 1
    return granted


CHRONIC_CONVERSION_TARGET = {
    "sprained_leg": "limp",
    "broken_jaw": "limp",
    "spinal_injury": "limp",
    "punctured_paw": "limp",
    "fractured_rib": "chronic_pain",
    "concussion": "chronic_pain",
    "torn_claw": "scarring",
    "festering_wound": "chronic_pain",
}


def convert_untreated_injuries_on_rollover(conn, current_day: int) -> list[tuple[int, str, str, str]]:
    """
    An injury left untreated isn't supposed to sit forever; `/medic` is the
    only thing that clears one, but a wolf nobody ever treats shouldn't get
    to coast on a temporary wound indefinitely either. Past
    CHRONIC_CONVERSION_MULTIPLIER times its normal heal_days, an untreated
    injury ages into the closest matching permanent long-term injury and is
    removed from active_injuries. Only injuries with a defined heal_days and
    a mapped chronic target convert; operates on the rollover's own
    connection to avoid a nested-connection deadlock.
    Returns a list of (wolf_id, wolf_name, injury_key, chronic_key) tuples.
    """
    from config import CHRONIC_CONVERSION_MULTIPLIER
    from engine.conditions import parse_injuries, parse_injury_since
    from herbs import INJURIES

    rows = conn.execute(
        """
        SELECT id, wolf_name, active_injuries, injury_since, long_term_injuries
        FROM users WHERE condition != 'dead' AND active_injuries IS NOT NULL
        """
    ).fetchall()
    converted: list[tuple[int, str, str, str]] = []
    for row in rows:
        injuries = parse_injuries(row["active_injuries"])
        if not injuries:
            continue
        since = parse_injury_since(row["injury_since"])
        remaining = list(injuries)
        changed = False
        lt_current = parse_long_term_injuries(row["long_term_injuries"])
        for key in injuries:
            target = CHRONIC_CONVERSION_TARGET.get(key)
            info = INJURIES.get(key)
            start = since.get(key)
            if not target or not info or not info.get("heal_days") or start is None:
                continue
            threshold = int(info["heal_days"]) * CHRONIC_CONVERSION_MULTIPLIER
            if current_day - start < threshold:
                continue
            remaining.remove(key)
            since.pop(key, None)
            if target not in lt_current:
                lt_current.append(target)
            changed = True
            converted.append((row["id"], row["wolf_name"], key, target))
        if changed:
            conn.execute(
                "UPDATE users SET active_injuries = ?, injury_since = ?, long_term_injuries = ? WHERE id = ?",
                (json.dumps(remaining), json.dumps(since), json.dumps(lt_current), row["id"]),
            )
    return converted


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
    a permanent scar; a lasting consequence beyond the HP bar, and a genuine
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


COMBAT_VICTORIES_FOR_BATTLE_HARDENED = 5


def record_combat_victory(wolf_id: int) -> str | None:
    """
    Increment a wolf's combat-victory counter. Grants battle_hardened at 5 wins.
    Returns a player-facing note when the trait is earned, or None.
    """
    wolf = db.get_user_by_id(wolf_id)
    if not wolf:
        return None
    current_lt = parse_long_term_injuries(
        wolf["long_term_injuries"] if "long_term_injuries" in wolf.keys() else None
    )
    if "battle_hardened" in current_lt:
        return None
    from engine.herb_buffs import buffs_json, get_buffs

    buffs = get_buffs(wolf)
    wins = int(buffs.get("combat_victories", 0)) + 1
    buffs["combat_victories"] = wins
    db.update_user_by_id(wolf_id, herb_buffs=buffs_json(buffs))
    if wins >= COMBAT_VICTORIES_FOR_BATTLE_HARDENED:
        add_long_term_injury(wolf_id, "battle_hardened")
        return (
            f"**{wolf['wolf_name']}** has fought through {wins} serious battles; "
            f"they are now **Battle-Hardened**; {LONG_TERM_TYPES['battle_hardened']['effect']}"
        )
    return None


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
    if "scarring" in entries and skill_key == "deception":
        mod += 1
        notes.append("Scars (+1 Deception; unsettling presence)")
    if "battle_hardened" in entries and skill_key == "intimidation":
        mod += 1
        notes.append("Battle-Hardened (+1 Intimidation)")
    if "bold_arrival" in entries and skill_key == "intimidation":
        mod += 1
        notes.append("Bold arrival (+1 Intimidation)")
    if "quiet_arrival" in entries and skill_key == "stealth":
        mod += 1
        notes.append("Quiet arrival (+1 Stealth)")
    if "wary_arrival" in entries and skill_key == "survival":
        mod += 1
        notes.append("Wary arrival (+1 Survival)")
    cold_weather = weather in ("rain", "sleet", "snow", "hail", "storm", "thunderstorm", "wind")
    shedding = day_number > 0 and day_number <= int(user["shedding_until_day"] or 0) if user and "shedding_until_day" in user.keys() else False
    if (
        "winter_survivor" in entries
        and cold_weather
        and not shedding
        and (skill_key == "survival" or "attr_con" in attr_keys)
    ):
        mod += 1
        notes.append("Winter survivor (+1 in cold/wet weather)")
    if shedding and cold_weather and "attr_con" in attr_keys:
        mod -= 1
        notes.append("Mid-shed; coat isn't fully grown in yet (cold hits harder)")
    if shedding and skill_key == "stealth":
        mod -= 1
        notes.append("Mid-shed; loose fur clings to everything (−1 Stealth)")
    if "arthritis" in entries and "attr_dex" in attr_keys:
        from engine.herb_buffs import pain_relief_active

        day = day_number
        if pain_relief_active(user, day):
            notes.append("pain relief (arthritis ease active)")
        else:
            mod -= 1
            notes.append("Arthritis (-1 Dex)")
            if weather in ("rain", "sleet", "snow", "hail", "storm", "thunderstorm", "wind"):
                disadvantage = True
                notes.append("joints seize in cold and wet (disadvantage)")

    if "chronic_pain" in entries and first_physical_today:
        from engine.herb_buffs import pain_relief_active

        day = day_number
        if pain_relief_active(user, day):
            notes.append("Pain relief (willow bark, poppy, etc.)")
        elif cold_weather and "winter_survivor" not in entries:
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

    # cumulative organ damage from herb overuse
    if "low_potassium" in entries and ("attr_str" in attr_keys or "attr_con" in attr_keys):
        mod -= 1
        notes.append("Weak-Heart (−1)")
    if "kidney_damage" in entries and "attr_con" in attr_keys:
        mod -= 1
        notes.append("Rot-Kidney (−1 Con)")
    if "liver_damage" in entries and "attr_con" in attr_keys:
        mod -= 1
        notes.append("Bile-Rot (−1 Con)")
    if "thiamine_deficiency" in entries and ("attr_dex" in attr_keys or "attr_wis" in attr_keys):
        mod -= 1
        notes.append("The Trembles (−1)")

    return mod, disadvantage, " · ".join(notes)


SEVERE_INJURIES = frozenset({"fractured_rib", "spinal_injury", "paralysis"})


def apply_winter_cold_injury_on_rollover(conn, season: str) -> list[dict]:
    """Winter cold worsens severe injuries: −1 HP per sunrise for fractured ribs,
    spinal injuries, and paralysis. Doesn't kill outright (floor 1 HP) so medics
    still have a window to intervene."""
    if season != "winter":
        return []
    from engine.conditions import parse_injuries

    rows = conn.execute(
        "SELECT * FROM users WHERE condition NOT IN ('dead', 'dying') AND active_injuries IS NOT NULL AND active_injuries != ''"
    ).fetchall()
    notes: list[dict] = []
    for wolf in rows:
        injuries = set(parse_injuries(wolf["active_injuries"]))
        severe = injuries & SEVERE_INJURIES
        if not severe:
            continue
        hp = int(wolf["hp"])
        if hp <= 1:
            continue
        new_hp = max(1, hp - 1)
        conn.execute("UPDATE users SET hp = ? WHERE id = ?", (new_hp, wolf["id"]))
        label = ", ".join(k.replace("_", " ") for k in sorted(severe))
        notes.append({
            "wolf_name": wolf["wolf_name"],
            "discord_id": int(wolf["discord_id"]),
            "line": f"winter cold deepens **{label}** (−1 hp → **{new_hp}**); see a medic.",
        })
    return notes
