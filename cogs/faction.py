"""Human faction relations: observe, approach, trade, raid, sabotage."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from engine.faction import (
    FACTIONS,
    OAK_KNOT_THRESHOLD,
    standing_label,
    faction_display_name,
    try_faction_approach,
    try_faction_observe,
    try_faction_raid,
    try_faction_sabotage,
    try_faction_trade,
)
from utils.embeds import EMBED_COLOR, ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from utils.replies import reply_ephemeral


def _active_wolf(interaction: discord.Interaction):
    return db.get_user(interaction.user.id)


_FACTION_CHOICES = [
    app_commands.Choice(name="lowland settlements", value="lowland_settlements"),
    app_commands.Choice(name="thorne lumber", value="thorne_lumber"),
    app_commands.Choice(name="river mill", value="river_mill"),
    app_commands.Choice(name="the crows", value="the_crows"),
    app_commands.Choice(name="university expedition", value="university_expedition"),
]

_SABOTAGE_FACTIONS = {"thorne_lumber", "river_mill"}
_RAID_FACTIONS = {"thorne_lumber", "river_mill", "lowland_settlements", "the_crows", "university_expedition"}

_PACK_TRADE_FACTIONS: dict[str, set[str]] = {
    "greyspire": {"the_crows", "lowland_settlements"},
    "silverrush": {"river_mill", "university_expedition", "lowland_settlements"},
    "mistmoor": {"lowland_settlements", "university_expedition"},
    "thistlehide": {"lowland_settlements"},
}


class Faction(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    faction = app_commands.Group(name="faction", description="human faction relations: observe, approach, trade, raid, sabotage.")

    @faction.command(name="status", description="view your pack's standing with all human factions.")
    async def status(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        user = _active_wolf(interaction)
        if not user:
            await interaction.response.send_message(howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        gp = user["great_pack"] if "great_pack" in user.keys() else None
        if not gp:
            await interaction.response.send_message(howlbert_embed("No Pack", "You must belong to a Great Pack to track faction standings.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        standings = db.get_all_faction_standings(gp)
        lines = []
        for key, label in FACTIONS.items():
            s = standings.get(key, 0)
            bar_filled = max(0, min(10, (s + 30) * 10 // 60))
            bar = "█" * bar_filled + "░" * (10 - bar_filled)
            lines.append(f"**{label}** `{bar}` {s:+} ({standing_label(s)})")
        embed = howlbert_embed(
            f"Faction Standing; {gp.title()}",
            "\n".join(lines),
            color=EMBED_COLOR,
        )
        embed.set_footer(text="actions: /faction observe · approach · trade · raid · sabotage")
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @faction.command(name="observe", description="watch a faction from a distance (flavor only; costs nothing).")
    @app_commands.describe(faction="which faction to observe")
    @app_commands.choices(faction=_FACTION_CHOICES)
    async def observe(self, interaction: discord.Interaction, faction: str):
        if not interaction.guild:
            await interaction.response.send_message(howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        user = _active_wolf(interaction)
        if not user:
            await interaction.response.send_message(howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world["day_number"] if world else 1
        gp = user["great_pack"] if "great_pack" in user.keys() else None
        if not gp:
            await interaction.response.send_message(embed=howlbert_embed("No Pack", "Faction actions require a Great Pack affiliation.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        flavor, _ = try_faction_observe(user, faction)
        standing = db.get_faction_standing(gp, faction)
        db.set_last_faction_action_day(interaction.user.id, day)
        embed = howlbert_embed(
            f"Observe; {faction_display_name(faction)}",
            flavor,
            color=EMBED_COLOR,
        )
        embed.add_field(name="Current Standing", value=f"{standing:+} ({standing_label(standing)})", inline=True)
        embed.set_footer(text="observe costs nothing · approach/trade/raid/sabotage change standing")
        await interaction.response.send_message(embed=embed)

    @faction.command(name="approach", description="attempt diplomatic contact with a faction (roll; standing change).")
    @app_commands.describe(faction="which faction to approach")
    @app_commands.choices(faction=_FACTION_CHOICES)
    async def approach(self, interaction: discord.Interaction, faction: str):
        if not interaction.guild:
            await interaction.response.send_message(howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        user = _active_wolf(interaction)
        if not user:
            await interaction.response.send_message(howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world["day_number"] if world else 1
        gp = user["great_pack"] if "great_pack" in user.keys() else None
        if not gp:
            await interaction.response.send_message(embed=howlbert_embed("No Pack", "Faction actions require a Great Pack affiliation.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        flavor, delta, bonus_bones = try_faction_approach(user, faction, day=day)
        from engine.diminishing import next_use_multiplier
        _fmult, _fn = next_use_multiplier(user, "faction_action", day)
        if delta > 0:
            delta = max(1, int(delta * _fmult))
            bonus_bones = int(bonus_bones * _fmult)
        new_standing = db.adjust_faction_standing(gp, faction, delta)
        db.set_last_faction_action_day(interaction.user.id, day)
        if _fn > 1:
            flavor += "\n_the same overture, repeated in a day, wins less ground._"
        if bonus_bones > 0:
            db.add_bones(interaction.user.id, bonus_bones, wolf_id=user["id"])
        color = SUCCESS_COLOR if delta > 0 else ERROR_COLOR
        embed = howlbert_embed(
            f"Approach; {faction_display_name(faction)}",
            flavor,
            color=color,
        )
        embed.add_field(name="Standing", value=f"{new_standing:+} ({standing_label(new_standing)})", inline=True)
        if bonus_bones > 0:
            embed.add_field(name="Cache Found", value=f"+**{bonus_bones}** bones", inline=True)
        await interaction.response.send_message(embed=embed)

    @faction.command(name="trade", description="offer resources to build standing with a faction (costs 3 bones; pack-specific access).")
    @app_commands.describe(faction="which faction to trade with")
    @app_commands.choices(faction=_FACTION_CHOICES)
    async def trade(self, interaction: discord.Interaction, faction: str):
        if not interaction.guild:
            await interaction.response.send_message(howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        user = _active_wolf(interaction)
        if not user:
            await interaction.response.send_message(howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        gp = user["great_pack"] if "great_pack" in user.keys() else None
        if not gp:
            await interaction.response.send_message(embed=howlbert_embed("No Pack", "Faction actions require a Great Pack affiliation.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        allowed = _PACK_TRADE_FACTIONS.get(gp, set())
        if faction not in allowed:
            allowed_names = ", ".join(faction_display_name(f) for f in sorted(allowed))
            await interaction.response.send_message(embed=howlbert_embed("Not Your Trade", f"**{gp.title()}** cannot trade with **{faction_display_name(faction)}**.\nAvailable: {allowed_names or 'none yet'}.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world["day_number"] if world else 1
        flavor, delta = try_faction_trade(user, faction)
        if delta == 0:
            await interaction.response.send_message(embed=howlbert_embed("Trade Failed", flavor, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.diminishing import next_use_multiplier
        _fmult, _fn = next_use_multiplier(user, "faction_action", day)
        if delta > 0:
            delta = max(1, int(delta * _fmult))
        new_standing = db.adjust_faction_standing(gp, faction, delta)
        db.set_last_faction_action_day(interaction.user.id, day)
        if _fn > 1:
            flavor += "\n_repeated tribute in one day is worth less._"
        embed = howlbert_embed(
            f"Trade; {faction_display_name(faction)}",
            flavor,
            color=SUCCESS_COLOR,
        )
        embed.add_field(name="Standing", value=f"{new_standing:+} ({standing_label(new_standing)})", inline=True)
        await interaction.response.send_message(embed=embed)

    @faction.command(name="raid", description="raid a faction's operations (aggressive; standing loss; possible injury).")
    @app_commands.describe(faction="which faction to raid")
    @app_commands.choices(faction=_FACTION_CHOICES)
    async def raid(self, interaction: discord.Interaction, faction: str):
        if not interaction.guild:
            await interaction.response.send_message(howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        user = _active_wolf(interaction)
        if not user:
            await interaction.response.send_message(howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        gp = user["great_pack"] if "great_pack" in user.keys() else None
        if not gp:
            await interaction.response.send_message(embed=howlbert_embed("No Pack", "Faction actions require a Great Pack affiliation.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world["day_number"] if world else 1
        flavor, delta, caught = try_faction_raid(user, faction)
        from engine.diminishing import next_use_multiplier
        _fmult, _fn = next_use_multiplier(user, "faction_action", day)
        new_standing = db.adjust_faction_standing(gp, faction, delta)
        db.set_last_faction_action_day(interaction.user.id, day)
        if caught:
            for f in FACTIONS:
                if f != faction:
                    db.adjust_faction_standing(gp, f, -1)
        # a successful settlement raid can carry off livestock milk; a barn
        # picked over again the same day has far less left to take
        milk_note = ""
        if not caught and faction == "lowland_settlements":
            import random as _milk_rand
            milk_item = db.get_item_by_key("liquid_milk")
            if milk_item and _milk_rand.random() < 0.6 * _fmult:
                got = _milk_rand.randint(1, 2)
                db.grant_item(interaction.user.id, milk_item["id"], got)
                milk_note = f"you knock over a pail in the barn and carry off **{got}× milk**."
        color = SUCCESS_COLOR if not caught else ERROR_COLOR
        embed = howlbert_embed(
            f"Raid; {faction_display_name(faction)}",
            flavor,
            color=color,
        )
        embed.add_field(name="Standing", value=f"{new_standing:+} ({standing_label(new_standing)})", inline=True)
        if caught:
            embed.add_field(name="Caught", value="All faction standings −1", inline=True)
        if milk_note:
            embed.add_field(name="Plunder", value=milk_note, inline=False)
        await interaction.response.send_message(embed=embed)

    @faction.command(name="sabotage", description="sabotage thorne_lumber or river_mill operations (Thistlehide/Silverrush; dc 15).")
    @app_commands.describe(faction="thorne_lumber or river_mill")
    @app_commands.choices(faction=[
        app_commands.Choice(name="thorne lumber", value="thorne_lumber"),
        app_commands.Choice(name="river mill", value="river_mill"),
    ])
    async def sabotage(self, interaction: discord.Interaction, faction: str):
        if not interaction.guild:
            await interaction.response.send_message(howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        user = _active_wolf(interaction)
        if not user:
            await interaction.response.send_message(howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        gp = user["great_pack"] if "great_pack" in user.keys() else None
        if not gp:
            await interaction.response.send_message(embed=howlbert_embed("No Pack", "Faction actions require a Great Pack affiliation.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if faction == "thorne_lumber" and gp != "thistlehide":
            await interaction.response.send_message(embed=howlbert_embed("Wrong Pack", "Only **Thistlehide** wolves have the forest access and motive to sabotage Thorne Lumber.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if faction == "river_mill" and gp != "silverrush":
            await interaction.response.send_message(embed=howlbert_embed("Wrong Pack", "Only **Silverrush** wolves know the mill well enough to sabotage it.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world["day_number"] if world else 1
        flavor, delta = try_faction_sabotage(user, faction, guild_id=interaction.guild.id, day=day)
        from engine.diminishing import next_use_multiplier
        _fmult, _fn = next_use_multiplier(user, "faction_action", day)
        if delta < 0:
            delta = min(-1, int(delta * _fmult))
        new_standing = db.adjust_faction_standing(gp, faction, delta)
        db.set_last_faction_action_day(interaction.user.id, day)
        if _fn > 1:
            flavor += "\n_a second strike the same day lands softer; they are watching now._"
        color = SUCCESS_COLOR if delta <= -3 else ERROR_COLOR
        embed = howlbert_embed(
            f"Sabotage; {faction_display_name(faction)}",
            flavor,
            color=color,
        )
        embed.add_field(name="Standing", value=f"{new_standing:+} ({standing_label(new_standing)})", inline=True)
        if faction == "thorne_lumber":
            oak = db.get_world_oak_knot(interaction.guild.id)
            embed.add_field(name="Memory-Knot", value=f"{oak}/{OAK_KNOT_THRESHOLD}", inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Faction(bot))
