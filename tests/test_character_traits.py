"""Tests for per-wolf character trait modifiers."""

import database as db
from engine.character_traits import (
    DUSK_CHARACTER_TRAITS,
    FINNPELT_CHARACTER_TRAITS,
    GASP_CHARACTER_TRAITS,
    KANAMI_CHARACTER_TRAITS,
    MIREWORT_CHARACTER_TRAITS,
    MURKVEIN_CHARACTER_TRAITS,
    SLUDGE_CHARACTER_TRAITS,
    SPLINTER_CHARACTER_TRAITS,
    canonical_traits_for_name,
    encode_character_traits,
    trait_blocks_howl,
    trait_check_adjustments,
    trait_check_disadvantage,
    trait_combat_modifier,
    trait_damage_reduction,
    trait_hunt_multiplier,
    trait_treat_heal_bonus,
)
from engine.dice import resolve_check


def _row(**kwargs):
    base = {
        "exhaustion": 0,
        "active_injuries": "[]",
        "genetic_conditions": "[]",
        "disease": None,
        "great_pack": "mistmoor",
        "character_traits": encode_character_traits(MIREWORT_CHARACTER_TRAITS),
        "attr_str": 2,
        "attr_dex": 3,
        "attr_con": 4,
        "attr_int": 5,
        "attr_cha": 2,
        "attr_wis": 8,
        "skill_proficiencies": '["herblore", "medicine"]',
    }
    base.update(kwargs)
    return base


def test_barkhollow_forage_herblore_not_hollow_chest():
    from engine.character_traits import BARKHOLLOW_CHARACTER_TRAITS

    user = _row(
        great_pack="thistlehide",
        wolf_role="forager",
        character_traits=encode_character_traits(BARKHOLLOW_CHARACTER_TRAITS),
        attr_int=3,
        attr_wis=4,
        attr_con=1,
    )
    mod, names = trait_check_adjustments(user, ("attr_int", "attr_wis"), skill_key="herblore")
    assert mod == 10
    assert "Foraging" in names
    assert "Herblore" in names
    assert "Survival" in names
    assert "Hollow Chest" not in names


def test_mirewort_herblore_bonus():
    user = _row()
    mod, names = trait_check_adjustments(user, ("attr_int",), skill_key="herblore")
    assert mod == 6
    assert "Herbal Mastery (Swamp)" in names


def test_mirewort_medicine_bonus():
    user = _row()
    mod, names = trait_check_adjustments(user, ("attr_wis",), skill_key="medicine")
    assert mod == 5
    assert "Wound-Tending" in names


def test_mirewort_swamp_nav_outside_mistmoor():
    user = _row(great_pack="thistlehide")
    mod, names = trait_check_adjustments(user, ("attr_con", "attr_str"), skill_key="survival")
    assert mod == 0
    assert "Physically Frail" not in names
    assert "Swamp Navigation" not in names
    assert trait_combat_modifier(user) == -4


def test_mirewort_frail_and_detachment_stack():
    user = _row()
    mod, names = trait_check_adjustments(user, ("attr_cha",), skill_key="persuasion")
    assert mod == -2
    assert names == ["Morbid Detachment"]


def test_mirewort_combat_penalty():
    user = _row()
    assert trait_combat_modifier(user) == -4


def test_splinter_stealth_bonus():
    user = _row(
        great_pack="rogue",
        character_traits=encode_character_traits(SPLINTER_CHARACTER_TRAITS),
        attr_dex=4,
        skill_proficiencies='["stealth", "tracking"]',
    )
    mod, names = trait_check_adjustments(user, ("attr_dex",), skill_key="stealth")
    assert mod == 4
    assert "Stealth" in names
    assert "Missing Leg" not in names


def test_resolve_check_includes_trait_modifier():
    from unittest.mock import patch

    import engine.dice as dice_mod

    user = _row()
    with patch.object(dice_mod, "roll_d20", return_value=10):
        result = resolve_check(
            user,
            attr_keys=("attr_int",),
            skill="Herblore",
            dc=15,
            proficient=True,
            skill_key="herblore",
        )
    assert result["trait_modifier"] == 6
    assert result["total"] == 16
    assert result["success"] is True


def test_kanami_blindness_penalties():
    user = _row(
        great_pack="thistlehide",
        character_traits=encode_character_traits(KANAMI_CHARACTER_TRAITS),
    )
    mult, note = trait_hunt_multiplier(user)
    assert mult == 0.65
    assert "Total Blindness" in note
    assert trait_check_disadvantage(user, ("attr_wis",), skill_key="persuasion")
    assert not trait_check_disadvantage(user, ("attr_wis",), skill_key="stealth")


def test_murkvein_no_tail_penalties():
    user = _row(
        great_pack="mistmoor",
        character_traits=encode_character_traits(MURKVEIN_CHARACTER_TRAITS),
    )
    mult, _ = trait_hunt_multiplier(user)
    assert mult == 0.9
    assert trait_check_disadvantage(user, ("attr_dex",), skill_key="survival")


def test_eltanin_canonical_traits():
    traits = canonical_traits_for_name("Eltanin")
    assert traits is not None
    mod, names = trait_check_adjustments(
        _row(
            great_pack="thistlehide",
            character_traits=encode_character_traits(traits),
            skill_proficiencies='["hunting", "tracking"]',
        ),
        ("attr_str",),
        skill_key="hunting",
    )
    assert mod == 3
    assert "Bold Hunter" in names


def test_gasp_frail_hunt_penalty():
    user = _row(
        great_pack="mistmoor",
        character_traits=encode_character_traits(GASP_CHARACTER_TRAITS),
    )
    mult, note = trait_hunt_multiplier(user)
    assert mult == 0.45
    assert "Frail" in note


def test_dusk_blocks_howl():
    user = _row(
        great_pack="mistmoor",
        character_traits=encode_character_traits(DUSK_CHARACTER_TRAITS),
    )
    blocked, name = trait_blocks_howl(user)
    assert blocked
    assert name == "Rasping Voice"


def test_sludge_hunt_abort_roll(monkeypatch):
    import random

    user = _row(
        great_pack="mistmoor",
        character_traits=encode_character_traits(SLUDGE_CHARACTER_TRAITS),
    )
    monkeypatch.setattr(random, "random", lambda: 0.0)
    from engine.character_traits import roll_trait_hunt_abort

    aborted, name = roll_trait_hunt_abort(user)
    assert aborted
    assert name == "Superstitious"


def test_finnpelt_damage_reduction():
    user = _row(
        great_pack="thistlehide",
        character_traits=encode_character_traits(FINNPELT_CHARACTER_TRAITS),
    )
    reduction, label = trait_damage_reduction(user)
    assert reduction == 2
    assert label == "Armor-Like Coat"


def test_mirewort_treat_heal_bonus():
    user = _row(
        great_pack="mistmoor",
        character_traits=encode_character_traits(MIREWORT_CHARACTER_TRAITS),
    )
    assert trait_treat_heal_bonus(user) == 1
