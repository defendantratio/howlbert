# energy.py
"""Wolvden-style activity energy.

Every repeatable field/social/den action spends energy. Energy never blocks an
action outright: spending past zero still lets the action happen, it just costs
extra exhaustion and mood instead of refusing the command. Energy sits *on top*
of the exhaustion / pain-exhaustion mechanics rather than replacing them.

Energy restores three ways, all coupled to hunger (a starving wolf has no
calories to spare, so it regenerates less):
  * a big chunk each sunrise (the overnight sleep / long rest),
  * a smaller chunk from a manual short or long rest, and
  * a slow real-time drip while a wolf is idle (not acting) during the day.

The daytime drip is lazy: nothing runs on a timer. Whenever energy is read or
spent we credit the idle hours since ``last_energy_at`` and re-stamp the clock,
so resting simply means not acting for a while.
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
    ENERGY_HUNGER_FLOOR,
    ENERGY_HUNGER_FULL,
    ENERGY_LONG_REST_GAIN,
    ENERGY_MAX,
    ENERGY_REALTIME_REGEN_PER_HOUR,
    ENERGY_SUNRISE_REGEN,
)
from engine.time_cooldowns import minutes_since_iso

# activity -> base energy cost (before any role discount)
ACTIVITY_COSTS: dict[str, int] = {
    "hunt": ENERGY_COST_HIGH,
    "forage": ENERGY_COST_MED,
    "verge_forage": ENERGY_COST_MED,
    "explore": ENERGY_COST_MED,
    "scavenge": ENERGY_COST_MED,
    "fishing": ENERGY_COST_MED,
    "track": ENERGY_COST_MED,
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
    "adopt": ENERGY_COST_MED,
    "cat_receive": ENERGY_COST_LOW,
    "npc_action": ENERGY_COST_LOW,
    "faction_action": ENERGY_COST_MED,
    "role_event": ENERGY_COST_MED,
    "prophecy": ENERGY_COST_LOW,
    "work": ENERGY_COST_MED,
    "crime": ENERGY_COST_MED,
    "court": ENERGY_COST_MED,
    "weep": ENERGY_COST_LOW,
}




# signature activities per role: a specialist tires slower at their own craft,
# the way a hunter tires slower on the hunt. This is the discount that replaces
# every old per-sunrise cap / diminishing-returns throttle (see engine.diminishing).
_SIGNATURE_ACTIVITIES: dict[str, str] = {
    "hunt": "hunter",
    "forage": "forager",
    "verge_forage": "forager",
    "explore": "scout",
    "survey": "scout",
    "trail": "scout",
    "track": "scout",
    "sniff": "scout",
}


def _is_signature_specialist(user, activity: str) -> bool:
    role = _SIGNATURE_ACTIVITIES.get(activity)
    if not role:
        return False
    try:
        from engine.role_privileges import is_hunter, is_forager, is_scout

        return {"hunter": is_hunter, "forager": is_forager, "scout": is_scout}[role](user)
    except Exception:
        return False


def activity_energy_cost(user, activity: str) -> int:
    """Energy ``activity`` costs *this* wolf: the flat discounted rate on their
    signature action (they tire slower at their own craft), else the base cost.
    Hunting keeps its own dedicated hunter rate."""
    if activity == "hunt":
        from config import HUNT_ENERGY_COST, HUNT_ENERGY_COST_HUNTER
        from engine.role_privileges import is_hunter

        return HUNT_ENERGY_COST_HUNTER if is_hunter(user) else HUNT_ENERGY_COST
    if _is_signature_specialist(user, activity):
        return ENERGY_COST_DISCOUNTED
    return ACTIVITY_COSTS.get(activity, ENERGY_COST_MED)


def current_energy(user) -> int:
    """Raw stored energy (no idle-drip credit applied)."""
    if not user or "energy" not in user.keys() or user["energy"] is None:
        return ENERGY_MAX
    return int(user["energy"])


def hunger_factor(user) -> float:
    """0..1 scale on energy regen: full at ENERGY_HUNGER_FULL hunger, floored so
    a starving wolf still recovers a trickle."""
    hunger = db.row_val(user, "hunger", 100)
    try:
        hunger = int(hunger)
    except (TypeError, ValueError):
        hunger = 100
    return max(ENERGY_HUNGER_FLOOR, min(1.0, hunger / float(ENERGY_HUNGER_FULL)))


def metabolic_factor(user, *, season: str | None = None) -> float:
    """<1.0 when a wolf is burning extra calories and so recovers energy slower:
    pregnancy, nursing, active illness/fever, and winter cold. Stacks
    multiplicatively with hunger_factor."""
    factor = 1.0
    if int(db.row_val(user, "is_pregnant", 0) or 0):
        factor *= 0.75
    try:
        from engine.nursing import is_nursing_mother

        if is_nursing_mother(user):
            factor *= 0.8
    except Exception:
        pass
    if (db.row_val(user, "disease", "") or ""):
        factor *= 0.85  # fighting illness burns reserves
    if season == "winter":
        factor *= 0.8  # cold nights cost energy to stay warm
    return factor


def sunrise_regen_amount(user, *, season: str | None = None) -> int:
    """Energy restored by the overnight sleep at each sunrise, scaled by hunger
    and by metabolically expensive states (pregnancy, nursing, illness, winter)."""
    scale = hunger_factor(user) * metabolic_factor(user, season=season)
    return int(round((ENERGY_SUNRISE_REGEN + ENERGY_LONG_REST_GAIN) * scale))


def sync_energy(user) -> int:
    """Credit the real-time idle drip since ``last_energy_at`` and persist it.

    Returns the wolf's current energy after the drip. A no-op (beyond stamping
    the clock) when energy is already full or no idle time has passed."""
    if not user or "id" not in user.keys():
        return current_energy(user)
    cur = current_energy(user)
    last = db.row_val(user, "last_energy_at", "") or ""
    if not last:
        # start the idle clock the first time we see this wolf.
        db.update_user(user["discord_id"], wolf_id=user["id"], last_energy_at=db.utcnow())
        return cur
    if cur >= ENERGY_MAX:
        return cur
    mins = minutes_since_iso(last)
    if not mins or mins <= 0:
        return cur
    regen = int((mins / 60.0) * ENERGY_REALTIME_REGEN_PER_HOUR * hunger_factor(user) * metabolic_factor(user))
    if regen <= 0:
        return cur
    new_energy = min(ENERGY_MAX, cur + regen)
    db.update_user(
        user["discord_id"], wolf_id=user["id"], energy=new_energy, last_energy_at=db.utcnow()
    )
    return new_energy


def spend_energy(user, activity: str, *, discounted: bool = False, cost: int | None = None) -> tuple[int, bool, str]:
    """
    Spend energy for ``activity``; always lets the action proceed. Credits the
    idle drip first, then spends. If there wasn't enough energy banked, applies
    an exhaustion+mood penalty instead of refusing the command, and restarts the
    idle clock. Returns (new_energy, had_enough, penalty_note).

    ``cost`` overrides the per-activity cost (used for role-scaled costs like the
    hunter's cheaper hunt); otherwise the ACTIVITY_COSTS/discounted rate is used.
    """
    if cost is None:
        cost = ENERGY_COST_DISCOUNTED if discounted else activity_energy_cost(user, activity)
    banked = sync_energy(user)
    had_enough = banked >= cost
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
    # restart the idle drip clock from this action.
    db.update_user(user["discord_id"], wolf_id=user["id"], last_energy_at=db.utcnow())
    return new_energy, had_enough, penalty_note


def energy_line(user) -> str:
    """`/vitals` display line for energy (syncs the idle drip first)."""
    energy = sync_energy(user)
    if energy <= 15:
        note = "; **spent**; acting now adds extra exhaustion and mood loss"
    elif energy <= 40:
        note = "; tiring; rest or wait out the day to recover"
    else:
        note = ""
    return f"**{energy}/{ENERGY_MAX}**{note}"
