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
    LARGE_PREY_ENCOUNTER_CHANCE,
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
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from engine.infractions import (
    crime_caught_standing,
    cross_pack_steal_caught_standing,
    cross_pack_steal_standing,
    pick_crime_caught_flavor,
    pick_cross_pack_steal_caught_flavor,
    roll_crime_caught,
    roll_cross_pack_steal_caught,
)
from engine.role_privileges import can_forage_again, can_hunt_again, hunts_remaining_today, is_hunter, record_hunt_use
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
    roll_large_prey_encounter,
    start_large_prey_fight,
)
from engine.shop_items import consume_item_by_key, has_item
from utils.hunting import award_bones, roll_range

SCAVENGE_TEXT = [
    "Old bones half-buried in leaf litter; someone else's loss, your gain.",
    "A forgotten cache near a collapsed den.",
    "Scraps along the trail. Humble, but honest.",
    "You nose out a marrow-rich bone beneath the frost.",
]

TRACK_OUTCOMES: list[tuple[str, str]] = [
    (
        "You follow spoor through bracken and pull a **vole** from a burrow mouth.",
        "vole",
    ),
    (
        "A moderate chase ends with a **hare** in your jaws.",
        "hare",
    ),
    (
        "Scent leads you to a watering hole; a **rabbit** drinks too late.",
        "rabbit",
    ),
    (
        "You tracked well. A **grouse** never hears you over the creek.",
        "grouse",
    ),
]

FISH_TEXT = [
    "A silver fish flips in your teeth at the riverbank.",
    "Slow paw, steady catch; the river gives without a chase.",
    "You pull trout from the shallows as dusk settles.",
    "The current runs cold, but your haul runs true.",
]


def _strenuous_injury_embed(user) -> discord.Embed | None:
    block = strenuous_activity_blocked_by_injury(user)
    if block:
        return howlbert_embed("Too Injured", block, color=ERROR_COLOR)
    return None


def _need_guild(interaction: discord.Interaction) -> int | None:
    return interaction.guild.id if interaction.guild else None


def _activity_block_embed(user, *, title: str) -> discord.Embed | None:
    block = full_activity_block(user)
    if block:
        return howlbert_embed(title, block, color=ERROR_COLOR)
    return None


def try_daily(interaction: discord.Interaction) -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR)
    day = db.get_world(guild_id)["day_number"]
    if user["last_daily_day"] >= day:
        return howlbert_embed("Already Claimed", "Daily stipend taken this rollover.", color=ERROR_COLOR)

    from engine.role_features import is_rogue_wolf

    if is_rogue_wolf(user):
        return howlbert_embed(
            "No Den Stipend",
            "Rogues scrape by outside pack treasuries; no `/bones action:daily` draw.\n\n"
            "Earn bones with `/bones action:hunt`, `/bones action:work`, or `/field action:scavenge`.",
            color=ERROR_COLOR,
        )

    pack_id = user["pack_id"] if "pack_id" in user.keys() else None
    if not pack_id:
        return howlbert_embed(
            "No Pack Treasury",
            "Loners don't draw from a den stash. Join a Great Pack with `/setfaction`, "
            "or earn bones with `/bones action:hunt`, `/bones action:work`, or `/field action:scavenge`.",
            color=ERROR_COLOR,
        )

    pack = db.get_pack(pack_id)
    if not pack:
        return howlbert_embed("Pack Not Found", color=ERROR_COLOR)

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
            "Treasury Bare",
            f"**{pack['name']}** only has **{format_bones(treasury)}** in the communal stash; "
            f"not enough for today's **{format_bones(base_reward)}** stipend.\n\n"
            "Feed the treasury: hunt (pack tax), `/pack deposit`, or share fresh-kill to the den on `/preypile`.",
            color=ERROR_COLOR,
        )

    if not db.claim_daily_stipend(interaction.user.id, pack_id, base_reward):
        return howlbert_embed(
            "Stipend Failed",
            "Could not pay from treasury; try again or ask your Alpha to deposit.",
            color=ERROR_COLOR,
        )

    if personal_bonus > 0:
        db.add_bones(interaction.user.id, personal_bonus, wolf_id=user["id"])

    db.update_user(interaction.user.id, last_daily_day=day)
    db.add_xp(interaction.user.id, 1)
    updated = db.get_user(interaction.user.id)
    updated_pack = db.get_pack(pack_id)
    total_payout = base_reward + personal_bonus
    embed = howlbert_embed("Daily Stipend", color=SUCCESS_COLOR)
    embed.description = daily_ration_note(
        account["prestige_tier"],
        pack_name=pack["name"],
        treasury=int(updated_pack["treasury"]) if updated_pack else 0,
        is_booster=is_booster,
        donor_bonus=donor_bonus,
    )
    embed.add_field(name="Received", value=format_bones(total_payout, signed=True), inline=True)
    embed.add_field(name="Your balance", value=format_bones(updated["bones"]), inline=True)
    embed.add_field(
        name="Pack treasury",
        value=format_bones(updated_pack["treasury"]) if updated_pack else "-",
        inline=True,
    )
    return embed


