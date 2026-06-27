"""Reptile / spider fear (Sypha and similar character traits) in combat."""

from __future__ import annotations

import database as db
from engine.combat_display import fighter_val

REPTILE_NPC_TEMPLATES = frozenset(
    {"water_snake", "garter_snake", "skink", "spider"}
)
VENOMOUS_REPTILE_TEMPLATES = frozenset(
    {"water_snake", "garter_snake", "spider"}
)


def has_reptile_insect_fear(user) -> bool:
    from engine.character_traits import _traits_for_user, canonical_traits_for_name

    traits = _traits_for_user(user)
    if not traits:
        wolf_name = ""
        if user is not None:
            if hasattr(user, "keys") and "wolf_name" in user.keys():
                wolf_name = user["wolf_name"] or ""
            elif isinstance(user, dict):
                wolf_name = user.get("wolf_name") or ""
        traits = canonical_traits_for_name(wolf_name)
    if not traits:
        return False
    for trait in traits.get("weaknesses", []):
        name = (trait.get("name") or "").lower()
        if "fear" in name and ("reptile" in name or "insect" in name):
            return True
    return False


def reptile_fear_roll_modifiers(
    attacker_f, defender_f
) -> tuple[bool, bool, str]:
    """
    return (disadvantage, advantage, flavor) for attack rolls.
    wolves with reptile fear flinch when struck and hesitate when striking snakes/lizards.
    """
    if not attacker_f or not defender_f:
        return False, False, ""

    atk_template = (
        attacker_f["npc_template"] if "npc_template" in attacker_f.keys() else None
    )
    def_template = (
        defender_f["npc_template"] if "npc_template" in defender_f.keys() else None
    )

    if fighter_val(attacker_f, "discord_id") and def_template in REPTILE_NPC_TEMPLATES:
        wolf = db.get_user(attacker_f["discord_id"])
        if wolf and has_reptile_insect_fear(wolf):
            return True, False, "_fear of reptiles; your strike wavers._"

    if atk_template in REPTILE_NPC_TEMPLATES and fighter_val(defender_f, "discord_id"):
        wolf = db.get_user(defender_f["discord_id"])
        if wolf and has_reptile_insect_fear(wolf):
            return False, True, "_reptile fear; you flinch and the strike lands clean._"

    return False, False, ""


def reptile_ambush_fear_note(user, template_key: str) -> str:
    if template_key not in REPTILE_NPC_TEMPLATES:
        return ""
    if not has_reptile_insect_fear(user):
        return ""
    return (
        "\n\n_your blood runs cold; scales and too many legs. "
        "medic training wars with instinct._"
    )
