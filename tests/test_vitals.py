"""Vitals / exhaustion tests; run: python -m tests.test_vitals"""

from __future__ import annotations

import sqlite3

import database as db
from config import HUNGER_LOW_THRESHOLD, MOOD_LOW_THRESHOLD, THIRST_LOW_THRESHOLD
from engine.conditions import herb_special_effect, progress_disease, progress_injuries
from engine.dice import resolve_check
from engine.disease_effects import disease_check_adjustments
from engine.exhaustion_effects import (
    apply_exhaustion_death_on_rollover,
    apply_mood_exhaustion_on_rollover,
    effective_max_hp,
    exhaustion_activity_block,
)
from engine.movement_penalties import apply_movement_hunt_penalty
from engine.vitals import apply_needs_exhaustion_on_rollover, full_activity_block
from engine.weather_hazards import hazard_failure_effects

_pass = 0
_fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  OK  {name}")
    else:
        _fail += 1
        print(f" FAIL {name}" + (f" - {detail}" if detail else ""))


class Row(dict):
    def keys(self):
        return super().keys()


def test_needs_exhaustion() -> None:
    print("\n=== needs exhaustion on rollover ===")
    db.init_db()
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = 999300001000000001")
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                hunger, thirst, exhaustion, condition, hunger_exhaustion_skip
            ) VALUES (999300001000000001, 'Starving', NULL, 'subordinate', 'test', ?, ?, 1, 'healthy', 0)
            """,
            (HUNGER_LOW_THRESHOLD - 1, 80),
        )
        notes = apply_needs_exhaustion_on_rollover(conn)
        row = conn.execute(
            "SELECT exhaustion FROM users WHERE discord_id = 999300001000000001"
        ).fetchone()
    test_notes = [n for n in notes if n.get("discord_id") == 999300001000000001]
    check("hunger low adds exhaustion", row["exhaustion"] == 2)
    check("note recorded", len(test_notes) == 1 and test_notes[0]["cause"] == "hunger")

    with db.get_db() as conn:
        conn.execute(
            "UPDATE users SET hunger = 80, thirst = ?, exhaustion = 0, hunger_exhaustion_skip = 0 "
            "WHERE discord_id = 999300001000000001",
            (THIRST_LOW_THRESHOLD - 1,),
        )
        apply_needs_exhaustion_on_rollover(conn)
        row = conn.execute(
            "SELECT exhaustion FROM users WHERE discord_id = 999300001000000001"
        ).fetchone()
    check("thirst low adds exhaustion", row["exhaustion"] == 1)

    with db.get_db() as conn:
        conn.execute(
            "UPDATE users SET hunger = ?, thirst = ?, exhaustion = 0 WHERE discord_id = 999300001000000001",
            (HUNGER_LOW_THRESHOLD - 5, THIRST_LOW_THRESHOLD - 5),
        )
        apply_needs_exhaustion_on_rollover(conn)
        row = conn.execute(
            "SELECT exhaustion FROM users WHERE discord_id = 999300001000000001"
        ).fetchone()
    check("both low stacks +2", row["exhaustion"] == 2)

    with db.get_db() as conn:
        conn.execute(
            "UPDATE users SET hunger = ?, thirst = 80, exhaustion = 0, hunger_exhaustion_skip = 1 "
            "WHERE discord_id = 999300001000000001",
            (HUNGER_LOW_THRESHOLD - 5,),
        )
        apply_needs_exhaustion_on_rollover(conn)
        row = conn.execute(
            "SELECT exhaustion, hunger_exhaustion_skip FROM users WHERE discord_id = 999300001000000001"
        ).fetchone()
    check("fennel skip blocks hunger ex", row["exhaustion"] == 0)
    check("fennel skip consumed", row["hunger_exhaustion_skip"] == 0)

    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = 999300001000000001")


def test_mood_exhaustion() -> None:
    print("\n=== mood exhaustion ===")
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = 999300002000000002")
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                mood, exhaustion, condition
            ) VALUES (999300002000000002, 'Glum', NULL, 'subordinate', 'test', ?, 0, 'healthy')
            """,
            (MOOD_LOW_THRESHOLD - 1,),
        )
        notes = apply_mood_exhaustion_on_rollover(conn)
        row = conn.execute(
            "SELECT exhaustion FROM users WHERE discord_id = 999300002000000002"
        ).fetchone()
    check("low mood adds exhaustion", row["exhaustion"] == 1)
    check("mood note", notes and notes[0]["cause"] == "low mood")
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = 999300002000000002")


