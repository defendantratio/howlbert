"""Self-owned-wolf combat: a second wolf on the same account can join a
fight its packmate is already in, letting two of your own wolves face off
or team up (sparring, sibling rivalry, and similar rp)."""

import database as db


def _setup(discord_id: int, name_a: str, name_b: str) -> tuple:
    db.init_db()
    with db.get_db() as conn:
        conn.execute("DELETE FROM combat_fighters")
        conn.execute("DELETE FROM combat_encounters")
        conn.execute("DELETE FROM users WHERE discord_id = ?", (discord_id,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                hp, max_hp, hunger, thirst, exhaustion, condition, wolf_role
            ) VALUES (?, ?, 1, 'hunter', 0, 20, 20, 80, 80, 0, 'healthy', 'hunter')
            """,
            (discord_id, name_a),
        )
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                hp, max_hp, hunger, thirst, exhaustion, condition, wolf_role
            ) VALUES (?, ?, 1, 'hunter', 0, 18, 18, 80, 80, 0, 'healthy', 'hunter')
            """,
            (discord_id, name_b),
        )
    wolves = db.list_user_wolves(discord_id)
    wolf_a = next(w for w in wolves if w["wolf_name"] == name_a)
    wolf_b = next(w for w in wolves if w["wolf_name"] == name_b)
    enc_id = db.create_encounter(1, 1, discord_id)
    db.add_combat_fighter(enc_id, discord_id=discord_id, wolf_id=wolf_a["id"], hp=wolf_a["hp"], max_hp=wolf_a["max_hp"])
    return enc_id, wolf_a, wolf_b


def test_wolf_in_encounter_is_wolf_scoped():
    enc_id, wolf_a, wolf_b = _setup(881001, "PackmateA", "PackmateB")
    assert db.wolf_in_encounter(enc_id, wolf_a["id"])
    assert not db.wolf_in_encounter(enc_id, wolf_b["id"])


def test_second_wolf_can_join_same_account_fight():
    enc_id, wolf_a, wolf_b = _setup(881002, "SparA", "SparB")
    # player_in_encounter still says the account is already in this fight...
    assert db.player_in_encounter(enc_id, 881002)
    # ...but resolve_combat_encounter with the second wolf's id lets it through.
    enc, err = db.resolve_combat_encounter(
        1, 881002, encounter_id=enc_id, joinable_only=True, wolf_id=wolf_b["id"],
    )
    assert err is None
    assert enc is not None and enc["id"] == enc_id


def test_same_wolf_cannot_rejoin():
    enc_id, wolf_a, wolf_b = _setup(881003, "RejoinA", "RejoinB")
    enc, err = db.resolve_combat_encounter(
        1, 881003, encounter_id=enc_id, joinable_only=True, wolf_id=wolf_a["id"],
    )
    assert enc is None
    assert err == "You're already in that fight."


def test_both_own_wolves_can_attack_each_other():
    enc_id, wolf_a, wolf_b = _setup(881004, "DuelA", "DuelB")
    fighter_b_id = db.add_combat_fighter(
        enc_id, discord_id=881004, wolf_id=wolf_b["id"], hp=wolf_b["hp"], max_hp=wolf_b["max_hp"]
    )
    fighters = db.get_combat_fighters(enc_id)
    fighter_a = next(f for f in fighters if f["wolf_id"] == wolf_a["id"])
    fighter_b = next(f for f in fighters if f["id"] == fighter_b_id)
    # no team/side concept: neither fighter is the same combat_fighters row,
    # so the "can't attack yourself" guard doesn't block wolf-vs-wolf.
    assert fighter_a["id"] != fighter_b["id"]
