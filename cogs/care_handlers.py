"""shared care command handlers (herbs, medic treatment, rites)."""

from __future__ import annotations

import json
import random
import discord
import database as db
from engine.role_privileges import treat_limit_reached
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message


async def dryall(interaction: discord.Interaction):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message(
            player_message('use `/register` in a server.'),
            ephemeral=reply_ephemeral()
        )
        return
    from engine.herb_preparation import dry_all_fresh_herbs
    world = db.get_world(interaction.guild.id)
    ok, msg = dry_all_fresh_herbs(
        user,
        day=world['day_number'],
        guild_id=interaction.guild.id,
        at_den=bool(user['pack_id'])
    )
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(
        embed=howlbert_embed('dry all herbs', msg, color=color)
    )


async def prepare_herb_inventory(interaction: discord.Interaction, item_key: str, prep_method: str):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message(
            player_message('use `/register` in a server.'),
            ephemeral=reply_ephemeral()
        )
        return
    from engine.herb_preparation import prepare_herb_from_inventory
    world = db.get_world(interaction.guild.id)
    ok, msg = prepare_herb_from_inventory(
        user,
        item_key,
        prep_method,
        day=world['day_number'],
        guild_id=interaction.guild.id,
        at_den=bool(user['pack_id'])
    )
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(
        embed=howlbert_embed('herb preparation', msg, color=color)
    )


