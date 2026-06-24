"""Autocomplete for herb stacks and inventory items."""

from __future__ import annotations

import discord
from discord import app_commands

import database as db


async def herb_inventory_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    user = db.get_user(interaction.user.id)
    choices: list[app_commands.Choice[str]] = []
    action = getattr(interaction.namespace, "action", None)
    prepare_action = action in ("prepare", None)
    if user and interaction.guild:
        world = db.get_world(interaction.guild.id)
        from engine.herb_storage import format_herb_stack_line

        for stack in db.get_herb_stacks(user["id"]):
            label = format_herb_stack_line(stack, world["day_number"])
            val = f"stack:{stack['id']}"
            if current and current.lower() not in label.lower() and current not in val:
                continue
            choices.append(app_commands.Choice(name=label[:100], value=val))
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
