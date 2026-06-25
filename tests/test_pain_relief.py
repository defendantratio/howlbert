"""Pain relief herb buffs; run: python -m tests.test_pain_relief"""

from __future__ import annotations

from engine.herb_buffs import apply_supplemental_herb, pain_relief_active
from engine.long_term_injuries import check_adjustments

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


def test_willow_bark_pain_relief() -> None:
    print("\n=== willow bark ===")
    user = {
        "id": 1,
        "discord_id": 1,
        "mood": 50,
        "herb_buffs": "{}",
        "disease": "",
    }
    outcome = apply_supplemental_herb("willow_bark", user, day=10, outcome="healed")
    check("applies relief", outcome is not None and "Pain" in outcome["message"])
    user["herb_buffs"] = outcome["fields"]["herb_buffs"]
    check("buff active", pain_relief_active(user, 10))
    check("expires next day", not pain_relief_active(user, 11))


def test_poppy_pain_relief() -> None:
    print("\n=== poppy seeds ===")
    user = {
        "id": 2,
        "discord_id": 2,
        "mood": 50,
        "herb_buffs": "{}",
        "disease": "insomnia:active",
    }
    outcome = apply_supplemental_herb("poppy_seeds", user, day=5, outcome="healed")
    check("sedative relief", outcome is not None and "Sedative" in outcome["message"])
    user["herb_buffs"] = outcome["fields"]["herb_buffs"]
    check("pain buff active", pain_relief_active(user, 5))
    check("lasts through day", pain_relief_active(user, 6))


def test_chronic_pain_suppressed() -> None:
    print("\n=== chronic pain check ===")
    user = {
        "long_term_injuries": '["chronic_pain"]',
        "herb_buffs": '{"pain_relief_until_day": 20}',
    }
    mod, disadv, note = check_adjustments(
        user,
        attr_keys=("attr_str",),
        skill_key=None,
        weather="rain",
        day_number=20,
        first_physical_today=True,
    )
    check("no disadvantage", not disadv, note)
    check("relief noted", "Pain relief" in note)


def test_meadowsweet_pain_exhaustion_skip() -> None:
    print("\n=== meadowsweet pain exhaustion ===")
    import sqlite3

    from engine.exhaustion_effects import consume_pain_exhaustion_skip
    from engine.herb_buffs import get_buffs

    user = {
        "id": 3,
        "discord_id": 3,
        "mood": 50,
        "herb_buffs": "{}",
        "disease": "",
        "condition": "healthy",
        "active_injuries": "[]",
    }
    outcome = apply_supplemental_herb("meadowsweet", user, day=8, outcome="healed")
    check("applies meadowsweet", outcome is not None and "exhaustion" in outcome["message"].lower())
    user["herb_buffs"] = outcome["fields"]["herb_buffs"]
    check("skip flag set", bool(get_buffs(user).get("pain_exhaustion_skip")))

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, herb_buffs TEXT)")
    conn.execute("INSERT INTO users (id, herb_buffs) VALUES (3, ?)", (user["herb_buffs"],))
    row = conn.execute("SELECT * FROM users WHERE id = 3").fetchone()
    gain, used = consume_pain_exhaustion_skip(conn, row, 1)
    check("skips one gain", used and gain == 0)
    row2 = conn.execute("SELECT herb_buffs FROM users WHERE id = 3").fetchone()
    check("flag consumed", "pain_exhaustion_skip" not in (row2["herb_buffs"] or ""))


def main() -> None:
    test_willow_bark_pain_relief()
    test_poppy_pain_relief()
    test_chronic_pain_suppressed()
    test_meadowsweet_pain_exhaustion_skip()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
