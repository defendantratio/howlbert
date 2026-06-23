"""Life system tests; run: python -m tests.test_life"""

from __future__ import annotations

import database as db
from engine.blooding import award_blooding_on_hunt, blooding_gate_message, is_unblooded_juvenile
from engine.courtship import suggest_court_difficulty
from engine.youth_lineage import parse_litter_names

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

    names, err = parse_litter_names("Ash, Briar", 2)
    check("parse litter names", names == ["Ash", "Briar"] and err is None)

    names_short, err_short = parse_litter_names("Ash", 2)
    check("reject short litter", names_short is None and err_short is not None)

    class Row(dict):
        def keys(self):
            return super().keys()

    juvenile = Row(
        age_months=12,
        has_blooding=0,
        wolf_name="Scout",
        discord_id=1,
        id=1,
        pack_id=None,
    )
    check("unblooded juvenile", is_unblooded_juvenile(juvenile))
    check("blooding gate", blooding_gate_message(juvenile) is not None)

    adult = Row(age_months=30, has_blooding=0, wolf_name="Old", discord_id=2, id=2)
    check("adult not unblooded", not is_unblooded_juvenile(adult))

    courter = Row(pack_id=1, standing=5)
    target_low = Row(pack_id=1, standing=2)
    check("hostile standing", suggest_court_difficulty(courter, target_low, None) == "hostile")

    target_high = Row(pack_id=1, standing=9)
    check("friendly standing", suggest_court_difficulty(courter, target_high, None) == "friendly")

    db.record_court_attempt(999001, 999002, 5000)
    check(
        "court pair block",
        db.court_blocked_for_pair(999001, 999002, 5000),
    )

    slots = db.count_slot_wolves(999999999)
    check("slot count ok", isinstance(slots, int))

    pending_id = db.create_pending_role_feature(
        guild_id=1,
        discord_id=888001,
        wolf_id=888101,
        wolf_name="TestWolf",
        role_feature="scout",
    )
    check("create pending role feature", pending_id > 0)

    row = db.get_pending_role_feature(pending_id)
    check(
        "get pending role feature",
        row is not None and row["status"] == "pending" and row["role_feature"] == "scout",
    )

    open_row = db.get_open_pending_for_wolf(888101)
    check("open pending for wolf", open_row is not None and open_row["id"] == pending_id)

    listed = db.list_open_pending_role_features(1)
    check("list open pending", any(r["id"] == pending_id for r in listed))

    db.set_pending_role_feature_status(pending_id, "approved", resolved_by_discord_id=1)
    resolved = db.get_pending_role_feature(pending_id)
    check(
        "set pending status",
        resolved is not None
        and resolved["status"] == "approved"
        and resolved["resolved_by_discord_id"] == 1,
    )

    check("no open after resolve", db.get_open_pending_for_wolf(888101) is None)

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
