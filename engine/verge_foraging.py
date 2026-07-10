"""Foraging at the Thunderpath shoulder and Twoleg compound edges."""

from __future__ import annotations

import random

import database as db
from config import (
    VERGE_COMPOUND_DC,
    VERGE_COMPOUND_DOG_CHANCE,
    VERGE_CRIT_FAIL_MOOD,
    VERGE_FAIL_MOOD,
    VERGE_MONSTER_NEAR_MISS_CHANCE,
    VERGE_ROADSIDE_DC,
    VERGE_TOXIC_MISID_CHANCE,
)
from engine.character import parse_proficiencies
from engine.dice import format_roll_result, resolve_check
from herbs import HERBS
from engine.season_effects import season_forage_dc_mod, season_forage_modifier_label
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed

VERGE_SITES = {
    "roadside": {
        "label": "Thunderpath shoulder",
        "skill": "Survival",
        "attrs": ("attr_wis", "attr_dex"),
        "skill_key": "survival",
        "dc": VERGE_ROADSIDE_DC,
        "intro": (
            "You slip down to the **Thunderpath** verge; crushed stone, warm rubber stink, "
            "and weeds rooted in the ditch where monsters rarely stop."
        ),
        "success_flavor": (
            "Gravel bites your pads but the disturbed soil is rich with hardscrabble growth.",
            "A rain-cut ditch holds the only green for miles; verge plants thrive here.",
            "You work the shoulder fast, nose down in wilted stems before a monster roars past.",
        ),
        "fail_flavor": (
            "A monster's wind washes over you; you flatten in the culvert empty-pawed.",
            "The verge is baked dry; only stubble and cigarette-stink remain.",
            "You misread tire-blackened weeds and come away with nothing useful.",
        ),
        "risk_flavor": (
            "_A monster blasts past; hot wind and stink. You press flat until it fades. **−{mood} mood.**_",
            "_Blue-red monster-lights sweep the fog line. You flee the shoulder. **−{mood} mood.**_",
        ),
    },
    "compound": {
        "label": "Twoleg compound edge",
        "skill": "Stealth",
        "attrs": ("attr_dex", "attr_int"),
        "skill_key": "stealth",
        "dc": VERGE_COMPOUND_DC,
        "intro": (
            "You skirt a **Twoleg nest**; mowed strip, chain-link bite, milk-and-iron on the air. "
            "Gardens and spilled seed grow what the deep woods never will."
        ),
        "success_flavor": (
            "Under the fence shadow you nip sprigs from an untended bed.",
            "Compost warmth and chicken scratch; exactly where the soft-leaf herbs root.",
            "A loose board gap; you dart in, harvest, and melt back to the treeline.",
        ),
        "fail_flavor": (
            "A porch light flicks on; you slip away before the door opens.",
            "A hound bellows from the kennel run; no herbs worth the risk tonight.",
            "Mowed lawn and bare dirt; the Twolegs scraped the verge clean.",
        ),
        "risk_flavor": (
            "_A **guard hearth-hound** hurls itself at the fence. You run; **−{mood} mood.**_",
            "_A Twoleg shouts from the porch. You abandon the bed. **−{mood} mood.**_",
        ),
    },
}


def _pick_verge_herb(user, site: str) -> str:
    from engine.herb_habitat import herbs_for_verge

    pool = herbs_for_verge(site)
    if user["great_pack"]:
        pack_herbs = [
            k
            for k in pool
            if user["great_pack"] in HERBS[k].get("packs", ())
        ]
        if pack_herbs and random.random() < 0.35:
            pool = pack_herbs
    if not pool:
        pool = herbs_for_verge(site)
    return random.choice(pool)