def try_hunt(interaction: discord.Interaction) -> tuple[discord.Embed | None, bool, int | None]:
    """Returns (embed, show_prey_buttons, hunt_combat_encounter_id)."""
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("Not Registered", color=ERROR_COLOR), False, None
    block = young_wolf_block(user, action="hunt")
    if block:
        return howlbert_embed("Too Young to Hunt", block, color=ERROR_COLOR), False, None
    inj_block = hunt_blocked_by_injury(user)
    if inj_block:
        return howlbert_embed("Cannot Hunt", inj_block, color=ERROR_COLOR), False, None
    blocked = _activity_block_embed(user, title="Cannot Hunt")
    if blocked:
        return blocked, False, None
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR), False, None
    world = db.get_world(guild_id)
    day = world["day_number"]
    if not can_hunt_again(user, day):
        return howlbert_embed("Already Hunted", "You've hunted this rollover.", color=ERROR_COLOR), False, None

    if roll_large_prey_encounter():
        record_hunt_use(interaction.user.id, wolf_id=user["id"], day=day)
        enc_id = start_large_prey_fight(
            user,
            guild_id=guild_id,
            channel_id=interaction.channel_id,
        )
        flavor = random.choice(LARGE_PREY_ENCOUNTER_TEXT)
        embed = howlbert_embed("Large Prey!", flavor, color=SUCCESS_COLOR)
        embed.set_footer(
            text=f"~{LARGE_PREY_ENCOUNTER_CHANCE}% hunt chance · down the prey to open the fresh-kill cache"
        )
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
        embed = ambush_embed(template_key, flavor)
        from config import HUNT_WILD_ENCOUNTER_CHANCE

        embed.set_footer(
            text=f"~{HUNT_WILD_ENCOUNTER_CHANCE}% ambush · win to finish your hunt · flee and you keep today's hunt"
        )
        return embed, False, enc_id

    from engine.character_traits import roll_trait_hunt_abort

    aborted, omen_trait = roll_trait_hunt_abort(user)
    if aborted:
        record_hunt_use(interaction.user.id, wolf_id=user["id"], day=day)
        flavor = (
            f"A bad omen stops you cold; **{omen_trait}** sends you back to the den empty-pawed."
        )
        embed = howlbert_embed("Hunt Aborted", flavor, color=ERROR_COLOR)
        embed.set_footer(text="Today's hunt is spent; try again after the next sunrise.")
        return embed, False, None

    dex_bonus = max(0, attr_modifier(get_attr(user, "dex")))
    amount = roll_hunt_amount()
    if amount > 0:
        amount += dex_bonus
    amount, sniff_bonus, sniff_note = apply_sniff_bone_bonus(user, amount, day)
    net_amount, tax, payout, lucky_bonus, mood_note, hunger_note, thirst_note, exhaustion_note, season_note = award_bones(
        user, amount, world["weather"], "hunt", season=world["season"], guild_id=guild_id
    )
    prey_key = prey_key_for_payout(payout) if payout > 0 else None
    flavor = hunt_flavor_for_payout(payout, prey_key)
    record_hunt_use(interaction.user.id, wolf_id=user["id"], day=day)
    db.update_user(
        interaction.user.id,
        last_hunt_yield=payout if payout > 0 else 0,
        last_prey_label=None,
    )
    updated = db.get_user(interaction.user.id)
    title = "Empty Paws" if net_amount == 0 else "Hunt Complete"
    color = ERROR_COLOR if net_amount == 0 else SUCCESS_COLOR
    embed = howlbert_embed(title, flavor, color=color)
    embed.add_field(name="Earned", value=format_bones(net_amount, signed=True), inline=True)
    if sniff_bonus > 0:
        embed.add_field(name="Sniff bonus", value=format_bones(sniff_bonus, signed=True), inline=True)
    if lucky_bonus > 0:
        embed.add_field(name="Lucky Tooth", value=format_bones(lucky_bonus, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="Pack Tax", value=format_bones(tax), inline=True)
    embed.add_field(name="Balance", value=format_bones(updated["bones"]), inline=True)
    if net_amount > 0 and prey_key:
        prey_name = grant_prey_carcass_canonical(
            user["id"],
            guild_id=guild_id,
            day=day,
            prey_key=prey_key,
        )
        footer = f"**{prey_name}** in your hoard (`/prey`) · lay out with `/preypile`"
        from engine.blooding import award_blooding_on_hunt

        blooding_note = award_blooding_on_hunt(user)
        if blooding_note:
            footer = f"{blooding_note} · {footer}"
        left = hunts_remaining_today(user, day)
        if is_hunter(user) and left > 0:
            footer += f" · Hunter: **{left}** hunt(s) left this sunrise"
        notes = [n for n in (sniff_note, season_note, mood_note, hunger_note, thirst_note, exhaustion_note) if n]
        if net_amount > 0:
            from engine.season_rollover import try_autumn_hunt_cache

            cache_note = try_autumn_hunt_cache(user, season=world["season"])
            if cache_note:
                notes.append(cache_note.strip("_"))
        if notes:
            footer += " · " + " · ".join(notes)
        embed.set_footer(text=footer)
    return embed, net_amount > 0, None


def try_scavenge(interaction: discord.Interaction) -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("Not Registered", color=ERROR_COLOR)
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR)
    world = db.get_world(guild_id)
    day = world["day_number"]
    if user["last_scavenge_day"] >= day:
        return howlbert_embed("Already Done", "Scavenged this rollover.", color=ERROR_COLOR)
    injured = _strenuous_injury_embed(user)
    if injured:
        return injured
    blocked = _activity_block_embed(user, title="Cannot Scavenge")
    if blocked:
        return blocked
    gross = roll_range(SCAVENGE_BONES)
    net, tax, _, _, mood_note, hunger_note, thirst_note, exhaustion_note, season_note = award_bones(
        user, gross, world["weather"], "scavenge", season=world["season"], guild_id=guild_id
    )
    db.update_user(interaction.user.id, last_scavenge_day=day)
    db.increment_quest_progress(interaction.user.id, "scavenge")
    if net > 0:
        grant_prey_carcass_canonical(
            user["id"],
            guild_id=guild_id,
            day=day,
            prey_key="carrion",
        )
    updated = db.get_user(interaction.user.id)
    embed = howlbert_embed(random.choice(SCAVENGE_TEXT), color=SUCCESS_COLOR if net else ERROR_COLOR)
    embed.add_field(name="Earned", value=format_bones(net, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="Pack Tax", value=format_bones(tax), inline=True)
    embed.add_field(name="Balance", value=format_bones(updated["bones"]), inline=True)
    if net > 0:
        from engine.disease_contract import try_scavenge_filth_exposure

        filth = try_scavenge_filth_exposure(user)
        notes = [n for n in (season_note, mood_note, hunger_note, thirst_note, exhaustion_note, filth) if n]
        if notes:
            embed.set_footer(text=" · ".join(notes))
    elif season_note or mood_note or hunger_note or thirst_note:
        embed.set_footer(text=" · ".join(n for n in (season_note, mood_note, hunger_note, thirst_note, exhaustion_note) if n))
    return embed


def try_track(
    interaction: discord.Interaction,
    *,
    trail_age: str = "recent",
) -> tuple[discord.Embed | None, bool]:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("Not Registered", color=ERROR_COLOR), False
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR), False
    world = db.get_world(guild_id)
    day = world["day_number"]
    if user["last_track_day"] >= day:
        return howlbert_embed("Already Done", "Tracked this rollover.", color=ERROR_COLOR), False
    injured = _strenuous_injury_embed(user)
    if injured:
        return injured, False
    blocked = _activity_block_embed(user, title="Cannot Track")
    if blocked:
        return blocked, False

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
    ok, track_msg, _ = run_skill_scenario(
        user,
        scenario_key,
        day=day,
        weather=world["weather"],
        time_of_day=world["time_of_day"],
        rained=rained,
    )
    if not ok:
        db.update_user(interaction.user.id, last_track_day=day)
        return (
            howlbert_embed("Trail Lost", track_msg, color=ERROR_COLOR),
            False,
        )

    wis_bonus = max(0, attr_modifier(get_attr(user, "wis")))
    flavor, track_prey_key = random.choice(TRACK_OUTCOMES)
    gross = roll_range(TRACK_BONES) + wis_bonus
    gross, sniff_bonus, sniff_note = apply_sniff_bone_bonus(user, gross, day)
    net, tax, payout, _, mood_note, hunger_note, thirst_note, exhaustion_note, season_note = award_bones(
        user, gross, world["weather"], "track", season=world["season"], guild_id=guild_id
    )
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
    embed = howlbert_embed(flavor, color=SUCCESS_COLOR)
    embed.description = f"{track_msg}\n\n_{flavor}_"
    embed.add_field(name="Earned", value=format_bones(net, signed=True), inline=True)
    if sniff_bonus > 0:
        embed.add_field(name="Sniff bonus", value=format_bones(sniff_bonus, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="Pack Tax", value=format_bones(tax), inline=True)
    embed.add_field(name="Balance", value=format_bones(updated["bones"]), inline=True)
    if net > 0:
        footer = f"**{prey_name}** in hoard (`/prey`) · `/preypile` to share at the den"
        notes = [n for n in (sniff_note, season_note, mood_note, hunger_note, thirst_note, exhaustion_note) if n]
        if notes:
            footer += " · " + " · ".join(notes)
        embed.set_footer(text=footer)
    elif sniff_note or season_note or mood_note or hunger_note or thirst_note:
        embed.set_footer(text=" · ".join(n for n in (sniff_note, season_note, mood_note, hunger_note, thirst_note, exhaustion_note) if n))
    return embed, net > 0


def try_fishing(interaction: discord.Interaction) -> tuple[discord.Embed | None, bool]:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("Not Registered", color=ERROR_COLOR), False
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR), False
    world = db.get_world(guild_id)
    day = world["day_number"]
    if user["last_fishing_day"] >= day:
        return howlbert_embed("Already Done", "Fished this rollover.", color=ERROR_COLOR), False
    injured = _strenuous_injury_embed(user)
    if injured:
        return injured, False
    blocked = _activity_block_embed(user, title="Cannot Fish")
    if blocked:
        return blocked, False
    gross = roll_range(FISHING_BONES)
    net, tax, payout, _, mood_note, hunger_note, thirst_note, exhaustion_note, season_note = award_bones(
        user, gross, world["weather"], "fishing", season=world["season"], guild_id=guild_id
    )
    db.update_user(
        interaction.user.id,
        last_fishing_day=day,
        last_hunt_yield=payout if payout > 0 else 0,
        last_prey_label=PREY_LABEL_FISH,
    )
    db.increment_quest_progress(interaction.user.id, "fishing")
    if net > 0:
        prey_name = grant_prey_carcass_canonical(
            user["id"],
            guild_id=guild_id,
            day=day,
            prey_key="fish",
        )
    updated = db.get_user(interaction.user.id)
    embed = howlbert_embed(random.choice(FISH_TEXT), color=SUCCESS_COLOR if net else ERROR_COLOR)
    embed.add_field(name="Earned", value=format_bones(net, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="Pack Tax", value=format_bones(tax), inline=True)
    embed.add_field(name="Balance", value=format_bones(updated["bones"]), inline=True)
    if net > 0:
        footer = f"**{prey_name}** in hoard (`/prey`) · `/preypile` to share at the den"
        if season_note or mood_note or hunger_note or thirst_note:
            footer += " · " + " · ".join(
                n for n in (season_note, mood_note, hunger_note, thirst_note, exhaustion_note) if n
            )
        embed.set_footer(text=footer)
    elif season_note or mood_note or hunger_note or thirst_note:
        embed.set_footer(text=" · ".join(n for n in (season_note, mood_note, hunger_note, thirst_note, exhaustion_note) if n))
    return embed, net > 0


def try_forage(interaction: discord.Interaction, rarity: str = "common") -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("Not Registered", color=ERROR_COLOR)
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR)
    world = db.get_world(guild_id)
    day = world["day_number"]
    if not can_forage_again(user, day):
        return howlbert_embed("Already Foraged", "You've foraged this rollover.", color=ERROR_COLOR)
    blocked = _activity_block_embed(user, title="Cannot Forage")
    if blocked:
        return blocked
    from engine.forager_perk import grant_forager_auto_herb

    auto_herb = grant_forager_auto_herb(user, day=day, guild_id=guild_id)
    forager_note = (
        f"\n\n_Forager perk: **{auto_herb}** turned up in pack territory._" if auto_herb else ""
    )
    dc = FORAGE_RARITY_DC[rarity] + season_forage_dc_mod(world["season"])
    season_note = season_forage_modifier_label(world["season"])
    season_suffix = f"\n_{season_note}_" if season_forage_dc_mod(world["season"]) else ""
    profs = parse_proficiencies(user["skill_proficiencies"])
    result = resolve_check(
        user,
        attr_keys=("attr_con", "attr_str"),
        skill="Survival",
        dc=dc,
        proficient="survival" in profs or "herblore" in profs,
        skill_key="survival",
        game_day=day,
    )
    db.update_user(interaction.user.id, last_forage_day=day)
    if result["outcome"] == "critical_failure":
        return howlbert_embed(
            "Misidentified!",
            format_roll_result(result)
            + "\n\nYou damaged the patch or gathered something toxic."
            + forager_note
            + season_suffix,
            color=ERROR_COLOR,
        )
    if not result["success"]:
        from engine.season_effects import maybe_spoil_herb_on_forage_fail

        spoil_note = maybe_spoil_herb_on_forage_fail(user, season=world["season"])
        return howlbert_embed(
            "Forage Failed",
            format_roll_result(result) + forager_note + season_suffix + spoil_note,
            color=ERROR_COLOR,
        )
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
    meta = HERBS[herb_key]
    stack_id, hoard_note = grant_fresh_herb(
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
            rare_id, _ = grant_fresh_herb(
                user["id"],
                herb_key=rare_key,
                guild_id=guild_id,
                day=day,
                user=user,
            )
            from engine.season_effects import season_activity_blurb

            rare_note = (
                f"\n\n**Critical find**: **{rare_meta['name']}** (`stack:{rare_id}`) "
                f"turned up in the undergrowth.\n_{season_activity_blurb(world['season'])}_"
            )
    db.increment_quest_progress(interaction.user.id, "forage")
    auto_note = forager_note
    return howlbert_embed(
        "Forage Success",
        format_roll_result(result)
        + f"\n\nFound **{meta['name']}**{qty_note}: fresh stack `#{stack_id}` in your herb bag."
        + f"\n_{meta['effect']}_"
        + fresh_herb_warning(herb_key)
        + (f"\n\n{hoard_note}" if hoard_note else "")
        + rare_note
        + auto_note
        + season_suffix,
        color=SUCCESS_COLOR,
    )


def purchase_item(interaction: discord.Interaction, item_key: str) -> discord.Embed | None:
    from engine.shop_purchase import purchase_shop_item

    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("Not Registered", color=ERROR_COLOR)
    shop_item = db.get_item_by_key(item_key)
    if not shop_item or shop_item["price"] <= 0:
        return howlbert_embed("Unknown Item", "Check `/shop` for valid items.", color=ERROR_COLOR)

    guild_id = interaction.guild.id if interaction.guild else None
    day = db.get_world(guild_id)["day_number"] if guild_id else 0
    ok, note, item_name = purchase_shop_item(
        interaction.user.id,
        item_key,
        guild_id=guild_id,
        day=day,
    )
    if not ok:
        return howlbert_embed(note if note != "Not enough bones." else "Not Enough Bones", color=ERROR_COLOR)
    updated = db.get_user(interaction.user.id)
    embed = howlbert_embed("Purchased", note, color=SUCCESS_COLOR)
    embed.add_field(name="Item", value=item_name or shop_item["name"], inline=True)
    embed.add_field(name="Spent", value=format_bones(shop_item["price"]), inline=True)
    embed.add_field(name="Balance", value=format_bones(updated["bones"]), inline=True)
    return embed


def accept_quest(interaction: discord.Interaction, quest_key: str) -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("Not Registered", color=ERROR_COLOR)
    q = db.get_quest_by_key(quest_key)
    if not q or q["quest_type"] == "daily":
        return howlbert_embed("Unknown Quest", color=ERROR_COLOR)
    req_role = q["required_role"] if "required_role" in q.keys() else None
    if req_role:
        from engine.apprentice_roles import quest_role_matches
        from rpg_rules import ROLE_LABELS

        wolf_role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
        if not quest_role_matches(wolf_role, req_role):

            return howlbert_embed(
                "Wrong Role",
                f"This quest is for **{ROLE_LABELS.get(req_role, req_role)}** wolves only.",
                color=ERROR_COLOR,
            )
        req_pack = q["required_pack"] if "required_pack" in q.keys() else None
        if req_pack and user["great_pack"] != req_pack:
            return howlbert_embed(
                "Wrong Pack",
                f"This Mistmoor tradition requires the **{req_pack.title()}** Great Pack.",
                color=ERROR_COLOR,
            )
    elif q["quest_type"] == "role":
        return howlbert_embed("Role Quest", "Use `/rolequests` for role-specific quests.", color=ERROR_COLOR)
    if q["quest_type"] == "unique" and db.has_completed_unique(interaction.user.id, q["id"]):
        return howlbert_embed("Already Done", "That tale is already written.", color=ERROR_COLOR)
    day = db.get_world(interaction.guild.id)["day_number"] if interaction.guild else 0
    if not db.accept_quest(interaction.user.id, q["id"], day):
        return howlbert_embed("Already Active", "You're already on that quest.", color=ERROR_COLOR)
    embed = howlbert_embed("Quest Accepted", q["description"], color=SUCCESS_COLOR)
    embed.add_field(name="Objective", value=f"{q['objective_type']} x{q['objective_count']}", inline=True)
    from engine.quest_rewards import format_quest_reward_line

    embed.add_field(name="Reward", value=format_quest_reward_line(q["key"], q["reward_bones"]), inline=True)
    return embed


def complete_quest(interaction: discord.Interaction, quest_key: str | None = None) -> discord.Embed | None:
    if not db.get_user(interaction.user.id):
        return howlbert_embed("Not Registered", color=ERROR_COLOR)
    result = db.complete_quest(interaction.user.id, quest_key)
    if not result:
        if quest_key:
            active = db.get_active_quest_by_key(interaction.user.id, quest_key)
            if active:
                return howlbert_embed(
                    "Not Ready",
                    f"**{active['title']}**: "
                    f"**{active['progress']}/{active['objective_count']}** "
                    f"({active['objective_type']}). "
                    "Do the objective after accepting, or abandon and re-accept if you already "
                    "finished that action today.",
                    color=ERROR_COLOR,
                )
        return howlbert_embed("Not Ready", "Quest objectives not finished yet.", color=ERROR_COLOR)
    embed = howlbert_embed("Quest Complete", color=SUCCESS_COLOR)
    embed.add_field(name="Quest", value=result["title"], inline=False)
    embed.add_field(name="Bones", value=format_bones(result["reward_bones"], signed=True), inline=True)
    embed.add_field(name="Standing", value=f"+{result['standing_reward']}", inline=True)
    from engine.quest_rewards import format_quest_reward_suffix, quest_xp_reward, quest_skill_reward

    xp_gain = quest_xp_reward(result["quest_key"])
    embed.add_field(name="XP", value=f"+{xp_gain}", inline=True)
    skill_reward = quest_skill_reward(result["quest_key"])
    if skill_reward:
        from rpg_rules import SKILLS, SKILL_RANK_BONUS

        skill_key, rank_gain = skill_reward
        label = SKILLS.get(skill_key, ((), skill_key))[1]
        embed.add_field(
            name="Skill",
            value=f"**{label}** rank +{rank_gain} (+{SKILL_RANK_BONUS}/rank on checks)",
            inline=False,
        )
    extra = format_quest_reward_suffix(result["quest_key"])
    if extra:
        embed.set_footer(text=f"Rewards: {extra}")
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
            "An Extra Paw Required",
            "Buy **An Extra Paw** from `/shop` to add a custom `scene:` or `staff:true` "
            "to `/work` or `/crime`.",
            color=ERROR_COLOR,
        )
    if not consume_item_by_key(interaction.user.id, "extra_paw"):
        return howlbert_embed("Item Missing", "You don't have **An Extra Paw**.", color=ERROR_COLOR)
    if scene:
        text = scene.strip()[:1000]
        embed.add_field(name="🐾 Your Scene", value=text, inline=False)
    if staff:
        embed.add_field(
            name="🐾 Staff RP",
            value="An admin will weave your wolf into this scene.",
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
        return howlbert_embed("Not Registered", color=ERROR_COLOR)
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR)
    world = db.get_world(guild_id)
    day = world["day_number"]
    if user["last_work_day"] >= day:
        return howlbert_embed("Already Worked", "You've worked this rollover.", color=ERROR_COLOR)
    blocked = _activity_block_embed(user, title="Cannot Work")
    if blocked:
        return blocked
    gross = roll_range(WORK_BONES)
    net, tax, _, _, _, _, _, _, _ = award_bones(user, gross, world["weather"], "work")
    db.update_user(interaction.user.id, last_work_day=day)
    updated = db.get_user(interaction.user.id)
    embed = howlbert_embed(random.choice(WORK_TEXT), color=SUCCESS_COLOR if net else ERROR_COLOR)
    embed.add_field(name="Earned", value=format_bones(net, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="Pack Tax", value=format_bones(tax), inline=True)
    embed.add_field(name="Balance", value=format_bones(updated["bones"]), inline=True)
    return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)


