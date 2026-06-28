"""Admin possess session tests; run: python -m tests.test_admin_possess"""

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
    db.purge_test_accounts()
    admin_id = 990001
    player_id = 990002

    db.register_user(admin_id, "AdminWolf", affiliation="lone", wolf_role="omega")
    db.register_user(player_id, "PlayerWolf", affiliation="lone", wolf_role="omega")
    player_wolf = db.get_user(player_id)
    assert player_wolf

    ok, msg = db.set_admin_possess(admin_id, player_wolf["id"])
    check("set possess", ok, msg)
    check("get_user returns possessed wolf", db.get_user(admin_id)["wolf_name"] == "PlayerWolf")
    session = db.get_possess_session(admin_id)
    check(
        "session owner",
        session is not None and session["owner_discord_id"] == player_id,
        str(session),
    )

    ok, msg = db.clear_admin_possess(admin_id)
    check("clear possess", ok, msg)
    check("back to admin wolf", db.get_user(admin_id)["wolf_name"] == "AdminWolf")
    check("no session", db.get_possess_session(admin_id) is None)

    ok, msg = db.set_admin_possess(admin_id, db.get_user(admin_id)["id"])
    check("cannot possess own wolf", not ok)

    print(f"\n{_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
