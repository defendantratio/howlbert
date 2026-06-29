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
    uses = int(stack["uses_left"])
    max_uses = meta["uses"]
    worn = " · _last use_" if uses == 1 else ""
    return f"`#{stack['id']}` **{meta['name']}**; {uses}/{max_uses} uses{worn}"


def play_amusement(user, stack_id: int, *, day: int | None = None) -> tuple[bool, str, int]:
    if day is not None:
        last = int(user["last_play_day"] if "last_play_day" in user.keys() else 0)
        if last >= day:
            return (
                False,
                "you already played with a toy this sunrise.\n\n"
                "_resets next sunrise · `/checklist`_",
                0,
            )
    stack = db.get_amusement_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "you don't have that toy.", 0
    if stack["uses_left"] <= 0:
        return False, "that toy is worn out.", 0

    meta = amusement_meta(stack["item_key"])
    mood_gain = meta["mood"]
    new_mood = db.adjust_mood(user["id"], mood_gain)
    uses_left = stack["uses_left"] - 1
    if uses_left <= 0:
        db.remove_amusement_stack(stack_id)
        uses_note = f"the **{meta['name']}** falls apart; spent."
    else:
        db.update_amusement_stack_uses(stack_id, uses_left)
        worn = " · _last use_" if uses_left == 1 else ""
        uses_note = f"**{uses_left}/{meta['uses']}** uses left{worn}."

    msg = (
        f"you bat **{meta['name']}** around the den; **+{mood_gain} mood** "
        f"(now **{new_mood}**).\n{uses_note}"
    )
    if random.random() < POOP_PLAY_CHANCE:
        filth = try_den_filth_exposure(user, day=day)
        if filth:
            msg += f"\n\nyou tumble into something foul. {filth}"
    return True, msg, mood_gain


def gift_amusement(user, stack_id: int, recipient) -> tuple[bool, str]:
    stack = db.get_amusement_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "you don't have that toy."
    if stack["uses_left"] <= 0:
        return False, "that toy is worn out."
    if recipient["id"] == user["id"]:
        return False, "you already carry it."

    meta = amusement_meta(stack["item_key"])
    if not db.transfer_amusement_stack(stack_id, recipient["id"]):
        return False, "couldn't pass the toy."
    return (
        True,
        f"you nudge **{meta['name']}** to **{recipient['wolf_name']}**; "
        f"it's in their `/playpen action:toys` now.",
    )
