"""Herb preparation; dry, poultice, tonic, decoction."""

from __future__ import annotations

import random

import database as db
from config import HERB_PREP_DC
from engine.character import parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from engine.herb_properties import herb_form_rule
from engine.role_features import is_full_medic
from herbs import HERBS


PREP_FORMS = ("dry", "poultice", "tonic", "decoction")


def _herblore_proficient(user) -> bool:
    profs = parse_proficiencies(user["skill_proficiencies"])
    return "herblore" in profs or "medicine" in profs or is_full_medic(user)


def _prep_dc(method: str, user, herb_key: str) -> int:
    if method == "poultice" and is_full_medic(user):
        return HERB_PREP_DC["poultice_simple"]
    if method == "dry":
        return HERB_PREP_DC["dry"]
    if method == "tonic":
        return HERB_PREP_DC["tonic"]
    if method == "decoction":
        return HERB_PREP_DC["decoction"]
    return HERB_PREP_DC.get(method, 10)


def _target_form(method: str) -> str:
    return {
        "dry": "dried",
        "poultice": "poultice",
        "tonic": "tonic",
        "decoction": "decoction",
    }[method]


def prepare_herb_stack(
    user,
    stack_id: int,
    method: str,
    *,
    day: int,
    at_den: bool = False,
) -> tuple[bool, str]:
    if method not in PREP_FORMS:
        return False, "Use **dry**, **poultice**, **tonic**, or **decoction**."
    stack = db.get_herb_stack(stack_id)
    if not stack or stack["wolf_id"] != user["id"]:
        return False, "That herb isn't in your forage bag."
    herb_key = stack["herb_key"]
    meta = HERBS.get(herb_key, {})
    rule = herb_form_rule(herb_key)
    if method == "decoction" and not at_den:
        pass  # wolves heat stones / den fire anywhere for decoction
    if stack["form"] != "fresh" and method == "dry":
        return False, "Only **fresh** herbs can be dried."
    if stack["form"] not in ("fresh", "dried") and method != "dry":
        return False, f"Already prepared as **{stack['form']}**."

    dc = _prep_dc(method, user, herb_key)
    result = resolve_check(
        user,
        attr_keys=("attr_int", "attr_wis"),
        skill="Herblore",
        dc=dc,
        proficient=_herblore_proficient(user),
        skill_key="herblore",
        game_day=day,
    )
    target = _target_form(method)

    if result["outcome"] == "critical_failure":
        db.remove_herb_stack(stack_id)
        return (
            False,
            format_roll_result(result)
            + f"\n\n**{meta.get('name', herb_key)}** ruined; batch spoiled.",
        )
    if not result["success"]:
        if method == "tonic":
            db.remove_herb_stack(stack_id)
            return (
                False,
                format_roll_result(result)
                + "\n\nContaminated tonic; patient would vomit; herb wasted.",
            )
        if method == "decoction":
            db.remove_herb_stack(stack_id)
            return False, format_roll_result(result) + "\n\nDecoction boiled over; batch ruined."
        if method == "dry":
            db.update_herb_stack(stack_id, potency=max(40, int(stack["potency"]) - 30))
            return (
                False,
                format_roll_result(result)
                + "\n\nPoor drying; **reduced potency** (still usable).",
            )
        return False, format_roll_result(result) + "\n\nPreparation failed; try again."

    potency = 100
    if method == "dry" and result["outcome"] != "critical_success":
        potency = 90
    if result["outcome"] == "critical_success":
        potency = 100
    if method == "decoction":
        potency = 120
    db.update_herb_stack(
        stack_id,
        form=target,
        acquired_day=day,
        potency=min(120, potency),
    )
    bonus = ""
    if method == "decoction":
        bonus = " Cure timers **halved** when used."
    elif method == "poultice":
        bonus = " Heals **1d4** on complex wounds (vs 1d2 raw)."
    elif method == "tonic":
        bonus = " Full tonic effect when administered."
    elif method == "dry":
        bonus = " Stores for months in your herb bag."
    return (
        True,
        format_roll_result(result)
        + f"\n\n**{meta.get('name', herb_key)}** → **{target}**.{bonus}",
    )


