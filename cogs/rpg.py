import discord
from discord import app_commands
from discord.ext import commands

import database as db
from rpg_rules import DC_TIERS, ROLE_LABELS, SKILLS
from engine.character import attr_modifier, parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from engine.shop_items import consume_item_by_key, has_item
from engine.role_features import can_use_role_reroll, has_any_role
from engine.role_privileges import HERB_HEAL_DAILY_LIMIT, herb_heal_limit_reached
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed

class Rpg(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="rpg",
        description="Roll checks, set attributes, or delete your profile.",
    )
    @app_commands.describe(
        action="roll, setstats, or delete",
        skill="Skill to roll (roll)",
        attribute="Raw attribute check (roll)",
        dc="Difficulty (roll)",
        use_safe_roll="Spend a Safe Roll on failure (roll)",
        use_role_reroll="Elder/Diplomat role reroll on failure (roll)",
        strength="Strength 1-10 (setstats)",
        dexterity="Dexterity 1-10 (setstats)",
        constitution="Constitution 1-10 (setstats)",
        intelligence="Intelligence 1-10 (setstats)",
        charisma="Charisma 1-10 (setstats)",
        wisdom="Wisdom 1-10 (setstats)",
        confirm="Type DELETE to confirm profile deletion",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Roll a check", value="roll"),
            app_commands.Choice(name="Set attributes", value="setstats"),
            app_commands.Choice(name="Delete profile", value="delete"),
        ],
        skill=[
            app_commands.Choice(name=label, value=key)
            for key, (_, label) in SKILLS.items()
        ],
        attribute=[
            app_commands.Choice(name="Strength", value="attr_str"),
            app_commands.Choice(name="Dexterity", value="attr_dex"),
            app_commands.Choice(name="Survival / Constitution", value="attr_con"),
            app_commands.Choice(name="Intelligence", value="attr_int"),
            app_commands.Choice(name="Charisma", value="attr_cha"),
            app_commands.Choice(name="Wisdom", value="attr_wis"),
        ],
        dc=[
            app_commands.Choice(name="Easy (10): Routine", value=10),
            app_commands.Choice(name="Moderate (15): Challenging", value=15),
            app_commands.Choice(name="Hard (20): Desperate", value=20),
            app_commands.Choice(name="Legendary (25): Nearly impossible", value=25),
        ],
    )
    async def rpg_hub(
        self,
        interaction: discord.Interaction,
        action: str,
        skill: str | None = None,
        attribute: str | None = None,
        dc: app_commands.Range[int, 1, 40] = 15,
        use_safe_roll: bool = False,
        use_role_reroll: bool = False,
        strength: app_commands.Range[int, 1, 10] | None = None,
        dexterity: app_commands.Range[int, 1, 10] | None = None,
        constitution: app_commands.Range[int, 1, 10] | None = None,
        intelligence: app_commands.Range[int, 1, 10] | None = None,
        charisma: app_commands.Range[int, 1, 10] | None = None,
        wisdom: app_commands.Range[int, 1, 10] | None = None,
        confirm: str | None = None,
    ):
        if action == "roll":
            await self._roll(
                interaction, skill, attribute, dc, use_safe_roll, use_role_reroll
            )
        elif action == "setstats":
            if None in (strength, dexterity, constitution, intelligence, charisma, wisdom):
                embed = howlbert_embed(
                    "Missing Stats",
                    "Provide all six attributes for **setstats**.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            await self._setstats(
                interaction, strength, dexterity, constitution, intelligence, charisma, wisdom
            )
        elif action == "delete":
            await self._deleteprofile(interaction, confirm or "")

    async def _roll(
        self,
        interaction: discord.Interaction,
        skill: str | None = None,
        attribute: str | None = None,
        dc: app_commands.Range[int, 1, 40] = 15,
        use_safe_roll: bool = False,
        use_role_reroll: bool = False,
    ):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not skill and not attribute:
            embed = howlbert_embed(
                "Choose a Check",
                "Pick a **skill** (e.g. Tracking) or an **attribute** (e.g. Wisdom).",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if use_safe_roll and not has_item(interaction.user.id, "safe_roll"):
            embed = howlbert_embed(
                "No Safe Roll",
                "Buy a **Safe Roll** from `/bones action:shop` or set `use_safe_roll:false`.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        day = 0
        if interaction.guild_id:
            world = db.get_world(interaction.guild_id)
            if world:
                day = int(world["day_number"])

        def _role_reroll_allowed(check_result: dict) -> bool:
            if not use_role_reroll or check_result["success"]:
                return False
            if check_result["outcome"] == "critical_failure":
                return False
            if not can_use_role_reroll(user, day):
                return False
            if has_any_role(user, "elder") and skill:
                return True
            if has_any_role(user, "diplomat"):
                if attribute == "attr_cha":
                    return True
                if skill:
                    attr_keys, _ = SKILLS[skill]
                    return "attr_cha" in attr_keys
            return False

        role_reroll_note = ""
        if skill:
            attr_keys, skill_label = SKILLS[skill]
            result = resolve_check(
                user,
                attr_keys=attr_keys,
                skill=skill_label,
                dc=dc,
                proficient=False,
                allow_safe_roll=use_safe_roll,
                has_safe_roll=use_safe_roll and has_item(interaction.user.id, "safe_roll"),
                skill_key=skill,
                game_day=day or None,
            )
            title = f"{skill_label} Check"
            if _role_reroll_allowed(result):
                first_die = result["die"]
                result = resolve_check(
                    user,
                    attr_keys=attr_keys,
                    skill=skill_label,
                    dc=dc,
                    proficient=False,
                    skill_key=skill,
                    game_day=day or None,
                )
                role_reroll_note = (
                    f"🎲 **Role reroll**; first die was **{first_die}**; rolled again.\n"
                )
                db.update_user(
                    interaction.user.id, wolf_id=user["id"], last_role_reroll_day=day
                )
        else:
            label_map = {
                "attr_str": "Strength",
                "attr_dex": "Dexterity",
                "attr_con": "Survival / Constitution",
                "attr_int": "Intelligence",
                "attr_cha": "Charisma",
                "attr_wis": "Wisdom",
            }
            result = resolve_check(
                user,
                attr_keys=(attribute,),
                skill=label_map.get(attribute, attribute),
                dc=dc,
                proficient=False,
                allow_safe_roll=use_safe_roll,
                has_safe_roll=use_safe_roll and has_item(interaction.user.id, "safe_roll"),
                game_day=day or None,
            )
            title = f"{label_map.get(attribute, 'Attribute')} Check"
            if _role_reroll_allowed(result):
                first_die = result["die"]
                result = resolve_check(
                    user,
                    attr_keys=(attribute,),
                    skill=label_map.get(attribute, attribute),
                    dc=dc,
                    proficient=False,
                    game_day=day or None,
                )
                role_reroll_note = (
                    f"🎲 **Role reroll**; first die was **{first_die}**; rolled again.\n"
                )
                db.update_user(
                    interaction.user.id, wolf_id=user["id"], last_role_reroll_day=day
                )

        if result.get("safe_roll_used"):
            consume_item_by_key(interaction.user.id, "safe_roll")

        setback_note = ""
        if skill:
            from engine.character_traits import (
                maybe_apply_failure_setback,
                maybe_apply_success_recovery,
            )

            if not result["success"]:
                setback_note = maybe_apply_failure_setback(
                    user,
                    skill_key=skill,
                    outcome=result["outcome"],
                    game_day=day or None,
                    total=result["total"],
                    dc=dc,
                )
            else:
                setback_note = maybe_apply_success_recovery(
                    user, skill_key=skill, game_day=day or None, dc=dc
                )
            if setback_note:
                setback_note = f"\n{setback_note}"

        color = SUCCESS_COLOR if result["success"] else ERROR_COLOR
        body = role_reroll_note + format_roll_result(result) + setback_note
        embed = howlbert_embed(title, body, color=color)
        tier_name = next((k for k, v in DC_TIERS.items() if v == dc), None)
        if tier_name:
            embed.set_footer(text=f"DC tier: {tier_name.title()} ({dc})")
        await interaction.response.send_message(embed=embed)

    async def _deleteprofile(self, interaction: discord.Interaction, confirm: str):
        if confirm.strip().upper() != "DELETE":
            embed = howlbert_embed(
                "Not Confirmed",
                "Re-run with `confirm: DELETE` to permanently remove your wolf.\n"
                "Your account prestige and legacy are **kept**.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed(
                "Not Registered",
                "You don't have a wolf profile to delete.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        wolf_name = user["wolf_name"]
        outcome = db.delete_wolf_profile(interaction.user.id)

        if outcome == "alpha_transfer":
            embed = howlbert_embed(
                "Cannot Delete",
                "You're the Alpha of a den with other wolves. Transfer leadership "
                "or leave the pack before deleting your profile.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = howlbert_embed("Profile Deleted", color=SUCCESS_COLOR)
        embed.description = (
            f"**{wolf_name}** has left the wild.\n"
            "Prestige and legacy on your account are unchanged."
        )
        remaining = db.count_user_wolves(interaction.user.id)
        if remaining:
            active = db.get_user(interaction.user.id)
            if active:
                embed.add_field(
                    name="Active Wolf",
                    value=f"Now playing as **{active['wolf_name']}**.",
                    inline=False,
                )
        else:
            embed.set_footer(text="Use /register to create a new wolf.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


    async def _setstats(
        self,
        interaction: discord.Interaction,
        strength: app_commands.Range[int, 1, 10],
        dexterity: app_commands.Range[int, 1, 10],
        constitution: app_commands.Range[int, 1, 10],
        intelligence: app_commands.Range[int, 1, 10],
        charisma: app_commands.Range[int, 1, 10],
        wisdom: app_commands.Range[int, 1, 10],
    ):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed("Not Registered", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        stats = {
            "attr_str": strength,
            "attr_dex": dexterity,
            "attr_con": constitution,
            "attr_int": intelligence,
            "attr_cha": charisma,
            "attr_wis": wisdom,
        }
        role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
        from engine.conditions import validate_stats

        error = validate_stats(role, stats)
        if error:
            from rpg_rules import ROLE_ATTRIBUTE_RANGES, ROLE_LABELS

            lo, hi = ROLE_ATTRIBUTE_RANGES.get(role, (16, 20))
            embed = howlbert_embed(
                "Invalid Spread",
                f"{error}\n\nYour role **{ROLE_LABELS.get(role, role)}** allows total **{lo}–{hi}**.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        db.set_user_stats(interaction.user.id, stats)
        total = sum(stats.values())
        from engine.character import compute_max_hp, format_max_hp_breakdown

        max_hp = compute_max_hp(strength, constitution)
        embed = howlbert_embed("Stats Updated", color=SUCCESS_COLOR)
        embed.description = (
            f"STR {strength} · DEX {dexterity} · CON {constitution}\n"
            f"INT {intelligence} · CHA {charisma} · WIS {wisdom}\n"
            f"**Total: {total}**\n"
            f"**Max HP:** {format_max_hp_breakdown(strength, constitution, max_hp=max_hp)}"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="vitals",
        description="View conditions or rest.",
    )
    @app_commands.describe(
        action="condition or rest",
        rest_type="Short or long rest (rest)",
        use_herb="Use comfrey for short rest healing (rest)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="View conditions", value="condition"),
            app_commands.Choice(name="Rest", value="rest"),
        ],
        rest_type=[
            app_commands.Choice(name="Long rest (6-8 hours sleep)", value="long"),
            app_commands.Choice(name="Short rest (10-30 min)", value="short"),
        ],
    )
    async def vitals(
        self,
        interaction: discord.Interaction,
        action: str,
        rest_type: str = "long",
        use_herb: bool = False,
    ):
        if action == "condition":
            await self._condition(interaction)
        elif action == "rest":
            await self._rest(interaction, rest_type, use_herb)

    async def _condition(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed("Not Registered", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from engine.character import format_max_hp_breakdown
        from engine.conditions import format_conditions
        from engine.exhaustion_effects import effective_max_hp, user_exhaustion
        from engine.hunger import format_hunger_line
        from engine.mood import format_mood_line
        from engine.thirst import format_thirst_line

        day = None
        if interaction.guild_id:
            world = db.get_world(interaction.guild_id)
            if world:
                day = world["day_number"]

        embed = howlbert_embed(
            f"{user['wolf_name']}: Conditions",
            format_conditions(user, day=day),
        )
        str_val = int(user["attr_str"]) if "attr_str" in user.keys() else 5
        con_val = int(user["attr_con"]) if "attr_con" in user.keys() else 5
        embed.add_field(
            name="HP",
            value=(
                f"{user['hp']}/{effective_max_hp(user)}\n"
                f"{format_max_hp_breakdown(str_val, con_val, max_hp=int(user['max_hp']))}"
                + (
                    f"\n_(exhaustion cap {effective_max_hp(user)}; base {user['max_hp']})_"
                    if user_exhaustion(user) >= 4
                    else ""
                )
            ),
            inline=True,
        )
        embed.add_field(name="Mood", value=format_mood_line(user), inline=True)
        embed.add_field(name="Hunger", value=format_hunger_line(user), inline=True)
        embed.add_field(name="Thirst", value=format_thirst_line(user), inline=True)
        from engine.treatment_plan import build_treatment_checklist

        checklist = build_treatment_checklist(user, day=day)
        embed.add_field(name="Treatment plan", value=checklist, inline=False)
        from engine.healer_refusal import healer_refusal_reminder

        refusal = healer_refusal_reminder(user, pack_id=user["pack_id"] if user["pack_id"] else None)
        if refusal:
            embed.add_field(name="Healer's Code", value=refusal, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _rest(
        self,
        interaction: discord.Interaction,
        rest_type: str = "long",
        use_herb: bool = False,
    ):
        import random

        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed("Not Registered", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        world = db.get_world(interaction.guild.id)
        day = world["day_number"]

        if rest_type == "long":
            if user["last_rest_day"] >= day:
                embed = howlbert_embed("Already Rested", "You took a long rest this rollover.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            from engine.conditions import apply_long_rest_healing

            new_hp, exhaustion = apply_long_rest_healing(user)
            db.set_user_conditions(
                interaction.user.id,
                hp=new_hp,
                exhaustion=exhaustion,
                last_rest_day=day,
                herb_heals_today=0,
            )
            embed = howlbert_embed(
                "Long Rest",
                f"Recovered **1 HP** (now {new_hp}/{user['max_hp']}).\n"
                f"Exhaustion: {user['exhaustion']} → {exhaustion}",
                color=SUCCESS_COLOR,
            )
            await interaction.response.send_message(embed=embed)
            return

        if herb_heal_limit_reached(user):
            embed = howlbert_embed(
                "Limit Reached",
                f"You can only use comfrey on short rest **{HERB_HEAL_DAILY_LIMIT}** times per sunrise.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        heal = 0
        if use_herb:
            item = db.get_item_by_key("herb_comfrey")
            if not item or db.get_inventory_quantity(interaction.user.id, item["id"]) < 1:
                embed = howlbert_embed("No Comfrey", "You need comfrey in your inventory.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            heal = random.randint(1, 4) + 1
            db.consume_item(interaction.user.id, item["id"])

        new_hp = min(user["max_hp"], user["hp"] + heal) if heal else user["hp"]
        db.set_user_conditions(
            interaction.user.id,
            hp=new_hp,
            herb_heals_today=user["herb_heals_today"] + (1 if heal else 0),
        )
        msg = f"Short rest." + (f" Comfrey healed **{heal} HP** (now {new_hp}/{user['max_hp']})." if heal else " No herb used.")
        embed = howlbert_embed("Short Rest", msg, color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Rpg(bot))
