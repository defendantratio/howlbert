"""Maw faith / belief; chosen at registration, shown on profile."""

from __future__ import annotations

MAW_BELIEF_OPTIONS: tuple[tuple[str, str], ...] = (
    ("Orthodox", "orthodox"),
    ("Orthodox (Pragmatic)", "orthodox_pragmatic"),
    ("Zealot", "zealot"),
    ("Doubter", "doubter"),
    ("Agnostic", "agnostic"),
    ("Atheist", "atheist"),
    ("Heretic", "heretic"),
)

MAW_BELIEF_LABELS: dict[str, str] = {value: label for label, value in MAW_BELIEF_OPTIONS}

MAW_BELIEF_BLURBS: dict[str, str] = {
    "orthodox": "The Maw is what is; wounded, hungry, neither good nor evil.",
    "orthodox_pragmatic": (
        "The Maw's hunger justifies the strong eating the weak; truth, not cruelty."
    ),
    "zealot": "Every illness is the Maw's question; every cure is the wolf's answer.",
    "doubter": "Wants to believe in justice; has not seen much of it.",
    "agnostic": "Too much suffering seen to claim certainty either way.",
    "atheist": "No god would let wolves suffer as they do.",
    "heretic": "Whispers that the Maw chooses to hunger; and enjoys the watching.",
}

VALID_MAW_BELIEFS = frozenset(MAW_BELIEF_LABELS)


def resolve_register_maw_belief(belief: str | None, *, affiliation: str) -> str | None:
    """Pick stored belief key; default orthodox for Great Pack wolves."""
    if belief and belief in VALID_MAW_BELIEFS:
        return belief
    from config import GREAT_PACKS, UNAFFILIATED_KEYS

    if affiliation in UNAFFILIATED_KEYS:
        return None
    if affiliation in GREAT_PACKS:
        return "orthodox"
    return None


def format_maw_belief(user) -> str | None:
    raw = None
    if user and hasattr(user, "keys") and "maw_belief" in user.keys():
        raw = user["maw_belief"]
    elif user and isinstance(user, dict):
        raw = user.get("maw_belief")
    if not raw or raw not in MAW_BELIEF_LABELS:
        return None
    label = MAW_BELIEF_LABELS[raw]
    blurb = MAW_BELIEF_BLURBS.get(raw, "")
    return f"**{label}**; {blurb}" if blurb else f"**{label}**"
