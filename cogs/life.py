import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.death_saves import roll_death_save, stabilize_check
from engine.attraction import BOND_FIRST_SEXUALITIES, are_bonded_mates, court_attraction_allowed, get_sexuality
from engine.family import GESTATION_DAYS, XP_PER_ATTRIBUTE, XP_PER_ROLE_FEATURE, birth_check, courtship_check, generate_pup_stats, spend_xp_attribute, spend_xp_trait_bonus
from engine.aging import stage_for_age, stage_label
from engine.youth_lineage import adoption_eligibility_error, parse_litter_names, random_birth_sex
from engine.courtship import apply_court_outcome, resolve_court_difficulty, run_court_check
from engine.pack_relations import court_relation_note
from engine.adoption_consent import accept_pending_adoption, decline_pending_adoption
from engine.mating import execute_mating, mating_embed_title
from config import JUVENILE_MAX_MOONS
from utils.adoption_views import AdoptionConsentView
from utils.mate_views import MateConsentView
from rpg_rules import ROLE_FEATURES, ROLE_LABELS, SKILLS, MAX_SKILL_RANK, XP_PER_TRAIT
from engine.role_restrictions import young_wolf_block
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label
from utils.notifications import notify_consent_request
from utils.herb_autocomplete import herb_inventory_autocomplete
from utils.wolf_autocomplete import make_member_wolf_autocomplete
from cogs.care_handlers import dissect_cadaver, field_dressing, lay_to_rest, naming_ceremony, quarantine_command, sacred_visit, spirit_ritual, treat, wound_wash

def _resolve_own_wolf(discord_id: int, name: str):
    rows = db.list_user_wolves(discord_id)
    return next((w for w in rows if w['wolf_name'].lower() == name.strip().lower()), None)


def _mentor_court_approval_note(courter, target) -> str | None:
    """
    If the courter has a mentor bond, the mentor's feelings about the target
    affect the courtship; approval eases it, disapproval adds shadow.
    Returns a note prefixed with '+' (ease) or '-' (tension) or None.
    """
    mentor_bonds = db.get_bonds_for_wolf(courter['id'])
    for row in mentor_bonds:
        if row['bond_type'] != 'mentor':
            continue
        mentor_id = row['wolf_b_id'] if row['wolf_a_id'] == courter['id'] else row['wolf_a_id']
        if int(row['strength']) < 40:
            continue
        mentor = db.get_user_by_id(mentor_id)
        if not mentor:
            continue
        rivalry = db.get_bond(mentor_id, target['id'], 'rivalry')
        friendship = db.get_bond(mentor_id, target['id'], 'friendship')
        if rivalry and int(rivalry['strength']) >= 50:
            return (
                f"-_**{mentor['wolf_name']}** knows **{target['wolf_name']}**; and not warmly. "
                f"their disapproval hangs in the air._"
            )
        if friendship and int(friendship['strength']) >= 50:
            return (
                f"+_**{mentor['wolf_name']}** thinks well of **{target['wolf_name']}**. "
                f"that quietly opens a door._"
            )
    return None


def _kin_protective_court_note(courter, target) -> str | None:
    """If a kin of the target has a rivalry with the courter, surface a protective note."""
    import random
    kin_bonds = db.get_bonds_for_wolf(target['id'])
    for row in kin_bonds:
        if row['bond_type'] != 'kin':
            continue
        kin_id = row['wolf_b_id'] if row['wolf_a_id'] == target['id'] else row['wolf_a_id']
        rivalry = db.get_bond(kin_id, courter['id'], 'rivalry')
        if rivalry and int(rivalry['strength']) >= 40:
            kin_wolf = db.get_user_by_id(kin_id)
            if not kin_wolf:
                continue
            phrases = (
                f"_word is already reaching **{kin_wolf['wolf_name']}**; and they don't feel warmly about you._",
                f"_**{kin_wolf['wolf_name']}** has their eye on this. the history between you two runs cold._",
                f"_**{kin_wolf['wolf_name']}** catches the scent of this. kin protect their own._",
            )
            return random.choice(phrases)
    return None

def _resolve_partner_wolf(user, interaction: discord.Interaction, *, partner: discord.Member | None, own_wolf: str | None, partner_wolf: str | None = None) -> tuple[object | None, str | None]:
    if partner and own_wolf:
        return (None, 'Pick either another **player** or one of your other wolves (`own_wolf`), not both.')
    if own_wolf:
        target = _resolve_own_wolf(interaction.user.id, own_wolf)
        if not target:
            return (None, 'No wolf with that name on your account. Check `/wolves`.')
        if target['id'] == user['id']:
            return (None, 'Pick a different wolf than your active one.')
        return (target, None)
    if partner:
        if partner.id == interaction.user.id:
            return (None, 'Use `own_wolf` to court or mate another character you own.')
        if partner_wolf:
            target = db.find_user_wolf(partner.id, partner_wolf)
            if not target:
                return (None, db.explain_wolf_not_found(partner.id, partner_wolf, player_label=partner.display_name))
        else:
            target = db.get_user(partner.id)
        if not target:
            return (None, '__not_registered__')
        return (target, None)
    return (None, 'Specify another player or your wolf name in `own_wolf`.')

def _resolve_adoptee(user, interaction: discord.Interaction, *, youth: discord.Member | None, own_youth: str | None, youth_wolf: str | None = None) -> tuple[object | None, str | None]:
    if youth and own_youth:
        return (None, 'Pick either another **player** (`youth`) or one of your young wolves (`own_youth`), not both.')
    if own_youth:
        target = _resolve_own_wolf(interaction.user.id, own_youth)
        if not target:
            return (None, 'No wolf with that name on your account. Check `/wolves`.')
        if target['id'] == user['id']:
            return (None, 'Pick a different wolf than your active one.')
        return (target, None)
    if youth:
        if youth.id == interaction.user.id:
            return (None, 'Use `own_youth` for one of your other pups or juveniles.')
        if youth_wolf:
            target = db.find_user_wolf(youth.id, youth_wolf)
        else:
            target = db.get_user(youth.id)
        if not target:
            return (None, '__not_registered__')
        return (target, None)
    return (None, 'Specify who to adopt with `youth` or `own_youth`.')

_patient_wolf_autocomplete = make_member_wolf_autocomplete("patient")
_helper_wolf_autocomplete = make_member_wolf_autocomplete("helper")
_deceased_wolf_autocomplete = make_member_wolf_autocomplete("deceased")
_quarantine_wolf_autocomplete = make_member_wolf_autocomplete("wolf")
_target_wolf_autocomplete = make_member_wolf_autocomplete("target")
_partner_wolf_autocomplete = make_member_wolf_autocomplete("partner")
_youth_wolf_autocomplete = make_member_wolf_autocomplete("youth")

async def _quarantine_own_wolf_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    active = db.get_user(interaction.user.id)
    if not active:
        return []
    choices = []
    for wolf in db.list_user_wolves(interaction.user.id):
        if wolf['id'] == active['id']:
            continue
        name = wolf['wolf_name']
        if current and current.lower() not in name.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(name), value=name))
    return choices[:25]

