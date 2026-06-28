"""Autocomplete for inventory herb items."""

from __future__ import annotations

import discord
from discord import app_commands

import database as db


async def herb_inventory_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    choices: list[app_commands.Choice[str]] = []
    action = getattr(interaction.namespace, "action", None)
    prepare_action = action in ("prepare", None)
    items = db.get_inventory(interaction.user.id)
    for row in items:
        if not row["key"].startswith("herb_") and row["key"] != "stick":
            continue
        if current and current.lower() not in row["key"] and current.lower() not in row["name"].lower():
            continue
        if prepare_action and action == "prepare":
            name = f"{row['name']} x{row['quantity']} · inventory (prepare)"[:100]
        else:
            name = f"{row['name']} x{row['quantity']} ({row['key']})"[:100]
        choices.append(app_commands.Choice(name=name, value=row["key"]))
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
