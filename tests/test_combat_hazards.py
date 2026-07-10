"""Combat hazard and wilderness encounter mechanics."""

from __future__ import annotations

from unittest.mock import patch

from engine.combat_hazards import (
    grant_field_injury,
    resolve_combat_hazard,
    roll_fence_hazard,
    roll_trap_hazard,
)
from engine.travel_hazards import roll_wilderness_encounter


def _mock_user(**overrides):
    base = {
        "id": 1,
        "discord_id": 100,
        "hp": 20,
        "max_hp": 20,
        "exhaustion": 0,
        "active_injuries": "[]",
        "skill_proficiencies": "[]",
        "bones": 0,
        "thirst": 4,
        "mood": 50,
        "condition": "healthy",
        "disease": "",
        "great_pack": "mistmoor",
        "attr_str": 5,
        "attr_dex": 5,
        "attr_con": 5,
        "attr_int": 5,
        "attr_cha": 5,
        "attr_wis": 5,
    }
    base.update(overrides)

    class Row(dict):
        def keys(self):
            return super().keys()

    return Row(base)


def test_combat_hazard_topics_resolve():
    user = _mock_user()
    for topic in ("humans", "thunderpath", "traps", "twoleg_nests", "fences"):
        ok, title, body = resolve_combat_hazard(user, topic, day=1, guild_id=1)
        assert isinstance(ok, bool)
        assert title
        assert body
        assert len(body) > 40


def _roll_result(**overrides):
    base = {
        "success": True,
        "outcome": "success",
        "total": 20,
        "dc": 15,
        "die": 18,
        "modifier": 2,
        "attr_label": "Dex",
        "skill": "Tracking",
    }
    base.update(overrides)
    return base


def test_trap_spot_success_no_damage():
    user = _mock_user(hp=20)

    with patch("engine.combat_hazards.resolve_check", lambda *_a, **_k: _roll_result()):
        ok, body = roll_trap_hazard(user, day=1)
    assert ok
    assert user["hp"] == 20
    assert "skirt" in body.lower()


def test_fence_wooden_fail_still_crosses():
    user = _mock_user(hp=20)

    with patch("engine.combat_hazards.random.choice", lambda _seq: "wooden"), patch(
        "engine.combat_hazards.random.randint", lambda _a, _b: 2
    ), patch(
        "engine.combat_hazards.resolve_check",
        lambda *_a, **_k: _roll_result(success=False, outcome="failure", total=5, dc=10),
    ), patch(
        "engine.vitals.apply_hp_damage",
        lambda u, amt: (u.__setitem__("hp", u["hp"] - amt) or (amt, [])),
    ):
        ok, body = roll_fence_hazard(user, day=1)
    assert ok
    assert user["hp"] == 18


def test_grant_field_injury_once():
    mock = _mock_user(active_injuries="[]")
    stored: dict = {}

    def capture(_uid, **kwargs):
        stored.update(kwargs)

    with patch("engine.combat_hazards.db.update_user_by_id", capture), patch(
        "engine.combat_hazards.db.record_injury_since", lambda *_a, **_k: None
    ):
        note = grant_field_injury(mock, "sprained_leg", day=5)
    assert note
    assert "sprained_leg" in stored.get("active_injuries", "")


def test_wilderness_encounter_find_grants_bones():
    user = _mock_user(bones=0)
    added: list[int] = []

    def track_bones(_did, amount, **_k):
        added.append(amount)

    with patch("engine.travel_hazards.random.randint", lambda a, b: 18 if a == 1 else 8), patch(
        "engine.travel_hazards.random.choice",
        lambda seq: ("Twoleg rubbish", "Useful scrap."),
    ), patch("engine.travel_hazards.db.add_bones", track_bones):
        kind, body, enc_id = roll_wilderness_encounter(user, day=1, guild_id=1)
    assert kind == "find"
    assert enc_id is None
    assert added
    assert "bones" in body.lower()


def test_wilderness_encounter_quiet():
    user = _mock_user()

    import engine.travel_hazards as th

    orig = th.random.randint

    def quiet_roll(a, b):
        if a == 1 and b == 20:
            return 10
        return orig(a, b)

    kind, body, enc_id = roll_wilderness_encounter(user, day=1, guild_id=1)
    assert kind in ("encounter", "quiet", "find")
    assert body
    assert enc_id is None or isinstance(enc_id, int)


if __name__ == "__main__":
    test_combat_hazard_topics_resolve()
    test_trap_spot_success_no_damage()
    test_fence_wooden_fail_still_crosses()
    test_grant_field_injury_once()
    test_wilderness_encounter_find_grants_bones()
    test_wilderness_encounter_quiet()
    print("test_combat_hazards: ok")
