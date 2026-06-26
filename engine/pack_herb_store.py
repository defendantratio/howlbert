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
            "any wolf may `/herbs action:store mode:deposit` or `mode:depositall` "
            "(forage bag + `/bones action:inventory` herbs); "
            "fresh stacks: `/herbs action:dryall`; "
            "use `/herbs action:turnin` for restricted poison herbs.\n\n"
            "_Withdraw: **Medics** and **Foragers** only (`/herbs action:store mode:withdraw`)._"
        )
    lines = "\n".join(format_pack_herb_line(s, day) for s in stacks)
    return (
        f"{lines}\n\n"
        "_Withdraw: **Medics** and **Foragers** only · anyone may deposit or turn in poison herbs._"
    )


def _deposit_herb_stack_to_store(
    user,
    stack_id: int,
    *,
    pack_id: int,
    guild_id: int,
) -> tuple[bool, str]:
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
    return True, f"**{name}** ({form_label(stack['form'])}) added to the den herb store (`/herbs action:store mode:list`)."


def deposit_herb_to_store(
    user,
    stack_id: int,
    *,
    pack_id: int,
    guild_id: int,
    day: int,
) -> tuple[bool, str]:
    if not user["pack_id"] or int(user["pack_id"]) != pack_id:
        return False, "You must be in this pack to deposit herbs."
    return _deposit_herb_stack_to_store(
        user, stack_id, pack_id=pack_id, guild_id=guild_id
    )


def deposit_inventory_herb_to_store(
    user,
    item_key: str,
    *,
    pack_id: int,
    guild_id: int,
    day: int,
) -> tuple[bool, str]:
    if not user["pack_id"] or int(user["pack_id"]) != pack_id:
        return False, "You must be in this pack to deposit herbs."
    key = item_key.strip().lower()
    if not key.startswith("herb_"):
        return False, "Use an inventory herb key like **`herb_arnica`**."
    herb_key = key.replace("herb_", "", 1)
    if herb_key not in HERBS:
        return False, "That herb isn't in the compendium."
    from engine.restricted_herbs import is_restricted_herb

    if is_restricted_herb(herb_key):
        return False, "Restricted poison herbs use `/herbs action:turnin`."
    item = db.get_item_by_key(key)
    if not item:
        return False, "Unknown herb item."
    if db.get_inventory_quantity(user["discord_id"], item["id"]) < 1:
        return False, f"You don't have **{item['name']}** in `/bones action:inventory`."
    if not db.consume_item(user["discord_id"], item["id"], quantity=1):
        return False, f"Could not use herb from `/bones action:inventory`."
    meta = HERBS.get(herb_key, {})
    name = meta.get("name", herb_key)
    db.add_pack_herb_stack(
        pack_id,
        herb_key,
        form="dried",
        potency=100,
        quantity=1,
        acquired_day=day,
        guild_id=guild_id,
        deposited_by=user["id"],
    )
    return (
        True,
        f"**{name}** (dried) from `/bones action:inventory` added to the den herb store "
        f"(`/herbs action:store mode:list`).",
    )


def deposit_all_herbs_to_store(
    user,
    *,
    pack_id: int,
    guild_id: int,
    day: int,
) -> tuple[bool, str]:
    if not user["pack_id"] or int(user["pack_id"]) != pack_id:
        return False, "You must be in this pack to deposit herbs."
    stacks = db.get_herb_stacks(user["id"])
    from engine.restricted_herbs import is_restricted_herb

    stack_ids = [int(s["id"]) for s in stacks if not is_restricted_herb(s["herb_key"])]
    skipped_restricted = sum(1 for s in stacks if is_restricted_herb(s["herb_key"]))
    inventory_herbs = [
        (row["key"], row["name"], int(row["quantity"]))
        for row in db.get_inventory(user["discord_id"])
        if row["key"].startswith("herb_")
    ]
    inventory_count = sum(
        qty for key, _, qty in inventory_herbs if not is_restricted_herb(key.replace("herb_", "", 1))
    )
    if not stack_ids and inventory_count == 0:
        if skipped_restricted or any(
            is_restricted_herb(k.replace("herb_", "", 1)) for k, _, _ in inventory_herbs
        ):
            return (
                False,
                "Only **restricted poison** herbs remain; use `/herbs action:turnin` for those.",
            )
        return (
            False,
            "No herbs to deposit in your **forage bag** (`/herbs action:bag`) "
            "or **inventory** (`/bones action:inventory`).",
        )

    deposited = 0
    names: list[str] = []
    for stack_id in stack_ids:
        ok, msg = _deposit_herb_stack_to_store(
            user,
            stack_id,
            pack_id=pack_id,
            guild_id=guild_id,
        )
        if ok:
            deposited += 1
            if "**" in msg:
                names.append(msg.split("**")[1])

    for item_key, name, qty in inventory_herbs:
        herb_key = item_key.replace("herb_", "", 1)
        if is_restricted_herb(herb_key):
            skipped_restricted += qty
            continue
        for _ in range(qty):
            ok, msg = deposit_inventory_herb_to_store(
                user,
                item_key,
                pack_id=pack_id,
                guild_id=guild_id,
                day=day,
            )
            if ok:
                deposited += 1
                names.append(name)
    if deposited == 0:
        return False, "Nothing could be deposited."

    summary = ", ".join(names[:8])
    if len(names) > 8:
        summary += f", _…and {len(names) - 8} more_"
    note = f"\n\n_{skipped_restricted} restricted stack(s) left; `/herbs action:turnin`._" if skipped_restricted else ""
    return True, f"**{deposited}** herb stack(s) added to the healers' store: {summary}.{note}"


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
    msg = f"**{name}** moved to your herb bag (`/herbs action:bag`)."
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
            "Medics/Foragers stock other herbs via `/herbs action:store mode:deposit` or `mode:depositall`.",
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
        f"(`/herbs action:store mode:list`).\n"
        f"Standing **+{RESTRICTED_HERB_TURNIN_STANDING}** for obeying Medicine law.{bone_note}{kick_note}"
    )
