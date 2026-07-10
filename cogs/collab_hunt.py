"""Pack collaborative hunt UI; join / set out / cancel buttons."""
from __future__ import annotations
import discord
from discord.ext import commands
import database as db
from config import COLLAB_HUNT_MIN_WOLVES
from engine.collab_hunt import build_collab_hunt_embed, try_set_out_collab_hunt, validate_join_collab_hunt, validate_start_collab_hunt, wolves_eligible_to_join
from utils.combat_views import make_combat_view
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message

class CollabWolfSelect(discord.ui.Select):

    def __init__(self, hunt_id: int, wolves: list):
        options = [discord.SelectOption(label=w['wolf_name'], value=str(w['id'])) for w in wolves[:25]]
        super().__init__(placeholder='which wolf joins the hunt?', min_values=1, max_values=1, options=options)
        self.hunt_id = hunt_id

    async def callback(self, interaction: discord.Interaction):
        wolf_id = int(self.values[0])
        wolf = db.get_user_by_id(wolf_id)
        if not wolf or wolf['discord_id'] != interaction.user.id:
            await interaction.response.send_message(player_message('Invalid wolf.'), ephemeral=reply_ephemeral())
            return
        await CollabHuntCog.apply_join(interaction, self.hunt_id, wolf)

class CollabWolfSelectView(discord.ui.View):

    def __init__(self, hunt_id: int, wolves: list):
        super().__init__(timeout=120)
        self.add_item(CollabWolfSelect(hunt_id, wolves))

def make_collab_hunt_view(hunt_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)

    async def join_cb(interaction: discord.Interaction, *, hid=hunt_id):
        await CollabHuntCog.handle_join(interaction, hid)

    async def go_cb(interaction: discord.Interaction, *, hid=hunt_id):
        await CollabHuntCog.handle_set_out(interaction, hid)

    async def cancel_cb(interaction: discord.Interaction, *, hid=hunt_id):
        await CollabHuntCog.handle_cancel(interaction, hid)
    join_btn = discord.ui.Button(label='join hunt', style=discord.ButtonStyle.secondary, emoji='🐺', custom_id=f'howlbert_collab:{hunt_id}:join')
    join_btn.callback = join_cb
    go_btn = discord.ui.Button(label='set out', style=discord.ButtonStyle.success, emoji='🏹', custom_id=f'howlbert_collab:{hunt_id}:go')
    go_btn.callback = go_cb
    cancel_btn = discord.ui.Button(label='cancel', style=discord.ButtonStyle.danger, custom_id=f'howlbert_collab:{hunt_id}:cancel')
    cancel_btn.callback = cancel_cb
    view.add_item(join_btn)
    view.add_item(go_btn)
    view.add_item(cancel_btn)
    return view

def _disabled_view() -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    for label in ('join hunt', 'set out', 'cancel'):
        view.add_item(discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, disabled=True))
    return view

