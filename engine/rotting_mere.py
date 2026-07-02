"""Rotting Mere: special foraging pool, swamp exposure, and Drown-Sick trigger."""
from __future__ import annotations

import random

import database as db

ROTTING_MERE_LOCATION = "The Rotting Mere"

_MERE_HERBS = [
    ("marsh_mallow", 0.55),
    ("belly_rip_fungus", 0.30),
    ("death_cap", 0.15),
]

_MAW_CONTACT_LINES = (
    "The water is not still. Something below the surface watches back.",
    "You feel it before you see it — a second heartbeat in the mud beneath your paws.",
    "The mushrooms glow brighter as you approach, then dim. A warning, or a welcome.",
    "The Maw does not only live in the mountain's mouth. It is here. It has always been here.",
    "You did not choose to come here. You were called.",
    "The mere has no bottom. Every wolf who has checked is still checking.",
)

_DROWN_SICK_LINES = (
    "The bank gives way and you are under before you can stop it. For one heartbeat "
    "— only one — the water is inside your skull. When you pull yourself out the fog "
    "speaks to you. It has been speaking. You just couldn't hear it before.",
    "Your paw slips on the slick root. The mere takes you face-first. You rise "
    "coughing pale water. Something in the depths stays behind your eyes.",
)

_SLIP_CHANCE = 0.12
_MAW_CONTACT_CHANCE = 0.25
_DROWN_SICK_CHANCE = 0.05


def is_rotting_mere(user) -> bool:
    loc = user["ic_location"] if "ic_location" in user.keys() else None
    return bool(loc and ROTTING_MERE_LOCATION.lower() in (loc or "").lower())


def pick_mere_herb() -> str:
    keys = [k for k, _ in _MERE_HERBS]
    weights = [w for _, w in _MERE_HERBS]
    return random.choices(keys, weights=weights, k=1)[0]


def try_rotting_mere_exposure(user, discord_id: int) -> tuple[str | None, bool]:
    """
    Run Maw contact flavor, swamp exposure, and Drown-Sick trigger.
    Returns (note_str, role_changed). role_changed is True if the wolf became drown_sick.
    """
    lines: list[str] = []
    role_changed = False

    if random.random() < _MAW_CONTACT_CHANCE:
        lines.append(f"_— {random.choice(_MAW_CONTACT_LINES)}_")

    if random.random() < _SLIP_CHANCE:
        from engine.disease_contract import try_mistmoor_swamp_exposure

        disease_note = try_mistmoor_swamp_exposure(user, belly_rip=True)
        if disease_note:
            lines.append(f"mere water: {disease_note}")

        role = user["wolf_role"] if "wolf_role" in user.keys() else None
        gp = user["great_pack"] if "great_pack" in user.keys() else None
        if gp == "mistmoor" and role != "drown_sick" and random.random() < _DROWN_SICK_CHANCE:
            db.update_user(discord_id, wolf_role="drown_sick")
            role_changed = True
            lines.append(
                f"\n**Drown-Sick:**\n{random.choice(_DROWN_SICK_LINES)}\n\n"
                "Your wolf is now **Drown-Sick** — a Mistmoor oracle changed by the water. "
                "Use `/role action:event`, `/role action:prophecy`, and `/role action:quests`."
            )

    return "\n\n".join(lines) if lines else None, role_changed
