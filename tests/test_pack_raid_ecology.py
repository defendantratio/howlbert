"""Pack raid ecology mechanics."""

from engine.pack_raid_ecology import (
    scaled_steal_attempt,
    steal_catch_chance,
    survey_dc_modifiers,
)


def test_thistlehide_higher_catch_chance():
    base = steal_catch_chance("mistmoor")
    thistle = steal_catch_chance("thistlehide")
    assert thistle > base


def test_greyspire_lower_steal_mult():
    assert scaled_steal_attempt("greyspire", 100) < 100
    assert scaled_steal_attempt("silverrush", 100) >= 100


def test_victim_survey_dc_easier():
    user = {"pack_id": 1}
    alert_user = {"pack_id": 1}

    class FakeAlert:
        def __getitem__(self, key):
            return {"victim_pack_id": 1, "suspect_pack_id": 2}[key]

    import database as db
    from unittest.mock import patch

    with patch.object(db, "get_active_raid_alert_for_victim", return_value=FakeAlert()):
        dc, note = survey_dc_modifiers(alert_user, 99, 5)
    assert dc < 0
    assert note
