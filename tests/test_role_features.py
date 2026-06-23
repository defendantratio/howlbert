"""Role feature hooks; run: python -m tests.test_role_features"""

from __future__ import annotations

import database as db
from engine.role_features import (
    can_grant_commanding_howl,
    grant_commanding_howl_buffs,
    guard_imposes_attack_disadvantage,
    scout_hide_after_check,
    try_consume_blood_oath_buff,
    try_consume_commanding_howl_buff,
    weather_is_lightly_obscured,
)

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


def test_weather_and_scout_hide() -> None:
    print("\n=== weather & scout hide ===")
    check("thick_fog obscured", weather_is_lightly_obscured("thick_fog"))
    check("clear not obscured", not weather_is_lightly_obscured("clear"))

    db.init_db()
    did = 900030001
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at, condition, wolf_role
            ) VALUES (?, 'Scout', 1, 'scout', 't', 'healthy', 'scout')
            """,
            (did,),
        )
    user = db.get_user(did)
    note = scout_hide_after_check(
        user,
        weather_key="thick_fog",
        day=3,
        skill_key="stealth",
        success=True,
    )
    check("stealth hide note", "Unseen Paw" in note)
    user = db.get_user(did)
    check("scout_hidden_day set", int(user["scout_hidden_day"]) >= 3)
    check(
        "tracking no hide",
        scout_hide_after_check(
            user, weather_key="thick_fog", day=3, skill_key="tracking", success=True
        )
        == "",
    )


def test_commanding_howl() -> None:
    print("\n=== commanding howl ===")
    db.init_db()
    did_a = 900010001
    did_b = 900010002
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id IN (?, ?)", (did_a, did_b))
        conn.execute(
            """
            INSERT INTO users (discord_id, wolf_name, pack_id, rank, created_at, condition, wolf_role)
            VALUES (?, 'Alpha', 1, 'alpha', 't', 'healthy', 'alpha'),
                   (?, 'Mate', 1, 'subordinate', 't', 'healthy', 'hunter')
            """,
            (did_a, did_b),
        )
    alpha = db.get_user(did_a)
    pack = db.get_pack(1)
    check("alpha can grant", can_grant_commanding_howl(alpha, pack))
    count = grant_commanding_howl_buffs(1, exclude_wolf_id=alpha["id"])
    check("buffs granted", count >= 1)
    mate = db.get_user(did_b)
    check("mate has buff", int(mate["commanding_howl_buff"]) == 1)
    check("consume buff", try_consume_commanding_howl_buff(mate))
    mate = db.get_user(did_b)
    check("buff cleared", int(mate["commanding_howl_buff"]) == 0)


def test_blood_oath() -> None:
    print("\n=== blood oath ===")
    db.init_db()
    did = 900020001
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at, condition, wolf_role
            ) VALUES (?, 'Advisor', 1, 'advisor', 't', 'healthy', 'advisor')
            """,
            (did,),
        )
    user = db.get_user(did)
    check(
        "first charisma adv",
        try_consume_blood_oath_buff(
            user, ("attr_cha",), skill_key="persuasion", game_day=5
        ),
    )
    user = db.get_user(did)
    check("day recorded", int(user["last_blood_oath_day"]) == 5)
    check(
        "same day blocked",
        not try_consume_blood_oath_buff(
            user, ("attr_cha",), skill_key="persuasion", game_day=5
        ),
    )
    user = db.get_user(did)
    check(
        "next day ok",
        try_consume_blood_oath_buff(
            user, ("attr_cha",), skill_key="persuasion", game_day=6
        ),
    )


def test_guard_disadvantage() -> None:
    print("\n=== guard ===")
    db.init_db()
    did_g = 900040003
    with db.get_db() as conn:
        conn.execute("DELETE FROM combat_fighters WHERE encounter_id = 9001")
        conn.execute("DELETE FROM combat_encounters WHERE id = 9001")
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did_g,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at, condition, wolf_role
            ) VALUES (?, 'Guard', 1, 'guard', 't', 'healthy', 'guard')
            """,
            (did_g,),
        )
        conn.execute(
            """
            INSERT INTO combat_encounters (id, guild_id, channel_id, status, round, created_at)
            VALUES (9001, 1, 1, 'active', 1, 'test')
            """
        )
        conn.execute(
            """
            INSERT INTO combat_fighters (id, encounter_id, discord_id, hp, max_hp, combat_flags)
            VALUES (9010, 9001, 1, 10, 10, '{}'),
                   (9020, 9001, 2, 10, 10, '{}'),
                   (9030, 9001, ?, 10, 10, '{}')
            """,
            (did_g,),
        )
    check(
        "guard imposes disadv",
        guard_imposes_attack_disadvantage(9001, 9010, 9020),
    )


if __name__ == "__main__":
    test_weather_and_scout_hide()
    test_commanding_howl()
    test_blood_oath()
    test_guard_disadvantage()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)
