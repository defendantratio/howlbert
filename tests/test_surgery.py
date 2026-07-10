"""Surgery supply checks and optional herb flags; run: python -m tests.test_surgery"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.surgery import (
    missing_surgery_herbs,
    run_surgery,
    SURGERY_PROCEDURES,
)

_pass = 0
_fail = 0


class Row(dict):
    def keys(self):
        return super().keys()


def check(name: str, cond: bool, detail: str = "") -> None:
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  OK  {name}")
    else:
        _fail += 1
        print(f" FAIL {name}" + (f" - {detail}" if detail else ""))


def _medic(**kw):
    base = dict(
        id=1,
        discord_id=100,
        wolf_name="Basil",
        wolf_role="medic",
        bonus_role_feature=None,
        last_surgery_day=0,
        skill_proficiencies='["medicine"]',
        attr_wis=6,
        hp=10,
        condition="healthy",
    )
    base.update(kw)
    return Row(base)


def _patient(**kw):
    base = dict(
        id=2,
        discord_id=200,
        wolf_name="Patch",
        active_injuries='["fractured_rib"]',
        hp=8,
        condition="healthy",
    )
    base.update(kw)
    return Row(base)


def _has_herbs(*keys: str):
    def side_effect(user, herb_key: str) -> bool:
        stacks = {
            1: ("comfrey", "bindweed", "cobwebs", "yarrow", "meadowsweet", "purple_loosestrife"),
            2: (),
        }
        if herb_key == "stick":
            return False
        return herb_key in stacks.get(user["id"], ())

    return side_effect


# _stick_count (engine/surgery.py) resolves sticks via the inventory item
# system now (db.get_item_by_key + db.get_inventory_quantity_for_wolf by
# wolf id), not the older herb_stacks table. Mock that path instead.
STICK_ITEM = {"id": 999, "key": "stick"}


def _stick_quantity(count: int, *, on_patient: bool = False):
    target_wolf_id = 2 if on_patient else 1

    def side_effect(wolf_id: int, item_id: int) -> int:
        return count if wolf_id == target_wolf_id else 0

    return side_effect


def main() -> None:
    surgeon = _medic()
    patient = _patient()

    with patch("engine.surgery.db.get_item_by_key", return_value=STICK_ITEM), patch(
        "engine.surgery.db.get_inventory_quantity_for_wolf", side_effect=_stick_quantity(0)
    ), patch("engine.surgery.is_full_medic", return_value=True):
        missing = missing_surgery_herbs(surgeon, patient, SURGERY_PROCEDURES["set_bone"])
        check("set_bone missing stick", "stick" in missing)

        ok, msg = run_surgery(surgeon, patient, "set_bone", day=1)
        check("stick missing fails surgery", not ok and "stick" in msg.lower(), msg)

    with patch("engine.surgery.db.get_item_by_key", return_value=STICK_ITEM), patch(
        "engine.surgery.db.get_inventory_quantity_for_wolf", side_effect=_stick_quantity(1)
    ), patch("engine.surgery.is_full_medic", return_value=True), patch(
        "engine.surgery.participant_has_herb", side_effect=_has_herbs()
    ):
        ok, msg = run_surgery(surgeon, patient, "set_bone", day=1)
        check("one stick not enough", not ok and "2 sticks" in msg, repr(msg))

    with patch("engine.surgery.db.get_item_by_key", return_value=STICK_ITEM), patch(
        "engine.surgery.db.get_inventory_quantity_for_wolf", side_effect=_stick_quantity(2)
    ), patch("engine.surgery.is_full_medic", return_value=True), patch(
        "engine.surgery.participant_has_herb",
        side_effect=lambda u, k: k in ("comfrey", "bindweed", "stick"),
    ), patch(
        "engine.surgery.consume_participant_herb", return_value=True
    ), patch("engine.surgery.medicine_check", return_value={"die": 15, "modifier": 5, "proficiency": 2, "total": 22}), patch(
        "engine.surgery.db.update_user_by_id"
    ), patch("engine.surgery.db.get_user_by_id", return_value=patient), patch(
        "engine.surgery.parse_injuries", return_value=["fractured_rib"]
    ):
        ok, msg = run_surgery(surgeon, patient, "set_bone", day=1, use_meadowsweet=True)
        check("meadowsweet flag without herb fails", not ok and "meadowsweet" in msg.lower(), repr(msg))

    consumed: list[str] = []

    def track_consume(user, herb_key: str) -> bool:
        consumed.append(herb_key)
        return True

    stitch_patient = _patient(active_injuries='["deep_gash"]')
    with patch("engine.surgery.db.get_item_by_key", return_value=STICK_ITEM), patch(
        "engine.surgery.db.get_inventory_quantity_for_wolf", side_effect=_stick_quantity(1, on_patient=True)
    ), patch("engine.surgery.is_full_medic", return_value=True), patch(
        "engine.surgery.participant_has_herb",
        side_effect=lambda u, k: k in ("cobwebs", "yarrow", "stick", "meadowsweet"),
    ), patch("engine.surgery.consume_participant_herb", side_effect=track_consume), patch(
        "engine.surgery.medicine_check", return_value={"die": 12, "modifier": 3, "proficiency": 2, "total": 17}
    ), patch("engine.surgery.db.update_user_by_id"), patch(
        "engine.surgery.db.get_user_by_id", return_value=stitch_patient
    ), patch("engine.surgery.parse_injuries", return_value=["deep_gash"]), patch(
        "engine.surgery.random.randint", return_value=2
    ), patch("engine.surgery.db.set_user_conditions"):
        ok, _ = run_surgery(surgeon, stitch_patient, "stitch", day=1, use_meadowsweet=False)
        check("optional herb not auto-used", ok and "meadowsweet" not in consumed, str(consumed))

    consumed.clear()
    with patch("engine.surgery.db.get_item_by_key", return_value=STICK_ITEM), patch(
        "engine.surgery.db.get_inventory_quantity_for_wolf", side_effect=_stick_quantity(1, on_patient=True)
    ), patch("engine.surgery.is_full_medic", return_value=True), patch(
        "engine.surgery.participant_has_herb",
        side_effect=lambda u, k: k in ("cobwebs", "yarrow", "stick", "meadowsweet"),
    ), patch("engine.surgery.consume_participant_herb", side_effect=track_consume), patch(
        "engine.surgery.medicine_check", return_value={"die": 12, "modifier": 3, "proficiency": 2, "total": 17}
    ), patch("engine.surgery.db.update_user_by_id"), patch(
        "engine.surgery.db.get_user_by_id", return_value=stitch_patient
    ), patch("engine.surgery.parse_injuries", return_value=["deep_gash"]), patch(
        "engine.surgery.random.randint", return_value=2
    ), patch("engine.surgery.db.set_user_conditions"):
        ok, msg = run_surgery(surgeon, stitch_patient, "stitch", day=1, use_meadowsweet=True)
        check("meadowsweet consumed when flagged", ok and "meadowsweet" in consumed, str(consumed))
        check("meadowsweet flavor on success", "Meadowsweet" in msg, msg)

    with patch("engine.surgery.db.get_item_by_key", return_value=STICK_ITEM), patch(
        "engine.surgery.db.get_inventory_quantity_for_wolf", side_effect=_stick_quantity(2)
    ), patch("engine.surgery.is_full_medic", return_value=True), patch(
        "engine.surgery.participant_has_herb",
        side_effect=lambda u, k: k in ("comfrey", "bindweed", "stick"),
    ):
        ok, msg = run_surgery(
            surgeon,
            _patient(active_injuries='["fractured_rib"]'),
            "set_bone",
            day=1,
            use_loosestrife=True,
        )
        check("loosestrife wrong procedure", not ok and "stitch" in msg.lower(), repr(msg))

    dying = _patient(condition="dying", hp=0, active_injuries='["deep_gash"]')
    with patch("engine.surgery.db.get_item_by_key", return_value=STICK_ITEM), patch(
        "engine.surgery.db.get_inventory_quantity_for_wolf", side_effect=_stick_quantity(1, on_patient=True)
    ), patch("engine.surgery.is_full_medic", return_value=True), patch(
        "engine.surgery.participant_has_herb",
        side_effect=lambda u, k: k in ("cobwebs", "yarrow", "stick"),
    ):
        ok, msg = run_surgery(surgeon, dying, "stitch", day=1)
        check("dying patient cannot bite stick", not ok and "bite" in msg.lower(), repr(msg))

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
