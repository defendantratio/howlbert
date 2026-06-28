"""Field hazard exposure tests; run: python -m tests.test_field_hazards"""

from __future__ import annotations

import database as db
from engine.disease_contract import (
    try_contract_disease,
    try_insect_sting_exposure,
    try_poison_ivy_exposure,
    try_snake_venom_exposure,
)
from engine.diseases import disease_matches_cure, parse_disease
from herbs import HERBS

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
    print("\n=== field hazard diseases ===")
    db.init_db()
    with db.get_db() as conn:
        conn.execute("DELETE FROM users WHERE discord_id = 999400001000000001")
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at, condition, disease
            ) VALUES (999400001000000001, 'Field', NULL, 'subordinate', 'test', 'healthy', '')
            """
        )
    user = db.get_user(999400001000000001)

    note = try_contract_disease(user, "mild_poison", "stung", chance=1.0)
    check("insect sting contracts", note is not None)
    key, stage = parse_disease(db.get_user(999400001000000001)["disease"])
    check("stung stage", key == "mild_poison" and stage == "stung")

    db.set_user_conditions(user["discord_id"], wolf_id=user["id"], disease="")
    user = db.get_user(999400001000000001)
    check(
        "witch hazel listed for mild_poison",
        "mild_poison" in HERBS["witch_hazel"]["cures"],
    )
    check(
        "jewelweed cures poison ivy",
        disease_matches_cure("poison_ivy", "active", HERBS["jewelweed"]["cures"]),
    )

    db.set_user_conditions(user["discord_id"], wolf_id=user["id"], disease="")
    user = db.get_user(999400001000000001)
    ivy = try_poison_ivy_exposure(user, chance=1.0)
    check("poison ivy exposure", ivy is not None)
    key, _ = parse_disease(db.get_user(999400001000000001)["disease"])
    check("ivy disease key", key == "poison_ivy")

    db.set_user_conditions(user["discord_id"], wolf_id=user["id"], disease="")
    user = db.get_user(999400001000000001)
    snake = try_snake_venom_exposure(user, chance=1.0)
    check("snake venom exposure", snake is not None)
    key, stage = parse_disease(db.get_user(999400001000000001)["disease"])
    check("venom stage", key == "mild_poison" and stage == "venom")

    db.set_user_conditions(user["discord_id"], wolf_id=user["id"], disease="")
    user = db.get_user(999400001000000001)
    sting = try_insect_sting_exposure(user, chance=1.0)
    check("insect helper wraps note", sting is not None and "biting insects" in sting)

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
