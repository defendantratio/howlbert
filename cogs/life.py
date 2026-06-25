import json

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from engine.maw_belief import MAW_BELIEF_OPTIONS
from engine.death_saves import roll_death_save, stabilize_check
from engine.attraction import (
    BIRTH_SEX_LABELS,
    BOND_FIRST_SEXUALITIES,
    SEXUALITY_LABELS,
    SEXUALITY_OPTIONS,
    are_bonded_mates,
    court_attraction_allowed,
    get_sexuality,
)
from engine.family import (
    GESTATION_DAYS,
    XP_PER_ATTRIBUTE,
    XP_PER_ROLE_FEATURE,
    XP_PER_SKILL,
    birth_check,
    courtship_check,
    generate_pup_stats,
    spend_xp_attribute,
    spend_xp_trait_bonus,
)
from engine.aging import stage_for_age, stage_label
from engine.youth_lineage import (
    adoption_eligibility_error,
    parse_litter_names,
    random_birth_sex,
)
from engine.courtship import apply_court_outcome, resolve_court_difficulty, run_court_check
from engine.adoption_consent import accept_pending_adoption, decline_pending_adoption
from engine.mating import execute_mating, mating_embed_title
from config import JUVENILE_MAX_MOONS
from utils.adoption_views import AdoptionConsentView
from utils.mate_views import MateConsentView
from rpg_rules import ROLE_FEATURES, ROLE_LABELS, SKILLS, MAX_SKILL_RANK, XP_PER_TRAIT
from engine.role_restrictions import young_wolf_block
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from utils.notifications import notify_consent_request
from utils.herb_autocomplete import herb_inventory_autocomplete
from cogs.care_handlers import (
    lay_to_rest,
    naming_ceremony,
    quarantine_command,
    sacred_visit,
    spirit_ritual,
    treat,
)


def _resolve_own_wolf(discord_id: int, name: str):
    rows = db.list_user_wolves(discord_id)
    return next((w for w in rows if w["wolf_name"].lower() == name.strip().lower()), None)


def _resolve_partner_wolf(
    user,
    interaction: discord.Interaction,
    *,
    partner: discord.Member | None,
    own_wolf: str | None,
) -> tuple[object | None, str | None]:
    if partner and own_wolf:
        return None, "Pick either another **player** or one of your other wolves (`own_wolf`), not both."
    if own_wolf:
        target = _resolve_own_wolf(interaction.user.id, own_wolf)
        if not target:
            return None, "No wolf with that name on your account. Check `/wolves`."
        if target["id"] == user["id"]:
            return None, "Pick a different wolf than your active one."
        return target, None
    if partner:
        if partner.id == interaction.user.id:
            return None, "Use `own_wolf` to court or mate another character you own."
        target = db.get_user(partner.id)
        if not target:
            return None, "__not_registered__"
        return target, None
    return None, "Specify another player or your wolf name in `own_wolf`."


def _resolve_adoptee(
    user,
    interaction: discord.Interaction,
    *,
    youth: discord.Member | None,
    own_youth: str | None,
) -> tuple[object | None, str | None]:
    if youth and own_youth:
        return None, "Pick either another **player** (`youth`) or one of your young wolves (`own_youth`), not both."
    if own_youth:
        target = _resolve_own_wolf(interaction.user.id, own_youth)
        if not target:
            return None, "No wolf with that name on your account. Check `/wolves`."
        if target["id"] == user["id"]:
            return None, "Pick a different wolf than your active one."
        return target, None
    if youth:
        if youth.id == interaction.user.id:
            return None, "Use `own_youth` for one of your other pups or juveniles."
        target = db.get_user(youth.id)
        if not target:
            return None, "__not_registered__"
        return target, None
    return None, "Specify who to adopt with `youth` or `own_youth`."


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


