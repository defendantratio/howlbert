"""Sniff the wind; hunt/track bonus, wolf encounters, and border cat fights."""

from __future__ import annotations

import random

import discord

from config import (
    GREAT_PACKS,
    SNIFF_ALERT_ENCOUNTER_BONUS,
    SNIFF_CAT_ENCOUNTER_CHANCE,
    SNIFF_HUNT_BONUS_PCT,
    SNIFF_THIRST_RESTORE,
    SNIFF_WOLF_ENCOUNTER_CHANCE,
    SNIFF_WOLF_ENCOUNTER_MOOD,
)
from engine.cat_pacts import pact_border_chance_multiplier
from engine.prey_items import SNIFF_FLAVORS
from utils.embeds import SUCCESS_COLOR, howlbert_embed


SNIFF_ENCOUNTER_PACKMATE = (
    "you catch **{name}** on the same ridge; they step out of the pines, ears forward, tail low.",
    "**{name}** is already here, nose in the same trail you were reading.",
    "a familiar scent; **{name}** rounds the boulder and gives a quick nose-bump.",
)

SNIFF_ENCOUNTER_FACTION = (
    "a **{pack}** wolf; **{name}**; watches from the treeline before padding closer.",
    "scent marks say **{pack}** territory. **{name}** appears on the trail, cautious but curious.",
    "**{name}** of **{pack}** crosses your path; neither of you expected company this early.",
)

SNIFF_ENCOUNTER_STRANGER = (
    "an unfamiliar wolf; **{name}**; freezes when you both read the same trail.",
    "a stranger's mark on the wind: **{name}** slips out of the brush, wary.",
    "**{name}** is here too, nose to the ground. you lock eyes, then relax.",
)


_BOND_ENCOUNTER_LINES = {
    "friendship": (
        "an old friend; something in your shoulders loosens.",
        "familiar warmth on the wind; you knew who it was before you saw them.",
        "you've walked this stretch together before. the ridge feels smaller.",
    ),
    "rivalry": (
        "the air goes taut. you've tangled before, and you both know it.",
        "old tension surfaces before either of you speaks. the trail suddenly feels contested.",
        "the body language is instinctive; weight forward, ears back, assessing.",
    ),
    "kin": (
        "blood is blood, even out here. something in you settles.",
        "kin on the wind; the trail feels less alone.",
        "family doesn't need a reason to find each other in the same territory.",
    ),
    "mentor": (
        "the old rhythm comes back easy; the one who taught you, on the same ground.",
        "you catch yourself reading the trail the way they showed you.",
        "mentor and mentee, out on the same ridge. habits die hard.",
    ),
    "romance": (
        "the scent hits before the sight, and your pace slows without thinking.",
        "the world quiets a little. just the two of you, and the trail.",
        "every encounter still carries that particular warmth.",
    ),
}


def _bond_encounter_note(user, encounter) -> str | None:
    import database as _db
    for bond_type in ("romance", "kin", "mentor", "friendship", "rivalry"):
        bond = _db.get_bond(user["id"], encounter["id"], bond_type)
        if bond and int(bond["strength"]) >= 30:
            lines = _BOND_ENCOUNTER_LINES.get(bond_type)
            if lines:
                return f"_({random.choice(lines)})_"
    return None


def sniff_bonus_active(user, day: int) -> bool:
    bonus_day = int(user["sniff_bonus_day"]) if "sniff_bonus_day" in user.keys() else 0
    return bonus_day >= day


def apply_sniff_bone_bonus(user, amount: int, day: int) -> tuple[int, int, str]:
    """return (new_amount, bonus_added, footer_note)."""
    if amount <= 0 or not sniff_bonus_active(user, day):
        return amount, 0, ""
    bonus = max(1, int(amount * SNIFF_HUNT_BONUS_PCT / 100))
    note = f"sniff bonus; +{SNIFF_HUNT_BONUS_PCT}% payout."
    return amount + bonus, bonus, note


