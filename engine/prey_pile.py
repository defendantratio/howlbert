"""Prey pile labels and choice outcomes."""

from config import CURRENCY_LABEL

PREY_LABEL_HARE = "a hare"
PREY_LABEL_FISH = "a fish"

PREY_CHOICES = {
    "eat": {
        "label": "Eat your fill",
        "emoji": "🍖",
        "description": "Take a portion; restores energy (−1 exhaustion, +HP).",
    },
    "share": {
        "label": "Share fairly",
        "emoji": "🤝",
        "description": "Split the kill with packmates.",
    },
    "den": {
        "label": "Leave for the den",
        "emoji": "🏠",
        "description": "Donate your share to pack treasury.",
    },
    "guard": {
        "label": "Guard the pile",
        "emoji": "🛡️",
        "description": "Watch for scavengers and rivals.",
    },
    "pass": {
        "label": "Walk away",
        "emoji": "👃",
        "description": "Leave the feast to others.",
    },
}


def prey_label_from_yield(yield_bones: int) -> str:
    if yield_bones <= 0:
        return "empty scraps"
    if yield_bones <= 15:
        return PREY_LABEL_HARE
    if yield_bones <= 35:
        return "a solid kill"
    if yield_bones <= 60:
        return "a heavy haul"
    return "a legendary feast"


def resolve_prey_label(user) -> str:
    """Use an explicit fresh-kill label (hare, fish) or infer from bone yield."""
    if user and "last_prey_label" in user.keys() and user["last_prey_label"]:
        return user["last_prey_label"]
    yield_bones = int(user["last_hunt_yield"]) if user else 0
    return prey_label_from_yield(yield_bones)


def choice_outcome_message(
    choice: str,
    *,
    bones: int = 0,
    standing: int = 0,
    treasury: int = 0,
    hp_gain: int = 0,
    exhaustion_delta: int = 0,
) -> str:
    base = PREY_CHOICES[choice]
    parts = [f"**{base['emoji']} {base['label']}**; {base['description']}"]
    if bones > 0:
        parts.append(f"+{bones} {CURRENCY_LABEL}")
    if hp_gain > 0:
        parts.append(f"+{hp_gain} HP")
    if exhaustion_delta < 0:
        parts.append(f"{exhaustion_delta} exhaustion (energy restored)")
    elif choice == "eat":
        parts.append("Belly full; no exhaustion to shed.")
    if standing > 0:
        parts.append(f"+{standing} standing")
    if treasury > 0:
        parts.append(f"+{treasury} bones to pack treasury")
    if choice == "pass":
        parts.append("You slip away without touching the pile.")
    if choice == "guard":
        parts.append("Your vigil earns respect at the den.")
    return "\n".join(parts)


def apply_prey_choice(choice: str, prey_bones: int) -> dict:
    """Return effect dict: bones, standing, treasury_bones, quest_objective."""
    if choice == "eat":
        return {
            "bones": max(3, prey_bones // 4),
            "standing": 0,
            "treasury_bones": 0,
            "restore_energy": True,
        }
    if choice == "share":
        return {"bones": max(2, prey_bones // 8), "standing": 2, "treasury_bones": 0}
    if choice == "den":
        return {"bones": 0, "standing": 1, "treasury_bones": max(5, prey_bones // 5)}
    if choice == "guard":
        return {
            "bones": 0,
            "standing": 1,
            "treasury_bones": 0,
            "quest_objective": "patrol",
        }
    return {"bones": 0, "standing": 0, "treasury_bones": 0}


def format_response_summary(rows) -> str:
    if not rows:
        return "_No wolves have responded yet._"
    lines = []
    for row in rows:
        info = PREY_CHOICES.get(row["choice"], {"label": row["choice"], "emoji": "•"})
        lines.append(f"{info['emoji']} {info['label']}: **{row['count']}**")
    return "\n".join(lines)
