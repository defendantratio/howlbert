"""Shared activity logic for slash commands and button panels."""

import random

import discord

import database as db
from config import (
    CRIME_BONES,
    CRIME_TEXT,
    CROSS_PACK_STEAL_BONES,
    CROSS_PACK_STEAL_TEXT,
    FISHING_BONES,
    SCAVENGE_BONES,
    TRACK_BONES,
    WORK_BONES,
    WORK_TEXT,
)
from engine.character import attr_modifier, get_attr, parse_proficiencies
from engine.cooldowns import daily_ration_note, daily_stipend_amount
from engine.donor import donor_daily_bonus
from engine.dice import format_roll_result, resolve_check
from herbs import FORAGE_RARITY_DC, HERBS
from engine.herb_storage import fresh_herb_warning, grant_fresh_herb
from engine.season_effects import season_forage_dc_mod, season_forage_modifier_label
from utils.currency import format_bones
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, embed_footer, howlbert_embed
from engine.infractions import (
    crime_caught_standing,
    cross_pack_steal_caught_standing,
    cross_pack_steal_standing,
    individual_steal_caught_standing,
    individual_steal_standing,
    pick_crime_caught_flavor,
    pick_cross_pack_steal_caught_flavor,
    roll_crime_caught,
    roll_individual_steal_caught,
)
from engine.role_privileges import (
    hunts_left_footer,
    hunts_used_today,
    is_hunter,
    record_hunt_use,
)
from engine.injury_effects import hunt_blocked_by_injury, strenuous_activity_blocked_by_injury
from engine.vitals import full_activity_block
from engine.role_restrictions import young_wolf_block
from engine.prey_pile import PREY_LABEL_FISH, PREY_LABEL_HARE
from engine.prey_storage import grant_prey_from_hunt
from engine.hunt import roll_hunt_amount
from engine.hunt_payout import grant_prey_carcass_canonical, hunt_flavor_for_payout, prey_key_for_payout
from engine.sniff import apply_sniff_bone_bonus, sniff_track_fail_reduction
from engine.hunt_combat import (
    LARGE_PREY_ENCOUNTER_TEXT,
    enrich_large_prey_embed,
    roll_large_prey_encounter,
    start_large_prey_fight,
)
from engine.shop_items import consume_item_by_key, has_item
from utils.hunting import award_bones, roll_range

SCAVENGE_TEXT = [
    "old bones half-buried in leaf litter; someone else's loss, your gain.",
    "a forgotten cache near a collapsed den.",
    "scraps along the trail. humble, but honest.",
    "you nose out a marrow-rich bone half-buried in the dirt.",
]

TRACK_OUTCOMES: list[tuple[str, str]] = [
    (
        "you follow spoor through bracken and pull a **vole** from a burrow mouth.",
        "vole",
    ),
    (
        "a moderate chase ends with a **hare** in your jaws.",
        "hare",
    ),
    (
        "scent leads you to a watering hole; a **rabbit** drinks too late.",
        "rabbit",
    ),
    (
        "you tracked well. a **grouse** never hears you over the creek.",
        "grouse",
    ),
    (
        "tiny prints in the mud lead to a **mouse** nest under a root.",
        "mouse",
    ),
    (
        "a chattering **squirrel** gives itself away from the underbrush.",
        "squirrel",
    ),
]

FISH_TEXT = [
    "a silver fish flips in your teeth at the riverbank.",
    "slow paw, steady catch; the river gives without a chase.",
    "you pull trout from the shallows as dusk settles.",
    "the current runs cold, but your haul runs true.",
]

TRACK_MISS_FLAVOR = (
    "the sign was old; whatever made it is already miles off.",
    "you lose the trail in wet stone and turn back empty-pawed.",
    "prey scent fades into pine; nothing worth the chase today.",
)

FISHING_FAIL_FLAVOR = (
    "the river runs empty; your jaws close on nothing but cold water.",
    "minnows scatter; no honest haul today.",
    "current too fast; the bank keeps its fish.",
)


def _strenuous_injury_embed(user) -> discord.Embed | None:
    block = strenuous_activity_blocked_by_injury(user)
    if block:
        return howlbert_embed("too injured", block, color=ERROR_COLOR)
    return None


def _need_guild(interaction: discord.Interaction) -> int | None:
    return interaction.guild.id if interaction.guild else None


def _activity_block_embed(
    user, *, title: str, day: int = 0, action: str = "hunt"
) -> discord.Embed | None:
    block = full_activity_block(user, day, action=action)
    if block:
        return howlbert_embed(title, block, color=ERROR_COLOR)
    return None


def try_daily(interaction: discord.Interaction) -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("server only", "use this in a server.", color=ERROR_COLOR)
    day = db.get_world(guild_id)["day_number"]
    if user["last_daily_day"] >= day:
        return howlbert_embed("already claimed", "daily stipend taken this rollover.", color=ERROR_COLOR)

    from engine.role_features import is_rogue_wolf

    if is_rogue_wolf(user):
        return howlbert_embed(
            "no den stipend",
            "rogues scrape by outside pack treasuries; no `/bones action:daily` draw.\n\n"
            "earn bones with `/bones action:hunt`, `/bones action:work`, or `/field action:scavenge`.",
            color=ERROR_COLOR,
        )

    pack_id = user["pack_id"] if "pack_id" in user.keys() else None
    if not pack_id:
        return howlbert_embed(
            "no pack treasury",
            "loners don't draw from a den stash. join a great pack with `/setfaction`, "
            "or earn bones with `/bones action:hunt`, `/bones action:work`, or `/field action:scavenge`.",
            color=ERROR_COLOR,
        )

    pack = db.get_pack(pack_id)
    if not pack:
        return howlbert_embed("pack not found", "join a great pack first.", color=ERROR_COLOR)

    account = db.get_account(interaction.user.id)

    is_booster = bool(
        isinstance(interaction.user, discord.Member) and interaction.user.premium_since
    )
    from config import BOOST_DAILY_BONUS

    donor_bonus = donor_daily_bonus(interaction.user.id)
    base_reward = daily_stipend_amount(account["prestige_tier"], is_booster=False)
    personal_bonus = (BOOST_DAILY_BONUS if is_booster else 0) + donor_bonus
    treasury = int(pack["treasury"])
    if treasury < base_reward:
        return howlbert_embed(
            "treasury bare",
            f"**{pack['name']}** only has **{format_bones(treasury)}** in the communal stash; "
            f"not enough for today's **{format_bones(base_reward)}** stipend.\n\n"
            "feed the treasury: hunt (pack tax), `/pack deposit`, or share fresh-kill to the den on `/preypile`.",
            color=ERROR_COLOR,
        )

    if not db.claim_daily_stipend(interaction.user.id, pack_id, base_reward):
        return howlbert_embed(
            "stipend failed",
            "could not pay from treasury; try again or ask your alpha to deposit.",
            color=ERROR_COLOR,
        )

    if personal_bonus > 0:
        db.add_bones(interaction.user.id, personal_bonus, wolf_id=user["id"])

    db.update_user(interaction.user.id, last_daily_day=day)
    db.add_xp(interaction.user.id, 1)
    updated = db.get_user(interaction.user.id)
    updated_pack = db.get_pack(pack_id)
    total_payout = base_reward + personal_bonus
    embed = howlbert_embed("daily stipend", color=SUCCESS_COLOR)
    embed.description = daily_ration_note(
        account["prestige_tier"],
        pack_name=pack["name"],
        treasury=int(updated_pack["treasury"]) if updated_pack else 0,
        is_booster=is_booster,
        donor_bonus=donor_bonus,
    )
    embed.add_field(name="received", value=format_bones(total_payout, signed=True), inline=True)
    embed.add_field(name="your balance", value=format_bones(updated["bones"]), inline=True)
    embed.add_field(
        name="pack treasury",
        value=format_bones(updated_pack["treasury"]) if updated_pack else "-",
        inline=True,
    )
    return embed


def _activity_fatigue_note(user, activity_key: str, day: int, **kwargs) -> str | None:
    # Activity-repeat fatigue is retired (energy is the throttle). This hook now
    # surfaces the strenuous-strain note instead: the cost of hunting/patrolling
    # through a spinal injury, post-surgery bone rest, or late pregnancy.
    from engine.strenuous_strain import apply_strenuous_strain

    action = {"fish": "fishing"}.get(activity_key, activity_key)
    return apply_strenuous_strain(user, day, action)


def _append_notes_to_footer(embed, *notes: str | None) -> None:
    parts = [n for n in notes if n]
    if not parts or not embed:
        return
    footer = embed.footer.text if embed.footer and embed.footer.text else ""
    extra = " · ".join(parts)
    embed.set_footer(text=f"{footer} · {extra}" if footer else extra)


