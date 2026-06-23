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


def _verge_risk_note(site: str, *, critical: bool = False) -> str:
    spec = VERGE_SITES[site]
    mood = VERGE_CRIT_FAIL_MOOD if critical else VERGE_FAIL_MOOD
    if site == "roadside":
        if critical and random.random() < VERGE_TOXIC_MISID_CHANCE:
            db_note = (
                "\n\n_You grabbed a toxic look-alike in the ditch; spit it out fast. "
                "Get a Medic to check you._"
            )
        else:
            db_note = ""
        if random.random() < VERGE_MONSTER_NEAR_MISS_CHANCE or critical:
            return random.choice(spec["risk_flavor"]).format(mood=mood) + db_note
        return ""
    if site == "compound":
        if random.random() < VERGE_COMPOUND_DOG_CHANCE or critical:
            return random.choice(spec["risk_flavor"]).format(mood=mood)
        return ""
    return ""


def try_verge_forage(interaction, site: str = "roadside"):
    from engine.herb_habitat import herbs_for_verge
    from engine.role_privileges import can_verge_forage_again

    user = db.get_user(interaction.user.id)
    if not user:
        return howlbert_embed("Not Registered", color=ERROR_COLOR)
    if site not in VERGE_SITES:
        return howlbert_embed("Unknown Verge", "Pick **roadside** or **compound**.", color=ERROR_COLOR)
    if not interaction.guild:
        return howlbert_embed("Server Only", "Edge-forage in a server channel.", color=ERROR_COLOR)

    from engine.activities import _activity_block_embed, _need_guild

    guild_id = _need_guild(interaction)
    if not guild_id:
        return howlbert_embed("Server Only", "Use this in a server.", color=ERROR_COLOR)

    world = db.get_world(guild_id)
    day = world["day_number"]
    if not can_verge_forage_again(user, day):
        return howlbert_embed(
            "Already Edged",
            "You've foraged the **verge** this sunrise; territory forage is separate (`/field action:forage`).",
            color=ERROR_COLOR,
        )

    blocked = _activity_block_embed(user, title="Cannot Edge-Forage")
    if blocked:
        return blocked

    spec = VERGE_SITES[site]
    pool = herbs_for_verge(site)
    if not pool:
        return howlbert_embed("No Verge Herbs", "Nothing configured for this site.", color=ERROR_COLOR)

    profs = parse_proficiencies(user["skill_proficiencies"])
    dc = spec["dc"] + season_forage_dc_mod(world["season"])
    season_suffix = (
        f"\n_{season_forage_modifier_label(world['season'])}_"
        if season_forage_dc_mod(world["season"])
        else ""
    )
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

    if result["outcome"] == "critical_failure":
        risk = _verge_risk_note(site, critical=True)
        if risk:
            db.adjust_mood(user["id"], -VERGE_CRIT_FAIL_MOOD)
        return howlbert_embed(
            "Spooked at the Verge",
            format_roll_result(result)
            + f"\n\n{spec['intro']}\n\n"
            "**Critical failure**; wrong patch, barking hearth-hound, or monster wind. Nothing gathered."
            + (f"\n\n{risk}" if risk else "")
            + season_suffix,
            color=ERROR_COLOR,
        )

    if not result["success"]:
        risk = _verge_risk_note(site)
        if risk:
            db.adjust_mood(user["id"], -VERGE_FAIL_MOOD)
        return howlbert_embed(
            "Verge Empty",
            format_roll_result(result)
            + f"\n\n{spec['intro']}\n\n{random.choice(spec['fail_flavor'])}"
            + (f"\n\n{risk}" if risk else "")
            + season_suffix,
            color=ERROR_COLOR,
        )

    herb_key = _pick_verge_herb(user, site)
    from engine.herb_storage import fresh_herb_warning, grant_fresh_herb

    stack_id, hoard_note = grant_fresh_herb(
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

    site_note = (
        "_Roadside herbs only grow on disturbed ground; never in deep territory._"
        if site == "roadside"
        else "_Compound herbs need Twoleg nests, fences, and spilled seed; too risky for casual forage._"
    )
    embed = howlbert_embed(
        f"Verge; {spec['label']}",
        format_roll_result(result)
        + f"\n\n{spec['intro']}\n\n{random.choice(spec['success_flavor'])}\n\n"
        f"Found **{meta['name']}**{qty_note}; fresh stack `#{stack_id}` in herb bag.\n_{meta['effect']}_"
        + fresh_herb_warning(herb_key)
        + (f"\n\n{hoard_note}" if hoard_note else "")
        + f"\n\n{site_note}"
        + season_suffix,
        color=SUCCESS_COLOR,
    )
    embed.set_footer(text="/field action:verge · once per sunrise · Foragers unlimited")
    return embed
