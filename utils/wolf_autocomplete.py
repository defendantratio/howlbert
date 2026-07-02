"""Factory for member wolf-roster autocomplete in slash commands."""
from __future__ import annotations

import discord
from discord import app_commands

import database as db
from utils.embeds import choice_label


def make_member_wolf_autocomplete(member_param: str):
    """Return an autocomplete fn that lists wolves owned by the member named in member_param."""
    async def _autocomplete(
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        member = getattr(interaction.namespace, member_param, None)
        if not isinstance(member, discord.Member):
            return []
        wolves = db.list_user_wolves(member.id)
        choices: list[app_commands.Choice[str]] = []
        for w in wolves:
            name = w["wolf_name"]
            if current and current.lower() not in name.lower():
                continue
            choices.append(app_commands.Choice(name=choice_label(name), value=name))
        return choices[:25]

    return _autocomplete
