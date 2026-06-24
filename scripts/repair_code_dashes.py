"""Restore arithmetic minus signs corrupted by fix_user_dashes offset drift."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Order matters: longer / more specific patterns first.
REPAIRS: list[tuple[str, str]] = [
    ("(datetime.now(timezone.utc); created)", "(datetime.now(timezone.utc) - created)"),
    ("PREY_ROTTEN_GRACE_DAYS; (age; rot_days)", "PREY_ROTTEN_GRACE_DAYS - (age - rot_days)"),
    ("int(pact[\"expires_day\"]); int(", "int(pact[\"expires_day\"]) - int("),
    ("max(0, int(pact[\"expires_day\"]); int(", "max(0, int(pact[\"expires_day\"]) - int("),
    ("max(0, current_day; acquired_day)", "max(0, current_day - acquired_day)"),
    ("max(0, day_number; row", "max(0, day_number - row"),
    ("max(0, day; last)", "max(0, day - last)"),
    ("max(0, day; subject", "max(0, day - subject"),
    ("max(0, int(user[\"hp\"]); dmg)", "max(0, int(user[\"hp\"]) - dmg)"),
    ("max(0, int(fresh[\"hp\"]); dmg)", "max(0, int(fresh[\"hp\"]) - dmg)"),
    ("max(0, int(attacker[\"hp\"]); dmg)", "max(0, int(attacker[\"hp\"]) - dmg)"),
    ("return amount; tax, tax", "return amount - tax, tax"),
    ("return ready_at; now", "return ready_at - now"),
    ("day; GESTATION_DAYS)", "day - GESTATION_DAYS)"),
    ("after; before ==", "after - before =="),
    ("max(0, old; amount)", "max(0, old - amount)"),
    ("max(0, DONOR_MONTHLY_BONE_CAP; used)", "max(0, DONOR_MONTHLY_BONE_CAP - used)"),
    ("max(0, HUNTER_HUNTS_PER_SUNRISE; hunts_used_today", "max(0, HUNTER_HUNTS_PER_SUNRISE - hunts_used_today"),
    ("max(0, SCOUT_RESCOUTS_PER_DAY; rescout_uses_today", "max(0, SCOUT_RESCOUTS_PER_DAY - rescout_uses_today)"),
    ("max(1, heal_days; bone_heal_days_reduction", "max(1, heal_days - bone_heal_days_reduction"),
    ("max(0, rot_days; age)", "max(0, rot_days - age)"),
    ("max(0, int(cooldown_minutes; elapsed", "max(0, int(cooldown_minutes - elapsed"),
    ("min(max_hp; hp,", "min(max_hp - hp,"),
    ("min(new_max, old_hp + (new_max; old_max))", "min(new_max, old_hp + (new_max - old_max))"),
    ("_to_julian_day(dt); KNOWN_NEW_MOON_JD", "_to_julian_day(dt) - KNOWN_NEW_MOON_JD"),
    ("abs(a; b)", "abs(a - b)"),
    ("elapsed = day; start", "elapsed = day - start"),
    ("grace = HALF_MOON_DAYS; day", "grace = HALF_MOON_DAYS - day"),
    ("left = HALF_MOON_DAYS; elapsed", "left = HALF_MOON_DAYS - elapsed"),
    ("remaining = GESTATION_DAYS; elapsed", "remaining = GESTATION_DAYS - elapsed"),
    ("remaining = max(0, GESTATION_DAYS; elapsed)", "remaining = max(0, GESTATION_DAYS - elapsed)"),
    ("{GESTATION_DAYS; elapsed}", "{GESTATION_DAYS - elapsed}"),
    ("{old_exhaustion; new_exhaustion}", "{old_exhaustion - new_exhaustion}"),
    ("{rest_until; day}", "{rest_until - day}"),
    ("{cooled; day}", "{cooled - day}"),
    ("day; stack[\"acquired_day\"]", "day - stack[\"acquired_day\"]"),
    ("day; int(stack[\"acquired_day\"])", "day - int(stack[\"acquired_day\"])"),
    ("day; subject[\"pregnancy_start_day\"]", "day - subject[\"pregnancy_start_day\"]"),
    ("if day; int(row[\"join_day\"])", "if day - int(row[\"join_day\"])"),
    ("if last and day; last <", "if last and day - last <"),
    ("int(pup[\"exhaustion\"]); HONEY_PUP_EXHAUSTION_RELIEF", "int(pup[\"exhaustion\"]) - HONEY_PUP_EXHAUSTION_RELIEF"),
    ("if mother_hunger; total_cost", "if mother_hunger - total_cost"),
    ("_clamp_hunger(mother_hunger; total_cost)", "_clamp_hunger(mother_hunger - total_cost)"),
    ("int(row[\"hunger\"]); PUP_UNFED_EXTRA_DECAY", "int(row[\"hunger\"]) - PUP_UNFED_EXTRA_DECAY"),
    ("(datetime.now(timezone.utc); then)", "(datetime.now(timezone.utc) - then)"),
    ("age = max(0, current_day; acquired_day)", "age = max(0, current_day - acquired_day)"),
    ("age = current_day; int(stack[\"acquired_day\"])", "age = current_day - int(stack[\"acquired_day\"])"),
    ("exhaustion_delta = new_exhaustion; int(wolf[\"exhaustion\"])", "exhaustion_delta = new_exhaustion - int(wolf[\"exhaustion\"])"),
    ("left = rest_until; day", "left = rest_until - day"),
    ("and day; int(stack[\"acquired_day\"]) >= 1", "and day - int(stack[\"acquired_day\"]) >= 1"),
    ("base[: max_len; len(suffix)]", "base[: max_len - len(suffix)]"),
]

def repair_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in REPAIRS:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return original.count("; ") - text.count("; ")  # rough signal
    return 0


def main() -> int:
    paths = list((ROOT / "engine").rglob("*.py"))
    paths += list((ROOT / "cogs").rglob("*.py"))
    paths += list((ROOT / "utils").rglob("*.py"))
    paths += [ROOT / "database.py", ROOT / "herbs.py"]
    changed = 0
    for path in paths:
        if ".venv" in path.parts:
            continue
        if repair_file(path):
            changed += 1
            print(path.relative_to(ROOT))
    print(f"Repaired {changed} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