class Life(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _require_user(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        return user

    @app_commands.command(
        name="medic",
        description="Clinical care, herb treatment, spirit rites, and sick-den quarantine.",
    )
    @app_commands.describe(
        action="deathsaves, stabilize, surgery, treat, checkup, sacred, ritual, naming, lay_to_rest, swim, quarantine, or observe",
        patient="Packmate (stabilize, surgery, treat, ritual, naming, observe)",
        helper="Assisting Medic for surgery (Medicine DC 10 → advantage)",
        procedure="Surgery type (surgery only)",
        herb="Herb key or forage stack (treat)",
        ritual_herb="douglas_sagewort, lavender, or mountain_ash (ritual)",
        deceased="Dead wolf to prepare (lay_to_rest)",
        lay_herb="rosemary, lavender, or mint (lay_to_rest)",
        wolf="Packmate to isolate or release (quarantine)",
        own_wolf="Your other wolf in the same pack (quarantine)",
        release="Release from quarantine instead of isolating",
        use_yarrow="Apply yarrow for +2 (stabilize)",
        use_cobwebs="Cobwebs auto-stabilize (stabilize)",
        use_poppy="Poppy seeds sedation +2 (amputation surgery)",
        use_meadowsweet="Meadowsweet pain ease +1 (stitch / set bone / amputate)",
        use_loosestrife="Purple loosestrife +1 (stitch only)",
        use_plantain="Plantain soothe +1 (extract only)",
        use_rush_stalks="Rush stalks lash splint +2 (set bone only)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Death save (dying wolf)", value="deathsaves"),
            app_commands.Choice(name="Stabilize packmate", value="stabilize"),
            app_commands.Choice(name="Surgery on patient", value="surgery"),
            app_commands.Choice(name="Treat with herb", value="treat"),
            app_commands.Choice(name="Den checkup", value="checkup"),
            app_commands.Choice(name="Sacred visit (Medic)", value="sacred"),
            app_commands.Choice(name="Spirit ritual", value="ritual"),
            app_commands.Choice(name="Pup naming rite", value="naming"),
            app_commands.Choice(name="Lay wolf to rest", value="lay_to_rest"),
            app_commands.Choice(name="Swim therapy (river)", value="swim"),
            app_commands.Choice(name="Quarantine sick wolf", value="quarantine"),
            app_commands.Choice(name="Observe case (apprentice)", value="observe"),
        ],
        procedure=[
            app_commands.Choice(name="Stitch wound (deep gash / infection)", value="stitch"),
            app_commands.Choice(name="Set bone / splint (comfrey + bindweed + 2 sticks)", value="set_bone"),
            app_commands.Choice(name="Extract thorn or splinter", value="extract"),
            app_commands.Choice(name="Amputate ruined limb", value="amputate"),
        ],
    )
    @app_commands.autocomplete(herb=herb_inventory_autocomplete, own_wolf=_quarantine_own_wolf_autocomplete)
    async def medic(
        self,
        interaction: discord.Interaction,
        action: str,
        patient: discord.Member | None = None,
        helper: discord.Member | None = None,
        procedure: str = "stitch",
        herb: str | None = None,
        ritual_herb: str | None = None,
        deceased: discord.Member | None = None,
        lay_herb: str | None = None,
        wolf: discord.Member | None = None,
        own_wolf: str | None = None,
        release: bool = False,
        use_yarrow: bool = False,
        use_cobwebs: bool = False,
        use_poppy: bool = False,
        use_meadowsweet: bool = False,
        use_loosestrife: bool = False,
        use_plantain: bool = False,
        use_rush_stalks: bool = False,
    ):
        if action == "deathsaves":
            await self._deathsaves(interaction)
        elif action == "stabilize":
            if not patient:
                embed = howlbert_embed(
                    "Pick a Patient",
                    "Stabilize requires a **patient** packmate.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            await self._stabilize(interaction, patient, use_yarrow, use_cobwebs)
        elif action == "surgery":
            if not patient:
                embed = howlbert_embed(
                    "Pick a Patient",
                    "Surgery requires a **patient** wolf.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            await self._surgery(
                interaction,
                patient,
                helper,
                procedure,
                use_poppy,
                use_meadowsweet,
                use_loosestrife,
                use_plantain,
                use_rush_stalks,
            )
        elif action == "treat":
            if not herb:
                await interaction.response.send_message(
                    "Provide an **herb** key or forage **stack:ID** from `/herbs action:bag`.",
                    ephemeral=True,
                )
                return
            await treat(interaction, herb, patient)
        elif action == "observe":
            if not patient:
                await interaction.response.send_message(
                    embed=howlbert_embed("Pick a Patient", "Observe requires a **patient**.", color=ERROR_COLOR),
                    ephemeral=True,
                )
                return
            await self._observe(interaction, patient)
        elif action in ("rounds", "checkup"):
            await self._medic_rounds(interaction)
        elif action == "sacred":
            await sacred_visit(interaction)
        elif action == "ritual":
            await spirit_ritual(interaction, patient, ritual_herb)
        elif action == "naming":
            await naming_ceremony(interaction, patient)
        elif action == "lay_to_rest":
            await lay_to_rest(interaction, deceased, lay_herb)
        elif action == "swim":
            await self._swim_therapy(interaction)
        elif action == "quarantine":
            await quarantine_command(interaction, wolf, own_wolf, release)

    async def _surgery(
        self,
        interaction: discord.Interaction,
        patient: discord.Member,
        helper: discord.Member | None,
        procedure: str,
        use_poppy: bool,
        use_meadowsweet: bool,
        use_loosestrife: bool,
        use_plantain: bool,
        use_rush_stalks: bool,
    ):
        surgeon = await self._require_user(interaction)
        if not surgeon:
            return
        if not interaction.guild:
            await interaction.response.send_message("Use in a server.", ephemeral=True)
            return

        target = db.get_user(patient.id)
        if not target:
            embed = howlbert_embed("Not Registered", "Patient is not on Howlbert.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        helper_row = None
        if helper:
            helper_row = db.get_user(helper.id)
            if not helper_row:
                embed = howlbert_embed("Not Registered", "Helper is not on Howlbert.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        world = db.get_world(interaction.guild.id)
        from engine.surgery import run_surgery

        ok, body = run_surgery(
            surgeon,
            target,
            procedure,
            day=world["day_number"],
            use_poppy=use_poppy,
            use_meadowsweet=use_meadowsweet,
            use_loosestrife=use_loosestrife,
            use_plantain=use_plantain,
            use_rush_stalks=use_rush_stalks,
            helper=helper_row,
            guild_id=interaction.guild.id if interaction.guild else None,
        )
        embed = howlbert_embed(
            "Surgery" if ok else "Surgery Failed",
            body,
            color=SUCCESS_COLOR if ok else ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed)
        if ok:
            gid = interaction.guild.id if interaction.guild else None
            db.increment_quest_progress(interaction.user.id, "treat", guild_id=gid)

    async def _observe(self, interaction: discord.Interaction, patient: discord.Member):
        medic = await self._require_user(interaction)
        if not medic:
            return
        if not interaction.guild:
            await interaction.response.send_message("Use in a server.", ephemeral=True)
            return
        target = db.get_user(patient.id)
        if not target:
            await interaction.response.send_message("Patient is not on Howlbert.", ephemeral=True)
            return
        world = db.get_world(interaction.guild.id)
        from engine.medical_care import run_observe_apprentice

        ok, body = run_observe_apprentice(
            medic,
            target,
            day=world["day_number"],
            guild_id=interaction.guild.id if interaction.guild else None,
        )
        if ok:
            from engine.plot_blinking import try_plot_observe_extras

            body += try_plot_observe_extras(medic, guild_id=interaction.guild.id, day=world["day_number"])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Observe", body, color=color))
        if ok:
            gid = interaction.guild.id if interaction.guild else None
            db.increment_quest_progress(interaction.user.id, "treat", guild_id=gid)

    async def _medic_rounds(self, interaction: discord.Interaction):
        medic = await self._require_user(interaction)
        if not medic:
            return
        if not interaction.guild:
            await interaction.response.send_message("Use in a server.", ephemeral=True)
            return
        if not medic["pack_id"]:
            await interaction.response.send_message(
                embed=howlbert_embed("No Pack", "Join a pack to walk den checkups.", color=ERROR_COLOR),
                ephemeral=True,
            )
            return
        world = db.get_world(interaction.guild.id)
        from engine.medical_care import run_medic_rounds

        ok, body = run_medic_rounds(medic, day=world["day_number"])
        if not ok:
            await interaction.response.send_message(
                embed=howlbert_embed("Den Checkup", body, color=ERROR_COLOR),
                ephemeral=True,
            )
            return
        from engine.healer_refusal import healer_refusal_reminder

        rem = healer_refusal_reminder(medic, pack_id=medic["pack_id"])
        if rem:
            body += f"\n\n{rem}"
        await interaction.response.send_message(embed=howlbert_embed("Den Checkup", body))

    async def _swim_therapy(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user or not interaction.guild:
            await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
            return
        world = db.get_world(interaction.guild.id)
        from engine.medical_care import run_swim_therapy

        ok, body = run_swim_therapy(user, day=world["day_number"], season=world["season"])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Swim Therapy", body, color=color))

    async def _deathsaves(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return

        if user["hp"] > 0 and user["condition"] != "dying":
            embed = howlbert_embed(
                "Not Dying",
                "Death saves are only for wolves who are **dying** (0 HP; from combat, starvation, or thirst).",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if user["condition"] == "dead":
            embed = howlbert_embed("Dead", "This wolf has already passed.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if user["death_save_round"] == 0:
            db.enter_dying_state(interaction.user.id)
            user = db.get_user(interaction.user.id)

        result = roll_death_save(user)
        if result.get("consume_fields"):
            db.update_user(interaction.user.id, wolf_id=user["id"], **result["consume_fields"])
        outcome = db.apply_death_save_result(
            interaction.user.id, result["success"], result.get("nat20", False)
        )

        body = (
            f"Round **{result['round']}**: 1d20 ({result['die']}) + {result['modifier']} "
            f"= **{result['total']}** vs DC **{result['dc']}**"
        )
        if outcome == "stabilized":
            body += "\n\n**Stabilized at 1 HP.** Depleted hunger/thirst restored to a survivable level."
            color = SUCCESS_COLOR
        elif outcome == "died":
            body += (
                "\n\n**The wolf dies.** `/bones action:use item:revive` or `/bones action:use item:reincarnation new_name:<name>` "
                "if you have one (Ko-fi shop), or `/rpg action:delete confirm:DELETE` / `/register` for a fresh wolf."
            )
            color = ERROR_COLOR
        else:
            body += f"\n\nSurvived round {result['round']}. **Round {result['round'] + 1}** next."
            color = SUCCESS_COLOR

        await interaction.response.send_message(embed=howlbert_embed("Death Save", body, color=color))

    async def _stabilize(
        self,
        interaction: discord.Interaction,
        patient: discord.Member,
        use_yarrow: bool = False,
        use_cobwebs: bool = False,
    ):
        healer = await self._require_user(interaction)
        if not healer:
            return

        target = db.get_user(patient.id)
        if not target or (target["hp"] > 0 and target["condition"] != "dying"):
            embed = howlbert_embed("Not Dying", f"{patient.display_name} is not at 0 HP.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if interaction.guild:
            from engine.medical_access import can_medic_treat_cross_pack

            ok_cross, cross_msg = can_medic_treat_cross_pack(
                healer, target, interaction.guild.id, emergency_stabilize=True
            )
            if not ok_cross:
                embed = howlbert_embed("Can't Stabilize", cross_msg, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        if use_cobwebs:
            item = db.get_item_by_key("herb_cobwebs")
            if not item or db.get_inventory_quantity(interaction.user.id, item["id"]) < 1:
                embed = howlbert_embed("No Cobwebs", "You need **cobwebs** in inventory.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            db.consume_item(interaction.user.id, item["id"])
            db.stabilize_patient(patient.id)
            embed = howlbert_embed(
                "Stabilized",
                f"Cobwebs hold; **{target['wolf_name']}** stabilizes at 1 HP.",
                color=SUCCESS_COLOR,
            )
            await interaction.response.send_message(embed=embed)
            gid = interaction.guild.id if interaction.guild else None
            db.increment_quest_progress(interaction.user.id, "treat", guild_id=gid)
            return

        if use_yarrow:
            item = db.get_item_by_key("herb_yarrow")
            if not item or db.get_inventory_quantity(interaction.user.id, item["id"]) < 1:
                embed = howlbert_embed("No Yarrow", "You need **yarrow** in inventory.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            db.consume_item(interaction.user.id, item["id"])

        check = stabilize_check(healer, yarrow=use_yarrow, patient=target)
        if check.get("consume_fields"):
            db.update_user(patient.id, wolf_id=target["id"], **check["consume_fields"])
        if check["success"]:
            db.stabilize_patient(patient.id)
            gid = interaction.guild.id if interaction.guild else None
            db.increment_quest_progress(interaction.user.id, "treat", guild_id=gid)
            embed = howlbert_embed(
                "Stabilized",
                f"Medicine: **{check['total']}** vs DC 15; **{target['wolf_name']}** at 1 HP.",
                color=SUCCESS_COLOR,
            )
        else:
            embed = howlbert_embed(
                "Failed",
                f"Medicine: **{check['total']}** vs DC 15; no effect.",
                color=ERROR_COLOR,
            )
        from engine.healer_refusal import healer_refusal_reminder

        rem = healer_refusal_reminder(healer, pack_id=healer["pack_id"] if healer["pack_id"] else None)
        if rem and embed.description:
            embed.description += f"\n\n{rem}"
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="advance",
        description="View XP or spend it on attributes, skills, or role features.",
    )
    @app_commands.describe(
        action="view or spend",
        purchase="What to buy (spend only)",
        attribute="Attribute to raise (spend)",
        skill="Skill to raise (spend)",
        role_feature="Role whose feature to gain (spend)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="View XP", value="view"),
            app_commands.Choice(name="Spend XP", value="spend"),
        ],
        purchase=[
            app_commands.Choice(name=f"+1 Attribute ({XP_PER_ATTRIBUTE} XP)", value="attribute"),
            app_commands.Choice(name=f"+1 Skill trait ({XP_PER_TRAIT} XP)", value="trait"),
            app_commands.Choice(name=f"Role feature ({XP_PER_ROLE_FEATURE} XP)", value="role_feature"),
        ],
        attribute=[
            app_commands.Choice(name="Strength", value="str"),
            app_commands.Choice(name="Dexterity", value="dex"),
            app_commands.Choice(name="Constitution", value="con"),
            app_commands.Choice(name="Intelligence", value="int"),
            app_commands.Choice(name="Charisma", value="cha"),
            app_commands.Choice(name="Wisdom", value="wis"),
        ],
        skill=[app_commands.Choice(name=label, value=key) for key, (_, label) in SKILLS.items()],
        role_feature=[
            app_commands.Choice(name=ROLE_LABELS[k], value=k) for k in ROLE_FEATURES
        ],
    )
    async def advance(
        self,
        interaction: discord.Interaction,
        action: str = "view",
        purchase: str | None = None,
        attribute: str | None = None,
        skill: str | None = None,
        role_feature: str | None = None,
    ):
        if action == "view":
            await self._xp(interaction)
        elif action == "spend":
            if not purchase:
                await interaction.response.send_message("Pick a **purchase** type.", ephemeral=True)
                return
            await self._spendxp(interaction, purchase, attribute, skill, role_feature)

    async def _xp(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return
        account = db.get_account(interaction.user.id)
        xp_val = account["xp"] if "xp" in account.keys() else 0
        embed = howlbert_embed("Experience", color=SUCCESS_COLOR)
        embed.description = (
            f"You have **{xp_val} XP**.\n\n"
            f"**{XP_PER_ATTRIBUTE} XP**: +1 attribute (max 10)\n"
            f"**{XP_PER_TRAIT} XP**: +1 **earned trait** on a skill (max +{MAX_SKILL_RANK} from play; stacks with lore)\n"
            f"**{XP_PER_ROLE_FEATURE} XP**; gain another role's feature (**requires admin approval**)"
        )
        embed.set_footer(text="Earn XP from quests, daily ration, den chat, and RP milestones. Quests may grant skill trait experience.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _spendxp(
        self,
        interaction: discord.Interaction,
        purchase: str,
        attribute: str | None = None,
        skill: str | None = None,
        role_feature: str | None = None,
    ):
        user = await self._require_user(interaction)
        if not user:
            return

        if purchase == "attribute":
            if not attribute:
                await interaction.response.send_message("Pick an attribute.", ephemeral=True)
                return
            err = spend_xp_attribute(user, attribute)
            if err:
                embed = howlbert_embed("Cannot Spend", err, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if not db.spend_xp(interaction.user.id, XP_PER_ATTRIBUTE):
                embed = howlbert_embed("Not Enough XP", f"Need {XP_PER_ATTRIBUTE} XP.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            key = f"attr_{attribute}"
            db.update_user(interaction.user.id, **{key: user[key] + 1})
            embed = howlbert_embed("Attribute Raised", f"**{attribute.upper()}** is now **{user[key] + 1}**.", color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            return

        if purchase == "trait":
            if not skill:
                await interaction.response.send_message("Pick a skill.", ephemeral=True)
                return
            err = spend_xp_trait_bonus(user, skill)
            if err:
                embed = howlbert_embed("Cannot Spend", err, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if not db.spend_xp(interaction.user.id, XP_PER_TRAIT):
                embed = howlbert_embed("Not Enough XP", f"Need {XP_PER_TRAIT} XP.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            from engine.character_traits import adjust_skill_trait_experience

            ok, msg = adjust_skill_trait_experience(user["id"], skill, 1)
            if not ok:
                embed = howlbert_embed("Cannot Spend", msg, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            embed = howlbert_embed("Trait Raised", msg, color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            return

        if purchase == "role_feature":
            if not role_feature or role_feature not in ROLE_FEATURES:
                await interaction.response.send_message("Pick a role feature.", ephemeral=True)
                return
            existing_bonus = (
                user["bonus_role_feature"]
                if "bonus_role_feature" in user.keys() and user["bonus_role_feature"]
                else None
            )
            if existing_bonus == role_feature:
                embed = howlbert_embed(
                    "Already Have Feature",
                    f"**{user['wolf_name']}** already has the **{ROLE_LABELS[role_feature]}** bonus feature.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if db.get_open_pending_for_wolf(user["id"]):
                embed = howlbert_embed(
                    "Request Pending",
                    "A role-feature request is already awaiting admin approval for this wolf.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            account = db.get_account(interaction.user.id)
            xp_val = account["xp"] if "xp" in account.keys() else 0
            if xp_val < XP_PER_ROLE_FEATURE:
                embed = howlbert_embed("Not Enough XP", f"Need {XP_PER_ROLE_FEATURE} XP.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            guild_id = interaction.guild.id if interaction.guild else 0
            db.create_pending_role_feature(
                guild_id=guild_id,
                discord_id=interaction.user.id,
                wolf_id=user["id"],
                wolf_name=user["wolf_name"],
                role_feature=role_feature,
            )
            embed = howlbert_embed(
                "Request Submitted",
                "Request submitted; an **admin** must approve before XP is spent.",
                color=SUCCESS_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="wolfset",
        description="Update birth sex, sexuality, Maw belief, or combat size.",
    )
    @app_commands.describe(
        field="What to update",
        birth_sex="Birth sex (field: birth_sex)",
        sexuality="Attraction (field: sexuality)",
        maw_belief="Faith in the Maw (field: maw_belief)",
        size="Combat build size (field: size)",
    )
    @app_commands.choices(
        field=[
            app_commands.Choice(name="Birth sex", value="birth_sex"),
            app_commands.Choice(name="Sexuality", value="sexuality"),
            app_commands.Choice(name="Maw belief", value="maw_belief"),
            app_commands.Choice(name="Combat size", value="size"),
        ],
        birth_sex=[
            app_commands.Choice(name="Female", value="female"),
            app_commands.Choice(name="Male", value="male"),
            app_commands.Choice(name="Intersex", value="intersex"),
            app_commands.Choice(name="Nonbinary", value="nonbinary"),
        ],
        sexuality=[
            app_commands.Choice(name=name, value=value)
            for name, value in SEXUALITY_OPTIONS
        ],
        maw_belief=[
            app_commands.Choice(name=label, value=value)
            for label, value in MAW_BELIEF_OPTIONS
        ],
        size=[
            app_commands.Choice(name="Auto (role / age)", value="auto"),
            app_commands.Choice(name="Small", value="small"),
            app_commands.Choice(name="Medium", value="medium"),
            app_commands.Choice(name="Large", value="large"),
        ],
    )
    async def wolfset(
        self,
        interaction: discord.Interaction,
        field: str,
        birth_sex: str | None = None,
        sexuality: str | None = None,
        maw_belief: str | None = None,
        size: str | None = None,
    ):
        if field == "birth_sex":
            if not birth_sex:
                await interaction.response.send_message("Pick a **birth_sex**.", ephemeral=True)
                return
            await self._setbirthsex(interaction, birth_sex)
        elif field == "sexuality":
            if not sexuality:
                await interaction.response.send_message("Pick a **sexuality**.", ephemeral=True)
                return
            await self._setsexuality(interaction, sexuality)
        elif field == "maw_belief":
            if not maw_belief:
                await interaction.response.send_message("Pick a **maw_belief**.", ephemeral=True)
                return
            await self._setmawbelief(interaction, maw_belief)
        elif field == "size":
            if not size:
                await interaction.response.send_message("Pick a **size**.", ephemeral=True)
                return
            await self._setsize(interaction, size)

    async def _setsize(self, interaction: discord.Interaction, size: str):
        user = await self._require_user(interaction)
        if not user:
            return
        ok, err = db.set_size_class(interaction.user.id, size)
        if not ok:
            embed = howlbert_embed("Cannot Update", err or "Invalid size.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        from engine.combat_size import format_size_class_profile

        updated = db.get_user(interaction.user.id)
        embed = howlbert_embed(
            "Combat Size Updated",
            format_size_class_profile(updated),
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _setbirthsex(self, interaction: discord.Interaction, birth_sex: str):
        user = await self._require_user(interaction)
        if not user:
            return
        db.set_birth_sex(interaction.user.id, birth_sex)
        label = BIRTH_SEX_LABELS.get(birth_sex, birth_sex.title())
        embed = howlbert_embed("Birth Sex Updated", f"Recorded as **{label}**.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _setsexuality(self, interaction: discord.Interaction, sexuality: str):
        user = await self._require_user(interaction)
        if not user:
            return
        ok, err = db.set_sexuality(interaction.user.id, sexuality)
        if not ok:
            embed = howlbert_embed("Cannot Update", err or "Invalid sexuality.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        label = SEXUALITY_LABELS.get(sexuality, sexuality.title())
        embed = howlbert_embed("Sexuality Updated", f"Recorded as **{label}**.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _setmawbelief(self, interaction: discord.Interaction, maw_belief: str):
        user = await self._require_user(interaction)
        if not user:
            return
        ok, err = db.set_maw_belief(interaction.user.id, maw_belief)
        if not ok:
            embed = howlbert_embed("Cannot Update", err or "Invalid belief.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        from engine.maw_belief import format_maw_belief

        user = db.get_user(interaction.user.id)
        text = format_maw_belief(user) or maw_belief
        embed = howlbert_embed("Maw Belief Updated", text, color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _other_wolf_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        active_id = db.get_active_wolf_id(interaction.user.id)
        choices = []
        for w in db.list_user_wolves(interaction.user.id):
            if w["id"] == active_id:
                continue
            if current and current.lower() not in w["wolf_name"].lower():
                continue
            choices.append(app_commands.Choice(name=w["wolf_name"], value=w["wolf_name"]))
        return choices[:25]

    async def _young_wolf_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        active_id = db.get_active_wolf_id(interaction.user.id)
        choices = []
        for w in db.list_user_wolves(interaction.user.id):
            if w["id"] == active_id:
                continue
            if w["age_months"] >= JUVENILE_MAX_MOONS:
                continue
            if current and current.lower() not in w["wolf_name"].lower():
                continue
            stage = stage_label(stage_for_age(w["age_months"]))
            choices.append(
                app_commands.Choice(name=f"{w['wolf_name']} ({stage})", value=w["wolf_name"])
            )
        return choices[:25]

    async def _nursing_pup_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        from config import PUP_MAX_MOONS
        from engine.nursing import is_nursery_caretaker

        user = db.get_user(interaction.user.id)
        if not user:
            return []
        pups: list = []
        if user["birth_sex"] == "female":
            pups.extend(db.get_nursing_pups_for_mother(user["id"]))
        if is_nursery_caretaker(user) and user["pack_id"]:
            pack_pups = db.get_pack_pups_needing_feed(user["pack_id"])
            seen = {p["id"] for p in pups}
            pups.extend(p for p in pack_pups if p["id"] not in seen)
        choices = []
        for pup in pups:
            if current and current.lower() not in pup["wolf_name"].lower():
                continue
            choices.append(
                app_commands.Choice(
                    name=f"{pup['wolf_name']} ({pup['age_months']} moons)",
                    value=pup["wolf_name"],
                )
            )
        return choices[:25]

    @app_commands.command(
        name="courtship",
        description="Court, mate, or check pregnancy status.",
    )
    @app_commands.describe(
        action="court, mate, pregnancy, or rival",
        target="Defender wolf (another player)",
        partner="Challenger wolf (another player; default: you)",
        rival_mode="Physical pin or vocal howl (rival)",
        favor_challenger="Receptive female favors challenger (+2)",
        own_wolf="One of your other wolves (court/mate)",
        difficulty="Social difficulty (court)",
        respond="Accept or decline pending request (mate)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Court another wolf", value="court"),
            app_commands.Choice(name="Mate with partner", value="mate"),
            app_commands.Choice(name="Check pregnancy", value="pregnancy"),
            app_commands.Choice(name="Rival challenge (spring)", value="rival"),
        ],
        difficulty=[
            app_commands.Choice(name="Auto: from standing", value="auto"),
            app_commands.Choice(name="Friendly (DC 12)", value="friendly"),
            app_commands.Choice(name="Neutral (DC 15)", value="neutral"),
            app_commands.Choice(name="Hostile (DC 18)", value="hostile"),
        ],
        respond=[
            app_commands.Choice(name="Accept pending request", value="accept"),
            app_commands.Choice(name="Decline pending request", value="decline"),
        ],
        rival_mode=[
            app_commands.Choice(name="Physical (Strength + Hunting)", value="physical"),
            app_commands.Choice(name="Vocal (Charisma + Intimidation)", value="vocal"),
        ],
    )
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete)
    async def courtship(
        self,
        interaction: discord.Interaction,
        action: str,
        target: discord.Member | None = None,
        partner: discord.Member | None = None,
        own_wolf: str | None = None,
        difficulty: str = "auto",
        respond: str | None = None,
        rival_mode: str = "physical",
        favor_challenger: bool = False,
    ):
        if action == "court":
            await self._court(interaction, target, own_wolf, difficulty)
        elif action == "mate":
            await self._mate(interaction, partner, own_wolf, respond)
        elif action == "pregnancy":
            await self._pregnancy(interaction)
        elif action == "rival":
            await self._rival_challenge(
                interaction, target, partner, own_wolf, rival_mode, favor_challenger
            )

    async def _court(
        self,
        interaction: discord.Interaction,
        target: discord.Member | None = None,
        own_wolf: str | None = None,
        difficulty: str = "auto",
    ):
        user = await self._require_user(interaction)
        if not user:
            return

        block = young_wolf_block(user, action="court")
        if block:
            embed = howlbert_embed("Forbidden", block, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from engine.mental_effects import social_activity_block

        mind_block = social_activity_block(user)
        if mind_block:
            embed = howlbert_embed("Mind Lost", mind_block, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        target_user, err = _resolve_partner_wolf(
            user, interaction, partner=target, own_wolf=own_wolf
        )
        if err:
            if err == "__not_registered__":
                embed = howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
            else:
                embed = howlbert_embed("Invalid Target", err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        tblock = young_wolf_block(target_user, action="court")
        if tblock:
            embed = howlbert_embed("Forbidden", tblock, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        partner_mind = social_activity_block(target_user)
        if partner_mind:
            embed = howlbert_embed(
                "Mind Lost",
                f"**{target_user['wolf_name']}**: {partner_mind}",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        u_orient = get_sexuality(user)
        allowed, reason = court_attraction_allowed(user, target_user)
        if not allowed:
            embed = howlbert_embed("No Attraction", reason or "Incompatible attraction.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day = world["day_number"] if world else 1
        user_last = user["last_court_day"] if "last_court_day" in user.keys() else 0
        if user_last >= day:
            embed = howlbert_embed(
                "Already Courted",
                "You may court **once per rollover**.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if db.court_blocked_for_pair(user["id"], target_user["id"], day):
            embed = howlbert_embed(
                "Already Tried",
                f"You already courted **{target_user['wolf_name']}** this sunrise.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_id = interaction.guild.id if interaction.guild else None
        effective, override_note = resolve_court_difficulty(
            user, target_user, guild_id, difficulty
        )
        result = run_court_check(user, effective)
        mood_line = apply_court_outcome(user, target_user, result, effective)

        if result["success"]:
            db.update_user(
                target_user["discord_id"],
                wolf_id=target_user["id"],
                receptive_day=day + 7,
            )
        db.update_user(interaction.user.id, wolf_id=user["id"], last_court_day=day)
        db.record_court_attempt(user["id"], target_user["id"], day)

        lines = [
            f"1d20 ({result['die']}) + CHA = **{result['total']}** vs DC **{result['dc']}**",
        ]
        if effective != difficulty or difficulty == "auto":
            lines.append(f"_Difficulty: **{effective}**._")
        if override_note:
            lines.append(override_note)
        if result["outcome"] == "critical_success":
            lines.append("**Critical success**: lasting attraction.")
        elif result["success"]:
            if u_orient == "asexual":
                lines.append("**Success**: a companion bond forms (platonic).")
            elif u_orient in BOND_FIRST_SEXUALITIES:
                lines.append("**Success**: trust deepens; a bond may follow before mateship.")
            else:
                lines.append("**Success**: target is receptive this season.")
        else:
            lines.append("**Failure**: awkwardness or offense.")
        if mood_line:
            lines.append(mood_line)
        from engine.healer_code import apply_medic_court_caught, healer_vow_reminder

        reminder = healer_vow_reminder(user) or healer_vow_reminder(target_user)
        if reminder:
            lines.append(reminder)
        if result["success"]:
            scandal = apply_medic_court_caught(user, target_user)
            if scandal:
                lines.extend(scandal)
        await interaction.response.send_message(
            embed=howlbert_embed("Courtship", "\n".join(lines), color=SUCCESS_COLOR if result["success"] else ERROR_COLOR)
        )

    async def _rival_challenge(
        self,
        interaction: discord.Interaction,
        defender_target: discord.Member | None,
        challenger_partner: discord.Member | None,
        own_wolf: str | None,
        mode: str,
        favor_challenger: bool,
    ):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message("Use in a server.", ephemeral=True)
            return

        world = db.get_world(interaction.guild.id)
        if world["season"] != "spring":
            embed = howlbert_embed(
                "Wrong Season",
                "Rival challenges only occur during **mating season** (spring).",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not defender_target:
            embed = howlbert_embed(
                "Need Defender",
                "Pick a **target** player as the wolf defending mating access.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        defender = db.get_user(defender_target.id)
        if not defender:
            embed = howlbert_embed("Not Registered", "Defender is not on Howlbert.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if challenger_partner:
            challenger = db.get_user(challenger_partner.id)
        elif own_wolf:
            wolves = db.list_user_wolves(interaction.user.id)
            challenger = next((w for w in wolves if w["wolf_name"] == own_wolf), None)
        else:
            challenger = user

        if not challenger:
            embed = howlbert_embed(
                "Need Challenger",
                "Pick a **partner** as challenger or register another wolf.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if challenger["id"] == defender["id"]:
            embed = howlbert_embed(
                "Same Wolf",
                "Challenger and defender must be different wolves.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from engine.rival_challenge import execute_rival_challenge

        winner, body = execute_rival_challenge(
            challenger,
            defender,
            mode="vocal" if mode == "vocal" else "physical",
            female_favors_challenger=favor_challenger,
            day=world["day_number"],
        )
        footer = (
            "_The receptive female is not forced to mate with the winner; she may still refuse._"
        )
        embed = howlbert_embed(
            f"Rival Challenge: {winner} wins",
            body + "\n\n" + footer,
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed)

    async def _mate(
        self,
        interaction: discord.Interaction,
        partner: discord.Member | None = None,
        own_wolf: str | None = None,
        respond: str | None = None,
    ):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message("Use in a server.", ephemeral=True)
            return

        if respond in ("accept", "decline"):
            pending = db.get_pending_mate_for_partner(interaction.user.id)
            if not pending:
                embed = howlbert_embed("No Request", "You have no pending mating request.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if respond == "decline":
                db.set_pending_mate_status(pending["id"], "declined")
                await interaction.response.send_message(
                    embed=howlbert_embed("Declined", "You declined the mating request.", color=ERROR_COLOR)
                )
                return
            initiator = db.get_user_by_id(pending["initiator_wolf_id"])
            partner_user = db.get_user_by_id(pending["partner_wolf_id"])
            if not initiator or not partner_user:
                db.set_pending_mate_status(pending["id"], "expired")
                embed = howlbert_embed("Expired", "One of the wolves no longer exists.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            world = db.get_world(interaction.guild.id)
            if world["season"] != "spring":
                embed = howlbert_embed(
                    "Wrong Season",
                    "Mating season ended before you could respond.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if partner_user["receptive_day"] < world["day_number"]:
                embed = howlbert_embed(
                    "Not Receptive",
                    "You are no longer receptive; they must `/court` you again.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            ok, body, color, hard_fail = execute_mating(
                initiator, partner_user, day_number=world["day_number"]
            )
            if ok and not hard_fail:
                db.set_pending_mate_status(pending["id"], "accepted")
            else:
                db.set_pending_mate_status(pending["id"], "expired")
            title = mating_embed_title(body, hard_fail=hard_fail or not ok)
            await interaction.response.send_message(embed=howlbert_embed(title, body, color=color))
            return

        block = young_wolf_block(user, action="mate")
        if block:
            embed = howlbert_embed("Forbidden", block, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from engine.mental_effects import social_activity_block

        for wolf, label in ((user, "You"),):
            mind_block = social_activity_block(wolf)
            if mind_block:
                embed = howlbert_embed("Mind Lost", mind_block, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        world = db.get_world(interaction.guild.id)
        if world["season"] != "spring":
            embed = howlbert_embed(
                "Wrong Season",
                "Females can only conceive during **Newgrowth** (spring mating season).",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        partner_user, err = _resolve_partner_wolf(
            user, interaction, partner=partner, own_wolf=own_wolf
        )
        if err:
            if err == "__not_registered__":
                embed = howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
            else:
                embed = howlbert_embed("Invalid Partner", err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        pblock = young_wolf_block(partner_user, action="mate")
        if pblock:
            embed = howlbert_embed("Forbidden", pblock, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        partner_mind = social_activity_block(partner_user)
        if partner_mind:
            embed = howlbert_embed(
                "Mind Lost",
                f"**{partner_user['wolf_name']}**: {partner_mind}",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        same_owner = partner_user["discord_id"] == interaction.user.id
        if not same_owner and partner_user["receptive_day"] < world["day_number"]:
            embed = howlbert_embed(
                "Not Receptive",
                "Court them first with `/court`, or they may refuse.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not same_owner:
            existing = db.get_pending_mate_for_pair(user["id"], partner_user["id"])
            if existing:
                embed = howlbert_embed(
                    "Request Pending",
                    "A mating request is already waiting for a response.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            pending_id = db.create_pending_mate(
                guild_id=interaction.guild.id,
                channel_id=interaction.channel.id,
                initiator_wolf_id=user["id"],
                partner_wolf_id=partner_user["id"],
                partner_discord_id=partner_user["discord_id"],
                day_number=world["day_number"],
            )
            view = MateConsentView(pending_id)
            embed = howlbert_embed(
                "Mating Request",
                f"**{user['wolf_name']}** wants to mate with **{partner_user['wolf_name']}**.\n"
                f"<@{partner_user['discord_id']}>; accept or decline below, or use "
                f"`/mate respond:Accept pending request`.",
                color=SUCCESS_COLOR,
            )
            await interaction.response.send_message(embed=embed, view=view)
            msg = await interaction.original_response()
            db.set_pending_mate_message(pending_id, msg.id)
            await notify_consent_request(
                self.bot,
                partner_user["discord_id"],
                title="Mating Request",
                body=(
                    f"**{user['wolf_name']}** wants to mate with **{partner_user['wolf_name']}**.\n"
                    "Check the channel for **Accept/Decline** buttons, or use "
                    "`/mate respond:Accept pending request`."
                ),
            )
            return

        ok, body, color, hard_fail = execute_mating(user, partner_user, day_number=world["day_number"])
        title = mating_embed_title(body, hard_fail=hard_fail or not ok)
        await interaction.response.send_message(embed=howlbert_embed(title, body, color=color))

    async def _pregnancy(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return

        if not user["is_pregnant"]:
            subject = None
            mate = db.get_bonded_mate(user)
            if mate and mate["is_pregnant"]:
                subject = mate
                role_note = f"You are the expectant mate of **{mate['wolf_name']}**."
            else:
                as_father = db.get_pregnancy_where_partner(user["id"])
                if as_father:
                    subject = as_father
                    role_note = f"Your mate **{as_father['wolf_name']}** is expecting."
            if not subject:
                embed = howlbert_embed("Not Pregnant", "No active pregnancy on you or your mate.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        else:
            subject = user
            role_note = None

        day = 0
        if interaction.guild:
            day = db.get_world(interaction.guild.id)["day_number"]
        elapsed = max(0, day - subject["pregnancy_start_day"])
        remaining = max(0, GESTATION_DAYS - elapsed)
        mate = db.get_mate_wolf(subject)
        mate_name = mate["wolf_name"] if mate else "Unknown"

        embed = howlbert_embed("Pregnancy", color=SUCCESS_COLOR)
        if role_note:
            embed.description = role_note
        embed.add_field(name="Expectant", value=subject["wolf_name"], inline=True)
        embed.add_field(name="Days elapsed", value=str(elapsed), inline=True)
        embed.add_field(name="Days until birth", value=str(remaining), inline=True)
        embed.add_field(name="Mate", value=mate_name, inline=True)
        if remaining == 0:
            who = "she" if subject["id"] == user["id"] else subject["wolf_name"]
            embed.set_footer(text=f"Ready for `/pupcare action:birth names:…`; {who} can name the litter.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="pupcare",
        description="List pups, birth a litter, save a dying pup, or adopt.",
    )
    @app_commands.describe(
        action="list, birth, feed, save, or adopt",
        names="Comma-separated pup names (birth)",
        name="Pup name (save or feed one pup)",
        partner="Bonded mate (adopt)",
        own_wolf="Your bonded mate wolf (adopt)",
        youth="Another player's wolf to adopt",
        own_youth="Your pup or juvenile to adopt",
        respond="Accept or decline adoption request",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="List your pups", value="list"),
            app_commands.Choice(name="Birth litter", value="birth"),
            app_commands.Choice(name="Feed / nurse pups", value="feed"),
            app_commands.Choice(name="Save dying pup", value="save"),
            app_commands.Choice(name="Adopt youth", value="adopt"),
        ],
        respond=[
            app_commands.Choice(name="Accept pending adoption", value="accept"),
            app_commands.Choice(name="Decline pending adoption", value="decline"),
        ],
    )
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, own_youth=_young_wolf_autocomplete, name=_nursing_pup_autocomplete)
    async def pupcare(
        self,
        interaction: discord.Interaction,
        action: str,
        names: str | None = None,
        name: str | None = None,
        partner: discord.Member | None = None,
        own_wolf: str | None = None,
        youth: discord.Member | None = None,
        own_youth: str | None = None,
        respond: str | None = None,
    ):
        if action == "list":
            await self._pups(interaction)
        elif action == "birth":
            if not names:
                await interaction.response.send_message("Provide **names** for the litter.", ephemeral=True)
                return
            await self._birth(interaction, names)
        elif action == "feed":
            await self._feedpups(interaction, name, own_wolf)
        elif action == "save":
            if not name:
                await interaction.response.send_message("Provide the pup **name**.", ephemeral=True)
                return
            await self._savepup(interaction, name)
        elif action == "adopt":
            await self._adoptpup(interaction, partner, own_wolf, youth, own_youth, respond)

    async def _birth(self, interaction: discord.Interaction, names: str):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message("Use in a server.", ephemeral=True)
            return

        if not user["is_pregnant"]:
            embed = howlbert_embed("Not Pregnant", "This wolf is not expecting pups.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        world = db.get_world(interaction.guild.id)
        elapsed = world["day_number"] - user["pregnancy_start_day"]
        if elapsed < GESTATION_DAYS:
            embed = howlbert_embed(
                "Too Early",
                f"**{GESTATION_DAYS - elapsed}** days of gestation remain.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        father = db.get_mate_wolf(user)
        result = birth_check(user)
        from engine.herb_buffs import consume_birth_save_advantage

        if result.get("used_birth_advantage"):
            db.update_user(interaction.user.id, wolf_id=user["id"], **consume_birth_save_advantage(user))
        if result.get("extra_pup_from_borage"):
            db.update_user(interaction.user.id, wolf_id=user["id"], extra_pup_milk=0)
        pups_born = result["litter_size"]
        if result["outcome"] == "critical_failure":
            pups_born = max(1, pups_born - 1)

        parsed_names, name_err = parse_litter_names(names, pups_born)
        if name_err:
            embed = howlbert_embed("Invalid Names", name_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        for pup_name in parsed_names:
            if db.wolf_name_taken(pup_name) or db.pending_pup_name_taken(pup_name):
                embed = howlbert_embed(
                    "Name Taken",
                    f"The name **{pup_name}** is already taken or reserved for neonatal care.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        born_names: list[str] = []
        born_pup_ids: list[int] = []
        stillborn_lines: list[str] = []
        mutation_lines: list[str] = []
        father_id = father["id"] if father else None
        from engine.genetics import GENETIC_CONDITIONS, encode_genetic_conditions, roll_pup_genetic_conditions
        from engine.stillborn import format_stillborn_save_hint, save_pending_stillborn

        world = db.get_world(interaction.guild.id)
        born_day = world["day_number"]

        for pup_name in parsed_names:
            conditions, lethal = roll_pup_genetic_conditions(
                user, father, birth_outcome=result["outcome"]
            )
            if lethal:
                stats = generate_pup_stats(user, father) if father else generate_pup_stats(user, user)
                save_pending_stillborn(
                    discord_id=user["discord_id"],
                    mother_wolf_id=user["id"],
                    pup_name=pup_name,
                    genetic_conditions=conditions,
                    stats=stats,
                    father_wolf_id=father_id,
                    pack_id=user["pack_id"],
                    great_pack=user["great_pack"],
                    birth_sex=random_birth_sex(),
                    born_day=born_day,
                )
                stillborn_lines.append(format_stillborn_save_hint(pup_name, conditions))
                continue
            stats = generate_pup_stats(user, father) if father else generate_pup_stats(user, user)
            pup_id = db.register_born_wolf(
                discord_id=user["discord_id"],
                wolf_name=pup_name,
                mother_wolf_id=user["id"],
                father_wolf_id=father_id,
                stats=stats,
                pack_id=user["pack_id"],
                great_pack=user["great_pack"],
                birth_sex=random_birth_sex(),
                genetic_conditions=encode_genetic_conditions(conditions),
            )
            born_pup_ids.append(pup_id)
            born_names.append(pup_name)
            if conditions:
                muts = ", ".join(GENETIC_CONDITIONS[c]["name"] for c in conditions)
                mutation_lines.append(f"**{pup_name}**: {muts}")

        if not born_names and stillborn_lines:
            db.clear_pregnancy(user["id"])
            body = (
                f"Birth check: **{result['total']}** vs DC 12; the litter did not survive.\n"
                + "\n".join(stillborn_lines)
                + "\n\nBuy **Vitality Salve** from `/bones action:shop` and use **`/pupcare action:save`** before the next `/rollover`."
            )
            await interaction.response.send_message(embed=howlbert_embed("Birth", body, color=ERROR_COLOR))
            return

        db.clear_pregnancy(user["id"])
        if user["pack_id"]:
            db.adjust_pack_unity(user["pack_id"], 1)

        from engine.disease_contract import schedule_milk_fever_risk

        world = db.get_world(interaction.guild.id)
        user = db.get_user(interaction.user.id)
        milk_note = schedule_milk_fever_risk(
            user,
            day=world["day_number"],
            difficult_birth=not result["success"],
            litter_size=len(born_names),
        )

        name_line = ", ".join(f"**{n}**" for n in born_names)
        father_line = ""
        if father:
            father_line = f"\n**{father['wolf_name']}** and **{user['wolf_name']}** named the litter."
        body = (
            f"Birth check: **{result['total']}** vs DC 12; "
            f"**{len(born_names)}** pup(s) born: {name_line}."
            f"{father_line}\n"
            "Born pups use **extra slots** (not your 3 `/register` slots). "
            "Use `/switchwolf` to play them."
        )
        if mutation_lines:
            body += "\n\n**Mutations:**\n" + "\n".join(mutation_lines)
        if stillborn_lines:
            body += "\n\n**Dying pups:**\n" + "\n".join(stillborn_lines)
        if not result["success"]:
            body += "\nDifficult birth; mother gains 1 exhaustion."
            db.set_user_conditions(interaction.user.id, exhaustion=min(6, user["exhaustion"] + 1))
        if milk_note:
            body += f"\n\n{milk_note}"
        body += (
            "\n\nNurse the litter each sunrise with **`/pupcare action:feed`** "
            "(mothers) or ask a **Caretaker** to mash-feed pack pups."
        )
        if not user["pack_id"]:
            from engine.nursing import lone_nursing_note

            body += lone_nursing_note(user)

        from engine.healer_code import apply_medic_birth_scandal, healer_vow_reminder

        reminder = healer_vow_reminder(user)
        if father:
            r2 = healer_vow_reminder(father)
            if r2:
                reminder = reminder or r2
        if reminder:
            body += f"\n\n{reminder}"
        scandal = apply_medic_birth_scandal(user, father, born_pup_ids)
        if scandal:
            body += "\n\n" + "\n\n".join(scandal)
            await interaction.response.send_message(
                embed=howlbert_embed("Birth; Healer Scandal", body, color=ERROR_COLOR)
            )
            return

        await interaction.response.send_message(embed=howlbert_embed("Birth", body, color=SUCCESS_COLOR))

    async def _feedpups(
        self,
        interaction: discord.Interaction,
        pup_name: str | None,
        own_wolf: str | None,
    ):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message("Use in a server.", ephemeral=True)
            return

        feeder = user
        if own_wolf:
            alt = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not alt:
                embed = howlbert_embed(
                    "Unknown Wolf",
                    f"You have no wolf named **{own_wolf.strip()}**.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            feeder = alt

        world = db.get_world(interaction.guild.id)
        from engine.nursing import execute_nursing

        ok, msg = execute_nursing(
            feeder,
            day_number=world["day_number"],
            pack_id=feeder["pack_id"],
            pup_name=pup_name,
        )
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = "Nursing" if ok else "Cannot Feed"
        await interaction.response.send_message(embed=howlbert_embed(title, msg, color=color))

    async def _savepup(self, interaction: discord.Interaction, name: str):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message("Use in a server.", ephemeral=True)
            return

        world = db.get_world(interaction.guild.id)
        from engine.stillborn import try_save_stillborn_pup

        ok, msg = try_save_stillborn_pup(
            interaction.user.id, name, current_day=world["day_number"]
        )
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed("Save Pup", msg, color=color))

    async def _pups(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return

        wolf_ids = {w["id"] for w in db.list_user_wolves(interaction.user.id)}
        children = db.get_lineage_children_for_discord(interaction.user.id)
        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day_number = world["day_number"] if world else None

        if not children:
            embed = howlbert_embed("No Pups", "You have no biological or adopted young yet.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from engine.nursing import pup_needs_milk_today

        lines = [
            db.format_pup_lineage_entry(
                child,
                wolf_ids,
                viewer_discord_id=interaction.user.id,
                day_number=day_number,
            )
            for child in children
        ]
        footer = ""
        if day_number is not None and any(
            pup_needs_milk_today(c, day_number) for c in children
        ):
            footer = (
                "\n\nPups marked **needs milk** want **`/pupcare action:feed`** this sunrise."
            )
        await interaction.response.send_message(
            embed=howlbert_embed("Your Pups", "\n".join(lines) + footer)
        )

    async def _adoptpup(
        self,
        interaction: discord.Interaction,
        partner: discord.Member | None = None,
        own_wolf: str | None = None,
        youth: discord.Member | None = None,
        own_youth: str | None = None,
        respond: str | None = None,
    ):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message("Use in a server.", ephemeral=True)
            return

        if respond in ("accept", "decline"):
            pending = db.get_pending_adoption_for_owner(interaction.user.id)
            if not pending:
                embed = howlbert_embed("No Request", "You have no pending adoption request.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if respond == "decline":
                ok, msg = decline_pending_adoption(pending["id"])
            else:
                ok, msg = accept_pending_adoption(pending["id"])
            color = SUCCESS_COLOR if ok and respond == "accept" else ERROR_COLOR
            title = "Adopted" if ok and respond == "accept" else ("Declined" if ok else "Failed")
            await interaction.response.send_message(embed=howlbert_embed(title, msg, color=color))
            return

        partner_user, err = _resolve_partner_wolf(
            user, interaction, partner=partner, own_wolf=own_wolf
        )
        if err:
            if err == "__not_registered__":
                embed = howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
            else:
                embed = howlbert_embed("Invalid Partner", err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not are_bonded_mates(user, partner_user):
            embed = howlbert_embed(
                "Not Bonded",
                "You must be **mutually bonded** mates (`/mate` after courtship).",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        world = db.get_world(interaction.guild.id)
        day = world["day_number"]
        user_last = user["last_adopt_day"] if "last_adopt_day" in user.keys() else 0
        partner_last = (
            partner_user["last_adopt_day"] if "last_adopt_day" in partner_user.keys() else 0
        )
        if user_last >= day or partner_last >= day:
            embed = howlbert_embed(
                "Already Adopted",
                "Each bonded pair may adopt **once per rollover**.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        adoptee, adoptee_err = _resolve_adoptee(
            user, interaction, youth=youth, own_youth=own_youth
        )
        if adoptee_err:
            if adoptee_err == "__not_registered__":
                embed = howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
            else:
                embed = howlbert_embed("Invalid Youth", adoptee_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        adopt_err = adoption_eligibility_error(adoptee, user, partner_user)
        if adopt_err:
            embed = howlbert_embed("Cannot Adopt", adopt_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        check = courtship_check(user, "friendly")
        if not check["success"]:
            embed = howlbert_embed(
                "Adoption Denied",
                f"Bonding check: **{check['total']}** vs DC **{check['dc']}**; the den is not ready.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed)
            return

        needs_consent = adoptee["discord_id"] not in (
            interaction.user.id,
            partner_user["discord_id"],
        )

        if not needs_consent:
            db.set_adoptive_parents(adoptee["id"], user["id"], partner_user["id"])
            db.update_user(interaction.user.id, wolf_id=user["id"], last_adopt_day=day)
            db.update_user(
                partner_user["discord_id"],
                wolf_id=partner_user["id"],
                last_adopt_day=day,
            )
            if user["pack_id"] and user["pack_id"] == partner_user["pack_id"]:
                db.adjust_pack_unity(user["pack_id"], 1)

            stage = stage_label(stage_for_age(adoptee["age_months"]))
            body = (
                f"**{adoptee['wolf_name']}** ({stage}) joins **{user['wolf_name']}** and "
                f"**{partner_user['wolf_name']}**'s den."
            )
            from engine.healer_code import apply_medic_adopt_scandal, healer_vow_reminder

            for w in (user, partner_user):
                rem = healer_vow_reminder(w)
                if rem:
                    body += f"\n\n{rem}"
            scandal = apply_medic_adopt_scandal(user, partner_user, adoptee)
            if scandal:
                body += "\n\n" + "\n\n".join(scandal)
                embed = howlbert_embed("Adoption; Healer Scandal", body, color=ERROR_COLOR)
            else:
                embed = howlbert_embed("Adopted", body, color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            return

        if db.get_pending_adoption_for_adopter_pair(user["id"], partner_user["id"]):
            embed = howlbert_embed(
                "Request Pending",
                "You already have an adoption awaiting the youth's answer.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        pending_id = db.create_pending_adoption(
            guild_id=interaction.guild.id,
            channel_id=interaction.channel.id,
            adopter_1_wolf_id=user["id"],
            adopter_2_wolf_id=partner_user["id"],
            youth_wolf_id=adoptee["id"],
            youth_owner_discord_id=adoptee["discord_id"],
            day_number=day,
        )
        view = AdoptionConsentView(pending_id)
        stage = stage_label(stage_for_age(adoptee["age_months"]))
        embed = howlbert_embed(
            "Adoption Request",
            f"**{user['wolf_name']}** and **{partner_user['wolf_name']}** want to adopt "
            f"**{adoptee['wolf_name']}** ({stage}).\n"
            f"<@{adoptee['discord_id']}>; accept or decline below, or `/adoptpup respond:Accept pending adoption`.",
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        db.set_pending_adoption_message(pending_id, msg.id)
        await notify_consent_request(
            self.bot,
            adoptee["discord_id"],
            title="Adoption Request",
            body=(
                f"**{user['wolf_name']}** and **{partner_user['wolf_name']}** want to adopt "
                f"**{adoptee['wolf_name']}** ({stage}).\n"
                "Check the channel for **Accept/Decline** buttons, or use "
                "`/adoptpup respond:Accept pending adoption`."
            ),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Life(bot))
