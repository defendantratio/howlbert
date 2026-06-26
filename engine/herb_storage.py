"""Fresh/dried/prepared herb stacks (foraged herbs)."""

from __future__ import annotations

import database as db
from config import (
    HERB_DRIED_STORAGE_DAYS,
    HERB_FRESH_DRY_DAYS,
    HERB_PREPARED_FORMS,
    HERB_PREPARED_STORAGE_DAYS,
)
from engine.herb_buffs import herb_storage_multiplier
from engine.herb_properties import form_label
from herbs import HERBS


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
) -> tuple[int, str]:
    """Add a herb stack; returns (stack_id, restricted-hoard standing note if any)."""
    stack_id = db.add_herb_stack(
        wolf_id,
        herb_key,
        guild_id=guild_id,
        acquired_day=day,
        form=form,
        conn=conn,
    )
    hoard_note = ""
    if user is None:
        user = db.get_user_by_id(wolf_id)
    if user:
        from engine.restricted_herbs import on_restricted_herb_acquired

        hoard_note = on_restricted_herb_acquired(user, herb_key)
    return stack_id, hoard_note


def parse_herb_stack_id(raw: str | None) -> int | None:
    """Accept stack:ID (autocomplete), #ID, or plain ID from herbbag."""
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


def format_herb_stack_line(stack, current_day: int, *, user=None) -> str:
    from engine.restricted_herbs import is_restricted_herb

    meta = HERBS.get(stack["herb_key"], {})
    name = meta.get("name", stack["herb_key"].replace("_", " ").title())
    if is_restricted_herb(stack["herb_key"]):
        name = f"⚠ {name}"
    form = form_label(stack["form"])
    potency = int(stack["potency"])
    age = current_day - int(stack["acquired_day"])
    fresh_note = ""
    if user is not None:
        fresh_lim, prep_lim, dried_lim = effective_storage_limits(user, current_day)
    else:
        fresh_lim, prep_lim, dried_lim = HERB_FRESH_DRY_DAYS, HERB_PREPARED_STORAGE_DAYS, HERB_DRIED_STORAGE_DAYS
    if stack["form"] == "fresh":
        left = fresh_lim - age
        if left <= 0:
            fresh_note = " · **spoiling**"
        else:
            fresh_note = f" · dry within **{left}** sunrise(s)"
    elif stack["form"] in HERB_PREPARED_FORMS:
        left = prep_lim - age
        if left <= 0:
            fresh_note = " · **spoiled**"
        else:
            fresh_note = f" · use within **{left}** sunrise(s)"
    elif stack["form"] == "dried":
        if age > dried_lim:
            fresh_note = " · faded"
        elif potency < 100:
            fresh_note = f" · potency **{potency}%**"
    return (
        f"`stack:{stack['id']}` **{name}** ({form}){fresh_note}"
    )


def list_herb_bag_summary(wolf_id: int, day: int) -> str:
    stacks = db.get_herb_stacks(wolf_id)
    if not stacks:
        return "No foraged herb stacks; gather with `/field action:forage` or `action:verge`."
    user = db.get_user_by_id(wolf_id)
    return "\n".join(format_herb_stack_line(s, day, user=user) for s in stacks)


def herb_bag_footer() -> str:
    return (
        "/herbs action:prepare · action:dryall · `/bones action:sell item:stack:ID` · "
        "/medic action:treat herb:stack:ID"
    )


def has_yarrow(user) -> bool:
    item = db.get_item_by_key("herb_yarrow")
    if item and db.get_inventory_quantity(user["discord_id"], item["id"]) > 0:
        return True
    for stack in db.get_herb_stacks(user["id"]):
        if stack["herb_key"] == "yarrow":
            return True
    return False


def consume_yarrow_from_bag(user) -> bool:
    """Consume one yarrow from forage stacks or shop inventory."""
    for stack in db.get_herb_stacks(user["id"]):
        if stack["herb_key"] == "yarrow":
            db.remove_herb_stack(stack["id"])
            return True
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
