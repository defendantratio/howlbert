"""Basil skill check catalog; DCs from pack survival rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillScenario:
    key: str
    label: str
    category: str
    dc: int
    skill_key: str
    attr_keys: tuple[str, ...]
    skill_label: str
    success: str
    failure: str
    crit_fail: str | None = None
    opposed: bool = False
    fail_damage: tuple[int, int] | None = None
    fail_mood: int = 0
    success_flag: str | None = None
    requires_opponent: bool = False


@dataclass(frozen=True)
class OpposedSpec:
    """Defender roll for opposed contests."""

    defender_skill_key: str
    defender_attr_keys: tuple[str, ...]
    defender_skill_label: str
    defender_flat_bonus: int = 0
    plant_dc_range: tuple[int, int] | None = None  # taste-test vs plant, no wolf opponent


def _s(
    key: str,
    label: str,
    category: str,
    dc: int,
    skill_key: str,
    attr_keys: tuple[str, ...],
    skill_label: str,
    success: str,
    failure: str,
    **kw,
) -> SkillScenario:
    return SkillScenario(
        key=key,
        label=label,
        category=category,
        dc=dc,
        skill_key=skill_key,
        attr_keys=attr_keys,
        skill_label=skill_label,
        success=success,
        failure=failure,
        **kw,
    )


SKILL_SCENARIOS: dict[str, SkillScenario] = {}

def _reg(*scenarios: SkillScenario) -> None:
    for sc in scenarios:
        SKILL_SCENARIOS[sc.key] = sc


_reg(
    _s("track_fresh", "Follow fresh trail (<1 hour)", "tracking", 8, "tracking", ("attr_int",), "Tracking",
       "You hold the hot scent; prey is close.", "Trail scattered; prey gone."),
    _s("track_recent", "Follow recent trail (1-6 hours)", "tracking", 12, "tracking", ("attr_int",), "Tracking",
       "Scent line holds through brush.", "Trail too cold to pay out."),
    _s("track_cold", "Follow cold trail (6-24 hours)", "tracking", 15, "tracking", ("attr_int",), "Tracking",
       "Patient work; the trail opens.", "Lost the thread."),
    _s("track_very_cold", "Follow very cold trail (1-3 days)", "tracking", 18, "tracking", ("attr_int",), "Tracking",
       "Old sign still whispers direction.", "Nothing left to read."),
    _s("track_faint", "Follow faint trail (3+ days)", "tracking", 25, "tracking", ("attr_int",), "Tracking",
       "Legendary nose-work; faint scent pulled from stone.", "Even ideal weather can't save this trail.",
       crit_fail="Wrong quarry; wasted the sunrise."),
    _s("track_prints", "Identify paw prints in mud/snow", "tracking", 10, "tracking", ("attr_int",), "Tracking",
       "Species and direction clear.", "Mud lies; can't be sure."),
    _s("track_pack_size", "Determine pack size from tracks", "tracking", 12, "tracking", ("attr_int",), "Tracking",
       "You count pads and drag marks.", "Could be one wolf or five."),
    _s("track_blood", "Track injured wolf by blood scent", "tracking", 10, "tracking", ("attr_int",), "Tracking",
       "Copper line leads on.", "Blood scent washed away."),
    _s("track_water", "Follow trail through water", "tracking", 18, "tracking", ("attr_int",), "Tracking",
       "Scent pools on the far bank.", "Scent washed away completely."),
    _s("track_count_smell", "Count wolves by smell alone", "tracking", 12, "tracking", ("attr_int",), "Tracking",
       "You count hearts by stink and breath.", "Wrong count (off by 1-3); could be a trap."),
    _s("track_scat_sign", "Pregnancy or illness from scat/urine", "tracking", 15, "tracking", ("attr_wis",), "Tracking",
       "Body signs read plain.", "Can't parse the sign."),
    _s("track_covered", "Follow deliberately covered trail", "tracking", 15, "tracking", ("attr_int",), "Tracking",
       "You pierce the cover-up.", "They hid their passage well.", opposed=True),
    _s("track_scent_known", "Identify known wolf's scent", "tracking", 10, "tracking", ("attr_int",), "tracking",
       "you'd know that musk anywhere.", "Scent muddled; not certain."),
    _s("track_scent_once", "Identify scent smelled once", "tracking", 18, "tracking", ("attr_int",), "Tracking",
       "Memory and nose align.", "Could be anyone."),
)

_reg(
    _s("stealth_leaves", "Move silent through leaves/snow", "stealth", 10, "stealth", ("attr_dex",), "Stealth",
       "Paws whisper over the ground.", "Twigs betray you."),
    _s("stealth_hide_grass", "Hide in grass or undergrowth", "stealth", 12, "stealth", ("attr_dex",), "Stealth",
       "You vanish into cover.", "Ears still find you."),
    _s("stealth_sneak_prey", "Sneak up on prey", "stealth", 15, "stealth", ("attr_dex",), "Stealth",
       "First strike will have advantage.", "Prey bolts before you close.",
       success_flag="sneak_advantage"),
    _s("stealth_no_scent", "Cross enemy territory without scent", "stealth", 18, "stealth", ("attr_dex",), "Stealth",
       "Wind favors you; no marker left.", "Patrol catches your line."),
    _s("stealth_hide_predator", "Hide from a predator", "stealth", 20, "stealth", ("attr_dex",), "Stealth",
       "Heart hammering; it passes.", "Found; run or fight.",
       fail_damage=(1, 4)),
)

_reg(
    _s("howl_locate", "Locate lost packmate (clear weather)", "howling", 6, "persuasion", ("attr_cha",), "Howling",
       "Answer howl pins direction.", "Echoes tangle; no fix."),
    _s("howl_message", "Howl a complex message", "howling", 10, "persuasion", ("attr_cha",), "Howling",
       "Pack reads your meaning.", "Garbled; misread."),
    _s("howl_warning", "Territorial warning howl", "howling", 12, "persuasion", ("attr_cha",), "Howling",
       "Border claimed.", "Sounds like fear, not law."),
    _s("howl_imitate", "Imitate another wolf's howl", "howling", 15, "persuasion", ("attr_cha",), "howling",
       "deception holds.", "caught in the lie."),
    _s("howl_storm", "howl through forest or storm", "howling", 15, "persuasion", ("attr_cha",), "howling",
       "voice carries.", "range halved; only nearby wolves catch it."),
)

_reg(
    _s("social_intimidate", "intimidate lone rival", "social", 12, "intimidation", ("attr_cha",), "intimidation",
       "they yield ground.", "they call your bluff."),
    _s("social_persuade_alpha", "persuade alpha (minor decision)", "social", 15, "persuasion", ("attr_cha",), "persuasion",
       "alpha bends.", "alpha annoyed; standing may slip.", fail_mood=3),
    _s("social_lie", "lie to packmate (small matter)", "social", 12, "persuasion", ("attr_cha",), "persuasion",
       "believed.", "ears twitch; not fooled."),
    _s("social_calm_pup", "calm frightened pup", "social", 8, "persuasion", ("attr_cha",), "persuasion",
       "whimper fades.", "pup still shakes."),
    _s("social_truce", "negotiate rival-pack truce", "social", 18, "persuasion", ("attr_cha",), "persuasion",
       "both sides lower hackles.", "talk breaks down."),
    _s("social_challenge_alpha", "challenge alpha (3+ supporters)", "social", 20, "intimidation", ("attr_cha",), "intimidation",
       "challenge lodged.", "pack laughs you off."),
    _s("social_read_alpha", "read alpha's mood", "social", 12, "persuasion", ("attr_wis",), "Insight",
       "You know if it's a good time to ask.", "Alpha's face is stone."),
    _s("social_dominance", "Assert dominance (opposed)", "social", 15, "intimidation", ("attr_cha",), "Intimidation",
       "Lower rank yields.", "Stared down.", opposed=True),
    _s("social_defuse", "Defuse packmate fight (opposed)", "social", 15, "persuasion", ("attr_cha",), "Persuasion",
       "Teeth unbarred.", "Caught between them.", opposed=True, fail_damage=(1, 4)),
    _s("social_apologize", "Apologize after breaking pack rule", "social", 15, "persuasion", ("attr_cha",), "Persuasion",
       "Forgiveness grudging or real.", "Standing still bleeds.", fail_mood=5),
)

_reg(
    _s("spirit_vision", "Interpret vision or dream", "spiritual", 15, "medicine", ("attr_wis",), "Medicine",
       "Symbol resolves.", "Meaning slips away."),
    _s("spirit_omen", "Interpret Maw omen", "spiritual", 12, "medicine", ("attr_wis",), "Medicine",
       "Omen read.", "Misread; wrong lesson."),
    _s("spirit_ancestors", "Ask ancestors at sacred site", "spiritual", 20, "medicine", ("attr_wis",), "Medicine",
       "One-word answer on the wind.", "Silence.",
       crit_fail="Nightmare visions: +1 exhaustion.", fail_mood=8),
    _s("spirit_cleanse", "Cleansing ritual (sagewort/lavender/rowan)", "spiritual", 15, "herblore", ("attr_wis",), "Herblore",
       "Curse scent lifts.", "Smoke wrong; curse clings."),
    _s("spirit_recall_patch", "Recall herb patch from last season", "spiritual", 15, "herblore", ("attr_int",), "Herblore",
       "Ground remembered.", "Patch gone or overgrown."),
    _s("spirit_recognize", "Recognize wolf met briefly", "spiritual", 12, "tracking", ("attr_int",), "Tracking",
       "Scent and silhouette match.", "Stranger still."),
    _s("spirit_prophecy", "Recall prophecy without misquote", "spiritual", 10, "medicine", ("attr_wis",), "Medicine",
       "Words exact.", "Misquoted; bad omen."),
    _s("spirit_learn_herb", "Learn herb from Medic", "spiritual", 12, "herblore", ("attr_int",), "Herblore",
       "Properties learned.", "Confused with lookalike."),
)

_reg(
    _s("surv_river", "Cross fast river", "survival", 12, "survival", ("attr_str", "attr_con"), "Survival",
       "Far bank gained.", "Swept downstream.", fail_damage=(1, 4)),
    _s("surv_swim", "Swim across lake", "survival", 10, "survival", ("attr_con",), "Survival",
       "Far shore.", "Cramp or panic.", fail_damage=(1, 4)),
    _s("surv_climb", "Climb steep rocky slope", "survival", 15, "survival", ("attr_str",), "Survival",
       "Summit.", "Fall.", fail_damage=(1, 6)),
    _s("surv_blizzard_shelter", "Find shelter in blizzard", "survival", 15, "survival", ("attr_con", "attr_wis"), "Survival",
       "Den or lee found.", "Exposure worsens.", fail_mood=0, success_flag="shelter"),
    _s("surv_dig_den", "Dig out buried den (snowslide)", "survival", 18, "survival", ("attr_str",), "Survival",
       "Paws break through.", "Still buried."),
    _s("surv_swamp", "Navigate swamp without sinking", "survival", 15, "survival", ("attr_con",), "Survival",
       "Solid line through mire.", "Stuck; hours lost.", fail_mood=4),
    _s("surv_stabilize", "Stabilize dying wolf", "survival", 15, "medicine", ("attr_wis",), "Medicine",
       "Breath steadied at 1 HP.", "Slips toward death."),
    _s("surv_set_bone", "Set bone without comfrey", "survival", 20, "medicine", ("attr_wis",), "Medicine",
       "Splint holds.", "Limp may be permanent.", crit_fail="Permanent limp risk."),
    _s("surv_thorn", "Remove deep thorn/splinter", "survival", 10, "medicine", ("attr_dex",), "Medicine",
       "Out clean.", "Driven deeper; infection risk."),
    _s("surv_diagnose", "Diagnose illness", "survival", 12, "medicine", ("attr_wis",), "Medicine",
       "Illness named.", "Wrong guess."),
)

_reg(
    _s("prep_chew_poultice", "Chew poultice correctly", "herb_prep", 8, "herblore", ("attr_int",), "Herblore",
       "Paste ready.", "Mush; wasted chew."),
    _s("prep_mix_tonic", "Mix tonic without contamination", "herb_prep", 12, "herblore", ("attr_int",), "Herblore",
       "Clean tonic.", "Contaminated; half effect or vomit."),
    _s("prep_dry_storage", "Dry herbs for winter storage", "herb_prep", 10, "herblore", ("attr_int",), "Herblore",
       "Stores months.", "Poor dry; potency lost in 1 month."),
    _s("prep_decoct", "Decoct in hot spring water", "herb_prep", 15, "herblore", ("attr_int",), "Herblore",
       "Double potency.", "Ruined batch.", crit_fail="Batch boiled over; stores ruined."),
    _s("prep_antidote", "Administer antidote in time", "herb_prep", 18, "medicine", ("attr_wis",), "Medicine",
       "Venom checked.", "Too slow."),
    _s("prep_sedative", "Mix sedative (poppy + honey)", "herb_prep", 8, "herblore", ("attr_int",), "Herblore",
       "Sleep draught.", "Weak or bitter."),
    _s("prep_incomplete_antidote", "Antidote from incomplete ingredients", "herb_prep", 20, "herblore", ("attr_int",), "Herblore",
       "Poison halved.", "Poison accelerated.", crit_fail="Poison accelerated."),
    _s("prep_preserve_rare", "Preserve rare herb for winter", "herb_prep", 15, "herblore", ("attr_int",), "Herblore",
       "Lasts 6 moons.", "Fades in 1 moon."),
    _s("prep_taste_test", "Taste-test unknown plant toxicity", "herb_prep", 12, "survival", ("attr_con",), "Survival",
       "Edible or spat out in time.", "Poisoned tongue.", opposed=True, fail_damage=(1, 4)),
)

_reg(
    _s("craft_splint", "Bind splint with sticks/vines", "crafting", 12, "survival", ("attr_dex",), "Survival",
       "Limb held.", "Splint slips."),
    _s("craft_pouch", "Fashion bark or hide pouch", "crafting", 10, "survival", ("attr_dex",), "Survival",
       "Pouch ready.", "Falls apart."),
    _s("craft_travois", "Build travois (2 wolves)", "crafting", 15, "survival", ("attr_str",), "Survival",
       "Half-speed haul.", "Travois breaks in 1 hour."),
    _s("nav_landmark_known", "Find known landmark (familiar)", "navigation", 6, "survival", ("attr_wis",), "Survival",
       "Landmark in sight.", "Wrong ridge."),
    _s("nav_landmark_unknown", "Find landmark (unfamiliar)", "navigation", 12, "survival", ("attr_wis",), "Survival",
       "Territory maps in your head.", "Lost."),
    _s("nav_scent_marker", "Recognize neighbor scent marker", "navigation", 10, "tracking", ("attr_int",), "Tracking",
       "Pack and border known.", "Unfamiliar mark."),
    _s("nav_trap_detect", "Detect herding into trap", "navigation", 15, "survival", ("attr_int",), "Survival",
       "Ambush smelled.", "Walked into it.", opposed=True, fail_damage=(2, 8)),
    _s("nav_blizzard_camp", "Find camp after blizzard chase", "navigation", 18, "survival", ("attr_wis",), "Survival",
       "Den warmth.", "Sleep outside.", crit_fail="Crossed into enemy territory."),
)

SKILL_CATEGORIES = {
    "tracking": "Tracking & scent",
    "stealth": "Stealth & evasion",
    "howling": "Howling & communication",
    "social": "Social & pack dynamics",
    "spiritual": "Spiritual & memory",
    "survival": "Environmental survival",
    "herb_prep": "Herb preparation",
    "crafting": "Crafting",
    "navigation": "Navigation",
}


def scenarios_for_category(category: str) -> list[SkillScenario]:
    return [s for s in SKILL_SCENARIOS.values() if s.category == category]


def scenario_keys_for_category(category: str) -> list[str]:
    return [s.key for s in scenarios_for_category(category)]


OPPOSED_SPECS: dict[str, OpposedSpec] = {
    "track_covered": OpposedSpec(
        "survival", ("attr_dex", "attr_con"), "Dexterity + Survival"
    ),
    "social_dominance": OpposedSpec(
        "intimidation", ("attr_cha", "attr_wis"), "Charisma + Wisdom"
    ),
    "social_defuse": OpposedSpec(
        "intimidation", ("attr_cha",), "Charisma (higher fighter)", defender_flat_bonus=2
    ),
    "prep_taste_test": OpposedSpec(
        "survival", ("attr_con",), "Plant toxicity", plant_dc_range=(12, 20)
    ),
    "nav_trap_detect": OpposedSpec(
        "persuasion", ("attr_cha", "attr_int"), "Enemy coordination", defender_flat_bonus=3
    ),
}


def opponent_required(scenario_key: str) -> bool:
    scenario = SKILL_SCENARIOS.get(scenario_key)
    if not scenario or not scenario.opposed:
        return False
    spec = OPPOSED_SPECS.get(scenario_key)
    return spec is None or spec.plant_dc_range is None
