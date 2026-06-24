"""NPC combat action selection (maneuvers for clan cats, etc.)."""

from __future__ import annotations

import random

from engine.combat_guide import COMBAT_MANEUVERS
from engine.combat_size import can_pin_target, size_rank
from engine.combat_status import maneuver_pin_block, parse_combat_flags


CAT_MANEUVER_POOL = (
    "forepaw_slash",
    "badger_defence",
    "front_paw_blow",
    "teeth_grip",
    "low_dodge",
    "tail_yank",
)

CAT_DEPUTY_MANEUVERS = CAT_MANEUVER_POOL + ("upright_lock",)

PIN_MANEUVERS = frozenset({"leap_and_hold", "jump_and_pin"})

ESCAPE_MANEUVERS = (
    "belly_rake",
    "back_kick",
    "duck_and_twist",
    "play_dead",
    "half_turn_belly_rake",
)


def _template_maneuvers(npc_stats: dict) -> list[str]:
    raw = npc_stats.get("maneuvers")
    if raw:
        return list(raw)
    template = npc_stats.get("npc_template")
    if template in ("clan_deputy",):
        return list(CAT_DEPUTY_MANEUVERS)
    if template and (
        str(template).endswith("_cat")
        or template in ("clan_warrior", "rogue_cat", "loner_cat", "kittypet")
    ):
        return list(CAT_MANEUVER_POOL)
    category = None
    if template:
        from engine.bestiary import BESTIARY_NPCS

        entry = BESTIARY_NPCS.get(template)
        if entry:
            category = entry.get("category")
    if category == "cats":
        return list(CAT_MANEUVER_POOL)
    return []


def _maneuver_allowed(
    key: str,
    attacker_f,
    defender_f,
    attacker_stats,
    defender_stats,
) -> bool:
    spec = COMBAT_MANEUVERS.get(key)
    if not spec:
        return False
    if key in PIN_MANEUVERS and not can_pin_target(attacker_stats, defender_stats):
        return False
    if key == "scruff_shake" and size_rank(attacker_stats) <= size_rank(defender_stats):
        return False
    block = maneuver_pin_block(
        spec,
        attacker_f,
        defender_f,
        defender_hp=int(defender_stats.get("hp", defender_f["hp"])),
        defender_max_hp=int(defender_stats.get("max_hp", defender_f["max_hp"])),
        attacker_stats=attacker_stats,
        defender_stats=defender_stats,
    )
    return block is None


def pick_npc_action(
    attacker_f,
    defender_f,
    attacker_stats: dict,
    defender_stats: dict,
) -> tuple[str, str | None]:
    """
    Return (attack_type, maneuver_key).
    maneuver_key is set when the NPC uses a special maneuver instead of a natural attack.
    """
    pool = _template_maneuvers(attacker_stats)
    if not pool:
        profile = attacker_stats.get("npc_attack_profile") or {}
        return profile.get("type", "bite"), None

    weight = float(attacker_stats.get("maneuver_weight", 0.42))
    a_flags = parse_combat_flags(attacker_f)

    if a_flags.get("pinned"):
        pinner_id = a_flags.get("pinned_by")
        if pinner_id and defender_f["id"] == pinner_id:
            escape = [k for k in ESCAPE_MANEUVERS if k in COMBAT_MANEUVERS]
            escape = [
                k
                for k in escape
                if _maneuver_allowed(
                    k, attacker_f, defender_f, attacker_stats, defender_stats
                )
            ]
            if escape:
                return "claw", random.choice(escape)
        profile = attacker_stats.get("npc_attack_profile") or {}
        return profile.get("type", "bite"), None

    if random.random() > weight:
        profile = attacker_stats.get("npc_attack_profile") or {}
        return profile.get("type", "bite"), None

    candidates = [
        k
        for k in pool
        if _maneuver_allowed(k, attacker_f, defender_f, attacker_stats, defender_stats)
    ]
    if not candidates:
        profile = attacker_stats.get("npc_attack_profile") or {}
        return profile.get("type", "bite"), None
    return "claw", random.choice(candidates)
