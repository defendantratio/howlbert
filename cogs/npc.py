"""Server NPC registry and `/npc say` for staff-defined characters."""
from __future__ import annotations
import logging
import random
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.signing import NPC_CAPABLE_SIGNALS, SIGNAL_CATALOG, apply_signal_to_target
from utils.embeds import EMBED_COLOR, ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, PlayerEmbed, choice_label
from utils.permissions import is_howlbert_admin
from utils.replies import reply_ephemeral
from utils.wolf_autocomplete import make_member_wolf_autocomplete
logger = logging.getLogger('howlbert')

# Only signals with a real mechanical effect on a target are offered here;
# pack-wide signals (alert/rally/freeze) and no-target "track" have no
# equivalent for an npc, which has no den, mood, or standing of its own.
_NPC_SIGNAL_CHOICES = [app_commands.Choice(name=choice_label(f"{info['name']}; {info['summary']}"), value=key) for key, info in SIGNAL_CATALOG.items() if key in NPC_CAPABLE_SIGNALS]
_member_wolf_autocomplete = make_member_wolf_autocomplete("member")

async def _npc_name_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if not interaction.guild:
        return []
    rows = db.list_server_npcs(interaction.guild.id)
    needle = current.lower()
    return [app_commands.Choice(name=choice_label(row['name']), value=row['name']) for row in rows if needle in row['name'].lower()][:25]

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
                bit += f'; {bio}'
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
    @app_commands.autocomplete(name=_npc_name_autocomplete)
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

    @npc.command(name='sign', description="body-language a registered npc at a player's wolf; most npcs don't share a wolf's tongue.")
    @app_commands.describe(name='npc name', signal='the body-language signal to give', member="the player whose wolf reacts (it's their mood/standing that changes)", member_wolf="specific wolf from that player's roster", line='optional roleplay line')
    @app_commands.choices(signal=_NPC_SIGNAL_CHOICES)
    @app_commands.autocomplete(name=_npc_name_autocomplete, member_wolf=_member_wolf_autocomplete)
    async def sign_npc(self, interaction: discord.Interaction, name: str, signal: app_commands.Choice[str], member: discord.Member, member_wolf: str | None=None, line: str | None=None):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        npc = db.get_server_npc(interaction.guild.id, name)
        if not npc:
            await interaction.response.send_message(embed=howlbert_embed('Unknown NPC', 'Use `/npc list`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if member.bot:
            await interaction.response.send_message(embed=howlbert_embed('Invalid Player', 'Bots cannot own wolves.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if member_wolf:
            target = db.find_user_wolf(member.id, member_wolf)
        else:
            target = db.get_user(member.id)
        if not target:
            await interaction.response.send_message(embed=howlbert_embed('No Wolf', f"**{member.display_name}** hasn't registered a wolf yet.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        info = SIGNAL_CATALOG[signal.value]
        posture = random.choice(info['posture'])
        lines = [f"**{npc['name']}** {posture}.", apply_signal_to_target(signal.value, target, npc_id=npc['id'])]
        if line:
            text = line.strip()
            if len(text) > 300:
                text = text[:299] + '…'
            if text:
                lines.append(f'_{text}_')
        embed = PlayerEmbed(description='\n'.join(lines), color=EMBED_COLOR)
        embed.set_author(name=npc['name'], icon_url=npc['avatar_url'] or None)
        embed.set_footer(text=f"npc · sign · {info['name']} · affects {target['wolf_name']} · posted by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='narrate', description='post anonymous scene narration with no named speaker (admin).')
    @app_commands.describe(text='the narration; scene description, weather, omniscient detail')
    async def narrate(self, interaction: discord.Interaction, text: str):
        if not interaction.guild or not is_howlbert_admin(interaction):
            await interaction.response.send_message(embed=howlbert_embed('Admin Only', 'Only admins can narrate.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        cleaned = text.strip()
        if not cleaned:
            await interaction.response.send_message(embed=howlbert_embed('Empty', 'Give the scene some words.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if len(cleaned) > 1500:
            cleaned = cleaned[:1499] + '…'
        embed = PlayerEmbed(description=f'*{cleaned}*', color=EMBED_COLOR)
        embed.set_footer(text='narration')
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Npc(bot))