"""UnbelievaBoat-style trading post sales for foraged herb stacks."""

from __future__ import annotations

import database as db
from config import HERB_FORAGE_SELL_BONES
from engine.herb_properties import form_label
from engine.restricted_herbs import is_restricted_herb
from herbs import HERBS


def forage_herb_sell_price(herb_key: str, *, form: str, potency: int, spoiling: bool) -> int:
    meta = HERBS.get(herb_key, {})
    rarity = meta.get("rarity", "common")
    if is_restricted_herb(herb_key):
        return 0
    base = HERB_FORAGE_SELL_BONES.get(rarity, HERB_FORAGE_SELL_BONES.get("common", 4))
    if form == "dried" and potency < 100:
        base = max(1, int(base * potency / 100))
    elif form in ("poultice", "tonic", "decoction"):
        base = max(base, base + 2)
    if spoiling:
        base = max(1, base // 2)
    return base


def sell_forage_herb_stack(
    user,
    stack_id: int,
    *,
    day: int,
) -> tuple[bool, str, int]:
    """
    Sell one forage stack at the trading post for bones.
    Returns (ok, message, bones_paid).
    """
    stack = db.get_herb_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "That herb isn't in your forage bag.", 0
    herb_key = stack["herb_key"]
    if is_restricted_herb(herb_key):
        return (
            False,
            "The trading post won't buy **restricted poison** herbs. "
            "Use `/herbs action:turnin` for a pack bounty instead.",
            0,
        )
    spoiling = stack["form"] == "fresh" and day - int(stack["acquired_day"]) >= 1
    price = forage_herb_sell_price(
        herb_key,
        form=stack["form"],
        potency=int(stack["potency"]),
        spoiling=spoiling,
    )
    if price <= 0:
        return False, "The den won't buy that herb back.", 0
    meta = HERBS.get(herb_key, {})
    name = meta.get("name", herb_key)
    db.remove_herb_stack(stack_id)
    db.add_bones(user["discord_id"], price, wolf_id=user["id"])
    spoil_note = " (spoiling; half price)" if spoiling else ""
    return (
        True,
        f"Sold **{name}** ({form_label(stack['form'])}) at the trading post for **{price}🦴**{spoil_note}.",
        price,
    )
