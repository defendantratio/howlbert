"""Kickstarter backer badge tests; run: python -m tests.test_kickstarter"""

from __future__ import annotations

import database as db
from engine.kickstarter import (
    grant_tier2_rewards,
    kickstarter_status_lines,
    profile_footer_suffix,
)

TEST_GUILD = 1516980863911329802
USER_KS = 999200001000000001

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


def _ensure_world() -> None:
    if not db.get_world(TEST_GUILD):
        with db.get_db() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO world_state
                (guild_id, day_number, season, weather, time_of_day, last_rollover)
                VALUES (?, 1, 'spring', 'clear', 'dawn', 'test')
                """,
                (TEST_GUILD,),
            )


def main() -> None:
    db.init_db()
    _ensure_world()
    if not db.get_user(USER_KS):
        db.register_user(USER_KS, "KsBacker", "greyspire", "hunter")

    db.revoke_kickstarter_backer(USER_KS)
    check("not backer initially", not db.is_kickstarter_backer(USER_KS))
    check("no status lines", kickstarter_status_lines(USER_KS) == [])

    check("grant badge", db.grant_kickstarter_backer(USER_KS))
    check("is backer", db.is_kickstarter_backer(USER_KS))
    check("grant idempotent", not db.grant_kickstarter_backer(USER_KS))
    check("status lines", len(kickstarter_status_lines(USER_KS)) >= 2)
    check("profile footer", profile_footer_suffix(USER_KS) is not None)

    db.revoke_kickstarter_backer(USER_KS)
    ok, note = grant_tier2_rewards(USER_KS, bonus_item="herb_bundle")
    check("tier2 grant ok", ok, note)
    check("tier2 badge", db.is_kickstarter_backer(USER_KS))
    user = db.get_user(USER_KS)
    check("tier2 bones", user["bones"] >= 75)

    bad, err = grant_tier2_rewards(USER_KS, bonus_item="not_real")
    check("reject bad item", not bad)

    db.revoke_kickstarter_backer(USER_KS)
    print(f"\n{_pass} passed, {_fail} failed")
    db.purge_test_accounts()
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
