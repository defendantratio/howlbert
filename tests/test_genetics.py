"""Genetics and redscratch tests; run: python -m tests.test_genetics"""

from __future__ import annotations

from engine.diseases import blocks_conception, mating_contagious_rate
from engine.genetics import (
    encode_genetic_conditions,
    parse_genetic_register_input,
    roll_pup_genetic_conditions,
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


def test_register_genetics() -> None:
    print("\n=== register genetics ===")
    keys, err = parse_genetic_register_input("blind, half_blind, deaf")
    check("parse aliases", err is None and keys == ["blindness", "partial_blindness", "deafness"])
    keys2, err3 = parse_genetic_register_input("missing_leg, no_tail")
    check("limb aliases", err3 is None and keys2 == ["missing_hindleg", "missing_tail"])
    _, err2 = parse_genetic_register_input("conjoined")
    check("conjoined not registerable", err2 is not None)
    check("encode", encode_genetic_conditions(["blindness"]) == '["blindness"]')


def test_redscratch() -> None:
    print("\n=== mating disease spread ===")
    check("redscratch", mating_contagious_rate("redscratch") == 0.45)
    check("influenza respiratory", mating_contagious_rate("influenza") == 0.275)
    cough_rate = mating_contagious_rate("cough")
    check("cough respiratory", abs(cough_rate - 0.077) < 1e-9, repr(cough_rate))
    check("fleas contact", mating_contagious_rate("fleas") == 0.162)
    check("diarrhea filth", mating_contagious_rate("diarrhea") == 0.12)
    check("blocks conception", blocks_conception("redscratch", "active"))


def test_birth_roll() -> None:
    print("\n=== birth mutations ===")
    mother = Row(genetic_conditions='["partial_blindness"]')
    father = Row(genetic_conditions="[]")
    conditions, carriers, lethal = roll_pup_genetic_conditions(mother, father, birth_outcome="success")
    check("returns tuple", isinstance(conditions, list) and isinstance(carriers, list) and isinstance(lethal, bool))
    # one affected parent + one clear parent => pup is a carrier, never affected
    check("recessive from one parent is carrier not expressed",
          "partial_blindness" not in conditions and "partial_blindness" in carriers)
    # kin pairing surfaces recessives and inbreeding depression far more often
    kin_hits = 0
    for _ in range(200):
        c, _cn, _l = roll_pup_genetic_conditions(mother, father, birth_outcome="success", kin=True)
        if "partial_blindness" in c or "inbreeding_depression" in c:
            kin_hits += 1
    check("kin mating expresses defects", kin_hits > 20)


def test_missing_limb_not_herb_curable() -> None:
    print("\n=== missing limb herb guard ===")
    from engine.conditions import treat_with_herb
    from engine.genetics import genetic_keys_matching_cures
    from herbs import HERBS

    user = Row(
        genetic_conditions='["missing_hindleg"]',
        active_injuries="[]",
        disease="",
        condition="healthy",
        hp=10,
    )
    check(
        "bindweed does not match missing limb genetics",
        genetic_keys_matching_cures(user, HERBS["bindweed"]["cures"]) == [],
    )
    check(
        "bindweed treat is not cured_genetic",
        treat_with_herb(user, "bindweed", HERBS["bindweed"]) != "cured_genetic",
    )
    partial = Row(genetic_conditions='["partial_blindness"]', active_injuries="[]", disease="")
    check(
        "celandine still matches partial blindness",
        "partial_blindness"
        in genetic_keys_matching_cures(partial, HERBS["celandine"]["cures"]),
    )


def main() -> None:
    test_register_genetics()
    test_redscratch()
    test_birth_roll()
    test_missing_limb_not_herb_curable()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
