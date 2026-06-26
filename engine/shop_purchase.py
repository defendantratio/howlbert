"""Buy prey carcasses and toys from the trading post with bones."""

from __future__ import annotations

import database as db
from engine.amusement_items import amusement_meta
from engine.amusement_storage import grant_amusement
from engine.prey_items import prey_meta
from engine.prey_storage import grant_prey_carcass


def purchase_shop_item(
    discord_id: int,
    item_key: str,
    *,
    guild_id: int | None,
    day: int,
) -> tuple[bool, str, str]:
    """
    Deduct bones and deliver a shop item.
    Returns (ok, user_message, item_name).
    """
    shop_item = db.get_item_by_key(item_key)
    if not shop_item or shop_item["price"] <= 0:
        return False, "That item isn't for sale; check `/bones action:shop`.", ""

    price = int(shop_item["price"])
    user = db.get_user(discord_id)
    if not user:
        return False, "Use `/register` first.", ""
    if user["bones"] < price:
        return False, "Not enough bones.", shop_item["name"]

    key = shop_item["key"]

    if key.startswith("prey_"):
        if not guild_id:
            return False, "Buy food in a server channel (carcasses go to your hoard).", shop_item["name"]
        prey_key = key.removeprefix("prey_")
        meta = prey_meta(prey_key)
        if not db.deduct_bones(discord_id, price):
            return False, "Purchase failed.", shop_item["name"]
        grant_prey_carcass(
            user["id"],
            prey_key,
            guild_id=guild_id,
            acquired_day=day,
            bone_value=meta["bones"],
        )
        return True, f"**{meta['name']}** added to your hoard (`/prey`).", shop_item["name"]

    if key.startswith("toy_"):
        if not guild_id:
            return False, "Buy toys in a server channel (they go to your active wolf).", shop_item["name"]
        toy_key = key.removeprefix("toy_")
        meta = amusement_meta(toy_key)
        if not db.deduct_bones(discord_id, price):
            return False, "Purchase failed.", shop_item["name"]
        grant_amusement(user["id"], toy_key)
        return True, f"**{meta['name']}** added to your toys (`/playpen action:toys` · `/playpen`).", shop_item["name"]

    if not db.buy_item(discord_id, shop_item["id"], price):
        return False, "Purchase failed.", shop_item["name"]
    return True, f"**{shop_item['name']}** added to `/bones action:inventory`.", shop_item["name"]
