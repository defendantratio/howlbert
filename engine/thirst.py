"""Thirst; separate from hunger; creek drinks and prey moisture restore it."""

from __future__ import annotations

from config import (
    DRINK_EXHAUSTION_RELIEF,
    DRINK_HP_RESTORE,
    DRINK_HUNGER_RESTORE,
    DRINK_MOOD_RESTORE,
    DRINK_THIRST_RESTORE,
    NEEDS_EXHAUSTION_GAIN,
    THIRST_CRITICAL_THRESHOLD,
    THIRST_HUNT_PENALTY_PCT,
    THIRST_LOW_THRESHOLD,
    THIRST_MAX,
    THIRST_ROLLOVER_DECAY,
)
from engine.time_cooldowns import cooldown_minutes_remaining

HUNT_ACTIVITIES = frozenset({"hunt", "scavenge", "track", "fishing"})

_PREY_THIRST: dict[str, int] = {
    "fish": 22,
    "vole": 6,
    "hare": 8,
    "rabbit": 8,
    "grouse": 7,
    "agouti": 7,
    "beaver": 10,
    "deer": 12,
    "elk": 14,
    "carrion": 3,
}


def user_thirst(user) -> int:
    if "thirst" not in user.keys():
        return 80
    return int(user["thirst"])




def thirst_activity_block(user) -> str | None:
    thirst = user_thirst(user)
    if thirst < THIRST_CRITICAL_THRESHOLD:
        return (
            f"you're parched (**{thirst}/{THIRST_MAX}**); `/drink` at the creek, eat moist prey, "
            "or ask your **alpha** for `/packlife action:drinkall` before ranging out."
        )
    return None


def apply_thirst_bone_penalty(amount: int, thirst: int) -> tuple[int, str]:
    if amount <= 0 or thirst >= THIRST_LOW_THRESHOLD:
        return amount, ""
    reduced = max(0, int(amount * (100 - THIRST_HUNT_PENALTY_PCT) / 100))
    note = f"low hydration ({thirst}); −{THIRST_HUNT_PENALTY_PCT}% bone payout."
    return reduced, note


def meal_thirst_gain(prey_key: str, uses_consumed: int = 1) -> int:
    from engine.prey_items import prey_meta

    meta = prey_meta(prey_key)
    per_use = meta.get("thirst", _PREY_THIRST.get(prey_key, 8))
    return min(THIRST_MAX, per_use * uses_consumed)


def format_thirst_line(user) -> str:
    thirst = user_thirst(user)
    if thirst <= 0:
        note = "; **dying**; roll **`/medic action:deathsaves`** or get **`/medic action:stabilize`**."
    elif thirst <= THIRST_ROLLOVER_DECAY:
        note = "; will **collapse** at next sunrise without water."
    elif thirst < THIRST_CRITICAL_THRESHOLD:
        note = "; parched; strenuous activity blocked until you drink."
    elif thirst < THIRST_LOW_THRESHOLD:
        note = (
            f"; low; hunt payouts **−{THIRST_HUNT_PENALTY_PCT}%**, "
            f"**+{NEEDS_EXHAUSTION_GAIN} exhaustion** each sunrise until you drink."
        )
    else:
        note = ""
    return f"**{thirst}/{THIRST_MAX}**{note}"