def prepare_pack_herb_stack(
    user,
    store_id: int,
    method: str,
    *,
    day: int,
    pack_id: int,
) -> tuple[bool, str]:
    """Dry (or prepare) one healers' den store stack; dryall uses this for fresh rows."""
    if method not in PREP_FORMS:
        return False, "Use **dry**, **poultice**, **tonic**, or **decoction**."
    stack = db.get_pack_herb_stack(store_id)
    if not stack or int(stack["pack_id"]) != pack_id:
        return False, "That stack isn't in your pack's herb store."
    herb_key = stack["herb_key"]
    meta = HERBS.get(herb_key, {})
    if stack["form"] != "fresh" and method == "dry":
        return False, "Only **fresh** herbs can be dried."
    if stack["form"] not in ("fresh", "dried") and method != "dry":
        return False, f"Already prepared as **{stack['form']}**."

    dc = _prep_dc(method, user, herb_key)
    result = resolve_check(
        user,
        attr_keys=("attr_int", "attr_wis"),
        skill="Herblore",
        dc=dc,
        proficient=_herblore_proficient(user),
        skill_key="herblore",
        game_day=day,
    )
    target = _target_form(method)
    name = meta.get("name", herb_key)
    qty = int(stack["quantity"])
    store_note = f" (den store ×**{qty}**)" if qty > 1 else " (den store)"

    if result["outcome"] == "critical_failure":
        db.remove_pack_herb_stack(store_id)
        return (
            False,
            format_roll_result(result)
            + f"\n\n**{name}**{store_note} ruined; batch spoiled.",
        )
    if not result["success"]:
        if method == "dry":
            db.update_pack_herb_stack(store_id, potency=max(40, int(stack["potency"]) - 30))
            return (
                False,
                format_roll_result(result)
                + f"\n\n**{name}**{store_note}: poor drying; **reduced potency** (still usable).",
            )
        return False, format_roll_result(result) + "\n\nPreparation failed; try again."

    potency = 100
    if method == "dry" and result["outcome"] != "critical_success":
        potency = 90
    if result["outcome"] == "critical_success":
        potency = 100
    if method == "decoction":
        potency = 120
    db.update_pack_herb_stack(
        store_id,
        form=target,
        acquired_day=day,
        potency=min(120, potency),
    )
    bonus = " Stores for months in the healers' den." if method == "dry" else ""
    return (
        True,
        format_roll_result(result)
        + f"\n\n**{name}**{store_note} → **{target}**.{bonus}",
    )


def prepare_herb_from_inventory(
    user,
    item_key: str,
    method: str,
    *,
    day: int,
    guild_id: int,
    at_den: bool = False,
) -> tuple[bool, str]:
    """Consume one inventory herb, add as a fresh forage stack, then prepare it."""
    key = item_key.strip().lower()
    if not key.startswith("herb_"):
        return False, "Use an inventory herb key like **`herb_arnica`**."
    herb_key = key.replace("herb_", "", 1)
    if herb_key not in HERBS:
        return False, "That herb isn't in the compendium."
    item = db.get_item_by_key(key)
    if not item:
        return False, "Unknown herb item."
    qty = db.get_inventory_quantity(user["discord_id"], item["id"])
    if qty < 1:
        return False, f"You don't have **{item['name']}** in `/inventory`."
    if not db.consume_item(user["discord_id"], item["id"], quantity=1):
        return False, "Could not use herb from inventory."

    from engine.herb_storage import grant_fresh_herb

    stack_id, _ = grant_fresh_herb(
        user["id"],
        herb_key=herb_key,
        guild_id=guild_id,
        day=day,
        user=user,
    )
    ok, msg = prepare_herb_stack(
        user,
        stack_id,
        method,
        day=day,
        at_den=at_den,
    )
    note = f"_Used **1× {item['name']}** from inventory → forage bag._\n\n"
    return ok, note + msg


