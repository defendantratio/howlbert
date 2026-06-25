"""Wolvden-style shred remnants (crafting recipes TBD)."""

from __future__ import annotations

import database as db
from engine.amusement_items import amusement_meta
from engine.amusement_storage import format_amusement_line


CRAFT_RECIPES: dict[str, dict] = {}


def shred_amusement_stack(user, stack_id: int) -> tuple[bool, str, int]:
    stack = db.get_amusement_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "You don't have that toy.", 0
    if stack["uses_left"] <= 0:
        return False, "Nothing left to shred.", 0

    meta = amusement_meta(stack["item_key"])
    remnants = max(2, stack["uses_left"] * meta.get("shred_remnants", 2))
    db.remove_amusement_stack(stack_id)
    total = db.add_remnants(user["id"], remnants)
    return (
        True,
        f"Shredded **{meta['name']}** into **{remnants}** remnants (total **{total}**).",
        remnants,
    )


def format_hoard_summary(user, *, day: int) -> str:
    from engine.prey_storage import format_prey_hoard_line

    lines: list[str] = []
    remnants = db.get_remnants(user["id"])
    lines.append(f"**Remnants:** {remnants} _(from `/hoarding action:shred`; save for future crafts)_")

    prey = db.get_prey_stacks(user["id"])
    if prey:
        lines.append("**Prey**")
        lines.extend(format_prey_hoard_line(s, day) for s in prey[:8])
        if len(prey) > 8:
            lines.append(f"_…and {len(prey) - 8} more; `/prey` for full list._")
    else:
        lines.append("**Prey**; empty")

    toys = db.get_amusement_stacks(user["id"])
    if toys:
        lines.append("**Toys**")
        lines.extend(format_amusement_line(s) for s in toys[:8])
        if len(toys) > 8:
            lines.append(f"_…and {len(toys) - 8} more; `/playpen action:toys` for full list._")
    else:
        lines.append("**Toys**; empty")

    return "\n".join(lines)
