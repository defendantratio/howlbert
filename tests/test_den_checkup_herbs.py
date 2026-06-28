"""Den checkup scans every packmate's herb bag; run: python -m tests.test_den_checkup_herbs"""

from __future__ import annotations

from unittest.mock import patch

import database as db
from engine.medical_care import run_medic_rounds

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


class Row(dict):
    def keys(self):
        return super().keys()


def main() -> None:
    medic = Row(
        id=99,
        discord_id=99,
        wolf_name="Medic",
        wolf_role="medic",
        pack_id=1,
        last_medic_rounds_day=0,
        character_traits="",
        active_injuries="[]",
        disease="",
        condition="healthy",
        hp=10,
        bone_rest_until=0,
    )
    hunter = Row(
        id=1,
        discord_id=1,
        wolf_name="HunterWolf",
        wolf_role="hunter",
        pack_id=1,
        character_traits="",
        active_injuries="[]",
        disease="",
        condition="healthy",
        hp=10,
        bone_rest_until=0,
    )
    barkhollow = Row(
        id=2,
        discord_id=2,
        wolf_name="Barkhollow",
        wolf_role="hunter",
        pack_id=1,
        character_traits="{}",
        active_injuries="[]",
        disease="",
        condition="healthy",
        hp=10,
        bone_rest_until=0,
    )

    with patch.object(db, "get_pack_den_wolves", return_value=[hunter, barkhollow]):
        with patch.object(db, "get_herb_stacks", return_value=[]):
            with patch.object(db, "update_user_by_id"):
                with patch(
                    "engine.restricted_herbs.medic_rounds_scan_hoarders",
                    return_value=([], []),
                ):
                    ok, body = run_medic_rounds(medic, day=1)

    check("checkup ok", ok)
    check("hunter thin bag listed", "HunterWolf" in body and "low herbs" in body)
    check("barkhollow thin bag listed", "Barkhollow" in body)
    check("lists both wolves", body.count("low herbs") == 2, body)

    apprentice = Row(
        id=3,
        wolf_name="Apprentice",
        wolf_role="medic_apprentice",
        pack_id=1,
        last_medic_rounds_day=0,
        character_traits="",
        active_injuries="[]",
        disease="",
        condition="healthy",
        hp=10,
        bone_rest_until=0,
    )
    ok_app, body_app = run_medic_rounds(apprentice, day=1)
    check("apprentice blocked", not ok_app and "apprentices observe" in body_app, body_app)

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
