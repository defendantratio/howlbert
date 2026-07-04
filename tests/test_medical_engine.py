"""Engine-layer medical and herb mechanics."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.conditions import injury_heal_note, progress_injuries, treat_with_herb
from engine.death_saves import stabilize_bonus, stabilize_check
from engine.disease_effects import disease_check_adjustments
from engine.herb_buffs import (
    apply_cough_dose,
    bone_heal_days_reduction,
    infection_ward_active,
    injury_heal_multiplier,
    is_cough_suppression_herb,
)
from engine.herb_storage import effective_storage_limits
from engine.long_term_injuries import fear_trigger_check, matching_fear_triggers
from engine.medical_access import can_medic_treat_cross_pack
from engine.movement_penalties import apply_movement_hunt_penalty
from engine.season_effects import winter_forage_fail_spoil_chance
from engine.shop_items import roll_herb_bundle_heal, use_herb_bundle
from engine.travel_hazards import travel_hazard_dc
from herbs import HERBS


class Row:
    def __init__(self, **kw):
        self._d = kw

    def __getitem__(self, k):
        return self._d[k]

    def keys(self):
        return self._d.keys()


def test_injury_heal_halved_display():
    import re

    def heal_days(note):
        m = re.search(r"~(\d+)d with rest", note)
        return int(m.group(1)) if m else None

    healthy = Row(herb_buffs="{}")
    halved = Row(herb_buffs='{"injury_heal_halved": true}')
    base_days = heal_days(injury_heal_note("sprained_leg", {"sprained_leg": 1}, day=5, user=healthy))
    halved_days = heal_days(injury_heal_note("sprained_leg", {"sprained_leg": 1}, day=5, user=halved))
    # the buff visibly speeds recovery: fewer projected days than without it
    assert base_days is not None and halved_days is not None
    assert halved_days < base_days
    assert injury_heal_multiplier(halved) == 0.5


def test_bone_heal_days_reduction():
    user = Row(herb_buffs='{"bone_heal_days_reduced": 7}')
    assert bone_heal_days_reduction(user) == 7


def test_infection_ward_skips_save():
    user = Row(
        herb_buffs='{"infection_ward_until_day": 10}',
        active_injuries='["infected_wound"]',
        last_rest_day=5,
        hp=8,
        exhaustion=0,
        skill_proficiencies="[]",
        attr_wis=3,
        attr_con=3,
    )
    assert infection_ward_active(user, 8)
    out = progress_injuries(user, day=8)
    assert any("ward" in m.lower() for m in out["messages"])
    assert out["hp_loss"] == 0


def test_cough_suppression_not_hard_cure():
    user = Row(disease="mild", active_injuries="[]")
    assert treat_with_herb(user, "wild_cherry_bark", HERBS["wild_cherry_bark"]) == "symptom_ease"
    assert is_cough_suppression_herb("thyme")


def test_cough_dose_tracking():
    user = Row(disease="mild", herb_buffs="{}", discord_id=1, id=1)
    cured, fields, msg = apply_cough_dose(user, "coltsfoot", day=1)
    assert cured
    assert "1/1" in msg
    user2 = Row(disease="mild", herb_buffs="{}", discord_id=2, id=2)
    cured2, _, msg2 = apply_cough_dose(user2, "chickweed", day=1)
    assert not cured2
    assert "1/3" in msg2


def test_pupcough_effects():
    active = Row(disease="pupcough:active", herb_buffs="{}", last_rest_day=3)
    mod, dis = disease_check_adjustments(active, ("attr_dex",))
    assert dis is True
    weak = Row(disease="pupcough:weak_lungs", herb_buffs="{}", last_rest_day=3)
    mod2, dis2 = disease_check_adjustments(weak, ("attr_con",))
    assert mod2 == -1
    assert dis2 is False


def test_limp_movement_penalty():
    user = Row(
        long_term_injuries='["limp"]',
        exhaustion=0,
        active_injuries="[]",
        disease="",
    )
    amount, note = apply_movement_hunt_penalty(100, user)
    assert amount == 75
    assert "Limp" in note


def test_stabilize_herb_bonus():
    from engine.character import attr_modifier

    assert stabilize_bonus(oak_bark=True, cattail=True, yarrow=True) == 6
    healer = Row(attr_wis=4, skill_proficiencies='["medicine"]')
    check = stabilize_check(healer, oak_bark=True)
    assert check["modifier"] == attr_modifier(4) + 2


def test_cross_pack_medic_block():
    surgeon = Row(id=1, pack_id=10)
    patient = Row(id=2, pack_id=20)
    ok, msg = can_medic_treat_cross_pack(surgeon, patient, guild_id=1)
    assert ok or "standing" in msg.lower()
    ok_em, _ = can_medic_treat_cross_pack(
        surgeon, patient, guild_id=1, emergency_stabilize=True
    )
    assert ok_em


def test_travel_and_season_hooks():
    assert travel_hazard_dc("river", season="spring") == 14
    assert winter_forage_fail_spoil_chance("winter") > 0
    assert winter_forage_fail_spoil_chance("spring") == 0


def test_beech_leaves_infection_ward():
    import json

    from engine.herb_treatment import apply_flavor_herb

    user = Row(
        disease="",
        exhaustion=0,
        mood=50,
        hp=10,
        max_hp=10,
        herb_buffs="{}",
        last_rest_day=5,
    )
    flavor = apply_flavor_herb("beech_leaves", user, day=5)
    assert flavor and flavor.get("kind") == "infection_ward"
    assert "infection ward" in flavor["message"].lower()
    buffs = json.loads(flavor["fields"]["herb_buffs"])
    assert buffs.get("infection_ward_until_day") == 6
    assert buffs.get("herb_storage_bonus_until_day") == 19


def test_herb_guide_beech_hint():
    from engine.herb_guide import _usage_hint
    from herbs import HERBS

    hint = _usage_hint("beech_leaves", HERBS["beech_leaves"])
    assert "Flavor effect" not in hint
    assert "infection ward" in hint.lower()


def test_herb_storage_multiplier():
    user = Row(herb_buffs='{"herb_storage_bonus_until_day": 20}', last_rest_day=5)
    fresh, prep, dried = effective_storage_limits(user, day=10)
    assert fresh >= 1
    assert prep >= 5


def test_herb_bundle_heal():
    user = Row(hp=5, max_hp=10, attr_con=3)
    heal = roll_herb_bundle_heal()
    assert 2 <= heal <= 5


def test_fear_trigger_match():
    user = Row(long_term_injuries='["fear:water"]', attr_wis=3)
    assert "water" in matching_fear_triggers(user, fear_context="spring_river", skill_key="survival")
    dis, note = fear_trigger_check(
        user,
        fear_context="river crossing",
        skill_key="survival",
        game_day=1,
    )
    assert isinstance(dis, bool)
