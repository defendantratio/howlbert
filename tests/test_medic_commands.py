"""Medic / vitals engine helpers; run: python -m tests.test_medic_commands"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class Row(dict):
    def keys(self):
        return super().keys()


def test_treatment_checklist_has_three_steps():
    from engine.treatment_plan import build_treatment_checklist

    user = Row(
        active_injuries='["deep_gash"]',
        disease="",
        wolf_name="Patch",
    )
    text = build_treatment_checklist(user, day=10)
    assert "1. **Herbs**" in text
    assert "2. **Surgery**" in text
    assert "3. **Rest**" in text
    assert "Stitch" in text or "stitch" in text.lower() or "Deep Gash" in text


def test_healer_refusal_when_dying_packmate():
    from engine.healer_refusal import healer_refusal_reminder

    medic = Row(id=1, pack_id=5, wolf_role="medic", bonus_role_feature=None)
    dying = Row(id=2, wolf_name="Bleeder", condition="dying", hp=0)
    with patch("engine.healer_refusal.db.get_pack_den_wolves", return_value=[dying]):
        rem = healer_refusal_reminder(medic, pack_id=5)
    assert rem and "dying" in rem.lower()


def test_rot_lung_outbreak_threshold():
    from engine.healer_refusal import rot_lung_outbreak_news

    w1 = Row(disease="rot_lung:fever", wolf_name="A")
    w2 = Row(disease="rot_lung:wheeze", wolf_name="B")
    with patch("engine.healer_refusal.db.get_pack_den_wolves", return_value=[w1, w2]):
        line = rot_lung_outbreak_news(1, threshold=2)
    assert line and "Rot-lung" in line


def test_treat_patient_requires_medic_in_cog():
    from engine.role_privileges import is_medic

    healer = Row(wolf_role="hunter", bonus_role_feature=None)
    assert not is_medic(healer)
    medic = Row(wolf_role="medic", bonus_role_feature=None)
    assert is_medic(medic)


def test_treat_stack_cross_pack_gate():
    from engine.medical_access import can_medic_treat_cross_pack

    surgeon = Row(id=1, pack_id=1)
    patient = Row(id=2, pack_id=2, condition="healthy", hp=8)
    with patch("engine.medical_access.db.get_pack_relation", return_value=2):
        ok, msg = can_medic_treat_cross_pack(surgeon, patient, 1, emergency_stabilize=False)
    assert not ok and "hostile" in msg.lower()


def test_observe_no_surgery_cooldown_field():
    from engine.medical_care import run_observe_apprentice

    medic = Row(id=1, wolf_name="Basil", wolf_role="medic_apprentice", bonus_role_feature=None, last_observe_day=0)
    patient = Row(id=2, wolf_name="Patch", active_injuries='["sprained_leg"]', disease="")
    with patch("engine.medical_care.db.update_user_by_id") as upd:
        ok, msg = run_observe_apprentice(medic, patient, day=3)
        upd.assert_called_once()
    assert ok and "cooldown untouched" in msg


def test_rush_stalks_flag_on_set_bone():
    from engine.surgery import _validate_optional_herb_flags, SURGERY_PROCEDURES

    spec = SURGERY_PROCEDURES["set_bone"]
    with patch("engine.surgery.participant_has_herb", return_value=False):
        err = _validate_optional_herb_flags(
            Row(id=1),
            "set_bone",
            spec,
            use_poppy=False,
            use_meadowsweet=False,
            use_loosestrife=False,
            use_plantain=False,
            use_rush_stalks=True,
        )
    assert err and "rush" in err.lower()


if __name__ == "__main__":
    test_treatment_checklist_has_three_steps()
    test_healer_refusal_when_dying_packmate()
    test_rot_lung_outbreak_threshold()
    test_treat_patient_requires_medic_in_cog()
    test_treat_stack_cross_pack_gate()
    test_observe_no_surgery_cooldown_field()
    test_rush_stalks_flag_on_set_bone()
    print("test_medic_commands: OK")
