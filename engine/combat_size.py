"""Size classes for pin / scruff maneuver eligibility."""

from __future__ import annotations

SIZE_RANK = {
    "small": 1,
    "medium": 2,
    "large": 3,
}

WOLF_DEFAULT_SIZE = "medium"

SIZE_LABELS = {
    "small": "small",
    "medium": "medium",
    "large": "large",
}

VALID_SIZE_CLASSES = frozenset(SIZE_RANK)

SIZE_BY_TEMPLATE: dict[str, str] = {
    "coyote": "small",
    "cougar": "large",
    "black_bear": "large",
    "grizzly_bear": "large",
    "wolverine": "small",
    "large_prey": "large",
    "fox": "small",
    "badger": "small",
    "water_snake": "small",
    "garter_snake": "small",
    "skink": "small",
    "spider": "small",
}

CATEGORY_DEFAULT_SIZE: dict[str, str] = {
    "cats": "small",
    "dogs": "medium",
    "predators": "medium",
    "reptiles": "small",
}


def size_class_for_template(template_key: str | None, category: str | None = None) -> str:
    if template_key and template_key in SIZE_BY_TEMPLATE:
        return SIZE_BY_TEMPLATE[template_key]
    if category and category in CATEGORY_DEFAULT_SIZE:
        return CATEGORY_DEFAULT_SIZE[category]
    return WOLF_DEFAULT_SIZE


def _explicit_size_class(user) -> str | None:
    raw = ""
    if hasattr(user, "keys"):
        if "size_class" in user.keys() and user["size_class"]:
            raw = str(user["size_class"]).strip().lower()
    elif isinstance(user, dict):
        raw = str(user.get("size_class") or "").strip().lower()
    if raw in VALID_SIZE_CLASSES:
        return raw
    return None


def size_class_for_wolf(user) -> str:
    explicit = _explicit_size_class(user)
    if explicit:
        return explicit
    role = ""
    if hasattr(user, "keys"):
        role = user["wolf_role"] if "wolf_role" in user.keys() else ""
    elif isinstance(user, dict):
        role = user.get("wolf_role", "")
    if role in ("pup", "juvenile"):
        return "small"
    return WOLF_DEFAULT_SIZE


def format_size_class_profile(user) -> str:
    """profile line for combat build size."""
    explicit = _explicit_size_class(user)
    effective = size_class_for_wolf(user)
    label = SIZE_LABELS.get(effective, effective.title())
    if explicit:
        return f"**{label}** _(custom · `/wolfset field:size`)_"
    role = user["wolf_role"] if hasattr(user, "keys") and "wolf_role" in user.keys() else user.get("wolf_role", "") if isinstance(user, dict) else ""
    if role in ("pup", "juvenile"):
        return f"**{label}** _(auto · young wolf)_"
    return f"**{label}** _(auto · adults default medium)_"


def size_class_from_stats(stats) -> str:
    if not stats:
        return WOLF_DEFAULT_SIZE
    if hasattr(stats, "keys"):
        if "size_class" in stats.keys() and stats["size_class"]:
            return str(stats["size_class"])
        template = stats["npc_template"] if "npc_template" in stats.keys() else None
        if template:
            from engine.bestiary import BESTIARY_NPCS

            t = BESTIARY_NPCS.get(template)
            if t:
                return size_class_for_template(template, t.get("category"))
        if "wolf_role" in stats.keys() or (
            "wolf_name" in stats.keys() and not template
        ):
            return size_class_for_wolf(stats)
    elif isinstance(stats, dict):
        if stats.get("size_class"):
            return str(stats["size_class"])
        template = stats.get("npc_template")
        if template:
            from engine.bestiary import BESTIARY_NPCS

            t = BESTIARY_NPCS.get(template)
            if t:
                return size_class_for_template(template, t.get("category"))
        if stats.get("wolf_role") or (stats.get("wolf_name") and not template):
            return size_class_for_wolf(stats)
    return WOLF_DEFAULT_SIZE


def size_rank(stats) -> int:
    return SIZE_RANK.get(size_class_from_stats(stats), SIZE_RANK[WOLF_DEFAULT_SIZE])


def can_pin_target(attacker_stats, defender_stats) -> bool:
    return size_rank(attacker_stats) >= size_rank(defender_stats)


def can_scruff_target(attacker_stats, defender_stats) -> bool:
    return size_rank(attacker_stats) > size_rank(defender_stats)