def drink_at_creek(user, *, day: int, season: str, guild_id: int | None = None, clean_water: bool = False) -> tuple[bool, str]:
    """Creek drink; once per hour (real time), unlimited over a long day."""
    from engine.vitals import living_wolf_block

    import database as db

    block = living_wolf_block(user)
    if block:
        return False, block

    from config import THIRST_MAX

    already_full = (int(user["thirst"]) if "thirst" in user.keys() and user["thirst"] is not None else 0) >= THIRST_MAX

    db.update_user(
        user["discord_id"],
        last_drink_at=db.utcnow(),
        last_drink_day=day,
        wolf_id=user["id"],
    )
    from engine.plot_blinking import plot_drink_thirst_bonus

    gp = user["great_pack"] if "great_pack" in user.keys() else None
    thirst_restore = DRINK_THIRST_RESTORE
    plot_line = ""
    if guild_id is not None:
        bonus, plot_line = plot_drink_thirst_bonus(guild_id, gp)
        thirst_restore = max(1, thirst_restore + bonus)
    thirst = db.adjust_thirst(user["id"], thirst_restore)
    hunger = db.adjust_hunger(user["id"], DRINK_HUNGER_RESTORE)
    hp_gain = min(user["max_hp"] - user["hp"], DRINK_HP_RESTORE)
    if hp_gain > 0:
        db.set_user_conditions(user["discord_id"], wolf_id=user["id"], hp=user["hp"] + hp_gain)
    mood = db.adjust_mood(user["id"], DRINK_MOOD_RESTORE)
    old_exhaustion = int(user["exhaustion"]) if "exhaustion" in user.keys() else 0
    new_exhaustion = max(0, old_exhaustion - DRINK_EXHAUSTION_RELIEF)
    if new_exhaustion != old_exhaustion:
        db.set_user_conditions(user["discord_id"], wolf_id=user["id"], exhaustion=new_exhaustion)
        from engine.energy import gain_energy_from_exhaustion_relief
        gain_energy_from_exhaustion_relief(user, old_exhaustion - new_exhaustion)

    # drink as often as you like; but forcing water down when already fully
    # watered bloats the gut, adding pain exhaustion (overhydration)
    overfull_note = ""
    if already_full:
        from engine.exhaustion_effects import PAIN_EXHAUSTION_MAX
        old_pe = int(user["pain_exhaustion"]) if "pain_exhaustion" in user.keys() else 0
        new_pe = min(PAIN_EXHAUSTION_MAX, old_pe + 1)
        db.update_user(user["discord_id"], wolf_id=user["id"], pain_exhaustion=new_pe)
        overfull_note = "\n_already watered to the brim; forcing more down bloats the gut, **+1 pain exhaustion**._"

    msg = (
        f"cold water from the **{season}** creek; hydration **{thirst}** (+{thirst_restore}), "
        f"satiety **{hunger}** (+{DRINK_HUNGER_RESTORE}), mood **{mood}** (+{DRINK_MOOD_RESTORE})"
    )
    if new_exhaustion != old_exhaustion:
        msg += f", exhaustion **{new_exhaustion}** (−{old_exhaustion - new_exhaustion})"
    if plot_line:
        msg += f"\n_{plot_line}_"
    from engine.disease_contract import (
        try_leptospirosis_exposure,
        try_mistmoor_swamp_exposure,
        try_silverrush_sewage_exposure,
    )

    rot_note = try_silverrush_sewage_exposure(user)
    if rot_note:
        msg += f"\n_{rot_note}_"
    if not clean_water:
        swamp_note = try_mistmoor_swamp_exposure(user)
        if swamp_note:
            msg += f"\n_{swamp_note}_"
    lepto_note = try_leptospirosis_exposure(user, clean_water=clean_water)
    if lepto_note:
        msg += f"\n_{lepto_note}_"
    if guild_id is not None:
        from engine.plot_blinking import try_plot_witness

        msg += try_plot_witness(user, guild_id, day, action="drink")
    if hp_gain:
        msg += f", **+{hp_gain} hp**"
    msg += overfull_note
    return True, msg


def run_drinkall(
    pack_id: int,
    day: int,
    *,
    caller=None,
    discord_admin: bool = False,
) -> tuple[bool, str, int]:
    """Alpha leads the den to the creek; hydration restore for all packmates once per sunrise."""
    import database as db

    from engine.pack_leadership import PACK_BULK_ALPHA_ONLY_MSG, can_run_pack_bulk_action
    from engine.vitals import living_wolf_block

    pack = db.get_pack(pack_id)
    if not pack:
        return False, "pack not found.", 0
    if caller and not can_run_pack_bulk_action(caller, pack, discord_admin=discord_admin):
        return False, PACK_BULK_ALPHA_ONLY_MSG, 0

    # unlimited; throttled by the caller's energy (see engine.energy) rather than
    # a shrinking restore, so a led creek trip always tops the den off.
    from engine.energy import spend_energy
    drinkall_penalty = ""
    if caller:
        _new_energy, _had_energy, drinkall_penalty = spend_energy(caller, "drinkall")
    restore = DRINK_THIRST_RESTORE

    members = db.get_pack_den_wolves(pack_id)
    if not members:
        return False, "no wolves in the den.", 0

    drank = 0
    lines: list[str] = []
    for wolf in members:
        block = living_wolf_block(wolf)
        if block:
            lines.append(f"**{wolf['wolf_name']}**; {block}")
            continue
        thirst = db.adjust_thirst(wolf["id"], restore)
        lines.append(f"**{wolf['wolf_name']}** → hydration **{thirst}** (+{restore})")
        drank += 1

    if drank == 0:
        return False, "no packmate could drink at the creek.", 0

    db.set_pack_drinkall_day(pack_id, day)
    summary = "\n".join(lines[:12])
    if len(lines) > 12:
        summary += f"\n_…and {len(lines) - 12} more._"
    msg = (
        f"**communal drink** at the creek; **{drank}** wolf(s) lapped up.\n{summary}"
    )
    if drinkall_penalty:
        msg += f"\n_{drinkall_penalty}_"
    return True, msg, drank
