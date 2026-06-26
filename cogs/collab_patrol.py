"""Pack collaborative scout patrol UI."""

from __future__ import annotations

import discord
from discord.ext import commands

import database as db
from config import COLLAB_PATROL_MAX_WOLVES, COLLAB_PATROL_MIN_WOLVES
from engine.collab_patrol import (
    build_collab_patrol_embed,
    try_set_out_collab_patrol,
    validate_join_collab_patrol,
    validate_start_collab_patrol,
    wolves_eligible_to_join_patrol,
)
from utils.combat_views import make_combat_view
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed


class PatrolWolfSelect(discord.ui.Select):
    def __init__(self, patrol_id: int, wolves: list):
        options = [
            discord.SelectOption(label=w["wolf_name"], value=str(w["id"])) for w in wolves[:25]
        ]
        super().__init__(
            placeholder="Which scout joins?",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.patrol_id = patrol_id

    async def callback(self, interaction: discord.Interaction):
        wolf_id = int(self.values[0])
        wolf = db.get_user_by_id(wolf_id)
        if not wolf or wolf["discord_id"] != interaction.user.id:
            await interaction.response.send_message("Invalid wolf.", ephemeral=reply_ephemeral())
            return
        await CollabPatrolCog.apply_join(interaction, self.patrol_id, wolf)


class PatrolWolfSelectView(discord.ui.View):
    def __init__(self, patrol_id: int, wolves: list):
        super().__init__(timeout=120)
        self.add_item(PatrolWolfSelect(patrol_id, wolves))


def make_collab_patrol_view(patrol_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    patrol = db.get_collab_patrol(patrol_id)
    trail = (
        patrol
        and "patrol_kind" in patrol.keys()
        and patrol["patrol_kind"] == "trail"
    )
    war = patrol and "patrol_kind" in patrol.keys() and patrol["patrol_kind"] == "war_patrol"
    join_label = "Join war patrol" if war else "Join trail" if trail else "Join patrol"

    async def join_cb(interaction: discord.Interaction, *, pid=patrol_id):
        await CollabPatrolCog.handle_join(interaction, pid)

    async def go_cb(interaction: discord.Interaction, *, pid=patrol_id):
        await CollabPatrolCog.handle_set_out(interaction, pid)

    async def cancel_cb(interaction: discord.Interaction, *, pid=patrol_id):
        await CollabPatrolCog.handle_cancel(interaction, pid)

    join_btn = discord.ui.Button(
        label=join_label,
        style=discord.ButtonStyle.secondary,
        emoji="🐾" if trail else "👣",
        custom_id=f"howlbert_patrol:{patrol_id}:join",
    )
    join_btn.callback = join_cb

    go_btn = discord.ui.Button(
        label="Set out",
        style=discord.ButtonStyle.success,
        emoji="🗺️",
        custom_id=f"howlbert_patrol:{patrol_id}:go",
    )
    go_btn.callback = go_cb

    cancel_btn = discord.ui.Button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        custom_id=f"howlbert_patrol:{patrol_id}:cancel",
    )
    cancel_btn.callback = cancel_cb

    view.add_item(join_btn)
    view.add_item(go_btn)
    view.add_item(cancel_btn)
    return view


def _disabled_view(*, trail: bool = False, war: bool = False) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    join_label = "Join war patrol" if war else "Join trail" if trail else "Join patrol"
    for label in (join_label, "Set out", "Cancel"):
        view.add_item(
            discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, disabled=True)
        )
    return view


