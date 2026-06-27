"""Server NPC registry and `/npc say` for staff-defined characters."""
from __future__ import annotations
import logging
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from utils.embeds import EMBED_COLOR, ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, PlayerEmbed, choice_label
from utils.permissions import is_howlbert_admin
from utils.replies import reply_ephemeral
logger = logging.getLogger('howlbert')

class Npc(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    npc = app_commands.Group(name='npc', description='server npcs for roleplay.')

    @npc.command(name='list', description='list npcs registered in this server.')
    async def list_npcs(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        rows = db.list_server_npcs(interaction.guild.id)
        if not rows:
            await interaction.response.send_message(embed=howlbert_embed('No NPCs', 'Admins can add one with `/npc add`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        lines = []
        for row in rows:
            bit = f"**{row['name']}**"
            if row['bio']:
                bio = str(row['bio'])
                if len(bio) > 80:
                    bio = bio[:77] + '…'
                bit += f' — {bio}'
            lines.append(bit)
        await interaction.response.send_message(embed=howlbert_embed('NPCs', '\n'.join(lines), color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @npc.command(name='add', description='register an npc (admin).')
    @app_commands.describe(name='npc name', bio='short description', avatar='image url for their portrait', tag='optional proxy-style tag prefix (e.g. oldcrow:)')
    async def add_npc(self, interaction: discord.Interaction, name: str, bio: str | None=None, avatar: str | None=None, tag: str | None=None):
        if not interaction.guild or not is_howlbert_admin(interaction):
            await interaction.response.send_message(embed=howlbert_embed('Admin Only', 'Only admins can add NPCs.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        prefix = suffix = None
        if tag:
            if 'text' in tag:
                prefix, _, suffix = tag.partition('text')
            else:
                prefix = tag
        npc_id = db.create_server_npc(interaction.guild.id, name, avatar_url=avatar, bio=bio, prefix=prefix or None, suffix=suffix or None, created_by=interaction.user.id)
        if not npc_id:
            await interaction.response.send_message(embed=howlbert_embed('Failed', 'That name may already exist or was invalid.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        await interaction.response.send_message(embed=howlbert_embed('NPC Added', f'**{name.strip()}** is in the registry. Use `/npc say`.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @npc.command(name='remove', description='remove an npc (admin).')
    @app_commands.describe(name='npc name')
    async def remove_npc(self, interaction: discord.Interaction, name: str):
        if not interaction.guild or not is_howlbert_admin(interaction):
            await interaction.response.send_message(embed=howlbert_embed('Admin Only', 'Only admins can remove NPCs.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if db.delete_server_npc(interaction.guild.id, name):
            await interaction.response.send_message(embed=howlbert_embed('Removed', f'**{name.strip()}** left the registry.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
        else:
            await interaction.response.send_message(embed=howlbert_embed('Not Found', 'No NPC by that name.', color=ERROR_COLOR), ephemeral=reply_ephemeral())

    @npc.command(name='say', description='speak as a registered npc.')
    @app_commands.describe(name='npc name', line='what they say or do')
    async def say_npc(self, interaction: discord.Interaction, name: str, line: str):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        npc = db.get_server_npc(interaction.guild.id, name)
        if not npc:
            await interaction.response.send_message(embed=howlbert_embed('Unknown NPC', 'Use `/npc list`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        text = line.strip()
        if not text:
            await interaction.response.send_message(embed=howlbert_embed('Empty', 'Give them a line.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if len(text) > 500:
            text = text[:499] + '…'
        embed = PlayerEmbed(description=f'*"{text}"*', color=EMBED_COLOR)
        embed.set_author(name=npc['name'], icon_url=npc['avatar_url'] or None)
        embed.set_footer(text=f'npc · posted by {interaction.user.display_name}')
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Npc(bot))