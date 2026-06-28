"""`/rivals`; named rival NPCs and grudge tracking."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from engine.rival_npcs import rival_status_lines
from utils.embeds import SUCCESS_COLOR, howlbert_embed, player_message
from utils.replies import reply_ephemeral


class Rivals(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='rivals', description="view your wolf's rival npcs and grudge levels.")
    async def rivals(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        lines = rival_status_lines(user['id'])
        if not lines:
            body = (
                "no rivals yet. hostile scent marks found via `/field action:sniff` near a pack "
                "your pack is feuding with can introduce one."
            )
        else:
            body = '\n'.join(lines)
        embed = howlbert_embed(f"{user['wolf_name']}'s rivals", body, color=SUCCESS_COLOR)
        embed.set_footer(text='grudge rises from hostile-scent sniff encounters; raise pack standing to ease tension')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())


async def setup(bot: commands.Bot):
    await bot.add_cog(Rivals(bot))
