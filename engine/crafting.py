"""Wolvden-style shred remnants (crafting recipes TBD)."""

from __future__ import annotations

import database as db
from engine.amusement_items import amusement_meta
from engine.amusement_storage import format_amusement_line


CRAFT_RECIPES: dict[str, dict] = {
    "bone_toy": {
        "name": "Bone Toy",
        "remnants": 8,
        "output_key": "bone",
        "uses": 3,
    },
    "stick_bundle": {
        "name": "Stick Bundle",
        "remnants": 6,
        "output_key": "stick",
        "uses": 4,
    },
}


def craft_from_remnants(user, recipe_key: str) -> tuple[bool, str]:
    recipe = CRAFT_RECIPES.get(recipe_key)
    if not recipe:
        return False, "unknown recipe."
    have = db.get_remnants(user["id"])
    cost = int(recipe["remnants"])
    if have < cost:
        return False, f"need **{cost}** remnants (you have **{have}**)."
    if not db.spend_remnants(user["id"], cost):
        return False, f"need **{cost}** remnants (you have **{have}**)."
    from engine.amusement_storage import grant_amusement

    grant_amusement(user["id"], recipe["output_key"])
    meta = amusement_meta(recipe["output_key"])
    left = db.get_remnants(user["id"])
    return (
        True,
        f"crafted **{recipe['name']}** → **{meta['name']}**. **{left}** remnants left (`/playpen action:toys`).",
    )


def shred_amusement_stack(user, stack_id: int) -> tuple[bool, str, int]:
    stack = db.get_amusement_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "you don't have that toy.", 0
    if stack["uses_left"] <= 0:
        return False, "nothing left to shred.", 0

    meta = amusement_meta(stack["item_key"])
    remnants = max(2, stack["uses_left"] * meta.get("shred_remnants", 2))
    db.remove_amusement_stack(stack_id)
    total = db.add_remnants(user["id"], remnants)
    return (
        True,
        f"shredded **{meta['name']}** into **{remnants}** remnants (total **{total}**).",
        remnants,
    )


def format_hoard_summary(user, *, day: int) -> str:
    from engine.prey_storage import format_prey_hoard_line

    lines: list[str] = []
    remnants = db.get_remnants(user["id"])
    lines.append(f"**remnants:** {remnants} _(shred toys; craft: bone toy **8**, stick bundle **6** via `/hoarding action:craft`)_")

    prey = db.get_prey_stacks(user["id"])
    if prey:
        lines.append("**prey**")
        lines.extend(format_prey_hoard_line(s, day) for s in prey[:8])
        if len(prey) > 8:
            lines.append(f"_…and {len(prey) - 8} more; `/food` for full list._")
    else:
        lines.append("**prey**; empty")

    toys = db.get_amusement_stacks(user["id"])
    if toys:
        lines.append("**toys**")
        lines.extend(format_amusement_line(s) for s in toys[:8])
        if len(toys) > 8:
            lines.append(f"_…and {len(toys) - 8} more; `/playpen action:toys` for full list._")
    else:
        lines.append("**toys**; empty")

    return "\n".join(lines)