def try_crime(
    interaction: discord.Interaction,
    *,
    target_pack: str | None = None,
    scene: str | None = None,
    staff: bool = False,
) -> discord.Embed | None:
    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("Not Registered", color=ERROR_COLOR)
    block = young_wolf_block(user, action="crime")
    if block:
        return howlbert_embed("Too Young", block, color=ERROR_COLOR)
    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR)
    world = db.get_world(guild_id)
    day = world["day_number"]
    if user["last_crime_day"] >= day:
        return howlbert_embed("Already Done", "You've run your score this rollover.", color=ERROR_COLOR)
    blocked = _activity_block_embed(user, title="Cannot Run a Score")
    if blocked:
        return blocked

    if target_pack:
        return _try_cross_pack_steal(
            interaction,
            user,
            day=day,
            target_pack=target_pack,
            scene=scene,
            staff=staff,
        )

    db.update_user(interaction.user.id, last_crime_day=day)

    from engine.plot_blinking import try_plot_rogue_crime

    gross = roll_range(CRIME_BONES)
    gross, plot_suffix, plot_caught = try_plot_rogue_crime(
        interaction, user, day=day, gross=gross
    )
    if plot_caught:
        embed = howlbert_embed("Caught on the Border", plot_caught, color=ERROR_COLOR)
        embed.set_footer(text="No bones earned. The den remembers.")
        return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)

    if roll_crime_caught():
        kick = db.adjust_wolf_standing(interaction.user.id, crime_caught_standing())
        embed = howlbert_embed("Caught", pick_crime_caught_flavor(), color=ERROR_COLOR)
        embed.add_field(
            name="Standing",
            value=(
                f"{crime_caught_standing()} "
                + ("- **cast out** as loner" if kick == "kicked" else "")
            ),
            inline=False,
        )
        embed.set_footer(text="No bones earned. The den remembers.")
        return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)

    net, tax, _, _, _, _, _, _, _ = award_bones(
        user, gross, world["weather"], "crime", guild_id=guild_id
    )
    db.increment_quest_progress(interaction.user.id, "crime")
    updated = db.get_user(interaction.user.id)
    body = random.choice(CRIME_TEXT)
    if plot_suffix:
        body += plot_suffix
    embed = howlbert_embed(body, color=SUCCESS_COLOR if net else ERROR_COLOR)
    embed.add_field(name="Earned", value=format_bones(net, signed=True), inline=True)
    if tax > 0:
        embed.add_field(name="Pack Tax", value=format_bones(tax), inline=True)
    embed.add_field(name="Balance", value=format_bones(updated["bones"]), inline=True)
    return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)


