"""Combat encounter list, resolve, reconcile, and mid-join."""

import json

import database as db


def _setup():
    db.init_db()
    with db.get_db() as conn:
        conn.execute("DELETE FROM combat_target_picks")
        conn.execute("DELETE FROM combat_fighters")
        conn.execute("DELETE FROM combat_encounters")
        conn.commit()


def test_multiple_encounters_same_channel():
    _setup()
    ch = 999001
    e1 = db.create_encounter(1, ch, 100)
    e2 = db.create_encounter(1, ch, 200)
    active = db.list_active_encounters(ch)
    assert len(active) == 2
    assert {e["id"] for e in active} == {e1, e2}


def test_reconcile_empty_fighters_ends_encounter():
    _setup()
    ch = 999002
    enc_id = db.create_encounter(1, ch, 100)
    with db.get_db() as conn:
        conn.execute(
            "UPDATE combat_encounters SET status = 'active', turn_order = '[]' WHERE id = ?",
            (enc_id,),
        )
        conn.commit()
    assert db.reconcile_encounter_if_broken(enc_id) is True
    enc = db.get_encounter(enc_id)
    assert enc["status"] == "ended"
    assert not db.list_active_encounters(ch)


def test_mid_join_inserts_initiative():
    _setup()
    ch = 999003
    enc_id = db.create_encounter(1, ch, 100)
    f1 = db.add_combat_fighter(enc_id, discord_id=100, wolf_id=1, hp=10, max_hp=10)
    f2 = db.add_combat_fighter(enc_id, npc_name="Coyote", npc_template="coyote", hp=8, max_hp=8)
    db.set_fighter_initiative(f1, 15)
    db.set_fighter_initiative(f2, 10)
    db.start_combat_encounter(enc_id, [f1, f2])

    late_id = db.add_combat_fighter(enc_id, discord_id=200, wolf_id=2, hp=12, max_hp=12)
    db.insert_fighter_into_active_encounter(enc_id, late_id, 12)

    enc = db.get_encounter(enc_id)
    order = json.loads(enc["turn_order"])
    assert late_id in order
    assert order.index(f1) < order.index(late_id)


def test_resolve_requires_encounter_id_when_ambiguous():
    _setup()
    ch = 999004
    db.create_encounter(1, ch, 100)
    db.create_encounter(1, ch, 200)
    enc, err = db.resolve_combat_encounter(ch, 300, None, joinable_only=True)
    assert enc is None
    assert err and "Several fights" in err
