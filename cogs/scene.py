"""`/scene`; lightweight RP scene threads with a who's-here roster."""
from __future__ import annotations
import logging
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.scene_roster import build_roster_embed, refresh_scene_roster
from engine.open_scenes_index import refresh_open_scenes_index
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label
from utils.permissions import is_howlbert_admin
from utils.replies import reply_ephemeral
from utils.wolf_autocomplete import make_member_wolf_autocomplete
logger = logging.getLogger('howlbert')

def _active_wolf(interaction: discord.Interaction):
    return db.get_user(interaction.user.id)

_with_member_wolf_autocomplete = make_member_wolf_autocomplete("with_member")

async def _other_wolf_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    active = db.get_user(interaction.user.id)
    if not active:
        return []
    choices = []
    for wolf in db.list_user_wolves(interaction.user.id):
        if wolf['id'] == active['id']:
            continue
        name = wolf['wolf_name']
        if current and current.lower() not in name.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(name), value=name))
    return choices[:25]

class Scene(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    scene = app_commands.Group(name='scene', description='run roleplay scenes in threads with a roster.')

    @scene.command(name='start', description='open an rp scene as a thread in this channel.')
    @app_commands.describe(with_member='another player in the scene (optional)', own_wolf='your other wolf in the scene (optional)', with_member_wolf="specific wolf from that player's roster", location='where the scene happens (defaults to your ic location)', topic="what's happening; goes in the opening post, not the thread title")
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, with_member_wolf=_with_member_wolf_autocomplete)
    async def start(self, interaction: discord.Interaction, with_member: discord.Member | None=None, own_wolf: str | None=None, with_member_wolf: str | None=None, location: str | None=None, topic: str | None=None):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        wolf = _active_wolf(interaction)
        if not wolf:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(embed=howlbert_embed('Wrong Place', 'Start a scene in a normal text channel, not a thread/DM.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        perms = channel.permissions_for(interaction.guild.me)
        if not perms.create_public_threads:
            await interaction.response.send_message(embed=howlbert_embed('Missing Permission', 'I need **Create Public Threads** here.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if with_member and own_wolf:
            await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use `with_member` or `own_wolf`; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        await interaction.response.defer(ephemeral=reply_ephemeral())
        from engine.scene_titles import build_scene_thread_title
        partner_wolf = None
        if own_wolf:
            rows = db.list_user_wolves(interaction.user.id)
            partner_wolf = next((w for w in rows if w['wolf_name'].lower() == own_wolf.strip().lower() and w['id'] != wolf['id']), None)
            if not partner_wolf:
                await interaction.followup.send(embed=howlbert_embed('Unknown Wolf', f'No wolf named **{own_wolf}** on your account.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
        elif with_member:
            if with_member.bot:
                await interaction.followup.send(embed=howlbert_embed('No', "You can't scene with a bot.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if with_member_wolf:
                partner_wolf = db.find_user_wolf(with_member.id, with_member_wolf)
            else:
                partner_wolf = db.get_user(with_member.id)
            if not partner_wolf:
                await interaction.followup.send(embed=howlbert_embed('No Wolf', f"**{with_member.display_name}** hasn't registered a wolf yet.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
        loc = (location or '').strip()
        if not loc:
            ic = wolf['ic_location'] if 'ic_location' in wolf.keys() else None
            if ic and str(ic).strip():
                loc = str(ic).strip()
        title = build_scene_thread_title(wolf['wolf_name'], partner_name=partner_wolf['wolf_name'] if partner_wolf else None, location=loc or None)
        try:
            thread = await channel.create_thread(name=title, type=discord.ChannelType.public_thread, reason=f'RP scene by {interaction.user}')
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send(embed=howlbert_embed('Could Not Open', 'Failed to create the scene thread.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = int(world['day_number']) if world else 0
        scene_id = db.create_scene(interaction.guild.id, thread.id, title, topic, interaction.user.id, day)
        db.join_scene(scene_id, wolf['id'], wolf['wolf_name'], interaction.user.id)
        if partner_wolf:
            partner_discord_id = with_member.id if with_member else interaction.user.id
            db.join_scene(scene_id, partner_wolf['id'], partner_wolf['wolf_name'], partner_discord_id)
        body = topic.strip() if topic else '_The scene is set. Wolves, take your places._'
        opening = howlbert_embed(f'🎬 {title}', body, color=SUCCESS_COLOR)
        opener_line = f"**{wolf['wolf_name']}**"
        if partner_wolf:
            opener_line += f" · with **{partner_wolf['wolf_name']}**"
        if loc:
            opener_line += f' · 📍 {loc}'
        opening.add_field(name='Cast', value=opener_line, inline=False)
        opening.set_footer(text='/scene join · /scene here · /scene poke · /scene end')
        try:
            await thread.send(embed=opening)
        except discord.HTTPException:
            pass
        scene = db.get_scene_by_thread(thread.id)
        if scene:
            await refresh_scene_roster(self.bot, scene)
        await refresh_open_scenes_index(self.bot, interaction.guild.id)
        await interaction.followup.send(embed=howlbert_embed('Scene Opened', f"{thread.mention} is live as **{wolf['wolf_name']}**.", color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    def _scene_here(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.Thread):
            return (None, 'Use this **inside a scene thread**.')
        scene = db.get_scene_by_thread(channel.id)
        if not scene or scene['status'] != 'open':
            return (None, 'No open scene here. Start one with `/scene start`.')
        return (scene, None)

    async def _maybe_auto_join(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        channel = message.channel
        if not isinstance(channel, discord.Thread):
            return
        scene = db.get_scene_by_thread(channel.id)
        if not scene or scene['status'] != 'open':
            return
        wolf = db.get_user(message.author.id)
        if not wolf:
            return
        members = db.get_scene_members(scene['id'])
        if any((int(m['wolf_id']) == int(wolf['id']) for m in members)):
            return
        db.join_scene(scene['id'], wolf['id'], wolf['wolf_name'], message.author.id)
        await refresh_scene_roster(self.bot, scene)
        await refresh_open_scenes_index(self.bot, message.guild.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self._maybe_auto_join(message)

    @scene.command(name='join', description='join the scene in this thread as your active wolf.')
    async def join(self, interaction: discord.Interaction):
        wolf = _active_wolf(interaction)
        if not wolf:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        scene, err = self._scene_here(interaction)
        if err:
            await interaction.response.send_message(embed=howlbert_embed('No Scene', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.join_scene(scene['id'], wolf['id'], wolf['wolf_name'], interaction.user.id)
        await refresh_scene_roster(self.bot, scene)
        await refresh_open_scenes_index(self.bot, interaction.guild.id)
        await interaction.response.send_message(embed=howlbert_embed('Joined Scene', f"**{wolf['wolf_name']}** steps in.", color=SUCCESS_COLOR))

    @scene.command(name='leave', description='leave the scene in this thread.')
    async def leave(self, interaction: discord.Interaction):
        wolf = _active_wolf(interaction)
        if not wolf:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        scene, err = self._scene_here(interaction)
        if err:
            await interaction.response.send_message(embed=howlbert_embed('No Scene', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        left = db.leave_scene(scene['id'], wolf['id'])
        if left:
            await refresh_scene_roster(self.bot, scene)
            await refresh_open_scenes_index(self.bot, interaction.guild.id)
        msg = f"**{wolf['wolf_name']}** slips away." if left else "You weren't in this scene."
        await interaction.response.send_message(embed=howlbert_embed('Scene', msg, color=SUCCESS_COLOR))

    @scene.command(name='here', description="show who's in this scene.")
    async def here(self, interaction: discord.Interaction):
        scene, err = self._scene_here(interaction)
        if err:
            await interaction.response.send_message(embed=howlbert_embed('No Scene', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        members = db.get_scene_members(scene['id'])
        embed = build_roster_embed(scene, members)
        await interaction.response.send_message(embed=embed)

    @scene.command(name='poke', description='ping everyone in this scene.')
    @app_commands.describe(note='optional note with the ping')
    async def poke(self, interaction: discord.Interaction, note: str | None=None):
        scene, err = self._scene_here(interaction)
        if err:
            await interaction.response.send_message(embed=howlbert_embed('No Scene', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        members = db.get_scene_members(scene['id'])
        if not members:
            await interaction.response.send_message(embed=howlbert_embed('Empty Scene', 'No one has joined yet.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        mentions = ' '.join((f"<@{m['discord_id']}>" for m in members))
        wolf = _active_wolf(interaction)
        who = wolf['wolf_name'] if wolf else interaction.user.display_name
        body = note.strip() if note else '_The scene stirs._'
        await interaction.response.send_message(f"🎬 **{scene['name']}**; **{who}** calls the scene.\n{body}\n{mentions}")

    @scene.command(name='end', description='close this scene (scene owner or admin).')
    async def end(self, interaction: discord.Interaction):
        scene, err = self._scene_here(interaction)
        if err:
            await interaction.response.send_message(embed=howlbert_embed('No Scene', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if interaction.user.id != int(scene['owner_discord_id']) and (not is_howlbert_admin(interaction)):
            await interaction.response.send_message(embed=howlbert_embed('Not Yours', "Only the scene's opener or an admin can end it.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.close_scene(scene['id'])
        await refresh_open_scenes_index(self.bot, interaction.guild.id)
        await interaction.response.send_message(embed=howlbert_embed('Scene Ended', f"**{scene['name']}** is closed. Thanks for playing.", color=SUCCESS_COLOR))
        channel = interaction.channel
        if isinstance(channel, discord.Thread):
            try:
                await channel.edit(archived=True, locked=False)
            except (discord.Forbidden, discord.HTTPException):
                pass

async def setup(bot: commands.Bot):
    await bot.add_cog(Scene(bot))