"""Combat pin tests; run: python -m tests.test_combat_pin"""

from __future__ import annotations

import json

import database as db
from engine.combat import resolve_maneuver
from engine.combat_status import (
    apply_maneuver_pin_effects,
    attack_target_block,
    attacker_roll_modifiers,
    clear_fighter_pin,
    is_holding_pin,
    maneuver_pin_block,
    parse_combat_flags,
    set_fighter_pinned,
)
from engine.combat_guide import COMBAT_MANEUVERS

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


def _fighter(fid: int, *, flags: dict | None = None, hp: int = 20, enc: int = 1) -> Row:
    return Row(
        id=fid,
        hp=hp,
        max_hp=20,
        encounter_id=enc,
        combat_flags=json.dumps(flags or {}),
    )


def _stats(**attrs) -> Row:
    base = {
        "attr_str": 10,
        "attr_dex": 10,
        "attr_con": 10,
        "attr_int": 10,
        "attr_cha": 10,
        "attr_wis": 10,
        "skill_proficiencies": "[]",
        "hp": 20,
        "max_hp": 20,
    }
    base.update(attrs)
    return Row(**base)


def main() -> None:
    db.init_db()

    pinner = _fighter(10)
    pinned = _fighter(20, flags={"pinned": True, "pinned_by": 10})
    free = _fighter(30)

    block = maneuver_pin_block(COMBAT_MANEUVERS["belly_rake"], free, pinner)
    check("belly rake blocked when not pinned", block is not None)

    ok = maneuver_pin_block(COMBAT_MANEUVERS["belly_rake"], pinned, pinner)
    check("belly rake allowed vs pinner", ok is None)

    wrong = maneuver_pin_block(COMBAT_MANEUVERS["belly_rake"], pinned, free)
    check("belly rake blocked vs wrong target", wrong is not None)

    jump_block = maneuver_pin_block(COMBAT_MANEUVERS["jump_and_pin"], pinned, free)
    check("jump and pin blocked while pinned", jump_block is not None)

    back_ok = maneuver_pin_block(COMBAT_MANEUVERS["back_kick"], pinned, pinner)
    check("back kick allowed vs pinner", back_ok is None)

    disadv, adv = attacker_roll_modifiers(_stats(), "bite", pinned, free)
    check("pinned attacker at disadvantage", disadv and not adv)

    disadv2, adv2 = attacker_roll_modifiers(_stats(), "bite", free, pinned)
    check("attacks vs pinned have advantage", adv2 and not disadv2)

    reach = attack_target_block(pinned, free)
    check("pinned wolf blocked from biting others", reach is not None)

    with db.get_db() as conn:
        conn.execute("DELETE FROM combat_fighters")
        conn.execute(
            """
            INSERT INTO combat_fighters (id, encounter_id, discord_id, hp, max_hp, combat_flags)
            VALUES (10, 1, 0, 20, 20, '{}'),
                   (20, 1, 0, 20, 20, '{}')
            """
        )

    set_fighter_pinned(20, 10, 1)
    row = db.get_combat_fighter(1, 20)
    flags = parse_combat_flags(row)
    check(
        "set pin stores pinned_by and prone",
        flags.get("pinned") and flags.get("pinned_by") == 10 and flags.get("prone"),
    )
    check("pinner shows as holding pin", is_holding_pin(10, 1))

    note = apply_maneuver_pin_effects(
        _fighter(10, enc=1),
        _fighter(20, enc=1),
        "jump_and_pin",
        hit=True,
        defender_name="Target",
    )
    check("jump and pin applies on hit", note and "pinned" in note.lower())

    db.update_fighter_combat_flags(20, pinned=True, pinned_by=10, prone=True)
    escape = apply_maneuver_pin_effects(
        _fighter(20, flags={"pinned": True, "pinned_by": 10}, enc=1),
        _fighter(10, enc=1),
        "duck_and_twist",
        hit=True,
        defender_name="Pinner",
    )
    check("duck and twist clears pin", escape and "break free" in escape.lower())
    cleared = parse_combat_flags(db.get_combat_fighter(1, 20))
    check("pin cleared in db", not cleared.get("pinned"))

    lethal_block = maneuver_pin_block(
        COMBAT_MANEUVERS["killing_bite"],
        free,
        _fighter(40, hp=20),
        defender_hp=20,
        defender_max_hp=20,
    )
    check("killing bite blocked without pin or wounds", lethal_block is not None)

    lethal_ok = maneuver_pin_block(
        COMBAT_MANEUVERS["killing_bite"],
        free,
        _fighter(40, flags={"pinned": True, "pinned_by": 30}),
        defender_hp=20,
        defender_max_hp=20,
    )
    check("killing bite allowed on pinned foe", lethal_ok is None)

    release = resolve_maneuver(
        _stats(attr_dex=18),
        _stats(attr_dex=6),
        "jump_and_pin",
        attacker_f=_fighter(10, enc=1),
        defender_f=_fighter(20, enc=1),
    )
    check("resolve applies pin block rules", not release.get("blocked"))

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
