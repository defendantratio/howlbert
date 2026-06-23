"""Sacred visit ancestor lines; run: python -m tests.test_sacred_visits"""

from __future__ import annotations

from unittest.mock import patch

from engine.sacred_visits import (
    HALF_MOON_DAYS,
    SACRED_ANCESTOR_LINES,
    pick_sacred_ancestor_word,
    record_sacred_visit,
)


class Row(dict):
    def keys(self):
        return super().keys()


_pass = 0
_fail = 0


def check(name: str, cond: bool) -> None:
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  OK  {name}")
    else:
        _fail += 1
        print(f" FAIL {name}")


def test_ancestor_word() -> None:
    print("\n=== sacred visit ===")
    user = Row(wolf_name="Mirewort", wolf_role="medic", great_pack="mistmoor", id=1, discord_id=1)
    word = pick_sacred_ancestor_word(user)
    check("word non-empty", bool(word))
    check("word in pools", word in SACRED_ANCESTOR_LINES or word in (
        "The Belly-Rip hears what you withhold from the sick.",
        "Fog lies; your hands on a fever do not.",
    ))
    with patch("engine.sacred_visits.pick_sacred_ancestor_word", return_value="Fog lies; your hands on a fever do not."):
        with patch("database.update_user_by_id"):
            ok, body = record_sacred_visit(user, day=10)
    check("visit ok", ok)
    check("wolf name", "Mirewort" in body)
    check("ancestors say", "The ancestors say:" in body and "Fog lies" in body)
    check("next visit", f"**{HALF_MOON_DAYS}**" in body)


def main() -> None:
    test_ancestor_word()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
