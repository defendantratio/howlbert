"""Reptile prey, ambushes, and Sypha fear wiring; run: python -m tests.test_reptile_layer"""

import database as db
from engine.bestiary import BESTIARY_NPCS
from engine.combat_prey import prey_key_for_npc_template
from engine.combat_status import attacker_roll_modifiers
from engine.disease_contract import try_nettle_sting_exposure
from engine.prey_items import PREY_CATALOG, prey_key_from_hunt_amount
from engine.reptile_fear import (
    REPTILE_NPC_TEMPLATES,
    has_reptile_insect_fear,
    reptile_ambush_fear_note,
    reptile_fear_roll_modifiers,
)
from engine.wild_encounters import REPTILE_ENCOUNTER_BY_PACK, pick_wild_encounter_template


def test_prey_catalog_has_amphibian_reptile() -> None:
    for key in ("frog", "snake", "lizard"):
        assert key in PREY_CATALOG
        assert PREY_CATALOG[key]["bones"] > 0


def test_combat_prey_mapping() -> None:
    assert prey_key_for_npc_template("water_snake") == "snake"
    assert prey_key_for_npc_template("garter_snake") == "snake"
    assert prey_key_for_npc_template("skink") == "lizard"
    # No combat kill is exempt; an unmapped template (e.g. spider) still
    # falls back to a generic "carrion" carcass rather than nothing.
    assert prey_key_for_npc_template("spider") == "carrion"


def test_marsh_hunt_bias_frog() -> None:
    hits = sum(
        1
        for _ in range(80)
        if prey_key_from_hunt_amount(6, great_pack="mistmoor") == "frog"
    )
    assert hits >= 10


def test_reptile_bestiary_templates() -> None:
    for key in REPTILE_NPC_TEMPLATES:
        assert key in BESTIARY_NPCS


def test_pick_wild_encounter_includes_reptiles_in_mistmoor() -> None:
    user = {"great_pack": "mistmoor"}
    seen = {pick_wild_encounter_template(user) for _ in range(200)}
    reptile_keys = {k for k, _ in REPTILE_ENCOUNTER_BY_PACK["mistmoor"]}
    assert seen & reptile_keys


def test_sypha_fear_trait_detection() -> None:
    sypha = {"wolf_name": "Sypha", "discord_id": 1, "id": 1}
    assert has_reptile_insect_fear(sypha)
    plain = {"wolf_name": "Ash", "discord_id": 2, "id": 2}
    assert not has_reptile_insect_fear(plain)


def test_reptile_fear_roll_modifiers(monkeypatch) -> None:
    sypha = {"wolf_name": "Sypha", "discord_id": 1, "id": 1}

    def fake_get_user(did):
        return sypha if did == 1 else None

    monkeypatch.setattr(db, "get_user", fake_get_user)
    wolf_f = {"discord_id": 1, "npc_template": None}
    snake_f = {"npc_template": "water_snake", "npc_name": "Water Snake"}
    dis, adv, note = reptile_fear_roll_modifiers(wolf_f, snake_f)
    assert dis and not adv and "fear" in note.lower()
    dis2, adv2, note2 = reptile_fear_roll_modifiers(snake_f, wolf_f)
    assert adv2 and not dis2 and "flinch" in note2.lower()


def test_reptile_ambush_fear_note() -> None:
    sypha = {"wolf_name": "Sypha", "discord_id": 1, "id": 1}
    note = reptile_ambush_fear_note(sypha, "garter_snake")
    assert "cold" in note.lower() or "scales" in note.lower()


def test_attacker_roll_modifiers_applies_reptile_fear(monkeypatch) -> None:
    sypha = {
        "wolf_name": "Sypha",
        "discord_id": 99,
        "id": 99,
        "disease": "",
        "condition": "healthy",
    }

    def fake_get_user(did):
        return sypha if did == 99 else None

    monkeypatch.setattr(db, "get_user", fake_get_user)
    wolf_f = {"discord_id": 99}
    snake_f = {"npc_template": "water_snake"}
    dis, adv, _ = attacker_roll_modifiers(sypha, "bite", wolf_f, snake_f)
    assert dis and not adv


def test_nettle_sting_contract(monkeypatch) -> None:
    user = {"discord_id": 1, "id": 1, "condition": "healthy", "disease": ""}
    calls: list[str] = []

    def fake_set(did, **kwargs):
        calls.append(kwargs.get("disease", ""))

    monkeypatch.setattr(db, "set_user_conditions", fake_set)
    note = try_nettle_sting_exposure(user, chance=1.0)
    assert note and "nettle" in note.lower()
    assert calls and "mild_poison" in calls[0]


if __name__ == "__main__":
    test_prey_catalog_has_amphibian_reptile()
    test_combat_prey_mapping()
    test_marsh_hunt_bias_frog()
    test_reptile_bestiary_templates()
    test_pick_wild_encounter_includes_reptiles_in_mistmoor()
    test_sypha_fear_trait_detection()
    test_reptile_ambush_fear_note()

    class _Patch:
        def setattr(self, obj, name, value):
            setattr(obj, name, value)

    monkeypatch = _Patch()
    test_reptile_fear_roll_modifiers(monkeypatch)
    test_attacker_roll_modifiers_applies_reptile_fear(monkeypatch)
    test_nettle_sting_contract(monkeypatch)
    print("OK")
