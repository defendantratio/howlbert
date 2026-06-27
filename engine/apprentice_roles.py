"""Apprentice ranks; trainee versions of core pack roles."""

from __future__ import annotations

APPRENTICE_PARENT: dict[str, str] = {
    "hunter_apprentice": "hunter",
    "medic_apprentice": "medic",
    "caretaker_apprentice": "caretaker",
    "diplomat_apprentice": "diplomat",
    "scout_apprentice": "scout",
    "forager_apprentice": "forager",
}

APPRENTICE_ROLES = frozenset(APPRENTICE_PARENT.keys())


def is_apprentice(role: str) -> bool:
    return role in APPRENTICE_ROLES


def parent_role(role: str) -> str | None:
    return APPRENTICE_PARENT.get(role)


def matches_parent_role(wolf_role: str, parent: str) -> bool:
    """true when role is the parent rank or its apprentice path."""
    if wolf_role == parent:
        return True
    return APPRENTICE_PARENT.get(wolf_role) == parent


def quest_role_matches(wolf_role: str, required_role: str) -> bool:
    """Apprentices may take role quests for their mentor path."""
    if wolf_role == required_role:
        return True
    return APPRENTICE_PARENT.get(wolf_role) == required_role


def role_event_key(role: str) -> str:
    """fall back to parent role events for apprentices."""
    return parent_role(role) or role
