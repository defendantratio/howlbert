"""Combat injury resolution; spine bites and paralysis."""

from __future__ import annotations

import random

from engine.conditions import add_injury, roll_injury, roll_severe_injury
from herbs import INJURIES


def resolve_player_injury_key(
    *,
    maneuver_key: str | None,
    crit: bool,
    hit: bool,
    new_hp: int,
    max_hp: int,
) -> str | None:
    """
    Pick an injury key when a player wolf is critically hit or dropped to 0 HP.
    Spine Bite can inflict temporary or permanent paralysis instead of a table
    roll. Any other critical hit risks the severe injury table; a plain
    knockout (no crit) uses the base 1d10 table.
    """
    if not hit:
        return None
    if maneuver_key == "spine_bite":
        if crit:
            return "paralyzed" if random.random() < 0.18 else "spinal_injury"
        if max_hp > 0 and new_hp <= max_hp * 0.35:
            if random.random() < 0.45:
                return "spinal_injury"
        if random.random() < 0.18:
            return "spinal_injury"
        if new_hp == 0:
            return roll_injury()
        return None
    if crit:
        return roll_severe_injury()
    if new_hp == 0:
        return roll_injury()
    return None


def injury_label(key: str) -> str:
    info = INJURIES.get(key)
    if not info:
        return key
    return f"**{info['name']}**; {info['effect']}"


def apply_injury_to_list(injuries: list[str], key: str) -> list[str]:
    if key in ("paralyzed", "spinal_injury"):
        cleaned = [i for i in injuries if i not in ("paralyzed", "spinal_injury")]
        return add_injury(cleaned, key)
    return add_injury(injuries, key)
