"""NPC display name tests; run: python -m tests.test_combat_names"""

from __future__ import annotations

import database as db

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

    # Inline numbering logic to avoid discord import in combat_display.
    def assign(enc_id: int, template_key: str, base_name: str) -> str:
        fighters = db.get_combat_fighters(enc_id)
        same = sorted(
            (f for f in fighters if f["npc_template"] == template_key),
            key=lambda f: f["id"],
        )
        n = len(same) + 1
        if n == 1:
            return base_name
        for i, fighter in enumerate(same, 1):
            label = f"{base_name} {i}"
            if fighter["npc_name"] != label:
                db.update_fighter_npc_name(fighter["id"], label)
        return f"{base_name} {n}"

    enc_id = db.create_encounter(1, 999001, 1)

    first = assign(enc_id, "kittypet", "Kittypet")
    check("first keeps plain name", first == "Kittypet", first)
    db.add_combat_fighter(enc_id, npc_name=first, npc_template="kittypet", hp=10, max_hp=10)

    second = assign(enc_id, "kittypet", "Kittypet")
    check("second numbered", second == "Kittypet 2", second)
    fighters = db.get_combat_fighters(enc_id)
    check("first renamed", fighters[0]["npc_name"] == "Kittypet 1", fighters[0]["npc_name"])

    db.add_combat_fighter(enc_id, npc_name=second, npc_template="kittypet", hp=10, max_hp=10)
    third = assign(enc_id, "kittypet", "Kittypet")
    check("third numbered", third == "Kittypet 3", third)
    db.add_combat_fighter(enc_id, npc_name=third, npc_template="kittypet", hp=10, max_hp=10)
    fighters = db.get_combat_fighters(enc_id)
    names = [f["npc_name"] for f in fighters if f["npc_template"] == "kittypet"]
    check("three numbered names", names == ["Kittypet 1", "Kittypet 2", "Kittypet 3"], str(names))

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
