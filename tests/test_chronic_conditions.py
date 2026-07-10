"""Chronic illness, paralysis, and mental degeneration; run: python -m tests.test_chronic_conditions"""

from __future__ import annotations

from engine.combat_injuries import resolve_player_injury_key
from engine.conditions import treat_with_herb
from engine.diseases import (
    HERB_CURE_STAGES,
    blocks_field,
    disease_matches_cure,
    encode_disease,
    parse_disease,
)
from engine.injury_effects import has_paralysis, hunt_blocked_by_injury
from engine.mental_effects import field_activity_block, mental_activity_block, social_activity_block
from herbs_compendium import HERBS

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


def main() -> None:
    print("\n=== parse chronic diseases ===")
    check("rabies parse", parse_disease("rabies:prodrome") == ("rabies", "prodrome"))
    check("cancer parse", parse_disease("cancer:lump") == ("cancer", "lump"))
    check("dementia parse", parse_disease("dementia:confused") == ("dementia", "confused"))
    check("feral encode", encode_disease("feral_shift", "feral") == "feral_shift:feral")

    print("\n=== herb cure stages ===")
    check(
        "rabies frenzy no herb",
        not disease_matches_cure(
            "rabies", "frenzy", HERBS["goldenrod"]["cures"], herb_key="goldenrod"
        ),
    )
    check(
        "rabies incubation no herb cure",
        not disease_matches_cure(
            "rabies", "incubation", HERBS["goldenrod"]["cures"], herb_key="goldenrod"
        ),
    )
    check("rabies not in herb stages", "rabies" not in HERB_CURE_STAGES)
    check(
        "rabies incubation goldenrod ease",
        treat_with_herb(Row(disease="rabies:incubation"), "goldenrod", HERBS["goldenrod"])
        == "rabies_ease",
    )
    check(
        "rabies prodrome boneset ease",
        treat_with_herb(Row(disease="rabies:prodrome"), "boneset", HERBS["boneset"]) == "rabies_ease",
    )
    check("cancer terminal blocked", "terminal" not in HERB_CURE_STAGES["cancer"])

    print("\n=== paralysis ===")
    paralyzed = Row(active_injuries='["paralyzed"]')
    spinal = Row(active_injuries='["spinal_injury"]')
    check("paralyzed blocks", hunt_blocked_by_injury(paralyzed) is not None)
    check("spinal injury no longer hard-blocks (penalty instead)", hunt_blocked_by_injury(spinal) is None)
    check("has_paralysis", has_paralysis(spinal))

    print("\n=== spine bite injury ===")
    inj = resolve_player_injury_key(
        maneuver_key="spine_bite",
        crit=True,
        hit=True,
        new_hp=5,
        max_hp=20,
    )
    check("spine crit injury", inj in ("spinal_injury", "paralyzed"))

    print("\n=== mental degeneration ===")
    lost = Row(disease="dementia:lost")
    feral_end = Row(disease="feral_shift:unsentient")
    check("dementia social block", social_activity_block(lost) is not None)
    check("feral no mental block", mental_activity_block(feral_end) is None)
    check("feral field block", field_activity_block(feral_end) is not None)
    check("blocks_field unsentient", blocks_field("feral_shift", "unsentient"))
    check("feral social block", social_activity_block(feral_end) is not None)
    field_msg = field_activity_block(feral_end)
    check(
        "unsentient message allows vitals",
        field_msg and "/eat" in field_msg,
    )

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
