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
            "\n_the den would have seen everything; you're lucky no pack claims you right now._"
        )
    db.adjust_wolf_standing_by_id(user["id"], -CANNIBALISM_STANDING_PENALTY)
    db.adjust_mood(user["id"], -CANNIBALISM_MOOD_PENALTY)
    return (
        f"\n**caught.** wolf-meat at the den does not go unnoticed. "
        f"standing **−{CANNIBALISM_STANDING_PENALTY}** · mood **−{CANNIBALISM_MOOD_PENALTY}**."
    )


def cannibalism_public_exposure(user, prey_key: str, *, action: str) -> str:
    """
    Laying wolf meat out for the pack (/preypile) or depositing to the den reserve
    always exposes you. Returns message suffix for the command response.
    """
    if not is_cannibal_prey(prey_key):
        return ""
    if action == "preypile":
        lead = "you laid **wolf flesh** at the fresh-kill cache for everyone to see."
    elif action == "feedall":
        lead = "You served **wolf flesh** to the whole den at communal feed."
    else:
        lead = "You put **wolf flesh** in the pack food reserve."
    return lead + _apply_caught_penalty(user)


def cannibalism_eat_consequences(user, prey_key: str) -> str:
    """private /eat or feedall bite; always costs mood; roll whether anyone notices."""
    if not is_cannibal_prey(prey_key):
        return ""
    db.adjust_mood(user["id"], -CANNIBALISM_EAT_MOOD_PENALTY)
    msg = f"\nthe taste lingers; mood **−{CANNIBALISM_EAT_MOOD_PENALTY}**."
    from engine.disease_contract import try_contract_disease

    filth_roll = random.random()
    if filth_roll < 0.18:
        sick = try_contract_disease(user, "hepatitis", chance=1.0)
        if sick:
            msg += f"\nwolf flesh carries rot in the gut; {sick}"
    elif filth_roll < 0.24:
        sick = try_contract_disease(user, "wasting_sickness", "waning", chance=1.0)
        if sick:
            msg += f"\nsomething wrong settles in the marrow; {sick}"
    if random.randint(1, 100) > CANNIBALISM_CAUGHT_CHANCE:
        return msg
    if not user["pack_id"]:
        return msg + "\n_no clan saw it; but the taste stays with you._"
    db.adjust_wolf_standing_by_id(user["id"], -CANNIBALISM_STANDING_PENALTY)
    extra_mood = CANNIBALISM_MOOD_PENALTY - CANNIBALISM_EAT_MOOD_PENALTY
    if extra_mood > 0:
        db.adjust_mood(user["id"], -extra_mood)
    return (
        msg
        + f"\n**caught.** a patrol saw you tear into a wolf. "
        f"standing **−{CANNIBALISM_STANDING_PENALTY}** · mood **−{CANNIBALISM_MOOD_PENALTY}** total."
    )
