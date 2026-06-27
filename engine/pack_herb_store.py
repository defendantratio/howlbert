"""Pack den herb store; medics and foragers deposit inventory herbs for the healers' den."""

from __future__ import annotations

import database as db
from engine.herb_properties import form_label
from engine.role_privileges import is_forager, is_medic
from herbs import HERBS, herb_inventory_key


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
            "no herbs in the **healers' store**; "
            "any wolf may `/herbs action:store mode:deposit` or `mode:depositall` "
            "from `/bones action:inventory`; "
            "fresh store herbs: `/herbs action:dryall`; "
            "use `/herbs action:turnin` for restricted poison herbs.\n\n"
            "_Withdraw: **Medics** and **Foragers** only (`/herbs action:store mode:withdraw`)._"
        )
    lines = "\n".join(format_pack_herb_line(s, day) for s in stacks)
    return (
        f"{lines}\n\n"
        "_withdraw: **medics** and **foragers** only · anyone may deposit or turn in poison herbs._"
    )


def count_depositable_inventory_herbs(user) -> int:
    from engine.restricted_herbs import is_restricted_herb

    total = 0
    for row in db.get_inventory(user["discord_id"]):
        key = row["key"]
        if not key.startswith("herb_"):
            continue
        herb_key = key.replace("herb_", "", 1)
        if is_restricted_herb(herb_key):
            continue
        total += int(row["quantity"])
    return total


def deposit_inventory_herb_to_store(
    user,
    item_key: str,
    *,
    pack_id: int,
    guild_id: int,
    day: int,
) -> tuple[bool, str]:
    if not user["pack_id"] or int(user["pack_id"]) != pack_id:
        return False, "you must be in this pack to deposit herbs."
    key = item_key.strip().lower()
    if not key.startswith("herb_"):
        return False, "use an inventory herb key like **`herb_arnica`**."
    herb_key = key.replace("herb_", "", 1)
    if herb_key not in HERBS:
        return False, "that herb isn't in the compendium."
    from engine.restricted_herbs import is_restricted_herb

    if is_restricted_herb(herb_key):
        return False, "restricted poison herbs use `/herbs action:turnin`."
    item = db.get_item_by_key(key)
    if not item:
        return False, "unknown herb item."
    if db.get_inventory_quantity(user["discord_id"], item["id"]) < 1:
        return False, f"you don't have **{item['name']}** in `/bones action:inventory`."
    if not db.consume_item(user["discord_id"], item["id"], quantity=1):
        return False, "could not use herb from `/bones action:inventory`."
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
        return False, "you must be in this pack to deposit herbs."
    from engine.restricted_herbs import is_restricted_herb

    inventory_herbs = [
        (row["key"], row["name"], int(row["quantity"]))
        for row in db.get_inventory(user["discord_id"])
        if row["key"].startswith("herb_")
    ]
    inventory_count = sum(
        qty for key, _, qty in inventory_herbs if not is_restricted_herb(key.replace("herb_", "", 1))
    )
    skipped_restricted = sum(
        qty for key, _, qty in inventory_herbs if is_restricted_herb(key.replace("herb_", "", 1))
    )
    if inventory_count == 0:
        if skipped_restricted:
            return (
                False,
                "only **restricted poison** herbs remain; use `/herbs action:turnin` for those.",
            )
        return (
            False,
            "no herbs to deposit in `/bones action:inventory`.",
        )

    deposited = 0
    names: list[str] = []
    for item_key, name, qty in inventory_herbs:
        herb_key = item_key.replace("herb_", "", 1)
        if is_restricted_herb(herb_key):
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
        return False, "nothing could be deposited."

    summary = ", ".join(names[:8])
    if len(names) > 8:
        summary += f", _…and {len(names) - 8} more_"
    note = f"\n\n_{skipped_restricted} restricted herb(s) left; `/herbs action:turnin`._" if skipped_restricted else ""
    return True, f"**{deposited}** herb(s) added to the healers' store: {summary}.{note}"


def withdraw_herb_from_store(
    user,
    store_id: int,
    *,
    pack_id: int,
    guild_id: int,
    day: int,
) -> tuple[bool, str]:
    if not can_manage_den_herbs(user):
        return False, "only **medics** and **foragers** may take from the healers' store."
    stack = db.get_pack_herb_stack(store_id)
    if not stack or stack["pack_id"] != pack_id:
        return False, "that stack isn't in your pack's herb store."
    qty = int(stack["quantity"])
    if qty <= 0:
        return False, "that store entry is empty."
    item_key = herb_inventory_key(stack["herb_key"])
    item = db.get_item_by_key(item_key)
    if not item:
        return False, "unknown herb item."
    db.grant_item(user["discord_id"], item["id"], quantity=1)
    if qty <= 1:
        db.remove_pack_herb_stack(store_id)
    else:
        db.update_pack_herb_stack(store_id, quantity=qty - 1)
    meta = HERBS.get(stack["herb_key"], {})
    name = meta.get("name", stack["herb_key"])
    from engine.restricted_herbs import on_restricted_herb_acquired

    hoard_note = on_restricted_herb_acquired(user, stack["herb_key"])
    msg = f"**{name}** moved to `/bones action:inventory`."
    if hoard_note:
        msg = f"{msg}\n\n{hoard_note}"
    return True, msg


def turnin_restricted_herb(
    user,
    item_key: str,
    *,
    pack_id: int,
    guild_id: int,
    day: int,
) -> tuple[bool, str]:
    """Any packmate may turn restricted poison herbs in from inventory."""
    if not user["pack_id"] or int(user["pack_id"]) != pack_id:
        return False, "you must be in this pack to turn herbs in."
    key = item_key.strip().lower()
    if not key.startswith("herb_"):
        return False, "use an inventory herb key like **`herb_wolfsbane`**."
    herb_key = key.replace("herb_", "", 1)
    from config import RESTRICTED_HERB_TURNIN_BONES, RESTRICTED_HERB_TURNIN_STANDING
    from engine.restricted_herbs import is_restricted_herb

    if not is_restricted_herb(herb_key):
        return (
            False,
            "only **restricted poison** herbs use turn-in. "
            "medics/foragers stock other herbs via `/herbs action:store mode:deposit` or `mode:depositall`.",
        )
    item = db.get_item_by_key(key)
    if not item or db.get_inventory_quantity(user["discord_id"], item["id"]) < 1:
        return False, f"you don't have **{herb_key.replace('_', ' ').title()}** in `/bones action:inventory`."
    if not db.consume_item(user["discord_id"], item["id"], quantity=1):
        return False, "could not use herb from inventory."
    meta = HERBS.get(herb_key, {})
    name = meta.get("name", herb_key)
    db.add_pack_herb_stack(
        pack_id,
        herb_key,
        form="fresh",
        potency=100,
        quantity=1,
        acquired_day=day,
        guild_id=guild_id,
        deposited_by=user["id"],
    )
    kick = db.adjust_wolf_standing_by_id(user["id"], RESTRICTED_HERB_TURNIN_STANDING)
    kick_note = " you were **cast out** of the pack." if kick == "kicked" else ""
    db.add_bones(user["discord_id"], RESTRICTED_HERB_TURNIN_BONES, wolf_id=user["id"])
    return (
        True,
        f"**{name}** turned in to the healers' store; "
        f"**+{RESTRICTED_HERB_TURNIN_BONES}🦴** bounty.{kick_note}",
    )
