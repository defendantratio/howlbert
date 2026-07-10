# energy.py
"""Wolvden-style activity energy.

Every repeatable field/social/den action spends energy instead of being
hard-capped or paying out on a diminishing curve. Energy never blocks an
action outright: spending past zero still lets the action happen, it just
costs extra exhaustion and mood instead of refusing the command. Energy
refills with a passive drip each sunrise (representing rest/inactivity
overnight) and a larger chunk from a long or short rest.
"""

from __future__ import annotations

import database as db
from config import (
    ENERGY_COST_DISCOUNTED,
    ENERGY_COST_HIGH,
    ENERGY_COST_LOW,
    ENERGY_COST_MED,
    ENERGY_EMPTY_EXHAUSTION_GAIN,
    ENERGY_EMPTY_MOOD_LOSS,
    ENERGY_MAX,
)

# activity -> base energy cost (before any role discount)
ACTIVITY_COSTS: dict[str, int] = {
    "hunt": ENERGY_COST_HIGH,
    "forage": ENERGY_COST_MED,
    "verge_forage": ENERGY_COST_MED,
    "explore": ENERGY_COST_MED,
    "sniff": ENERGY_COST_LOW,
    "howl": ENERGY_COST_LOW,
    "survey": ENERGY_COST_HIGH,
    "trail": ENERGY_COST_HIGH,
    "war_patrol": ENERGY_COST_HIGH,
    "groom": ENERGY_COST_MED,
    "self_groom": ENERGY_COST_LOW,
    "socialize": ENERGY_COST_MED,
    "whisper": ENERGY_COST_LOW,
    "rank_dispute": ENERGY_COST_LOW,
    "surgery": ENERGY_COST_HIGH,
    "swim": ENERGY_COST_LOW,
    "sacred_visit": ENERGY_COST_MED,
    "omen": ENERGY_COST_LOW,
    "sign_read": ENERGY_COST_LOW,
    "hunt_prayer": ENERGY_COST_LOW,
    "share_territory": ENERGY_COST_MED,
    "aid_rival_pack": ENERGY_COST_MED,
    "duplicate_trade": ENERGY_COST_MED,
    "wolf_pact_food_trade": ENERGY_COST_MED,
    "wolf_receive": ENERGY_COST_MED,
    "playall": ENERGY_COST_HIGH,
    "accuse": ENERGY_COST_LOW,
    "drinkall": ENERGY_COST_HIGH,
    "duptrade": ENERGY_COST_MED,
    "pack_food_share": ENERGY_COST_MED,
    "pup_training": ENERGY_COST_MED,
    "court": ENERGY_COST_LOW,
    "adopt": ENERGY_COST_MED,
    "scavenge": ENERGY_COST_LOW,
    "track": ENERGY_COST_MED,
    "fishing": ENERGY_COST_MED,
    "work": ENERGY_COST_LOW,
    "crime": ENERGY_COST_MED,
    "cat_receive": ENERGY_COST_LOW,
    "npc_action": ENERGY_COST_LOW,
    "weep": ENERGY_COST_LOW,
    "faction_action": ENERGY_COST_MED,
    "role_event": ENERGY_COST_MED,
    "prophecy": ENERGY_COST_LOW,
}


def energy_cost(activity: str, *, discounted: bool = False) -> int:
    """Base energy cost for an activity; role specialists pay a flat
    discounted cost instead (their signature action, not a random one)."""
    if discounted:
        return ENERGY_COST_DISCOUNTED
    return ACTIVITY_COSTS.get(activity, ENERGY_COST_MED)


def current_energy(user) -> int:
    if not user or "energy" not in user.keys() or user["energy"] is None:
        return ENERGY_MAX
    return int(user["energy"])


def spend_energy(user, activity: str, *, discounted: bool = False) -> tuple[int, bool, str]:
    """
    Spend energy for `activity`; always lets the action proceed. If there
    wasn't enough energy banked, applies an exhaustion+mood penalty instead
    of refusing the command. Returns (new_energy, had_enough, penalty_note).
    """
    cost = energy_cost(activity, discounted=discounted)
    had_enough = current_energy(user) >= cost
    new_energy = db.adjust_energy(user["id"], -cost)

    penalty_note = ""
    if not had_enough:
        from engine.exhaustion_effects import EXHAUSTION_MAX

        exhaustion = int(user["exhaustion"]) if "exhaustion" in user.keys() and user["exhaustion"] is not None else 0
        new_exhaustion = min(EXHAUSTION_MAX, exhaustion + ENERGY_EMPTY_EXHAUSTION_GAIN)
        db.set_user_conditions(user["discord_id"], wolf_id=user["id"], exhaustion=new_exhaustion)
        db.adjust_mood(user["id"], -ENERGY_EMPTY_MOOD_LOSS)
        penalty_note = (
            f"running on empty; **+{ENERGY_EMPTY_EXHAUSTION_GAIN} exhaustion**, "
            f"**−{ENERGY_EMPTY_MOOD_LOSS} mood**."
        )
    return new_energy, had_enough, penalty_note


def regen_energy_on_rollover(conn) -> None:
    """Passive energy drip for every living wolf each sunrise."""
    from config import ENERGY_MAX, ENERGY_SUNRISE_REGEN

    conn.execute(
        """
        UPDATE users
        SET energy = MIN(?, energy + ?)
        WHERE condition NOT IN ('dead', 'dying')
        """,
        (ENERGY_MAX, ENERGY_SUNRISE_REGEN),
    )
