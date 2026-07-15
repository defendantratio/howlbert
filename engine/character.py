import json

from rpg_rules import ATTRIBUTE_MODIFIERS, ROLE_DEFAULT_STATS


def attr_modifier(score: int) -> int:
    score = max(1, min(10, score))
    return ATTRIBUTE_MODIFIERS.get(score, 0)


def compute_max_hp(attr_str: int, attr_con: int) -> int:
    """hp = 10 + 2 × survival (constitution score). vitality is constitution, not
    muscle; strength drives bite damage and hunting, not how much punishment a wolf
    can take. (attr_str is kept in the signature for callers but no longer used.)"""
    survival = max(1, min(10, int(attr_con)))
    return max(1, 10 + 2 * survival)


def format_max_hp_breakdown(attr_str: int, attr_con: int, *, max_hp: int | None = None) -> str:
    survival = max(1, min(10, int(attr_con)))
    total = max_hp if max_hp is not None else compute_max_hp(attr_str, survival)
    return f"10 + {survival}(survival) × 2 = {total}"


def legacy_modifier_max_hp(attr_str: int, attr_con: int) -> int:
    """Old HP rule; used once to fix wolves left hurt after the formula change."""
    return max(1, 10 + attr_modifier(attr_str) + attr_modifier(attr_con))


def hp_after_max_change(old_hp: int, old_max: int, new_max: int) -> int:
    """When max HP changes, shift current HP by the same delta (clamped)."""
    new_max = max(1, int(new_max))
    old_hp = max(0, int(old_hp))
    old_max = max(1, int(old_max))
    if new_max == old_max:
        return min(old_hp, new_max)
    return max(0, min(new_max, old_hp + (new_max - old_max)))


def reconcile_hp(old_hp: int, old_max: int, attr_str: int, attr_con: int) -> tuple[int, int]:
    """Return (hp, max_hp) after recalculating max from attributes."""
    new_max = compute_max_hp(attr_str, attr_con)
    old_hp = max(0, int(old_hp))
    old_max = max(1, int(old_max))
    legacy_max = legacy_modifier_max_hp(attr_str, attr_con)

    if old_hp == legacy_max and new_max > legacy_max:
        return new_max, new_max
    if new_max > old_max and old_hp >= old_max:
        return new_max, new_max
    return hp_after_max_change(old_hp, old_max, new_max), new_max




def best_modifier(user, attr_keys: tuple[str, ...]) -> tuple[int, str]:
    best_key = attr_keys[0]
    best_val = user[best_key]
    for key in attr_keys[1:]:
        if user[key] > best_val:
            best_key, best_val = key, user[key]
    label = best_key.replace("attr_", "").upper()[:3]
    return attr_modifier(best_val), label


def parse_proficiencies(raw: str | None) -> set[str]:
    if not raw:
        return set()
    try:
        data = json.loads(raw)
        return set(data) if isinstance(data, list) else set()
    except json.JSONDecodeError:
        return {s.strip().lower() for s in raw.split(",") if s.strip()}


def parse_skill_ranks(raw: str | None) -> dict[str, int]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {}
        return {str(k).lower(): max(0, int(v)) for k, v in data.items()}
    except (json.JSONDecodeError, TypeError, ValueError):
        return {}




def is_skill_proficient(user, skill_key: str) -> bool:
    from rpg_rules import ROLE_PROFICIENCIES

    if skill_key in parse_proficiencies(user["skill_proficiencies"] if "skill_proficiencies" in user.keys() else None):
        return True
    role = user["wolf_role"] if "wolf_role" in user.keys() else ""
    return skill_key in ROLE_PROFICIENCIES.get(role, ())






def default_stats_for_role(role: str) -> dict:
    return dict(ROLE_DEFAULT_STATS.get(role, ROLE_DEFAULT_STATS["hunter"]))


def get_attr(user, short: str) -> int:
    """read an attribute (str, dex, con, int, cha, wis) from a user row."""
    key = f"attr_{short}"
    if key in user.keys() and user[key] is not None:
        return int(user[key])
    legacy = {
        "str": "strength",
        "dex": "speed",
        "con": "stamina",
        "wis": "scent",
    }
    if short in legacy and legacy[short] in user.keys():
        legacy_val = int(user[legacy[short]])
        return max(1, min(10, 5 + (legacy_val - 10) // 2))
    return 5
