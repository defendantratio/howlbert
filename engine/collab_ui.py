"""Refresh collab hunt/patrol channel posts after completion."""

from __future__ import annotations

import discord
from discord.ext import commands

import database as db
from engine.collab_hunt import build_collab_hunt_embed
from engine.collab_patrol import build_collab_patrol_embed


def _disabled_view(*, trail: bool = False, war: bool = False) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    if war:
        join_label = "Join war patrol"
    else:
        join_label = "Join trail" if trail else "Join patrol"
    for label in (join_label, "Set out", "Cancel"):
        view.add_item(
            discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, disabled=True)
        )
    return view


async def refresh_collab_hunt_post(bot: commands.Bot, hunt_id: int) -> None:
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt or not hunt["message_id"]:
        return
    channel = bot.get_channel(hunt["channel_id"])
    if not channel:
        return
    try:
        msg = await channel.fetch_message(hunt["message_id"])
        await msg.edit(embed=build_collab_hunt_embed(hunt_id), view=_disabled_view())
    except discord.HTTPException:
        pass


async def refresh_collab_patrol_post(bot: commands.Bot, patrol_id: int) -> None:
    patrol = db.get_collab_patrol(patrol_id)
    if not patrol or not patrol["message_id"]:
        return
    channel = bot.get_channel(patrol["channel_id"])
    if not channel:
        return
    trail = "patrol_kind" in patrol.keys() and patrol["patrol_kind"] == "trail"
    war = "patrol_kind" in patrol.keys() and patrol["patrol_kind"] == "war_patrol"
    try:
        msg = await channel.fetch_message(patrol["message_id"])
        await msg.edit(
            embed=build_collab_patrol_embed(patrol_id),
            view=_disabled_view(trail=trail, war=war),
        )
    except discord.HTTPException:
        pass


async def post_collab_hunt_prey_pile(
    bot: commands.Bot,
    channel: discord.abc.Messageable,
    hunt_id: int,
) -> bool:
    """Lay caller's fresh kill at the den after a successful pack hunt."""
    hunt = db.get_collab_hunt(hunt_id)
    if not hunt or hunt["status"] != "done":
        return False
    leader = db.get_user_by_id(hunt["leader_wolf_id"])
    if not leader:
        return False
    world = db.get_world(hunt["guild_id"])
    stack = db.pick_prey_stack_for_pile(leader["id"], world["day_number"])
    if not stack:
        return False

    from cogs.prey_pile import post_prey_pile_to_channel
    from engine.prey_items import prey_meta

    pile_bones = stack["bone_value"]
    pile_label = prey_meta(stack["prey_key"])["label"]
    db.remove_prey_stack(stack["id"])
    await post_prey_pile_to_channel(
        bot,
        channel,
        leader,
        prey_bones=pile_bones,
        prey_label=pile_label,
        day_number=world["day_number"],
    )

    row = db.get_collab_hunt(hunt_id)
    note = "\n\n**fresh-kill cache** open below; packmates choose how to respond."
    if row and row["result_text"] and "fresh-kill cache" not in row["result_text"]:
        db.set_collab_hunt_status(hunt_id, "done", result_text=row["result_text"] + note)
    return True