class Life(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _require_user(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return user

    @app_commands.command(name='medic', description='clinical care, herb treatment, spirit rites, and sick-den quarantine.')
    @app_commands.describe(action='medic action (see dropdown for the full list)', patient='packmate (stabilize, surgery, treat, ritual, naming, observe)', patient_wolf="specific wolf from that player's roster", own_patient='your other wolf as patient (stabilize, surgery, observe, ritual, naming)', helper='assisting medic for surgery (medicine dc 10 → advantage)', helper_wolf="specific wolf from helper's roster", own_helper='your other wolf as surgery helper', procedure='surgery type (surgery only)', herb='herb key or forage stack (treat)', ritual_herb='douglas_sagewort, lavender, or mountain_ash (ritual)', deceased='dead wolf (lay_to_rest, dissect)', deceased_wolf="specific wolf from that player's roster (lay_to_rest, dissect)", own_deceased='your own dead wolf (lay_to_rest, dissect)', lay_herb='rosemary, lavender, or mint (lay_to_rest)', wolf='packmate to isolate or release (quarantine)', wolf_name="specific wolf from that player's roster (quarantine)", own_wolf='your other wolf (quarantine, treat, field_dressing, wound_wash)', release='release from quarantine instead of isolating', use_yarrow='apply yarrow for +2 (stabilize)', use_cobwebs='cobwebs auto-stabilize (stabilize)', use_poppy='poppy seeds sedation +2 (amputation surgery)', use_meadowsweet='meadowsweet pain ease +1 (stitch / set bone / amputate)', use_loosestrife='purple loosestrife +1 (stitch only)', use_plantain='plantain soothe +1 (extract only)', use_rush_stalks='rush stalks lash splint +2 (set bone only)')
    @app_commands.choices(action=[app_commands.Choice(name='death save (dying wolf)', value='deathsaves'), app_commands.Choice(name='stabilize packmate', value='stabilize'), app_commands.Choice(name='surgery on patient', value='surgery'), app_commands.Choice(name='treat with herb', value='treat'), app_commands.Choice(name='field dressing (cobwebs; slows deep gash bleed)', value='field_dressing'), app_commands.Choice(name='wound wash (dock/horsetail; clears infected wound)', value='wound_wash'), app_commands.Choice(name='den checkup', value='checkup'), app_commands.Choice(name='sacred visit (medic)', value='sacred'), app_commands.Choice(name='spirit ritual', value='ritual'), app_commands.Choice(name='pup naming rite', value='naming'), app_commands.Choice(name='lay wolf to rest', value='lay_to_rest'), app_commands.Choice(name='swim therapy (river)', value='swim'), app_commands.Choice(name='quarantine sick wolf', value='quarantine'), app_commands.Choice(name='observe case (apprentice)', value='observe'), app_commands.Choice(name='dissect cadaver (apprentice; learn anatomy)', value='dissect')], procedure=[app_commands.Choice(name='stitch wound (deep gash / infection)', value='stitch'), app_commands.Choice(name='set bone / splint (comfrey + bindweed + 2 sticks)', value='set_bone'), app_commands.Choice(name='extract thorn or splinter', value='extract'), app_commands.Choice(name='amputate ruined limb', value='amputate')])
    @app_commands.autocomplete(herb=herb_inventory_autocomplete, own_wolf=_quarantine_own_wolf_autocomplete, own_patient=_quarantine_own_wolf_autocomplete, own_helper=_quarantine_own_wolf_autocomplete, own_deceased=_quarantine_own_wolf_autocomplete, patient_wolf=_patient_wolf_autocomplete, helper_wolf=_helper_wolf_autocomplete, deceased_wolf=_deceased_wolf_autocomplete, wolf_name=_quarantine_wolf_autocomplete)
    async def medic(self, interaction: discord.Interaction, action: str, patient: discord.Member | None=None, own_patient: str | None=None, helper: discord.Member | None=None, own_helper: str | None=None, procedure: str='stitch', herb: str | None=None, ritual_herb: str | None=None, deceased: discord.Member | None=None, own_deceased: str | None=None, lay_herb: str | None=None, wolf: discord.Member | None=None, own_wolf: str | None=None, release: bool=False, use_yarrow: bool=False, use_cobwebs: bool=False, use_poppy: bool=False, use_meadowsweet: bool=False, use_loosestrife: bool=False, use_plantain: bool=False, use_rush_stalks: bool=False, patient_wolf: str | None=None, helper_wolf: str | None=None, deceased_wolf: str | None=None, wolf_name: str | None=None):
        if action == 'deathsaves':
            await self._deathsaves(interaction)
        elif action == 'stabilize':
            if not patient and not own_patient:
                embed = howlbert_embed('Pick a Patient', 'Stabilize requires a **patient** or **own_patient**.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            if patient and own_patient:
                await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use `patient` or `own_patient`; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if own_patient:
                target_row = _resolve_own_wolf(interaction.user.id, own_patient)
                if not target_row:
                    await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', f'No wolf named **{own_patient}** on your account.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                    return
            else:
                if patient_wolf:
                    target_row = db.find_user_wolf(patient.id, patient_wolf)
                    if not target_row:
                        await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', db.explain_wolf_not_found(patient.id, patient_wolf, player_label=patient.display_name), color=ERROR_COLOR), ephemeral=reply_ephemeral())
                        return
                else:
                    target_row = db.get_user(patient.id)
                if not target_row:
                    await interaction.response.send_message(embed=howlbert_embed('Not Registered', 'Patient is not on Howlbert.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                    return
            await self._stabilize(interaction, target_row, use_yarrow, use_cobwebs)
        elif action == 'surgery':
            if not patient and not own_patient:
                embed = howlbert_embed('Pick a Patient', 'Surgery requires a **patient** or **own_patient**.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            if patient and own_patient:
                await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use `patient` or `own_patient`; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if own_patient:
                target_row = _resolve_own_wolf(interaction.user.id, own_patient)
                if not target_row:
                    await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', f'No wolf named **{own_patient}** on your account.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                    return
            else:
                if patient_wolf:
                    target_row = db.find_user_wolf(patient.id, patient_wolf)
                    if not target_row:
                        await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', db.explain_wolf_not_found(patient.id, patient_wolf, player_label=patient.display_name), color=ERROR_COLOR), ephemeral=reply_ephemeral())
                        return
                else:
                    target_row = db.get_user(patient.id)
                if not target_row:
                    await interaction.response.send_message(embed=howlbert_embed('Not Registered', 'Patient is not on Howlbert.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                    return
            if helper and own_helper:
                await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use `helper` or `own_helper`; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if own_helper:
                helper_row = _resolve_own_wolf(interaction.user.id, own_helper)
                if not helper_row:
                    await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', f'No wolf named **{own_helper}** on your account.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                    return
            elif helper:
                if helper_wolf:
                    helper_row = db.find_user_wolf(helper.id, helper_wolf)
                    if not helper_row:
                        await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', db.explain_wolf_not_found(helper.id, helper_wolf, player_label=helper.display_name), color=ERROR_COLOR), ephemeral=reply_ephemeral())
                        return
                else:
                    helper_row = db.get_user(helper.id)
                if not helper_row:
                    await interaction.response.send_message(embed=howlbert_embed('Not Registered', 'Helper is not on Howlbert.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                    return
            else:
                helper_row = None
            await self._surgery(interaction, target_row, helper_row, procedure, use_poppy, use_meadowsweet, use_loosestrife, use_plantain, use_rush_stalks)
        elif action == 'treat':
            if not herb:
                await interaction.response.send_message(player_message('Provide an inventory **herb** key from `/bones action:inventory` (e.g. `herb_yarrow`).'), ephemeral=reply_ephemeral())
                return
            await treat(interaction, herb, patient, own_wolf, patient_wolf=patient_wolf)
        elif action == 'field_dressing':
            await field_dressing(interaction, own_wolf)
        elif action == 'wound_wash':
            await wound_wash(interaction, own_wolf)
        elif action == 'observe':
            if not patient and not own_patient:
                await interaction.response.send_message(embed=howlbert_embed('Pick a Patient', 'Observe requires a **patient** or **own_patient**.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if patient and own_patient:
                await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use `patient` or `own_patient`; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if own_patient:
                target_row = _resolve_own_wolf(interaction.user.id, own_patient)
                if not target_row:
                    await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', f'No wolf named **{own_patient}** on your account.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                    return
            else:
                if patient_wolf:
                    target_row = db.find_user_wolf(patient.id, patient_wolf)
                    if not target_row:
                        await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', db.explain_wolf_not_found(patient.id, patient_wolf, player_label=patient.display_name), color=ERROR_COLOR), ephemeral=reply_ephemeral())
                        return
                else:
                    target_row = db.get_user(patient.id)
                if not target_row:
                    await interaction.response.send_message(player_message('Patient is not on Howlbert.'), ephemeral=reply_ephemeral())
                    return
            await self._observe(interaction, target_row)
        elif action in ('rounds', 'checkup'):
            await self._medic_rounds(interaction)
        elif action == 'sacred':
            await sacred_visit(interaction)
        elif action == 'ritual':
            await spirit_ritual(interaction, patient, ritual_herb, own_patient=own_patient, patient_wolf=patient_wolf)
        elif action == 'naming':
            await naming_ceremony(interaction, patient, own_patient=own_patient, patient_wolf=patient_wolf)
        elif action == 'lay_to_rest':
            await lay_to_rest(interaction, deceased, lay_herb, own_deceased=own_deceased, deceased_wolf=deceased_wolf)
        elif action == 'dissect':
            await dissect_cadaver(interaction, deceased, own_deceased=own_deceased, deceased_wolf=deceased_wolf)
        elif action == 'swim':
            await self._swim_therapy(interaction)
        elif action == 'quarantine':
            await quarantine_command(interaction, wolf, own_wolf, release, wolf_name=wolf_name)

    async def _surgery(self, interaction: discord.Interaction, target: dict, helper_row: dict | None, procedure: str, use_poppy: bool, use_meadowsweet: bool, use_loosestrife: bool, use_plantain: bool, use_rush_stalks: bool):
        surgeon = await self._require_user(interaction)
        if not surgeon:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        from engine.surgery import run_surgery
        ok, body = run_surgery(surgeon, target, procedure, day=world['day_number'], use_poppy=use_poppy, use_meadowsweet=use_meadowsweet, use_loosestrife=use_loosestrife, use_plantain=use_plantain, use_rush_stalks=use_rush_stalks, helper=helper_row, guild_id=interaction.guild.id if interaction.guild else None)
        embed = howlbert_embed('Surgery' if ok else 'Surgery Failed', body, color=SUCCESS_COLOR if ok else ERROR_COLOR)
        await interaction.response.send_message(embed=embed)
        if ok:
            gid = interaction.guild.id if interaction.guild else None
            db.increment_quest_progress(interaction.user.id, 'treat', guild_id=gid)

    async def _observe(self, interaction: discord.Interaction, target: dict):
        medic = await self._require_user(interaction)
        if not medic:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        from engine.medical_care import run_observe_apprentice
        ok, body = run_observe_apprentice(medic, target, day=world['day_number'], guild_id=interaction.guild.id if interaction.guild else None)
        if ok:
            from engine.plot_blinking import try_plot_observe_extras
            body += try_plot_observe_extras(medic, guild_id=interaction.guild.id, day=world['day_number'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Observe', body, color=color))
        if ok:
            gid = interaction.guild.id if interaction.guild else None
            db.increment_quest_progress(interaction.user.id, 'treat', guild_id=gid)

    async def _medic_rounds(self, interaction: discord.Interaction):
        medic = await self._require_user(interaction)
        if not medic:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use in a server.'), ephemeral=reply_ephemeral())
            return
        if not medic['pack_id']:
            await interaction.response.send_message(embed=howlbert_embed('No Pack', 'Join a pack to walk den checkups.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        from engine.medical_care import run_medic_rounds
        ok, body = run_medic_rounds(medic, day=world['day_number'])
        if not ok:
            await interaction.response.send_message(embed=howlbert_embed('Den Checkup', body, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.healer_refusal import healer_refusal_reminder
        rem = healer_refusal_reminder(medic, pack_id=medic['pack_id'])
        if rem:
            body += f'\n\n{rem}'
        await interaction.response.send_message(embed=howlbert_embed('Den Checkup', body))

    async def _swim_therapy(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use `/register` in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        from engine.medical_care import run_swim_therapy
        ok, body = run_swim_therapy(user, day=world['day_number'], season=world['season'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Swim Therapy', body, color=color))

    async def _deathsaves(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return
        if user['hp'] > 0 and user['condition'] != 'dying':
            embed = howlbert_embed('Not Dying', 'Death saves are only for wolves who are **dying** (0 HP; from combat, starvation, or thirst).', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if user['condition'] == 'dead':
            embed = howlbert_embed('Dead', 'This wolf has already passed.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if user['death_save_round'] == 0:
            db.enter_dying_state(interaction.user.id)
            user = db.get_user(interaction.user.id)
        result = roll_death_save(user)
        if result.get('consume_fields'):
            db.update_user(interaction.user.id, wolf_id=user['id'], **result['consume_fields'])
        outcome = db.apply_death_save_result(interaction.user.id, result['success'], result.get('nat20', False))
        body = f"Round **{result['round']}**: 1d20 ({result['die']}) + {result['modifier']} = **{result['total']}** vs DC **{result['dc']}**"
        if outcome == 'stabilized':
            body += '\n\n**Stabilized at 1 HP.** Depleted satiety/hydration restored to a survivable level.'
            color = SUCCESS_COLOR
        elif outcome == 'died':
            from engine.obituary import format_obituary_line
            obituary = format_obituary_line(user['id'], user['wolf_name'], 'failed death saves')
            body += f"\n\n**The wolf dies. Permanently.**\n{obituary}\n`/rpg action:delete confirm:DELETE` then `/register` for a fresh wolf."
            color = ERROR_COLOR
        else:
            body += f"\n\nSurvived round {result['round']}. **Round {result['round'] + 1}** next."
            color = SUCCESS_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Death Save', body, color=color))
        if outcome == 'died' and interaction.guild_id:
            from utils.notifications import post_obituary_to_memoriam
            try:
                await post_obituary_to_memoriam(
                    interaction.client, interaction.guild_id, obituary, wolf_name=user['wolf_name']
                )
            except Exception:
                import logging
                logging.getLogger("howlbert").exception(
                    "Could not post obituary for wolf %s", user['id']
                )

    async def _stabilize(self, interaction: discord.Interaction, target: dict, use_yarrow: bool=False, use_cobwebs: bool=False):
        healer = await self._require_user(interaction)
        if not healer:
            return
        if target['hp'] > 0 and target['condition'] != 'dying':
            embed = howlbert_embed('Not Dying', f"**{target['wolf_name']}** is not at 0 HP.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if interaction.guild:
            from engine.medical_access import can_medic_treat_cross_pack
            ok_cross, cross_msg = can_medic_treat_cross_pack(healer, target, interaction.guild.id, emergency_stabilize=True)
            if not ok_cross:
                embed = howlbert_embed("Can't Stabilize", cross_msg, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        if use_cobwebs:
            item = db.get_item_by_key('herb_cobwebs')
            if not item or db.get_inventory_quantity(interaction.user.id, item['id']) < 1:
                embed = howlbert_embed('No Cobwebs', 'You need **cobwebs** in inventory.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            db.consume_item(interaction.user.id, item['id'])
            db.stabilize_patient_by_wolf_id(target['id'])
            body = f"Cobwebs hold; **{target['wolf_name']}** stabilizes at 1 HP."
            from engine.medical_access import apply_stabilize_standing
            body += apply_stabilize_standing(healer, target, interaction.guild.id if interaction.guild else None, success=True)
            embed = howlbert_embed('Stabilized', body, color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            gid = interaction.guild.id if interaction.guild else None
            db.increment_quest_progress(interaction.user.id, 'treat', guild_id=gid)
            return
        if use_yarrow:
            item = db.get_item_by_key('herb_yarrow')
            if not item or db.get_inventory_quantity(interaction.user.id, item['id']) < 1:
                embed = howlbert_embed('No Yarrow', 'You need **yarrow** in inventory.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            db.consume_item(interaction.user.id, item['id'])
        check = stabilize_check(healer, yarrow=use_yarrow, patient=target)
        if check.get('consume_fields'):
            db.update_user(target['discord_id'], wolf_id=target['id'], **check['consume_fields'])
        from engine.medical_access import apply_stabilize_standing
        standing_note = apply_stabilize_standing(healer, target, interaction.guild.id if interaction.guild else None, success=bool(check['success']))
        if check['success']:
            db.stabilize_patient_by_wolf_id(target['id'])
            gid = interaction.guild.id if interaction.guild else None
            db.increment_quest_progress(interaction.user.id, 'treat', guild_id=gid)
            embed = howlbert_embed('Stabilized', f"Medicine: **{check['total']}** vs DC 15; **{target['wolf_name']}** at 1 HP." + standing_note, color=SUCCESS_COLOR)
        else:
            embed = howlbert_embed('Failed', f"Medicine: **{check['total']}** vs DC 15; no effect." + standing_note, color=ERROR_COLOR)
        from engine.healer_refusal import healer_refusal_reminder
        rem = healer_refusal_reminder(healer, pack_id=healer['pack_id'] if healer['pack_id'] else None)
        if rem and embed.description:
            embed.description += f'\n\n{rem}'
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='advance', description='view xp or spend it on attributes, skills, or role features.')
    @app_commands.describe(action='view or spend', purchase='what to buy (spend only)', attribute='attribute to raise (spend)', skill='skill to raise (spend)', role_feature='role whose feature to gain (spend)')
    @app_commands.choices(action=[app_commands.Choice(name='view xp', value='view'), app_commands.Choice(name='spend xp', value='spend')], purchase=[app_commands.Choice(name=choice_label(f'+1 attribute ({XP_PER_ATTRIBUTE} xp)'), value='attribute'), app_commands.Choice(name=choice_label(f'+1 skill trait ({XP_PER_TRAIT} xp)'), value='trait'), app_commands.Choice(name=choice_label(f'role feature ({XP_PER_ROLE_FEATURE} xp)'), value='role_feature')], attribute=[app_commands.Choice(name='strength', value='str'), app_commands.Choice(name='dexterity', value='dex'), app_commands.Choice(name='constitution', value='con'), app_commands.Choice(name='intelligence', value='int'), app_commands.Choice(name='charisma', value='cha'), app_commands.Choice(name='wisdom', value='wis')], skill=[app_commands.Choice(name=label, value=key) for key, (_, label) in SKILLS.items()], role_feature=[app_commands.Choice(name=ROLE_LABELS[k], value=k) for k in ROLE_FEATURES])
    async def advance(self, interaction: discord.Interaction, action: str='view', purchase: str | None=None, attribute: str | None=None, skill: str | None=None, role_feature: str | None=None):
        if action == 'view':
            await self._xp(interaction)
        elif action == 'spend':
            if not purchase:
                await interaction.response.send_message(player_message('Pick a **purchase** type.'), ephemeral=reply_ephemeral())
                return
            await self._spendxp(interaction, purchase, attribute, skill, role_feature)

    async def _xp(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return
        account = db.get_account(interaction.user.id)
        xp_val = account['xp'] if 'xp' in account.keys() else 0
        embed = howlbert_embed('Experience', color=SUCCESS_COLOR)
        embed.description = f"You have **{xp_val} XP**.\n\n**{XP_PER_ATTRIBUTE} XP**: +1 attribute (max 10)\n**{XP_PER_TRAIT} XP**: +1 **earned trait** on a skill (max +{MAX_SKILL_RANK} from play; stacks with lore)\n**{XP_PER_ROLE_FEATURE} XP**; gain another role's feature (**requires admin approval**)"
        embed.set_footer(text='earn xp from quests, daily ration, den chat, and rp milestones. quests may grant skill trait experience.')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _spendxp(self, interaction: discord.Interaction, purchase: str, attribute: str | None=None, skill: str | None=None, role_feature: str | None=None):
        user = await self._require_user(interaction)
        if not user:
            return
        if purchase == 'attribute':
            if not attribute:
                await interaction.response.send_message(player_message('Pick an attribute.'), ephemeral=reply_ephemeral())
                return
            err = spend_xp_attribute(user, attribute)
            if err:
                embed = howlbert_embed('Cannot Spend', err, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            if not db.spend_xp(interaction.user.id, XP_PER_ATTRIBUTE):
                embed = howlbert_embed('Not Enough XP', f'Need {XP_PER_ATTRIBUTE} XP.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            key = f'attr_{attribute}'
            db.update_user(interaction.user.id, **{key: user[key] + 1})
            embed = howlbert_embed('Attribute Raised', f'**{attribute.upper()}** is now **{user[key] + 1}**.', color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            return
        if purchase == 'trait':
            if not skill:
                await interaction.response.send_message(player_message('Pick a skill.'), ephemeral=reply_ephemeral())
                return
            err = spend_xp_trait_bonus(user, skill)
            if err:
                embed = howlbert_embed('Cannot Spend', err, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            if not db.spend_xp(interaction.user.id, XP_PER_TRAIT):
                embed = howlbert_embed('Not Enough XP', f'Need {XP_PER_TRAIT} XP.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            from engine.character_traits import adjust_skill_trait_experience
            ok, msg = adjust_skill_trait_experience(user['id'], skill, 1)
            if not ok:
                embed = howlbert_embed('Cannot Spend', msg, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            embed = howlbert_embed('Trait Raised', msg, color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            return
        if purchase == 'role_feature':
            if not role_feature or role_feature not in ROLE_FEATURES:
                await interaction.response.send_message(player_message('Pick a role feature.'), ephemeral=reply_ephemeral())
                return
            existing_bonus = user['bonus_role_feature'] if 'bonus_role_feature' in user.keys() and user['bonus_role_feature'] else None
            if existing_bonus == role_feature:
                embed = howlbert_embed('Already Have Feature', f"**{user['wolf_name']}** already has the **{ROLE_LABELS[role_feature]}** bonus feature.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            if db.get_open_pending_for_wolf(user['id']):
                embed = howlbert_embed('Request Pending', 'A role-feature request is already awaiting admin approval for this wolf.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            account = db.get_account(interaction.user.id)
            xp_val = account['xp'] if 'xp' in account.keys() else 0
            if xp_val < XP_PER_ROLE_FEATURE:
                embed = howlbert_embed('Not Enough XP', f'Need {XP_PER_ROLE_FEATURE} XP.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            guild_id = interaction.guild.id if interaction.guild else 0
            db.create_pending_role_feature(guild_id=guild_id, discord_id=interaction.user.id, wolf_id=user['id'], wolf_name=user['wolf_name'], role_feature=role_feature)
            embed = howlbert_embed('Request Submitted', 'Request submitted; an **admin** must approve before XP is spent.', color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _other_wolf_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        active_id = db.get_active_wolf_id(interaction.user.id)
        choices = []
        for w in db.list_user_wolves(interaction.user.id):
            if w['id'] == active_id:
                continue
            if current and current.lower() not in w['wolf_name'].lower():
                continue
            choices.append(app_commands.Choice(name=choice_label(w['wolf_name']), value=w['wolf_name']))
        return choices[:25]

    async def _young_wolf_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        active_id = db.get_active_wolf_id(interaction.user.id)
        choices = []
        for w in db.list_user_wolves(interaction.user.id):
            if w['id'] == active_id:
                continue
            if w['age_months'] >= JUVENILE_MAX_MOONS:
                continue
            if current and current.lower() not in w['wolf_name'].lower():
                continue
            stage = stage_label(stage_for_age(w['age_months']))
            choices.append(app_commands.Choice(name=choice_label(f"{w['wolf_name']} ({stage})"), value=w['wolf_name']))
        return choices[:25]

    async def _nursing_pup_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        from engine.nursing import is_nursery_caretaker
        user = db.get_user(interaction.user.id)
        if not user:
            return []
        pups: list = []
        if user['birth_sex'] == 'female':
            pups.extend(db.get_nursing_pups_for_mother(user['id']))
        if is_nursery_caretaker(user) and user['pack_id']:
            pack_pups = db.get_pack_pups_needing_feed(user['pack_id'])
            seen = {p['id'] for p in pups}
            pups.extend((p for p in pack_pups if p['id'] not in seen))
        choices = []
        for pup in pups:
            if current and current.lower() not in pup['wolf_name'].lower():
                continue
            choices.append(app_commands.Choice(name=choice_label(f"{pup['wolf_name']} ({pup['age_months']} moons)"), value=pup['wolf_name']))
        return choices[:25]

    @app_commands.command(name='courtship', description='court, mate, or check pregnancy status.')
    @app_commands.describe(action='court, mate, pregnancy, or rival', target='defender wolf (another player)', target_wolf="specific wolf from that player's roster (rival)", partner='challenger wolf (another player; default: you)', partner_wolf="specific wolf from that player's roster (court/mate)", rival_mode='physical pin or vocal howl (rival)', favor_challenger='receptive female favors challenger (+2)', own_wolf='one of your other wolves (court/mate)', difficulty='social difficulty (court)', respond='accept or decline pending request (mate)')
    @app_commands.choices(action=[app_commands.Choice(name='court another wolf', value='court'), app_commands.Choice(name='mate with partner', value='mate'), app_commands.Choice(name='check pregnancy', value='pregnancy'), app_commands.Choice(name='rival challenge (mating access)', value='rival')], difficulty=[app_commands.Choice(name='auto: from standing', value='auto'), app_commands.Choice(name='friendly (dc 12)', value='friendly'), app_commands.Choice(name='neutral (dc 15)', value='neutral'), app_commands.Choice(name='hostile (dc 18)', value='hostile')], respond=[app_commands.Choice(name='accept pending request', value='accept'), app_commands.Choice(name='decline pending request', value='decline')], rival_mode=[app_commands.Choice(name='physical (strength + hunting)', value='physical'), app_commands.Choice(name='vocal (charisma + intimidation)', value='vocal')])
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, target_wolf=_target_wolf_autocomplete, partner_wolf=_partner_wolf_autocomplete)
    async def courtship(self, interaction: discord.Interaction, action: str, target: discord.Member | None=None, partner: discord.Member | None=None, own_wolf: str | None=None, difficulty: str='auto', respond: str | None=None, rival_mode: str='physical', favor_challenger: bool=False, target_wolf: str | None=None, partner_wolf: str | None=None):
        if action == 'court':
            await self._court(interaction, target, own_wolf, difficulty, target_wolf=target_wolf)
        elif action == 'mate':
            await self._mate(interaction, partner, own_wolf, respond, partner_wolf=partner_wolf)
        elif action == 'pregnancy':
            await self._pregnancy(interaction)
        elif action == 'rival':
            await self._rival_challenge(interaction, target, partner, own_wolf, rival_mode, favor_challenger, target_wolf=target_wolf, partner_wolf=partner_wolf)

    async def _court(self, interaction: discord.Interaction, target: discord.Member | None=None, own_wolf: str | None=None, difficulty: str='auto', *, target_wolf: str | None=None):
        user = await self._require_user(interaction)
        if not user:
            return
        block = young_wolf_block(user, action='court')
        if block:
            embed = howlbert_embed('Forbidden', block, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.mental_effects import social_activity_block
        mind_block = social_activity_block(user)
        if mind_block:
            embed = howlbert_embed('Mind Lost', mind_block, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        grief = int(user["grief_sunrises"]) if "grief_sunrises" in user.keys() else 0
        if grief > 0:
            embed = howlbert_embed(
                'Still Grieving',
                f'**{user["wolf_name"]}** is not ready to court again; the wound is too fresh. ({grief} sunrise{"s" if grief != 1 else ""} remain.)',
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        target_user, err = _resolve_partner_wolf(user, interaction, partner=target, own_wolf=own_wolf, partner_wolf=target_wolf)
        if err:
            if err == '__not_registered__':
                embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            else:
                embed = howlbert_embed('Invalid Target', err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        tblock = young_wolf_block(target_user, action='court')
        if tblock:
            embed = howlbert_embed('Forbidden', tblock, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        partner_mind = social_activity_block(target_user)
        if partner_mind:
            embed = howlbert_embed('Mind Lost', f"**{target_user['wolf_name']}**: {partner_mind}", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        u_orient = get_sexuality(user)
        allowed, reason = court_attraction_allowed(user, target_user)
        if not allowed:
            embed = howlbert_embed('No Attraction', reason or 'Incompatible attraction.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day = world['day_number'] if world else 1
        from engine.herb_buffs import courtship_blocked
        if courtship_blocked(user, day):
            embed = howlbert_embed('Song Blocked', f"**{user['wolf_name']}** was driven off in a vocal challenge and cannot court until the next sunrise.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if courtship_blocked(target_user, day):
            embed = howlbert_embed('Approach Blocked', f"**{target_user['wolf_name']}** lost a vocal rival challenge and cannot be courted until the next sunrise.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.energy import spend_energy
        _new_energy, _had_energy, court_penalty = spend_energy(user, 'court')
        guild_id = interaction.guild.id if interaction.guild else None
        effective, override_note = resolve_court_difficulty(user, target_user, guild_id, difficulty)
        mentor_note = _mentor_court_approval_note(user, target_user)
        if mentor_note and mentor_note.startswith('+'):
            effective = 'friendly' if effective in ('neutral', 'hostile') else effective
        from engine.herb_buffs import mating_fear_active
        fearful = mating_fear_active(user, day)
        result = run_court_check(user, effective, fearful=fearful)
        mood_line = apply_court_outcome(user, target_user, result, effective, guild_id=guild_id, day=day)
        if fearful:
            mood_line += '\n_a lingering **fear of mating** grips you; this courtship was rolled at disadvantage._'
        if court_penalty:
            mood_line += f'\n_{court_penalty}_'
        if result['success']:
            db.update_user(target_user['discord_id'], wolf_id=target_user['id'], receptive_day=day + 7)
        db.update_user(interaction.user.id, wolf_id=user['id'], last_court_day=day)
        db.record_court_attempt(user['id'], target_user['id'], day)
        lines = [f"1d20 ({result['die']}) + CHA = **{result['total']}** vs DC **{result['dc']}**"]
        if effective != difficulty or difficulty == 'auto':
            lines.append(f'_Difficulty: **{effective}**._')
        if override_note:
            lines.append(override_note)
        if mentor_note:
            lines.append(mentor_note)
        if result['outcome'] == 'critical_success':
            lines.append('**Critical success**: lasting attraction.')
        elif result['success']:
            if u_orient == 'asexual':
                lines.append('**Success**: a companion bond forms (platonic).')
            elif u_orient in BOND_FIRST_SEXUALITIES:
                lines.append('**Success**: trust deepens; a bond may follow before mateship.')
            else:
                lines.append('**Success**: target is receptive this season.')
        else:
            lines.append('**Failure**: awkwardness or offense.')
        if mood_line:
            lines.append(mood_line)
        from engine.healer_code import apply_medic_court_caught, healer_vow_reminder
        reminder = healer_vow_reminder(user) or healer_vow_reminder(target_user)
        if reminder:
            lines.append(reminder)
        if result['success']:
            scandal = apply_medic_court_caught(user, target_user)
            if scandal:
                lines.extend(scandal)
            from engine.bonds import apply_mentor_mate_caught
            mentor_caught = apply_mentor_mate_caught(user, target_user, guild_id=guild_id, day=day)
            if mentor_caught:
                lines.append(mentor_caught)
        protective_kin = _kin_protective_court_note(user, target_user)
        if protective_kin:
            lines.append(protective_kin)
        embed = howlbert_embed('Courtship', '\n'.join(lines), color=SUCCESS_COLOR if result['success'] else ERROR_COLOR)
        rel_note = court_relation_note(user, target_user, guild_id, effective)
        if rel_note:
            embed.set_footer(text=rel_note.strip('_'))
        else:
            embed.set_footer(text='/courtship action:mate · /checklist')
        await interaction.response.send_message(embed=embed)

    async def _rival_challenge(self, interaction: discord.Interaction, defender_target: discord.Member | None, challenger_partner: discord.Member | None, own_wolf: str | None, mode: str, favor_challenger: bool, *, target_wolf: str | None=None, partner_wolf: str | None=None):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        if not defender_target:
            embed = howlbert_embed('Need Defender', 'Pick a **target** player as the wolf defending mating access.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if target_wolf:
            defender = db.find_user_wolf(defender_target.id, target_wolf)
            if not defender:
                embed = howlbert_embed('Unknown Wolf', db.explain_wolf_not_found(defender_target.id, target_wolf, player_label=defender_target.display_name), color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        else:
            defender = db.get_user(defender_target.id)
        if not defender:
            embed = howlbert_embed('Not Registered', 'Defender is not on Howlbert.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if challenger_partner:
            if partner_wolf:
                challenger = db.find_user_wolf(challenger_partner.id, partner_wolf)
                if not challenger:
                    embed = howlbert_embed('Unknown Wolf', db.explain_wolf_not_found(challenger_partner.id, partner_wolf, player_label=challenger_partner.display_name), color=ERROR_COLOR)
                    await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                    return
            else:
                challenger = db.get_user(challenger_partner.id)
        elif own_wolf:
            wolves = db.list_user_wolves(interaction.user.id)
            challenger = next((w for w in wolves if w['wolf_name'] == own_wolf), None)
        else:
            challenger = user
        if not challenger:
            embed = howlbert_embed('Need Challenger', 'Pick a **partner** as challenger or register another wolf.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if challenger['id'] == defender['id']:
            embed = howlbert_embed('Same Wolf', 'Challenger and defender must be different wolves.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.rival_challenge import execute_rival_challenge
        winner, body = execute_rival_challenge(challenger, defender, mode='vocal' if mode == 'vocal' else 'physical', female_favors_challenger=favor_challenger, day=world['day_number'])
        footer = '_The receptive female is not forced to mate with the winner; she may still refuse._'
        embed = howlbert_embed(f'Rival Challenge: {winner} wins', body + '\n\n' + footer, color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)

    async def _mate(self, interaction: discord.Interaction, partner: discord.Member | None=None, own_wolf: str | None=None, respond: str | None=None, *, partner_wolf: str | None=None):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use in a server.'), ephemeral=reply_ephemeral())
            return
        grief = int(user["grief_sunrises"]) if "grief_sunrises" in user.keys() else 0
        if grief > 0 and respond not in ('accept', 'decline'):
            embed = howlbert_embed(
                'Still Grieving',
                f'**{user["wolf_name"]}** cannot take a new mate while still raw from loss. ({grief} sunrise{"s" if grief != 1 else ""} remain.)',
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if respond in ('accept', 'decline'):
            pending = db.get_pending_mate_for_partner(interaction.user.id)
            if not pending:
                embed = howlbert_embed('No Request', 'You have no pending mating request.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            if respond == 'decline':
                db.set_pending_mate_status(pending['id'], 'declined')
                await interaction.response.send_message(embed=howlbert_embed('Declined', 'You declined the mating request.', color=ERROR_COLOR))
                return
            initiator = db.get_user_by_id(pending['initiator_wolf_id'])
            partner_user = db.get_user_by_id(pending['partner_wolf_id'])
            if not initiator or not partner_user:
                db.set_pending_mate_status(pending['id'], 'expired')
                embed = howlbert_embed('Expired', 'One of the wolves no longer exists.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            from engine.attraction import kinship_blocked
            kin_block = kinship_blocked(initiator, partner_user)
            if kin_block:
                db.set_pending_mate_status(pending['id'], 'declined')
                embed = howlbert_embed('Forbidden', kin_block, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            world = db.get_world(interaction.guild.id)
            if partner_user['receptive_day'] < world['day_number']:
                embed = howlbert_embed('Not Receptive', 'You are no longer receptive; they must `/courtship action:court` you again.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            from engine.herb_buffs import courtship_blocked
            day = world['day_number']
            if courtship_blocked(initiator, day) or courtship_blocked(partner_user, day):
                blocked = initiator if courtship_blocked(initiator, day) else partner_user
                embed = howlbert_embed('Song Blocked', f"**{blocked['wolf_name']}** lost a vocal rival challenge and cannot mate until the next sunrise.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            ok, body, color, hard_fail = execute_mating(initiator, partner_user, day_number=world['day_number'], guild_id=interaction.guild.id)
            if ok and (not hard_fail):
                db.set_pending_mate_status(pending['id'], 'accepted')
            else:
                db.set_pending_mate_status(pending['id'], 'expired')
            title = mating_embed_title(body, hard_fail=hard_fail or not ok)
            if ok and not hard_fail:
                from engine.bonds import apply_mentor_mate_caught
                mentor_caught = apply_mentor_mate_caught(initiator, partner_user, guild_id=interaction.guild.id, day=world['day_number'])
                if mentor_caught:
                    body += f'\n\n{mentor_caught}'
            await interaction.response.send_message(embed=howlbert_embed(title, body, color=color))
            return
        block = young_wolf_block(user, action='mate')
        if block:
            embed = howlbert_embed('Forbidden', block, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.mental_effects import social_activity_block
        for wolf, label in ((user, 'You'),):
            mind_block = social_activity_block(wolf)
            if mind_block:
                embed = howlbert_embed('Mind Lost', mind_block, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        world = db.get_world(interaction.guild.id)
        partner_user, err = _resolve_partner_wolf(user, interaction, partner=partner, own_wolf=own_wolf, partner_wolf=partner_wolf)
        if err:
            if err == '__not_registered__':
                embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            else:
                embed = howlbert_embed('Invalid Partner', err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        pblock = young_wolf_block(partner_user, action='mate')
        if pblock:
            embed = howlbert_embed('Forbidden', pblock, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        partner_mind = social_activity_block(partner_user)
        if partner_mind:
            embed = howlbert_embed('Mind Lost', f"**{partner_user['wolf_name']}**: {partner_mind}", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.attraction import kinship_blocked
        kin_block = kinship_blocked(user, partner_user)
        if kin_block:
            embed = howlbert_embed('Forbidden', kin_block, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        same_owner = partner_user['discord_id'] == interaction.user.id
        if not same_owner and partner_user['receptive_day'] < world['day_number']:
            embed = howlbert_embed('Not Receptive', 'Court them first with `/courtship action:court`, or they may refuse.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.herb_buffs import courtship_blocked
        day = world['day_number']
        if courtship_blocked(user, day):
            embed = howlbert_embed('Song Blocked', f"**{user['wolf_name']}** was driven off in a vocal challenge and cannot mate until the next sunrise.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if courtship_blocked(partner_user, day):
            embed = howlbert_embed('Approach Blocked', f"**{partner_user['wolf_name']}** lost a vocal rival challenge and cannot mate until the next sunrise.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not same_owner:
            existing = db.get_pending_mate_for_pair(user['id'], partner_user['id'])
            if existing:
                embed = howlbert_embed('Request Pending', 'A mating request is already waiting for a response.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            pending_id = db.create_pending_mate(guild_id=interaction.guild.id, channel_id=interaction.channel.id, initiator_wolf_id=user['id'], partner_wolf_id=partner_user['id'], partner_discord_id=partner_user['discord_id'], day_number=world['day_number'])
            view = MateConsentView(pending_id)
            embed = howlbert_embed('Mating Request', f"**{user['wolf_name']}** wants to mate with **{partner_user['wolf_name']}**.\n<@{partner_user['discord_id']}>; accept or decline below, or use `/courtship action:mate respond:Accept pending request`.", color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed, view=view)
            msg = await interaction.original_response()
            db.set_pending_mate_message(pending_id, msg.id)
            await notify_consent_request(self.bot, partner_user['discord_id'], title='Mating Request', body=f"**{user['wolf_name']}** wants to mate with **{partner_user['wolf_name']}**.\nCheck the channel for **Accept/Decline** buttons, or use `/courtship action:mate respond:Accept pending request`.")
            return
        ok, body, color, hard_fail = execute_mating(user, partner_user, day_number=world['day_number'], guild_id=interaction.guild.id)
        title = mating_embed_title(body, hard_fail=hard_fail or not ok)
        if ok and not hard_fail:
            from engine.bonds import apply_mentor_mate_caught
            mentor_caught = apply_mentor_mate_caught(user, partner_user, guild_id=interaction.guild.id, day=world['day_number'])
            if mentor_caught:
                body += f'\n\n{mentor_caught}'
        await interaction.response.send_message(embed=howlbert_embed(title, body, color=color))

    async def _pregnancy(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return
        if not user['is_pregnant']:
            subject = None
            mate = db.get_bonded_mate(user)
            if mate and mate['is_pregnant']:
                subject = mate
                role_note = f"You are the expectant mate of **{mate['wolf_name']}**."
            else:
                as_father = db.get_pregnancy_where_partner(user['id'])
                if as_father:
                    subject = as_father
                    role_note = f"Your mate **{as_father['wolf_name']}** is expecting."
            if not subject:
                embed = howlbert_embed('Not Pregnant', 'No active pregnancy on you or your mate.')
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        else:
            subject = user
            role_note = None
        day = 0
        if interaction.guild:
            day = db.get_world(interaction.guild.id)['day_number']
        elapsed = max(0, day - subject['pregnancy_start_day'])
        remaining = max(0, GESTATION_DAYS - elapsed)
        mate = db.get_mate_wolf(subject)
        mate_name = mate['wolf_name'] if mate else 'Unknown'
        embed = howlbert_embed('Pregnancy', color=SUCCESS_COLOR)
        if role_note:
            embed.description = role_note
        embed.add_field(name='Expectant', value=subject['wolf_name'], inline=True)
        embed.add_field(name='Days elapsed', value=str(elapsed), inline=True)
        embed.add_field(name='Days until birth', value=str(remaining), inline=True)
        embed.add_field(name='Mate', value=mate_name, inline=True)
        from engine.pregnancy import in_late_pregnancy, LATE_PREGNANCY_SUNRISES
        if subject['id'] == user['id'] and in_late_pregnancy(subject, day):
            embed.add_field(name='Den rest', value=f'Final **{LATE_PREGNANCY_SUNRISES}** sunrises; strenuous work blocked (hunt, patrol, explore, combat, fishing, …).', inline=False)
        if remaining == 0:
            who = 'she' if subject['id'] == user['id'] else subject['wolf_name']
            embed.set_footer(text=f'ready for `/pupcare action:birth names:…`; {who} can name the litter.')
        elif mate and (not db.row_val(mate, 'pack_id')) and (subject['id'] == user['id']):
            embed.set_footer(text=f"breeding mate {mate['wolf_name']} walks outside the den; pups stay with your pack.")
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @app_commands.command(name='pupcare', description='list pups, birth a litter, save a dying pup, train a pup, or adopt.')
    @app_commands.describe(action='list, birth, feed, save, train, or adopt', names='comma-separated pup names (birth)', name='pup name (save, feed, or train one pup)', partner='bonded mate (adopt)', partner_wolf="specific wolf from partner's roster", own_wolf='your bonded mate wolf (adopt) or trainer wolf (train)', youth="another player's wolf to adopt", youth_wolf="specific wolf from that player's roster to adopt", own_youth='your pup or juvenile to adopt', respond='accept or decline adoption request', attribute='attribute to train (train)', hide_father="don't reveal the sire publicly; only you and the father's player will know (birth)")
    @app_commands.choices(action=[app_commands.Choice(name='list your pups', value='list'), app_commands.Choice(name='birth litter', value='birth'), app_commands.Choice(name='feed / nurse pups', value='feed'), app_commands.Choice(name='save dying pup', value='save'), app_commands.Choice(name='train a pup', value='train'), app_commands.Choice(name='adopt youth', value='adopt')], respond=[app_commands.Choice(name='accept pending adoption', value='accept'), app_commands.Choice(name='decline pending adoption', value='decline')], attribute=[app_commands.Choice(name='strength', value='str'), app_commands.Choice(name='dexterity', value='dex'), app_commands.Choice(name='constitution', value='con'), app_commands.Choice(name='intelligence', value='int'), app_commands.Choice(name='charisma', value='cha'), app_commands.Choice(name='wisdom', value='wis')])
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, own_youth=_young_wolf_autocomplete, name=_nursing_pup_autocomplete, partner_wolf=_partner_wolf_autocomplete, youth_wolf=_youth_wolf_autocomplete)
    async def pupcare(self, interaction: discord.Interaction, action: str, names: str | None=None, name: str | None=None, partner: discord.Member | None=None, partner_wolf: str | None=None, own_wolf: str | None=None, youth: discord.Member | None=None, youth_wolf: str | None=None, own_youth: str | None=None, respond: str | None=None, attribute: str | None=None, hide_father: bool=False):
        if action == 'list':
            await self._pups(interaction)
        elif action == 'birth':
            if not names:
                await interaction.response.send_message(player_message('Provide **names** for the litter.'), ephemeral=reply_ephemeral())
                return
            await self._birth(interaction, names, hide_father=hide_father)
        elif action == 'feed':
            await self._feedpups(interaction, name, own_wolf)
        elif action == 'save':
            if not name:
                await interaction.response.send_message(player_message('Provide the pup **name**.'), ephemeral=reply_ephemeral())
                return
            await self._savepup(interaction, name)
        elif action == 'train':
            if not name or not attribute:
                await interaction.response.send_message(player_message('Provide the pup **name** and the **attribute** to train.'), ephemeral=reply_ephemeral())
                return
            await self._trainpup(interaction, name, attribute, own_wolf)
        elif action == 'adopt':
            await self._adoptpup(interaction, partner, own_wolf, youth, own_youth, respond, youth_wolf=youth_wolf, partner_wolf=partner_wolf)

    async def _birth(self, interaction: discord.Interaction, names: str, *, hide_father: bool=False):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use in a server.'), ephemeral=reply_ephemeral())
            return
        if not user['is_pregnant']:
            embed = howlbert_embed('Not Pregnant', 'This wolf is not expecting pups.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        elapsed = world['day_number'] - user['pregnancy_start_day']
        if elapsed < GESTATION_DAYS:
            embed = howlbert_embed('Too Early', f'**{GESTATION_DAYS - elapsed}** days of gestation remain.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        father = db.get_mate_wolf(user)
        result = birth_check(user)
        from engine.herb_buffs import consume_birth_save_advantage
        if result.get('used_birth_advantage'):
            db.update_user(interaction.user.id, wolf_id=user['id'], **consume_birth_save_advantage(user))
        if result.get('extra_pup_from_borage'):
            db.update_user(interaction.user.id, wolf_id=user['id'], extra_pup_milk=0)
        pups_born = result['litter_size']
        if result['outcome'] == 'critical_failure':
            pups_born = max(1, pups_born - 1)
        parsed_names, name_err = parse_litter_names(names, pups_born)
        if name_err:
            embed = howlbert_embed('Invalid Names', name_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        for pup_name in parsed_names:
            if db.wolf_name_taken(pup_name) or db.pending_pup_name_taken(pup_name):
                embed = howlbert_embed('Name Taken', f'The name **{pup_name}** is already taken or reserved for neonatal care.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        born_names: list[str] = []
        born_pup_ids: list[int] = []
        born_pup_stats: list[tuple[int, str, dict]] = []
        stillborn_lines: list[str] = []
        mutation_lines: list[str] = []
        inheritance_lines: list[str] = []
        from config import RUNT_LITTER_MIN_SIZE
        father_id = father['id'] if father else None
        from engine.genetics import GENETIC_CONDITIONS, encode_genetic_conditions, roll_pup_genetic_conditions
        from engine.stillborn import format_stillborn_save_hint, save_pending_stillborn
        from engine.attraction import kinship_taboo
        # parents who share close blood raise recessive expression, mutation load,
        # inbreeding depression, and stillbirth risk for every pup in the litter.
        is_kin = bool(father) and kinship_taboo(user, father) is not None
        world = db.get_world(interaction.guild.id)
        born_day = world['day_number']
        for pup_name in parsed_names:
            conditions, carriers, lethal = roll_pup_genetic_conditions(user, father, birth_outcome=result['outcome'], kin=is_kin)
            if lethal:
                stats = generate_pup_stats(user, father) if father else generate_pup_stats(user, user)
                save_pending_stillborn(discord_id=user['discord_id'], mother_wolf_id=user['id'], pup_name=pup_name, genetic_conditions=conditions, stats=stats, father_wolf_id=father_id, pack_id=user['pack_id'], great_pack=user['great_pack'], birth_sex=random_birth_sex(), born_day=born_day)
                stillborn_lines.append(format_stillborn_save_hint(pup_name, conditions))
                continue
            stats = generate_pup_stats(user, father) if father else generate_pup_stats(user, user)
            pup_id = db.register_born_wolf(discord_id=user['discord_id'], wolf_name=pup_name, mother_wolf_id=user['id'], father_wolf_id=father_id, stats=stats, pack_id=user['pack_id'], great_pack=user['great_pack'], birth_sex=random_birth_sex(), genetic_conditions=encode_genetic_conditions(conditions), father_hidden=hide_father)
            from engine.family import inherit_pup_appearance
            appearance_fields = inherit_pup_appearance(user, father)
            if appearance_fields:
                db.set_wolf_identity(pup_id, **appearance_fields)
            if carriers:
                db.update_user(user['discord_id'], wolf_id=pup_id, genetic_carriers=encode_genetic_conditions(carriers))
            born_pup_ids.append(pup_id)
            born_names.append(pup_name)
            if conditions:
                muts = ', '.join((GENETIC_CONDITIONS[c]['name'] for c in conditions))
                mutation_lines.append(f'**{pup_name}**: {muts}')
            if carriers:
                carrier_names = ', '.join((GENETIC_CONDITIONS[c]['name'] for c in carriers))
                inheritance_lines.append(f'**{pup_name}** silently carries {carrier_names} (unexpressed; can pass to pups).')
            from engine.family import inherit_parent_skill_trait

            inherit_note = inherit_parent_skill_trait(pup_id, user, father)
            if inherit_note:
                inheritance_lines.append(f'**{pup_name}** {inherit_note}')
            born_pup_stats.append((pup_id, pup_name, stats))

        if len(born_pup_ids) >= RUNT_LITTER_MIN_SIZE:
            from engine.family import mark_runt_pup

            runt_id, runt_name, runt_stats = min(
                born_pup_stats, key=lambda entry: sum(entry[2].values())
            )
            weakened = mark_runt_pup(runt_id, runt_stats)
            inheritance_lines.append(
                f'**{runt_name}** is the runt of the litter; its **{weakened}** is permanently weaker.'
            )
        if len(born_pup_ids) > 1:
            import random as _random

            for i, pup_a in enumerate(born_pup_ids):
                for pup_b in born_pup_ids[i + 1:]:
                    db.set_bond(pup_a, pup_b, "kin", strength=_random.randint(35, 65), note="littermates", day=born_day)
        if not born_names and stillborn_lines:
            db.clear_pregnancy(user['id'])
            body = f"Birth check: **{result['total']}** vs DC 12; the litter did not survive.\n" + '\n'.join(stillborn_lines) + '\n\nBuy **Vitality Salve** from `/bones action:shop` and use **`/pupcare action:save`** before the next `/rollover`.'
            await interaction.response.send_message(embed=howlbert_embed('Birth', body, color=ERROR_COLOR))
            return
        db.clear_pregnancy(user['id'])
        if user['pack_id']:
            db.adjust_pack_unity(user['pack_id'], 1)
        from engine.disease_contract import schedule_milk_fever_risk
        world = db.get_world(interaction.guild.id)
        user = db.get_user(interaction.user.id)
        milk_note = schedule_milk_fever_risk(user, day=world['day_number'], difficult_birth=not result['success'], litter_size=len(born_names))
        name_line = ', '.join((f'**{n}**' for n in born_names))
        father_line = ''
        if father:
            father_line = f"\n**{father['wolf_name']}** and **{user['wolf_name']}** named the litter."
            if not db.row_val(father, 'pack_id'):
                father_line += f"\n_**{father['wolf_name']}** is a lone wolf; pups inherit **{user['wolf_name']}**'s den unless you `/setfaction` or adopt them elsewhere._"
            elif user['pack_id'] and int(father['pack_id']) != int(user['pack_id']):
                father_line += f"\n_**{father['wolf_name']}** is from another Great Pack; pups start in **{user['wolf_name']}**'s den._"
        body = f"Birth check: **{result['total']}** vs DC 12; **{len(born_names)}** pup(s) born: {name_line}.{father_line}\nBorn pups use **extra slots** (not your 3 `/register` slots). Use `/switchwolf` to play them."
        if hide_father and father:
            body += "\n\n_the sire's name stays off the litter's public family tree; only you and **" + father['wolf_name'] + "**'s player will see it._"
        if mutation_lines:
            body += '\n\n**Mutations:**\n' + '\n'.join(mutation_lines)
        if inheritance_lines:
            body += '\n\n**Inherited:**\n' + '\n'.join(inheritance_lines)
        if stillborn_lines:
            body += '\n\n**Dying pups:**\n' + '\n'.join(stillborn_lines)
        if not result['success']:
            body += '\nDifficult birth; mother gains 1 exhaustion.'
            db.set_user_conditions(interaction.user.id, exhaustion=min(6, user['exhaustion'] + 1))
        if milk_note:
            body += f'\n\n{milk_note}'
        body += '\n\nNurse the litter each sunrise with **`/pupcare action:feed`** (mothers) or ask a **Caretaker** to mash-feed pack pups.'
        if not user['pack_id']:
            from engine.nursing import lone_nursing_note
            body += lone_nursing_note(user)
        from engine.healer_code import apply_medic_birth_scandal, healer_vow_reminder
        reminder = healer_vow_reminder(user)
        if father:
            r2 = healer_vow_reminder(father)
            if r2:
                reminder = reminder or r2
        if reminder:
            body += f'\n\n{reminder}'
        scandal = apply_medic_birth_scandal(user, father, born_pup_ids)
        if scandal:
            body += '\n\n' + '\n\n'.join(scandal)
            await interaction.response.send_message(embed=howlbert_embed('Birth; Healer Scandal', body, color=ERROR_COLOR))
            return
        embed = howlbert_embed('Birth', body, color=SUCCESS_COLOR)
        embed.set_footer(text='/pupcare action:feed · /pupcare action:list · /checklist')
        await interaction.response.send_message(embed=embed)

    async def _feedpups(self, interaction: discord.Interaction, pup_name: str | None, own_wolf: str | None):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use in a server.'), ephemeral=reply_ephemeral())
            return
        feeder = user
        if own_wolf:
            alt = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not alt:
                embed = howlbert_embed('Unknown Wolf', f'You have no wolf named **{own_wolf.strip()}**.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            feeder = alt
        world = db.get_world(interaction.guild.id)
        from engine.nursing import execute_nursing
        ok, msg = execute_nursing(feeder, day_number=world['day_number'], pack_id=feeder['pack_id'], pup_name=pup_name)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = 'Nursing' if ok else 'Cannot Feed'
        embed = howlbert_embed(title, msg, color=color)
        embed.set_footer(text='/pupcare action:list · each pup needs milk once a sunrise · /checklist')
        await interaction.response.send_message(embed=embed)

    async def _savepup(self, interaction: discord.Interaction, name: str):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use in a server.'), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        from engine.stillborn import try_save_stillborn_pup
        ok, msg = try_save_stillborn_pup(interaction.user.id, name, current_day=world['day_number'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Save Pup', msg, color=color))

    async def _trainpup(self, interaction: discord.Interaction, name: str, attribute: str, own_wolf: str | None):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use in a server.'), ephemeral=reply_ephemeral())
            return
        trainer = user
        if own_wolf:
            alt = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not alt:
                embed = howlbert_embed('Unknown Wolf', f'You have no wolf named **{own_wolf.strip()}**.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            trainer = alt
        children = db.get_lineage_children_for_discord(interaction.user.id)
        pup = next((c for c in children if c['wolf_name'].lower() == name.strip().lower()), None)
        if not pup:
            embed = howlbert_embed('Unknown Pup', f'No pup or juvenile named **{name}** in your family.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        from engine.pup_training import train_pup
        ok, msg = train_pup(trainer, pup, attribute=attribute, day=world['day_number'])
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Train Pup', msg, color=color)
        embed.set_footer(text='unlimited; each lesson spends energy · pups and juveniles only')
        await interaction.response.send_message(embed=embed)

    async def _pups(self, interaction: discord.Interaction):
        user = await self._require_user(interaction)
        if not user:
            return
        wolf_ids = {w['id'] for w in db.list_user_wolves(interaction.user.id)}
        children = db.get_lineage_children_for_discord(interaction.user.id)
        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day_number = world['day_number'] if world else None
        if not children:
            embed = howlbert_embed('No Pups', 'You have no biological or adopted young yet.')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.nursing import pup_needs_milk_today
        lines = [db.format_pup_lineage_entry(child, wolf_ids, viewer_discord_id=interaction.user.id, day_number=day_number) for child in children]
        footer = ''
        if day_number is not None and any((pup_needs_milk_today(c, day_number) for c in children)):
            footer = '\n\nPups marked **needs milk** want **`/pupcare action:feed`** this sunrise.'
        if not user['pack_id'] and day_number is not None and any((pup_needs_milk_today(c, day_number) for c in children)):
            from engine.nursing import lone_nursing_note
            footer += lone_nursing_note(user)
        embed = howlbert_embed('Your Pups', '\n'.join(lines) + footer)
        embed.set_footer(text='/pupcare action:feed · /switchwolf · /checklist')
        await interaction.response.send_message(embed=embed)

    async def _adoptpup(self, interaction: discord.Interaction, partner: discord.Member | None=None, own_wolf: str | None=None, youth: discord.Member | None=None, own_youth: str | None=None, respond: str | None=None, *, youth_wolf: str | None=None, partner_wolf: str | None=None):
        user = await self._require_user(interaction)
        if not user:
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use in a server.'), ephemeral=reply_ephemeral())
            return
        if respond in ('accept', 'decline'):
            pending = db.get_pending_adoption_for_owner(interaction.user.id)
            if not pending:
                embed = howlbert_embed('No Request', 'You have no pending adoption request.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            if respond == 'decline':
                ok, msg = decline_pending_adoption(pending['id'])
            else:
                ok, msg = accept_pending_adoption(pending['id'])
            color = SUCCESS_COLOR if ok and respond == 'accept' else ERROR_COLOR
            title = 'Adopted' if ok and respond == 'accept' else 'Declined' if ok else 'Failed'
            await interaction.response.send_message(embed=howlbert_embed(title, msg, color=color))
            return
        partner_user, err = _resolve_partner_wolf(user, interaction, partner=partner, own_wolf=own_wolf, partner_wolf=partner_wolf)
        if err:
            if err == '__not_registered__':
                embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            else:
                embed = howlbert_embed('Invalid Partner', err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not are_bonded_mates(user, partner_user):
            embed = howlbert_embed('Not Bonded', 'You must be **mutually bonded** mates (`/mate` after courtship).', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        from engine.energy import spend_energy
        adoptee, adoptee_err = _resolve_adoptee(user, interaction, youth=youth, own_youth=own_youth, youth_wolf=youth_wolf)
        if adoptee_err:
            if adoptee_err == '__not_registered__':
                embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            else:
                embed = howlbert_embed('Invalid Youth', adoptee_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        adopt_err = adoption_eligibility_error(adoptee, user, partner_user)
        if adopt_err:
            embed = howlbert_embed('Cannot Adopt', adopt_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        _new_energy, user_had_energy, user_adopt_penalty = spend_energy(user, 'adopt')
        _new_energy2, partner_had_energy, partner_adopt_penalty = spend_energy(partner_user, 'adopt')
        running_empty = not user_had_energy or not partner_had_energy
        check = courtship_check(user, 'friendly', fearful=running_empty)
        adopt_penalty = ' '.join(p for p in (user_adopt_penalty, partner_adopt_penalty) if p)
        if not check['success']:
            tired = ' _(running on empty; bonding check at disadvantage)_' if running_empty else ''
            embed = howlbert_embed('Adoption Denied', f"Bonding check: **{check['total']}** vs DC **{check['dc']}**; the den is not ready.{tired}", color=ERROR_COLOR)
            if adopt_penalty:
                embed.set_footer(text=f'{adopt_penalty} · /help topic:skills')
            await interaction.response.send_message(embed=embed)
            return
        needs_consent = adoptee['discord_id'] not in (interaction.user.id, partner_user['discord_id'])
        if not needs_consent:
            db.set_adoptive_parents(adoptee['id'], user['id'], partner_user['id'])
            db.update_user(interaction.user.id, wolf_id=user['id'], last_adopt_day=day)
            db.update_user(partner_user['discord_id'], wolf_id=partner_user['id'], last_adopt_day=day)
            if user['pack_id'] and user['pack_id'] == partner_user['pack_id']:
                db.adjust_pack_unity(user['pack_id'], 1)
            stage = stage_label(stage_for_age(adoptee['age_months']))
            body = f"**{adoptee['wolf_name']}** ({stage}) joins **{user['wolf_name']}** and **{partner_user['wolf_name']}**'s den."
            if adopt_penalty:
                body += f'\n_{adopt_penalty}_'
            from engine.healer_code import apply_medic_adopt_scandal, healer_vow_reminder
            for w in (user, partner_user):
                rem = healer_vow_reminder(w)
                if rem:
                    body += f'\n\n{rem}'
            scandal = apply_medic_adopt_scandal(user, partner_user, adoptee)
            if scandal:
                body += '\n\n' + '\n\n'.join(scandal)
                embed = howlbert_embed('Adoption; Healer Scandal', body, color=ERROR_COLOR)
            else:
                embed = howlbert_embed('Adopted', body, color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            return
        if db.get_pending_adoption_for_adopter_pair(user['id'], partner_user['id']):
            embed = howlbert_embed('Request Pending', "You already have an adoption awaiting the youth's answer.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        pending_id = db.create_pending_adoption(guild_id=interaction.guild.id, channel_id=interaction.channel.id, adopter_1_wolf_id=user['id'], adopter_2_wolf_id=partner_user['id'], youth_wolf_id=adoptee['id'], youth_owner_discord_id=adoptee['discord_id'], day_number=day)
        view = AdoptionConsentView(pending_id)
        stage = stage_label(stage_for_age(adoptee['age_months']))
        embed = howlbert_embed('Adoption Request', f"**{user['wolf_name']}** and **{partner_user['wolf_name']}** want to adopt **{adoptee['wolf_name']}** ({stage}).\n<@{adoptee['discord_id']}>; accept or decline below, or `/pupcare action:adopt respond:Accept pending adoption`.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        db.set_pending_adoption_message(pending_id, msg.id)
        await notify_consent_request(self.bot, adoptee['discord_id'], title='Adoption Request', body=f"**{user['wolf_name']}** and **{partner_user['wolf_name']}** want to adopt **{adoptee['wolf_name']}** ({stage}).\nCheck the channel for **Accept/Decline** buttons, or use `/pupcare action:adopt respond:Accept pending adoption`.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Life(bot))