async def post_collab_hunt_call(interaction: discord.Interaction, bot: commands.Bot) -> None:
    user = db.get_user(interaction.user.id)
    if not user:
        embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if not interaction.guild:
        await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
        return
    day = db.get_world(interaction.guild.id)['day_number']
    err = validate_start_collab_hunt(user, guild_id=interaction.guild.id, day=day)
    if err:
        embed = howlbert_embed("Can't Call Hunt", err, color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    hunt_id = db.create_collab_hunt(guild_id=interaction.guild.id, channel_id=interaction.channel_id, leader_wolf_id=user['id'], pack_id=user['pack_id'], day_number=day)
    db.add_collab_hunt_member(hunt_id, wolf_id=user['id'], wolf_name=user['wolf_name'], discord_id=user['discord_id'], hunt_role='leader')
    embed = build_collab_hunt_embed(hunt_id)
    view = make_collab_hunt_view(hunt_id)
    await interaction.response.defer()
    message = await interaction.channel.send(embed=embed, view=view)
    db.set_collab_hunt_message(hunt_id, message.id)
    bot.add_view(view, message_id=message.id)
    await interaction.followup.send(embed=howlbert_embed('Pack Hunt Called', 'Your den can join with the buttons on the hunt post.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

class CollabHuntCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        for hunt in db.get_open_collab_hunts():
            self.bot.add_view(make_collab_hunt_view(hunt['id']), message_id=hunt['message_id'])

    @staticmethod
    async def apply_join(interaction: discord.Interaction, hunt_id: int, wolf) -> None:
        hunt = db.get_collab_hunt(hunt_id)
        if not hunt or hunt['status'] != 'open':
            embed = howlbert_embed('Hunt Closed', 'This pack hunt is no longer open.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        day = db.get_world(hunt['guild_id'])['day_number']
        err = validate_join_collab_hunt(wolf, hunt, day)
        if err:
            embed = howlbert_embed("Can't Join", err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        await interaction.response.defer(thinking=False)
        from engine.hunt_party import assign_hunt_role
        existing = [m['hunt_role'] for m in db.get_collab_hunt_members(hunt_id) if 'hunt_role' in m.keys()]
        role = assign_hunt_role(wolf, existing)
        db.add_collab_hunt_member(hunt_id, wolf_id=wolf['id'], wolf_name=wolf['wolf_name'], discord_id=wolf['discord_id'], hunt_role=role)
        from engine.pack_relations import can_join_friendly_pack_hunt
        _, allied_note = can_join_friendly_pack_hunt(wolf, hunt, guild_id=int(hunt['guild_id']))
        join_body = f"**{wolf['wolf_name']}** joins the hunting party as **{role}**."
        if allied_note:
            join_body += f"\n\n{allied_note.strip('_')}"
        embed = build_collab_hunt_embed(hunt_id)
        channel = interaction.client.get_channel(hunt['channel_id'])
        if channel and hunt['message_id']:
            try:
                msg = await channel.fetch_message(hunt['message_id'])
                await msg.edit(embed=embed)
            except discord.HTTPException:
                pass
        await interaction.followup.send(embed=howlbert_embed('Joined', join_body, color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @staticmethod
    async def handle_join(interaction: discord.Interaction, hunt_id: int) -> None:
        if not db.get_user(interaction.user.id):
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        hunt = db.get_collab_hunt(hunt_id)
        if not hunt:
            await interaction.response.send_message(player_message('Hunt not found.'), ephemeral=reply_ephemeral())
            return
        day = db.get_world(hunt['guild_id'])['day_number']
        eligible = wolves_eligible_to_join(interaction.user.id, hunt_id, day)
        if not eligible:
            embed = howlbert_embed("Can't Join", 'No eligible wolf on your account for this hunt (wrong pack, already hunted, or already joined).', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if len(eligible) == 1:
            await CollabHuntCog.apply_join(interaction, hunt_id, eligible[0])
            return
        view = CollabWolfSelectView(hunt_id, eligible)
        await interaction.response.send_message(embed=howlbert_embed('Choose Your Wolf', 'Which character joins the pack hunt?', color=SUCCESS_COLOR), view=view, ephemeral=reply_ephemeral())

    @staticmethod
    async def handle_set_out(interaction: discord.Interaction, hunt_id: int) -> None:
        hunt = db.get_collab_hunt(hunt_id)
        if not hunt:
            await interaction.response.send_message(player_message('Hunt not found.'), ephemeral=reply_ephemeral())
            return
        user = db.get_user(interaction.user.id)
        if not user or user['id'] != hunt['leader_wolf_id']:
            embed = howlbert_embed('Caller Only', 'Only the wolf who called this hunt can set the party out.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        members = db.get_collab_hunt_members(hunt_id)
        if len(members) < COLLAB_HUNT_MIN_WOLVES:
            embed = howlbert_embed('Too Few Wolves', f'Need at least **{COLLAB_HUNT_MIN_WOLVES}** wolves before setting out.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        await interaction.response.defer(thinking=False)
        embed, err, enc_id = try_set_out_collab_hunt(hunt_id)
        if err:
            await interaction.followup.send(err, ephemeral=reply_ephemeral())
            return
        channel = interaction.client.get_channel(hunt['channel_id'])
        if channel and hunt['message_id']:
            try:
                msg = await channel.fetch_message(hunt['message_id'])
                hunt_embed = build_collab_hunt_embed(hunt_id)
                await msg.edit(embed=hunt_embed, view=_disabled_view())
            except discord.HTTPException:
                pass
        if enc_id:
            view = make_combat_view(enc_id, interaction.client)
            if channel:
                await channel.send(embed=embed, view=view)
            await interaction.followup.send(embed=howlbert_embed('Trouble!', 'Large prey or an ambush; the party fights together below (+1 attack per ally, max +3).', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
            return
        if channel and hunt['message_id']:
            try:
                msg = await channel.fetch_message(hunt['message_id'])
                await msg.edit(embed=embed, view=_disabled_view())
            except discord.HTTPException:
                pass
        from engine.collab_ui import post_collab_hunt_prey_pile, refresh_collab_hunt_post
        if channel:
            await post_collab_hunt_prey_pile(interaction.client, channel, hunt_id)
        await refresh_collab_hunt_post(interaction.client, hunt_id)
        await interaction.followup.send(embed=howlbert_embed('Away!', 'The pack hunt is complete.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @staticmethod
    async def handle_cancel(interaction: discord.Interaction, hunt_id: int) -> None:
        hunt = db.get_collab_hunt(hunt_id)
        if not hunt or hunt['status'] != 'open':
            await interaction.response.send_message(player_message('This hunt is already closed.'), ephemeral=reply_ephemeral())
            return
        user = db.get_user(interaction.user.id)
        if not user or user['id'] != hunt['leader_wolf_id']:
            embed = howlbert_embed('Caller Only', 'Only the wolf who called this hunt can cancel it.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        db.set_collab_hunt_status(hunt_id, 'cancelled')
        embed = build_collab_hunt_embed(hunt_id)
        channel = interaction.client.get_channel(hunt['channel_id'])
        if channel and hunt['message_id']:
            try:
                msg = await channel.fetch_message(hunt['message_id'])
                await msg.edit(embed=embed, view=_disabled_view())
            except discord.HTTPException:
                pass
        await interaction.response.send_message(embed=howlbert_embed('Cancelled', 'The pack hunt was called off.', color=ERROR_COLOR), ephemeral=reply_ephemeral())

async def setup(bot: commands.Bot):
    await bot.add_cog(CollabHuntCog(bot))