def try_hunt(interaction: discord.Interaction, *, territory: str | None = None) -> tuple[discord.Embed | None, bool, int | None]:
    """Returns (embed, show_prey_buttons, hunt_combat_encounter_id)."""
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR), False, None
    block = young_wolf_block(user, action="hunt")
    if block:
        return howlbert_embed("too young to hunt", block, color=ERROR_COLOR), False, None
    inj_block = hunt_blocked_by_injury(user)
    if inj_block:
        return howlbert_embed("cannot hunt", inj_block, color=ERROR_COLOR), False, None
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("server only", "use this in a server.", color=ERROR_COLOR), False, None
    world = db.get_world(guild_id)
    day = world["day_number"]
    blocked = _activity_block_embed(user, title="cannot hunt", day=day, action="hunt")
    if blocked:
        return blocked, False, None
    # no hunt cap: hunt as often as you like; energy runs out instead of
    # blocking, and running on empty costs exhaustion/mood, not the hunt.
    if roll_large_prey_encounter():
        record_hunt_use(interaction.user.id, wolf_id=user["id"], day=day)
        enc_id = start_large_prey_fight(
            user,
            guild_id=guild_id,
            channel_id=interaction.channel_id,
        )
        flavor = random.choice(LARGE_PREY_ENCOUNTER_TEXT)
        embed = howlbert_embed("large prey!", flavor, color=SUCCESS_COLOR)
        updated = db.get_user(interaction.user.id)
        embed = enrich_large_prey_embed(embed, enc_id, updated, day=day)
        fatigue = _activity_fatigue_note(
            updated, "hunt", day, activity_count=hunts_used_today(updated, day)
        )
        _append_notes_to_footer(embed, fatigue)
        return embed, False, enc_id

    from engine.wild_encounters import ambush_embed, maybe_start_activity_ambush

    ambush = maybe_start_activity_ambush(
        user,
        guild_id=guild_id,
        channel_id=interaction.channel_id,
        activity="hunt",
    )
    if ambush:
        enc_id, template_key, flavor = ambush
        embed = ambush_embed(template_key, flavor, user, activity="hunt")
        from config import HUNT_WILD_ENCOUNTER_CHANCE

        embed.set_footer(
            text=f"~{HUNT_WILD_ENCOUNTER_CHANCE}% ambush · win to finish your hunt · flee and you keep today's hunt"
        )
        return embed, False, enc_id

    from engine.character_traits import roll_trait_hunt_abort

    aborted, omen_trait = roll_trait_hunt_abort(user)
    if aborted:
        record_hunt_use(interaction.user.id, wolf_id=user["id"], day=day)
        updated = db.get_user(interaction.user.id)
        fatigue = _activity_fatigue_note(
            updated, "hunt", day, activity_count=hunts_used_today(updated, day)
        )
        flavor = (
            f"a bad omen stops you cold; **{omen_trait}** sends you back to the den empty-pawed."
        )
        embed = howlbert_embed("hunt aborted", flavor, color=ERROR_COLOR)
        updated = db.get_user(interaction.user.id)
        embed.set_footer(text=hunts_left_footer(updated, day))
        _append_notes_to_footer(embed, fatigue)
        return embed, False, None

    dex_bonus = max(0, attr_modifier(get_attr(user, "dex")))
    amount = roll_hunt_amount()
    if amount > 0:
        amount += dex_bonus
    from engine.energy import spend_energy
    _new_energy, _had_energy, hunt_penalty = spend_energy(user, "hunt", discounted=is_hunter(user))
    amount, sniff_bonus, sniff_note = apply_sniff_bone_bonus(user, amount, day)

    # prayer bonus (set by /bones action:pray same day)
    from engine.hunt_prayer import HUNT_PRAYER_BONE_BONUS
    _pray_day = user["hunt_prayer_day"] if "hunt_prayer_day" in user.keys() else 0
    prayer_bonus = HUNT_PRAYER_BONE_BONUS if (_pray_day == day and amount > 0) else 0
    if prayer_bonus:
        amount += prayer_bonus

    # --- loner penalty (if no pack) ---
    loner_note = ""
    pack_id = user["pack_id"] if "pack_id" in user.keys() else None
    if not pack_id and amount > 0:
        from config import LONER_HUNT_PENALTY_PCT
        penalty = max(1, int(amount * LONER_HUNT_PENALTY_PCT // 100))
        amount = max(0, amount - penalty)
        loner_note = f"hunting alone: −{LONER_HUNT_PENALTY_PCT}% yield"

    # --- always calculate payout (important: unindented from the if above) ---
    net_amount, tax, payout, lucky_bonus, mood_note, hunger_note, thirst_note, exhaustion_note, season_note = award_bones(
        user, amount, world["weather"], "hunt", season=world["season"], guild_id=guild_id, day=day, territory=territory
    )

    prey_key = prey_key_for_payout(payout, user=user, season=world["season"]) if payout > 0 else None
    flavor = hunt_flavor_for_payout(payout, prey_key)
    record_hunt_use(interaction.user.id, wolf_id=user["id"], day=day)
    if net_amount > 0:
        db.increment_quest_progress(interaction.user.id, "hunt", guild_id=guild_id)
    updated = db.get_user(interaction.user.id)
    from engine.role_shift_bonus import apply_first_hunt_bonus

    hunt_shift = apply_first_hunt_bonus(updated, day)
    fatigue = _activity_fatigue_note(
        updated, "hunt", day, activity_count=hunts_used_today(updated, day)
    )
    db.update_user(
        interaction.user.id,
        last_hunt_yield=payout if payout > 0 else 0,
        last_prey_label=None,
    )
    updated = db.get_user(interaction.user.id)
    title = "empty paws" if net_amount == 0 else "hunt complete"
    color = ERROR_COLOR if net_amount == 0 else SUCCESS_COLOR
    embed = howlbert_embed(title, flavor, color=color)
    embed.add_field(name="earned", value=format_bones(net_amount, signed=True), inline=True)
    if sniff_bonus > 0:
        embed.add_field(name="sniff bonus", value=format_bones(sniff_bonus, signed=True), inline=True)
    if prayer_bonus > 0:
        embed.add_field(name="hunt prayer", value=format_bones(prayer_bonus, signed=True), inline=True)
    if lucky_bonus > 0:
        embed.add_field(name="lucky tooth", value=format_bones(lucky_bonus, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="pack tax", value=format_bones(tax), inline=True)
    embed.add_field(name="balance", value=format_bones(updated["bones"]), inline=True)
    if net_amount > 0 and prey_key:
        prey_name = grant_prey_carcass_canonical(
            user["id"],
            guild_id=guild_id,
            day=day,
            prey_key=prey_key,
        )
        footer = f"{prey_name} in your hoard (`/food`) · lay out with `/preypile`"
        from engine.blooding import award_blooding_on_hunt

        blooding_note = award_blooding_on_hunt(user)
        if blooding_note:
            footer = f"{blooding_note} · {footer}"
        footer += f" · {hunts_left_footer(updated, day)}"
        from engine.nursing import is_nursing_mother

        if is_nursing_mother(updated):
            footer += " · Nursing dam: eat extra from `/food`; lactation drains hunger each sunrise"
        notes = [n for n in (loner_note, sniff_note, season_note, mood_note, hunger_note, thirst_note, exhaustion_note) if n]
        if hunt_shift:
            notes.append(hunt_shift.strip("_"))
        if hunt_penalty:
            notes.append(hunt_penalty)
        from utils.hunting import weather_hunt_modifier_label

        weather_note = weather_hunt_modifier_label(world["weather"])
        if weather_note:
            notes.insert(0, weather_note)
        if net_amount > 0:
            from engine.season_rollover import try_autumn_hunt_cache

            cache_note = try_autumn_hunt_cache(user, season=world["season"])
            if cache_note:
                notes.append(cache_note.strip("_"))
        if notes:
            footer += " · " + " · ".join(notes)
        embed.set_footer(text=footer)
    elif net_amount == 0:
        footer = hunts_left_footer(updated, day)
        from utils.hunting import weather_hunt_modifier_label

        notes = [n for n in (sniff_note, season_note, mood_note, hunger_note, thirst_note, exhaustion_note) if n]
        weather_note = weather_hunt_modifier_label(world["weather"])
        if weather_note:
            notes.insert(0, weather_note)
        if hunt_penalty:
            notes.append(hunt_penalty)
        if notes:
            footer += " · " + " · ".join(notes)
        from engine.nursing import is_nursing_mother

        if is_nursing_mother(updated):
            footer += " · Nursing dam: eat extra from `/food`; lactation drains hunger each sunrise"
        embed.set_footer(text=footer)
    _append_notes_to_footer(embed, fatigue)
    from engine.disease_contract import try_hunt_flea_exposure, try_insect_sting_exposure

    hazard = try_hunt_flea_exposure(user, day=day) or try_insect_sting_exposure(user, chance=0.05)
    if hazard:
        embed.description = (embed.description or "") + f"\n\n{hazard}"
    if net_amount <= 0:
        from engine.injury_effects import try_prey_counter_injury
        injury_note = try_prey_counter_injury(updated, net_amount, day)
        if injury_note:
            embed.description = (embed.description or "") + f"\n\n{injury_note}"
    # Surgery rest violation: hunting within surgery rest window extends rest and risks reopening.
    from engine.herb_buffs import get_buffs as _get_buffs_h, merge_buff_fields as _mbf_sr
    _h_buffs = _get_buffs_h(user)
    _rest_until = _h_buffs.get("surgery_rest_until_day", 0)
    if _rest_until and int(_rest_until) >= day:
        import random as _rand_sr
        _sr_user = db.get_user(interaction.user.id)
        if _sr_user:
            _new_rest = int(_rest_until) + 2
            _ext_fields = _mbf_sr(_sr_user, surgery_rest_until_day=_new_rest)
            db.update_user_by_id(_sr_user["id"], **_ext_fields)
            embed.description = (embed.description or "") + f"\n\n_over-exertion; rest window extended to sunrise **{_new_rest}**._"
            if _rand_sr.random() < 0.30:
                import json as _json_sr
                from engine.conditions import parse_injuries as _parse_inj_sr, add_injury as _add_inj_sr
                _sr_user2 = db.get_user(interaction.user.id)
                if _sr_user2:
                    _sr_injs = _parse_inj_sr(_sr_user2["active_injuries"] if "active_injuries" in _sr_user2.keys() else None)
                    if "deep_gash" not in _sr_injs:
                        _sr_injs = _add_inj_sr(_sr_injs, "deep_gash")
                        db.set_user_conditions(interaction.user.id, wolf_id=_sr_user2["id"], active_injuries=_json_sr.dumps(_sr_injs))
                        embed.description = (embed.description or "") + " **deep gash** re-opens."
    # Concussion escalation: strenuous activity worsens untreated concussion.
    from engine.conditions import parse_injuries as _parse_conc
    _conc_injs = _parse_conc(user["active_injuries"] if "active_injuries" in user.keys() else None)
    if "concussion" in _conc_injs and "swollen_eye" not in _conc_injs:
        import random as _rand_conc
        if _rand_conc.random() < 0.30:
            import json as _json_conc
            from engine.conditions import add_injury as _add_conc
            _conc_fresh = db.get_user(interaction.user.id)
            if _conc_fresh:
                _conc_list = _parse_conc(_conc_fresh["active_injuries"] if "active_injuries" in _conc_fresh.keys() else None)
                _conc_list = _add_conc(_conc_list, "swollen_eye")
                db.set_user_conditions(interaction.user.id, wolf_id=_conc_fresh["id"], active_injuries=_json_conc.dumps(_conc_list))
                embed.description = (embed.description or "") + "\n\n_running with a concussion; the blow to the eye socket swells; **swollen eye** early onset._"
    # Heat exhaustion: summer hunts at exhaustion ≥ 3 risk +1 exhaustion (10%, DC 10 CON save).
    _world_season = world["season"] if "season" in world.keys() else None
    _u_exhaustion = int(user["exhaustion"]) if "exhaustion" in user.keys() else 0
    if _world_season == "summer" and _u_exhaustion >= 3:
        import random as _rand_he
        if _rand_he.random() < 0.10:
            from engine.rolls import roll_d20 as _roll_he
            from engine.character import attr_modifier as _amod_he
            from engine.exhaustion_effects import EXHAUSTION_MAX as _EXMAX_HE
            _con_mod = _amod_he(int(user["attr_con"]) if "attr_con" in user.keys() else 5)
            _heat_roll = _roll_he() + _con_mod
            if _heat_roll < 10:
                _he_user = db.get_user(interaction.user.id)
                if _he_user:
                    _new_ex = min(_EXMAX_HE, int(_he_user["exhaustion"]) + 1)
                    db.set_user_conditions(interaction.user.id, wolf_id=_he_user["id"], exhaustion=_new_ex)
                    embed.description = (embed.description or "") + f"\n\n_summer heat strain (con **{_heat_roll}** vs dc **10**); **+1 exhaustion** (now **{_new_ex}/{_EXMAX_HE}**)._"
    return embed, net_amount > 0, None


def try_scavenge(interaction: discord.Interaction) -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("server only", "use this in a server.", color=ERROR_COLOR)
    world = db.get_world(guild_id)
    day = world["day_number"]
    injured = _strenuous_injury_embed(user)
    if injured:
        return injured
    blocked = _activity_block_embed(user, title="cannot scavenge", day=day, action="scavenge")
    if blocked:
        return blocked
    from engine.energy import spend_energy
    _new_energy, _had_energy, scavenge_penalty = spend_energy(user, "scavenge")
    gross = roll_range(SCAVENGE_BONES)
    gross, sniff_bonus, sniff_note = apply_sniff_bone_bonus(user, gross, day)
    from engine.shop_items import raven_companion_scavenge_bonus
    gross, raven_scavenge_bonus = raven_companion_scavenge_bonus(user["discord_id"], gross)
    raven_scavenge_note = f"raven companion (+{raven_scavenge_bonus} bones)" if raven_scavenge_bonus > 0 else ""
    net, tax, _, _, mood_note, hunger_note, thirst_note, exhaustion_note, season_note = award_bones(
        user, gross, world["weather"], "scavenge", season=world["season"], guild_id=guild_id
    )
    db.update_user(interaction.user.id, last_scavenge_day=day)
    fatigue = _activity_fatigue_note(db.get_user(interaction.user.id), "scavenge", day)
    gid = interaction.guild.id if interaction.guild else None
    db.increment_quest_progress(interaction.user.id, "scavenge", guild_id=gid)
    scavenge_food_note = ""
    if net > 0:
        grant_prey_carcass_canonical(
            user["id"],
            guild_id=guild_id,
            day=day,
            prey_key="carrion",
        )
        if random.random() < 0.30:
            food_key = random.choice(["berries", "windfall_fruit", "roots", "forage_greens"])
            food_name = grant_prey_carcass_canonical(
                user["id"], guild_id=guild_id, day=day, prey_key=food_key
            )
            scavenge_food_note = f"nosed out **{food_name}** too (`/eat`)"
    updated = db.get_user(interaction.user.id)
    title = "empty paws" if net == 0 else random.choice(SCAVENGE_TEXT)
    embed = howlbert_embed(title, color=SUCCESS_COLOR if net else ERROR_COLOR)
    embed.add_field(name="earned", value=format_bones(net, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="pack tax", value=format_bones(tax), inline=True)
    embed.add_field(name="balance", value=format_bones(updated["bones"]), inline=True)
    if net > 0:
        from engine.disease_contract import try_scavenge_filth_exposure

        filth = try_scavenge_filth_exposure(user, day=day)
        notes = [n for n in (scavenge_food_note, season_note, mood_note, hunger_note, thirst_note, exhaustion_note, filth, sniff_note, raven_scavenge_note, scavenge_penalty) if n]
        footer = "old carrion in hoard (`/food`) · rotting meat risks gut sickness"
        if notes:
            footer += " · " + " · ".join(notes)
        embed.set_footer(text=footer)
    else:
        footer = "nothing worth carrying home this time."
        notes = [n for n in (season_note, mood_note, hunger_note, thirst_note, exhaustion_note, sniff_note, scavenge_penalty) if n]
        if notes:
            footer += " · " + " · ".join(notes)
        embed.set_footer(text=footer)
    _append_notes_to_footer(embed, fatigue)
    return embed


def try_track(
    interaction: discord.Interaction,
    *,
    trail_age: str = "recent",
) -> tuple[discord.Embed | None, bool]:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR), False
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("server only", "use this in a server.", color=ERROR_COLOR), False
    world = db.get_world(guild_id)
    day = world["day_number"]
    injured = _strenuous_injury_embed(user)
    if injured:
        return injured, False
    blocked = _activity_block_embed(user, title="cannot track", day=day, action="track")
    if blocked:
        return blocked, False
    from engine.energy import spend_energy
    _new_energy, _had_energy, track_penalty = spend_energy(user, "track")

    trail_map = {
        "fresh": "track_fresh",
        "recent": "track_recent",
        "cold": "track_cold",
        "very_cold": "track_very_cold",
        "faint": "track_faint",
    }
    scenario_key = trail_map.get(trail_age, "track_recent")
    from engine.skill_runner import run_skill_scenario

    rained = world["weather"] in ("rain", "sleet", "storm", "thunderstorm", "snow")
    sniff_red = sniff_track_fail_reduction(user, day)
    ok, track_msg, _ = run_skill_scenario(
        user,
        scenario_key,
        day=day,
        weather=world["weather"],
        time_of_day=world["time_of_day"],
        rained=rained,
        season=world["season"],
        sniff_dc_reduction=sniff_red,
    )
    if not ok:
        db.update_user(interaction.user.id, last_track_day=day)
        embed = howlbert_embed("trail lost", track_msg, color=ERROR_COLOR)
        footer = "try `/field action:sniff` before tracking again."
        if track_penalty:
            footer += f" · {track_penalty}"
        embed.set_footer(text=footer)
        return embed, False

    wis_bonus = max(0, attr_modifier(get_attr(user, "wis")))
    gross = roll_range(TRACK_BONES) + wis_bonus
    gross, sniff_bonus, sniff_note = apply_sniff_bone_bonus(user, gross, day)
    from engine.shop_items import raven_companion_track_bonus
    gross, raven_track_bonus = raven_companion_track_bonus(user["discord_id"], gross)
    raven_track_note = f"raven companion (+{raven_track_bonus} bones)" if raven_track_bonus > 0 else ""
    net, tax, payout, _, mood_note, hunger_note, thirst_note, exhaustion_note, season_note = award_bones(
        user, gross, world["weather"], "track", season=world["season"], guild_id=guild_id
    )
    if net > 0:
        flavor, track_prey_key = random.choice(TRACK_OUTCOMES)
    else:
        flavor = random.choice(TRACK_MISS_FLAVOR)
        track_prey_key = None
    db.update_user(
        interaction.user.id,
        last_track_day=day,
        last_hunt_yield=payout if payout > 0 else 0,
        last_prey_label=PREY_LABEL_HARE if track_prey_key == "hare" else None,
    )
    db.increment_quest_progress(interaction.user.id, "track")
    if net > 0:
        prey_name = grant_prey_carcass_canonical(
            user["id"],
            guild_id=guild_id,
            day=day,
            prey_key=track_prey_key,
        )
    updated = db.get_user(interaction.user.id)
    title = "track success" if net > 0 else "empty paws"
    embed = howlbert_embed(title, color=SUCCESS_COLOR if net > 0 else ERROR_COLOR)
    embed.description = f"{track_msg}\n\n_{flavor}_"
    embed.add_field(name="earned", value=format_bones(net, signed=True), inline=True)
    if sniff_bonus > 0:
        embed.add_field(name="sniff bonus", value=format_bones(sniff_bonus, signed=True), inline=True)
    if raven_track_bonus > 0:
        embed.add_field(name="raven bonus", value=format_bones(raven_track_bonus, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="pack tax", value=format_bones(tax), inline=True)
    embed.add_field(name="balance", value=format_bones(updated["bones"]), inline=True)
    if net > 0:
        footer = f"{prey_name} in hoard (`/food`) · `/preypile` to share at the den"
        notes = [n for n in (raven_track_note, sniff_note, season_note, mood_note, hunger_note, thirst_note, exhaustion_note, track_penalty) if n]
        if notes:
            footer += " · " + " · ".join(notes)
        from engine.nursing import is_nursing_mother

        if is_nursing_mother(updated):
            footer += " · Nursing dam: eat extra from `/food`; lactation drains hunger each sunrise"
        embed.set_footer(text=footer)
    else:
        footer = "the trail goes cold."
        notes = [n for n in (raven_track_note, sniff_note, season_note, mood_note, hunger_note, thirst_note, exhaustion_note, track_penalty) if n]
        if notes:
            footer += " · " + " · ".join(notes)
        embed.set_footer(text=footer)
    from engine.disease_contract import try_insect_sting_exposure

    sting = try_insect_sting_exposure(user, chance=0.06)
    if sting:
        embed.description = (embed.description or "") + f"\n\n{sting}"
    return embed, net > 0


def try_fishing(interaction: discord.Interaction) -> tuple[discord.Embed | None, bool]:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR), False
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("server only", "use this in a server.", color=ERROR_COLOR), False
    world = db.get_world(guild_id)
    day = world["day_number"]
    injured = _strenuous_injury_embed(user)
    if injured:
        return injured, False
    blocked = _activity_block_embed(user, title="cannot fish", day=day, action="fishing")
    if blocked:
        return blocked, False
    from engine.energy import spend_energy
    _new_energy, _had_energy, fishing_penalty = spend_energy(user, "fishing")
    gross = roll_range(FISHING_BONES)
    gross, sniff_bonus, sniff_note = apply_sniff_bone_bonus(user, gross, day)
    net, tax, payout, _, mood_note, hunger_note, thirst_note, exhaustion_note, season_note = award_bones(
        user, gross, world["weather"], "fishing", season=world["season"], guild_id=guild_id
    )
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    from engine.fishing import pick_fishing_catch
    from engine.world import conditions_snippet, effective_time_of_day

    catch = None
    live_tod = effective_time_of_day(world)
    if net > 0:
        catch = pick_fishing_catch(
            great_pack=gp,
            time_of_day=live_tod,
            weather=world["weather"],
            season=world["season"],
        )
    db.update_user(
        interaction.user.id,
        last_fishing_day=day,
        last_hunt_yield=payout if payout > 0 else 0,
        last_prey_label=catch["label"] if catch else PREY_LABEL_FISH,
    )
    fatigue = _activity_fatigue_note(db.get_user(interaction.user.id), "fish", day)
    gid = interaction.guild.id if interaction.guild else None
    db.increment_quest_progress(interaction.user.id, "fishing", guild_id=gid)
    prey_name = None
    if net > 0 and catch:
        prey_name = grant_prey_carcass_canonical(
            user["id"],
            guild_id=guild_id,
            day=day,
            prey_key=catch["prey_key"],
        )
    updated = db.get_user(interaction.user.id)
    if net > 0 and catch:
        title = "legendary catch!" if catch["rarity"] == "legendary" else "river catch"
        body = catch["flavor"]
    else:
        title = "empty paws"
        body = random.choice(FISHING_FAIL_FLAVOR)
    embed = howlbert_embed(title, body, color=SUCCESS_COLOR if net else ERROR_COLOR)
    embed.add_field(name="earned", value=format_bones(net, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="pack tax", value=format_bones(tax), inline=True)
    embed.add_field(name="balance", value=format_bones(updated["bones"]), inline=True)
    if net > 0 and prey_name:
        wx = world["weather"]
        tod = live_tod
        footer = (
            f"{prey_name} in hoard (`/food`) · `/preypile` to share · "
            f"{conditions_snippet(tod, wx)}"
        )
        if season_note or mood_note or hunger_note or thirst_note or exhaustion_note or sniff_note or fishing_penalty:
            footer += " · " + " · ".join(
                n for n in (season_note, mood_note, hunger_note, thirst_note, exhaustion_note, sniff_note, fishing_penalty) if n
            )
        from engine.nursing import is_nursing_mother

        if is_nursing_mother(updated):
            footer += " · Nursing dam: eat extra from `/food`; lactation drains hunger each sunrise"
        embed.set_footer(text=footer)
        from engine.disease_contract import try_snake_venom_exposure

        snake = try_snake_venom_exposure(user, chance=0.07)
        if snake:
            embed.description = (embed.description or "") + f"\n\n{snake}"
    else:
        footer = "pack waters shift with weather and time (`/world`)."
        if season_note or mood_note or hunger_note or thirst_note or sniff_note or fishing_penalty:
            footer = " · ".join(
                n for n in (season_note, mood_note, hunger_note, thirst_note, exhaustion_note, sniff_note, fishing_penalty) if n
            ) + " · " + footer
        embed.set_footer(text=footer)
    _append_notes_to_footer(embed, fatigue)
    return embed, net > 0


def try_forage(interaction: discord.Interaction, rarity: str = "common") -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("server only", "use this in a server.", color=ERROR_COLOR)
    world = db.get_world(guild_id)
    day = world["day_number"]
    blocked = _activity_block_embed(user, title="cannot forage")
    if blocked:
        return blocked
    from engine.energy import spend_energy
    from engine.role_privileges import is_full_forager
    _new_energy, _had_energy, forage_penalty = spend_energy(
        user, "forage", discounted=is_full_forager(user)
    )
    from engine.forager_perk import grant_forager_auto_herb

    auto_herb = grant_forager_auto_herb(user, day=day, guild_id=guild_id)
    forager_note = (
        f"\n\n_forager perk: **{auto_herb}** turned up in pack territory._" if auto_herb else ""
    )
    forage_penalty_note = f"\n\n_{forage_penalty}_" if forage_penalty else ""
    dc = FORAGE_RARITY_DC[rarity] + season_forage_dc_mod(world["season"])
    season_note = season_forage_modifier_label(world["season"])
    season_suffix = f"\n_{season_note}_" if season_forage_dc_mod(world["season"]) else ""
    profs = parse_proficiencies(user["skill_proficiencies"])
    from engine.role_privileges import forage_check_params, forage_sunrise_footer

    attr_keys, skill_label, skill_key, proficient = forage_check_params(user, profs)
    result = resolve_check(
        user,
        attr_keys=attr_keys,
        skill=skill_label,
        dc=dc,
        proficient=proficient,
        skill_key=skill_key,
        game_day=day,
    )
    db.update_user(interaction.user.id, last_forage_day=day)
    from engine.rotting_mere import is_rotting_mere, try_rotting_mere_exposure

    at_mere = is_rotting_mere(user)
    mere_note, _role_changed = try_rotting_mere_exposure(user, interaction.user.id) if at_mere else (None, False)
    if _role_changed:
        user = db.get_user(interaction.user.id)
    fatigue = _activity_fatigue_note(db.get_user(interaction.user.id), "forage", day)
    if result["outcome"] == "critical_failure":
        from engine.disease_contract import try_nettle_sting_exposure
        from engine.character import attr_modifier

        nettle_note = try_nettle_sting_exposure(user, chance=0.35) or ""
        # a botched forage always bites: you test-taste a misidentified plant.
        # con save or swallow the toxin and sicken; either way it costs hp.
        con_mod = attr_modifier(int(user["attr_con"]) if "attr_con" in user.keys() else 5)
        save_total = random.randint(1, 20) + con_mod
        if save_total >= 12:
            dmg = 1
            tox_note = f"a bitter mouthful; you spit most of it out in time. **minus 1 hp**. _(con {save_total} vs 12)_"
        else:
            dmg = random.randint(2, 4)
            tox_note = f"you swallow a toxic sample before the taste warns you. **minus {dmg} hp**. _(con {save_total} vs 12)_"
            from engine.disease_contract import try_contract_disease

            gi = try_contract_disease(user, "diarrhea", chance=1.0)
            if gi:
                tox_note += f"\n{gi}"
        new_hp = max(1, int(user["hp"]) - dmg)
        db.set_user_conditions(user["discord_id"], wolf_id=user["id"], hp=new_hp)
        embed = howlbert_embed(
            "misidentified!",
            format_roll_result(result)
            + "\n\nyou gathered the wrong plant and tested it on your tongue.\n"
            + tox_note
            + (f"\n\n{nettle_note}" if nettle_note else "")
            + forager_note
            + season_suffix
            + (f"\n\n{mere_note}" if mere_note else "")
            + forage_penalty_note,
            color=ERROR_COLOR,
        )
        embed.set_footer(text=embed_footer(forage_sunrise_footer(user)))
        _append_notes_to_footer(embed, fatigue)
        return embed
    if not result["success"]:
        from engine.season_effects import maybe_spoil_herb_on_forage_fail

        spoil_note = maybe_spoil_herb_on_forage_fail(user, season=world["season"])
        embed = howlbert_embed(
            "forage failed",
            format_roll_result(result) + forager_note + season_suffix + spoil_note
            + (f"\n\n{mere_note}" if mere_note else "")
            + forage_penalty_note,
            color=ERROR_COLOR,
        )
        embed.set_footer(text=embed_footer(forage_sunrise_footer(user)))
        _append_notes_to_footer(embed, fatigue)
        return embed
    pool = [
        k
        for k, m in HERBS.items()
        if m["rarity"] == rarity
        and m.get("rarity") != "restricted"
        and not m.get("poison")
        and "wild" in m.get("habitat", ("wild",))
    ]
    if user["great_pack"]:
        pack_herbs = [k for k, m in HERBS.items() if user["great_pack"] in m.get("packs", ())]
        if pack_herbs and random.random() < 0.4:
            pool = pack_herbs
    if not pool:
        pool = [
            k
            for k, m in HERBS.items()
            if m["rarity"] == "common" and "wild" in m.get("habitat", ("wild",))
        ]
    herb_key = random.choice(pool)
    if at_mere:
        from engine.rotting_mere import pick_mere_herb
        herb_key = pick_mere_herb()
    meta = HERBS[herb_key]
    item_key, hoard_note = grant_fresh_herb(
        user["id"],
        herb_key=herb_key,
        guild_id=guild_id,
        day=day,
        user=user,
    )
    qty_note = " (double yield!)" if result["outcome"] == "critical_success" else ""
    rare_note = ""
    if result["outcome"] == "critical_success":
        grant_fresh_herb(
            user["id"],
            herb_key=herb_key,
            guild_id=guild_id,
            day=day,
            user=user,
        )
        rare_pool = [
            k
            for k, m in HERBS.items()
            if m.get("rarity") in ("rare", "very_rare")
            and not m.get("poison")
            and m.get("rarity") != "restricted"
            and "wild" in m.get("habitat", ("wild",))
        ]
        if rare_pool and random.random() < 0.55:
            rare_key = random.choice(rare_pool)
            rare_meta = HERBS[rare_key]
            rare_key_item, _ = grant_fresh_herb(
                user["id"],
                herb_key=rare_key,
                guild_id=guild_id,
                day=day,
                user=user,
            )
            from engine.season_effects import season_activity_blurb

            rare_note = (
                f"\n\n**critical find**: **{rare_meta['name']}** (`{rare_key_item}`) "
                f"turned up in the undergrowth.\n_{season_activity_blurb(world['season'])}_"
            )
    db.increment_quest_progress(interaction.user.id, "forage")
    auto_note = forager_note
    seed_note = ""
    from config import GARDEN_FORAGE_SEED_CHANCE
    from engine.herb_growing import can_cultivate

    if can_cultivate(herb_key) and random.random() < GARDEN_FORAGE_SEED_CHANCE:
        db.add_herb_seeds(user["id"], herb_key)
        seed_note = f"\n\nyou also pocket a few **{meta['name']} seeds** for the den garden (`/garden plant`)."
    food_note = ""
    from engine.prey_items import seasonal_forage_food

    food_chance = 0.65 if result["outcome"] == "critical_success" else 0.45
    if random.random() < food_chance:
        food_key = seasonal_forage_food(world["season"])
        if food_key:
            from engine.hunt_payout import grant_prey_carcass_canonical

            food_name = grant_prey_carcass_canonical(
                user["id"], guild_id=guild_id, day=day, prey_key=food_key
            )
            food_note = f"\n\nyou also browse **{food_name}** to eat (`/food` · `/eat`)."
    from engine.disease_contract import try_insect_sting_exposure

    insect_chance = 0.11 if world["season"] == "summer" else 0.07
    sting_note = try_insect_sting_exposure(user, chance=insect_chance) or ""
    nettle_note = ""
    if herb_key == "stinging_nettle":
        from engine.disease_contract import try_nettle_sting_exposure

        nettle_note = try_nettle_sting_exposure(user, chance=0.5) or ""
    embed = howlbert_embed(
        "forage success",
        format_roll_result(result)
        + f"\n\nfound **{meta['name']}**{qty_note}: added to `/bones action:inventory` (`{item_key}`)."
        + f"\n_{meta['effect']}_"
        + fresh_herb_warning(herb_key)
        + (f"\n\n{hoard_note}" if hoard_note else "")
        + rare_note
        + auto_note
        + seed_note
        + food_note
        + season_suffix
        + (f"\n\n{sting_note}" if sting_note else "")
        + (f"\n\n{nettle_note}" if nettle_note else "")
        + (f"\n\n{mere_note}" if mere_note else "")
        + forage_penalty_note,
        color=SUCCESS_COLOR,
    )
    embed.set_footer(text=embed_footer(forage_sunrise_footer(user, success_hint=True)))
    _append_notes_to_footer(embed, fatigue)
    return embed


def purchase_item(interaction: discord.Interaction, item_key: str) -> discord.Embed | None:
    from engine.shop_purchase import purchase_shop_item

    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    shop_item = db.get_item_by_key(item_key)
    if not shop_item or shop_item["price"] <= 0:
        return howlbert_embed("unknown item", "check `/bones action:shop` for valid items.", color=ERROR_COLOR)

    guild_id = interaction.guild.id if interaction.guild else None
    day = db.get_world(guild_id)["day_number"] if guild_id else 0
    ok, note, item_name = purchase_shop_item(
        interaction.user.id,
        item_key,
        guild_id=guild_id,
        day=day,
    )
    if not ok:
        return howlbert_embed(note if note != "not enough bones." else "not enough bones", color=ERROR_COLOR)
    updated = db.get_user(interaction.user.id)
    embed = howlbert_embed("purchased", note, color=SUCCESS_COLOR)
    embed.add_field(name="item", value=item_name or shop_item["name"], inline=True)
    embed.add_field(name="spent", value=format_bones(shop_item["price"]), inline=True)
    embed.add_field(name="balance", value=format_bones(updated["bones"]), inline=True)
    key = shop_item["key"]
    footer_bits = ["/bones action:inventory"]
    if key.startswith("prey_"):
        footer_bits.append("/food")
    elif key.startswith("toy_"):
        footer_bits.append("/playpen action:toys")
    elif key.startswith("herb_"):
        footer_bits.append("/herbs action:dryall · action:prepare")
    elif key in ("herb_bundle", "prey_bundle", "den_charm"):
        footer_bits.append("/bones action:use item:<key>")
    embed.set_footer(text=" · ".join(footer_bits))
    return embed


def accept_quest(interaction: discord.Interaction, quest_key: str) -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    q = db.get_quest_by_key(quest_key)
    if not q or q["quest_type"] == "daily":
        return howlbert_embed("unknown quest", "that key isn't on the den board.", color=ERROR_COLOR)
    req_pack = q["required_pack"] if "required_pack" in q.keys() else None
    if req_pack:
        wolf_pack = user["great_pack"] if "great_pack" in user.keys() else None
        if wolf_pack != req_pack:
            return howlbert_embed(
                "wrong pack",
                f"this tradition requires the **{req_pack.title()}** great pack.",
                color=ERROR_COLOR,
            )
    req_role = q["required_role"] if "required_role" in q.keys() else None
    if req_role:
        from engine.apprentice_roles import quest_role_matches
        from rpg_rules import ROLE_LABELS

        wolf_role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
        if not quest_role_matches(wolf_role, req_role):

            return howlbert_embed(
                "wrong role",
                f"this quest is for **{ROLE_LABELS.get(req_role, req_role)}** wolves only.",
                color=ERROR_COLOR,
            )
    elif q["quest_type"] == "role":
        return howlbert_embed("role quest", "use `/role action:quests` for role-specific quests.", color=ERROR_COLOR)
    if q["quest_type"] == "unique" and db.has_completed_unique(interaction.user.id, q["id"]):
        return howlbert_embed("already done", "that tale is already written.", color=ERROR_COLOR)
    guild_id = interaction.guild.id if interaction.guild else None
    if q["key"].startswith("blink_"):
        from engine.plot_quests import plot_quest_available

        if not plot_quest_available(q["key"], guild_id):
            return howlbert_embed(
                "not yet",
                "that **book one** quest isn't on the den board for the current plot phase.",
                color=ERROR_COLOR,
            )
        if q["key"] == "blink_rogue_ledger":
            from engine.role_features import is_rogue_wolf

            if not is_rogue_wolf(user):
                return howlbert_embed(
                    "rogues only",
                    "**edge ledger** is for **rogue** wolves running border scores.",
                    color=ERROR_COLOR,
                )
    day = db.get_world(guild_id)["day_number"] if guild_id else 0
    if not db.accept_quest(interaction.user.id, q["id"], day, guild_id=guild_id):
        return howlbert_embed("already active", "you're already on that quest.", color=ERROR_COLOR)
    embed = howlbert_embed("quest accepted", q["description"], color=SUCCESS_COLOR)
    embed.add_field(name="objective", value=f"{q['objective_type']} x{q['objective_count']}", inline=True)
    from engine.quest_rewards import format_quest_reward_line

    embed.add_field(name="reward", value=format_quest_reward_line(q["key"], q["reward_bones"]), inline=True)
    return embed


def complete_quest(interaction: discord.Interaction, quest_key: str | None = None) -> discord.Embed | None:
    if not db.get_user(interaction.user.id):
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    result = db.complete_quest(interaction.user.id, quest_key)
    if not result:
        if quest_key:
            active = db.get_active_quest_by_key(interaction.user.id, quest_key)
            if active:
                return howlbert_embed(
                    "not ready",
                    f"**{active['title']}**: "
                    f"**{active['progress']}/{active['objective_count']}** "
                    f"({active['objective_type']}). "
                    "Do the objective after accepting, or abandon and re-accept if you already "
                    "finished that action today.",
                    color=ERROR_COLOR,
                )
        return howlbert_embed("not ready", "quest objectives not finished yet.", color=ERROR_COLOR)
    embed = howlbert_embed("quest complete", color=SUCCESS_COLOR)
    embed.add_field(name="quest", value=result["title"], inline=False)
    embed.add_field(name="bones", value=format_bones(result["reward_bones"], signed=True), inline=True)
    embed.add_field(name="standing", value=f"+{result['standing_reward']}", inline=True)
    from engine.quest_rewards import format_quest_reward_suffix, quest_xp_reward, quest_skill_reward

    xp_gain = quest_xp_reward(
        result["quest_key"],
        difficulty=result["difficulty"] if "difficulty" in result.keys() else None,
    )
    embed.add_field(name="xp", value=f"+{xp_gain}", inline=True)
    skill_reward = quest_skill_reward(result["quest_key"])
    if skill_reward:
        from rpg_rules import SKILLS, SKILL_RANK_BONUS

        skill_key, rank_gain = skill_reward
        label = SKILLS.get(skill_key, ((), skill_key))[1]
        embed.add_field(
            name="skill",
            value=f"**{label}** rank +{rank_gain} (+{SKILL_RANK_BONUS}/rank on checks)",
            inline=False,
        )
    extra = format_quest_reward_suffix(
        result["quest_key"],
        difficulty=result["difficulty"] if "difficulty" in result.keys() else None,
    )
    if extra:
        embed.set_footer(text=f"rewards: {extra}")
    return embed


def _apply_extra_paw(
    interaction: discord.Interaction,
    embed: discord.Embed,
    *,
    scene: str | None,
    staff: bool,
) -> discord.Embed | None:
    """Attach RP scene from An Extra Paw, or return an error embed."""
    if not scene and not staff:
        return embed
    if not has_item(interaction.user.id, "extra_paw"):
        return howlbert_embed(
            "an extra paw required",
            "buy **an extra paw** from `/bones action:shop` to add a custom `scene:` or `staff:true` "
            "to `/bones action:work` or `/bones action:crime`.",
            color=ERROR_COLOR,
        )
    if not consume_item_by_key(interaction.user.id, "extra_paw"):
        return howlbert_embed("item missing", "you don't have **an extra paw**.", color=ERROR_COLOR)
    if scene:
        text = scene.strip()[:1000]
        embed.add_field(name="🐾 your scene", value=text, inline=False)
    if staff:
        embed.add_field(
            name="🐾 staff rp",
            value="an admin will weave your wolf into this scene.",
            inline=False,
        )
    return embed


def try_work(
    interaction: discord.Interaction,
    *,
    scene: str | None = None,
    staff: bool = False,
) -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("server only", "use this in a server.", color=ERROR_COLOR)
    world = db.get_world(guild_id)
    day = world["day_number"]
    blocked = _activity_block_embed(user, title="cannot work")
    if blocked:
        return blocked
    from engine.energy import spend_energy

    _new_energy, _had_energy, work_penalty = spend_energy(user, "work")
    gross = roll_range(WORK_BONES)
    net, tax, _, _, _, _, _, _, _ = award_bones(user, gross, world["weather"], "work")
    db.update_user(interaction.user.id, last_work_day=day)
    updated = db.get_user(interaction.user.id)
    title = "empty paws" if net == 0 else random.choice(WORK_TEXT)
    embed = howlbert_embed(title, color=SUCCESS_COLOR if net else ERROR_COLOR)
    embed.add_field(name="earned", value=format_bones(net, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="pack tax", value=format_bones(tax), inline=True)
    embed.add_field(name="balance", value=format_bones(updated["bones"]), inline=True)
    if work_penalty:
        embed.set_footer(text=embed_footer(work_penalty))
    elif net == 0:
        embed.set_footer(text=embed_footer("today's work turned up nothing; try again."))
    return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)


def try_crime(
    interaction: discord.Interaction,
    *,
    target_pack: str | None = None,
    target_wolf: "discord.Member | None" = None,
    victim_row=None,
    raid_type: str = "bones",
    scene: str | None = None,
    staff: bool = False,
) -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
    block = young_wolf_block(user, action="crime")
    if block:
        return howlbert_embed("too young", block, color=ERROR_COLOR)
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("server only", "use this in a server.", color=ERROR_COLOR)
    world = db.get_world(guild_id)
    day = world["day_number"]
    blocked = _activity_block_embed(user, title="cannot run a score")
    if blocked:
        return blocked
    from engine.energy import spend_energy
    _new_energy, _had_energy, crime_penalty = spend_energy(user, "crime")

    if target_pack:
        return _try_cross_pack_steal(
            interaction,
            user,
            day=day,
            target_pack=target_pack,
            raid_type=raid_type,
            scene=scene,
            staff=staff,
            crime_penalty=crime_penalty,
        )

    if victim_row is not None:
        return _try_individual_steal(
            interaction,
            user,
            day=day,
            victim_row=victim_row,
            scene=scene,
            staff=staff,
            crime_penalty=crime_penalty,
        )

    if target_wolf:
        return _try_individual_steal(
            interaction,
            user,
            day=day,
            target_wolf=target_wolf,
            scene=scene,
            staff=staff,
            crime_penalty=crime_penalty,
        )

    db.update_user(interaction.user.id, last_crime_day=day)

    from engine.plot_blinking import try_plot_rogue_crime

    gross = roll_range(CRIME_BONES)
    gross, plot_suffix, plot_caught = try_plot_rogue_crime(
        interaction, user, day=day, gross=gross
    )
    if plot_caught:
        embed = howlbert_embed("caught on the border", plot_caught, color=ERROR_COLOR)
        embed.set_footer(text="no bones earned. the den remembers.")
        return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)

    if roll_crime_caught():
        kick = db.adjust_wolf_standing(interaction.user.id, crime_caught_standing())
        embed = howlbert_embed("caught", pick_crime_caught_flavor(), color=ERROR_COLOR)
        embed.add_field(
            name="standing",
            value=(
                f"{crime_caught_standing()} "
                + ("- **cast out** as loner" if kick == "kicked" else "")
            ),
            inline=False,
        )
        embed.set_footer(text="no bones earned. the den remembers.")
        return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)

    net, tax, _, _, _, _, _, _, _ = award_bones(
        user, gross, world["weather"], "crime", guild_id=guild_id
    )
    gid = interaction.guild.id if interaction.guild else None
    db.increment_quest_progress(interaction.user.id, "crime", guild_id=gid)
    updated = db.get_user(interaction.user.id)
    body = random.choice(CRIME_TEXT)
    if plot_suffix:
        body += plot_suffix
    title = "empty paws" if net == 0 else "score pulled"
    embed = howlbert_embed(title, body, color=SUCCESS_COLOR if net else ERROR_COLOR)
    embed.add_field(name="earned", value=format_bones(net, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="pack tax", value=format_bones(tax), inline=True)
    embed.add_field(name="balance", value=format_bones(updated["bones"]), inline=True)
    if crime_penalty:
        embed.set_footer(text=embed_footer(crime_penalty))
    elif net == 0:
        embed.set_footer(text=embed_footer("nothing worth taking this time."))
    return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)


def _try_individual_steal(
    interaction: discord.Interaction,
    user,
    *,
    day: int,
    target_wolf: "discord.Member | None" = None,
    victim_row=None,
    scene: str | None,
    staff: bool,
    crime_penalty: str = "",
) -> discord.Embed | None:
    from config import INDIVIDUAL_STEAL_PCT, INDIVIDUAL_STEAL_RIVALRY_GAIN

    if victim_row is None:
        if target_wolf.id == interaction.user.id:
            return howlbert_embed("your own paws", "you can't pick your own pocket.", color=ERROR_COLOR)
        victim_row = db.get_user(target_wolf.id)
        if not victim_row:
            return howlbert_embed("no wolf", f"**{target_wolf.display_name}** has no registered wolf.", color=ERROR_COLOR)

    victim = victim_row

    if int(victim["bones"]) <= 0:
        return howlbert_embed(
            "empty pockets",
            f"**{victim['wolf_name']}** has no bones worth lifting.",
            color=ERROR_COLOR,
        )

    db.update_user(interaction.user.id, last_crime_day=day)

    from engine.role_features import is_full_medic
    targeting_medic = is_full_medic(victim)

    if roll_individual_steal_caught():
        penalty = individual_steal_caught_standing()
        kick = db.adjust_wolf_standing(interaction.user.id, penalty)
        db.adjust_bond_strength(user["id"], victim["id"], "rivalry", INDIVIDUAL_STEAL_RIVALRY_GAIN, day=day)
        embed = howlbert_embed(
            "caught red-pawed",
            f"**{victim['wolf_name']}** wakes mid-theft and snaps at your heels.",
            color=ERROR_COLOR,
        )
        embed.add_field(
            name="standing",
            value=f"{penalty}" + ("; **cast out** as loner" if kick == "kicked" else ""),
            inline=False,
        )
        if targeting_medic:
            from engine.healer_code import apply_medic_neutrality_violated
            medic_note = apply_medic_neutrality_violated(interaction.user.id, victim)
            embed.add_field(name="Healer's Neutrality", value=medic_note, inline=False)
        footer = f"no bones taken from {victim['wolf_name']}. rivalry deepens."
        if crime_penalty:
            footer += f" · {crime_penalty}"
        embed.set_footer(text=footer)
        return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)

    pct = random.uniform(*INDIVIDUAL_STEAL_PCT)
    attempted = max(1, int(int(victim["bones"]) * pct))
    stolen_ok = db.transfer_bones_by_wolf_id(victim["id"], user["id"], attempted)
    if not stolen_ok:
        return howlbert_embed(
            "raid failed",
            f"**{victim['wolf_name']}**'s stash was lighter than it looked.",
            color=ERROR_COLOR,
        )

    standing_gain = individual_steal_standing()
    db.adjust_wolf_standing(interaction.user.id, standing_gain)
    db.adjust_bond_strength(user["id"], victim["id"], "rivalry", INDIVIDUAL_STEAL_RIVALRY_GAIN, day=day)
    updated = db.get_user(interaction.user.id)
    embed = howlbert_embed(
        "score pulled",
        f"you lift **{format_bones(attempted)}** off of **{victim['wolf_name']}** while they're not looking.",
        color=SUCCESS_COLOR,
    )
    embed.add_field(name="stolen", value=format_bones(attempted, signed=True), inline=True)
    embed.add_field(name="standing", value=f"+{standing_gain}", inline=True)
    embed.add_field(name="balance", value=format_bones(updated["bones"]), inline=True)
    if targeting_medic:
        from config import MAW_MEDIC_CRIME_KARMA
        new_karma = db.adjust_maw_karma(interaction.user.id, MAW_MEDIC_CRIME_KARMA)
        maw_note = (
            "the Maw's eye does not leave you; **divine displeasure grows**."
            if new_karma >= 10
            else "the healer's sanctity was violated; the Maw saw what you did in the dark."
        )
        embed.add_field(name="the Great Maw watches", value=maw_note, inline=False)
    footer = f"{victim['wolf_name']} won't forget this. rivalry deepens."
    if crime_penalty:
        footer += f" · {crime_penalty}"
    embed.set_footer(text=footer)
    return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)


