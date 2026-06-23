"""Consent, rollover news, and pack season goal tests; run: python -m tests.test_consent_news"""

from __future__ import annotations

import database as db
from engine.adoption_consent import accept_pending_adoption, decline_pending_adoption
from engine.family import GESTATION_DAYS
from engine.pack_season_goals import format_stash_goal_line, record_stash_deposit, stash_goal_target
from engine.rollover_news import collect_births_ready, collect_den_news
from utils.notifications import births_crossing_threshold

TEST_GUILD = 1516980863911329802
USER_MOTHER = 999100001000000001
USER_FATHER = 999100002000000002
USER_ADOPTER_A = 999100003000000003
USER_ADOPTER_B = 999100004000000004
USER_YOUTH_OWNER = 999100005000000005

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


def _ensure_world(day: int = 100) -> None:
    if not db.get_world(TEST_GUILD):
        with db.get_db() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO world_state
                (guild_id, day_number, season, weather, time_of_day, last_rollover)
                VALUES (?, ?, 'spring', 'clear', 'dawn', 'test')
                """,
                (TEST_GUILD, day),
            )
    else:
        with db.get_db() as conn:
            conn.execute(
                "UPDATE world_state SET day_number = ? WHERE guild_id = ?",
                (day, TEST_GUILD),
            )


def _ensure_user(discord_id: int, name: str) -> int:
    if not db.get_user(discord_id):
        _ensure_world()
        db.register_user(discord_id, name, "greyspire", "hunter")
    return db.get_user(discord_id)["id"]


def test_rollover_den_news() -> None:
    print("\n=== rollover den news ===")
    news = collect_den_news(500, age_milestones=[])
    check("den news keys", all(k in news for k in ("births_ready", "pack_events", "treasury_warnings")))


def test_births_ready() -> None:
    print("\n=== birth notifications ===")
    day = 200
    _ensure_world(day)
    mother_id = _ensure_user(USER_MOTHER, "BirthMother")
    father_id = _ensure_user(USER_FATHER, "BirthFather")
    db.set_bonded_mates(mother_id, father_id)
    db.set_pregnancy(mother_id, father_id, day; GESTATION_DAYS)

    ready = collect_births_ready(day)
    check("births ready list", any("BirthMother" in line for line in ready))

    recipients = births_crossing_threshold(day)
    ids = {r[0] for r in recipients}
    check("mother notified", USER_MOTHER in ids)
    check("father notified", USER_FATHER in ids)

    db.clear_pregnancy(mother_id)


def test_adoption_consent() -> None:
    print("\n=== adoption consent ===")
    day = 50
    _ensure_world(day)
    adopter1 = _ensure_user(USER_ADOPTER_A, "AdopterOne")
    adopter2 = _ensure_user(USER_ADOPTER_B, "AdopterTwo")
    youth_id = _ensure_user(USER_YOUTH_OWNER, "YouthPup")
    db.update_user(USER_YOUTH_OWNER, wolf_id=youth_id, age_months=4)

    pending_id = db.create_pending_adoption(
        guild_id=TEST_GUILD,
        channel_id=1,
        adopter_1_wolf_id=adopter1,
        adopter_2_wolf_id=adopter2,
        youth_wolf_id=youth_id,
        youth_owner_discord_id=USER_YOUTH_OWNER,
        day_number=day,
    )
    check("pending created", pending_id > 0)

    ok, msg = decline_pending_adoption(pending_id)
    check("decline ok", ok and "stays" in msg.lower())

    db.set_bonded_mates(adopter1, adopter2)
    with db.get_db() as conn:
        conn.execute(
            "UPDATE users SET adopt_parent_1_id = NULL, adopt_parent_2_id = NULL WHERE id = ?",
            (youth_id,),
        )
    pending_id2 = db.create_pending_adoption(
        guild_id=TEST_GUILD,
        channel_id=1,
        adopter_1_wolf_id=adopter1,
        adopter_2_wolf_id=adopter2,
        youth_wolf_id=youth_id,
        youth_owner_discord_id=USER_YOUTH_OWNER,
        day_number=day,
    )
    ok2, msg2 = accept_pending_adoption(pending_id2)
    check("accept ok", ok2, msg2)
    youth = db.get_user_by_id(youth_id)
    check(
        "adoptive parents set",
        youth["adopt_parent_1_id"] == adopter1 and youth["adopt_parent_2_id"] == adopter2,
    )


def test_mate_pending() -> None:
    print("\n=== mate consent pending ===")
    day = 60
    _ensure_world(day)
    wolf_a = _ensure_user(999100006000000006, "CourterA")
    wolf_b = _ensure_user(999100007000000007, "CourterB")
    pending_id = db.create_pending_mate(
        guild_id=TEST_GUILD,
        channel_id=1,
        initiator_wolf_id=wolf_a,
        partner_wolf_id=wolf_b,
        partner_discord_id=999100007000000007,
        day_number=day,
    )
    check("mate pending created", pending_id > 0)
    existing = db.get_pending_mate_for_pair(wolf_a, wolf_b)
    check("mate pair lookup", existing is not None and existing["id"] == pending_id)
    db.set_pending_mate_status(pending_id, "declined")


def test_pack_season_goal() -> None:
    print("\n=== pack season goals ===")
    pack = db.get_pack_by_key("greyspire")
    check("greyspire pack", pack is not None)
    if not pack:
        return
    day = 7
    target = stash_goal_target(day)
    db.update_pack_season_goal(
        pack["id"],
        season_goal_epoch=0,
        season_stash_deposits=0,
        season_stash_goal_met=0,
    )
    line = None
    for _ in range(target):
        line = record_stash_deposit(pack["id"], day)
    check("goal completes", line is not None and "Season goal met" in line)
    progress = format_stash_goal_line(db.get_pack(pack["id"]), day)
    check("goal shows complete", "complete" in progress.lower())
    db.update_pack_season_goal(
        pack["id"],
        season_stash_deposits=0,
        season_stash_goal_met=0,
    )


def main() -> None:
    db.init_db()
    test_rollover_den_news()
    test_births_ready()
    test_adoption_consent()
    test_mate_pending()
    test_pack_season_goal()
    print(f"\n{_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
