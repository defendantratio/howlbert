"""Standing penalties for crimes and mating infractions."""

from __future__ import annotations

import random

import database as db
from config import (
    CRIME_CATCH_CHANCE,
    CRIME_CAUGHT_STANDING,
    CRIME_CAUGHT_TEXT,
    CROSS_PACK_MATE_CATCH_CHANCE,
    CROSS_PACK_MATE_CAUGHT_STANDING,
    CROSS_PACK_MATE_CAUGHT_TEXT,
    CROSS_PACK_STEAL_CATCH_CHANCE,
    CROSS_PACK_STEAL_CAUGHT_STANDING,
    CROSS_PACK_STEAL_CAUGHT_TEXT,
    CROSS_PACK_STEAL_STANDING,
    INDIVIDUAL_STEAL_CATCH_CHANCE,
    INDIVIDUAL_STEAL_CAUGHT_STANDING,
    INDIVIDUAL_STEAL_STANDING,
    MEDIC_MATE_CATCH_CHANCE,
    MEDIC_MATE_CAUGHT_STANDING,
    MEDIC_MATE_CAUGHT_TEXT,
    YIELD_CATCH_CHANCE,
    YIELD_CAUGHT_STANDING,
    YIELD_CAUGHT_TEXT,
)

from engine.apprentice_roles import parent_role

MEDIC_ROLE = "medic"


def wolves_share_pack(a, b) -> bool:
    if not a or not b:
        return False
    pack_a = a["pack_id"] if "pack_id" in a.keys() else None
    pack_b = b["pack_id"] if "pack_id" in b.keys() else None
    return bool(pack_a and pack_b and pack_a == pack_b)


def is_cross_pack_pair(a, b) -> bool:
    """true when two wolves are not in the same great pack (at least one in a den)."""
    if wolves_share_pack(a, b):
        return False
    pack_a = a["pack_id"] if a and "pack_id" in a.keys() else None
    pack_b = b["pack_id"] if b and "pack_id" in b.keys() else None
    return bool(pack_a or pack_b)


def is_medic(wolf) -> bool:
    if not wolf:
        return False
    role = wolf["wolf_role"] if "wolf_role" in wolf.keys() else "hunter"
    return role == MEDIC_ROLE or parent_role(role) == "medic"


def roll_crime_caught() -> bool:
    return random.random() < CRIME_CATCH_CHANCE




def roll_cross_pack_mate_caught() -> bool:
    return random.random() < CROSS_PACK_MATE_CATCH_CHANCE




def roll_yield_caught() -> bool:
    return random.random() < YIELD_CATCH_CHANCE


def crime_caught_standing() -> int:
    return CRIME_CAUGHT_STANDING


def roll_individual_steal_caught() -> bool:
    return random.random() < INDIVIDUAL_STEAL_CATCH_CHANCE


def individual_steal_caught_standing() -> int:
    return INDIVIDUAL_STEAL_CAUGHT_STANDING


def individual_steal_standing() -> int:
    return INDIVIDUAL_STEAL_STANDING


def cross_pack_steal_standing() -> int:
    return CROSS_PACK_STEAL_STANDING


def cross_pack_steal_caught_standing() -> int:
    return CROSS_PACK_STEAL_CAUGHT_STANDING


def cross_pack_mate_caught_standing() -> int:
    return CROSS_PACK_MATE_CAUGHT_STANDING




def yield_caught_standing() -> int:
    return YIELD_CAUGHT_STANDING


def pick_yield_caught_flavor() -> str:
    return random.choice(YIELD_CAUGHT_TEXT)


def apply_yield_caught(user) -> tuple[str | None, str]:
    """
    if a wolf in a pack is caught yielding, penalize standing.
    returns (expulsion note, flavor text) or (none, '').
    """
    if not user:
        return None, ""
    pack_id = user["pack_id"] if "pack_id" in user.keys() else None
    if not pack_id:
        return None, ""
    if not roll_yield_caught():
        return None, ""

    flavor = pick_yield_caught_flavor()
    kick = db.adjust_wolf_standing_by_id(user["id"], YIELD_CAUGHT_STANDING)
    expulsion_note = "you were **cast out** of the pack." if kick == "kicked" else None
    return expulsion_note, flavor


def pick_crime_caught_flavor() -> str:
    return random.choice(CRIME_CAUGHT_TEXT)


def pick_cross_pack_steal_caught_flavor(pack_name: str) -> str:
    return random.choice(CROSS_PACK_STEAL_CAUGHT_TEXT).format(pack=pack_name)


def pick_cross_pack_mate_caught_flavor() -> str:
    return random.choice(CROSS_PACK_MATE_CAUGHT_TEXT)




def _apply_standing_penalties(
    wolves: tuple,
    *,
    penalty: int,
    actor,
) -> str | None:
    expulsion_note = None
    for wolf in wolves:
        if not wolf:
            continue
        pack_id = wolf["pack_id"] if "pack_id" in wolf.keys() else None
        if not pack_id:
            continue
        kick = db.adjust_wolf_standing_by_id(wolf["id"], penalty)
        if kick == "kicked" and wolf["id"] == actor["id"]:
            expulsion_note = "you were **cast out** of the pack."
    return expulsion_note


def apply_cross_pack_mate_caught(
    user, partner, *, guild_id: int | None = None, day: int = 0
) -> tuple[str | None, str]:
    """
    If a cross-pack pairing is caught, penalize standing for wolves in a pack.
    Returns (expulsion note for actor, flavor text) or (None, '').
    """
    if not is_cross_pack_pair(user, partner):
        return None, ""
    if not roll_cross_pack_mate_caught():
        return None, ""

    flavor = pick_cross_pack_mate_caught_flavor()
    expulsion_note = _apply_standing_penalties(
        (user, partner),
        penalty=cross_pack_mate_caught_standing(),
        actor=user,
    )
    if guild_id:
        db.record_cross_pack_scandal(
            guild_id,
            int(user["id"]),
            int(partner["id"]),
            caught_day=day or 0,
        )
    return expulsion_note, flavor


def apply_medic_mate_caught(user, partner) -> tuple[str | None, str]:
    """
    if a medic mates and is caught, penalize standing and exile family.
    returns (expulsion note for actor, flavor text) or (none, '').
    """
    from engine.healer_code import apply_medic_mate_caught as _healer_mate

    return _healer_mate(user, partner)


def apply_mate_infractions(
    user, partner, *, guild_id: int | None = None, day: int = 0
) -> tuple[str | None, list[str]]:
    """
    Run all mating infraction checks (cross-pack, medic oath, etc.).
    Returns (expulsion note for actor, embed lines).
    """
    lines: list[str] = []
    expulsion_note = None

    cross_exp, cross_flavor = apply_cross_pack_mate_caught(
        user, partner, guild_id=guild_id, day=day
    )
    if cross_flavor:
        lines.append(
            f"**caught (cross-pack)**; {cross_flavor}\n"
            f"standing **{cross_pack_mate_caught_standing()}** for each wolf still in a pack."
        )
        expulsion_note = cross_exp

    medic_exp, medic_lines = apply_medic_mate_caught(user, partner)
    if medic_lines:
        lines.extend(medic_lines)
        if medic_exp:
            expulsion_note = medic_exp

    return expulsion_note, lines
