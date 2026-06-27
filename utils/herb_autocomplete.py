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