def _try_cross_pack_steal(
    interaction: discord.Interaction,
    user,
    *,
    day: int,
    target_pack: str,
    raid_type: str = "bones",
    scene: str | None,
    staff: bool,
    crime_penalty: str = "",
) -> discord.Embed | None:
    from config import GREAT_PACKS

    if target_pack not in GREAT_PACKS:
        return howlbert_embed(
            "unknown pack",
            "pick a rival great pack: greyspire, mistmoor, thistlehide, or silverrush.",
            color=ERROR_COLOR,
        )

    own_pack = user["great_pack"] if "great_pack" in user.keys() else None
    if own_pack == target_pack:
        return howlbert_embed(
            "your own den",
            "you can't raid your own pack's stores.",
            color=ERROR_COLOR,
        )
    if not user["pack_id"]:
        return howlbert_embed(
            "no pack",
            "join a great pack to run a den raid; loners use `/bones action:crime` without a target for scraps.",
            color=ERROR_COLOR,
        )

    victim = db.get_pack_by_key(target_pack)
    if not victim:
        return howlbert_embed("pack not found", "join a great pack first.", color=ERROR_COLOR)

    victim_name = GREAT_PACKS[target_pack]["name"]

    if raid_type in ("food", "herbs", "amusement"):
        return _try_cross_pack_goods_steal(
            interaction,
            user,
            day=day,
            victim=victim,
            victim_name=victim_name,
            target_pack=target_pack,
            raid_type=raid_type,
            scene=scene,
            staff=staff,
        )

    if int(victim["treasury"]) <= 0:
        return howlbert_embed(
            "empty stash",
            f"**{victim_name}**'s treasury is bare; nothing to steal this sunrise.",
            color=ERROR_COLOR,
        )

    db.update_user(interaction.user.id, last_crime_day=day)

    from engine.pack_raid_ecology import roll_steal_caught, scaled_steal_attempt

    if roll_steal_caught(target_pack):
        penalty = cross_pack_steal_caught_standing()
        from engine.plot_blinking import plot_cross_pack_caught_standing_extra

        penalty += plot_cross_pack_caught_standing_extra(interaction.guild.id)
        kick = db.adjust_wolf_standing(interaction.user.id, penalty)
        guild_id = interaction.guild.id if interaction.guild else None
        relation_note = ""
        if guild_id and user["pack_id"]:
            new_rel = db.adjust_pack_relation(guild_id, user["pack_id"], victim["id"], -1)
            relation_note = f"\npack standing with **{victim_name}** **−1** (now **{new_rel}/10**)."
            from engine.pack_raid_ecology import record_treasury_raid

            record_treasury_raid(
                guild_id,
                victim_pack_id=victim["id"],
                raider_pack_id=int(user["pack_id"]),
                stolen_amount=0,
                day=day,
                caught=True,
            )
            from engine.wolf_journal import log_raid

            log_raid(
                user["id"],
                user["wolf_name"],
                victim_name,
                caught=True,
                guild_id=guild_id,
                day=day,
            )
        embed = howlbert_embed(
            "caught at the border",
            pick_cross_pack_steal_caught_flavor(victim_name) + relation_note,
            color=ERROR_COLOR,
        )
        embed.add_field(
            name="standing",
            value=f"{penalty}" + ("; **cast out** as loner" if kick == "kicked" else ""),
            inline=False,
        )
        footer = f"no bones taken from {victim_name}."
        if crime_penalty:
            footer += f" · {crime_penalty}"
        embed.set_footer(text=footer)
        return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)

    attempted = scaled_steal_attempt(target_pack, roll_range(CROSS_PACK_STEAL_BONES))
    stolen = db.raid_pack_treasury(interaction.user.id, victim["id"], attempted)
    if stolen <= 0:
        return howlbert_embed(
            "raid failed",
            f"**{victim_name}**'s treasury emptied before you reached it.",
            color=ERROR_COLOR,
        )

    standing_gain = cross_pack_steal_standing()
    db.adjust_wolf_standing(interaction.user.id, standing_gain)
    guild_id = interaction.guild.id if interaction.guild else None
    paranoia_note = ""
    if guild_id and user["pack_id"]:
        from engine.pack_raid_ecology import record_treasury_raid

        record_treasury_raid(
            guild_id,
            victim_pack_id=victim["id"],
            raider_pack_id=int(user["pack_id"]),
            stolen_amount=stolen,
            day=day,
            caught=False,
        )
        from engine.wolf_journal import log_raid

        log_raid(
            user["id"],
            user["wolf_name"],
            victim_name,
            stolen=stolen,
            guild_id=guild_id,
            day=day,
        )
        from engine.plot_blinking import PARANOIA_PHASES, plot_phase
        from config import PARANOIA_RAID_UNITY_PENALTY, PARANOIA_RAID_UNITY_RISK

        if plot_phase(guild_id) in PARANOIA_PHASES and random.random() < PARANOIA_RAID_UNITY_RISK:
            outcome = db.adjust_pack_unity(int(user["pack_id"]), PARANOIA_RAID_UNITY_PENALTY)
            paranoia_note = (
                f"\nden whispers about the raid; pack unity **{PARANOIA_RAID_UNITY_PENALTY}**."
            )
            if outcome == "dissolved":
                paranoia_note += " _(den fractured)_"
    updated = db.get_user(interaction.user.id)
    victim_after = db.get_pack(victim["id"])

    flavor = random.choice(CROSS_PACK_STEAL_TEXT).format(pack=victim_name)
    embed = howlbert_embed("raid successful", flavor + paranoia_note, color=SUCCESS_COLOR)
    embed.add_field(name="stolen", value=format_bones(stolen, signed=True), inline=True)
    embed.add_field(name="den standing", value=f"+{standing_gain}", inline=True)
    embed.add_field(name="your balance", value=format_bones(updated["bones"]), inline=True)
    if victim_after:
        embed.add_field(
            name=f"{victim_name} treasury",
            value=format_bones(victim_after["treasury"]),
            inline=True,
        )
    footer = "your den praises a successful rival raid."
    if crime_penalty:
        footer += f" · {crime_penalty}"
    embed.set_footer(text=footer)
    return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)


