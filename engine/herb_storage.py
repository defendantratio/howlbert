# herb_storage.py
"""Herb inventory helpers (foraged herbs live in `/bones action:inventory`)."""

from __future__ import annotations

import database as db
from config import (
    HERB_DRIED_STORAGE_DAYS,
    HERB_FRESH_DRY_DAYS,
    HERB_PREPARED_STORAGE_DAYS,
)
from engine.herb_buffs import herb_storage_multiplier
from herbs import herb_inventory_key


def effective_storage_limits(user, day: int) -> tuple[int, int, int]:
    """Return (fresh_days, prepared_days, dried_days) after storage buff multiplier."""
    mult = herb_storage_multiplier(user, day)
    fresh = max(1, int(HERB_FRESH_DRY_DAYS * mult))
    prepared = max(1, int(HERB_PREPARED_STORAGE_DAYS * mult))
    dried = max(1, int(HERB_DRIED_STORAGE_DAYS * mult))
    return fresh, prepared, dried


def grant_fresh_herb(
    wolf_id: int,
    *,
    herb_key: str,
    guild_id: int,
    day: int,
    form: str = "fresh",
    user=None,
    conn=None,
) -> tuple[str, str]:
    """Grant a foraged herb to inventory; returns (item_key, restricted-hoard note if any)."""
    _ = (guild_id, day, form)
    if user is None:
        user = db.get_user_by_id(wolf_id)
    if not user:
        return "", "unknown wolf."
    item_key = herb_inventory_key(herb_key)
    item = db.get_item_by_key(item_key)
    if not item:
        return "", "unknown herb item."
    db.grant_item(user["discord_id"], item["id"], quantity=1, conn=conn)
    hoard_note = ""
    from engine.restricted_herbs import on_restricted_herb_acquired

    hoard_note = on_restricted_herb_acquired(user, herb_key)
    return item_key, hoard_note


def parse_herb_stack_id(raw: str | None) -> int | None:
    """legacy stack ids (deprecated; herb bag removed)."""
    if not raw:
        return None
    text = raw.strip()
    lower = text.lower()
    if lower.startswith("stack:"):
        text = text.split(":", 1)[1].strip()
    elif text.startswith("#"):
        text = text[1:].strip()
    if not text.isdigit():
        return None
    return int(text)


def inventory_herb_count(user) -> int:
    return sum(
        int(row["quantity"])
        for row in db.get_inventory(user["discord_id"])
        if row["key"].startswith("herb_") or row["key"] == "stick"
    )


def list_inventory_herb_summary(discord_id: int) -> str:
    rows = [
        row
        for row in db.get_inventory(discord_id)
        if row["key"].startswith("herb_") or row["key"] == "stick"
    ]
    if not rows:
        return "no herbs in `/bones action:inventory`; gather with `/field action:forage` or `action:verge`."
    lines = []
    for row in rows:
        lines.append(f"`{row['key']}` **{row['name']}** ×**{row['quantity']}**")
    return "\n".join(lines)


def herb_inventory_footer() -> str:
    return (
        "/herbs action:prepare · action:dryall · `/bones action:sell item:herb_arnica` · "
        "/medic action:treat herb:herb_arnica"
    )


def has_yarrow(user) -> bool:
    item = db.get_item_by_key("herb_yarrow")
    return bool(item and db.get_inventory_quantity(user["discord_id"], item["id"]) > 0)


def consume_yarrow_from_bag(user) -> bool:
    """Consume one yarrow from inventory."""
    item = db.get_item_by_key("herb_yarrow")
    if item and db.get_inventory_quantity(user["discord_id"], item["id"]) > 0:
        db.consume_item(user["discord_id"], item["id"], quantity=1)
        return True
    return False


def fresh_herb_warning(herb_key: str) -> str:
    from engine.herb_properties import herb_form_rule

    rule = herb_form_rule(herb_key)
    if not rule.toxic_if_fresh and not rule.must_dry_before_use and not rule.requires_poultice:
        return ""
    bits = []
    if rule.toxic_if_fresh:
        bits.append("**toxic if eaten fresh**")
    if rule.must_dry_before_use:
        bits.append("**must dry** within 1 sunrise")
    if rule.requires_poultice:
        bits.append("best as **poultice**")
    note = rule.notes or ""
    return f"\n_⚠ {' · '.join(bits)}.{(' ' + note) if note else ''}_"