"""Pack den herb store; medics and foragers deposit forage stacks for the healers' den."""

from __future__ import annotations

import database as db
from engine.herb_properties import form_label
from engine.role_privileges import is_forager, is_medic
from herbs import HERBS


def can_manage_den_herbs(user) -> bool:
    return is_medic(user) or is_forager(user)


def format_pack_herb_line(stack, current_day: int) -> str:
    meta = HERBS.get(stack["herb_key"], {})
    name = meta.get("name", stack["herb_key"].replace("_", " ").title())
    form = form_label(stack["form"])
    qty = int(stack["quantity"])
    return f"`#{stack['id']}` **{name}** ({form}) ×**{qty}** · den herb store"


def list_pack_herb_store(pack_id: int, day: int) -> str:
    stacks = db.get_pack_herb_stacks(pack_id)
    if not stacks:
        return (
            "No herbs in the **healers' store**; "
            "Medics/Foragers deposit with `/vitals action:denstore mode:deposit`; "
            "any wolf may `/vitals action:turnin` restricted poison herbs."
        )
    return "\n".join(format_pack_herb_line(s, day) for s in stacks)


def deposit_herb_to_store(
    user,
    stack_id: int,
    *,
    pack_id: int,
    guild_id: int,
    day: int,
) -> tuple[bool, str]:
    if not can_manage_den_herbs(user):
        return False, "Only **Medics** and **Foragers** may stock the healers' den store."
    stack = db.get_herb_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "That herb isn't in your forage bag."
    meta = HERBS.get(stack["herb_key"], {})
    name = meta.get("name", stack["herb_key"])
    db.add_pack_herb_stack(
        pack_id,
        stack["herb_key"],
        form=stack["form"],
        potency=int(stack["potency"]),
        quantity=1,
        acquired_day=int(stack["acquired_day"]),
        guild_id=guild_id,
        deposited_by=user["id"],
    )
    db.remove_herb_stack(stack_id)
    return True, f"**{name}** ({form_label(stack['form'])}) added to the den herb store (`/vitals action:denstore mode:list`)."


def withdraw_herb_from_store(
    user,
    store_id: int,
    *,
    pack_id: int,
    guild_id: int,
    day: int,
) -> tuple[bool, str]:
    if not can_manage_den_herbs(user):
        return False, "Only **Medics** and **Foragers** may take from the healers' store."
    stack = db.get_pack_herb_stack(store_id)
    if not stack or stack["pack_id"] != pack_id:
        return False, "That stack isn't in your pack's herb store."
    qty = int(stack["quantity"])
    if qty <= 0:
        return False, "That store entry is empty."
    db.add_herb_stack(
        user["id"],
        stack["herb_key"],
        guild_id=guild_id,
        acquired_day=day,
        form=stack["form"],
        potency=int(stack["potency"]),
    )
    if qty <= 1:
        db.remove_pack_herb_stack(store_id)
    else:
        db.update_pack_herb_stack(store_id, quantity=qty - 1)
    meta = HERBS.get(stack["herb_key"], {})
    name = meta.get("name", stack["herb_key"])
    from engine.restricted_herbs import on_restricted_herb_acquired

    hoard_note = on_restricted_herb_acquired(user, stack["herb_key"])
    msg = f"**{name}** moved to your herb bag (`/vitals action:herbbag`)."
    if hoard_note:
        msg = f"{msg}\n\n{hoard_note}"
    return True, msg


def turnin_restricted_herb(
    user,
    stack_id: int,
    *,
    pack_id: int,
    guild_id: int,
    day: int,
) -> tuple[bool, str]:
    """Any packmate may turn restricted poison herbs in to the healers' store (Warriors medicine-cat handoff)."""
    if not user["pack_id"] or int(user["pack_id"]) != pack_id:
        return False, "You must be in this pack to turn herbs in."
    stack = db.get_herb_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "That herb isn't in your forage bag."
    from config import RESTRICTED_HERB_TURNIN_BONES, RESTRICTED_HERB_TURNIN_STANDING
    from engine.restricted_herbs import is_restricted_herb

    if not is_restricted_herb(stack["herb_key"]):
        return (
            False,
            "Only **restricted poison** herbs use turn-in. "
            "Medics/Foragers stock other herbs via `/vitals action:denstore mode:deposit`.",
        )
    meta = HERBS.get(stack["herb_key"], {})
    name = meta.get("name", stack["herb_key"])
    db.add_pack_herb_stack(
        pack_id,
        stack["herb_key"],
        form=stack["form"],
        potency=int(stack["potency"]),
        quantity=1,
        acquired_day=int(stack["acquired_day"]),
        guild_id=guild_id,
        deposited_by=user["id"],
    )
    db.remove_herb_stack(stack_id)
    kick = db.adjust_wolf_standing_by_id(user["id"], RESTRICTED_HERB_TURNIN_STANDING)
    kick_note = " You were **cast out** of the pack." if kick == "kicked" else ""
    bone_note = ""
    if db.deduct_pack_treasury(pack_id, RESTRICTED_HERB_TURNIN_BONES):
        db.add_bones(user["discord_id"], RESTRICTED_HERB_TURNIN_BONES, wolf_id=user["id"])
        bone_note = f" Pack treasury paid **{RESTRICTED_HERB_TURNIN_BONES}🦴**."
    else:
        bone_note = " Pack treasury was empty; no bone bounty this time."
    return True, (
        f"**{name}** ({form_label(stack['form'])}) handed to the healers' den "
        f"(`/vitals action:denstore mode:list`).\n"
        f"Standing **+{RESTRICTED_HERB_TURNIN_STANDING}** for obeying Medicine law.{bone_note}{kick_note}"
    )