def _verge_compound_dog_risk(
    user,
    *,
    guild_id: int,
    channel_id: int,
    day: int,
    critical: bool,
) -> tuple[str, int | None]:
    """Mechanical compound dog charge; ambush or bite."""
    from engine.wild_encounters import start_verge_dog_ambush, verge_dog_bite_fallback

    ambush = start_verge_dog_ambush(
        user,
        guild_id=guild_id,
        channel_id=channel_id,
        activity="verge",
    )
    if ambush:
        enc_id, _key, flavor = ambush
        return (
            f"_{flavor}_\n\n"
            f"a **guard hearth-hound** breaks the fence-line; combat **#{enc_id}** is live in-channel.",
            enc_id,
        )
    bite = verge_dog_bite_fallback(user, day=day)
    mood = VERGE_CRIT_FAIL_MOOD if critical else VERGE_FAIL_MOOD
    return (
        random.choice(VERGE_SITES["compound"]["risk_flavor"]).format(mood=mood)
        + f"\n\n_{bite}_",
        None,
    )


def _verge_risk_note(
    site: str,
    *,
    critical: bool = False,
    user=None,
    guild_id: int | None = None,
    channel_id: int | None = None,
    day: int = 1,
) -> tuple[str, int | None]:
    spec = VERGE_SITES[site]
    mood = VERGE_CRIT_FAIL_MOOD if critical else VERGE_FAIL_MOOD
    if site == "roadside":
        if critical and random.random() < VERGE_TOXIC_MISID_CHANCE:
            from engine.disease_contract import try_verge_toxic_misid_exposure

            toxic = try_verge_toxic_misid_exposure(user) if user else None
            db_note = (
                f"\n\n_{toxic}_" if toxic else "\n\n_you grabbed a toxic look-alike in the ditch; spit it out fast. "
                "Get a Medic to check you._"
            )
        else:
            db_note = ""
        if random.random() < VERGE_MONSTER_NEAR_MISS_CHANCE or critical:
            return random.choice(spec["risk_flavor"]).format(mood=mood) + db_note, None
        stripped = db_note.lstrip("\n\n") if db_note and not critical else ""
        return stripped, None
    if site == "compound":
        if random.random() < VERGE_COMPOUND_DOG_CHANCE or critical:
            if user and guild_id and channel_id:
                return _verge_compound_dog_risk(
                    user,
                    guild_id=guild_id,
                    channel_id=channel_id,
                    day=day,
                    critical=critical,
                )
            return random.choice(spec["risk_flavor"]).format(mood=mood), None
        return "", None
    return "", None


