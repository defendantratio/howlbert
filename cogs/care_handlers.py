"""Shared care command handlers (herbs, medic treatment, rites)."""
from __future__ import annotations
import json
import random
import discord
import database as db
from engine.role_privileges import treat_limit_reached
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label

async def prepare_herb(interaction: discord.Interaction, stack_id: int, prep_method: str):
    _ = (stack_id, prep_method)
    await interaction.response.send_message(player_message('Forage herbs live in `/bones action:inventory`. Use `/herbs action:prepare` with an inventory herb key.'), ephemeral=reply_ephemeral())

async def dryall(interaction: discord.Interaction):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message(player_message('Use `/register` in a server.'), ephemeral=reply_ephemeral())
        return
    from engine.herb_preparation import dry_all_fresh_herbs
    world = db.get_world(interaction.guild.id)
    ok, msg = dry_all_fresh_herbs(user, day=world['day_number'], guild_id=interaction.guild.id, at_den=bool(user['pack_id']))
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed('Dry All Herbs', msg, color=color))

async def prepare_herb_inventory(interaction: discord.Interaction, item_key: str, prep_method: str):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message(player_message('Use `/register` in a server.'), ephemeral=reply_ephemeral())
        return
    from engine.herb_preparation import prepare_herb_from_inventory
    world = db.get_world(interaction.guild.id)
    ok, msg = prepare_herb_from_inventory(user, item_key, prep_method, day=world['day_number'], guild_id=interaction.guild.id, at_den=bool(user['pack_id']))
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed('Herb Preparation', msg, color=color))