def sniff_track_fail_reduction(user, day: int) -> int:
    """points subtracted from tracking dc when sniff bonus is active."""
    if not sniff_bonus_active(user, day):
        return 0
    return max(5, int(SNIFF_HUNT_BONUS_PCT / 2))


def _encounter_flavor(user, other) -> str:
    name = other["wolf_name"]
    if user["pack_id"] and user["pack_id"] == other["pack_id"]:
        return random.choice(SNIFF_ENCOUNTER_PACKMATE).format(name=name)
    gp = other["great_pack"] if "great_pack" in other.keys() and other["great_pack"] else None
    if gp and gp in GREAT_PACKS:
        pack = GREAT_PACKS[gp]["name"]
        return random.choice(SNIFF_ENCOUNTER_FACTION).format(name=name, pack=pack)
    return random.choice(SNIFF_ENCOUNTER_STRANGER).format(name=name)


def try_sniff(interaction) -> tuple[discord.Embed, int | None]:
    """
    Sniff the wind once per sunrise.
    Returns (embed, border_combat_encounter_id or None).
    """
    import database as db

    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first."), None
    if not interaction.guild:
        return howlbert_embed("server only", "use this in a server."), None

    world = db.get_world(interaction.guild.id)
    day = world["day_number"]

    from engine.diminishing import diminishing_note, next_use_multiplier

    sniff_mult, sniff_n = next_use_multiplier(user, "sniff", day)

    db.update_user(interaction.user.id, last_sniff_day=day)
    flavor = random.choice(SNIFF_FLAVORS)
    body = flavor["text"]
    from engine.world import conditions_snippet, effective_time_of_day

    live_tod = effective_time_of_day(world)
    footer_bits: list[str] = [conditions_snippet(live_tod, world["weather"])]
    combat_enc_id: int | None = None
    alert_bonus = 0.0

    kind = flavor["kind"]
    if kind == "gather":
        db.update_user(interaction.user.id, sniff_bonus_day=day)
        track_cut = sniff_track_fail_reduction(user, day)
        body += (
            f"\n\n**+{SNIFF_HUNT_BONUS_PCT}%** hunt/track/scavenge/fish bones · "
            f"**−{track_cut}** track dc this sunrise."
        )
        footer_bits.append(f"sniff bonus (+{SNIFF_HUNT_BONUS_PCT}% bones, −{track_cut} track dc)")
    elif kind == "water":
        restore = max(1, int(SNIFF_THIRST_RESTORE * sniff_mult))
        new_thirst = db.adjust_thirst(user["id"], restore)
        body += f"\n\n**+{restore} hydration** (now **{new_thirst}**); the damp air wets your tongue."
    elif kind == "alert":
        alert_bonus = SNIFF_ALERT_ENCOUNTER_BONUS
        body += "\n\nyour hackles rise; whoever left that is close. you stay sharp on the way back."
        footer_bits.append("on alert")
        if user["pack_id"]:
            from engine.rival_npcs import pick_rival_for_hostile_pack, record_rival_encounter

            pick = pick_rival_for_hostile_pack(interaction.guild.id, user["pack_id"])
            if pick:
                rival, other_pack_name = pick
                grudge = record_rival_encounter(user["id"], rival["key"], day=day)
                body += (
                    f"\n\nthe mark belongs to **{rival['name']}** of **{other_pack_name}**; "
                    f"{rival['blurb']}\ngrudge with **{rival['name']}**: **{grudge}/100** "
                    f"(`/rivals` for the full list)."
                )
                footer_bits.append(f"rival: {rival['name']}")

    from utils.hunting import weather_hunt_modifier_label

    weather_note = weather_hunt_modifier_label(world["weather"])
    if weather_note:
        body += f"\n\n**weather read:** {weather_note.lower()} on hunt/track this sunrise."
    from engine.season_effects import season_forage_modifier_label

    forage_note = season_forage_modifier_label(world["season"])
    if forage_note:
        body += f"\n**forage read:** {forage_note.lower()}."

    if user["pack_id"]:
        hostile: list[str] = []
        for row in db.list_pack_relations(interaction.guild.id, user["pack_id"]):
            if int(row["standing"]) <= 3:
                hostile.append(f"**{row['other_pack_name']}** ({row['standing']}/10)")
        if hostile:
            body += (
                "\n\n**hostile scent:** "
                + ", ".join(hostile[:3])
                + "; sniff/survey fights more likely until standing rises."
            )
            footer_bits.append("border tension")

    gp = user["great_pack"] if "great_pack" in user.keys() and user["great_pack"] else None
    if gp and gp in GREAT_PACKS:
        from engine.territory_marking import read_marks_for_sniff

        marks = read_marks_for_sniff(gp, guild_id=interaction.guild.id, day=day)
        if marks:
            body += "\n\n**scent marks on the wind:**\n" + "\n".join(f"· {m}" for m in marks[:4])
            footer_bits.append("border marks")

    encounter = None
    sniff_odds = SNIFF_WOLF_ENCOUNTER_CHANCE + alert_bonus
    if "shedding_until_day" in user.keys() and int(user["shedding_until_day"] or 0) >= day > 0:
        sniff_odds += 0.08
    howl_exposed = int(user["howl_exposed_day"]) if "howl_exposed_day" in user.keys() else 0
    if howl_exposed > 0 and day > 0 and howl_exposed >= day - 1:
        from config import HOWL_EXPOSED_BORDER_BONUS
        sniff_odds += HOWL_EXPOSED_BORDER_BONUS
    if interaction.guild and user["pack_id"]:
        from engine.pack_raid_ecology import sniff_encounter_chance_bonus

        with db.get_db() as conn:
            rival_packs = conn.execute(
                "SELECT id FROM packs WHERE id != ?",
                (user["pack_id"],),
            ).fetchall()
        for rp in rival_packs:
            sniff_odds += sniff_encounter_chance_bonus(
                interaction.guild.id,
                user["pack_id"],
                int(rp["id"]),
                day,
            )
    if random.random() < min(0.85, sniff_odds):
        encounter = db.pick_sniff_encounter_wolf(
            exclude_wolf_id=user["id"],
            exclude_discord_id=interaction.user.id,
            pack_id=user["pack_id"],
            great_pack=gp,
        )

    if encounter:
        from engine.pack_relations import sniff_encounter_lines

        relation_body, skirmish_id = sniff_encounter_lines(
            user,
            encounter,
            guild_id=interaction.guild.id,
            channel_id=interaction.channel_id,
            day=day,
        )
        if relation_body:
            body += relation_body
            if skirmish_id:
                combat_enc_id = skirmish_id
                footer_bits.append("Hostile rival; combat panel below")
        else:
            body += f"\n\n{_encounter_flavor(user, encounter)}"
            bond_line = _bond_encounter_note(user, encounter)
            if bond_line:
                body += f"\n\n{bond_line}"
            rival_bond = db.get_bond(user["id"], encounter["id"], "rivalry")
            if rival_bond and int(rival_bond["strength"]) >= 50:
                db.adjust_wolf_standing(user["discord_id"], 1)
                body += "\n_your rival is out here too. the standing you carry sharpens._"
            mood_gain = max(1, int(SNIFF_WOLF_ENCOUNTER_MOOD * sniff_mult))
            new_mood = db.adjust_mood(user["id"], mood_gain)
            body += f"\n\n**+{mood_gain} mood** (now **{new_mood}**)."
            if user["pack_id"] and user["pack_id"] == encounter["pack_id"]:
                body += (
                    "\npackmate on the trail; try **`/playpen action:socialize`** "
                    "if you haven't mingled today."
                )
            from engine.disease_contract import try_spread_from_close_contact
            disease_note = try_spread_from_close_contact(user, encounter)
            if disease_note:
                body += f"\n\n{disease_note}"
        footer_bits.append("Wolf encounter")
    else:
        border_odds = (SNIFF_CAT_ENCOUNTER_CHANCE + alert_bonus) * pact_border_chance_multiplier(
            interaction.guild.id, user["pack_id"]
        )
        from engine.wolf_pack_pacts import wolf_pact_border_multiplier

        border_odds *= wolf_pact_border_multiplier(interaction.guild.id, user["pack_id"])
        from engine.plot_blinking import plot_sniff_border_mult

        border_odds *= plot_sniff_border_mult(interaction.guild.id, user=user)
        if (
            border_odds > 0
            and random.random() < border_odds
        ):
            from engine.border_combat import start_border_cat_fight
            from engine.cat_clans import sniff_cat_scent_line
            from engine.cat_pacts import pick_border_cat_for_pack

            border_pick = pick_border_cat_for_pack(interaction.guild.id, user["pack_id"])
            _template, border_clan, violation = border_pick
            if violation:
                scent = sniff_cat_scent_line(allied_clan=border_clan, allied_patrol=True)
            else:
                scent = sniff_cat_scent_line(rival_clan=border_clan)
            body += f"\n\n_{scent}_"
            enc_id, _template, fight_flavor = start_border_cat_fight(
                user,
                guild_id=interaction.guild.id,
                channel_id=interaction.channel_id,
                pick=border_pick,
            )
            body += f"\n\n{fight_flavor}"
            combat_enc_id = enc_id
            footer_bits.append("border fight; use the combat panel")

    from engine.role_features import try_scout_hide_in_weather

    hide_note = try_scout_hide_in_weather(user, weather_key=world["weather"], day=day)
    if hide_note:
        body += f"\n\n_{hide_note}_"
        footer_bits.append("unseen paw active")

    from engine.restricted_herbs import try_catch_hoarder_on_sniff

    hoard_caught = try_catch_hoarder_on_sniff(user)
    if hoard_caught:
        body += f"\n\n{hoard_caught}"
        footer_bits.append("poison herbs seized")

    wis = int(user["attr_wis"]) if "attr_wis" in user.keys() else 0
    if wis >= 6 and user["pack_id"] and day > 0:
        packmates = [
            w for w in db.get_pack_den_wolves(int(user["pack_id"]))
            if w["id"] != user["id"] and (w["condition"] if "condition" in w.keys() else "healthy") != "dead"
        ]
        if packmates:
            import random as _r
            pm = _r.choice(packmates)
            pm_name = pm["wolf_name"]
            PREV = day - 1
            _ACT_HINTS = [
                ("last_hunt_day", "hunted"),
                ("last_forage_day", "foraged"),
                ("last_explore_day", "explored"),
                ("last_socialize_day", "socialized"),
                ("last_groom_day", "groomed someone"),
                ("last_sniff_day", "read the wind"),
                ("last_fishing_day", "fished"),
                ("last_work_day", "worked"),
                ("last_howl_day", "howled for the den"),
            ]
            pm_acts = [label for col, label in _ACT_HINTS if col in pm.keys() and int(pm[col] or 0) == PREV]
            if pm_acts:
                act_str = " and ".join(pm_acts[:2])
                body += f"\n\n_your nose catches **{pm_name}**'s trail from yesterday; they {act_str}._"
            else:
                body += f"\n\n_your nose catches **{pm_name}**'s scent; quiet, unremarkable; they kept to themselves._"
            footer_bits.append("den read")

    from engine.plot_blinking import try_plot_sniff_extras

    body += try_plot_sniff_extras(user, interaction.guild.id, day=day)

    from engine.whispering_wild import spirit_whisper_on_sniff

    whisper = spirit_whisper_on_sniff(user, weather=world["weather"])
    if whisper:
        body += f"\n\n{whisper}"
        footer_bits.append("spirit whisper")

    dim_note = diminishing_note(sniff_n)
    if dim_note:
        body += f"\n\n_{dim_note}_"

    embed = howlbert_embed("on the wind", body, color=SUCCESS_COLOR)
    embed.set_footer(text=" · ".join(footer_bits))
    return embed, combat_enc_id
