"""Pack unity meter; hunt bonuses, howl rally rules, and dissolve threshold."""

from __future__ import annotations

import random

from config import (
    PACK_UNITY_DISSOLVE_THRESHOLD,
    PACK_UNITY_MAX,
    PACK_UNITY_MIN,
)


HOWL_CALLS = (
    "Your voice carries over the ridges; a long, clear note.",
    "The den answers in scattered echoes before the wind takes them.",
    "You throw your head back and let the wild hear where you stand.",
    "A mourning note, then a rallying rise; the old song of the pack.",
    "Your howl threads through the pines; somewhere, a packmate pricks their ears.",
)

HOWL_ECHO_CALLS = (
    "The chorus swells; **{count}** wolves howl as one this sunrise.",
    "**{count}** voices braid the sky. Even the river seems to listen.",
    "Answer builds on answer; **{count}** throats, one heartbeat.",
)

HOWL_MUTED_CALLS = (
    "Your howl goes up; but the den is too fractured to answer with strength.",
    "You sing anyway. The silence between echoes hurts more than hunger.",
    "Only a few voices answer. The pack's heart is not in it yet.",
)


def unity_is_broken(unity: int) -> bool:
    """Unity at 0 or below; ordinary howls cannot raise unity."""
    return unity <= 0


def howl_can_rally_unity(user, pack) -> bool:
    """alpha or beta (advisor) can rally a broken pack; ordinary wolves cannot."""
    from engine.pack_leadership import is_pack_alpha, is_pack_beta

    if not unity_is_broken(int(pack["pack_unity"])):
        return True
    if is_pack_alpha(user, pack):
        return True
    return is_pack_beta(user, pack)


def compute_howl_unity_gain(user, pack, unity: int, echo_count: int) -> int:
    from engine.pack_leadership import is_pack_alpha

    if unity_is_broken(unity) and not howl_can_rally_unity(user, pack):
        return 0

    gain = 2 if is_pack_alpha(user, pack) else 1

    if echo_count >= 3 and gain > 0:
        gain += 1
    return gain


HOWL_MUFFLING_WEATHER = frozenset({"fog", "wind", "storm", "thunderstorm", "hail"})


def howl_weather_muffle_note(unity_gain: int, weather: str) -> tuple[int, str]:
    """
    A howl genuinely doesn't carry as far through fog, wind, or a storm; on
    muffling weather a successful (nonzero) howl loses 1 unity off its gain,
    never dropping below 1. Returns (adjusted_gain, note); note is "" when
    nothing changed.
    """
    if unity_gain <= 0 or weather not in HOWL_MUFFLING_WEATHER:
        return unity_gain, ""
    adjusted = max(1, unity_gain - 1)
    if adjusted == unity_gain:
        return unity_gain, ""
    return adjusted, f"_the call is swallowed by the {weather}; unity gain dampened (**{adjusted}** instead of **{unity_gain}**)._"


def unity_effect_text(unity: int) -> str:
    if unity <= PACK_UNITY_DISSOLVE_THRESHOLD:
        return (
            f"**dissolved**; at **{PACK_UNITY_DISSOLVE_THRESHOLD}** unity the den fractures; "
            "every wolf is cast to **loner** until they `/setfaction` back in."
        )
    if unity < 0:
        return (
            f"pack fracturing (**{unity}**); **−25%** bones on `/bones action:hunt` "
            "(50🦴 → 37🦴 before tax). "
            "**Plain `/howl` cannot raise unity** until **Alpha** or **Beta (Advisor)** rallies, "
            "or you share fresh-kill / hang a den charm."
        )
    if unity == 0:
        return (
            "pack breaking; **−20%** hunt bones (50🦴 → 40🦴). "
            "**plain `/howl` does not raise unity**; need alpha, beta (advisor), den charm, or fresh-kill."
        )
    if unity <= 2:
        return "low unity; **−10%** hunt bones (50🦴 → 45🦴 before tax)."
    if unity >= 8:
        return "high unity; **+10%** hunt bones (50🦴 → 55🦴); howls rally harder."
    return "steady; normal hunt payouts. howl to strengthen the chorus."


def standing_effect_text(standing: int) -> str:
    from config import WOLF_STANDING_KICK_THRESHOLD

    if standing <= WOLF_STANDING_KICK_THRESHOLD:
        return (
            f"**cast out**; at **{WOLF_STANDING_KICK_THRESHOLD}** standing you are expelled "
            "from the pack (loner until `/setfaction`). "
            "**Alphas** face the **Rite of the Broken Canine** instead (`/pack brokenrite`)."
        )
    if standing < 0:
        return (
            f"disfavored (**{standing}**); one step from exile at "
            f"**{WOLF_STANDING_KICK_THRESHOLD}**. earn standing through quests, howls, and sharing. "
            "**Crime** and **cross-pack mating** (if caught) lower standing. "
            "A clean rival treasury raid earns den standing; getting caught costs standing and rival pack trust."
        )
    return "in good standing with the den."


def hunt_bone_multiplier(unity: int) -> float:
    if unity < 0:
        return 0.75
    if unity == 0:
        return 0.8
    if unity <= 2:
        return 0.9
    if unity >= 8:
        return 1.1
    return 1.0


def apply_unity_to_hunt_amount(amount: int, unity: int) -> int:
    if amount <= 0:
        return 0
    return max(0, int(amount * hunt_bone_multiplier(unity)))


OVERHUNTING_THRESHOLD = 10
OVERHUNTING_STEP_PENALTY = 0.05
OVERHUNTING_FLOOR_MULT = 0.6


def overhunting_hunt_multiplier(hunts_today: int) -> tuple[float, str]:
    """
    Local prey thins out after a pack hammers the same ground too many times
    in one sunrise; each hunt past OVERHUNTING_THRESHOLD trims yield further,
    bottoming out at OVERHUNTING_FLOOR_MULT. Resets clean at the next rollover.
    """
    over = hunts_today - OVERHUNTING_THRESHOLD
    if over <= 0:
        return 1.0, ""
    mult = max(OVERHUNTING_FLOOR_MULT, 1.0 - over * OVERHUNTING_STEP_PENALTY)
    pct = int(round((1.0 - mult) * 100))
    return mult, f"overhunted ground (hunt #{hunts_today} this sunrise): −{pct}% hunt bones"


def pick_howl_flavor(*, echo_count: int, muted: bool = False) -> str:
    if muted:
        return random.choice(HOWL_MUTED_CALLS)
    if echo_count >= 3:
        return random.choice(HOWL_ECHO_CALLS).format(count=echo_count)
    return random.choice(HOWL_CALLS)


def format_unity_meter(unity: int) -> str:
    return f"{unity}/{PACK_UNITY_MAX} (min {PACK_UNITY_MIN})"


def format_howl_carry(reach: int, *, natural_20: bool = False) -> str:
    """In-world how far today's chorus carries (tree-lengths on the wind)."""
    unit = "tree-length" if reach == 1 else "tree-lengths"
    text = f"carries **{reach}** {unit} on the wind"
    if natural_20:
        text += " — the note doubles back across the ridges"
    return text
