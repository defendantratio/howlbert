"""sqlite3.Row safe column access."""

import sqlite3

import database as db
from engine.combat_display import fighter_val
from engine.combat_status import attack_target_block, maneuver_pin_block
from engine.combat_guide import COMBAT_MANEUVERS
from engine.hunt_party import assign_hunt_role


def test_row_val_on_sqlite_row():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE t (a INTEGER, b TEXT)")
    conn.execute("INSERT INTO t VALUES (1, 'x')")
    row = conn.execute("SELECT * FROM t").fetchone()
    assert db.row_val(row, "a") == 1
    assert db.row_val(row, "b") == "x"
    assert db.row_val(row, "missing", 9) == 9
    assert fighter_val(row, "a") == 1


def test_attack_target_block_accepts_sqlite_fighter_row():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE combat_fighters (
            id INTEGER, encounter_id INTEGER, discord_id INTEGER,
            hp INTEGER, max_hp INTEGER, npc_name TEXT, combat_flags TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO combat_fighters VALUES (1, 5, 100, 20, 20, NULL, '{}')"
    )
    conn.execute(
        "INSERT INTO combat_fighters VALUES (2, 5, 0, 20, 20, 'Prey', '{}')"
    )
    attacker = conn.execute("SELECT * FROM combat_fighters WHERE id=1").fetchone()
    defender = conn.execute("SELECT * FROM combat_fighters WHERE id=2").fetchone()
    assert attack_target_block(attacker, defender) is None


def test_maneuver_pin_block_accepts_sqlite_fighter_row():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE combat_fighters (
            id INTEGER, encounter_id INTEGER, discord_id INTEGER,
            hp INTEGER, max_hp INTEGER, npc_name TEXT, combat_flags TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO combat_fighters VALUES (1, 5, 100, 20, 20, NULL, '{}')"
    )
    conn.execute(
        "INSERT INTO combat_fighters VALUES (2, 5, 0, 15, 20, 'Prey', '{}')"
    )
    attacker = conn.execute("SELECT * FROM combat_fighters WHERE id=1").fetchone()
    defender = conn.execute("SELECT * FROM combat_fighters WHERE id=2").fetchone()
    block = maneuver_pin_block(
        COMBAT_MANEUVERS["jump_and_pin"],
        attacker,
        defender,
        defender_hp=15,
        defender_max_hp=20,
    )
    assert block is None or isinstance(block, str)


def test_assign_hunt_role_sqlite_wolf_row():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE users (wolf_role TEXT)")
    conn.execute("INSERT INTO users VALUES ('hunter')")
    wolf = conn.execute("SELECT * FROM users").fetchone()
    assert assign_hunt_role(wolf, [], is_leader=False) == "chaser"


def test_reply_ephemeral_defaults():
    from utils.replies import reply_ephemeral

    assert reply_ephemeral() is False
