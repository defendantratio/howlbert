"""Playability rules for young wolf roles (pup, juvenile)."""

from rpg_rules import ROLE_LABELS

YOUNG_ROLES = frozenset({"pup", "juvenile"})
PUP_ROLE = "pup"
JUVENILE_ROLE = "juvenile"
DROWN_SICK_ROLE = "drown_sick"

# Roles that may be held at any life stage (not forced to pup/juvenile by age).
AGE_OVERRIDE_ROLES = frozenset({DROWN_SICK_ROLE})


def wolf_role(user) -> str:
    if not user:
        return "hunter"
    return user["wolf_role"] if "wolf_role" in user.keys() else "hunter"


def wolf_age_moons(user) -> int:
    if not user:
        return 24
    return int(user["age_months"]) if "age_months" in user.keys() else 24


def life_stage(user) -> str:
    from engine.aging import stage_for_age

    return stage_for_age(wolf_age_moons(user))


def is_pup(role: str) -> bool:
    return role == PUP_ROLE


def is_juvenile(role: str) -> bool:
    return role == JUVENILE_ROLE


def is_young_wolf(role: str) -> bool:
    return role in YOUNG_ROLES


def young_wolf_block(user, *, action: str) -> str | None:
    """return an error message if this wolf is too young for the action."""
    role = wolf_role(user)
    label = ROLE_LABELS.get(role, role.title())
    stage = life_stage(user)

    if action in ("court", "mate", "birth") and (is_young_wolf(role) or stage in ("pup", "juvenile")):
        return (
            f"**{label}** wolves are forbidden to mate. "
            "juveniles (6 to 24 moons) and pups (under 6 moons) cannot court or breed."
        )

    if action == "hunt" and (is_pup(role) or stage == "pup"):
        return (
            "pups are too small to hunt. you are fed by caretakers until you earn a juvenile role "
            "or survive to practice hunting."
        )

    if action == "combat" and (is_pup(role) or stage == "pup"):
        return "pups cannot join combat encounters; the den protects you."

    if action == "crime" and (is_pup(role) or stage == "pup"):
        return "pups cannot run scores; the den keeps you out of trouble."

    return None
