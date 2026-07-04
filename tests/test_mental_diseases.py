"""Mental illness and herb cure tests; run: python -m tests.test_mental_diseases"""

from __future__ import annotations

from engine.conditions import treat_with_herb
from engine.diseases import (
    HERB_CURE_STAGES,
    MENTAL_DISEASES,
    blocks_social,
    disease_matches_cure,
    encode_disease,
    is_mental_disease,
    parse_disease,
)
from engine.herb_buffs import DISEASE_DOSE_HERBS, apply_disease_dose, apply_supplemental_herb
from engine.mental_effects import mental_check_adjustments, social_activity_block
from herbs import HERBS

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


def test_parse_and_flags() -> None:
    print("\n=== parse & flags ===")
    check("insomnia parse", parse_disease("insomnia:restless") == ("insomnia", "restless"))
    check("anxiety encode", encode_disease("anxiety", "panic_prone") == "anxiety:panic_prone")
    check("mental set size", len(MENTAL_DISEASES) >= 10, str(len(MENTAL_DISEASES)))
    check("insomnia mental", is_mental_disease("insomnia"))
    check("shock mental", is_mental_disease("shock_emotional"))
    check("cough not mental", not is_mental_disease("cough"))
    check("panic no longer blocks social", not blocks_social("anxiety", "panic_prone"))


def test_herb_cures() -> None:
    print("\n=== herb cures ===")
    check(
        "chamomile anxiety anxious",
        disease_matches_cure(
            "anxiety", "anxious", HERBS["chamomile"]["cures"], herb_key="chamomile"
        ),
    )
    check(
        "chamomile dose blocks uneasy instant",
        not disease_matches_cure(
            "anxiety", "uneasy", HERBS["chamomile"]["cures"], herb_key="chamomile"
        ),
    )
    check(
        "valerian dose blocks instant sleepless",
        not disease_matches_cure(
            "insomnia", "sleepless", HERBS["valerian"]["cures"], herb_key="valerian"
        ),
    )
    check(
        "poppy clears exhaustion cascade",
        disease_matches_cure(
            "insomnia",
            "exhaustion_cascade",
            HERBS["poppy_seeds"]["cures"],
            herb_key="poppy_seeds",
        ),
    )
    check(
        "passionflower night terrors",
        disease_matches_cure(
            "night_terrors",
            "restless_nights",
            HERBS["passionflower"]["cures"],
            herb_key="passionflower",
        ),
    )
    check("insomnia cure stages", "exhaustion_cascade" not in HERB_CURE_STAGES["insomnia"])


def test_dose_and_supplemental() -> None:
    print("\n=== doses & buffs ===")
    user = Row(
        disease="insomnia:sleepless",
        herb_buffs="{}",
        discord_id=1,
        id=1,
        mood=50,
        last_rest_day=3,
        active_injuries="[]",
        condition="healthy",
        hp=10,
    )
    cured, fields, msg = apply_disease_dose(user, "valerian", day=3)
    check("valerian dose 1 not cured", not cured and "1/2" in msg)
    user2 = Row(
        disease=user["disease"],
        herb_buffs=fields.get("herb_buffs", "{}"),
        discord_id=1,
        id=1,
        mood=50,
        last_rest_day=3,
        active_injuries="[]",
        condition="healthy",
        hp=10,
    )
    cured2, _, msg2 = apply_disease_dose(user2, "valerian", day=3)
    check("valerian dose 2 cured", cured2 and "2/2" in msg2)

    anxious = Row(
        disease="anxiety:uneasy",
        herb_buffs="{}",
        mood=40,
        last_rest_day=1,
        active_injuries="[]",
        condition="healthy",
        hp=10,
    )
    sup = apply_supplemental_herb("chamomile", anxious, day=1, outcome="symptom_ease")
    check("chamomile calm buff", sup and "Calm" in sup["message"])

    user3 = Row(disease="anxiety:anxious", last_rest_day=1)
    _, dis = mental_check_adjustments(user3, ("attr_wis", "attr_cha"))
    check("anxiety check disadv", dis)
    user4 = Row(disease="anxiety:panic_prone", last_rest_day=1)
    check("panic social block", social_activity_block(user4) is not None)


def test_treat_paths() -> None:
    print("\n=== treat paths ===")
    user = Row(disease="anxiety:uneasy", active_injuries="[]", hp=10, condition="healthy")
    outcome = treat_with_herb(user, "chamomile", HERBS["chamomile"])
    check("chamomile dose path", outcome == "cough_dose")
    user2 = Row(disease="insomnia:restless", active_injuries="[]", hp=10, condition="healthy")
    outcome2 = treat_with_herb(user2, "lavender", HERBS["lavender"])
    check("lavender cures restless", outcome2 == "cured_disease")
    check("dose herbs registered", "valerian" in DISEASE_DOSE_HERBS)


def main() -> None:
    test_parse_and_flags()
    test_herb_cures()
    test_dose_and_supplemental()
    test_treat_paths()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
