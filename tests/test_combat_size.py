"""Combat size and maneuver eligibility; run: python -m tests.test_combat_size"""

from __future__ import annotations

import database as db
from engine.bestiary import build_npc_stats
from engine.combat import resolve_maneuver
from engine.combat_guide import COMBAT_MANEUVERS
from engine.combat_size import can_pin_target, can_scruff_target, size_rank
from engine.combat_status import maneuver_pin_block

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


def _fighter(fid: int, *, enc: int = 1) -> Row:
    return Row(id=fid, hp=20, max_hp=20, encounter_id=enc, combat_flags="{}")


def main() -> None:
    db.init_db()

    cat = build_npc_stats("clan_warrior")
    wolf = {"attr_str": 6, "attr_dex": 5, "attr_con": 5, "size_class": "medium", "hp": 20, "max_hp": 20}
    bear = build_npc_stats("grizzly_bear")

    check("cat is small", size_rank(cat) < size_rank(wolf))
    check("wolf can pin cat", can_pin_target(wolf, cat))
    check("cat cannot pin wolf", not can_pin_target(cat, wolf))
    check("wolf can scruff cat", can_scruff_target(wolf, cat))
    check("cat cannot scruff wolf", not can_scruff_target(cat, wolf))
    check("bear outranks wolf", size_rank(bear) > size_rank(wolf))

    block = maneuver_pin_block(
        COMBAT_MANEUVERS["jump_and_pin"],
        _fighter(10),
        _fighter(20),
        defender_hp=20,
        defender_max_hp=20,
        attacker_stats=cat,
        defender_stats=wolf,
    )
    check("jump and pin blocked cat vs wolf", block is not None)

    scruff_block = maneuver_pin_block(
        COMBAT_MANEUVERS["scruff_shake"],
        _fighter(10),
        _fighter(20),
        defender_hp=20,
        defender_max_hp=20,
        attacker_stats=cat,
        defender_stats=wolf,
    )
    check("scruff shake blocked cat vs wolf", scruff_block is not None)

    dodge = resolve_maneuver(
        wolf,
        cat,
        "low_dodge",
        attacker_f=_fighter(10, enc=1),
        defender_f=_fighter(20, enc=1),
    )
    check("low dodge applies defense bonus", dodge["defender_mod"] >= 2)

    from engine.npc_combat import pick_npc_action

    action, maneuver = pick_npc_action(_fighter(1), _fighter(2), cat, wolf)
    check("npc cat picks action", action in ("bite", "claw"))

    juvenile = {"wolf_role": "juvenile", "wolf_name": "Pup", "attr_str": 3, "attr_dex": 4, "hp": 15, "max_hp": 15}
    check("juvenile wolf is small", size_rank(juvenile) < size_rank(wolf))
    check("cat can pin juvenile", can_pin_target(cat, juvenile))

    large_wolf = {"wolf_role": "hunter", "size_class": "large", "wolf_name": "Bulk", "hp": 25, "max_hp": 25}
    check("custom large wolf outranks medium", size_rank(large_wolf) > size_rank(wolf))
    check("large wolf can pin medium wolf", can_pin_target(large_wolf, wolf))

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
