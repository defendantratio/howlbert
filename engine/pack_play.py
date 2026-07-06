"""Pack-wide play session; FAPA-style mood boost for the whole den."""

from __future__ import annotations

import random

import database as db
from config import PLAYALL_MOOD_GAIN
from engine.amusement_items import amusement_meta
from engine.disease_contract import try_den_filth_exposure
from engine.pack_leadership import PACK_BULK_ALPHA_ONLY_MSG, can_run_pack_bulk_action

PLAYALL_FILTH_CHANCE = 0.08


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

    # unlimited; each repeat romp the same sunrise gives less mood (the den tires
    # of the same game), instead of a hard once-per-sunrise block.
    from engine.diminishing import multiplier_for_use, record_use, use_count_today
    play_repeat = use_count_today(user, "playall", day)
    play_mult = multiplier_for_use(play_repeat + 1)
    mood_gain = PLAYALL_MOOD_GAIN if play_mult >= 1.0 else max(1, int(PLAYALL_MOOD_GAIN * play_mult))

    members = db.get_pack_den_wolves(pack_id)
    if not members:
        return False, "no wolves in the den."

    from_pack = False
    stacks = [s for s in db.get_amusement_stacks(user["id"]) if int(s["uses_left"]) > 0]
    if stacks:
        stack = stacks[0]
    else:
        pack_stacks = [
            s for s in db.get_pack_amusement_stacks(pack_id) if int(s["uses_left"]) > 0
        ]
        if not pack_stacks:
            return (
                False,
                "you need a toy (`/playpen action:toys`) or one in the **den toy store** "
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
        toy_note = f"the den's **{meta['name']}** falls apart leading the romp."
    else:
        if from_pack:
            db.update_pack_amusement_stack_uses(stack["id"], uses_left)
        else:
            db.update_amusement_stack_uses(stack["id"], uses_left)
        source = "den toy store" if from_pack else "your hoard"
        worn = " · _last use_" if uses_left == 1 else ""
        toy_note = f"**{meta['name']}** ({source}); **{uses_left}/{meta['uses']}** uses left{worn}."

    lines: list[str] = []
    filth_lines: list[str] = []
    for wolf in members:
        mood = db.adjust_mood(wolf["id"], mood_gain)
        lines.append(f"**{wolf['wolf_name']}** → **{mood}** mood")
        db.update_user_by_id(int(wolf["id"]), last_play_day=day)
        if random.random() < PLAYALL_FILTH_CHANCE:
            filth = try_den_filth_exposure(wolf, day=day)
            if filth:
                filth_lines.append(f"**{wolf['wolf_name']}** rolls in filth; {filth}")

    db.update_user(user["discord_id"], last_playall_day=day, wolf_id=user["id"])
    record_use(user, "playall", day)
    summary = "\n".join(lines[:15])
    if len(lines) > 15:
        summary += f"\n_…and {len(lines) - 15} more._"
    msg = (
        f"den romp! every packmate gains **+{mood_gain} mood**.\n"
        f"{summary}\n\n{toy_note}"
    )
    if play_repeat > 0:
        msg += f"\n_rallied {play_repeat + 1}x this sunrise; mood scaled to **{int(play_mult * 100)}%**._"
    if filth_lines:
        extra = "\n".join(filth_lines[:5])
        if len(filth_lines) > 5:
            extra += f"\n_…and {len(filth_lines) - 5} more caught the stink._"
        msg += f"\n\n{extra}"
    return True, msg