async def post_collab_party_call(
    interaction: discord.Interaction,
    bot: commands.Bot,
    *,
    patrol_kind: str = "survey",
) -> None:
    trail = patrol_kind == "trail"
    war = patrol_kind == "war_patrol"
    user = db.get_user(interaction.user.id)
    if not user:
        embed = howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if not interaction.guild:
        await interaction.response.send_message("Use this in a server.", ephemeral=reply_ephemeral())
        return

    day = db.get_world(interaction.guild.id)["day_number"]
    err = validate_start_collab_patrol(
        user, guild_id=interaction.guild.id, day=day, kind=patrol_kind
    )
    if err:
        if war:
            title = "Can't Call War Patrol"
        elif trail:
            title = "Can't Call Trail"
        else:
            title = "Can't Call Patrol"
        embed = howlbert_embed(title, err, color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    patrol_id = db.create_collab_patrol(
        guild_id=interaction.guild.id,
        channel_id=interaction.channel_id,
        leader_wolf_id=user["id"],
        pack_id=user["pack_id"],
        day_number=day,
        patrol_kind=patrol_kind,
    )
    db.add_collab_patrol_member(
        patrol_id,
        wolf_id=user["id"],
        wolf_name=user["wolf_name"],
        discord_id=user["discord_id"],
    )

    embed = build_collab_patrol_embed(patrol_id)
    view = make_collab_patrol_view(patrol_id)

    await interaction.response.defer()
    message = await interaction.channel.send(embed=embed, view=view)
    db.set_collab_patrol_message(patrol_id, message.id)
    bot.add_view(view, message_id=message.id)

    if war:
        done_title = "War Patrol Called"
        done_body = "Packmates in your den can join with the buttons on the war patrol post."
    elif trail:
        done_title = "Pack Trail Called"
        done_body = "Scouts in your den can join with the buttons on the trail post."
    else:
        done_title = "Pack Patrol Called"
        done_body = "Scouts in your den can join with the buttons on the patrol post."
    await interaction.followup.send(
        embed=howlbert_embed(done_title, done_body, color=SUCCESS_COLOR),
        ephemeral=reply_ephemeral(),
    )


async def post_collab_war_patrol_call(interaction: discord.Interaction, bot: commands.Bot) -> None:
    await post_collab_party_call(interaction, bot, patrol_kind="war_patrol")


async def post_collab_patrol_call(interaction: discord.Interaction, bot: commands.Bot) -> None:
    await post_collab_party_call(interaction, bot, patrol_kind="survey")


async def post_collab_trail_call(interaction: discord.Interaction, bot: commands.Bot) -> None:
    await post_collab_party_call(interaction, bot, patrol_kind="trail")


class CollabPatrolCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        for patrol in db.get_open_collab_patrols():
            self.bot.add_view(make_collab_patrol_view(patrol["id"]), message_id=patrol["message_id"])

    @staticmethod
    async def apply_join(interaction: discord.Interaction, patrol_id: int, wolf) -> None:
        patrol = db.get_collab_patrol(patrol_id)
        if not patrol or patrol["status"] != "open":
            await interaction.response.send_message(
                embed=howlbert_embed("Patrol Closed", "This pack patrol is no longer open.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return

        day = db.get_world(patrol["guild_id"])["day_number"]
        err = validate_join_collab_patrol(wolf, patrol, day)
        if err:
            await interaction.response.send_message(
                embed=howlbert_embed("Can't Join", err, color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return

        await interaction.response.defer(thinking=False)

        db.add_collab_patrol_member(
            patrol_id,
            wolf_id=wolf["id"],
            wolf_name=wolf["wolf_name"],
            discord_id=wolf["discord_id"],
        )
        embed = build_collab_patrol_embed(patrol_id)
        channel = interaction.client.get_channel(patrol["channel_id"])
        if channel and patrol["message_id"]:
            try:
                msg = await channel.fetch_message(patrol["message_id"])
                await msg.edit(embed=embed)
            except discord.HTTPException:
                pass

        await interaction.followup.send(
            embed=howlbert_embed("Joined", f"**{wolf['wolf_name']}** joins the patrol.", color=SUCCESS_COLOR),
            ephemeral=reply_ephemeral(),
        )

    @staticmethod
    async def handle_join(interaction: discord.Interaction, patrol_id: int) -> None:
        if not db.get_user(interaction.user.id):
            await interaction.response.send_message(
                embed=howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return

        patrol = db.get_collab_patrol(patrol_id)
        if not patrol:
            await interaction.response.send_message("Patrol not found.", ephemeral=reply_ephemeral())
            return

        day = db.get_world(patrol["guild_id"])["day_number"]
        eligible = wolves_eligible_to_join_patrol(interaction.user.id, patrol_id, day)
        if not eligible:
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Can't Join",
                    "No eligible scout on your account (wrong pack, already surveyed, or already joined).",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

        if len(eligible) == 1:
            await CollabPatrolCog.apply_join(interaction, patrol_id, eligible[0])
            return

        view = PatrolWolfSelectView(patrol_id, eligible)
        await interaction.response.send_message(
            embed=howlbert_embed("Choose Your Wolf", "Which scout joins the patrol?", color=SUCCESS_COLOR),
            view=view,
            ephemeral=reply_ephemeral(),
        )

    @staticmethod
    async def handle_set_out(interaction: discord.Interaction, patrol_id: int) -> None:
        patrol = db.get_collab_patrol(patrol_id)
        if not patrol:
            await interaction.response.send_message("Patrol not found.", ephemeral=reply_ephemeral())
            return

        user = db.get_user(interaction.user.id)
        if not user or user["id"] != patrol["leader_wolf_id"]:
            await interaction.response.send_message(
                embed=howlbert_embed("Caller Only", "Only the scout who called this patrol can set out.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return

        members = db.get_collab_patrol_members(patrol_id)
        if len(members) < COLLAB_PATROL_MIN_WOLVES:
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Too Few Scouts",
                    f"Need at least **{COLLAB_PATROL_MIN_WOLVES}** scouts before setting out.",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

        await interaction.response.defer(thinking=False)

        embed, err, enc_id = try_set_out_collab_patrol(patrol_id)
        if err:
            await interaction.followup.send(err, ephemeral=reply_ephemeral())
            return

        channel = interaction.client.get_channel(patrol["channel_id"])
        trail = (
            patrol
            and "patrol_kind" in patrol.keys()
            and patrol["patrol_kind"] == "trail"
        )
        war = patrol and "patrol_kind" in patrol.keys() and patrol["patrol_kind"] == "war_patrol"
        if channel and patrol["message_id"]:
            try:
                msg = await channel.fetch_message(patrol["message_id"])
                await msg.edit(embed=build_collab_patrol_embed(patrol_id), view=_disabled_view(trail=trail, war=war))
            except discord.HTTPException:
                pass

        if enc_id:
            view = make_combat_view(enc_id, interaction.client)
            if channel:
                await channel.send(embed=embed, view=view)
            await interaction.followup.send(
                embed=howlbert_embed(
                    "Ambush!",
                    "The party fights together below (+1 attack per ally, max +3).",
                    color=SUCCESS_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

        if channel and patrol["message_id"]:
            try:
                msg = await channel.fetch_message(patrol["message_id"])
                await msg.edit(embed=embed, view=_disabled_view(trail=trail, war=war))
            except discord.HTTPException:
                pass

        done = "War patrol complete." if war else "Pack trail complete." if trail else "Pack patrol complete."
        from engine.collab_ui import refresh_collab_patrol_post

        await refresh_collab_patrol_post(interaction.client, patrol_id)

        await interaction.followup.send(
            embed=howlbert_embed("Away!", done, color=SUCCESS_COLOR),
            ephemeral=reply_ephemeral(),
        )

    @staticmethod
    async def handle_cancel(interaction: discord.Interaction, patrol_id: int) -> None:
        patrol = db.get_collab_patrol(patrol_id)
        if not patrol or patrol["status"] != "open":
            await interaction.response.send_message("This party is already closed.", ephemeral=reply_ephemeral())
            return

        user = db.get_user(interaction.user.id)
        if not user or user["id"] != patrol["leader_wolf_id"]:
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Caller Only",
                    "Only the scout who called this party can cancel it.",
                    color=ERROR_COLOR,
                ),
                ephemeral=reply_ephemeral(),
            )
            return

        trail = "patrol_kind" in patrol.keys() and patrol["patrol_kind"] == "trail"
        war = "patrol_kind" in patrol.keys() and patrol["patrol_kind"] == "war_patrol"
        db.set_collab_patrol_status(patrol_id, "cancelled")
        channel = interaction.client.get_channel(patrol["channel_id"])
        if channel and patrol["message_id"]:
            try:
                msg = await channel.fetch_message(patrol["message_id"])
                await msg.edit(embed=build_collab_patrol_embed(patrol_id), view=_disabled_view(trail=trail, war=war))
            except discord.HTTPException:
                pass

        label = "war patrol" if war else "trail" if trail else "patrol"
        await interaction.response.send_message(
            embed=howlbert_embed("Cancelled", f"The pack {label} was called off.", color=ERROR_COLOR),
            ephemeral=reply_ephemeral(),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(CollabPatrolCog(bot))
