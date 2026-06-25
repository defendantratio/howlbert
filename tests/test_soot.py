"""Soot character sheet: traits, lore, and medic register defaults."""

from __future__ import annotations

import json

from engine.aging import proficiencies_for_role
from engine.character_lore import parse_character_lore
from engine.character_lore_data import CHARACTER_LORE_BY_NAME
from engine.character_traits import (
    SOOT_CHARACTER_TRAITS,
    canonical_register_defaults_for_name,
    canonical_traits_for_name,
    encode_character_traits,
    trait_check_adjustments,
)

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


def _soot_row(**kwargs):
    base = {
        "exhaustion": 0,
        "active_injuries": "[]",
        "genetic_conditions": "[]",
        "disease": None,
        "great_pack": "mistmoor",
        "character_traits": encode_character_traits(SOOT_CHARACTER_TRAITS),
        "attr_str": 2,
        "attr_dex": 3,
        "attr_con": 4,
        "attr_int": 4,
        "attr_cha": 3,
        "attr_wis": 5,
        "skill_proficiencies": '["herblore", "medicine", "tracking", "stealth"]',
    }
    base.update(kwargs)
    return base


def test_canonical_name() -> None:
    print("\n=== canonical name ===")
    check("Soot traits", canonical_traits_for_name("Soot") is SOOT_CHARACTER_TRAITS)
    check("case insensitive", canonical_traits_for_name("soot") is SOOT_CHARACTER_TRAITS)


def test_trait_modifiers() -> None:
    print("\n=== trait modifiers ===")
    user = _soot_row()
    herblore_mod, herblore_names = trait_check_adjustments(
        user, ("attr_int",), skill_key="herblore"
    )
    check("herblore +4", herblore_mod == 4 and "Herblore" in herblore_names)

    perception_mod, perception_names = trait_check_adjustments(
        user, ("attr_wis",), skill_key="tracking"
    )
    check(
        "perception net +1",
        perception_mod == 1
        and "Perception" in perception_names
        and "Overly Attached to Mirewort" in perception_names,
    )

    stealth_mod, stealth_names = trait_check_adjustments(
        user, ("attr_dex",), skill_key="stealth"
    )
    check("stealth +3 no clumsy", stealth_mod == 3 and "Stealth" in stealth_names)
    check("clumsy excluded on stealth", "Clumsy" not in stealth_names)

    dex_mod, dex_names = trait_check_adjustments(user, ("attr_dex",), skill_key="crime")
    check("dex clumsy and stealth cancel", dex_mod == 0)
    check("clumsy on dex", "Clumsy" in dex_names)


def test_register_defaults_medic() -> None:
    print("\n=== register defaults ===")
    defaults = canonical_register_defaults_for_name("Soot")
    check("defaults exist", defaults is not None)
    check("medic role", defaults and defaults.get("wolf_role") == "medic")
    check("orthodox belief", defaults and defaults.get("maw_belief") == "orthodox")
    profs = json.loads(proficiencies_for_role("medic"))
    check("medic proficiencies", "herblore" in profs and "medicine" in profs)


def test_lore_sheet() -> None:
    print("\n=== lore sheet ===")
    raw = CHARACTER_LORE_BY_NAME.get("Soot")
    check("lore on file", raw is not None)
    lore = parse_character_lore(raw)
    check("rot-lung backstory", lore and "rot-lung" in lore["backstory"].lower())
    check("Mirewort mentor", lore and "Mirewort" in lore["family_ties"])
    check("second sight", lore and "second sight" in lore["backstory"].lower())


def main() -> None:
    test_canonical_name()
    test_trait_modifiers()
    test_register_defaults_medic()
    test_lore_sheet()
    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
