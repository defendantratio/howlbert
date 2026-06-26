"""Death cause tracking and wolf_death_log."""

import database as db


def _insert_wolf(discord_id: int, wolf_name: str, *, pack_id: int | None = None) -> int:
    with db.get_db() as conn:
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                hp, max_hp, hunger, thirst, exhaustion, condition, wolf_role
            ) VALUES (?, ?, ?, 'hunter', datetime('now'), 20, 20, 80, 80, 0, 'healthy', 'hunter')
            """,
            (discord_id, wolf_name, pack_id),
        )
    user = db.get_user(discord_id)
    return int(user["id"])


def test_mark_wolf_dead_records_cause_and_log():
    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO world_state (guild_id, day_number, season, weather, time_of_day, last_rollover) "
            "VALUES (42, 17, 'spring', 'clear', 'dawn', datetime('now'))"
        )
    wolf_id = _insert_wolf(9001, "Ash")

    db.mark_wolf_dead(wolf_id, "starvation", guild_id=42, day=17)

    user = db.get_user_by_id(wolf_id)
    assert user["condition"] == "dead"
    assert user["cause_of_death"] == "starvation"
    assert int(user["death_day"]) == 17

    rows = db.list_death_log(wolf_id=wolf_id)
    assert len(rows) == 1
    assert rows[0]["cause"] == "starvation"
    assert int(rows[0]["day"]) == 17


def test_set_user_conditions_dead_uses_death_cause():
    wolf_id = _insert_wolf(9002, "River")

    db.set_user_conditions(9002, wolf_id=wolf_id, condition="dead", death_cause="mercy (Poppy Seeds)")

    user = db.get_user_by_id(wolf_id)
    assert user["condition"] == "dead"
    assert user["cause_of_death"] == "mercy (Poppy Seeds)"
    assert len(db.list_death_log(wolf_id=wolf_id)) == 1


def test_revive_clears_cause_but_keeps_log():
    wolf_id = _insert_wolf(9003, "Fern")

    db.mark_wolf_dead(wolf_id, "exhaustion")
    assert db.get_user(9003)["cause_of_death"] == "exhaustion"

    err = db.revive_wolf(9003)
    assert err is None
    revived = db.get_user(9003)
    assert revived["condition"] == "healthy"
    assert revived["cause_of_death"] is None
    assert revived["death_day"] is None
    assert len(db.list_death_log(wolf_id=wolf_id)) == 1


def test_list_current_dead_wolves():
    wolf_id = _insert_wolf(9004, "Stone")

    db.mark_wolf_dead(wolf_id, "failed death saves", guild_id=99, day=3)
    dead = db.list_current_dead_wolves(guild_id=99)
    assert len(dead) == 1
    assert dead[0]["wolf_name"] == "Stone"
    assert dead[0]["cause_of_death"] == "failed death saves"


if __name__ == "__main__":
    db.init_db()
    test_mark_wolf_dead_records_cause_and_log()
    test_set_user_conditions_dead_uses_death_cause()
    test_revive_clears_cause_but_keeps_log()
    test_list_current_dead_wolves()
    print("OK")
