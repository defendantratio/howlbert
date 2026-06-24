"""Pack den toy store; any wolf may deposit toys for communal play."""

from __future__ import annotations

import database as db
from engine.amusement_items import amusement_meta
from engine.amusement_storage import format_amusement_line


def format_pack_amusement_line(stack) -> str:
    meta = amusement_meta(stack["item_key"])
    return (
        f"`#{stack['id']}` **{meta['name']}**; "
        f"{stack['uses_left']}/{meta['uses']} uses · **den toy store**"
    )


def list_pack_amusement_store(pack_id: int) -> str:
    stacks = db.get_pack_amusement_stacks(pack_id)
    if not stacks:
        return (
            "No toys in the **den toy store**; "
            "deposit with `/playpen action:toystore mode:deposit` or `mode:depositall`."
        )
    return "\n".join(format_pack_amusement_line(s) for s in stacks)


def _deposit_amusement_stack_to_store(
    user,
    stack_id: int,
    *,
    pack_id: int,
    guild_id: int,
) -> tuple[bool, str]:
    stack = db.get_amusement_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "You don't carry that toy."
    if stack["uses_left"] <= 0:
        return False, "That toy is worn out."
    meta = amusement_meta(stack["item_key"])
    db.add_pack_amusement_stack(
        pack_id,
        stack["item_key"],
        uses_left=int(stack["uses_left"]),
        guild_id=guild_id,
        deposited_by=user["id"],
    )
    db.remove_amusement_stack(stack_id)
    return (
        True,
        f"**{meta['name']}** added to the den toy store "
        f"(`/playpen action:toystore mode:list`).",
    )


def deposit_amusement_to_store(
    user,
    stack_id: int,
    *,
    pack_id: int,
    guild_id: int,
) -> tuple[bool, str]:
    if not user["pack_id"] or int(user["pack_id"]) != pack_id:
        return False, "You must be in this pack to deposit toys."
    return _deposit_amusement_stack_to_store(
        user, stack_id, pack_id=pack_id, guild_id=guild_id
    )


def deposit_all_amusement_to_store(
    user,
    *,
    pack_id: int,
    guild_id: int,
) -> tuple[bool, str]:
    if not user["pack_id"] or int(user["pack_id"]) != pack_id:
        return False, "You must be in this pack to deposit toys."
    stacks = db.get_amusement_stacks(user["id"])
    if not stacks:
        return False, "You aren't carrying any toys (`/playpen action:toys`)."
    stack_ids = [int(s["id"]) for s in stacks if int(s["uses_left"]) > 0]
    if not stack_ids:
        return False, "Your toys are all worn out."

    deposited = 0
    names: list[str] = []
    for stack_id in stack_ids:
        ok, msg = _deposit_amusement_stack_to_store(
            user,
            stack_id,
            pack_id=pack_id,
            guild_id=guild_id,
        )
        if ok:
            deposited += 1
            if "**" in msg:
                names.append(msg.split("**")[1])
    if deposited == 0:
        return False, "Nothing could be deposited."

    summary = ", ".join(names[:8])
    if len(names) > 8:
        summary += f", _…and {len(names) - 8} more_"
    return True, f"**{deposited}** toy(s) added to the den store: {summary}."


def withdraw_amusement_from_store(
    user,
    store_id: int,
    *,
    pack_id: int,
) -> tuple[bool, str]:
    stack = db.get_pack_amusement_stack(store_id)
    if not stack or stack["pack_id"] != pack_id:
        return False, "That toy isn't in your pack's den store."
    if stack["uses_left"] <= 0:
        return False, "That store toy is spent."
    meta = amusement_meta(stack["item_key"])
    db.add_amusement_stack(user["id"], stack["item_key"], uses_left=int(stack["uses_left"]))
    db.remove_pack_amusement_stack(store_id)
    return True, f"**{meta['name']}** moved to your toys (`/playpen action:toys`)."
