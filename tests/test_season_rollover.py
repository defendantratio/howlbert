"""Season rollover hooks; no invalid packs.guild_id queries."""

import sqlite3

from engine.season_rollover import (
    apply_food_cache_on_rollover,
    apply_season_rollover_effects,
    apply_winter_hunger_stress,
)


def test_winter_stress_does_not_query_pack_guild_id():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            wolf_name TEXT,
            pack_id INTEGER,
            condition TEXT NOT NULL DEFAULT 'healthy',
            hunger INTEGER NOT NULL DEFAULT 50,
            food_cache_meals INTEGER NOT NULL DEFAULT 0
        );
        INSERT INTO users (id, wolf_name, pack_id, hunger) VALUES (1, 'Ash', 1, 40);
        """
    )
    lines = apply_winter_hunger_stress(conn, guild_id=99, season="winter")
    assert lines
    row = conn.execute("SELECT hunger FROM users WHERE id = 1").fetchone()
    assert int(row["hunger"]) < 40


def test_food_cache_on_rollover():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            wolf_name TEXT,
            pack_id INTEGER,
            condition TEXT NOT NULL DEFAULT 'healthy',
            hunger INTEGER NOT NULL DEFAULT 50,
            food_cache_meals INTEGER NOT NULL DEFAULT 2
        );
        INSERT INTO users (id, wolf_name, pack_id) VALUES (1, 'Ash', 1);
        """
    )
    notes = apply_food_cache_on_rollover(conn, guild_id=99)
    assert len(notes) == 1
    row = conn.execute(
        "SELECT hunger, food_cache_meals FROM users WHERE id = 1"
    ).fetchone()
    assert int(row["food_cache_meals"]) == 0
    assert int(row["hunger"]) > 50


def test_apply_season_rollover_effects_winter():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            wolf_name TEXT,
            pack_id INTEGER,
            condition TEXT NOT NULL DEFAULT 'healthy',
            hunger INTEGER NOT NULL DEFAULT 50,
            food_cache_meals INTEGER NOT NULL DEFAULT 0
        );
        INSERT INTO users (id, wolf_name, pack_id) VALUES (1, 'River', 2);
        """
    )
    lines, cache = apply_season_rollover_effects(conn, 12345, "winter")
    assert lines
    assert cache == []