def test_exhaustion_death_and_tiers() -> None:
    print("\n=== exhaustion tiers ===")
    user = Row(max_hp=20, exhaustion=4, hp=18)
    check("hp cap halved", effective_max_hp(user) == 10)
    check("exhaustion 5 blocks", exhaustion_activity_block(Row(exhaustion=5)) is not None)
    reduced, note = apply_movement_hunt_penalty(100, Row(exhaustion=2, active_injuries="[]"))
    check("hunt halved at ex 2", reduced == 50 and "halved" in note.lower())
    sprained, s_note = apply_movement_hunt_penalty(
        100, Row(exhaustion=0, active_injuries='["sprained_leg"]', disease=None)
    )
    check("sprained leg halves hunt", sprained == 50 and "sprained" in s_note.lower())

    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = 999300003000000003")
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                exhaustion, condition, hp, max_hp
            ) VALUES (999300003000000003, 'Done', NULL, 'subordinate', 'test', 6, 'healthy', 5, 11)
            """
        )
        deaths = apply_exhaustion_death_on_rollover(conn)
        row = conn.execute(
            "SELECT condition FROM users WHERE discord_id = 999300003000000003"
        ).fetchone()
    check("exhaustion 6 kills", row["condition"] == "dead")
    check("death logged", deaths and deaths[0]["cause"] == "exhaustion")
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = 999300003000000003")


def test_bleeding_exhaustion() -> None:
    print("\n=== bleeding exhaustion ===")
    user = Row(active_injuries='["deep_gash"]', skill_proficiencies="[]", attr_wis=10, attr_con=10)
    outcome = progress_injuries(user)
    check("bleeding costs hp only", outcome.get("hp_loss") == 1)
    check("bleeding no exhaustion", outcome.get("exhaustion_gain", 0) == 0)


def test_herbs_and_hazards() -> None:
    print("\n=== herbs & hazards ===")
    user = Row(exhaustion=2, disease="mild")
    check("honey reduces ex when depleted", herb_special_effect("honey", Row(hunger=10, thirst=80)) == "reduce_exhaustion")
    check("honey needs depletion", herb_special_effect("honey", Row(hunger=80, thirst=80)) == "honey_needs_depletion")
    check("fennel shield", herb_special_effect("fennel", user) == "hunger_shield")
    check("ragweed needs 3", herb_special_effect("ragweed", user, inventory_qty=2) == "ragweed_need_three")
    check("blizzard fail", hazard_failure_effects("blizzard", failed=True).get("exhaustion") == 1)
    check("smoke debuff", hazard_failure_effects("wildfire_smoke", failed=True).get("smoke_debuff") == 1)
    check("freezing rain ex", hazard_failure_effects("freezing_rain", failed=True).get("exhaustion") == 1)
    check("thunder mood", hazard_failure_effects("thunderstorm", failed=True).get("mood_loss") == 6)
    heat = hazard_failure_effects("extreme_heat", failed=True)
    check("heat thirst", heat.get("thirst_loss") == 25)


def test_exhaustion_disadvantage() -> None:
    print("\n=== skill check disadvantage ===")
    user = Row(
        attr_str=10,
        attr_dex=10,
        attr_con=10,
        attr_int=10,
        attr_cha=10,
        attr_wis=10,
        skill_proficiencies="[]",
        active_injuries="[]",
        exhaustion=2,
    )
    result = resolve_check(
        user,
        attr_keys=("attr_str",),
        skill=None,
        dc=30,
        proficient=False,
    )
    check("exhaustion flags disadvantage", result.get("exhaustion_disadvantage") is True)


def test_disease_and_gates() -> None:
    print("\n=== disease & activity gates ===")
    user = Row(
        attr_str=10,
        attr_dex=10,
        skill_proficiencies="[]",
        active_injuries="[]",
        exhaustion=0,
        disease="mild",
    )
    _, disadv = disease_check_adjustments(user, ("attr_dex",))
    check("mild dex disadvantage", disadv is True)
    result = resolve_check(
        user,
        attr_keys=("attr_dex",),
        skill=None,
        dc=30,
        proficient=False,
    )
    check("disease flags disadvantage", result.get("disease_disadvantage") is True)

    deadly = Row(
        attr_con=10,
        disease="deadly",
        skill_proficiencies="[]",
        active_injuries="[]",
        exhaustion=0,
        attr_str=10,
        attr_dex=10,
        attr_int=10,
        attr_cha=10,
        attr_wis=10,
        hp=10,
    )
    outcome = progress_disease(deadly)
    check("deadly daily hp", outcome.get("hp_loss", 0) >= 1)

    starved = Row(
        exhaustion=0,
        hunger=5,
        thirst=80,
        mood=5,
        condition="healthy",
    )
    check("critical mood blocks", full_activity_block(starved) is not None)
    check("burnet shield", herb_special_effect("burnet", deadly) == "march_shield")
    check("sorrel restore", herb_special_effect("sorrel", deadly) == "sorrel_restore")
    check("slippery elm", herb_special_effect("slippery_elm", deadly) == "jaw_meal_shield")


def main() -> None:
    test_needs_exhaustion()
    test_mood_exhaustion()
    test_exhaustion_death_and_tiers()
    test_bleeding_exhaustion()
    test_herbs_and_hazards()
    test_exhaustion_disadvantage()
    test_disease_and_gates()
    print(f"\n{_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
