"""Autocomplete for inventory herb items."""

from __future__ import annotations

import discord
from discord import app_commands

import database as db

# order longest-first so substrings don't shadow longer suffixes (simmered_milk before milk)
_FORM_SUFFIXES = (
    "_simmered_milk",
    "_decoction",
    "_poultice",
    "_infusion",
    "_ointment",
    "_cooked",
    "_chewed",
    "_tonic",
    "_juice",
    "_dried",
    "_tea",
    "_sap",
    "_rub",
)


def _split_herb_form(item_key: str) -> tuple[str, str | None]:
    """Return (herb_key, form) for a prepared item key, or (herb_key, None) for raw.

    Validates the candidate herb_key against HERBS so that herb names ending in
    a form word (e.g. labrador_tea ending in _tea) are not incorrectly split.
    """
    if not item_key.startswith("herb_"):
        return item_key, None
    rest = item_key[5:]  # strip leading "herb_"
    from herbs import HERBS
    if rest in HERBS:
        return rest, None
    for suffix in _FORM_SUFFIXES:
        if rest.endswith(suffix):
            candidate = rest[: -len(suffix)]
            if candidate in HERBS:
                return candidate, suffix[1:]  # strip leading "_" from suffix
    return rest, None


async def herb_inventory_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    choices: list[app_commands.Choice[str]] = []
    needle = current.lower()
    items = db.get_inventory(interaction.user.id)

    # build herb_key -> {form: potency} — one entry per form, most recent wins
    # (get_herb_stacks returns rows ORDER BY acquired_day DESC so first seen = most recent)
    stacks_by_herb: dict[str, dict[str, int]] = {}
    try:
        user_row = db.get_user(interaction.user.id)
        if user_row:
            for stack in db.get_herb_stacks(int(user_row["id"])):
                hk = str(stack["herb_key"])
                form_key = str(stack["form"])
                herb_forms = stacks_by_herb.setdefault(hk, {})
                if form_key not in herb_forms:
                    herb_forms[form_key] = int(stack["potency"])
    except Exception:
        pass

    for row in items:
        if not row["key"].startswith("herb_") and row["key"] != "stick":
            continue

        herb_key, form = _split_herb_form(row["key"])
        display_name = row["name"].lower()
        qty = row["quantity"]
        item_key = row["key"]

        if needle and needle not in item_key and needle not in display_name:
            continue

        if form:
            # prepared item with its own DB entry (herb_knotgrass_infusion exists as an item)
            potency = stacks_by_herb.get(herb_key, {}).get(form)
            pot_str = f" {potency}%" if potency is not None else ""
            label = f"{display_name} - {form}{pot_str} x{qty}"
        else:
            # raw herb — annotate with any prepared stacks (one per unique form)
            herb_forms = stacks_by_herb.get(herb_key, {})
            if herb_forms:
                prep_note = "; ".join(f"{f} {p}%" for f, p in list(herb_forms.items())[:3])
                label = f"{display_name} x{qty} · {prep_note}"
            else:
                label = f"{display_name} x{qty}"

        choices.append(app_commands.Choice(name=label[:100], value=item_key))

    return choices[:25]


async def store_stack_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    action = getattr(interaction.namespace, "action", None)
    needle = current.lower()
    choices: list[app_commands.Choice[str]] = []
    if action == "turnin":
        from engine.restricted_herbs import is_restricted_herb

        for row in db.get_inventory(interaction.user.id):
            if not row["key"].startswith("herb_"):
                continue
            herb_key = row["key"].replace("herb_", "", 1)
            if not is_restricted_herb(herb_key):
                continue
            if needle and needle not in row["key"] and needle not in row["name"].lower():
                continue
            name = f"{row['name']} x{row['quantity']} ({row['key']})"[:100]
            choices.append(app_commands.Choice(name=name, value=row["key"]))
        return choices[:25]
    mode = getattr(interaction.namespace, "mode", None)
    if action == "store" and mode == "withdraw":
        user = db.get_user(interaction.user.id)
        if not user or not user["pack_id"]:
            return []
        from herbs import HERBS

        for stack in db.get_pack_herb_stacks(user["pack_id"]):
            meta = HERBS.get(stack["herb_key"], {})
            name = meta.get("name", stack["herb_key"])
            label = f"#{stack['id']} {name} x{stack['quantity']}"[:100]
            if needle and needle not in str(stack["id"]) and needle not in name.lower():
                continue
            choices.append(app_commands.Choice(name=label, value=str(stack["id"])))
        return choices[:25]
    return []
