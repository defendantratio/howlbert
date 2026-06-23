"""Pack-wide play session; FAPA-style mood boost for the whole den."""

from __future__ import annotations

import database as db
from config import PLAYALL_MOOD_GAIN
from engine.amusement_items import amusement_meta


def run_playall(user, pack_id: int, day: int) -> tuple[bool, str]:
    if int(user["last_playall_day"]) >= day:
        return False, "You already rallied the den to play this sunrise."
    stacks = db.get_amusement_stacks(user["id"])
    if not stacks:
        return False, "You need at least one toy (`/toys`) to start a den romp."

    stack = stacks[0]
    meta = amusement_meta(stack["item_key"])
    uses_left = stack["uses_left"] - 1
    if uses_left <= 0:
        db.remove_amusement_stack(stack["id"])
        toy_note = f"Your **{meta['name']}** falls apart leading the romp."
    else:
        db.update_amusement_stack_uses(stack["id"], uses_left)
        toy_note = f"**{meta['name']}**; **{uses_left}** uses left."

    members = db.get_pack_den_wolves(pack_id)
    if not members:
        return False, "No wolves in the den."

    lines: list[str] = []
    for wolf in members:
        mood = db.adjust_mood(wolf["id"], PLAYALL_MOOD_GAIN)
        lines.append(f"**{wolf['wolf_name']}** → **{mood}** mood")

    db.update_user(user["discord_id"], last_playall_day=day, wolf_id=user["id"])
    summary = "\n".join(lines[:15])
    if len(lines) > 15:
        summary += f"\n_…and {len(lines) - 15} more._"
    msg = (
        f"Den romp! Every packmate gains **+{PLAYALL_MOOD_GAIN} mood**.\n"
        f"{summary}\n\n{toy_note}"
    )
    return True, msg
