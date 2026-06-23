"""Whispering Wild fog spirit hooks; run: python -m tests.test_whispering_wild"""

from __future__ import annotations

from unittest.mock import patch

from engine.whispering_wild import (
    format_mental_rounds_line,
    is_whispering_weather,
    spirit_whisper_on_sniff,
)


class Row(dict):
    def keys(self):
        return super().keys()


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


def test_weather_and_whispers() -> None:
    print("\n=== whispering weather ===")
    check("fog whispers", is_whispering_weather("fog"))
    check("clear not", not is_whispering_weather("clear"))
    user = Row(
        discord_id=1,
        id=1,
        wolf_name="Mist",
        great_pack="mistmoor",
        wolf_role="hunter",
        condition="healthy",
        disease="",
    )
    with patch("engine.whispering_wild.random.choice", return_value="test whisper"):
        with patch("engine.whispering_wild.try_contract_disease", return_value=None):
            note = spirit_whisper_on_sniff(user, weather="fog")
    check("sniff note", note and "test whisper" in note)
    mental = format_mental_rounds_line(
        Row(wolf_name="Ash", disease="anxiety:uneasy", condition="healthy")
    )
    check("mental rounds", mental and "Ash" in mental and "Uneasy" in mental)


def main() -> None:
    test_weather_and_whispers()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
