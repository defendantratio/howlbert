"""Audit herb mechanical coverage; run: python tools/audit_herb_mechanics.py"""

from __future__ import annotations

from engine.conditions import herb_special_effect, treat_with_herb
from engine.herb_mechanics import (
    SPECIAL_MECHANICS,
    STATIC_HINTS,
    _probe_supplemental_message,
    build_usage_hint,
)
from herbs import HERBS


def probe_user(**kw):
    base = {
        "disease": "",
        "exhaustion": 0,
        "mood": 50,
        "hp": 10,
        "max_hp": 10,
        "herb_buffs": "{}",
        "last_rest_day": 5,
        "active_injuries": "[]",
        "condition": "healthy",
        "genetic_conditions": "[]",
        "skill_proficiencies": "[]",
        "attr_wis": 3,
        "hunger": 50,
        "thirst": 50,
        "age_months": 24,
    }
    base.update(kw)
    return base


PROBES = (
    probe_user(),
    probe_user(active_injuries='["sprained_leg"]'),
    probe_user(active_injuries='["punctured_paw"]'),
    probe_user(active_injuries='["deep_gash"]'),
    probe_user(active_injuries='["infected_wound"]'),
    probe_user(condition="dying", hp=0),
    probe_user(disease="anxiety:uneasy"),
    probe_user(disease="mild"),
    probe_user(disease="cough:severe"),
    probe_user(genetic_conditions='["partial_blindness"]'),
)


def main() -> None:
    weak: list[tuple[str, str]] = []
    for key in sorted(HERBS):
        meta = HERBS[key]
        hint = build_usage_hint(key, meta)
        has_supp = _probe_supplemental_message(key) is not None
        has_static = key in STATIC_HINTS
        special = herb_special_effect(key, probe_user())
        has_special = special in SPECIAL_MECHANICS
        has_cures = bool(meta.get("cures"))
        treat_ok = any(
            treat_with_herb(p, key, meta) not in (None, "no_effect", "failed")
            for p in PROBES
        )
        if not (has_supp or has_static or has_special or has_cures or treat_ok):
            weak.append((key, hint[:120]))
        elif "Use via `/medic action:treat`" in hint and not has_supp and not has_static:
            weak.append((key, f"generic: {hint[:100]}"))

    print(f"Total herbs: {len(HERBS)}")
    print(f"Weak or generic: {len(weak)}")
    for key, hint in weak:
        print(f"  {key}: {hint}")


if __name__ == "__main__":
    main()