def dry_all_fresh_herbs(
    user,
    *,
    day: int,
    guild_id: int,
    at_den: bool = False,
) -> tuple[bool, str]:
    """Roll drying separately for each fresh forage stack and inventory herb item."""
    stacks = db.get_herb_stacks(user["id"])
    fresh_ids = [int(s["id"]) for s in stacks if s["form"] == "fresh"]
    inventory_herbs = [
        (row["key"], row["name"], int(row["quantity"]))
        for row in db.get_inventory(user["discord_id"])
        if row["key"].startswith("herb_")
    ]
    pack_id = int(user["pack_id"]) if user and user["pack_id"] else None
    pack_fresh_ids: list[int] = []
    if pack_id:
        pack_fresh_ids = [
            int(s["id"])
            for s in db.get_pack_herb_stacks(pack_id)
            if s["form"] == "fresh"
        ]
    if not fresh_ids and not inventory_herbs and not pack_fresh_ids:
        return (
            False,
            "No herbs to dry in your **forage bag** (`/herbs action:bag`), "
            "**inventory** (`/inventory`), or **healers' den store** (`/herbs action:store mode:list`).",
        )

    dried = 0
    failed = 0
    ruined = 0
    lines: list[str] = []

    for stack_id in fresh_ids:
        stack = db.get_herb_stack(stack_id)
        if not stack or stack["form"] != "fresh":
            continue
        meta = HERBS.get(stack["herb_key"], {})
        name = meta.get("name", stack["herb_key"])
        ok, msg = prepare_herb_stack(user, stack_id, "dry", day=day, at_den=at_den)
        if ok:
            dried += 1
            lines.append(f"**{name}** → dried")
        elif "ruined" in msg.lower() or "spoiled" in msg.lower():
            ruined += 1
            lines.append(f"**{name}** — ruined")
        else:
            failed += 1
            lines.append(f"**{name}** — failed")

    for item_key, name, qty in inventory_herbs:
        for _ in range(qty):
            ok, msg = prepare_herb_from_inventory(
                user,
                item_key,
                "dry",
                day=day,
                guild_id=guild_id,
                at_den=at_den,
            )
            if ok:
                dried += 1
                lines.append(f"**{name}** → dried")
            elif "ruined" in msg.lower() or "spoiled" in msg.lower():
                ruined += 1
                lines.append(f"**{name}** — ruined")
            else:
                failed += 1
                lines.append(f"**{name}** — failed")

    if pack_id:
        for store_id in pack_fresh_ids:
            stack = db.get_pack_herb_stack(store_id)
            if not stack or stack["form"] != "fresh":
                continue
            meta = HERBS.get(stack["herb_key"], {})
            name = meta.get("name", stack["herb_key"])
            qty = int(stack["quantity"])
            label = f"**{name}** (den store ×{qty})" if qty > 1 else f"**{name}** (den store)"
            ok, msg = prepare_pack_herb_stack(
                user, store_id, "dry", day=day, pack_id=pack_id
            )
            if ok:
                dried += 1
                lines.append(f"{label} → dried")
            elif "ruined" in msg.lower() or "spoiled" in msg.lower():
                ruined += 1
                lines.append(f"{label} — ruined")
            else:
                failed += 1
                lines.append(f"{label} — failed")

    if dried == 0:
        summary = "\n".join(lines[:10])
        return False, f"No herbs dried.\n{summary}"

    summary = "\n".join(lines[:12])
    if len(lines) > 12:
        summary += f"\n_…and {len(lines) - 12} more._"
    tail = f"\n\n**{dried}** dried"
    if failed:
        tail += f", **{failed}** failed"
    if ruined:
        tail += f", **{ruined}** ruined"
    return True, f"**Dry all** complete.{tail}\n{summary}"
