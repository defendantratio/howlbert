"""Role-specific quests, events, and Maw faith commands."""

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from engine.activities import accept_quest
from engine.character import parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from engine.role_content import pick_prophecy, pick_role_event
from rpg_rules import ROLE_FEATURES, ROLE_LABELS
from utils.currency import format_bones
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from utils.views import make_quest_accept_view


class RoleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="role",
        description="Role quests, role events, or Drown-Sick prophecy.",
    )
    @app_commands.describe(action="quests, event, or prophecy")
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Role quests", value="quests"),
            app_commands.Choice(name="Role event", value="event"),
            app_commands.Choice(name="Prophecy (Drown-Sick)", value="prophecy"),
        ]
    )
    async def role(self, interaction: discord.Interaction, action: str):
        if action == "quests":
            await self._rolequests(interaction)
        elif action == "event":
            await self._roleevent(interaction)
        elif action == "prophecy":
            await self._prophecy(interaction)

    async def _rolequests(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return

        role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
        label = ROLE_LABELS.get(role, role.title())
        rows = db.get_role_quests(interaction.user.id)

        if not rows:
            embed = howlbert_embed(
                f"Role Quests: {label}",
                "No role quests available right now. You may have finished them all, "
                "or none are posted for your path yet.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = howlbert_embed(
            f"Role Quests: {label}",
            "Quests only your role can take. Accept with the buttons below.",
        )
        for q in rows[:8]:
            pack_note = ""
            if q["required_pack"]:
                pack_note = f" _(requires {q['required_pack'].title()} pack)_"
            from engine.quest_rewards import format_quest_reward_line

            reward_line = format_quest_reward_line(q["key"], q["reward_bones"])
            embed.add_field(
                name=f"{q['title']} ({q['difficulty']}); {reward_line}",
                value=f"`{q['key']}`; {q['description']}{pack_note}",
                inline=False,
            )
        view = make_quest_accept_view(rows[:8])
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def _roleevent(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        from engine.blooding import blooding_gate_message

        gate = blooding_gate_message(user)
        if gate:
            embed = howlbert_embed("Not Blooded", gate, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        world = db.get_world(interaction.guild.id)
        day = world["day_number"]
        if user["last_role_event_day"] >= day:
            embed = howlbert_embed(
                "Already Lived This Day",
                "Your role's story for this rollover has played out. Wait for the den to roll over.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
        event = pick_role_event(role)
        body = event["text"]
        success = True
        roll_note = ""

        if event.get("skill"):
            profs = parse_proficiencies(user["skill_proficiencies"])
            skill = event["skill"]
            result = resolve_check(
                user,
                attr_keys=_skill_attrs(skill),
                skill=skill.title(),
                dc=event["dc"],
                proficient=skill in profs,
                skill_key=skill,
                game_day=day,
            )
            success = result["success"]
            roll_note = "\n\n" + format_roll_result(result)

        if success:
            outcome = event["success"]
            if event.get("prophecy"):
                prophecy = pick_prophecy()
                outcome += f"\n\n**Prophecy:** _{prophecy}_"
            db.add_bones(interaction.user.id, event["bones"])
            if event.get("standing"):
                kick = db.adjust_wolf_standing(interaction.user.id, event["standing"])
                if kick == "kicked":
                    outcome += "\n\n**Cast out**; your standing fell too low. You walk as a **loner** now."
            color = SUCCESS_COLOR
        else:
            outcome = event["failure"]
            color = ERROR_COLOR
            if event.get("standing_fail"):
                kick = db.adjust_wolf_standing(interaction.user.id, event["standing_fail"])
                if kick == "kicked":
                    outcome += "\n\n**Cast out**; the den will not keep you. You are a **loner** now."

        db.update_user(interaction.user.id, wolf_id=user["id"], last_role_event_day=day)

        from engine.disease_contract import try_mistmoor_swamp_exposure

        user = db.get_user(interaction.user.id)
        if role == "drown_sick":
            swamp_note = try_mistmoor_swamp_exposure(
                user, belly_rip=event.get("title") == "Belly-Rip Vigil"
            )
            if swamp_note:
                outcome += f"\n\n{swamp_note}"

        embed = howlbert_embed(event["title"], body + roll_note + f"\n\n{outcome}", color=color)
        if success and event.get("bones"):
            embed.add_field(name="Earned", value=format_bones(event["bones"], signed=True), inline=True)
        if success and event.get("standing"):
            embed.add_field(name="Standing", value=f"+{event['standing']}", inline=True)
        if not success and event.get("standing_fail"):
            embed.add_field(name="Standing", value=str(event["standing_fail"]), inline=True)
        feature = ROLE_FEATURES.get(role)
        if feature:
            footer = f"{ROLE_LABELS.get(role, role)} · {feature}"
            if len(footer) > 256:
                footer = footer[:253] + "…"
            embed.set_footer(text=footer)
        await interaction.response.send_message(embed=embed)

    async def _prophecy(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
        if role != "drown_sick":
            embed = howlbert_embed(
                "Not Drown-Sick",
                "Only wolves who fell into the Belly-Rip and rose changed can hear prophecies. "
                f"Your role: **{ROLE_LABELS.get(role, role)}**.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.get_world(interaction.guild.id)
        day = world["day_number"]
        if user["last_prophecy_day"] >= day:
            embed = howlbert_embed(
                "The Chewing Fades",
                "The Belly-Rip is quiet for you today. Return after the den rolls over.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from engine.lexicon import season_display

        line = pick_prophecy()
        season = season_display(world.get("season", "autumn"))
        weather = world.get("weather", "fog")
        db.update_user(interaction.user.id, wolf_id=user["id"], last_prophecy_day=day)
        embed = howlbert_embed(
            "Prophecy from the Dark Water",
            f"You press your nose to the mud. The chewing slows.\n\n**_{line}_**\n\n"
            f"The moon feels closer tonight. ({season}, {weather})",
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="It will make sense when it happens; or after it does.")
        await interaction.response.send_message(embed=embed)


def _skill_attrs(skill: str) -> tuple[str, ...]:
    from rpg_rules import SKILLS

    if skill in SKILLS:
        return SKILLS[skill][0]
    return ("attr_wis",)


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleCog(bot))
