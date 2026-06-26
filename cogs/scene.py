"""`/scene`; lightweight RP scene threads with a who's-here roster."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from engine.scene_roster import build_roster_embed, refresh_scene_roster
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from utils.permissions import is_howlbert_admin
from utils.replies import reply_ephemeral

logger = logging.getLogger("howlbert")


def _active_wolf(interaction: discord.Interaction):
    return db.get_user(interaction.user.id)


class Scene(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    scene = app_commands.Group(name="scene", description="Run roleplay scenes in threads with a roster.")

    @scene.command(name="start", description="Open an RP scene as a thread in this channel.")
    @app_commands.describe(name="Scene title", topic="What's happening (optional)")
    async def start(
        self, interaction: discord.Interaction, name: str, topic: str | None = None
    ):
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=reply_ephemeral())
            return
        wolf = _active_wolf(interaction)
        if not wolf:
            await interaction.response.send_message("Use `/register` first.", ephemeral=reply_ephemeral())
            return
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                embed=howlbert_embed("Wrong Place", "Start a scene in a normal text channel, not a thread/DM.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        perms = channel.permissions_for(interaction.guild.me)
        if not perms.create_public_threads:
            await interaction.response.send_message(
                embed=howlbert_embed("Missing Permission", "I need **Create Public Threads** here.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return

        await interaction.response.defer(ephemeral=reply_ephemeral())
        title = name.strip()[:90] or "Scene"
        try:
            thread = await channel.create_thread(
                name=title,
                type=discord.ChannelType.public_thread,
                reason=f"RP scene by {interaction.user}",
            )
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send(
                embed=howlbert_embed("Could Not Open", "Failed to create the scene thread.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return

        world = db.get_world(interaction.guild.id)
        day = int(world["day_number"]) if world else 0
        scene_id = db.create_scene(interaction.guild.id, thread.id, title, topic, interaction.user.id, day)
        db.join_scene(scene_id, wolf["id"], wolf["wolf_name"], interaction.user.id)

        body = topic.strip() if topic else "_The scene is set. Wolves, take your places._"
        opening = howlbert_embed(f"🎬 {title}", body, color=SUCCESS_COLOR)
        opening.add_field(name="Opened by", value=f"**{wolf['wolf_name']}**", inline=True)
        opening.set_footer(text="/scene join · /scene here · /scene poke · /scene end")
        try:
            await thread.send(embed=opening)
        except discord.HTTPException:
            pass

        scene = db.get_scene_by_thread(thread.id)
        if scene:
            await refresh_scene_roster(self.bot, scene)

        await interaction.followup.send(
            embed=howlbert_embed("Scene Opened", f"{thread.mention} is live as **{wolf['wolf_name']}**.", color=SUCCESS_COLOR),
            ephemeral=reply_ephemeral(),
        )

    def _scene_here(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.Thread):
            return None, "Use this **inside a scene thread**."
        scene = db.get_scene_by_thread(channel.id)
        if not scene or scene["status"] != "open":
            return None, "No open scene here. Start one with `/scene start`."
        return scene, None

    async def _maybe_auto_join(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        channel = message.channel
        if not isinstance(channel, discord.Thread):
            return
        scene = db.get_scene_by_thread(channel.id)
        if not scene or scene["status"] != "open":
            return
        wolf = db.get_user(message.author.id)
        if not wolf:
            return
        members = db.get_scene_members(scene["id"])
        if any(int(m["wolf_id"]) == int(wolf["id"]) for m in members):
            return
        db.join_scene(scene["id"], wolf["id"], wolf["wolf_name"], message.author.id)
        await refresh_scene_roster(self.bot, scene)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self._maybe_auto_join(message)

    @scene.command(name="join", description="Join the scene in this thread as your active wolf.")
    async def join(self, interaction: discord.Interaction):
        wolf = _active_wolf(interaction)
        if not wolf:
            await interaction.response.send_message("Use `/register` first.", ephemeral=reply_ephemeral())
            return
        scene, err = self._scene_here(interaction)
        if err:
            await interaction.response.send_message(embed=howlbert_embed("No Scene", err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.join_scene(scene["id"], wolf["id"], wolf["wolf_name"], interaction.user.id)
        await refresh_scene_roster(self.bot, scene)
        await interaction.response.send_message(
            embed=howlbert_embed("Joined Scene", f"**{wolf['wolf_name']}** steps in.", color=SUCCESS_COLOR)
        )

    @scene.command(name="leave", description="Leave the scene in this thread.")
    async def leave(self, interaction: discord.Interaction):
        wolf = _active_wolf(interaction)
        if not wolf:
            await interaction.response.send_message("Use `/register` first.", ephemeral=reply_ephemeral())
            return
        scene, err = self._scene_here(interaction)
        if err:
            await interaction.response.send_message(embed=howlbert_embed("No Scene", err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        left = db.leave_scene(scene["id"], wolf["id"])
        if left:
            await refresh_scene_roster(self.bot, scene)
        msg = f"**{wolf['wolf_name']}** slips away." if left else "You weren't in this scene."
        await interaction.response.send_message(embed=howlbert_embed("Scene", msg, color=SUCCESS_COLOR))

    @scene.command(name="here", description="Show who's in this scene.")
    async def here(self, interaction: discord.Interaction):
        scene, err = self._scene_here(interaction)
        if err:
            await interaction.response.send_message(embed=howlbert_embed("No Scene", err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        members = db.get_scene_members(scene["id"])
        embed = build_roster_embed(scene, members)
        await interaction.response.send_message(embed=embed)

    @scene.command(name="poke", description="Ping everyone in this scene.")
    @app_commands.describe(note="Optional note with the ping")
    async def poke(self, interaction: discord.Interaction, note: str | None = None):
        scene, err = self._scene_here(interaction)
        if err:
            await interaction.response.send_message(embed=howlbert_embed("No Scene", err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        members = db.get_scene_members(scene["id"])
        if not members:
            await interaction.response.send_message(
                embed=howlbert_embed("Empty Scene", "No one has joined yet.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        mentions = " ".join(f"<@{m['discord_id']}>" for m in members)
        wolf = _active_wolf(interaction)
        who = wolf["wolf_name"] if wolf else interaction.user.display_name
        body = note.strip() if note else "_The scene stirs._"
        await interaction.response.send_message(
            f"🎬 **{scene['name']}** — **{who}** calls the scene.\n{body}\n{mentions}"
        )

    @scene.command(name="end", description="Close this scene (scene owner or admin).")
    async def end(self, interaction: discord.Interaction):
        scene, err = self._scene_here(interaction)
        if err:
            await interaction.response.send_message(embed=howlbert_embed("No Scene", err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if interaction.user.id != int(scene["owner_discord_id"]) and not is_howlbert_admin(interaction):
            await interaction.response.send_message(
                embed=howlbert_embed("Not Yours", "Only the scene's opener or an admin can end it.", color=ERROR_COLOR),
                ephemeral=reply_ephemeral(),
            )
            return
        db.close_scene(scene["id"])
        await interaction.response.send_message(
            embed=howlbert_embed("Scene Ended", f"**{scene['name']}** is closed. Thanks for playing.", color=SUCCESS_COLOR)
        )
        channel = interaction.channel
        if isinstance(channel, discord.Thread):
            try:
                await channel.edit(archived=True, locked=False)
            except (discord.Forbidden, discord.HTTPException):
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Scene(bot))
