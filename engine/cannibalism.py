"""Cannibalism; eating wolf flesh is allowed; public exposure always gets you caught."""

from __future__ import annotations

import random

import database as db
from config import (
    CANNIBALISM_CAUGHT_CHANCE,
    CANNIBALISM_EAT_MOOD_PENALTY,
    CANNIBALISM_MOOD_PENALTY,
    CANNIBALISM_STANDING_PENALTY,
)
from engine.prey_items import is_cannibal_prey


def _apply_caught_penalty(user) -> str:
    if not user["pack_id"]:
        return (
            "\n_The den would have seen everything; you're lucky no pack claims you right now._"
        )
    db.adjust_wolf_standing(user["discord_id"], -CANNIBALISM_STANDING_PENALTY)
    db.adjust_mood(user["id"], -CANNIBALISM_MOOD_PENALTY)
    return (
        f"\n**Caught.** Wolf-meat at the den does not go unnoticed. "
        f"Standing **−{CANNIBALISM_STANDING_PENALTY}** · mood **−{CANNIBALISM_MOOD_PENALTY}**."
    )


def cannibalism_public_exposure(user, prey_key: str, *, action: str) -> str:
    """
    Laying wolf meat out for the pack (/preypile) or depositing to the den reserve
    always exposes you. Returns message suffix for the command response.
    """
    if not is_cannibal_prey(prey_key):
        return ""
    if action == "preypile":
        lead = "You laid **wolf flesh** at the fresh-kill cache for everyone to see."
    elif action == "feedall":
        lead = "You served **wolf flesh** to the whole den at communal feed."
    else:
        lead = "You put **wolf flesh** in the pack food reserve."
    return lead + _apply_caught_penalty(user)


def cannibalism_eat_consequences(user, prey_key: str) -> str:
    """Private /eat or feedall bite; always costs mood; roll whether anyone notices."""
    if not is_cannibal_prey(prey_key):
        return ""
    db.adjust_mood(user["id"], -CANNIBALISM_EAT_MOOD_PENALTY)
    msg = f"\nThe taste lingers; mood **−{CANNIBALISM_EAT_MOOD_PENALTY}**."
    if random.randint(1, 100) > CANNIBALISM_CAUGHT_CHANCE:
        return msg
    if not user["pack_id"]:
        return msg + "\n_No clan saw it; but the taste stays with you._"
    db.adjust_wolf_standing(user["discord_id"], -CANNIBALISM_STANDING_PENALTY)
    extra_mood = CANNIBALISM_MOOD_PENALTY; CANNIBALISM_EAT_MOOD_PENALTY
    if extra_mood > 0:
        db.adjust_mood(user["id"], -extra_mood)
    return (
        msg
        + f"\n**Caught.** A patrol saw you tear into a wolf. "
        f"Standing **−{CANNIBALISM_STANDING_PENALTY}** · mood **−{CANNIBALISM_MOOD_PENALTY}** total."
    )