async def treat(interaction: discord.Interaction, herb: str, patient: discord.Member | None=None, own_wolf: str | None=None):
    if patient and own_wolf:
        embed = howlbert_embed('Pick One', 'Choose another **patient** or your **own_wolf** — not both.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if own_wolf:
        user = db.find_user_wolf(interaction.user.id, own_wolf)
        if not user:
            embed = howlbert_embed('Unknown Wolf', f'No wolf named **{own_wolf}** on your account.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
    else:
        user = db.get_user(interaction.user.id)
    if not user:
        embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    from engine.herb_storage import parse_herb_stack_id
    stack_id = parse_herb_stack_id(herb)
    if stack_id is not None:
        embed = howlbert_embed('Herb Bag Removed', 'Forage herbs live in `/bones action:inventory`. Use **`/medic action:treat herb:herb_yarrow`** (inventory key).', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    item = db.get_item_by_key(herb.strip().lower())
    if not item or (not item['key'].startswith('herb_') and item['key'] != 'stick'):
        embed = howlbert_embed('Unknown Herb', 'Use an herb from `/bones action:inventory` (keys like `herb_yarrow` or `stick`).', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    qty = db.get_inventory_quantity(interaction.user.id, item['id'])
    if qty < 1:
        embed = howlbert_embed('Not In Inventory', f"You don't have **{item['name']}**.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if treat_limit_reached(user):
        embed = howlbert_embed('Limit Reached', 'You can only **`/medic action:treat`** with herbs **3 times per sunrise**. **Medics** have no cap; promote to full Medic rank or wait for the next `/rollover`.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    from herbs import HERBS
    from engine.conditions import medicine_check, parse_injuries, treat_with_herb, herb_special_effect
    herb_key = 'stick' if item['key'] == 'stick' else item['key'].replace('herb_', '', 1)
    meta = HERBS.get(herb_key, {'cures': (), 'effect': item['description']})
    special = herb_special_effect(herb_key, user, inventory_qty=qty)
    world = db.get_world(interaction.guild.id) if interaction.guild else None
    treat_day = world['day_number'] if world else int(user['last_rest_day'] or 0)
    if special == 'ragweed_need_three':
        embed = howlbert_embed('Not Enough Ragweed', 'Ragweed needs **3 leaves** in inventory to remove 1 exhaustion.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if special == 'honey_needs_depletion':
        embed = howlbert_embed('Not Depleted Enough', 'Honey only shakes off **starvation exhaustion**; your hunger and thirst must be low first.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if special == 'honey_pup_not_depleted':
        embed = howlbert_embed('Not Depleted Enough', 'Honey feeds starving pups; hunger or thirst must be low first.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if special == 'feed_pup_honey':
        if not db.consume_item(interaction.user.id, item['id'], quantity=1):
            embed = howlbert_embed('Not In Inventory', f"You don't have enough **{item['name']}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day_number = world['day_number'] if world else None
        from config import HONEY_PUP_HUNGER_BONUS
        from engine.nursing import apply_honey_to_pup
        fields = apply_honey_to_pup(user, day_number=day_number)
        db.update_user(interaction.user.id, wolf_id=user['id'], **fields)
        ex_note = ''
        if 'exhaustion' in fields:
            ex_note = f" Exhaustion **→ {fields['exhaustion']}**."
        msg = f"**{item['name']}**: warm sweetness (**+{HONEY_PUP_HUNGER_BONUS}** hunger).{ex_note}"
        embed = howlbert_embed('Honey', msg, color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)
        return
    treat_subject = user
    treat_patient = None
    if patient:
        from engine.role_features import has_any_role, is_full_medic
        if not (is_full_medic(user) or has_any_role(user, 'medic_apprentice')):
            await interaction.response.send_message(embed=howlbert_embed('Medic Only', 'Only **Medics** and **Medic apprentices** may treat a **patient** from `/bones action:inventory` herbs.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        treat_patient = db.get_user(patient.id)
        if not treat_patient:
            await interaction.response.send_message(embed=howlbert_embed('Not Registered', 'Patient is not on Howlbert.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.medical_access import can_medic_treat_cross_pack
        p_cond = treat_patient['condition'] if 'condition' in treat_patient.keys() else 'healthy'
        emergency = p_cond in ('dying',) or int(treat_patient['hp']) <= 0
        ok_cross, cross_msg = can_medic_treat_cross_pack(user, treat_patient, interaction.guild.id, emergency_stabilize=emergency)
        if not ok_cross:
            await interaction.response.send_message(embed=howlbert_embed('Cannot Treat', cross_msg, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        treat_subject = treat_patient
    if treat_patient and special in ('reduce_exhaustion', 'hunger_shield', 'march_shield', 'jaw_meal_shield', 'purslane_thirst', 'sorrel_restore'):
        await interaction.response.send_message(embed=howlbert_embed('Self Use Only', f"**{item['name']}** must be taken by the wolf themselves; not via patient treat.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
        return
    outcome = treat_with_herb(treat_subject, herb_key, meta)
    if special == 'reduce_exhaustion' and int(user['exhaustion']) <= 0:
        embed = howlbert_embed('No Effect', f"**{item['name']}**: you aren't carrying exhaustion to shed.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if special == 'hunger_shield' and int(user['hunger_exhaustion_skip'] if 'hunger_exhaustion_skip' in user.keys() else 0):
        embed = howlbert_embed('Already Shielded', "Fennel's hunger shield is already active for the next sunrise.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if special == 'march_shield' and int(user['march_exhaustion_skip'] if 'march_exhaustion_skip' in user.keys() else 0):
        embed = howlbert_embed('Already Shielded', "Burnet's march ward is already active for the next sunrise.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if outcome == 'no_effect' and (not special) and (herb_key not in ('comfrey', 'cobwebs')):
        check = medicine_check(user, dc=15)
        from engine.herb_buffs import consume_herb_check_buffs
        consume_fields = consume_herb_check_buffs(user, skill_key='medicine')
        if consume_fields:
            db.update_user(interaction.user.id, wolf_id=user['id'], **consume_fields)
        if not check['success']:
            embed = howlbert_embed('Treatment Failed', f"Medicine check: {check['total']} vs DC 15; no effect.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed)
            return
    use_qty = 3 if herb_key == 'ragweed' and special == 'reduce_exhaustion' else 1
    if not db.consume_item(interaction.user.id, item['id'], quantity=use_qty):
        embed = howlbert_embed('Not In Inventory', f"You don't have enough **{item['name']}**.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    injuries = parse_injuries(treat_subject['active_injuries'] if 'active_injuries' in treat_subject.keys() else None)
    msg = ''
    subject_did = treat_subject['discord_id']
    subject_id = treat_subject['id']
    if special == 'reduce_exhaustion':
        old_ex = int(user['exhaustion'])
        new_ex = max(0, old_ex - 1)
        db.set_user_conditions(interaction.user.id, wolf_id=user['id'], exhaustion=new_ex)
        msg = f"**{item['name']}**: exhaustion **{old_ex}** → **{new_ex}**."
    elif special == 'hunger_shield':
        db.update_user(interaction.user.id, wolf_id=user['id'], hunger_exhaustion_skip=1)
        msg = f"**{item['name']}**: you won't gain hunger exhaustion on the next sunrise (thirst still applies)."
    elif special == 'march_shield':
        db.update_user(interaction.user.id, wolf_id=user['id'], march_exhaustion_skip=1)
        msg = f"**{item['name']}**: ignore the first **+1 exhaustion** from strain on the next sunrise."
    elif special == 'jaw_meal_shield':
        db.update_user(interaction.user.id, wolf_id=user['id'], jaw_meal_shield=1)
        msg = f"**{item['name']}**: you can eat and drink without pain until the next sunrise."
        if outcome == 'cured_injury':
            for inj in meta.get('cures', ()):
                if inj in injuries:
                    injuries.remove(inj)
                    db.clear_injury_since(subject_id, inj)
            db.set_user_conditions(subject_did, wolf_id=subject_id, active_injuries=json.dumps(injuries), condition='healthy' if not injuries else treat_subject['condition'])
            msg += ' Broken jaw treated.'
    elif special == 'purslane_thirst':
        thirst = db.adjust_thirst(user['id'], 12)
        msg = f"**{item['name']}**: chewed leaves restore thirst **{thirst}** (+12)."
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
            msg += ' Bleeding staunched.'
    elif outcome == 'cured_disease':
        db.set_user_conditions(subject_did, wolf_id=subject_id, clear_disease=True, condition='healthy')
        who = 'their disease' if treat_patient else 'your disease'
        msg = f"**{meta.get('name', item['name'])}** cured {who}."
    elif outcome == 'rabies_ease':
        from engine.herb_buffs import grant_disease_save_advantage
        db.update_user(subject_did, wolf_id=subject_id, **grant_disease_save_advantage(treat_subject))
        who = treat_subject['wolf_name'] if treat_patient else 'you'
        msg = f"**{item['name']}**: herbs slow early rabies for **{who}**; **advantage** on the next disease save (one sunrise). Rabies is not cured."
    elif outcome == 'cured_injury':
        for inj in meta.get('cures', ()):
            if inj in injuries:
                injuries.remove(inj)
                db.clear_injury_since(subject_id, inj)
        db.set_user_conditions(subject_did, wolf_id=subject_id, active_injuries=json.dumps(injuries), condition='healthy' if not injuries else treat_subject['condition'])
        who = f"**{treat_subject['wolf_name']}**'s injury" if treat_patient else 'your injury'
        msg = f"**{item['name']}** treated {who}."
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
        msg = f"**{item['name']}**: restricted poison; no safe cure applied. Medic knowledge only."
    elif outcome == 'healed' or herb_key == 'comfrey':
        from engine.exhaustion_effects import effective_max_hp
        heal = random.randint(1, 4)
        cap = effective_max_hp(treat_subject)
        new_hp = min(cap, int(treat_subject['hp']) + heal)
        db.set_user_conditions(subject_did, wolf_id=subject_id, hp=new_hp)
        who = treat_subject['wolf_name'] if treat_patient else 'you'
        msg = f'Comfrey poultice healed **{who}** **{heal} HP** (now **{new_hp}/{cap}**).'
    elif outcome == 'stabilized':
        db.set_user_conditions(subject_did, wolf_id=subject_id, hp=1, condition='stable')
        who = treat_subject['wolf_name'] if treat_patient else 'you'
        msg = f"**{item['name']}** stabilized **{who}** at 1 HP." if herb_key != 'cobwebs' else f'Cobwebs stabilized **{who}** at 1 HP.'
    from engine.herb_buffs import apply_supplemental_herb
    supplemental = apply_supplemental_herb(herb_key, treat_subject, day=treat_day, outcome=outcome)
    if supplemental:
        kind = supplemental['kind']
        sfields = supplemental.get('fields') or {}
        if kind == 'mercy':
            db.set_user_conditions(subject_did, wolf_id=subject_id, condition='dead', hp=0, death_cause=f"mercy ({item['name']})")
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
        msg = f"Applied **{item['name']}**: {meta.get('effect', 'minor relief')}."
    if treat_patient and treat_patient['id'] != user['id']:
        msg = f"**{user['wolf_name']}** treats **{treat_subject['wolf_name']}**:\n{msg}"
    db.update_user(interaction.user.id, wolf_id=user['id'], herb_treats_today=int(user['herb_treats_today'] if 'herb_treats_today' in user.keys() else 0) + 1)
    treats_after = int(user['herb_treats_today'] if 'herb_treats_today' in user.keys() else 0) + 1
    from engine.role_shift_bonus import apply_first_treat_bonus
    treat_shift = apply_first_treat_bonus(user, treats_after)
    if treat_shift:
        msg += f'\n\n_{treat_shift}_'
    embed = howlbert_embed('Treatment', msg, color=SUCCESS_COLOR)
    embed.set_footer(text='care plan: `/vitals action:condition` · surgery: `/medic action:surgery`')
    gid = interaction.guild.id if interaction.guild else None
    db.increment_quest_progress(interaction.user.id, 'treat', guild_id=gid)
    await interaction.response.send_message(embed=embed)

async def herb_guide(interaction: discord.Interaction, herb_filter: str='all'):
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
        await interaction.response.send_message(player_message('Use `/register` in a server.'), ephemeral=reply_ephemeral())
        return
    if not user['pack_id']:
        await interaction.response.send_message(embed=howlbert_embed('No Pack', "Join a pack to use the healers' herb store.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
        return
    from engine.pack_herb_store import can_manage_den_herbs, deposit_all_herbs_to_store, deposit_inventory_herb_to_store, list_pack_herb_store, withdraw_all_herbs_from_store, withdraw_herb_from_store
    world = db.get_world(interaction.guild.id)
    if mode == 'list':
        body = list_pack_herb_store(user['pack_id'], world['day_number'])
        embed = howlbert_embed("Healers' Herb Store", body)
        embed.set_footer(text='anyone: `mode:deposit` / `depositall` · medics & foragers: `mode:withdraw` / `withdrawall`')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if mode == 'depositall':
        ok, msg = deposit_all_herbs_to_store(user, pack_id=user['pack_id'], guild_id=interaction.guild.id, day=world['day_number'])
    elif mode == 'deposit':
        raw = (store_stack or herb or '').strip().lower()
        if not raw.startswith('herb_'):
            await interaction.response.send_message(player_message('Pick an inventory herb key like **`herb_arnica`** to deposit.'), ephemeral=reply_ephemeral())
            return
        ok, msg = deposit_inventory_herb_to_store(user, raw, pack_id=user['pack_id'], guild_id=interaction.guild.id, day=world['day_number'])
    elif mode == 'withdraw':
        if not can_manage_den_herbs(user):
            await interaction.response.send_message(embed=howlbert_embed('Medic / Forager Only', "Only **Medics** and **Foragers** may withdraw from the healers' store.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        try:
            sid = int((store_stack or herb or '').strip().lstrip('#'))
        except (ValueError, TypeError):
            await interaction.response.send_message(player_message('Enter store stack **`#ID`** from `/herbs action:store mode:list`.'), ephemeral=reply_ephemeral())
            return
        ok, msg = withdraw_herb_from_store(user, sid, pack_id=user['pack_id'], guild_id=interaction.guild.id, day=world['day_number'])
    elif mode == 'withdrawall':
        if not can_manage_den_herbs(user):
            await interaction.response.send_message(embed=howlbert_embed('Medic / Forager Only', "Only **Medics** and **Foragers** may withdraw from the healers' store.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        ok, msg = withdraw_all_herbs_from_store(user, pack_id=user['pack_id'], guild_id=interaction.guild.id, day=world['day_number'])
    else:
        await interaction.response.send_message(player_message('Pick **list**, **deposit**, **depositall**, **withdraw**, or **withdrawall**.'), ephemeral=reply_ephemeral())
        return
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed('Den Herb Store', msg, color=color))

async def turnin_restricted(interaction: discord.Interaction, herb_key: str | None):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message(player_message('Use `/register` in a server.'), ephemeral=reply_ephemeral())
        return
    if not user['pack_id']:
        await interaction.response.send_message(embed=howlbert_embed('No Pack', 'Join a pack to turn poison herbs in.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
        return
    from engine.pack_herb_store import turnin_restricted_herb
    raw = (herb_key or '').strip().lower()
    if not raw.startswith('herb_'):
        await interaction.response.send_message(player_message('Enter an inventory **`herb_wolfsbane`** key for the restricted herb to turn in.'), ephemeral=reply_ephemeral())
        return
    world = db.get_world(interaction.guild.id)
    ok, msg = turnin_restricted_herb(user, raw, pack_id=int(user['pack_id']), guild_id=interaction.guild.id, day=world['day_number'])
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed('Poison Herb Turn-In', msg, color=color))

async def sacred_visit(interaction: discord.Interaction):
    user = db.get_user(interaction.user.id)
    if not user:
        await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
        return
    if not interaction.guild:
        await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
        return
    world = db.get_world(interaction.guild.id)
    from engine.sacred_visits import record_sacred_visit
    ok, body = record_sacred_visit(user, day=world['day_number'])
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed('Sacred Visit', body, color=color))

async def spirit_ritual(interaction: discord.Interaction, patient: discord.Member | None, ritual_herb: str | None):
    medic = db.get_user(interaction.user.id)
    if not medic or not interaction.guild:
        await interaction.response.send_message(player_message('Use `/register` in a server.'), ephemeral=reply_ephemeral())
        return
    if not patient:
        await interaction.response.send_message(player_message('Pick a **patient** for the cleansing ritual.'), ephemeral=reply_ephemeral())
        return
    if not ritual_herb:
        await interaction.response.send_message(player_message('Pick **douglas_sagewort**, **lavender**, or **mountain_ash** (rowan).'), ephemeral=reply_ephemeral())
        return
    target = db.get_user(patient.id)
    if not target:
        await interaction.response.send_message(player_message('Patient is not on Howlbert.'), ephemeral=reply_ephemeral())
        return
    world = db.get_world(interaction.guild.id)
    from engine.medical_care import run_spirit_ritual
    ok, body = run_spirit_ritual(medic, target, ritual_herb, day=world['day_number'], guild_id=interaction.guild.id if interaction.guild else None)
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed('Spirit Ritual', body, color=color))
    if ok:
        gid = interaction.guild.id if interaction.guild else None
        db.increment_quest_progress(interaction.user.id, 'treat', guild_id=gid)

async def naming_ceremony(interaction: discord.Interaction, patient: discord.Member | None):
    medic = db.get_user(interaction.user.id)
    if not medic or not interaction.guild:
        await interaction.response.send_message(player_message('Use `/register` in a server.'), ephemeral=reply_ephemeral())
        return
    if not patient:
        await interaction.response.send_message(player_message('Pick the **pup** (`patient`) for the naming rite.'), ephemeral=reply_ephemeral())
        return
    pup = db.get_user(patient.id)
    if not pup:
        await interaction.response.send_message(player_message('That wolf is not on Howlbert.'), ephemeral=reply_ephemeral())
        return
    world = db.get_world(interaction.guild.id)
    from engine.medical_care import run_naming_ceremony
    ok, body = run_naming_ceremony(medic, pup, day=world['day_number'])
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed('Naming Ceremony', body, color=color))

async def lay_to_rest(interaction: discord.Interaction, deceased: discord.Member | None, lay_herb: str | None):
    medic = db.get_user(interaction.user.id)
    if not medic:
        await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
        return
    if not deceased or not lay_herb:
        await interaction.response.send_message(player_message('Pick **deceased** and **lay_herb** (rosemary, lavender, mint).'), ephemeral=reply_ephemeral())
        return
    target = db.get_user(deceased.id)
    if not target:
        await interaction.response.send_message(player_message('That wolf is not on Howlbert.'), ephemeral=reply_ephemeral())
        return
    from engine.medical_care import run_lay_to_rest
    world = db.get_world(interaction.guild.id) if interaction.guild else None
    day = world['day_number'] if world else 0
    ok, body = run_lay_to_rest(medic, target, lay_herb, day=day)
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed('Lay to Rest', body, color=color))

async def quarantine_command(interaction: discord.Interaction, wolf: discord.Member | None=None, own_wolf: str | None=None, release: bool=False):
    from engine.diseases import disease_display
    from engine.quarantine import can_manage_quarantine, is_quarantined
    actor = db.get_user(interaction.user.id)
    if not actor:
        embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if wolf and own_wolf:
        embed = howlbert_embed('Pick One Target', 'Choose another **player** or `own_wolf`; not both.', color=ERROR_COLOR)
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
            embed = howlbert_embed('Quarantined', body, color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if pack and can_manage_quarantine(actor, pack):
            rows = db.list_pack_quarantined(pack['id'])
            if not rows:
                embed = howlbert_embed('Sick Den', 'No wolves are quarantined in your pack.', color=SUCCESS_COLOR)
            else:
                lines = [f"**{r['wolf_name']}**" for r in rows]
                embed = howlbert_embed('Sick Den: Quarantined', '\n'.join(lines), color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Quarantine', 'Pick a **wolf** to isolate, or use `release:true` to free someone.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if own_wolf:
        rows = db.list_user_wolves(interaction.user.id)
        target = next((w for w in rows if w['wolf_name'].lower() == own_wolf.strip().lower()), None)
        if not target:
            embed = howlbert_embed('Unknown Wolf', f'No wolf named **{own_wolf}**.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
    else:
        target = db.get_user(wolf.id)
        if not target:
            embed = howlbert_embed('Not Registered', "That wolf isn't registered.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
    if not pack:
        embed = howlbert_embed('No Pack', 'Quarantine is a pack sick-den measure.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if target['pack_id'] != pack['id']:
        embed = howlbert_embed('Wrong Pack', "**{0}** isn't in your pack.".format(target['wolf_name']), color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if not can_manage_quarantine(actor, pack):
        embed = howlbert_embed('Not Authorized', 'Only **Medics**, **Alphas**, and **Advisors** can manage quarantine.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if release:
        if not is_quarantined(target):
            embed = howlbert_embed('Not Quarantined', f"**{target['wolf_name']}** isn't in isolation.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        db.set_quarantined(target['discord_id'], False, wolf_id=target['id'])
        embed = howlbert_embed('Released', f"**{target['wolf_name']}** may leave the sick den.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)
        return
    if is_quarantined(target):
        embed = howlbert_embed('Already Quarantined', f"**{target['wolf_name']}** is already isolated.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    db.set_quarantined(target['discord_id'], True, wolf_id=target['id'])
    illness = disease_display(target)
    from engine.diseases import illness_displays
    all_ill = illness_displays(target)
    extra = ''
    if all_ill:
        extra = '\n\nIllness: ' + '; '.join((f'**{name}** — {effect}' for name, effect in all_ill))
    elif illness:
        extra = f'\n\nIllness: **{illness[0]}**: {illness[1]}'
    embed = howlbert_embed('Quarantined', f"**{target['wolf_name']}** is isolated in the sick den. They cannot spread illness or join pack activities until released.{extra}", color=SUCCESS_COLOR)