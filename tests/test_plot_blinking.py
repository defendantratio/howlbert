"""Book One plot phase mechanics."""

import sqlite3

import database as db
from engine.plot_blinking import (
    apply_plot_rollover_effects,
    plot_activity_payout_mult,
    plot_cat_pact_forge_dc_bonus,
    plot_den_news_line,
    plot_drink_thirst_bonus,
    plot_sniff_border_mult,
    plot_travel_dc_bonus,
    try_plot_rogue_crime,
)


def test_plot_phase_migration_and_set():
    db.init_db()
    guild_id = 999_991
    db.set_plot_phase(guild_id, 0)
    assert db.get_plot_phase(guild_id) == 0
    db.set_plot_phase(guild_id, 4)
    assert db.get_plot_phase(guild_id) == 4
    new_phase, _ = db.advance_plot_phase(guild_id)
    assert new_phase == 5


def test_plot_den_news():
    line = plot_den_news_line(1, 100)
    assert "Blinking" in line
    assert "moon" in line.lower()
    assert plot_den_news_line(0, 1) == ""


def test_warm_river_fishing_debuff():
    db.init_db()
    guild_id = 999_002
    db.set_plot_phase(guild_id, 4)
    mult, note = plot_activity_payout_mult(guild_id, "fishing", great_pack="silverrush")
    assert mult == 0.70
    assert note


def test_plot_rollover_silverrush_thirst():
    db.init_db()
    guild_id = 999_003
    db.set_plot_phase(guild_id, 4)
    with db.get_db() as conn:
        row = conn.execute(
            "SELECT id, thirst FROM users WHERE great_pack = 'silverrush' LIMIT 1"
        ).fetchone()
        if not row:
            return
        wolf_id = int(row["id"])
        conn.execute("UPDATE users SET thirst = 50 WHERE id = ?", (wolf_id,))
        before = 50
        apply_plot_rollover_effects(conn, guild_id, 10, 4)
        after = conn.execute("SELECT thirst FROM users WHERE id = ?", (wolf_id,)).fetchone()
    assert int(after["thirst"]) == before - 2


def test_plot_travel_and_pact_mods():
    db.init_db()
    guild_id = 999_004
    db.set_plot_phase(guild_id, 3)
    assert plot_travel_dc_bonus(guild_id, "mountain") == 2
    db.set_plot_phase(guild_id, 7)
    assert plot_travel_dc_bonus(guild_id, "forest") == 2
    assert plot_cat_pact_forge_dc_bonus(guild_id) == 2
    db.set_plot_phase(guild_id, 6)
    assert plot_sniff_border_mult(guild_id) == 1.25


def test_plot_drink_ash_naming():
    db.init_db()
    guild_id = 999_005
    db.set_plot_phase(guild_id, 11)
    bonus, note = plot_drink_thirst_bonus(guild_id, "thistlehide")
    assert bonus == 5
    assert note


class _Guild:
    id = 999_006


class _Interaction:
    guild = _Guild()
    user = None


def test_rogue_crime_inactive_before_phase_6():
    db.init_db()
    user = db.get_user(1056053114177855548)
    if not user:
        return
    db.set_plot_phase(_Guild.id, 2)
    gross, suffix, caught = try_plot_rogue_crime(_Interaction(), user, day=1, gross=10)
    assert gross == 10
    assert suffix == ""
    assert caught is None


def test_firepaw_plot_sniff_and_treat():
    from engine.plot_blinking import (
        apply_plot_firepaw_sniff,
        plot_firepaw_heal_bonus,
        try_plot_sniff_extras,
        try_plot_treat_extras,
    )

    db.init_db()
    guild_id = 999_007
    day = 42
    db.set_plot_phase(guild_id, 2)
    user = {
        "wolf_name": "Firepaw",
        "discord_id": 99010,
        "great_pack": "thistlehide",
        "id": 99011,
        "last_firepaw_reward_day": 0,
        "mood": 50,
    }
    with db.get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (id, discord_id, wolf_name, great_pack, wolf_role, mood, hp, max_hp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user["id"], user["discord_id"], user["wolf_name"], user["great_pack"], "medic_apprentice", 50, 20, 20),
        )
        conn.commit()

    sniff = try_plot_sniff_extras(user, guild_id, day=day)
    assert sniff and "+2 mood" in sniff

    db.set_plot_phase(guild_id, 7)
    healer = dict(user)
    healer["last_firepaw_reward_day"] = 0
    patient = {"wolf_name": "Patient", "id": 99012, "discord_id": 99013}
    extra = try_plot_treat_extras(healer, patient, guild_id=guild_id, day=day)
    assert extra and "standing" in extra.lower()
    assert plot_firepaw_heal_bonus(healer, guild_id) == 2

    healer["last_firepaw_reward_day"] = day  # treat marks daily plot reward
    early = apply_plot_firepaw_sniff(healer, guild_id, day=day)
    assert early == ""  # same sunrise: sniff daily already claimed via treat


if __name__ == "__main__":
    test_plot_phase_migration_and_set()
    test_plot_den_news()
    test_warm_river_fishing_debuff()
    test_plot_rollover_silverrush_thirst()
    test_plot_travel_and_pact_mods()
    test_plot_drink_ash_naming()
    test_rogue_crime_inactive_before_phase_6()
    test_firepaw_plot_sniff_and_treat()
    print("test_plot_blinking: ok")