async def treat(
    interaction: discord.Interaction,
    herb: str,
    patient: discord.Member | None = None,
    own_wolf: str | None = None,
    patient_wolf: str | None = None
):
    if patient and own_wolf:
        embed = howlbert_embed('pick one', 'choose another **patient** or your **own_wolf**; not both.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if own_wolf:
        user = db.find_user_wolf(interaction.user.id, own_wolf)
        if not user:
            embed = howlbert_embed('unknown wolf', f'no wolf named **{own_wolf}** on your account.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
    else:
        user = db.get_user(interaction.user.id)

    if not user:
        embed = howlbert_embed('not registered', 'use `/register` first.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    from engine.herb_storage import parse_herb_stack_id
    stack_id = parse_herb_stack_id(herb)
    if stack_id is not None:
        embed = howlbert_embed(
            'herb bag removed',
            'foraged herbs live in `/bones action:inventory`. use **`/medic action:treat herb:herb_yarrow`** (inventory key).',
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    item = db.get_item_by_key(herb.strip().lower())
    if not item or (not item['key'].startswith('herb_') and item['key'] != 'stick'):
        embed = howlbert_embed(
            'unknown herb',
            'use an herb from `/bones action:inventory` (keys like `herb_yarrow` or `stick`).',
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    qty = db.get_inventory_quantity(interaction.user.id, item['id'])
    # a fully-prepared herb (tea/poultice/ointment) can leave the raw copy at
    # 0 once /herbs action:prepare consumes it; the qty<1 case is decided
    # below, after we know whether a matching prepared stack can cover it
    # instead (see prepared_stack_source).
    prepared_stack_source: str | None = None
    prepared_stack_row = None

    if treat_limit_reached(user):
        embed = howlbert_embed(
            'limit reached',
            'you can only **`/medic action:treat`** with herbs **3 times per sunrise**. **medics** and **medic apprentices** have no cap; wait for the next `/rollover`.',
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    from herbs import HERBS
    from engine.conditions import medicine_check, parse_injuries, treat_with_herb, herb_special_effect
    from engine.herb_properties import herb_form_rule
    from engine.rolls import roll_d20
    from engine.character import attr_modifier
    from engine.diseases import parse_disease
    from engine.herb_admin import DEFAULT_METHOD_REQS

    herb_key = 'stick' if item['key'] == 'stick' else item['key'].replace('herb_', '', 1)
    meta = HERBS.get(herb_key, {'cures': (), 'effect': item['description']})
    special = herb_special_effect(herb_key, user, inventory_qty=qty)
    world = db.get_world(interaction.guild.id) if interaction.guild else None
    treat_day = world['day_number'] if world else int(user['last_rest_day'] or 0)

    # ---- fresh toxicity check ----
    rule = herb_form_rule(herb_key)
    if rule.toxic_if_fresh:
        # inventory herbs are normally dried, but we keep this as a safety net
        from engine.character import parse_proficiencies
        profs = parse_proficiencies(user['skill_proficiencies'])
        survival_bonus = attr_modifier(int(user['attr_wis'] if 'attr_wis' in user.keys() else 3))
        if 'survival' in profs or 'herblore' in profs:
            survival_bonus += 2
        die = roll_d20()
        total = die + survival_bonus
        if total < rule.toxic_dc:
            dmg = random.randint(rule.toxic_damage[0], rule.toxic_damage[1])
            new_hp = max(0, int(user['hp']) - dmg)
            db.set_user_conditions(user['discord_id'], wolf_id=user['id'], hp=new_hp)
            embed = howlbert_embed(
                'toxic herb!',
                f"**{item['name']}** is toxic fresh! survival check failed ({total} vs dc {rule.toxic_dc}). you lose **{dmg} hp**. {rule.notes}",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed)
            return

    # ---- determine target (self or patient) ----
    treat_subject = user
    treat_patient = None

    if patient:
        from engine.role_features import has_any_role, is_full_medic
        if not (is_full_medic(user) or has_any_role(user, 'medic_apprentice')):
            embed = howlbert_embed(
                'medic only',
                'only **medics** and **medic apprentices** may treat a **patient** from inventory herbs.',
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        if patient_wolf:
            treat_patient = db.find_user_wolf(patient.id, patient_wolf)
            if not treat_patient:
                embed = howlbert_embed(
                    'unknown wolf',
                    db.explain_wolf_not_found(patient.id, patient_wolf, player_label=patient.display_name),
                    color=ERROR_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        else:
            treat_patient = db.get_user(patient.id)

        if not treat_patient:
            embed = howlbert_embed('not registered', 'patient is not on howlbert.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        from engine.medical_access import can_medic_treat_cross_pack
        p_cond = treat_patient['condition'] if 'condition' in treat_patient.keys() else 'healthy'
        emergency = p_cond in ('dying',) or int(treat_patient['hp']) <= 0
        ok_cross, cross_msg = can_medic_treat_cross_pack(
            user,
            treat_patient,
            interaction.guild.id,
            emergency_stabilize=emergency
        )
        if not ok_cross:
            embed = howlbert_embed('cannot treat', cross_msg, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        treat_subject = treat_patient

    # ---- preparation requirement check ----
    target_disease_raw = treat_subject['disease'] if 'disease' in treat_subject.keys() else ''
    disease_key, stage = parse_disease(target_disease_raw)

    if disease_key:
        method_reqs = meta.get('method_requirements', {})
        required_method = method_reqs.get(disease_key)
        if required_method is None:
            required_method = DEFAULT_METHOD_REQS.get(disease_key)

        if required_method and required_method in ('poultice', 'tea', 'ointment'):
            # check if the user already has a prepared version in the den store or personal stacks
            has_prepared = False
            pack_id = int(user['pack_id']) if ('pack_id' in user.keys() and user['pack_id']) else None

            if pack_id:
                stacks = db.get_pack_herb_stacks(pack_id)
                for s in stacks:
                    if s['herb_key'] == herb_key and s['form'] == required_method:
                        has_prepared = True
                        prepared_stack_source = 'pack'
                        prepared_stack_row = s
                        break

            if not has_prepared:
                personal_stacks = db.get_herb_stacks(user['id'])
                for s in personal_stacks:
                    if s['herb_key'] == herb_key and s['form'] == required_method:
                        has_prepared = True
                        prepared_stack_source = 'personal'
                        prepared_stack_row = s
                        break

            if not has_prepared:
                embed = howlbert_embed(
                    'needs preparation',
                    f"**{item['name']}** must be prepared as **{required_method}** to treat **{disease_key}**.\n"
                    f"use `/herbs action:prepare herb:{item['key']} method:{required_method}` first.\n"
                    f"_(raw dried herbs are not strong enough for this illness.)_",
                    color=ERROR_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return

    # ---- special self-only checks ----
    if treat_patient and special in (
        'reduce_exhaustion', 'hunger_shield', 'march_shield',
        'jaw_meal_shield', 'purslane_thirst', 'sorrel_restore', 'cobnuts_energy'
    ):
        embed = howlbert_embed(
            'self use only',
            f"**{item['name']}** must be taken by the wolf themselves; not via patient treat.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    # ---- main treatment outcome ----
    outcome = treat_with_herb(treat_subject, herb_key, meta)

    # herb tolerance (same herb on same wound within 3 days -> dc+2)
    from engine.herb_buffs import herb_tolerance_dc_penalty as _htdc
    _early_injuries = parse_injuries(treat_subject['active_injuries'] if 'active_injuries' in treat_subject.keys() else None)
    _tol_injuries = [inj for inj in meta.get('cures', ()) if inj in _early_injuries]
    _tol_inj_key = _tol_injuries[0] if _tol_injuries else ''
    _tol_penalty = _htdc(treat_subject, herb_key, _tol_inj_key, day=treat_day) if _tol_inj_key else 0
    _tol_blocked = False

    if outcome == 'cured_injury' and _tol_penalty > 0:
        from engine.conditions import medicine_check as _mc
        _tol_check = _mc(treat_subject, dc=15 + _tol_penalty)
        if not _tol_check['success']:
            outcome = 'no_effect'
            _tol_blocked = True

    # special case early exits
    if special == 'reduce_exhaustion' and int(user['exhaustion']) <= 0:
        embed = howlbert_embed(
            'no effect',
            f"**{item['name']}**: you aren't carrying exhaustion to shed.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if special == 'hunger_shield' and int(user['hunger_exhaustion_skip'] if 'hunger_exhaustion_skip' in user.keys() else 0):
        embed = howlbert_embed(
            'already shielded',
            "fennel's hunger shield is already active for the next sunrise.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if special == 'march_shield' and int(user['march_exhaustion_skip'] if 'march_exhaustion_skip' in user.keys() else 0):
        embed = howlbert_embed(
            'already shielded',
            "burnet's march ward is already active for the next sunrise.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    # no effect -> medicine check
    if outcome == 'no_effect' and (not special) and (herb_key not in ('comfrey', 'cobwebs')):
        _check_dc = 15 + _tol_penalty
        if _tol_blocked:
            tol_note = f" (herb tolerance: same herb used on same wound recently; dc raised to {_check_dc})"
        else:
            tol_note = ''
        check = medicine_check(user, dc=_check_dc)
        from engine.herb_buffs import consume_herb_check_buffs
        consume_fields = consume_herb_check_buffs(user, skill_key='medicine')
        if consume_fields:
            db.update_user(interaction.user.id, wolf_id=user['id'], **consume_fields)
        if not check['success']:
            embed = howlbert_embed(
                'treatment failed',
                f"medicine check: {check['total']} vs dc {_check_dc}; no effect.{tol_note}",
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed)
            return

    # consume herb: from the raw dried copy normally, or from the prepared
    # stack itself when the raw copy was fully used up making it (see
    # prepared_stack_source above).
    use_qty = 3 if herb_key == 'ragweed' and special == 'reduce_exhaustion' else 1
    if qty >= use_qty:
        db.consume_item(interaction.user.id, item['id'], quantity=use_qty)
    elif prepared_stack_row is not None:
        if prepared_stack_source == 'pack':
            remaining = int(prepared_stack_row['quantity']) - 1
            if remaining > 0:
                db.update_pack_herb_stack(int(prepared_stack_row['id']), quantity=remaining)
            else:
                db.remove_pack_herb_stack(int(prepared_stack_row['id']))
        else:
            db.remove_herb_stack(int(prepared_stack_row['id']))
    else:
        embed = howlbert_embed(
            'not in inventory',
            f"you don't have enough **{item['name']}**.",
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    # ---- apply outcomes ----
    injuries = parse_injuries(treat_subject['active_injuries'] if 'active_injuries' in treat_subject.keys() else None)
    msg = ''
    subject_did = treat_subject['discord_id']
    subject_id = treat_subject['id']

    if special == 'reduce_exhaustion':
        old_ex = int(user['exhaustion'])
        new_ex = max(0, old_ex - 1)
        db.set_user_conditions(interaction.user.id, wolf_id=user['id'], exhaustion=new_ex)
        if new_ex < old_ex:
            from engine.energy import gain_energy_from_exhaustion_relief
            gain_energy_from_exhaustion_relief(user, old_ex - new_ex)
        msg = f"**{item['name']}**: exhaustion **{old_ex}** -> **{new_ex}**."

    elif special == 'hunger_shield':
        db.update_user(interaction.user.id, wolf_id=user['id'], hunger_exhaustion_skip=1)
        msg = "**{item['name']}**: you won't gain hunger exhaustion on the next sunrise (hydration still applies)."

    elif special == 'march_shield':
        db.update_user(interaction.user.id, wolf_id=user['id'], march_exhaustion_skip=1)
        msg = "**{item['name']}**: ignore the first **+1 exhaustion** from strain on the next sunrise."

    elif special == 'jaw_meal_shield':
        db.update_user(interaction.user.id, wolf_id=user['id'], jaw_meal_shield=1)
        msg = "**{item['name']}**: you can eat and drink without pain until the next sunrise."
        if outcome == 'cured_injury':
            for inj in meta.get('cures', ()):
                if inj in injuries:
                    injuries.remove(inj)
                    db.clear_injury_since(subject_id, inj)
            db.set_user_conditions(
                subject_did,
                wolf_id=subject_id,
                active_injuries=json.dumps(injuries),
                condition='healthy' if not injuries else treat_subject['condition']
            )
            msg += ' broken jaw treated.'

    elif special == 'purslane_thirst':
        thirst = db.adjust_thirst(user['id'], 12)
        msg = f"**{item['name']}**: chewed leaves restore hydration **{thirst}** (+12)."

    elif special == 'cobnuts_energy':
        from config import HUNGER_MAX
        new_hunger = min(HUNGER_MAX, int(user['hunger']) + 8)
        db.update_user(interaction.user.id, wolf_id=user['id'], hunger=new_hunger)
        msg = f"**{item['name']}**: sustained energy; hunger +8 ({new_hunger})."

    elif special == 'sorrel_restore':
        from config import HUNGER_MAX
        new_hunger = min(HUNGER_MAX, int(user['hunger']) + 18)
        had_gash = 'deep_gash' in injuries
        fields: dict = {'hunger': new_hunger}
        if had_gash:
            injuries.remove('deep_gash')
            db.clear_injury_since(user['id'], 'deep_gash')
            fields['active_injuries'] = json.dumps(injuries)
            if not injuries:
                fields['condition'] = 'healthy'
        db.update_user(interaction.user.id, wolf_id=user['id'], **fields)
        msg = f"**{item['name']}**: appetite returns (**hunger {new_hunger}**)."
        if had_gash:
            msg += ' bleeding staunched.'

    elif outcome == 'cured_disease':
        db.set_user_conditions(subject_did, wolf_id=subject_id, clear_disease=True, condition='healthy')
        who = 'their disease' if treat_patient else 'your disease'
        msg = f"**{meta.get('name', item['name'])}** cured {who}."

    elif outcome == 'cough_dose':
        from engine.herb_buffs import apply_disease_dose
        _cured, _dose_fields2, _dose_msg = apply_disease_dose(treat_subject, herb_key, day=treat_day)
        if _dose_fields2:
            db.update_user(subject_did, wolf_id=subject_id, **_dose_fields2)
        if _cured:
            db.set_user_conditions(subject_did, wolf_id=subject_id, clear_disease=True, condition='healthy')
        msg = f"**{item['name']}**: {_dose_msg}"

    elif outcome == 'rabies_ease':
        from engine.herb_buffs import grant_disease_save_advantage
        db.update_user(subject_did, wolf_id=subject_id, **grant_disease_save_advantage(treat_subject))
        who = treat_subject['wolf_name'] if treat_patient else 'you'
        msg = (
            f"**{item['name']}**: herbs slow early rabies for **{who}**; "
            "**advantage** on the next disease save (one sunrise). rabies is not cured."
        )

    elif outcome == 'cured_injury':
        from engine.character_traits import trait_clears_infection_on_heal
        for inj in meta.get('cures', ()):
            if inj in injuries:
                injuries.remove(inj)
                db.clear_injury_since(subject_id, inj)
        _infection_cleared = False
        if 'infected_wound' in injuries and trait_clears_infection_on_heal(user):
            injuries.remove('infected_wound')
            db.clear_injury_since(subject_id, 'infected_wound')
            _infection_cleared = True
        db.set_user_conditions(
            subject_did,
            wolf_id=subject_id,
            active_injuries=json.dumps(injuries),
            condition='healthy' if not injuries else treat_subject['condition']
        )
        who = f"**{treat_subject['wolf_name']}**'s injury" if treat_patient else 'your injury'
        msg = f"**{item['name']}** treated {who}."
        if _infection_cleared:
            msg += " a practiced touch clears the infection too."

    elif outcome == 'cured_genetic':
        from engine.genetics import genetic_keys_matching_cures, remove_genetic_keys
        matched = genetic_keys_matching_cures(treat_subject, meta.get('cures', ()))
        new_genetics = remove_genetic_keys(treat_subject, matched)
        db.update_user(subject_did, wolf_id=subject_id, genetic_conditions=new_genetics)
        names = ', '.join((m.replace('_', ' ').title() for m in matched))
        msg = f"**{item['name']}** eased or corrected **{names}**."

    elif outcome == 'symptom_ease':
        msg = f"**{item['name']}**: {meta.get('effect', 'symptoms ease for now')}."

    elif outcome == 'poison_herb':
        from engine.restricted_herbs import on_restricted_herb_treat
        penalty_note = on_restricted_herb_treat(user, herb_key)
        msg = f"**{item['name']}**: restricted poison; no safe cure applied. medic knowledge only."
        if penalty_note:
            msg += f"\n{penalty_note}"

    elif outcome == 'healed' or herb_key == 'comfrey':
        from engine.exhaustion_effects import effective_max_hp
        from engine.character_traits import trait_treat_heal_bonus
        cap = effective_max_hp(treat_subject)
        lo = max(1, cap // 5)
        hi = max(2, cap // 3)
        _heal_bonus = trait_treat_heal_bonus(user)
        if herb_key == 'comfrey':
            heal = random.randint(lo, hi) + _heal_bonus
            heal_label = 'comfrey (raw)'
            prep_hint = f' _prepare as poultice for up to {hi + 1} hp._'
        else:
            heal = random.randint(lo, hi) + _heal_bonus
            heal_label = meta.get('name', item['name'])
            prep_hint = ''
        new_hp = min(cap, int(treat_subject['hp']) + heal)
        db.set_user_conditions(subject_did, wolf_id=subject_id, hp=new_hp)
        who = treat_subject['wolf_name'] if treat_patient else 'you'
        msg = f'{heal_label} healed **{who}** **{heal} hp** (now **{new_hp}/{cap}**).{prep_hint}'

    elif outcome == 'stabilized':
        db.set_user_conditions(subject_did, wolf_id=subject_id, hp=1, condition='stable')
        who = treat_subject['wolf_name'] if treat_patient else 'you'
        if herb_key == 'cobwebs':
            msg = f'cobwebs stabilized **{who}** at 1 hp.'
        else:
            msg = f"**{item['name']}** stabilized **{who}** at 1 hp."

    # supplemental effects (buffs, etc.)
    from engine.herb_buffs import apply_supplemental_herb
    supplemental = apply_supplemental_herb(herb_key, treat_subject, day=treat_day, outcome=outcome)
    if supplemental:
        kind = supplemental['kind']
        sfields = supplemental.get('fields') or {}
        if kind == 'mercy':
            db.set_user_conditions(
                subject_did,
                wolf_id=subject_id,
                condition='dead',
                hp=0,
                death_cause=f"mercy ({item['name']})"
            )
            msg = f"**{item['name']}**: {supplemental['message']}"
        elif kind == 'stabilize' and outcome != 'stabilized':
            db.set_user_conditions(subject_did, wolf_id=subject_id, hp=1, condition='stable')
            msg = f"**{item['name']}**: {supplemental['message']}"
        else:
            if sfields:
                db.update_user(subject_did, wolf_id=subject_id, **sfields)
            extra = supplemental['message']
            if not msg:
                msg = f"**{item['name']}**; {extra}"
            elif kind in ('disease_save_buff', 'minor_relief', 'heal', 'symptom_relief'):
                msg += f' {extra}'

    if not msg:
        msg = f"applied **{item['name']}**: {meta.get('effect', 'minor relief')}."

    if treat_patient and treat_patient['id'] != user['id']:
        msg = f"**{user['wolf_name']}** treats **{treat_subject['wolf_name']}**:\n{msg}"

    # daily dose limits: record this dose first, then check whether it tipped the
    # wolf over the cap (a soft overdose that makes them sick, not a hard block).
    from engine.herb_dose_tracking import check_herb_overdose, record_herb_dose
    _dose_fields = record_herb_dose(treat_subject, herb_key, treat_day)
    if _dose_fields:
        db.update_user(subject_did, wolf_id=subject_id, **_dose_fields)
        treat_subject = db.get_user_by_id(subject_id) or treat_subject
    _od, _od_cond, _od_msg = check_herb_overdose(treat_subject, herb_key, treat_day)
    if _od:
        from engine.disease_contract import try_contract_disease as _tcd
        _od_fresh = db.get_user_by_id(subject_id) or treat_subject
        if _od_cond:
            _tcd(_od_fresh, _od_cond, chance=1.0)
        msg += f"\n\n**warning**: {_od_msg}"

    # chronic-disease care: if the herb didn't cure it, it may still ease the wolf
    # (support) and hold the sickness from worsening for a few sunrises (halt).
    if outcome != 'cured_disease':
        from engine.chronic_care import apply_chronic_herb_support, grant_chronic_halt
        _supp_fields, _supp_note = apply_chronic_herb_support(treat_subject, herb_key)
        if _supp_fields:
            db.update_user(subject_did, wolf_id=subject_id, **_supp_fields)
            treat_subject = db.get_user_by_id(subject_id) or treat_subject
        _halt_fields, _halt_note = grant_chronic_halt(treat_subject, herb_key, day=treat_day)
        if _halt_fields:
            db.update_user(subject_did, wolf_id=subject_id, **_halt_fields)
        _chronic_note = ' '.join(n for n in (_supp_note, _halt_note) if n)
        if _chronic_note:
            msg += f"\n\n_{_chronic_note}_"

    # record herb tolerance and bone_treated after a successful injury cure
    if outcome == 'cured_injury' and _tol_inj_key:
        from engine.herb_buffs import record_herb_tolerance as _rht
        _rht_fields = _rht(treat_subject, herb_key, _tol_inj_key, day=treat_day)
        if _rht_fields:
            db.update_user(subject_did, wolf_id=subject_id, **_rht_fields)

        _MALUNION_KEYS = {'fractured_rib', 'spinal_injury', 'sprained_leg', 'broken_jaw'}
        if _tol_inj_key in _MALUNION_KEYS:
            from engine.herb_buffs import record_bone_treated as _rbt
            _ts_fresh = db.get_user_by_id(subject_id) or treat_subject
            _rbt_fields = _rbt(_ts_fresh, _tol_inj_key)
            if _rbt_fields:
                db.update_user(subject_did, wolf_id=subject_id, **_rbt_fields)

    # increment treat counter
    db.update_user(
        interaction.user.id,
        wolf_id=user['id'],
        herb_treats_today=int(user['herb_treats_today'] if 'herb_treats_today' in user.keys() else 0) + 1
    )
    treats_after = int(user['herb_treats_today'] if 'herb_treats_today' in user.keys() else 0) + 1

    # healer's instinct: track lifetime successful cures
    if outcome in ('cured_injury', 'cured_disease', 'healed'):
        from engine.herb_buffs import get_buffs as _gi_gb, buffs_json as _gi_bj
        _gi_fresh = db.get_user(interaction.user.id) or user
        _gi_buffs = _gi_gb(_gi_fresh)
        _gi_count = int(_gi_buffs.get('heals_given_lifetime', 0)) + 1
        _gi_buffs['heals_given_lifetime'] = _gi_count
        db.update_user(interaction.user.id, wolf_id=user['id'], herb_buffs=_gi_bj(_gi_buffs))

        if _gi_count == 20:
            from engine.long_term_injuries import parse_long_term_injuries
            _gi_lti = parse_long_term_injuries(_gi_fresh.get('long_term_injuries', None))
            if 'healer_instinct' not in _gi_lti:
                _gi_lti.append('healer_instinct')
                import json as _json
                new_wis = (int(_gi_fresh.get('attr_wis', 3)) + 1)
                db.update_user(
                    interaction.user.id,
                    wolf_id=user['id'],
                    long_term_injuries=_json.dumps(_gi_lti),
                    attr_wis=new_wis
                )
                msg += "\n\n_20 successful treatments; **healer's instinct** unlocked: **+1 wis** permanently._"

    from engine.role_shift_bonus import apply_first_treat_bonus
    treat_shift = apply_first_treat_bonus(user, treats_after)
    if treat_shift:
        msg += f'\n\n_{treat_shift}_'

    # side effects, systemic benefits + addiction; external use (poultice) skips internal effects
    _se_form = 'poultice' if (rule.external_only or rule.requires_poultice) else 'tea'
    _se_fresh = db.get_user_by_id(subject_id) or treat_subject
    from engine.herb_side_effects import roll_herb_side_effects
    _side_note = roll_herb_side_effects(_se_fresh, herb_key, _se_form, day=treat_day)
    if _side_note:
        msg += _side_note
    from engine.herb_benefits import roll_herb_benefits
    _benefit_fresh = db.get_user_by_id(subject_id) or _se_fresh
    _benefit_note = roll_herb_benefits(_benefit_fresh, herb_key, _se_form, day=treat_day)
    if _benefit_note:
        msg += _benefit_note
    from engine.herb_addiction import register_herb_dose
    _addict_note = register_herb_dose(_se_fresh, herb_key, day=treat_day)
    if _addict_note:
        msg += _addict_note

    if interaction.guild:
        from engine.plot_blinking import try_plot_treat_extras
        _plot_note = try_plot_treat_extras(user, treat_subject, guild_id=interaction.guild.id, day=treat_day)
        if _plot_note:
            msg += f'\n\n{_plot_note}'

    embed = howlbert_embed('treatment', msg, color=SUCCESS_COLOR)
    embed.set_footer(text='care plan: `/vitals action:condition` · surgery: `/medic action:surgery`')

    gid = interaction.guild.id if interaction.guild else None
    db.increment_quest_progress(interaction.user.id, 'treat', guild_id=gid)
    await interaction.response.send_message(embed=embed)


async def field_dressing(interaction: discord.Interaction, own_wolf: str | None = None):
    """apply improvised field dressing to suppress deep_gash sunrise bleed (survival dc 14)."""
    if own_wolf:
        user = db.find_user_wolf(interaction.user.id, own_wolf)
        if not user:
            embed = howlbert_embed('unknown wolf', f'no wolf named **{own_wolf}** on your account.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
    else:
        user = db.get_user(interaction.user.id)

    if not user:
        embed = howlbert_embed('not registered', 'use `/register` first.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    from engine.injury_effects import has_injury
    if not has_injury(user, 'deep_gash'):
        embed = howlbert_embed('no wound', f"**{user['wolf_name']}** doesn't have a **deep gash** to dress.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    cobweb_item = db.get_item_by_key('herb_cobwebs')
    if not cobweb_item:
        embed = howlbert_embed('item error', 'cobwebs item not found.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    cobweb_qty = db.get_inventory_quantity(interaction.user.id, cobweb_item['id'])
    if cobweb_qty < 1:
        embed = howlbert_embed(
            'no cobwebs',
            'field dressing requires **1 cobweb** from your inventory. forage them with `/field action:forage`.',
            color=ERROR_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    from engine.rolls import roll_d20
    from engine.character import attr_modifier
    wis_attr = int(user['attr_wis'] if 'attr_wis' in user.keys() else 3)
    mod = attr_modifier(wis_attr)
    die = roll_d20()
    total = die + mod
    dc = 14
    roll_note = f"\n_survival: **{die}** + wis **{mod:+}** = **{total}** vs dc **{dc}**_"

    db.consume_item(interaction.user.id, cobweb_item['id'], quantity=1)

    if total >= dc:
        world = db.get_world(interaction.guild.id) if interaction.guild else None
        treat_day = world['day_number'] if world else int(user['last_rest_day'] or 0)
        from engine.herb_buffs import grant_bleed_dressed as _gbd
        db.update_user(interaction.user.id, wolf_id=user['id'], **_gbd(user, day=treat_day))
        msg = (
            f"**{user['wolf_name']}** packs cobwebs into the wound; the bleeding is slowed. "
            f"deep gash won't bleed at the next sunrise. (-1 cobweb){roll_note}"
        )
        embed = howlbert_embed('field dressing', msg, color=SUCCESS_COLOR)
    else:
        msg = (
            f"**{user['wolf_name']}** fumbles the dressing; the wound stays open. "
            f"the cobweb is lost. (-1 cobweb){roll_note}"
        )
        embed = howlbert_embed('field dressing failed', msg, color=ERROR_COLOR)

    await interaction.response.send_message(embed=embed)


async def wound_wash(interaction: discord.Interaction, own_wolf: str | None = None):
    """wash an infected wound with dock or horsetail, dc 10 medicine; clears infected_wound."""
    if own_wolf:
        user = db.find_user_wolf(interaction.user.id, own_wolf)
        if not user:
            embed = howlbert_embed('unknown wolf', f'no wolf named **{own_wolf}** on your account.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
    else:
        user = db.get_user(interaction.user.id)

    if not user:
        embed = howlbert_embed('not registered', 'use `/register` first.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    from engine.injury_effects import has_injury
    if not has_injury(user, 'infected_wound'):
        embed = howlbert_embed('no infection', f"**{user['wolf_name']}** doesn't have an **infected wound** to wash.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    WASH_HERBS = {'herb_dock': 'dock leaves', 'herb_horsetail': 'horsetail'}
    herb_item = None
    herb_label = None
    for herb_key, label in WASH_HERBS.items():
        item = db.get_item_by_key(herb_key)
        if item and db.get_inventory_quantity(interaction.user.id, item['id']) >= 1:
            herb_item = item
            herb_label = label
            break

    if not herb_item:
        embed = howlbert_embed('no herb', 'wound wash requires **1 dock leaf** or **1 horsetail** from your inventory.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    from engine.rolls import roll_d20
    from engine.character import attr_modifier
    wis_attr = int(user['attr_wis'] if 'attr_wis' in user.keys() else 3)
    mod = attr_modifier(wis_attr)
    die = roll_d20()
    total = die + mod
    dc = 10
    roll_note = f"\n_medicine: **{die}** + wis **{mod:+}** = **{total}** vs dc **{dc}**_"

    db.consume_item(interaction.user.id, herb_item['id'], quantity=1)

    if total >= dc:
        import json
        from engine.conditions import parse_injuries
        injuries = parse_injuries(user['active_injuries'] if 'active_injuries' in user.keys() else None)
        if 'infected_wound' in injuries:
            injuries.remove('infected_wound')
        db.set_user_conditions(user['discord_id'], active_injuries=json.dumps(injuries))
        msg = (
            f"**{user['wolf_name']}** flushes the wound with {herb_label}; the infection clears. "
            f"(-1 {herb_label}){roll_note}"
        )
        embed = howlbert_embed('wound wash', msg, color=SUCCESS_COLOR)
    else:
        msg = (
            f"**{user['wolf_name']}** struggles to clean the wound; the infection lingers. "
            f"the {herb_label} is spent. (-1 {herb_label}){roll_note}"
        )
        embed = howlbert_embed('wound wash failed', msg, color=ERROR_COLOR)

    await interaction.response.send_message(embed=embed)


async def herb_guide(interaction: discord.Interaction, herb_filter: str = 'all'):
    from engine.herb_guide import build_herb_guide_embed
    from utils.herb_views import make_herb_guide_view

    if herb_filter not in ('all', 'wild', 'roadside', 'compound'):
        herb_filter = 'all'

    title, body = build_herb_guide_embed(page=0, filter_key=herb_filter)
    embed = howlbert_embed(title, body)
    embed.set_footer(text='herb guide · /herbs action:guide')
    view = make_herb_guide_view(page=0, filter_key=herb_filter)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=reply_ephemeral())


async def denstore(interaction: discord.Interaction, mode: str, store_stack: str | None, herb: str | None):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message(
            player_message('use `/register` in a server.'),
            ephemeral=reply_ephemeral()
        )
        return

    if not user['pack_id']:
        embed = howlbert_embed('no pack', "join a pack to use the healers' herb store.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    from engine.pack_herb_store import (
        can_manage_den_herbs,
        deposit_all_herbs_to_store,
        deposit_inventory_herb_to_store,
        list_pack_herb_store,
        withdraw_all_herbs_from_store,
        withdraw_herb_from_store
    )

    world = db.get_world(interaction.guild.id)

    if mode == 'list':
        body = list_pack_herb_store(user['pack_id'], world['day_number'])
        embed = howlbert_embed("healers' herb store", body)
        embed.set_footer(
            text='anyone: `mode:deposit` / `depositall` · medics only: `mode:withdraw` / `withdrawall`'
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if mode == 'depositall':
        ok, msg = deposit_all_herbs_to_store(
            user,
            pack_id=user['pack_id'],
            guild_id=interaction.guild.id,
            day=world['day_number']
        )
    elif mode == 'deposit':
        raw = (store_stack or herb or '').strip().lower()
        if not raw.startswith('herb_'):
            await interaction.response.send_message(
                player_message('pick an inventory herb key like **`herb_arnica`** to deposit.'),
                ephemeral=reply_ephemeral()
            )
            return
        ok, msg = deposit_inventory_herb_to_store(
            user,
            raw,
            pack_id=user['pack_id'],
            guild_id=interaction.guild.id,
            day=world['day_number']
        )
    elif mode == 'withdraw':
        if not can_manage_den_herbs(user):
            embed = howlbert_embed('medic only', "only **medics** may withdraw from the healers' store.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        try:
            sid = int((store_stack or herb or '').strip().lstrip('#'))
        except (ValueError, TypeError):
            await interaction.response.send_message(
                player_message('enter store stack **`#ID`** from `/herbs action:store mode:list`.'),
                ephemeral=reply_ephemeral()
            )
            return
        ok, msg = withdraw_herb_from_store(
            user,
            sid,
            pack_id=user['pack_id'],
            guild_id=interaction.guild.id,
            day=world['day_number']
        )
    elif mode == 'withdrawall':
        if not can_manage_den_herbs(user):
            embed = howlbert_embed('medic only', "only **medics** may withdraw from the healers' store.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        ok, msg = withdraw_all_herbs_from_store(
            user,
            pack_id=user['pack_id'],
            guild_id=interaction.guild.id,
            day=world['day_number']
        )
    else:
        await interaction.response.send_message(
            player_message('pick **list**, **deposit**, **depositall**, **withdraw**, or **withdrawall**.'),
            ephemeral=reply_ephemeral()
        )
        return

    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(
        embed=howlbert_embed('den herb store', msg, color=color)
    )


async def turnin_restricted(interaction: discord.Interaction, herb_key: str | None):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message(
            player_message('use `/register` in a server.'),
            ephemeral=reply_ephemeral()
        )
        return

    if not user['pack_id']:
        embed = howlbert_embed('no pack', 'join a pack to turn poison herbs in.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    from engine.pack_herb_store import turnin_restricted_herb

    raw = (herb_key or '').strip().lower()
    if not raw.startswith('herb_'):
        await interaction.response.send_message(
            player_message('enter an inventory **`herb_wolfsbane`** key for the restricted herb to turn in.'),
            ephemeral=reply_ephemeral()
        )
        return

    world = db.get_world(interaction.guild.id)
    ok, msg = turnin_restricted_herb(
        user,
        raw,
        pack_id=int(user['pack_id']),
        guild_id=interaction.guild.id,
        day=world['day_number']
    )
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(
        embed=howlbert_embed('poison herb turn-in', msg, color=color)
    )


async def sacred_visit(interaction: discord.Interaction):
    user = db.get_user(interaction.user.id)
    if not user:
        await interaction.response.send_message(
            player_message('use `/register` first.'),
            ephemeral=reply_ephemeral()
        )
        return

    if not interaction.guild:
        await interaction.response.send_message(
            player_message('use this in a server.'),
            ephemeral=reply_ephemeral()
        )
        return

    world = db.get_world(interaction.guild.id)
    from engine.sacred_visits import record_sacred_visit
    ok, body = record_sacred_visit(user, day=world['day_number'])
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(
        embed=howlbert_embed('sacred visit', body, color=color)
    )


async def spirit_ritual(
    interaction: discord.Interaction,
    patient: discord.Member | None,
    ritual_herb: str | None,
    own_patient: str | None = None,
    patient_wolf: str | None = None
):
    medic = db.get_user(interaction.user.id)
    if not medic or not interaction.guild:
        await interaction.response.send_message(
            player_message('use `/register` in a server.'),
            ephemeral=reply_ephemeral()
        )
        return

    if patient and own_patient:
        embed = howlbert_embed('pick one', 'use `patient` or `own_patient`; not both.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if not patient and not own_patient:
        await interaction.response.send_message(
            player_message('pick a **patient** or **own_patient** for the cleansing ritual.'),
            ephemeral=reply_ephemeral()
        )
        return

    if not ritual_herb:
        await interaction.response.send_message(
            player_message('pick **douglas_sagewort**, **lavender**, or **mountain_ash** (rowan).'),
            ephemeral=reply_ephemeral()
        )
        return

    if own_patient:
        rows = db.list_user_wolves(interaction.user.id)
        target = next((w for w in rows if w['wolf_name'].lower() == own_patient.strip().lower()), None)
        if not target:
            embed = howlbert_embed('unknown wolf', f'no wolf named **{own_patient}** on your account.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
    else:
        if patient_wolf:
            target = db.find_user_wolf(patient.id, patient_wolf)
            if not target:
                embed = howlbert_embed(
                    'unknown wolf',
                    db.explain_wolf_not_found(patient.id, patient_wolf, player_label=patient.display_name),
                    color=ERROR_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        else:
            target = db.get_user(patient.id)
        if not target:
            await interaction.response.send_message(
                player_message('patient is not on howlbert.'),
                ephemeral=reply_ephemeral()
            )
            return

    world = db.get_world(interaction.guild.id)
    from engine.medical_care import run_spirit_ritual
    ok, body = run_spirit_ritual(
        medic,
        target,
        ritual_herb,
        day=world['day_number'],
        guild_id=interaction.guild.id if interaction.guild else None
    )
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(
        embed=howlbert_embed('spirit ritual', body, color=color)
    )

    if ok:
        gid = interaction.guild.id if interaction.guild else None
        db.increment_quest_progress(interaction.user.id, 'treat', guild_id=gid)


async def naming_ceremony(
    interaction: discord.Interaction,
    patient: discord.Member | None,
    own_patient: str | None = None,
    patient_wolf: str | None = None
):
    medic = db.get_user(interaction.user.id)
    if not medic or not interaction.guild:
        await interaction.response.send_message(
            player_message('use `/register` in a server.'),
            ephemeral=reply_ephemeral()
        )
        return

    if patient and own_patient:
        embed = howlbert_embed('pick one', 'use `patient` or `own_patient`; not both.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if not patient and not own_patient:
        await interaction.response.send_message(
            player_message('pick the **pup** (`patient` or `own_patient`) for the naming rite.'),
            ephemeral=reply_ephemeral()
        )
        return

    if own_patient:
        rows = db.list_user_wolves(interaction.user.id)
        pup = next((w for w in rows if w['wolf_name'].lower() == own_patient.strip().lower()), None)
        if not pup:
            embed = howlbert_embed('unknown wolf', f'no wolf named **{own_patient}** on your account.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
    else:
        if patient_wolf:
            pup = db.find_user_wolf(patient.id, patient_wolf)
            if not pup:
                embed = howlbert_embed(
                    'unknown wolf',
                    db.explain_wolf_not_found(patient.id, patient_wolf, player_label=patient.display_name),
                    color=ERROR_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        else:
            pup = db.get_user(patient.id)
        if not pup:
            await interaction.response.send_message(
                player_message('that wolf is not on howlbert.'),
                ephemeral=reply_ephemeral()
            )
            return

    world = db.get_world(interaction.guild.id)
    from engine.medical_care import run_naming_ceremony
    ok, body = run_naming_ceremony(medic, pup, day=world['day_number'])
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(
        embed=howlbert_embed('naming ceremony', body, color=color)
    )


async def lay_to_rest(
    interaction: discord.Interaction,
    deceased: discord.Member | None,
    lay_herb: str | None,
    own_deceased: str | None = None,
    deceased_wolf: str | None = None
):
    medic = db.get_user(interaction.user.id)
    if not medic:
        await interaction.response.send_message(
            player_message('use `/register` first.'),
            ephemeral=reply_ephemeral()
        )
        return

    if deceased and own_deceased:
        embed = howlbert_embed('pick one', 'use `deceased` or `own_deceased`; not both.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if not deceased and not own_deceased:
        await interaction.response.send_message(
            player_message('pick **deceased** (or `own_deceased`) and **lay_herb** (rosemary, lavender, mint).'),
            ephemeral=reply_ephemeral()
        )
        return

    if not lay_herb:
        await interaction.response.send_message(
            player_message('pick a **lay_herb** (rosemary, lavender, mint).'),
            ephemeral=reply_ephemeral()
        )
        return

    if own_deceased:
        rows = db.list_user_wolves(interaction.user.id)
        target = next((w for w in rows if w['wolf_name'].lower() == own_deceased.strip().lower()), None)
        if not target:
            embed = howlbert_embed('unknown wolf', f'no wolf named **{own_deceased}** on your account.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
    else:
        if deceased_wolf:
            target = db.find_user_wolf(deceased.id, deceased_wolf)
            if not target:
                embed = howlbert_embed(
                    'unknown wolf',
                    db.explain_wolf_not_found(deceased.id, deceased_wolf, player_label=deceased.display_name),
                    color=ERROR_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        else:
            target = db.get_user(deceased.id)
        if not target:
            await interaction.response.send_message(
                player_message('that wolf is not on howlbert.'),
                ephemeral=reply_ephemeral()
            )
            return

    from engine.medical_care import run_lay_to_rest
    world = db.get_world(interaction.guild.id) if interaction.guild else None
    day = world['day_number'] if world else 0
    ok, body = run_lay_to_rest(medic, target, lay_herb, day=day)
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(
        embed=howlbert_embed('lay to rest', body, color=color)
    )


async def quarantine_command(
    interaction: discord.Interaction,
    wolf: discord.Member | None = None,
    own_wolf: str | None = None,
    release: bool = False,
    wolf_name: str | None = None
):
    from engine.diseases import disease_display
    from engine.quarantine import can_manage_quarantine, is_quarantined

    actor = db.get_user(interaction.user.id)
    if not actor:
        embed = howlbert_embed('not registered', 'use `/register` first.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if wolf and own_wolf:
        embed = howlbert_embed('pick one target', 'choose another **player** or `own_wolf`; not both.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    pack = db.get_pack(actor['pack_id']) if actor['pack_id'] else None

    if not wolf and (not own_wolf):
        if is_quarantined(actor):
            from engine.conditions import format_conditions
            day = None
            if interaction.guild_id:
                world = db.get_world(interaction.guild_id)
                if world:
                    day = world['day_number']
            body = f"**{actor['wolf_name']}** is isolated in the sick den.\n\n{format_conditions(actor, day=day)}"
            embed = howlbert_embed('quarantined', body, color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        if pack and can_manage_quarantine(actor, pack):
            rows = db.list_pack_quarantined(pack['id'])
            if not rows:
                embed = howlbert_embed('sick den', 'no wolves are quarantined in your pack.', color=SUCCESS_COLOR)
            else:
                lines = [f"**{r['wolf_name']}**" for r in rows]
                embed = howlbert_embed('sick den: quarantined', '\n'.join(lines), color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        embed = howlbert_embed('quarantine', 'pick a **wolf** to isolate, or use `release:true` to free someone.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if own_wolf:
        rows = db.list_user_wolves(interaction.user.id)
        target = next((w for w in rows if w['wolf_name'].lower() == own_wolf.strip().lower()), None)
        if not target:
            embed = howlbert_embed('unknown wolf', f'no wolf named **{own_wolf}**.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
    else:
        if wolf_name:
            target = db.find_user_wolf(wolf.id, wolf_name)
            if not target:
                embed = howlbert_embed(
                    'unknown wolf',
                    db.explain_wolf_not_found(wolf.id, wolf_name, player_label=wolf.display_name),
                    color=ERROR_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        else:
            target = db.get_user(wolf.id)
        if not target:
            embed = howlbert_embed('not registered', "that wolf isn't registered.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

    if not pack:
        embed = howlbert_embed('no pack', 'quarantine is a pack sick-den measure.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if target['pack_id'] != pack['id']:
        embed = howlbert_embed('wrong pack', f"**{target['wolf_name']}** isn't in your pack.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if not can_manage_quarantine(actor, pack):
        embed = howlbert_embed('not authorized', 'only **medics**, **alphas**, and **advisors** can manage quarantine.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if release:
        if not is_quarantined(target):
            embed = howlbert_embed('not quarantined', f"**{target['wolf_name']}** isn't in isolation.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        db.set_quarantined(target['discord_id'], False, wolf_id=target['id'])
        embed = howlbert_embed('released', f"**{target['wolf_name']}** may leave the sick den.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)
        return

    if is_quarantined(target):
        embed = howlbert_embed('already quarantined', f"**{target['wolf_name']}** is already isolated.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    db.set_quarantined(target['discord_id'], True, wolf_id=target['id'])
    illness = disease_display(target)
    from engine.diseases import illness_displays
    all_ill = illness_displays(target)
    extra = ''
    if all_ill:
        extra = '\n\nillness: ' + '; '.join((f'**{name}**; {effect}' for name, effect in all_ill))
    elif illness:
        extra = f'\n\nillness: **{illness[0]}**: {illness[1]}'

    embed = howlbert_embed(
        'quarantined',
        f"**{target['wolf_name']}** is isolated in the sick den. "
        f"they cannot spread illness or join pack activities until released.{extra}",
        color=SUCCESS_COLOR
    )
    await interaction.response.send_message(embed=embed)


async def dissect_cadaver(
    interaction: discord.Interaction,
    deceased: discord.Member | None,
    own_deceased: str | None = None,
    deceased_wolf: str | None = None,
):
    """Medic-apprentice cadaver dissection: study a fallen packmate to train anatomy."""
    apprentice = db.get_user(interaction.user.id)
    if not apprentice:
        await interaction.response.send_message(player_message('use `/register` first.'), ephemeral=reply_ephemeral())
        return

    from engine.medic_cadaver import perform_dissection, is_apprentice_medic

    if not is_apprentice_medic(apprentice):
        await interaction.response.send_message(
            embed=howlbert_embed('not an apprentice', 'only **medic apprentices** may dissect cadavers to learn anatomy.', color=ERROR_COLOR),
            ephemeral=reply_ephemeral(),
        )
        return

    if deceased and own_deceased:
        await interaction.response.send_message(embed=howlbert_embed('pick one', 'use `deceased` or `own_deceased`; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
        return
    if not deceased and not own_deceased:
        await interaction.response.send_message(
            player_message('pick the cadaver: **deceased** (another player) with optional **deceased_wolf**, or your own **own_deceased**.'),
            ephemeral=reply_ephemeral(),
        )
        return

    if own_deceased:
        rows = db.list_user_wolves(interaction.user.id)
        cadaver = next((w for w in rows if w['wolf_name'].lower() == own_deceased.strip().lower()), None)
        if not cadaver:
            await interaction.response.send_message(embed=howlbert_embed('unknown wolf', f'no wolf named **{own_deceased}** on your account.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
    elif deceased_wolf:
        cadaver = db.find_user_wolf(deceased.id, deceased_wolf)
        if not cadaver:
            await interaction.response.send_message(embed=howlbert_embed('unknown wolf', db.explain_wolf_not_found(deceased.id, deceased_wolf, player_label=deceased.display_name), color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
    else:
        cadaver = db.get_user(deceased.id)
        if not cadaver:
            await interaction.response.send_message(player_message('that wolf is not on Howlbert.'), ephemeral=reply_ephemeral())
            return

    if cadaver['condition'] != 'dead':
        await interaction.response.send_message(
            embed=howlbert_embed('not dead', f"**{cadaver['wolf_name']}** is not dead; only the dead can be studied.", color=ERROR_COLOR),
            ephemeral=reply_ephemeral(),
        )
        return

    day = db.get_world(interaction.guild.id)['day_number'] if interaction.guild else 0
    dissected, success, msg = perform_dissection(apprentice, cadaver, day=day)
    color = SUCCESS_COLOR if success else ERROR_COLOR
    header = f"**{apprentice['wolf_name']}** studies **{cadaver['wolf_name']}**."
    embed = howlbert_embed('cadaver dissection', f"{header}\n\n{msg}", color=color)
    await interaction.response.send_message(embed=embed)

    # notify the cadaver's owner that their fallen wolf was studied (skip self).
    if dissected:
        owner_id = cadaver['discord_id'] if 'discord_id' in cadaver.keys() else None
        if owner_id and owner_id != interaction.user.id:
            from utils.notifications import try_dm_user
            pack_label = apprentice['great_pack'] if 'great_pack' in apprentice.keys() and apprentice['great_pack'] else 'the pack'
            await try_dm_user(
                interaction.client,
                owner_id,
                embed=howlbert_embed(
                    'a fallen wolf was studied',
                    f"**{apprentice['wolf_name']}** ({pack_label}) studied your fallen wolf "
                    f"**{cadaver['wolf_name']}** in the healers' den, to learn anatomy for the pack's medicine.",
                    color=SUCCESS_COLOR,
                ),
            )
