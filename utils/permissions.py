import os

import discord


def _admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_IDS", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}


def is_howlbert_admin(interaction: discord.Interaction) -> bool:
    if interaction.user.id in _admin_ids():
        return True
    if interaction.guild and isinstance(interaction.user, discord.Member):
        if interaction.user.guild_permissions.administrator:
            return True
    return False
