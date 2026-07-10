"""Herb wiring tests; flea ward, frostbite, burial ritual, herb_prep batches."""

from __future__ import annotations

from unittest.mock import patch

from engine.bury_ritual import bury_carcass
from engine.herb_buffs import (
    apply_supplemental_herb,
    disease_save_uses_advantage,
    flea_ward_active,
    get_buffs,
    grant_frostbite,
    herb_storage_multiplier,
    pain_relief_active,
)
from engine.herb_prep_batches import apply_herb_prep_outcome
from engine.disease_contract import try_hunt_flea_exposure


class Row(dict):
    def keys(self):
        return super().keys()


def _user(**kw):
    base = {
        "id": 1,
        "discord_id": 1,
        "hp": 20,
        "mood": 50,
        "herb_buffs": "{}",
        "last_rest_day": 5,
        "disease": "",
        "exhaustion": 0,
        "condition": "healthy",
        "active_injuries": "[]",
        "skill_proficiencies": "[]",
    }
    base.update(kw)
    return Row(base)


def test_flea_ward_blocks_hunt_fleas():
    user = _user(herb_buffs='{"flea_ward_until_day": 10}')
    assert flea_ward_active(user, 5)
    assert try_hunt_flea_exposure(user, day=5) is None


def test_mugwort_grants_flea_ward():
    user = _user()
    result = apply_supplemental_herb("mugwort", user, day=5, outcome="no_effect")
    assert result
    user["herb_buffs"] = result["fields"]["herb_buffs"]
    assert "flea ward" in result["message"].lower()
    assert flea_ward_active(user, 5)


def test_prickly_ash_clears_frostbite():
    user = _user(herb_buffs='{"frostbite_until_day": 12}')
    fields = grant_frostbite(user, day=5)
    user["herb_buffs"] = fields["herb_buffs"]
    result = apply_supplemental_herb("prickly_ash", user, day=5, outcome="no_effect")
    assert result
    assert "frostbite" in result["message"].lower() or "frozen" in result["message"].lower()
    user["herb_buffs"] = result["fields"]["herb_buffs"]
    assert "frostbite_until_day" not in get_buffs(user)


def test_heather_when_ill():
    user = _user(disease="diarrhea:active")
    result = apply_supplemental_herb("heather", user, day=5, outcome="no_effect")
    assert result
    assert "disease save" in result["message"].lower()


def test_bury_without_herb():
    user = _user()
    stack = {"id": 99, "wolf_id": 1, "prey_key": "rabbit"}

    with patch("engine.bury_ritual.db.get_prey_stack", return_value=stack), patch(
        "engine.bury_ritual.db.remove_prey_stack"
    ), patch("engine.bury_ritual.db.adjust_mood", return_value=52):
        ok, body = bury_carcass(user, 99, day=1)
    assert ok
    assert "+2" in body


def test_prep_chew_poultice_grants_pain_relief():
    user = _user()
    fields, _, lines = apply_herb_prep_outcome(
        user, "prep_chew_poultice", success=True, outcome="success", day=5
    )
    assert fields.get("herb_buffs")
    user["herb_buffs"] = fields["herb_buffs"]
    assert pain_relief_active(user, 5)
    assert any("pain" in line.lower() for line in lines)


def test_prep_dry_storage_grants_storage_buff():
    user = _user()
    fields, _, lines = apply_herb_prep_outcome(
        user, "prep_dry_storage", success=True, outcome="success", day=5
    )
    user["herb_buffs"] = fields["herb_buffs"]
    assert herb_storage_multiplier(user, 5) == 1.5
    assert any("50%" in line for line in lines)


def test_prep_antidote_grants_disease_save():
    user = _user(disease="mild_poison:venom")
    fields, cond, lines = apply_herb_prep_outcome(
        user,
        "prep_antidote",
        success=True,
        outcome="critical_success",
        day=5,
    )
    assert fields.get("disease_save_buff") == 1
    user.update(fields)
    assert disease_save_uses_advantage(user)
    assert cond.get("clear_disease") or cond.get("disease")
    assert lines


def test_prep_sedative_grants_calm():
    user = _user()
    fields, _, lines = apply_herb_prep_outcome(
        user, "prep_sedative", success=True, outcome="success", day=5
    )
    buffs = get_buffs(_user(herb_buffs=fields["herb_buffs"]))
    assert buffs.get("calm_until_day") == 6
    assert any("sedative" in line.lower() or "calm" in line.lower() for line in lines)


if __name__ == "__main__":
    test_flea_ward_blocks_hunt_fleas()
    test_mugwort_grants_flea_ward()
    test_prickly_ash_clears_frostbite()
    test_heather_when_ill()
    test_bury_without_herb()
    test_prep_chew_poultice_grants_pain_relief()
    test_prep_dry_storage_grants_storage_buff()
    test_prep_antidote_grants_disease_save()
    test_prep_sedative_grants_calm()
    print("test_herb_wiring: ok")
