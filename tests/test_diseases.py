"""Disease spread and contraction tests; run: python -m tests.test_diseases"""

from __future__ import annotations

from unittest.mock import patch

import database as db
from engine.disease_contract import try_contract_disease, try_poop_roll_exposure
from engine.diseases import contagious_rate, disease_matches_cure, encode_disease, parse_disease
from engine.disease_spread import apply_disease_spread_on_rollover
from engine.quarantine import is_quarantined

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


def _make_test_pack(conn, suffix: str) -> int:
    """Isolated den so rollover spread tests don't hit real pack data."""
    name = f"DiseaseTest-{suffix}"
    conn.execute("DELETE FROM packs WHERE name = ?", (name,))
    cur = conn.execute(
        "INSERT INTO packs (name, alpha_id, created_at) VALUES (?, NULL, 'test')",
        (name,),
    )
    return int(cur.lastrowid)


def _cleanup_test_pack(conn, pack_id: int, discord_ids: tuple[int, ...]) -> None:
    for did in discord_ids:
        conn.execute("DELETE FROM users WHERE discord_id = ?", (did,))
    conn.execute("DELETE FROM packs WHERE id = ?", (pack_id,))


def test_parse_and_cures() -> None:
    print("\n=== parse & cures ===")
    check("legacy mild", parse_disease("mild") == ("cough", "mild"))
    check("diarrhea", parse_disease("diarrhea") == ("diarrhea", "active"))
    check("encode cough", encode_disease("cough", "severe") == "severe")
    check("cure cough stage", disease_matches_cure("cough", "mild", ("mild",)))
    check("cure disease key", disease_matches_cure("diarrhea", "active", ("diarrhea",)))
    check("yellowcough parse", parse_disease("yellowcough") == ("yellowcough", "active"))
    check("cure yellowcough", disease_matches_cure("yellowcough", "active", ("yellowcough",)))
    from herbs_compendium import HERBS

    check(
        "lungwort cures yellowcough",
        disease_matches_cure("yellowcough", "active", HERBS["lungwort"]["cures"]),
    )
    check("yellowcough contagious", contagious_rate("yellowcough") == 0.45)
    check("influenza contagious", contagious_rate("influenza") == 0.50)
    check("cough contagious", contagious_rate("cough") == 0.14)
    check("diarrhea not contagious", contagious_rate("diarrhea") == 0.0)
    check("rot_lung parse", parse_disease("rot_lung:fever") == ("rot_lung", "fever"))
    check("rot_lung encode", encode_disease("rot_lung", "wheeze") == "rot_lung:wheeze")
    check("milk_fever parse", parse_disease("milk_fever") == ("milk_fever", "active"))
    check("shaking parse", parse_disease("shaking_sickness:hemorrhage") == ("shaking_sickness", "hemorrhage"))
    check(
        "marsh-mallow cures rot_lung fever",
        disease_matches_cure(
            "rot_lung", "fever", HERBS["marsh_mallow"]["cures"], herb_key="marsh_mallow"
        ),
    )
    check(
        "belly-rip fungus cures necrosis",
        disease_matches_cure(
            "rot_lung",
            "necrosis",
            HERBS["belly_rip_fungus"]["cures"],
            herb_key="belly_rip_fungus",
        ),
    )
    check(
        "marsh-mallow not necrosis",
        not disease_matches_cure(
            "rot_lung", "necrosis", HERBS["marsh_mallow"]["cures"], herb_key="marsh_mallow"
        ),
    )
    check("parsley cures milk_fever", disease_matches_cure("milk_fever", "active", HERBS["parsley"]["cures"]))
    check("rot_lung contagious", contagious_rate("rot_lung") == 0.42)
    check("milk_fever not contagious", contagious_rate("milk_fever") == 0.0)


def test_contract_and_spread() -> None:
    print("\n=== contract & spread ===")
    db.init_db()
    did = 999400001000000001
    pid = 999400002000000002
    with db.get_db() as conn:
        pack_id = _make_test_pack(conn, "spread")
        conn.execute("DELETE FROM users WHERE discord_id IN (?, ?)", (did, pid))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at, condition, disease
            ) VALUES (?, 'Sick', ?, 'subordinate', 'test', 'healthy', 'mild')
            """,
            (did, pack_id),
        )
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at, condition, disease
            ) VALUES (?, 'Well', ?, 'subordinate', 'test', 'healthy', NULL)
            """,
            (pid, pack_id),
        )
        with patch("engine.disease_spread.random.random", return_value=0.0):
            notes = apply_disease_spread_on_rollover(conn)
        row = conn.execute(
            "SELECT disease FROM users WHERE discord_id = ?", (pid,)
        ).fetchone()
        _cleanup_test_pack(conn, pack_id, (did, pid))
    check("spread infects packmate", row["disease"] == "mild", f"got {row['disease']!r}")
    check("spread note logged", len(notes) == 1)

    user = Row(discord_id=did, id=1, condition="healthy", disease=None)
    note = try_contract_disease(user, "diarrhea", chance=1.0)
    check("contract diarrhea", note is not None and "Diarrhea" in note)


