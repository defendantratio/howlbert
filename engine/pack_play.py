"""Pack-wide play session; FAPA-style mood boost for the whole den."""

from __future__ import annotations

import database as db
from config import PLAYALL_MOOD_GAIN
from engine.amusement_items import amusement_meta
from engine.pack_leadership import PACK_BULK_ALPHA_ONLY_MSG, can_run_pack_bulk_action


def run_playall(
    user,
    pack_id: int,
    day: int,
    *,
    discord_admin: bool = False,
) -> tuple[bool, str]:
    pack = db.get_pack(pack_id)
    if not can_run_pack_bulk_action(user, pack, discord_admin=discord_admin):
        return False, PACK_BULK_ALPHA_ONLY_MSG
    if int(user["last_playall_day"]) >= day:
        return False, "You already rallied the den to play this sunrise."

    from_pack = False
    stacks = db.get_amusement_stacks(user["id"])
    if stacks:
        stack = stacks[0]
    else:
        pack_stacks = db.get_pack_amusement_stacks(pack_id)
        if not pack_stacks:
            return (
                False,
                "You need a toy (`/playpen action:toys`) or one in the **den toy store** "
                "(`/playpen action:toystore mode:depositall`).",
            )
        stack = pack_stacks[0]
        from_pack = True

    meta = amusement_meta(stack["item_key"])
    uses_left = int(stack["uses_left"]) - 1
    if uses_left <= 0:
        if from_pack:
            db.remove_pack_amusement_stack(stack["id"])
        else:
            db.remove_amusement_stack(stack["id"])
        toy_note = f"The den's **{meta['name']}** falls apart leading the romp."
    else:
        if from_pack:
            db.update_pack_amusement_stack_uses(stack["id"], uses_left)
        else:
            db.update_amusement_stack_uses(stack["id"], uses_left)
        source = "den toy store" if from_pack else "your hoard"
        toy_note = f"**{meta['name']}** ({source}); **{uses_left}** uses left."

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