def _try_cross_pack_goods_steal(
    interaction: discord.Interaction,
    user,
    *,
    day: int,
    victim,
    victim_name: str,
    target_pack: str,
    raid_type: str,
    scene: str | None,
    staff: bool,
) -> discord.Embed | None:
    """Raid a rival den's communal food reserve, herb store, or toy store (not treasury)."""
    nouns = {"food": "food reserve", "herbs": "herb store", "amusement": "toy store"}
    noun = nouns.get(raid_type, "food reserve")
    if raid_type == "food":
        stacks = db.get_pack_prey_stacks(victim["id"])
    elif raid_type == "amusement":
        stacks = db.get_pack_amusement_stacks(victim["id"])
    else:
        stacks = db.get_pack_herb_stacks(victim["id"])
    if not stacks:
        return howlbert_embed(
            "empty stash",
            f"**{victim_name}**'s {noun} is bare; nothing to steal this sunrise.",
            color=ERROR_COLOR,
        )

    db.update_user(interaction.user.id, last_crime_day=day)

    from engine.pack_raid_ecology import roll_steal_caught

    guild_id = interaction.guild.id if interaction.guild else None

    if roll_steal_caught(target_pack):
        penalty = cross_pack_steal_caught_standing()
        from engine.plot_blinking import plot_cross_pack_caught_standing_extra

        penalty += plot_cross_pack_caught_standing_extra(guild_id)
        kick = db.adjust_wolf_standing(interaction.user.id, penalty)
        relation_note = ""
        if guild_id and user["pack_id"]:
            new_rel = db.adjust_pack_relation(guild_id, user["pack_id"], victim["id"], -1)
            relation_note = f"\npack standing with **{victim_name}** **−1** (now **{new_rel}/10**)."
            from config import RAID_ALERT_SUNRISES

            db.record_pack_raid_alert(
                guild_id,
                victim_pack_id=victim["id"],
                suspect_pack_id=int(user["pack_id"]),
                stolen_amount=0,
                raid_day=day,
                expires_day=day + RAID_ALERT_SUNRISES,
                caught=True,
            )
            from engine.wolf_journal import log_raid

            log_raid(
                user["id"],
                user["wolf_name"],
                victim_name,
                caught=True,
                guild_id=guild_id,
                day=day,
                loot_label=noun,
            )
        embed = howlbert_embed(
            "caught at the border",
            f"a denmate scents you lurking near their {noun}; you bolt before getting a paw on it."
            + relation_note,
            color=ERROR_COLOR,
        )
        embed.add_field(
            name="standing",
            value=f"{penalty}" + ("; **cast out** as loner" if kick == "kicked" else ""),
            inline=False,
        )
        embed.set_footer(text=f"nothing taken from {victim_name}.")
        return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)

    stack = random.choice(stacks)
    if raid_type == "food":
        from engine.prey_items import prey_meta

        meta = prey_meta(stack["prey_key"])
        loot_name = meta["name"]
        loot_value = max(1, int(stack["bone_value"]))
        db.add_prey_stack(
            user["id"],
            stack["prey_key"],
            uses_left=stack["uses_left"],
            bone_value=stack["bone_value"],
            acquired_day=stack["acquired_day"],
            guild_id=stack["guild_id"],
            is_rotting=int(stack["is_rotting"]),
        )
        db.remove_pack_prey_stack(stack["id"])
        loot_line = f"**{loot_name}** dragged off into your own hoard (`/food`)."
    elif raid_type == "amusement":
        from engine.amusement_items import amusement_meta

        meta = amusement_meta(stack["item_key"])
        loot_name = meta["name"]
        loot_value = 5
        db.add_amusement_stack(user["id"], stack["item_key"], uses_left=int(stack["uses_left"]))
        db.remove_pack_amusement_stack(stack["id"])
        loot_line = f"**{loot_name}** snatched into your toys (`/playpen action:toys`)."
    else:
        from herbs import HERBS, herb_inventory_key

        meta = HERBS.get(stack["herb_key"], {})
        loot_name = meta.get("name", stack["herb_key"])
        loot_value = 5
        item_key = herb_inventory_key(stack["herb_key"])
        item = db.get_item_by_key(item_key)
        if not item:
            return howlbert_embed("raid failed", "couldn't carry that herb; try again next sunrise.", color=ERROR_COLOR)
        db.grant_item(user["discord_id"], item["id"], quantity=1)
        qty = int(stack["quantity"])
        if qty <= 1:
            db.remove_pack_herb_stack(stack["id"])
        else:
            db.update_pack_herb_stack(stack["id"], quantity=qty - 1)
        loot_line = f"**{loot_name}** stuffed into your jaws, straight to `/bones action:inventory`."

    standing_gain = cross_pack_steal_standing()
    db.adjust_wolf_standing(interaction.user.id, standing_gain)
    paranoia_note = ""
    if guild_id and user["pack_id"]:
        new_rel = db.adjust_pack_relation(guild_id, user["pack_id"], victim["id"], -1)
        from config import RAID_ALERT_SUNRISES

        db.record_pack_raid_alert(
            guild_id,
            victim_pack_id=victim["id"],
            suspect_pack_id=int(user["pack_id"]),
            stolen_amount=loot_value,
            raid_day=day,
            expires_day=day + RAID_ALERT_SUNRISES,
            caught=False,
        )
        from engine.wolf_journal import log_raid

        log_raid(
            user["id"],
            user["wolf_name"],
            victim_name,
            guild_id=guild_id,
            day=day,
            loot_label=f"{loot_name}",
        )
        from engine.plot_blinking import PARANOIA_PHASES, plot_phase
        from config import PARANOIA_RAID_UNITY_PENALTY, PARANOIA_RAID_UNITY_RISK

        if plot_phase(guild_id) in PARANOIA_PHASES and random.random() < PARANOIA_RAID_UNITY_RISK:
            outcome = db.adjust_pack_unity(int(user["pack_id"]), PARANOIA_RAID_UNITY_PENALTY)
            paranoia_note = f"\nden whispers about the raid; pack unity **{PARANOIA_RAID_UNITY_PENALTY}**."
            if outcome == "dissolved":
                paranoia_note += " _(den fractured)_"
    else:
        new_rel = None

    embed = howlbert_embed(
        "raid successful",
        f"you slip into **{victim_name}**'s {noun} and make off with it. {loot_line}" + paranoia_note,
        color=SUCCESS_COLOR,
    )
    embed.add_field(name="stolen", value=loot_name, inline=True)
    embed.add_field(name="den standing", value=f"+{standing_gain}", inline=True)
    if new_rel is not None:
        embed.add_field(name=f"standing with {victim_name}", value=f"{new_rel}/10", inline=True)
    embed.set_footer(text="your den praises a successful rival raid.")
    return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)


