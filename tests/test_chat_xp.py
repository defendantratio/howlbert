"""Chat XP tests; run: python -m tests.test_chat_xp"""

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

    discord_id = 888001
    guild_id = 888002
    day = 9001

    db.register_user(
        discord_id,
        "ChatWolf",
        affiliation="lone",
        wolf_role="omega",
    )
    account = db.get_account(discord_id)
    start_xp = account["xp"] if account else 0

    first = db.try_grant_chat_xp(discord_id, guild_id, day)
    after_first = db.get_account(discord_id)["xp"]
    check("first chat xp granted", first and after_first == start_xp + 1, f"{after_first} vs {start_xp + 1}")

    second = db.try_grant_chat_xp(discord_id, guild_id, day)
    after_second = db.get_account(discord_id)["xp"]
    check("same day no duplicate", not second and after_second == after_first)

    next_day = db.try_grant_chat_xp(discord_id, guild_id, day + 1)
    after_next = db.get_account(discord_id)["xp"]
    check("next sunrise grants again", next_day and after_next == after_second + 1)

    unregistered = db.try_grant_chat_xp(888999, guild_id, day + 2)
    check("unregistered wolf skipped", not unregistered)

    print(f"\n{_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
