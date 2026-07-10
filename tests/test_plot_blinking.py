"""Book One plot phase mechanics."""


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
    assert "blinking" in line.lower()
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


def test_soot_plot_sniff_and_treat():
    from engine.plot_blinking import (
        apply_plot_soot_sniff,
        plot_healer_heal_bonus,
        plot_soot_heal_bonus,
        try_plot_treat_extras,
    )

    db.init_db()
    guild_id = 999_008
    day = 55
    db.set_plot_phase(guild_id, 5)
    healer = {
        "wolf_name": "Soot",
        "discord_id": 99020,
        "great_pack": "mistmoor",
        "id": 99021,
        "last_soot_reward_day": 0,
        "mood": 50,
    }
    patient = {
        "wolf_name": "Wheezer",
        "id": 99022,
        "discord_id": 99023,
        "disease": "rot_lung:fever",
    }
    with db.get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (id, discord_id, wolf_name, great_pack, wolf_role, mood, hp, max_hp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (healer["id"], healer["discord_id"], healer["wolf_name"], healer["great_pack"], "medic", 50, 20, 20),
        )
        conn.commit()

    sniff = apply_plot_soot_sniff(healer, guild_id, day=day)
    assert sniff and "+2 mood" in sniff and "mist-light" in sniff

    extra = try_plot_treat_extras(healer, patient, guild_id=guild_id, day=day)
    assert extra and "mirewort" in extra.lower()
    assert plot_soot_heal_bonus(healer, patient, guild_id) == 3
    assert plot_healer_heal_bonus(healer, patient, guild_id) == 3

    healer["last_soot_reward_day"] = day
    assert apply_plot_soot_sniff(healer, guild_id, day=day)  # mood still; no second standing


def test_plot_witness_once_per_day():
    from engine.plot_blinking import try_plot_witness

    db.init_db()
    guild_id = 999_009
    db.set_plot_phase(guild_id, 3)
    user = {
        "wolf_name": "Witness",
        "discord_id": 99030,
        "great_pack": "greyspire",
        "id": 99031,
        "last_plot_witness_day": 0,
        "mood": 40,
    }
    with db.get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (id, discord_id, wolf_name, great_pack, mood, hp, max_hp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user["id"], user["discord_id"], user["wolf_name"], user["great_pack"], 40, 20, 20),
        )
        conn.commit()
    first = try_plot_witness(user, guild_id, day=60, action="howl")
    assert first and "+1 mood" in first
    user["last_plot_witness_day"] = 60
    second = try_plot_witness(user, guild_id, day=60, action="drink")
    assert second == ""


def test_plot_quest_phase_gates():
    from engine.plot_quests import plot_quest_available, plot_sniff_quest_keys

    db.init_db()
    gid = 999_010
    db.set_plot_phase(gid, 0)
    assert not plot_quest_available("blink_healer_listen", gid)
    db.set_plot_phase(gid, 3)
    assert plot_quest_available("blink_healer_listen", gid)
    assert plot_quest_available("blink_border_patrol", gid)
    assert not plot_quest_available("blink_wind_witness", gid)
    db.set_plot_phase(gid, 6)
    assert not plot_quest_available("blink_healer_listen", gid)
    assert plot_quest_available("blink_wind_witness", gid)
    assert not plot_quest_available("blink_ash_naming", gid)
    db.set_plot_phase(gid, 11)
    assert plot_quest_available("blink_ash_naming", gid)
    keys = plot_sniff_quest_keys(gid)
    assert "blink_wind_witness" in keys
    assert "blink_healer_listen" not in keys
    db.set_plot_phase(gid, 4)
    assert "blink_healer_listen" in plot_sniff_quest_keys(gid)


def test_horsetail_death_save_consumed():
    from engine.death_saves import roll_death_save
    from engine.herb_buffs import death_save_bonus

    user = {
        "death_save_round": 1,
        "attr_con": 10,
        "herb_buffs": '{"death_save_bonus_next": 3}',
    }
    assert death_save_bonus(user) == 3
    result = roll_death_save(user)
    assert result.get("consume_fields")
    merged = dict(user)
    merged.update(result["consume_fields"])
    assert death_save_bonus(merged) == 0


def test_rivershroud_and_finnpelt_plot_sniff():
    from engine.plot_blinking import (
        apply_plot_finnpelt_sniff,
        apply_plot_rivershroud_sniff,
        plot_howl_unity_bonus,
        plot_thistlehide_patrol_standing_bonus,
        rivershroud_plot_active,
    )

    db.init_db()
    guild_id = 999_010
    day = 70

    alpha = {
        "wolf_name": "RiverShroud",
        "discord_id": 99040,
        "great_pack": "thistlehide",
        "wolf_role": "alpha",
        "id": 99041,
        "last_rivershroud_reward_day": 0,
        "mood": 50,
    }
    hunter = {
        "wolf_name": "Finnpelt",
        "discord_id": 99042,
        "great_pack": "thistlehide",
        "wolf_role": "hunter",
        "id": 99043,
        "last_finnpelt_reward_day": 0,
        "mood": 50,
    }
    with db.get_db() as conn:
        for u in (alpha, hunter):
            conn.execute(
                """
                INSERT OR IGNORE INTO users (
                    id, discord_id, wolf_name, great_pack, wolf_role, mood, hp, max_hp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (u["id"], u["discord_id"], u["wolf_name"], u["great_pack"], u["wolf_role"], 50, 20, 20),
            )
        conn.commit()

    db.set_plot_phase(guild_id, 2)
    early = apply_plot_rivershroud_sniff(alpha, guild_id, day=day)
    assert early and "+1 mood" in early.lower() and "sniff bonus" in early.lower()
    assert not apply_plot_finnpelt_sniff(hunter, guild_id, day=day)

    db.set_plot_phase(guild_id, 7)
    finn = apply_plot_finnpelt_sniff(hunter, guild_id, day=day)
    assert finn and "+2 mood" in finn and "+1 standing" in finn

    alpha["last_rivershroud_reward_day"] = 0
    river = apply_plot_rivershroud_sniff(alpha, guild_id, day=day)
    assert river and "+2 standing" in river
    assert plot_thistlehide_patrol_standing_bonus(guild_id, "thistlehide", user=alpha) == 1
    assert plot_thistlehide_patrol_standing_bonus(guild_id, "thistlehide", user=hunter) == 1

    db.set_plot_phase(guild_id, 11)
    assert plot_howl_unity_bonus(guild_id, user=alpha) == 2
    assert rivershroud_plot_active(alpha, guild_id)
    assert not rivershroud_plot_active({**alpha, "wolf_role": "hunter"}, guild_id)


if __name__ == "__main__":
    test_plot_phase_migration_and_set()
    test_plot_den_news()
    test_warm_river_fishing_debuff()
    test_plot_rollover_silverrush_thirst()
    test_plot_travel_and_pact_mods()
    test_plot_drink_ash_naming()
    test_rogue_crime_inactive_before_phase_6()
    test_firepaw_plot_sniff_and_treat()
    test_soot_plot_sniff_and_treat()
    test_plot_witness_once_per_day()
    test_plot_quest_phase_gates()
    test_horsetail_death_save_consumed()
    test_rivershroud_and_finnpelt_plot_sniff()
    print("test_plot_blinking: ok")
