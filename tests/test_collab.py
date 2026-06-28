"""Collaborative hunt/patrol DB tests; run: python -m tests.test_collab"""

from __future__ import annotations

import database as db

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


def main() -> None:
    db.init_db()

    hunt_id = db.create_collab_hunt(
        guild_id=99,
        channel_id=1,
        leader_wolf_id=1001,
        pack_id=5,
        day_number=1,
    )
    db.add_collab_hunt_member(
        hunt_id, wolf_id=1001, wolf_name="Alpha", discord_id=1
    )
    check("collab hunt created", hunt_id > 0)
    check("wolf in open hunt", db.wolf_in_open_collab_hunt(1001))

    db.set_collab_hunt_status(hunt_id, "encounter")
    check("wolf still blocked in encounter", db.wolf_in_open_collab_hunt(1001))
    check(
        "leader blocked from second call",
        db.get_open_collab_hunt_by_leader(1001) is not None,
    )

    survey_id = db.create_collab_patrol(
        guild_id=99,
        channel_id=2,
        leader_wolf_id=2001,
        pack_id=5,
        day_number=1,
        patrol_kind="survey",
    )
    trail_id = db.create_collab_patrol(
        guild_id=99,
        channel_id=3,
        leader_wolf_id=2002,
        pack_id=5,
        day_number=1,
        patrol_kind="trail",
    )
    survey = db.get_collab_patrol(survey_id)
    trail = db.get_collab_patrol(trail_id)
    check("survey kind", survey["patrol_kind"] == "survey")
    check("trail kind", trail["patrol_kind"] == "trail")

    db.close_collab_hunts_for_guild(99)
    db.close_collab_patrols_for_guild(99)
    hunt = db.get_collab_hunt(hunt_id)
    check("rollover closes encounter hunts", hunt["status"] == "cancelled")

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