def _try_cross_pack_steal(
    interaction: discord.Interaction,
    user,
    *,
    day: int,
    target_pack: str,
    scene: str | None,
    staff: bool,
) -> discord.Embed | None:
    from config import GREAT_PACKS

    if target_pack not in GREAT_PACKS:
        return howlbert_embed(
            "Unknown Pack",
            "Pick a rival Great Pack: greyspire, mistmoor, thistlehide, or silverrush.",
            color=ERROR_COLOR,
        )

    own_pack = user["great_pack"] if "great_pack" in user.keys() else None
    if own_pack == target_pack:
        return howlbert_embed(
            "Your Own Den",
            "You can't raid your own pack's treasury.",
            color=ERROR_COLOR,
        )
    if not user["pack_id"]:
        return howlbert_embed(
            "No Pack",
            "Join a Great Pack to run a den raid; loners use `/crime` without a target for scraps.",
            color=ERROR_COLOR,
        )

    victim = db.get_pack_by_key(target_pack)
    if not victim:
        return howlbert_embed("Pack Not Found", color=ERROR_COLOR)

    victim_name = GREAT_PACKS[target_pack]["name"]
    if int(victim["treasury"]) <= 0:
        return howlbert_embed(
            "Empty Stash",
            f"**{victim_name}**'s treasury is bare; nothing to steal this sunrise.",
            color=ERROR_COLOR,
        )

    db.update_user(interaction.user.id, last_crime_day=day)

    if roll_cross_pack_steal_caught():
        penalty = cross_pack_steal_caught_standing()
        from engine.plot_blinking import plot_cross_pack_caught_standing_extra

        penalty += plot_cross_pack_caught_standing_extra(interaction.guild.id)
        kick = db.adjust_wolf_standing(interaction.user.id, penalty)
        embed = howlbert_embed(
            "Caught at the Border",
            pick_cross_pack_steal_caught_flavor(victim_name),
            color=ERROR_COLOR,
        )
        embed.add_field(
            name="Standing",
            value=f"{penalty}" + ("; **cast out** as loner" if kick == "kicked" else ""),
            inline=False,
        )
        embed.set_footer(text=f"No bones taken from {victim_name}.")
        return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)

    attempted = roll_range(CROSS_PACK_STEAL_BONES)
    stolen = db.raid_pack_treasury(interaction.user.id, victim["id"], attempted)
    if stolen <= 0:
        return howlbert_embed(
            "Raid Failed",
            f"**{victim_name}**'s treasury emptied before you reached it.",
            color=ERROR_COLOR,
        )

    standing_gain = cross_pack_steal_standing()
    db.adjust_wolf_standing(interaction.user.id, standing_gain)
    updated = db.get_user(interaction.user.id)
    victim_after = db.get_pack(victim["id"])

    flavor = random.choice(CROSS_PACK_STEAL_TEXT).format(pack=victim_name)
    embed = howlbert_embed("Raid Successful", flavor, color=SUCCESS_COLOR)
    embed.add_field(name="Stolen", value=format_bones(stolen, signed=True), inline=True)
    embed.add_field(name="Standing", value=f"+{standing_gain}", inline=True)
    embed.add_field(name="Your balance", value=format_bones(updated["bones"]), inline=True)
    if victim_after:
        embed.add_field(
            name=f"{victim_name} treasury",
            value=format_bones(victim_after["treasury"]),
            inline=True,
        )
    embed.set_footer(text="Your den praises a successful rival raid.")
    return _apply_extra_paw(interaction, embed, scene=scene, staff=staff)


def preypile_error(interaction: discord.Interaction) -> str | None:
    """Return an error message if prey pile cannot be opened, else None."""
    user = db.get_user(interaction.user.id)
    if not user:
        return "Use `/register` first."
    if not interaction.guild:
        return "Use this in a server."
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
        return (
            "No fresh carcass in your hoard; hunt, track, or fish first (`/prey` to check)."
        )
    if user["last_prey_pile_day"] >= day:
        return "You've already laid out fresh-kill at the cache this sunrise."
    return None


def _migrate_legacy_prey_to_hoard(user, guild_id: int, day: int) -> None:
    """One-time bridge: old last_hunt_yield → prey stack."""
    label = user["last_prey_label"] if "last_prey_label" in user.keys() else None
    bones = int(user["last_hunt_yield"])
    if label == PREY_LABEL_FISH:
        prey_key = "fish"
    elif label == PREY_LABEL_HARE:
        prey_key = "hare"
    else:
        from engine.prey_items import prey_key_from_hunt_amount

        prey_key = prey_key_from_hunt_amount(bones)
    grant_prey_from_hunt(
        user["id"],
        guild_id=guild_id,
        day=day,
        bone_value=bones,
        prey_key=prey_key,
    )

