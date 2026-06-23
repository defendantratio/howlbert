"""Grant and play amusement items (Wolvden hoard toys)."""

from __future__ import annotations

import random

import database as db
from engine.amusement_items import amusement_meta
from engine.disease_contract import try_den_filth_exposure


POOP_PLAY_CHANCE = 0.10


def grant_amusement(wolf_id: int, item_key: str) -> int:
    meta = amusement_meta(item_key)
    return db.add_amusement_stack(wolf_id, item_key, uses_left=meta["uses"])


def format_amusement_line(stack) -> str:
    meta = amusement_meta(stack["item_key"])
    return f"`#{stack['id']}` **{meta['name']}**; {stack['uses_left']}/{meta['uses']} uses"


def play_amusement(user, stack_id: int) -> tuple[bool, str, int]:
    stack = db.get_amusement_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "You don't have that toy.", 0
    if stack["uses_left"] <= 0:
        return False, "That toy is worn out.", 0

    meta = amusement_meta(stack["item_key"])
    mood_gain = meta["mood"]
    new_mood = db.adjust_mood(user["id"], mood_gain)
    uses_left = stack["uses_left"] - 1
    if uses_left <= 0:
        db.remove_amusement_stack(stack_id)
        uses_note = "The toy falls apart; spent."
    else:
        db.update_amusement_stack_uses(stack_id, uses_left)
        uses_note = f"**{uses_left}** uses left."

    msg = (
        f"You bat **{meta['name']}** around the den; **+{mood_gain} mood** "
        f"(now **{new_mood}**).\n{uses_note}"
    )
    if random.random() < POOP_PLAY_CHANCE:
        filth = try_den_filth_exposure(user)
        if filth:
            msg += f"\n\nYou tumble into something foul. {filth}"
    return True, msg, mood_gain


def gift_amusement(user, stack_id: int, recipient) -> tuple[bool, str]:
    stack = db.get_amusement_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "You don't have that toy."
    if stack["uses_left"] <= 0:
        return False, "That toy is worn out."
    if recipient["id"] == user["id"]:
        return False, "You already carry it."

    meta = amusement_meta(stack["item_key"])
    if not db.transfer_amusement_stack(stack_id, recipient["id"]):
        return False, "Couldn't pass the toy."
    return (
        True,
        f"You nudge **{meta['name']}** to **{recipient['wolf_name']}**; "
        f"it's in their `/toys` now.",
    )