def preypile_error(interaction: discord.Interaction) -> str | None:
    """return an error message if prey pile cannot be opened, else none."""
    user = db.get_user(interaction.user.id)
    if not user:
        return "use `/register` first."
    if not interaction.guild:
        return "use this in a server."
    world = db.get_world(interaction.guild.id)
    day = world["day_number"]
    stack = db.pick_prey_stack_for_pile(user["id"], day)
    if not stack:
        has_activity = (
            user["last_hunt_day"] >= day
            or user["last_track_day"] >= day
            or user["last_fishing_day"] >= day
        )
        if has_activity and user["last_hunt_yield"] > 0:
            _migrate_legacy_prey_to_hoard(user, interaction.guild.id, day)
            stack = db.pick_prey_stack_for_pile(user["id"], day)
    if not stack:
        from engine.prey_storage import fresh_kill_pile_block_message

        rotting_msg = fresh_kill_pile_block_message(user["id"], day)
        if rotting_msg:
            return rotting_msg
        return (
            "no fresh carcass in your hoard; hunt, track, or fish first (`/food` to check)."
        )
    # no block: lay out fresh-kill as often as there is carcass to share
    return None


def _migrate_legacy_prey_to_hoard(user, guild_id: int, day: int) -> None:
    """one-time bridge: old last_hunt_yield → prey stack."""
    label = user["last_prey_label"] if "last_prey_label" in user.keys() else None
    bones = int(user["last_hunt_yield"])
    from engine.prey_items import prey_key_from_hunt_amount, prey_key_from_label

    prey_key = prey_key_from_label(label)
    if prey_key:
        pass
    elif label == PREY_LABEL_FISH:
        prey_key = "fish"
    elif label == PREY_LABEL_HARE:
        prey_key = "hare"
    else:
        gp = user["great_pack"] if "great_pack" in user.keys() else None
        prey_key = prey_key_from_hunt_amount(bones, great_pack=gp)
    grant_prey_from_hunt(
        user["id"],
        guild_id=guild_id,
        day=day,
        bone_value=bones,
        prey_key=prey_key,
    )