import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import GREAT_PACKS, GREAT_PACK_PATH_TIERS, PRESTIGE_TIERS
from engine.prestige import bone_bonus_pct, get_tier_info, next_tier_requirements
from utils.currency import format_bones
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed

PRESTIGE_ACTIONS = [
    app_commands.Choice(name="View tier", value="view"),
    app_commands.Choice(name="Requirements", value="require"),
    app_commands.Choice(name="Bonuses", value="bonus"),
    app_commands.Choice(name="Legacy", value="legacy"),
    app_commands.Choice(name="Retire wolf", value="retire"),
    app_commands.Choice(name="Hall of fame", value="halloffame"),
]


class Prestige(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="prestige",
        description="Prestige tier, legacy, retirement, and hall of fame.",
    )
    @app_commands.describe(action="What to view or do")
    @app_commands.choices(action=PRESTIGE_ACTIONS)
    async def prestige(self, interaction: discord.Interaction, action: str = "view"):
        if action == "view":
            await self._prestige_view(interaction)
        elif action == "require":
            await self._prestige_require(interaction)
        elif action == "bonus":
            await self._prestige_bonus(interaction)
        elif action == "legacy":
            await self._legacy(interaction)
        elif action == "retire":
            await self._retire(interaction)
        elif action == "halloffame":
            await self._halloffame(interaction)

    async def _prestige_view(self, interaction: discord.Interaction):
        if not db.get_user(interaction.user.id):
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return

        account = db.get_account(interaction.user.id)
        user = db.get_user(interaction.user.id)
        info = get_tier_info(account["prestige_tier"])

        embed = howlbert_embed(f"Tier {info['tier']}; {info['name']}", info["lore"])
        embed.add_field(name="Legacy Score", value=str(account["legacy_score"]), inline=True)
        embed.add_field(name="Bone Bonus", value=f"+{bone_bonus_pct(account['prestige_tier'])}%", inline=True)
        if user["great_pack"] and user["great_pack"] in GREAT_PACK_PATH_TIERS:
            embed.add_field(
                name="Great Pack Path",
                value=GREAT_PACK_PATH_TIERS[user["great_pack"]],
                inline=False,
            )
        if info["title"]:
            embed.set_footer(text=f"Title: [{info['title']}]")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _prestige_require(self, interaction: discord.Interaction):
        if not db.get_user(interaction.user.id):
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return

        account = db.get_account(interaction.user.id)
        nxt = next_tier_requirements(account["prestige_tier"])
        if not nxt:
            embed = howlbert_embed("Peak Prestige", "You stand at **The Sunderer**; the summit of legend.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = howlbert_embed(f"Next: Tier {nxt['tier']}; {nxt['name']}", nxt["lore"])
        embed.add_field(
            name="Legacy",
            value=f"{account['legacy_score']} / {nxt['legacy_req']}",
            inline=True,
        )
        embed.add_field(
            name="Quests",
            value=f"{account['total_quests']} / {nxt['quests_req']}",
            inline=True,
        )
        embed.add_field(
            name="Hunts",
            value=f"{account['total_hunts']} / {nxt['hunts_req']}",
            inline=True,
        )
        embed.add_field(
            name="Retirements",
            value=f"{account['total_retirements']} / {nxt['retirements_req']}",
            inline=True,
        )
        embed.add_field(
            name="Unlocks",
            value=f"+{nxt['bone_bonus_pct']}% bone gain from hunts & daily",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _prestige_bonus(self, interaction: discord.Interaction):
        if not db.get_user(interaction.user.id):
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return

        account = db.get_account(interaction.user.id)
        lines = []
        for info in PRESTIGE_TIERS:
            if info["tier"] <= account["prestige_tier"] and info["tier"] > 0:
                lines.append(f"**Tier {info['tier']} {info['name']}**; unlocked")

        if not lines:
            lines.append("No bonuses yet. Complete quests and build your legacy.")

        embed = howlbert_embed(
            f"Active Bonuses (+{bone_bonus_pct(account['prestige_tier'])}% total)",
            "\n".join(lines),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _legacy(self, interaction: discord.Interaction):
        if not db.get_user(interaction.user.id):
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return

        account = db.get_account(interaction.user.id)
        retired = db.get_retired_wolves(interaction.user.id)

        embed = howlbert_embed("Your Legacy", f"**{account['legacy_score']}** legacy across the bloodline.")
        embed.add_field(name="Wolves Retired", value=str(account["total_retirements"]), inline=True)
        embed.add_field(name="Quests Completed", value=str(account["total_quests"]), inline=True)
        embed.add_field(name="Hunts Logged", value=str(account["total_hunts"]), inline=True)

        if retired:
            lines = [
                f"**{r['wolf_name']}**; +{r['legacy_contribution']} legacy"
                for r in retired[:5]
            ]
            embed.add_field(name="Dynasty", value="\n".join(lines), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _retire(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return

        result = db.retire_wolf(interaction.user.id)
        if not result:
            await interaction.response.send_message("Retirement failed.", ephemeral=True)
            return

        legacy_gain, tier = result
        info = get_tier_info(tier)
        embed = howlbert_embed(
            f"{user['wolf_name']} Enters the Dynasty",
            f"**{user['wolf_name']}** is remembered. Their deeds echo in the bloodline.",
            color=SUCCESS_COLOR,
        )
        embed.add_field(name="Legacy Gained", value=f"+{legacy_gain}", inline=True)
        embed.add_field(name="Prestige Tier", value=f"{info['name']}", inline=True)
        embed.set_footer(text="Your wolf still walks the wild; but their legend is etched.")
        await interaction.response.send_message(embed=embed)

    async def _halloffame(self, interaction: discord.Interaction):
        rows = db.get_hall_of_fame(10)
        if not rows:
            embed = howlbert_embed("Hall of Fame", "No legends recorded yet.")
            await interaction.response.send_message(embed=embed)
            return

        lines = []
        for i, row in enumerate(rows, 1):
            user = db.get_user(row["discord_id"])
            name = user["wolf_name"] if user else f"Wolf #{row['discord_id']}"
            info = get_tier_info(row["prestige_tier"])
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"**{i}.**")
            lines.append(f"{medal} {name}; {row['legacy_score']} legacy ({info['name']})")

        embed = howlbert_embed("Hall of Fame", "\n".join(lines))
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Prestige(bot))
