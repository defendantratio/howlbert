"""Mechanical effects of each great pack's trait (see config.GREAT_PACKS).

Previously these were display-only text on /profile. A wolf gets its
directly-affiliated great pack's trait, OR — for a founded pack — every great
pack trait represented by *any* current denmate's heritage (see
engine.factions.founded_pack_heritage_keys), not just the two original
founders.

Whisper Tree (Thistlehide) is intentionally left mechanic-free; it's an
admin/RP prompt ("ask the GM a question"), not a numeric bonus.
"""

from __future__ import annotations

FOUNDERS_GRIT_BONUS_PCT = 10
STONE_ENDURANCE_LABEL = "Stone Endurance"


def active_pack_trait_keys(user) -> set[str]:
    """Great pack keys whose trait currently applies to this wolf."""
    great_pack = user["great_pack"] if user and "great_pack" in user.keys() else None
    if not great_pack:
        return set()
    from config import GREAT_PACKS

    if great_pack in GREAT_PACKS:
        return {great_pack}
    from engine.factions import founded_pack_heritage_keys, founded_pack_id

    pid = founded_pack_id(great_pack)
    if pid is not None:
        return founded_pack_heritage_keys(pid)
    return set()


def has_pack_trait(user, key: str) -> bool:
    return key in active_pack_trait_keys(user)


def pack_damage_reduction(defender) -> tuple[int, str]:
    """Greyspire's Stone Endurance: once per long rest, shave 1d6 + Strength
    modifier off a single hit. Consumes the use immediately so a second hit
    in the same rest window doesn't also benefit."""
    if "greyspire" not in active_pack_trait_keys(defender):
        return 0, ""
    last_rest = int(defender["last_rest_day"]) if "last_rest_day" in defender.keys() else 0
    last_use = (
        int(defender["last_stone_endurance_day"])
        if "last_stone_endurance_day" in defender.keys() and defender["last_stone_endurance_day"] is not None
        else 0
    )
    if last_use >= last_rest:
        return 0, ""
    import random

    from engine.character import attr_modifier

    reduction = max(0, random.randint(1, 6) + attr_modifier(defender["attr_str"]))
    if reduction <= 0:
        return 0, ""
    import database as db

    db.update_user(defender["discord_id"], wolf_id=defender["id"], last_stone_endurance_day=last_rest)
    return reduction, STONE_ENDURANCE_LABEL


def swim_check_dc_adjustment(user) -> int:
    """Silverrush's Swift Current on the swim/river-crossing scenarios
    (engine.skill_checks 'surv_swim' / 'surv_river'); effectively +2 to the
    check by trimming the DC instead, so it works regardless of which
    attribute the scenario rolls against."""
    return -2 if "silverrush" in active_pack_trait_keys(user) else 0


def founders_grit_bonus(amount: int, user) -> tuple[int, str]:
    """Founders' Grit: dispersers who built a den from nothing hunt and work
    a little harder for it; +10% bones from any bone-earning activity."""
    if amount <= 0:
        return amount, ""
    great_pack = user["great_pack"] if user and "great_pack" in user.keys() else None
    from engine.factions import is_founded_key

    if not is_founded_key(great_pack):
        return amount, ""
    bonus = max(1, int(amount * FOUNDERS_GRIT_BONUS_PCT / 100))
    return amount + bonus, f"Founders' Grit: +{FOUNDERS_GRIT_BONUS_PCT}% bones"