def try_verge_forage(interaction, site: str = "roadside"):
    from engine.herb_habitat import herbs_for_verge
    from engine.role_privileges import is_full_forager

    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR), None
    if site not in VERGE_SITES:
        return howlbert_embed("unknown verge", "pick **roadside** or **compound**.", color=ERROR_COLOR), None
    if not interaction.guild:
        return howlbert_embed("server only", "edge-forage in a server channel.", color=ERROR_COLOR), None

    from engine.activities import _activity_block_embed, _need_guild

    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("server only", "use this in a server.", color=ERROR_COLOR), None

    world = db.get_world(guild_id)
    day = world["day_number"]

    from engine.energy import spend_energy

    _new_energy, _had_energy, verge_penalty = spend_energy(
        user, "verge_forage", discounted=is_full_forager(user)
    )

    from engine.forager_perk import grant_forager_auto_herb

    auto_herb = grant_forager_auto_herb(user, day=day, guild_id=guild_id)
    forager_note = (
        f"\n\n_forager perk: **{auto_herb}** turned up in pack territory._" if auto_herb else ""
    )

    blocked = _activity_block_embed(user, title="cannot edge-forage")
    if blocked:
        return blocked, None

    spec = VERGE_SITES[site]
    pool = herbs_for_verge(site)
    if not pool:
        return howlbert_embed("no verge herbs", "nothing configured for this site.", color=ERROR_COLOR), None

    profs = parse_proficiencies(user["skill_proficiencies"])
    season_mod = season_forage_dc_mod(world["season"])
    dc = spec["dc"] + season_mod
    penalty_note = f"\n_{verge_penalty}_" if verge_penalty else ""
    season_suffix = (
        f"\n_{season_forage_modifier_label(world['season'])} · effective dc **{dc}**._"
        if season_mod
        else f"\n_effective dc **{dc}**._"
    ) + penalty_note
    proficient = spec["skill_key"] in profs or "herblore" in profs
    result = resolve_check(
        user,
        attr_keys=spec["attrs"],
        skill=spec["skill"],
        dc=dc,
        proficient=proficient,
        skill_key=spec["skill_key"],
        game_day=day,
    )
    db.update_user(interaction.user.id, last_verge_forage_day=day)
    combat_enc: int | None = None

    if result["outcome"] == "critical_failure":
        risk, combat_enc = _verge_risk_note(
            site,
            critical=True,
            user=user,
            guild_id=guild_id,
            channel_id=interaction.channel_id,
            day=day,
        )
        if risk and combat_enc is None:
            db.adjust_mood(user["id"], -VERGE_CRIT_FAIL_MOOD)
        return howlbert_embed(
            "spooked at the verge",
            format_roll_result(result)
            + f"\n\n{spec['intro']}\n\n"
            "**Critical failure**; wrong patch, barking hearth-hound, or monster wind. Nothing gathered."
            + forager_note
            + (f"\n\n{risk}" if risk else "")
            + season_suffix,
            color=ERROR_COLOR,
        ), combat_enc

    if not result["success"]:
        risk, combat_enc = _verge_risk_note(
            site,
            user=user,
            guild_id=guild_id,
            channel_id=interaction.channel_id,
            day=day,
        )
        if risk and combat_enc is None:
            db.adjust_mood(user["id"], -VERGE_FAIL_MOOD)
        return howlbert_embed(
            "verge empty",
            format_roll_result(result)
            + f"\n\n{spec['intro']}\n\n{random.choice(spec['fail_flavor'])}"
            + forager_note
            + (f"\n\n{risk}" if risk else "")
            + season_suffix,
            color=ERROR_COLOR,
        ), combat_enc

    herb_key = _pick_verge_herb(user, site)
    from engine.herb_storage import fresh_herb_warning, grant_fresh_herb

    item_key, hoard_note = grant_fresh_herb(
        user["id"],
        herb_key=herb_key,
        guild_id=guild_id,
        day=day,
        user=user,
    )
    meta = HERBS[herb_key]
    qty_note = ""
    if result["outcome"] == "critical_success":
        grant_fresh_herb(
            user["id"],
            herb_key=herb_key,
            guild_id=guild_id,
            day=day,
            user=user,
        )
        qty_note = " (double yield!)"
    db.increment_quest_progress(interaction.user.id, "forage")

    from engine.disease_contract import try_insect_sting_exposure, try_poison_ivy_exposure

    if site == "compound":
        hazard = try_poison_ivy_exposure(user, chance=0.10) or ""
    else:
        hazard = try_insect_sting_exposure(user, chance=0.07) or ""

    site_note = (
        "_the verge turns up hardy plants of disturbed ground; some also grow deep in territory, many do not._"
        if site == "roadside"
        else "_Compound herbs need Twoleg nests, fences, and spilled seed; too risky for casual forage._"
    )
    embed = howlbert_embed(
        f"verge; {spec['label']}",
        format_roll_result(result)
        + f"\n\n{spec['intro']}\n\n{random.choice(spec['success_flavor'])}\n\n"
        f"found **{meta['name']}**{qty_note}; added to `/bones action:inventory` (`{item_key}`).\n_{meta['effect']}_"
        + fresh_herb_warning(herb_key)
        + (f"\n\n{hoard_note}" if hoard_note else "")
        + forager_note
        + (f"\n\n{hazard}" if hazard else "")
        + f"\n\n{site_note}"
        + season_suffix,
        color=SUCCESS_COLOR,
    )
    footer = "/field action:verge · costs energy"
    if season_mod:
        footer += f" · {season_forage_modifier_label(world['season'])}"
    embed.set_footer(text=footer)
    return embed, combat_enc
