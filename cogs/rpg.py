import discord
from discord import app_commands
from discord.ext import commands

import database as db
from rpg_rules import DC_TIERS, ROLE_LABELS, SKILLS
from engine.character import attr_modifier, parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from engine.shop_items import consume_item_by_key, has_item
from engine.role_features import can_use_role_reroll, has_any_role
from engine.role_privileges import HERB_HEAL_DAILY_LIMIT, herb_heal_limit_reached, treat_limit_reached
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed


async def _quarantine_own_wolf_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    active = db.get_user(interaction.user.id)
    if not active:
        return []
    choices = []
    for wolf in db.list_user_wolves(interaction.user.id):
        if wolf["id"] == active["id"]:
            continue
        name = wolf["wolf_name"]
        if current and current.lower() not in name.lower():
            continue
        choices.append(app_commands.Choice(name=name[:100], value=name))
    return choices[:25]


async def _herb_inventory_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    user = db.get_user(interaction.user.id)
    choices = []
    action = getattr(interaction.namespace, "action", None)
    prepare_action = action == "prepare"
    if user and interaction.guild:
        world = db.get_world(interaction.guild.id)
        from engine.herb_storage import format_herb_stack_line

        for stack in db.get_herb_stacks(user["id"]):
            label = format_herb_stack_line(stack, world["day_number"])
            val = f"stack:{stack['id']}"
            if current and current.lower() not in label.lower() and current not in val:
                continue
            choices.append(app_commands.Choice(name=label[:100], value=val))
    items = db.get_inventory(interaction.user.id)
    for row in items:
        if not row["key"].startswith("herb_") and row["key"] != "stick":
            continue
        if current and current.lower() not in row["key"] and current.lower() not in row["name"].lower():
            continue
        if prepare_action:
            name = f"{row['name']} x{row['quantity']} · inventory (prepare)"[:100]
        else:
            name = f"{row['name']} x{row['quantity']} ({row['key']})"[:100]
        choices.append(
            app_commands.Choice(
                name=name,
                value=row["key"],
            )
        )
    return choices[:25]


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
        proficient="Add +2 if proficient (roll)",
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
        proficient: bool | None = None,
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
                interaction, skill, attribute, dc, proficient, use_safe_roll, use_role_reroll
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
        proficient: bool | None = None,
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

        profs = parse_proficiencies(user["skill_proficiencies"])
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
            is_prof = proficient if proficient is not None else skill in profs
            result = resolve_check(
                user,
                attr_keys=attr_keys,
                skill=skill_label,
                dc=dc,
                proficient=is_prof,
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
                    proficient=is_prof,
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

        color = SUCCESS_COLOR if result["success"] else ERROR_COLOR
        body = role_reroll_note + format_roll_result(result)
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
        description="View conditions, rest, treat with herbs, or medic rites.",
    )
    @app_commands.describe(
        action="condition, rest, treat, prepare, herbbag, herbs, sacred, denstore, turnin, ritual, naming, lay_to_rest, or swim",
        rest_type="Short or long rest (rest)",
        use_herb="Use comfrey for short rest healing (rest)",
        herb="Forage stack (`stack:ID`) or inventory key (`herb_arnica`)",
        herb_filter="Habitat filter for herb guide (herbs)",
        prep_method="dry, poultice, tonic, or decoction (prepare)",
        patient="Packmate to treat from your herb bag (treat; Medics)",
        mode="denstore: list, deposit, or withdraw",
        store_stack="Forage stack ID to deposit, withdraw, or turn in poison herbs (denstore / turnin)",
        ritual_herb="douglas_sagewort, lavender, or mountain_ash (ritual)",
        deceased="Dead wolf to prepare (lay_to_rest)",
        lay_herb="rosemary, lavender, or mint (lay_to_rest)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="View conditions", value="condition"),
            app_commands.Choice(name="Rest", value="rest"),
            app_commands.Choice(name="Treat with herb", value="treat"),
            app_commands.Choice(name="Prepare herb", value="prepare"),
            app_commands.Choice(name="Forage herb bag", value="herbbag"),
            app_commands.Choice(name="Herb guide", value="herbs"),
            app_commands.Choice(name="Sacred visit (Medic)", value="sacred"),
            app_commands.Choice(name="Den herb store", value="denstore"),
            app_commands.Choice(name="Turn in poison herbs", value="turnin"),
            app_commands.Choice(name="Spirit ritual", value="ritual"),
            app_commands.Choice(name="Pup naming rite", value="naming"),
            app_commands.Choice(name="Lay wolf to rest", value="lay_to_rest"),
            app_commands.Choice(name="Swim therapy (river)", value="swim"),
        ],
        rest_type=[
            app_commands.Choice(name="Long rest (6-8 hours sleep)", value="long"),
            app_commands.Choice(name="Short rest (10-30 min)", value="short"),
        ],
        herb_filter=[
            app_commands.Choice(name="All herbs", value="all"),
            app_commands.Choice(name="Territory (wild)", value="wild"),
            app_commands.Choice(name="Thunderpath verge", value="roadside"),
            app_commands.Choice(name="Twoleg compound edge", value="compound"),
        ],
        prep_method=[
            app_commands.Choice(name="Dry for storage", value="dry"),
            app_commands.Choice(name="Poultice (chewed leaves)", value="poultice"),
            app_commands.Choice(name="Tonic (crushed + water)", value="tonic"),
            app_commands.Choice(name="Decoction (boiled / hot spring)", value="decoction"),
        ],
        mode=[
            app_commands.Choice(name="List store", value="list"),
            app_commands.Choice(name="Deposit herb", value="deposit"),
            app_commands.Choice(name="Withdraw herb", value="withdraw"),
        ],
    )
    @app_commands.autocomplete(herb=_herb_inventory_autocomplete)
    async def vitals(
        self,
        interaction: discord.Interaction,
        action: str,
        rest_type: str = "long",
        use_herb: bool = False,
        herb: str | None = None,
        herb_filter: str = "all",
        prep_method: str = "dry",
        patient: discord.Member | None = None,
        mode: str = "list",
        store_stack: str | None = None,
        ritual_herb: str | None = None,
        deceased: discord.Member | None = None,
        lay_herb: str | None = None,
    ):
        if action == "condition":
            await self._condition(interaction)
        elif action == "rest":
            await self._rest(interaction, rest_type, use_herb)
        elif action == "treat":
            if not herb:
                await interaction.response.send_message(
                    "Provide an **herb** key or forage **stack:ID** from `/vitals action:herbbag`.",
                    ephemeral=True,
                )
                return
            await self._treat(interaction, herb, patient)
        elif action == "prepare":
            from engine.herb_storage import parse_herb_stack_id

            if not herb:
                await interaction.response.send_message(
                    "Pick a **forage bag** stack or an **inventory** herb from autocomplete.",
                    ephemeral=True,
                )
                return
            if herb.strip().lower().startswith("herb_"):
                await self._prepare_herb_inventory(interaction, herb.strip().lower(), prep_method)
                return
            stack_id = parse_herb_stack_id(herb)
            if stack_id is None:
                await interaction.response.send_message(
                    "Pick from autocomplete, or enter **`stack:ID`** (forage bag) or **`herb_arnica`** (inventory).",
                    ephemeral=True,
                )
                return
            await self._prepare_herb(interaction, stack_id, prep_method)
        elif action == "herbbag":
            await self._herbbag(interaction)
        elif action == "herbs":
            await self._herb_guide(interaction, herb_filter)
        elif action == "sacred":
            await self._sacred_visit(interaction)
        elif action == "denstore":
            await self._denstore(interaction, mode, store_stack, herb)
        elif action == "turnin":
            await self._turnin_restricted(interaction, store_stack)
        elif action == "ritual":
            await self._spirit_ritual(interaction, patient, ritual_herb)
        elif action == "naming":
            await self._naming_ceremony(interaction, patient)
        elif action == "lay_to_rest":
            await self._lay_to_rest(interaction, deceased, lay_herb)
        elif action == "swim":
            await self._swim_therapy(interaction)

    async def _sacred_visit(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return
        world = db.get_world(interaction.guild.id)
        from engine.sacred_visits import record_sacred_visit

        ok, body = record_sacred_visit(user, day=world["day_number"])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Sacred Visit", body, color=color))

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

    async def _herbbag(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        if not interaction.guild:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return
        from engine.herb_storage import list_herb_bag_summary
        from engine.restricted_herbs import herbbag_hoard_warning

        world = db.get_world(interaction.guild.id)
        body = list_herb_bag_summary(user["id"], world["day_number"])
        hoard_warn = herbbag_hoard_warning(user)
        stacks = db.get_herb_stacks(user["id"])
        spoiling = sum(
            1
            for s in stacks
            if s["form"] == "fresh"
            and world["day_number"] - int(s["acquired_day"]) >= 1
        )
        spoil_note = f"\n\n**{spoiling}** stack(s) spoiling; `/vitals action:prepare` method:dry today." if spoiling else ""
        embed = howlbert_embed(
            f"{user['wolf_name']}: Forage Herb Bag",
            body
            + spoil_note
            + hoard_warn
            + "\n\n`/vitals action:prepare`: forage **stack:ID** or **inventory** herb key (`herb_arnica`)"
            + "\nPrepared herbs land in this bag. Fresh forage stacks rot if not **dried** within 1 sunrise.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _prepare_herb(self, interaction: discord.Interaction, stack_id: int, prep_method: str):
        user = db.get_user(interaction.user.id)
        if not user or not interaction.guild:
            await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
            return
        from engine.herb_preparation import prepare_herb_stack

        world = db.get_world(interaction.guild.id)
        ok, msg = prepare_herb_stack(
            user,
            stack_id,
            prep_method,
            day=world["day_number"],
            at_den=bool(user["pack_id"]),
        )
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Herb Preparation", msg, color=color))

    async def _prepare_herb_inventory(
        self, interaction: discord.Interaction, item_key: str, prep_method: str
    ):
        user = db.get_user(interaction.user.id)
        if not user or not interaction.guild:
            await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
            return
        from engine.herb_preparation import prepare_herb_from_inventory

        world = db.get_world(interaction.guild.id)
        ok, msg = prepare_herb_from_inventory(
            user,
            item_key,
            prep_method,
            day=world["day_number"],
            guild_id=interaction.guild.id,
            at_den=bool(user["pack_id"]),
        )
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Herb Preparation", msg, color=color))

    async def _treat(
        self,
        interaction: discord.Interaction,
        herb: str,
        patient: discord.Member | None = None,
    ):
        import json
        import random

        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed("Not Registered", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from engine.herb_storage import parse_herb_stack_id

        stack_id = parse_herb_stack_id(herb)
        if stack_id is not None:
            if treat_limit_reached(user) and not patient:
                embed = howlbert_embed(
                    "Limit Reached",
                    "You can only **/treat** **3 times per sunrise** (Medics unlimited).",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            from engine.herb_treat import treat_from_herb_stack

            world = db.get_world(interaction.guild.id) if interaction.guild else None
            day = world["day_number"] if world else 0
            treat_patient = None
            if patient:
                from engine.role_privileges import is_medic

                if not is_medic(user):
                    await interaction.response.send_message(
                        embed=howlbert_embed(
                            "Medic Only",
                            "Only **Medics** may treat a **patient** from their herb bag.",
                            color=ERROR_COLOR,
                        ),
                        ephemeral=True,
                    )
                    return
                target = db.get_user(patient.id)
                if not target:
                    await interaction.response.send_message(
                        embed=howlbert_embed("Not Registered", "Patient is not on Howlbert.", color=ERROR_COLOR),
                        ephemeral=True,
                    )
                    return
                treat_patient = target
            ok, msg = treat_from_herb_stack(
                user,
                stack_id,
                day=day,
                patient=treat_patient,
                guild_id=interaction.guild.id if interaction.guild else None,
            )
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            embed = howlbert_embed("Treatment", msg, color=color)
            if ok:
                db.update_user(
                    interaction.user.id,
                    wolf_id=user["id"],
                    herb_treats_today=int(
                        user["herb_treats_today"] if "herb_treats_today" in user.keys() else 0
                    )
                    + 1,
                )
                db.increment_quest_progress(interaction.user.id, "treat")
            await interaction.response.send_message(embed=embed)
            return

        item = db.get_item_by_key(herb.strip().lower())
        if not item or (not item["key"].startswith("herb_") and item["key"] != "stick"):
            embed = howlbert_embed(
                "Unknown Herb",
                "Use an herb from `/inventory` (keys like `herb_yarrow` or `stick`).",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        qty = db.get_inventory_quantity(interaction.user.id, item["id"])
        if qty < 1:
            embed = howlbert_embed("Not In Inventory", f"You don't have **{item['name']}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if treat_limit_reached(user):
            embed = howlbert_embed(
                "Limit Reached",
                "You can only **/treat** with herbs **3 times per sunrise**. "
                "**Medics** have no cap; promote to full Medic rank or wait for the next `/rollover`.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from herbs import HERBS
        from engine.conditions import medicine_check, parse_injuries, treat_with_herb, herb_special_effect

        herb_key = "stick" if item["key"] == "stick" else item["key"].replace("herb_", "", 1)
        meta = HERBS.get(herb_key, {"cures": (), "effect": item["description"]})
        special = herb_special_effect(herb_key, user, inventory_qty=qty)
        world = db.get_world(interaction.guild.id) if interaction.guild else None
        treat_day = world["day_number"] if world else int(user["last_rest_day"] or 0)
        if special == "ragweed_need_three":
            embed = howlbert_embed(
                "Not Enough Ragweed",
                "Ragweed needs **3 leaves** in inventory to remove 1 exhaustion.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if special == "honey_needs_depletion":
            embed = howlbert_embed(
                "Not Depleted Enough",
                "Honey only shakes off **starvation exhaustion**; your hunger and thirst "
                "must be low first.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if special == "honey_pup_not_depleted":
            embed = howlbert_embed(
                "Not Depleted Enough",
                "Honey feeds starving pups; hunger or thirst must be low first.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if special == "feed_pup_honey":
            if not db.consume_item(interaction.user.id, item["id"], quantity=1):
                embed = howlbert_embed(
                    "Not In Inventory", f"You don't have enough **{item['name']}**.", color=ERROR_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            world = db.get_world(interaction.guild.id) if interaction.guild else None
            day_number = world["day_number"] if world else None
            from config import HONEY_PUP_HUNGER_BONUS
            from engine.nursing import apply_honey_to_pup

            fields = apply_honey_to_pup(user, day_number=day_number)
            db.update_user(interaction.user.id, wolf_id=user["id"], **fields)
            ex_note = ""
            if "exhaustion" in fields:
                ex_note = f" Exhaustion **→ {fields['exhaustion']}**."
            msg = (
                f"**{item['name']}**: warm sweetness (**+{HONEY_PUP_HUNGER_BONUS}** hunger)."
                f"{ex_note}"
            )
            embed = howlbert_embed("Honey", msg, color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            return

        outcome = treat_with_herb(user, herb_key, meta)

        if special == "reduce_exhaustion" and int(user["exhaustion"]) <= 0:
            embed = howlbert_embed(
                "No Effect",
                f"**{item['name']}**: you aren't carrying exhaustion to shed.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if special == "hunger_shield" and int(
            user["hunger_exhaustion_skip"] if "hunger_exhaustion_skip" in user.keys() else 0
        ):
            embed = howlbert_embed(
                "Already Shielded",
                "Fennel's hunger shield is already active for the next sunrise.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if special == "march_shield" and int(
            user["march_exhaustion_skip"] if "march_exhaustion_skip" in user.keys() else 0
        ):
            embed = howlbert_embed(
                "Already Shielded",
                "Burnet's march ward is already active for the next sunrise.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if outcome == "no_effect" and not special and herb_key not in ("comfrey", "cobwebs"):
            check = medicine_check(user, dc=15)
            from engine.herb_buffs import consume_herb_check_buffs

            consume_fields = consume_herb_check_buffs(user, skill_key="medicine")
            if consume_fields:
                db.update_user(interaction.user.id, wolf_id=user["id"], **consume_fields)
            if not check["success"]:
                embed = howlbert_embed(
                    "Treatment Failed",
                    f"Medicine check: {check['total']} vs DC 15; no effect.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed)
                return

        use_qty = 3 if herb_key == "ragweed" and special == "reduce_exhaustion" else 1
        if not db.consume_item(interaction.user.id, item["id"], quantity=use_qty):
            embed = howlbert_embed("Not In Inventory", f"You don't have enough **{item['name']}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        injuries = parse_injuries(user["active_injuries"])
        msg = ""

        if special == "reduce_exhaustion":
            old_ex = int(user["exhaustion"])
            new_ex = max(0, old_ex - 1)
            db.set_user_conditions(interaction.user.id, exhaustion=new_ex)
            msg = f"**{item['name']}**: exhaustion **{old_ex}** → **{new_ex}**."
        elif special == "hunger_shield":
            db.update_user(interaction.user.id, wolf_id=user["id"], hunger_exhaustion_skip=1)
            msg = (
                f"**{item['name']}**: you won't gain hunger exhaustion on the next sunrise "
                "(thirst still applies)."
            )
        elif special == "march_shield":
            db.update_user(interaction.user.id, wolf_id=user["id"], march_exhaustion_skip=1)
            msg = (
                f"**{item['name']}**: ignore the first **+1 exhaustion** from strain "
                "on the next sunrise."
            )
        elif special == "jaw_meal_shield":
            db.update_user(interaction.user.id, wolf_id=user["id"], jaw_meal_shield=1)
            msg = (
                f"**{item['name']}**: you can eat and drink without pain until the next sunrise."
            )
            if outcome == "cured_injury":
                for inj in meta.get("cures", ()):
                    if inj in injuries:
                        injuries.remove(inj)
                        db.clear_injury_since(user["id"], inj)
                db.set_user_conditions(
                    interaction.user.id,
                    active_injuries=json.dumps(injuries),
                    condition="healthy" if not injuries else user["condition"],
                )
                msg += " Broken jaw treated."
        elif special == "purslane_thirst":
            thirst = db.adjust_thirst(user["id"], 12)
            msg = f"**{item['name']}**: chewed leaves restore thirst **{thirst}** (+12)."
        elif special == "sorrel_restore":
            from config import HUNGER_MAX

            new_hunger = min(HUNGER_MAX, int(user["hunger"]) + 18)
            had_gash = "deep_gash" in injuries
            fields: dict = {"hunger": new_hunger}
            if had_gash:
                injuries.remove("deep_gash")
                db.clear_injury_since(user["id"], "deep_gash")
                fields["active_injuries"] = json.dumps(injuries)
                if not injuries:
                    fields["condition"] = "healthy"
            db.update_user(interaction.user.id, wolf_id=user["id"], **fields)
            msg = f"**{item['name']}**: appetite returns (**hunger {new_hunger}**)."
            if had_gash:
                msg += " Bleeding staunched."
        elif outcome == "cured_disease":
            db.set_user_conditions(interaction.user.id, clear_disease=True, condition="healthy")
            msg = f"**{meta.get('name', item['name'])}** cured your disease."
        elif outcome == "rabies_ease":
            from engine.herb_buffs import grant_disease_save_advantage

            db.update_user(
                interaction.user.id,
                wolf_id=user["id"],
                **grant_disease_save_advantage(user),
            )
            msg = (
                f"**{item['name']}**: herbs slow early rabies; **advantage** on your next disease save "
                "(one sunrise). Rabies is not cured."
            )
        elif outcome == "cured_injury":
            for inj in meta.get("cures", ()):
                if inj in injuries:
                    injuries.remove(inj)
                    db.clear_injury_since(user["id"], inj)
            db.set_user_conditions(
                interaction.user.id,
                active_injuries=json.dumps(injuries),
                condition="healthy" if not injuries else user["condition"],
            )
            msg = f"**{item['name']}** treated your injury."
        elif outcome == "cured_genetic":
            from engine.genetics import genetic_keys_matching_cures, remove_genetic_keys

            matched = genetic_keys_matching_cures(user, meta.get("cures", ()))
            new_genetics = remove_genetic_keys(user, matched)
            db.update_user(interaction.user.id, wolf_id=user["id"], genetic_conditions=new_genetics)
            names = ", ".join(m.replace("_", " ").title() for m in matched)
            msg = f"**{item['name']}** eased or corrected **{names}**."
        elif outcome == "symptom_ease":
            msg = f"**{item['name']}**: {meta.get('effect', 'symptoms ease for now')}."
        elif outcome == "poison_herb":
            msg = (
                f"**{item['name']}**: restricted poison; no safe cure applied. "
                "Medic knowledge only."
            )
        elif outcome == "healed" or herb_key == "comfrey":
            from engine.exhaustion_effects import effective_max_hp

            heal = random.randint(1, 4)
            cap = effective_max_hp(user)
            new_hp = min(cap, user["hp"] + heal)
            db.set_user_conditions(interaction.user.id, hp=new_hp)
            msg = f"Comfrey poultice healed **{heal} HP**."
        elif outcome == "stabilized":
            db.set_user_conditions(interaction.user.id, hp=1, condition="stable")
            msg = (
                f"**{item['name']}** stabilized you at 1 HP."
                if herb_key != "cobwebs"
                else "Cobwebs stabilized you at 1 HP."
            )

        from engine.herb_buffs import apply_supplemental_herb

        supplemental = apply_supplemental_herb(herb_key, user, day=treat_day, outcome=outcome)
        if supplemental:
            kind = supplemental["kind"]
            sfields = supplemental.get("fields") or {}
            if kind == "mercy":
                db.set_user_conditions(interaction.user.id, condition="dead", hp=0)
                msg = f"**{item['name']}**: {supplemental['message']}"
            elif kind == "stabilize" and outcome != "stabilized":
                db.set_user_conditions(interaction.user.id, hp=1, condition="stable")
                msg = f"**{item['name']}**: {supplemental['message']}"
            else:
                if sfields:
                    db.update_user(interaction.user.id, wolf_id=user["id"], **sfields)
                extra = supplemental["message"]
                if not msg:
                    msg = f"**{item['name']}**; {extra}"
                elif kind in ("disease_save_buff", "minor_relief", "heal", "symptom_relief"):
                    msg += f" {extra}"

        if not msg:
            msg = f"Applied **{item['name']}**: {meta.get('effect', 'minor relief')}."

        embed = howlbert_embed("Treatment", msg, color=SUCCESS_COLOR)
        db.update_user(
            interaction.user.id,
            wolf_id=user["id"],
            herb_treats_today=int(
                user["herb_treats_today"] if "herb_treats_today" in user.keys() else 0
            )
            + 1,
        )
        db.increment_quest_progress(interaction.user.id, "treat")
        await interaction.response.send_message(embed=embed)

    async def _herb_guide(self, interaction: discord.Interaction, herb_filter: str = "all"):
        from engine.herb_guide import build_herb_guide_embed
        from utils.herb_views import make_herb_guide_view

        if herb_filter not in ("all", "wild", "roadside", "compound"):
            herb_filter = "all"
        title, body = build_herb_guide_embed(page=0, filter_key=herb_filter)
        embed = howlbert_embed(title, body)
        embed.set_footer(text="Herb guide · /vitals action:herbs")
        view = make_herb_guide_view(page=0, filter_key=herb_filter)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def _denstore(
        self,
        interaction: discord.Interaction,
        mode: str,
        store_stack: str | None,
        herb: str | None,
    ):
        user = db.get_user(interaction.user.id)
        if not user or not interaction.guild:
            await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
            return
        if not user["pack_id"]:
            await interaction.response.send_message(
                embed=howlbert_embed("No Pack", "Join a pack to use the healers' herb store.", color=ERROR_COLOR),
                ephemeral=True,
            )
            return
        from engine.pack_herb_store import (
            can_manage_den_herbs,
            deposit_herb_to_store,
            list_pack_herb_store,
            withdraw_herb_from_store,
        )

        world = db.get_world(interaction.guild.id)
        if mode == "list":
            body = list_pack_herb_store(user["pack_id"], world["day_number"])
            embed = howlbert_embed(f"Healers' Herb Store", body)
            embed.set_footer(text="Medics & Foragers: deposit/withdraw via `/vitals action:denstore`")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if not can_manage_den_herbs(user):
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Medic / Forager Only",
                    "Only **Medics** and **Foragers** manage the den herb store.",
                    color=ERROR_COLOR,
                ),
                ephemeral=True,
            )
            return
        if mode == "deposit":
            from engine.herb_storage import parse_herb_stack_id

            raw = store_stack or herb
            stack_id = parse_herb_stack_id(raw)
            if stack_id is None:
                await interaction.response.send_message(
                    "Pick a forage **stack:ID** from autocomplete to deposit.", ephemeral=True
                )
                return
            ok, msg = deposit_herb_to_store(
                user,
                stack_id,
                pack_id=user["pack_id"],
                guild_id=interaction.guild.id,
                day=world["day_number"],
            )
        elif mode == "withdraw":
            try:
                sid = int((store_stack or herb or "").strip().lstrip("#"))
            except (ValueError, TypeError):
                await interaction.response.send_message(
                    "Enter store stack **`#ID`** from `/vitals action:denstore mode:list`.",
                    ephemeral=True,
                )
                return
            ok, msg = withdraw_herb_from_store(
                user,
                sid,
                pack_id=user["pack_id"],
                guild_id=interaction.guild.id,
                day=world["day_number"],
            )
        else:
            await interaction.response.send_message("Pick **list**, **deposit**, or **withdraw**.", ephemeral=True)
            return
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Den Herb Store", msg, color=color))

    async def _turnin_restricted(self, interaction: discord.Interaction, store_stack: str | None):
        user = db.get_user(interaction.user.id)
        if not user or not interaction.guild:
            await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
            return
        if not user["pack_id"]:
            await interaction.response.send_message(
                embed=howlbert_embed("No Pack", "Join a pack to turn poison herbs in.", color=ERROR_COLOR),
                ephemeral=True,
            )
            return
        from engine.herb_storage import parse_herb_stack_id
        from engine.pack_herb_store import turnin_restricted_herb

        sid = parse_herb_stack_id(store_stack)
        if not sid:
            await interaction.response.send_message(
                "Enter your forage **`stack:ID`** for the restricted herb to turn in.",
                ephemeral=True,
            )
            return
        world = db.get_world(interaction.guild.id)
        ok, msg = turnin_restricted_herb(
            user,
            sid,
            pack_id=int(user["pack_id"]),
            guild_id=interaction.guild.id,
            day=world["day_number"],
        )
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Poison Herb Turn-In", msg, color=color))

    async def _spirit_ritual(
        self,
        interaction: discord.Interaction,
        patient: discord.Member | None,
        ritual_herb: str | None,
    ):
        medic = db.get_user(interaction.user.id)
        if not medic or not interaction.guild:
            await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
            return
        if not patient:
            await interaction.response.send_message("Pick a **patient** for the cleansing ritual.", ephemeral=True)
            return
        if not ritual_herb:
            await interaction.response.send_message(
                "Pick **douglas_sagewort**, **lavender**, or **mountain_ash** (rowan).", ephemeral=True
            )
            return
        target = db.get_user(patient.id)
        if not target:
            await interaction.response.send_message("Patient is not on Howlbert.", ephemeral=True)
            return
        world = db.get_world(interaction.guild.id)
        from engine.medical_care import run_spirit_ritual

        ok, body = run_spirit_ritual(medic, target, ritual_herb, day=world["day_number"])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Spirit Ritual", body, color=color))
        if ok:
            db.increment_quest_progress(interaction.user.id, "treat")

    async def _naming_ceremony(
        self,
        interaction: discord.Interaction,
        patient: discord.Member | None,
    ):
        medic = db.get_user(interaction.user.id)
        if not medic or not interaction.guild:
            await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
            return
        if not patient:
            await interaction.response.send_message("Pick the **pup** (`patient`) for the naming rite.", ephemeral=True)
            return
        pup = db.get_user(patient.id)
        if not pup:
            await interaction.response.send_message("That wolf is not on Howlbert.", ephemeral=True)
            return
        world = db.get_world(interaction.guild.id)
        from engine.medical_care import run_naming_ceremony

        ok, body = run_naming_ceremony(medic, pup, day=world["day_number"])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Naming Ceremony", body, color=color))

    async def _lay_to_rest(
        self,
        interaction: discord.Interaction,
        deceased: discord.Member | None,
        lay_herb: str | None,
    ):
        medic = db.get_user(interaction.user.id)
        if not medic:
            await interaction.response.send_message("Use `/register` first.", ephemeral=True)
            return
        if not deceased or not lay_herb:
            await interaction.response.send_message(
                "Pick **deceased** and **lay_herb** (rosemary, lavender, mint).", ephemeral=True
            )
            return
        target = db.get_user(deceased.id)
        if not target:
            await interaction.response.send_message("That wolf is not on Howlbert.", ephemeral=True)
            return
        from engine.medical_care import run_lay_to_rest

        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day = world["day_number"] if world else 0
        ok, body = run_lay_to_rest(medic, target, lay_herb, day=day)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Lay to Rest", body, color=color))

    async def _swim_therapy(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user or not interaction.guild:
            await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
            return
        world = db.get_world(interaction.guild.id)
        from engine.medical_care import run_swim_therapy

        ok, body = run_swim_therapy(user, day=world["day_number"], season=world["season"])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Swim Therapy", body, color=color))

    @app_commands.command(
        name="quarantine",
        description="Isolate sick packmates in the sick den (Medics, Alpha, Advisor).",
    )
    @app_commands.describe(
        wolf="Packmate to isolate or release",
        own_wolf="One of your other wolves (same pack)",
        release="Release from quarantine instead of isolating",
    )
    @app_commands.autocomplete(own_wolf=_quarantine_own_wolf_autocomplete)
    async def quarantine(
        self,
        interaction: discord.Interaction,
        wolf: discord.Member | None = None,
        own_wolf: str | None = None,
        release: bool = False,
    ):
        from engine.diseases import disease_display
        from engine.quarantine import can_manage_quarantine, is_quarantined

        actor = db.get_user(interaction.user.id)
        if not actor:
            embed = howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if wolf and own_wolf:
            embed = howlbert_embed(
                "Pick One Target",
                "Choose another **player** or `own_wolf`; not both.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        pack = db.get_pack(actor["pack_id"]) if actor["pack_id"] else None

        if not wolf and not own_wolf:
            if is_quarantined(actor):
                embed = howlbert_embed(
                    "Quarantined",
                    f"**{actor['wolf_name']}** is isolated in the sick den.",
                    color=SUCCESS_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if pack and can_manage_quarantine(actor, pack):
                rows = db.list_pack_quarantined(pack["id"])
                if not rows:
                    embed = howlbert_embed(
                        "Sick Den",
                        "No wolves are quarantined in your pack.",
                        color=SUCCESS_COLOR,
                    )
                else:
                    lines = [f"**{r['wolf_name']}**" for r in rows]
                    embed = howlbert_embed(
                        "Sick Den: Quarantined",
                        "\n".join(lines),
                        color=SUCCESS_COLOR,
                    )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            embed = howlbert_embed(
                "Quarantine",
                "Pick a **wolf** to isolate, or use `release:true` to free someone.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if own_wolf:
            rows = db.list_user_wolves(interaction.user.id)
            target = next(
                (w for w in rows if w["wolf_name"].lower() == own_wolf.strip().lower()),
                None,
            )
            if not target:
                embed = howlbert_embed("Unknown Wolf", f"No wolf named **{own_wolf}**.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        else:
            target = db.get_user(wolf.id)
            if not target:
                embed = howlbert_embed("Not Registered", "That wolf isn't registered.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        if not pack:
            embed = howlbert_embed("No Pack", "Quarantine is a pack sick-den measure.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if target["pack_id"] != pack["id"]:
            embed = howlbert_embed(
                "Wrong Pack",
                "**{0}** isn't in your pack.".format(target["wolf_name"]),
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not can_manage_quarantine(actor, pack):
            embed = howlbert_embed(
                "Not Authorized",
                "Only **Medics**, **Alphas**, and **Advisors** can manage quarantine.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if release:
            if not is_quarantined(target):
                embed = howlbert_embed(
                    "Not Quarantined",
                    f"**{target['wolf_name']}** isn't in isolation.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            db.set_quarantined(target["discord_id"], False, wolf_id=target["id"])
            embed = howlbert_embed(
                "Released",
                f"**{target['wolf_name']}** may leave the sick den.",
                color=SUCCESS_COLOR,
            )
            await interaction.response.send_message(embed=embed)
            return

        if is_quarantined(target):
            embed = howlbert_embed(
                "Already Quarantined",
                f"**{target['wolf_name']}** is already isolated.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        db.set_quarantined(target["discord_id"], True, wolf_id=target["id"])
        illness = disease_display(target)
        extra = ""
        if illness:
            extra = f"\n\nIllness: **{illness[0]}**: {illness[1]}"
        embed = howlbert_embed(
            "Quarantined",
            f"**{target['wolf_name']}** is isolated in the sick den. "
            f"They cannot spread illness or join pack activities until released.{extra}",
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Rpg(bot))