def test_quarantine_blocks_spread() -> None:
    print("\n=== quarantine ===")
    db.init_db()
    did = 999400003000000003
    pid = 999400004000000004
    with db.get_db() as conn:
        pack_id = _make_test_pack(conn, "quarantine")
        conn.execute("DELETE FROM users WHERE discord_id IN (?, ?)", (did, pid))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at, condition,
                disease, quarantined
            ) VALUES (?, 'Carrier', ?, 'subordinate', 'test', 'healthy', 'yellowcough', 1)
            """,
            (did, pack_id),
        )
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at, condition, disease
            ) VALUES (?, 'Well', ?, 'subordinate', 'test', 'healthy', NULL)
            """,
            (pid, pack_id),
        )
        with patch("engine.disease_spread.random.random", return_value=0.0):
            notes = apply_disease_spread_on_rollover(conn)
        row = conn.execute(
            "SELECT disease FROM users WHERE discord_id = ?", (pid,)
        ).fetchone()
        _cleanup_test_pack(conn, pack_id, (did, pid))
    check(
        "quarantined carrier skips spread",
        row["disease"] is None and len(notes) == 0,
        f"disease={row['disease']!r} notes={len(notes)}",
    )
    carrier = Row(discord_id=did, id=1, condition="healthy", disease="yellowcough", quarantined=1)
    check("is_quarantined", is_quarantined(carrier))


def test_exposure_vectors() -> None:
    print("\n=== exposure vectors ===")
    user = Row(
        id=1,
        discord_id=999001,
        condition="healthy",
        disease=None,
        age_months=6,
    )
    with patch("engine.disease_contract.random.random", return_value=0.0):
        with patch("engine.disease_contract.db.set_user_conditions"):
            rot = __import__("engine.disease_contract", fromlist=["try_rotting_meat_exposure"]).try_rotting_meat_exposure(user)
    check("rotting meat favors gut", rot and "Rotting meat" in rot)
    with patch("engine.disease_contract.random.random", return_value=0.15):
        with patch("engine.disease_contract.db.set_user_conditions"):
            from engine.disease_contract import try_carrion_exposure

            car = try_carrion_exposure(user)
    check("carrion can seed distemper", car and "Distemper" in car)
    with patch("engine.disease_contract.random.random", side_effect=[0.50, 0.10]):
        with patch("engine.disease_contract.db.set_user_conditions"):
            from engine.disease_contract import try_rotting_meat_exposure

            mold = try_rotting_meat_exposure(user)
    check("rotting meat mold green-cough", mold and "Green-cough" in mold)


def test_rabies_herb_no_cure() -> None:
    print("\n=== rabies herb prophylaxis ===")
    from engine.conditions import treat_with_herb
    from herbs_compendium import HERBS
    from engine.herb_treatment import apply_flavor_herb

    rabies_user = Row(discord_id=1, id=1, disease="rabies:incubation", active_injuries="[]")
    check(
        "rabies not in goldenrod cures",
        "rabies" not in HERBS["goldenrod"]["cures"],
    )
    check(
        "goldenrod does not cure rabies",
        treat_with_herb(rabies_user, "goldenrod", HERBS["goldenrod"]) != "cured_disease",
    )
    flavor = apply_flavor_herb("goldenrod", rabies_user)
    check(
        "goldenrod rabies prophylaxis buff",
        flavor
        and flavor.get("kind") == "disease_save_buff"
        and flavor.get("fields", {}).get("disease_save_buff") == 1,
    )
    boneset_flavor = apply_flavor_herb("boneset", Row(disease="rabies:prodrome"))
    check(
        "boneset rabies prophylaxis buff",
        boneset_flavor and boneset_flavor.get("kind") == "disease_save_buff",
    )
    check(
        "rabies frenzy no herb cure",
        not disease_matches_cure(
            "rabies", "frenzy", HERBS["goldenrod"]["cures"], herb_key="goldenrod"
        ),
    )


def main() -> None:
    test_parse_and_cures()
    test_contract_and_spread()
    test_quarantine_blocks_spread()
    test_exposure_vectors()
    test_rabies_herb_no_cure()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
