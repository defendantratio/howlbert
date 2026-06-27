"""StarClan omens; Warrior Cats spiritual flavor for wilderness rest and clan gifts."""

from __future__ import annotations

import random

STARCLAN_BAD_OMENS = (
    "A frost-star moth spirals wrong-way through the pines; **StarClan** turns their backs.",
    "The moon hides; for a heartbeat every ancestor's eyes feel cold on your pelt.",
    "Three drops of blood on snow that was not there a moment ago.",
    "A warrior's silhouette on the ridge vanishes when you blink; only ash-scent remains.",
)

STARCLAN_GOOD_OMENS = (
    "A star-flecked moth crosses the moon; **StarClan** walks with you tonight.",
    "Silver fur brushes your flank; no wolf is there, only warmth and cedar scent.",
    "Four stones gleam like starlight at a crossroads; the path ahead feels blessed.",
    "An elder's voice on the wind: _'The forest remembers those who keep their oaths.'_",
)

STARCLAN_NEUTRAL_OMENS = (
    "Roll **{roll}**; the stars are distant but steady.",
    "Roll **{roll}**; **StarClan** watches without speaking.",
    "Roll **{roll}**; ancestor-scent drifts through the trees, then fades.",
    "Roll **{roll}**; the moon is silent; neither blessing nor curse.",
)

STARCLAN_VISION_OMENS = (
    "The sky splits with starlight; for one breath you see **Fourtrees** crowned in silver mist.",
    "A river of stars pours between the branches; your paws feel lighter on the trail.",
    "Whispers without words: _patrol the border, honor the code, the lake endures._",
)

STARCLAN_RECEIVE_OMENS = (
    "A medicine cat left a sprig bound in cobweb beside the bundle; **StarClan** approves the trade.",
    "Starlight catches the dew on the herbs; an omen of trust between Clans and wolves.",
    "A moth with wings like tiny moons settles on the prey, then flies toward the high stones.",
)


def rest_omen_available(user, day: int) -> bool:
    """Once per sunrise for `/world action:omen`."""
    if not user or not day:
        return True
    last = int(user["last_rest_omen_day"]) if "last_rest_omen_day" in user.keys() else 0
    return last < day


def mark_rest_omen(user, day: int) -> None:
    import database as db

    db.update_user_by_id(user["id"], last_rest_omen_day=day)


def roll_rest_omen() -> tuple[str, str]:
    """
    Rest omen for `/world action:omen`.
    Returns (kind, body) where kind is good | bad | vision | neutral.
    """
    roll = random.randint(1, 20)
    if roll == 1:
        line = random.choice(STARCLAN_BAD_OMENS)
        return (
            "bad",
            f"{line}\n\nroll **1**; bad omen (**disadvantage** on tomorrow's first roll).",
        )
    if roll == 20:
        line = random.choice(STARCLAN_GOOD_OMENS)
        return (
            "good",
            f"{line}\n\nroll **20**; good omen (**advantage** on tomorrow's first roll).",
        )
    if roll >= 18 and random.random() < 0.4:
        line = random.choice(STARCLAN_VISION_OMENS)
        return "vision", f"{line}\n\nroll **{roll}**; **starclan** vision (no roll buff, +mood)."
    return "neutral", random.choice(STARCLAN_NEUTRAL_OMENS).format(roll=roll)


def try_starclan_receive_omen() -> str | None:
    """Rare flavor line when collecting high-trust clan goods."""
    return random.choice(STARCLAN_RECEIVE_OMENS)
