"""Bestiary tests; cats, fox, badger; run: python -m tests.test_bestiary"""

from __future__ import annotations

import database as db
from engine.bestiary import BESTIARY_NPCS, NPC_CATEGORY_LABELS, build_npc_stats, npc_choices_for_category, npc_hp

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

    check("cats category label", "cats" in NPC_CATEGORY_LABELS)
    check("reptiles category label", "reptiles" in NPC_CATEGORY_LABELS)
    cat_keys = [k for k, v in BESTIARY_NPCS.items() if v["category"] == "cats"]
    check("five cat types", len(cat_keys) == 5, str(cat_keys))
    reptile_keys = [k for k, v in BESTIARY_NPCS.items() if v["category"] == "reptiles"]
    check("four reptile types", len(reptile_keys) == 4, str(reptile_keys))

    for key in ("fox", "badger"):
        check(f"{key} in predators", BESTIARY_NPCS[key]["category"] == "predators")

    stats = build_npc_stats("clan_warrior")
    check("clan warrior claw profile", stats["npc_attack_profile"]["type"] == "claw")
    check("clan warrior hp", npc_hp(BESTIARY_NPCS["clan_warrior"]) == 21)

    badger_hp = npc_hp(BESTIARY_NPCS["badger"])
    check("badger tough", badger_hp >= 14, str(badger_hp))

    choices = npc_choices_for_category("cats")
    check("cat npc choices", len(choices) == 5)

    border_keys = {k for k, v in BESTIARY_NPCS.items() if v["category"] == "cats"}
    check("border templates are cats", "clan_warrior" in border_keys)

    class _Row:
        def __init__(self, **kwargs):
            self._data = kwargs

        def __getitem__(self, key):
            return self._data[key]

        def keys(self):
            return self._data.keys()

    fighter = _Row(npc_name="Clan Warrior", npc_template="clan_warrior")
    check("cat template in bestiary", fighter["npc_template"] in BESTIARY_NPCS)

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
