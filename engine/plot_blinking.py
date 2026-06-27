"""Book One: The Blinking — plot phases with mechanical pressure (not lore-only)."""

from __future__ import annotations

import random
import sqlite3
from typing import Any

import database as db
from config import GREAT_PACKS

PLOT_TITLE = "book one: the blinking"
PLOT_MAX_PHASE = 12

# phase -> act label, staff beat, active mechanical summary
PHASES: dict[int, dict[str, Any]] = {
    1: {
        "act": "Act I",
        "title": "Bitten Moon",
        "news": "The moon rises bruised-purple with a chunk missing from its lower edge.",
        "mechanics": "Den mood −1 at sunrise; lunar omen visible on `/world action:plot`.",
    },
    2: {
        "act": "Act I",
        "title": "White Omen",
        "news": "Star-speech carries on the wind; border patrols report wolves listening instead of hunting.",
        "mechanics": "Quest **blink_border_patrol** live; Thistlehide `/pack patrol` +1 standing roll chance.",
    },
    3: {
        "act": "Act I",
        "title": "Peak Bleeds",
        "news": "Greyspire scouts swear the high spur weeps rust down the stone.",
        "mechanics": "Mountain `/world action:travel territory:mountain` DC +2; Greyspire hunt/scavenge +10% bones.",
    },
    4: {
        "act": "Act I",
        "title": "Warm Below",
        "news": "Silverrush water runs warm; fish belly-up in the shallows.",
        "mechanics": "Silverrush thirst −2 extra at sunrise; fishing −25%; pack fish rot 1 day faster.",
    },
    5: {
        "act": "Act I",
        "title": "Belly Silence",
        "news": "Mistmoor vigils go quiet; the chewing sound the Drown-Sick wait for does not come.",
        "mechanics": "Mistmoor wolves +5% disease spread on sunrise; sacred-visit reminders doubled in den news.",
    },
    6: {
        "act": "Act II",
        "title": "Border Paranoia",
        "news": "Cat musk and wolf theft on the same wind; every patrol suspects Greyspire.",
        "mechanics": "Cat pact trust −3; `/field action:sniff` border fights +25%; rogue `/bones action:crime` plot branch; quest **blink_wind_witness**.",
    },
    7: {
        "act": "Act II",
        "title": "Iron Debt",
        "news": "Logging scars and outlaw scent thread toward the old paper mill.",
        "mechanics": "Forest travel DC +2; `/pact action:forge` DC +2; cross-pack steal caught standing −2 extra.",
    },
    8: {
        "act": "Act II",
        "title": "Mill Tooth",
        "news": "Something ancient sleeps under the mill timbers; iron taste on every tongue.",
        "mechanics": "Successful `/explore investigate` may yield **Fossil Tooth** (+bones, standing); quest **blink_mill_scout**.",
    },
    9: {
        "act": "Act II",
        "title": "Memory Bites",
        "news": "Names of forgotten dead ride the howl; listeners flinch.",
        "mechanics": "Pack `/howl` costs −3 mood when pack unity < 5.",
    },
    10: {
        "act": "Act II",
        "title": "Blame Spiral",
        "news": "Treasury raids and cat truce cracks; every den blames another.",
        "mechanics": "All Great Pack unity −1 at sunrise; cat trust −2.",
    },
    11: {
        "act": "Act III",
        "title": "Ash Naming",
        "news": "Wolves gather at the river bend to put a name to what was buried.",
        "mechanics": "Quest **blink_ash_naming** (howl); creek drink +5 thirst for all; howl +1 unity bonus.",
    },
    12: {
        "act": "Act III",
        "title": "Pact Remembered",
        "news": "The river cools; cat clans and packs mark a fragile truce at the border stones.",
        "mechanics": "Cat trust +5 all active pacts; warm-river debuffs end; plot can reset to 0 when staff closes Book One.",
    },
}

WARM_RIVER_PHASES = frozenset(range(4, 11))
FISH_ROT_PHASES = frozenset(range(4, 9))
PARANOIA_PHASES = frozenset(range(6, 11))
MILL_PHASES = frozenset(range(8, 13))

SPLINTER_NAME = "Splinter"
FIREPAW_NAME = "Firepaw"
SOOT_NAME = "Soot"
RIVERSHROUD_NAME = "RiverShroud"
FINNPELT_NAME = "Finnpelt"

HEALER_PLOT_PHASES = frozenset(range(5, 12))
SOOT_PLOT_PHASES = frozenset(range(5, 12))

PACK_LABELS = {
    "thistlehide": "thistlehide",
    "silverrush": "silverrush",
    "mistmoor": "mistmoor",
    "greyspire": "Greyspire",
}


def _is_plot_wolf(user, canon_name: str) -> bool:
    return (user["wolf_name"] or "").strip().casefold() == canon_name.casefold()


def _thistlehide_canon_plot_active(user, guild_id: int, canon_name: str, role: str) -> bool:
    if plot_phase(guild_id) <= 0 or not _is_plot_wolf(user, canon_name):
        return False
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    if gp != "thistlehide":
        return False
    from engine.pack_leadership import wolf_role_key

    return wolf_role_key(user) == role


def rivershroud_plot_active(user, guild_id: int) -> bool:
    return _thistlehide_canon_plot_active(user, guild_id, RIVERSHROUD_NAME, "alpha")


def finnpelt_plot_active(user, guild_id: int) -> bool:
    return _thistlehide_canon_plot_active(user, guild_id, FINNPELT_NAME, "hunter")


def is_plot_healer_role(user) -> bool:
    from engine.role_features import has_any_role, is_full_medic

    return is_full_medic(user) or has_any_role(user, "medic_apprentice")


def increment_plot_sniff_quests(user, guild_id: int) -> None:
    """Progress phase-appropriate blink sniff quests (listen 1–5, witness 6+)."""
    from engine.plot_quests import plot_sniff_quest_keys

    keys = plot_sniff_quest_keys(guild_id)
    if not keys:
        return
    db.increment_quest_progress_by_keys(
        user["discord_id"], keys, wolf_id=user["id"], guild_id=guild_id
    )


def _plot_witness_available(user, day: int) -> bool:
    last = int(user["last_plot_witness_day"]) if "last_plot_witness_day" in user.keys() else 0
    return last < day


def _mark_plot_witness(user, day: int) -> None:
    db.update_user_by_id(user["id"], last_plot_witness_day=day)


def try_plot_witness(user, guild_id: int, day: int, *, action: str) -> str:
    """
    Once per sunrise: any wolf earns a small mood bump for living through The Blinking.
    """
    phase = plot_phase(guild_id)
    if phase <= 0 or not day or not _plot_witness_available(user, day):
        return ""
    from config import PLOT_WITNESS_MOOD

    meta = phase_meta(phase)
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    pack = PACK_LABELS.get(gp, "The den")
    title = meta["title"] if meta else f"phase {phase}"
    _mark_plot_witness(user, day)
    mood = db.adjust_mood(user["id"], PLOT_WITNESS_MOOD)
    action_hint = {
        "sniff": "scent on the wind",
        "howl": "voice in the howl",
        "drink": "creek under a bruised moon",
        "survey": "patrol on the ridge",
        "explore": "step into the unknown",
        "treat": "hands on a wound",
        "hunt": "jaws in the brush",
        "patrol": "paws on the border",
    }.get(action, "paw in the story")
    return (
        f"\n\n_**the blinking** — {pack}, **{title}**: you mark the sunrise "
        f"({action_hint}) · **+{PLOT_WITNESS_MOOD} mood** (now **{mood}**)._"
    )


def apply_plot_generic_healer_treat_rewards(
    healer,
    patient,
    *,
    guild_id: int,
    day: int,
) -> str:
    """Medics and apprentices (non-canon) earn healer quest credit and modest daily rewards."""
    if plot_phase(guild_id) not in HEALER_PLOT_PHASES:
        return ""
    if not is_plot_healer_role(healer):
        return ""
    if firepaw_plot_active(healer, guild_id) or soot_plot_active(healer, guild_id):
        return ""
    from config import PLOT_GENERIC_HEALER_MOOD, PLOT_GENERIC_HEALER_STANDING

    last = int(healer["last_plot_healer_day"]) if "last_plot_healer_day" in healer.keys() else 0
    if last >= day:
        return "\n\n_healer's work counts toward **blink_healer_touch**._"
    db.update_user_by_id(healer["id"], last_plot_healer_day=day)
    if healer["id"] != patient["id"]:
        kick = db.adjust_wolf_standing(healer["discord_id"], PLOT_GENERIC_HEALER_STANDING)
        if kick == "kicked":
            return "\n\n_the den needed your hands — but the pack casts you out._"
        return (
            f"\n\n_the blinking strains every shelf; your touch earns trust "
            f"(**+{PLOT_GENERIC_HEALER_STANDING} standing**). "
            "Counts toward **blink_healer_touch**._"
        )
    mood = db.adjust_mood(healer["id"], PLOT_GENERIC_HEALER_MOOD)
    return (
        f"\n\n_you steady yourself amid the pressure "
        f"(**+{PLOT_GENERIC_HEALER_MOOD} mood**, now **{mood}**). "
        "Counts toward **blink_healer_touch**._"
    )


def apply_plot_generic_healer_observe_rewards(medic, *, guild_id: int, day: int) -> str:
    if plot_phase(guild_id) not in HEALER_PLOT_PHASES:
        return ""
    if not is_plot_healer_role(medic):
        return ""
    if firepaw_plot_active(medic, guild_id) or soot_plot_active(medic, guild_id):
        return ""
    from config import PLOT_GENERIC_HEALER_MOOD

    mood = db.adjust_mood(medic["id"], PLOT_GENERIC_HEALER_MOOD)
    return (
        f"\n\n_**+{PLOT_GENERIC_HEALER_MOOD} mood** (now **{mood}**). "
        "apprentice hours count toward **blink_healer_touch**._"
    )


def plot_phase(guild_id: int) -> int:
    return db.get_plot_phase(guild_id)


def plot_is_active(guild_id: int) -> bool:
    return plot_phase(guild_id) > 0


def phase_meta(phase: int) -> dict[str, Any] | None:
    if phase <= 0 or phase > PLOT_MAX_PHASE:
        return None
    return PHASES[phase]


def plot_den_news_line(phase: int, day: int) -> str:
    meta = phase_meta(phase)
    if not meta:
        return ""
    return f"**the blinking** (phase {phase}, sunrise {day}); _{meta['news']}_"


def plot_status_fields(world) -> list[tuple[str, str, bool]]:
    phase = int(world["plot_phase"]) if "plot_phase" in world.keys() else 0
    if phase <= 0:
        return [
            (
                "plot",
                "book one is **off**. staff: `/setplotphase phase:1` to begin *the blinking*.",
                False,
            )
        ]
    meta = phase_meta(phase)
    if not meta:
        return []
    mech = meta["mechanics"]
    if phase < PLOT_MAX_PHASE:
        mech += f"\n\nstaff: `/plotadvance` or `/setplotphase` (now **{phase}/{PLOT_MAX_PHASE}**)."
    else:
        mech += "\n\nStaff: `/setplotphase phase:0` to end Book One."
    return [
        (f"{meta['act']}: {meta['title']}", meta["news"], False),
        ("mechanics", mech, False),
    ]


def apply_plot_rollover_effects(
    conn: sqlite3.Connection, guild_id: int, day: int, phase: int
) -> list[str]:
    """Sunrise plot pressure; returns den-wide note lines."""
    if phase <= 0:
        return []
    notes: list[str] = []

    if phase == 1:
        conn.execute(
            """
            UPDATE users
            SET mood = MAX(0, mood - 1)
            WHERE condition NOT IN ('dead', 'dying')
            """
        )
        notes.append("The bitten moon weighs on every wolf; **−1 mood**.")

    if phase in WARM_RIVER_PHASES:
        conn.execute(
            """
            UPDATE users
            SET thirst = MAX(0, thirst - 2)
            WHERE great_pack = 'silverrush'
              AND condition NOT IN ('dead', 'dying')
            """
        )
        notes.append("Silverrush wolves feel the warm river; **−2 thirst**.")

    if phase == 5:
        notes.extend(_mistmoor_silence_disease_pressure(conn))

    if phase in range(6, 10):
        _adjust_all_cat_trust(conn, guild_id, -3)

    if phase == 10:
        _adjust_all_cat_trust(conn, guild_id, -2)
        for key in GREAT_PACKS:
            pack = db.get_pack_by_key(key)
            if pack:
                outcome = db.adjust_pack_unity(pack["id"], -1)
                if outcome == "dissolved":
                    notes.append(f"**{pack['name']}** fractures under blame (**unity −5**).")
                else:
                    notes.append(f"**{pack['name']}** unity slips amid accusations (**−1**).")

    if phase == 12:
        _adjust_all_cat_trust(conn, guild_id, 5)
        notes.append("Active cat pacts gain **+5 trust** as borders cool.")

    if phase in FISH_ROT_PHASES:
        n = _accelerate_pack_fish_rot(conn, guild_id, day)
        if n:
            notes.append(f"warm water spoils **{n}** pack fish stack(s) early.")

    return notes


def _mistmoor_silence_disease_pressure(conn: sqlite3.Connection) -> list[str]:
    """low chance mistmoor wolves contract rot-lung when the belly falls silent."""
    from engine.diseases import encode_disease, spread_stage_for

    notes: list[str] = []
    rows = conn.execute(
        """
        SELECT id, wolf_name FROM users
        WHERE great_pack = 'mistmoor'
          AND (disease IS NULL OR disease = '')
          AND condition NOT IN ('dead', 'dying')
          AND pack_id IS NOT NULL
        """
    ).fetchall()
    for row in rows:
        if random.random() >= 0.05:
            continue
        encoded = encode_disease("rot_lung", spread_stage_for("rot_lung"))
        conn.execute("UPDATE users SET disease = ? WHERE id = ?", (encoded, row["id"]))
        notes.append(f"**{row['wolf_name']}**: rot-lung in the belly's silence.")
    if not notes:
        notes.append("Mistmoor dens hold their breath; disease pressure rises.")
    return notes


def _adjust_all_cat_trust(conn: sqlite3.Connection, guild_id: int, delta: int) -> None:
    if delta == 0:
        return
    rows = conn.execute(
        """
        SELECT pack_id, clan_name FROM pack_cat_pacts
        WHERE guild_id = ? AND status = 'active'
        """,
        (guild_id,),
    ).fetchall()
    for row in rows:
        db.adjust_cat_pact_trust(int(row["pack_id"]), row["clan_name"], delta)


def _accelerate_pack_fish_rot(conn: sqlite3.Connection, guild_id: int, day: int) -> int:
    from engine.prey_items import PREY_ROTTEN_GRACE_DAYS, prey_meta

    from config import PACK_STASH_ROT_BONUS_DAYS

    n = 0
    rows = conn.execute(
        "SELECT * FROM pack_prey_stacks WHERE guild_id = ? AND prey_key = 'fish'",
        (guild_id,),
    ).fetchall()
    for stack in rows:
        age = day - int(stack["acquired_day"])
        rot_days = prey_meta("fish").get("rot_days", 5) + PACK_STASH_ROT_BONUS_DAYS
        early = max(1, rot_days - 1)
        if age >= rot_days + PREY_ROTTEN_GRACE_DAYS:
            conn.execute("DELETE FROM pack_prey_stacks WHERE id = ?", (stack["id"],))
            n += 1
        elif age >= early and not stack["is_rotting"]:
            conn.execute(
                "UPDATE pack_prey_stacks SET is_rotting = 1 WHERE id = ?",
                (stack["id"],),
            )
            n += 1
    return n


def plot_activity_payout_mult(
    guild_id: int, activity: str, *, great_pack: str | None
) -> tuple[float, str]:
    """Return (multiplier, footer note) for hunt/fish/scavenge payouts."""
    phase = plot_phase(guild_id)
    if phase <= 0:
        return 1.0, ""
    gp = great_pack or ""
    if activity == "fishing" and phase in WARM_RIVER_PHASES:
        if gp == "silverrush":
            return 0.70, "blinking; warm silverrush water (**−30%** fish)."
        return 0.85, "blinking; river sickness (**−15%** fish)."
    if activity in ("hunt", "scavenge", "track") and phase == 3 and gp == "greyspire":
        return 1.10, "blinking; iron-scented ridge (**+10%** hunt)."
    return 1.0, ""


def plot_drink_thirst_bonus(guild_id: int, great_pack: str | None) -> tuple[int, str]:
    phase = plot_phase(guild_id)
    if phase == 11:
        return 5, "ash naming; the creek answers (**+5** thirst restore)."
    if phase in WARM_RIVER_PHASES and great_pack == "silverrush":
        return -3, "blinking; the creek runs unnaturally warm (**−3** thirst restore)."
    return 0, ""


def plot_travel_dc_bonus(guild_id: int, territory: str) -> int:
    phase = plot_phase(guild_id)
    if phase <= 0:
        return 0
    if phase == 3 and territory == "mountain":
        return 2
    if phase == 7 and territory == "forest":
        return 2
    if phase in MILL_PHASES and territory == "river":
        return 1
    return 0


def plot_cat_pact_forge_dc_bonus(guild_id: int) -> int:
    phase = plot_phase(guild_id)
    if phase in (6, 7, 10):
        return 2
    if phase == 12:
        return -2
    return 0


def plot_sniff_border_mult(guild_id: int) -> float:
    phase = plot_phase(guild_id)
    if phase in PARANOIA_PHASES:
        return 1.25
    return 1.0


def plot_cross_pack_caught_standing_extra(guild_id: int) -> int:
    return -2 if plot_phase(guild_id) == 7 else 0


def plot_howl_unity_bonus(guild_id: int, user=None) -> int:
    phase = plot_phase(guild_id)
    bonus = 1 if phase == 11 else 0
    if user and rivershroud_plot_active(user, guild_id) and phase in (9, 10, 11):
        from config import RIVERSHROUD_PLOT_HOWL_UNITY

        bonus += RIVERSHROUD_PLOT_HOWL_UNITY
    return bonus


def apply_plot_howl_mood_cost(user, pack, guild_id: int) -> tuple[int, str]:
    phase = plot_phase(guild_id)
    if phase != 9 or not pack:
        return 0, ""
    if rivershroud_plot_active(user, guild_id):
        return 0, "the alpha's antlers hold the line; your howl does not buckle (**memory bites** waived)."
    unity = int(pack["pack_unity"]) if "pack_unity" in pack.keys() else 5
    if unity >= 5:
        return 0, ""
    db.adjust_mood(user["id"], -3)
    return -3, "memory bites; fragile unity makes the howl hurt (**−3 mood**)."


def plot_thistlehide_patrol_standing_bonus(
    guild_id: int, great_pack: str | None, user=None
) -> int:
    bonus = 0
    if plot_phase(guild_id) == 2 and great_pack == "thistlehide":
        bonus += 1
    if user and great_pack == "thistlehide" and plot_phase(guild_id) in PARANOIA_PHASES:
        from config import FINNPELT_PLOT_PATROL_STANDING, RIVERSHROUD_PLOT_PATROL_STANDING
        from engine.pack_leadership import wolf_role_key

        role = wolf_role_key(user)
        if _is_plot_wolf(user, RIVERSHROUD_NAME) and role == "alpha":
            bonus += RIVERSHROUD_PLOT_PATROL_STANDING
        elif _is_plot_wolf(user, FINNPELT_NAME) and role == "hunter":
            bonus += FINNPELT_PLOT_PATROL_STANDING
    return bonus


def try_plot_mill_investigate(
    user,
    *,
    guild_id: int,
    day: int,
    success: bool,
) -> str:
    """Extra reward on successful investigate during mill phase."""
    phase = plot_phase(guild_id)
    if not success or phase not in MILL_PHASES:
        return ""
    if random.random() > 0.45:
        return ""
    bones = random.randint(15, 35)
    db.add_bones(user["discord_id"], bones, wolf_id=user["id"])
    standing = db.adjust_wolf_standing(user["discord_id"], 2)
    kick = f" standing **+2**" if standing != "kicked" else " (**cast out**)"
    return (
        f"\n\n_under the mill timbers you uncover a **fossil tooth** wrapped in rust._\n"
        f"**+{bones}** bones{kick}; report with `/world action:plot`."
    )


def firepaw_plot_active(user, guild_id: int) -> bool:
    if plot_phase(guild_id) <= 0 or not _is_plot_wolf(user, FIREPAW_NAME):
        return False
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    return gp == "thistlehide"


def firepaw_can_treat_patient(user, guild_id: int) -> bool:
    """medic apprentice firepaw may treat packmates during healer-plot phases."""
    return firepaw_plot_active(user, guild_id) and plot_phase(guild_id) in HEALER_PLOT_PHASES


def soot_plot_active(user, guild_id: int) -> bool:
    if plot_phase(guild_id) <= 0 or not _is_plot_wolf(user, SOOT_NAME):
        return False
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    return gp == "mistmoor"


def plot_firepaw_heal_bonus(healer, guild_id: int | None) -> int:
    if not guild_id or not firepaw_plot_active(healer, guild_id):
        return 0
    if plot_phase(guild_id) not in HEALER_PLOT_PHASES:
        return 0
    from config import FIREPAW_PLOT_TREAT_HEAL_BONUS

    return FIREPAW_PLOT_TREAT_HEAL_BONUS


def plot_soot_heal_bonus(healer, patient, guild_id: int | None) -> int:
    if not guild_id or not soot_plot_active(healer, guild_id):
        return 0
    if plot_phase(guild_id) not in SOOT_PLOT_PHASES:
        return 0
    from config import SOOT_PLOT_ROT_LUNG_HEAL_BONUS, SOOT_PLOT_TREAT_HEAL_BONUS
    from engine.diseases import parse_disease

    bonus = SOOT_PLOT_TREAT_HEAL_BONUS
    disease_raw = patient["disease"] if "disease" in patient.keys() else None
    key, _ = parse_disease(disease_raw)
    if key == "rot_lung":
        bonus += SOOT_PLOT_ROT_LUNG_HEAL_BONUS
    return bonus


def plot_healer_heal_bonus(healer, patient, guild_id: int | None) -> int:
    """stacked book one heal bonuses for canon healer wolves."""
    return plot_firepaw_heal_bonus(healer, guild_id) + plot_soot_heal_bonus(
        healer, patient, guild_id
    )


def _firepaw_daily_available(user, day: int) -> bool:
    last = int(user["last_firepaw_reward_day"]) if "last_firepaw_reward_day" in user.keys() else 0
    return last < day


def _mark_firepaw_daily(user, day: int) -> None:
    db.update_user_by_id(user["id"], last_firepaw_reward_day=day)


def _soot_daily_available(user, day: int) -> bool:
    last = int(user["last_soot_reward_day"]) if "last_soot_reward_day" in user.keys() else 0
    return last < day


def _mark_soot_daily(user, day: int) -> None:
    db.update_user_by_id(user["id"], last_soot_reward_day=day)


def _rivershroud_daily_available(user, day: int) -> bool:
    last = (
        int(user["last_rivershroud_reward_day"])
        if "last_rivershroud_reward_day" in user.keys()
        else 0
    )
    return last < day


def _mark_rivershroud_daily(user, day: int) -> None:
    db.update_user_by_id(user["id"], last_rivershroud_reward_day=day)


def _finnpelt_daily_available(user, day: int) -> bool:
    last = (
        int(user["last_finnpelt_reward_day"])
        if "last_finnpelt_reward_day" in user.keys()
        else 0
    )
    return last < day


def _mark_finnpelt_daily(user, day: int) -> None:
    db.update_user_by_id(user["id"], last_finnpelt_reward_day=day)


def apply_plot_rivershroud_sniff(user, guild_id: int, day: int) -> str:
    """Alpha border rewards for River'Shroud on /sniff during The Blinking."""
    if not rivershroud_plot_active(user, guild_id):
        return ""
    from config import (
        RIVERSHROUD_PLOT_SNIFF_MOOD_EARLY,
        RIVERSHROUD_PLOT_SNIFF_MOOD_LATE,
        RIVERSHROUD_PLOT_SNIFF_STANDING,
        SNIFF_HUNT_BONUS_PCT,
    )

    phase = plot_phase(guild_id)
    lines: list[str] = []

    if phase < 6:
        mood = db.adjust_mood(user["id"], RIVERSHROUD_PLOT_SNIFF_MOOD_EARLY)
        db.update_user(user["discord_id"], wolf_id=user["id"], sniff_bonus_day=day)
        lines.append(
            f"**+{RIVERSHROUD_PLOT_SNIFF_MOOD_EARLY} mood** (now **{mood}**)."
        )
        lines.append(
            f"**sniff bonus** active (**+{SNIFF_HUNT_BONUS_PCT}%** hunt/track); "
            "the border listens when the alpha stands watch."
        )
        return "\n\n_" + " ".join(lines) + "_"

    if phase in PARANOIA_PHASES:
        mood = db.adjust_mood(user["id"], RIVERSHROUD_PLOT_SNIFF_MOOD_LATE)
        db.update_user(user["discord_id"], wolf_id=user["id"], sniff_bonus_day=day)
        lines.append(
            f"**+{RIVERSHROUD_PLOT_SNIFF_MOOD_LATE} mood** (now **{mood}**). "
            f"**sniff bonus** active (**+{SNIFF_HUNT_BONUS_PCT}%** hunt/track)."
        )
        if _rivershroud_daily_available(user, day):
            _mark_rivershroud_daily(user, day)
            kick = db.adjust_wolf_standing(
                user["discord_id"], RIVERSHROUD_PLOT_SNIFF_STANDING
            )
            standing_note = (
                f"**+{RIVERSHROUD_PLOT_SNIFF_STANDING} standing**"
                if kick != "kicked"
                else "**cast out**"
            )
            lines.append(f"antlered alpha on the ridge — {standing_note}.")
    return ("\n\n_" + " ".join(lines) + "_") if lines else ""


def apply_plot_finnpelt_sniff(user, guild_id: int, day: int) -> str:
    """Hunter ridge rewards for Finnpelt on /sniff during Border Paranoia+."""
    if not finnpelt_plot_active(user, guild_id):
        return ""
    from config import (
        FINNPELT_PLOT_SNIFF_MOOD,
        FINNPELT_PLOT_SNIFF_STANDING,
        SNIFF_HUNT_BONUS_PCT,
    )

    phase = plot_phase(guild_id)
    if phase not in PARANOIA_PHASES:
        return ""
    lines: list[str] = []

    mood = db.adjust_mood(user["id"], FINNPELT_PLOT_SNIFF_MOOD)
    db.update_user(user["discord_id"], wolf_id=user["id"], sniff_bonus_day=day)
    lines.append(f"**+{FINNPELT_PLOT_SNIFF_MOOD} mood** (now **{mood}**).")
    lines.append(
        f"**sniff bonus** active (**+{SNIFF_HUNT_BONUS_PCT}%** hunt/track); "
        "greyspire line mapped muscle by muscle."
    )
    if _finnpelt_daily_available(user, day):
        _mark_finnpelt_daily(user, day)
        kick = db.adjust_wolf_standing(user["discord_id"], FINNPELT_PLOT_SNIFF_STANDING)
        standing_note = (
            f"**+{FINNPELT_PLOT_SNIFF_STANDING} standing**"
            if kick != "kicked"
            else "**cast out**"
        )
        lines.append(f"ridge held without the crown — {standing_note}.")
    return "\n\n_" + " ".join(lines) + "_"


def apply_plot_firepaw_sniff(user, guild_id: int, day: int) -> str:
    """real rewards for firepaw on /sniff during the blinking."""
    if not firepaw_plot_active(user, guild_id):
        return ""
    from config import (
        FIREPAW_PLOT_SNIFF_MOOD_EARLY,
        FIREPAW_PLOT_SNIFF_MOOD_LATE,
        FIREPAW_PLOT_SNIFF_STANDING,
        SNIFF_HUNT_BONUS_PCT,
    )

    phase = plot_phase(guild_id)
    lines: list[str] = []

    if phase < 6:
        mood = db.adjust_mood(user["id"], FIREPAW_PLOT_SNIFF_MOOD_EARLY)
        db.update_user(user["discord_id"], wolf_id=user["id"], sniff_bonus_day=day)
        lines.append(
            f"**+{FIREPAW_PLOT_SNIFF_MOOD_EARLY} mood** (now **{mood}**)."
        )
        lines.append(
            f"**sniff bonus** active (**+{SNIFF_HUNT_BONUS_PCT}%** hunt/track); "
            "your ears map the wind."
        )
        return "\n\n_" + " ".join(lines) + "_"

    if phase in PARANOIA_PHASES and _firepaw_daily_available(user, day):
        _mark_firepaw_daily(user, day)
        mood = db.adjust_mood(user["id"], FIREPAW_PLOT_SNIFF_MOOD_LATE)
        kick = db.adjust_wolf_standing(user["discord_id"], FIREPAW_PLOT_SNIFF_STANDING)
        standing_note = (
            f"**+{FIREPAW_PLOT_SNIFF_STANDING} standing**"
            if kick != "kicked"
            else "**cast out**"
        )
        lines.append(
            f"border mapped by ear — {standing_note} · **+{FIREPAW_PLOT_SNIFF_MOOD_LATE} mood** "
            f"(now **{mood}**)."
        )
    return ("\n\n_" + " ".join(lines) + "_") if lines else ""


def apply_plot_soot_sniff(user, guild_id: int, day: int) -> str:
    """Mistmoor second-sight rewards for Soot on /sniff during Belly Silence+."""
    if not soot_plot_active(user, guild_id):
        return ""
    from config import (
        SNIFF_HUNT_BONUS_PCT,
        SOOT_PLOT_SNIFF_MOOD,
        SOOT_PLOT_SNIFF_STANDING,
    )

    phase = plot_phase(guild_id)
    if phase not in SOOT_PLOT_PHASES:
        return ""
    lines: list[str] = []

    mood = db.adjust_mood(user["id"], SOOT_PLOT_SNIFF_MOOD)
    db.update_user(user["discord_id"], wolf_id=user["id"], sniff_bonus_day=day)
    lines.append(f"**+{SOOT_PLOT_SNIFF_MOOD} mood** (now **{mood}**).")
    lines.append(
        f"**sniff bonus** active (**+{SNIFF_HUNT_BONUS_PCT}%** hunt/track); "
        "mist-light and insect drift show paths others miss."
    )

    if phase in PARANOIA_PHASES and _soot_daily_available(user, day):
        _mark_soot_daily(user, day)
        kick = db.adjust_wolf_standing(user["discord_id"], SOOT_PLOT_SNIFF_STANDING)
        standing_note = (
            f"**+{SOOT_PLOT_SNIFF_STANDING} standing**"
            if kick != "kicked"
            else "**cast out**"
        )
        lines.append(
            f"mirewort's second sight on the border — {standing_note}."
        )
    return "\n\n_" + " ".join(lines) + "_"


def apply_plot_firepaw_treat_rewards(
    healer,
    patient,
    *,
    guild_id: int,
    day: int,
) -> str:
    """Standing, mood, and quest credit for Firepaw treatments during The Blinking."""
    if not firepaw_plot_active(healer, guild_id):
        return ""
    from config import (
        FIREPAW_PLOT_TREAT_HEAL_BONUS,
        FIREPAW_PLOT_TREAT_MOOD_SELF,
        FIREPAW_PLOT_TREAT_STANDING,
    )

    phase = plot_phase(guild_id)
    lines: list[str] = []

    if phase in HEALER_PLOT_PHASES:
        lines.append(
            f"plot heal bonus: **+{FIREPAW_PLOT_TREAT_HEAL_BONUS} hp** on healing outcomes."
        )

    if _firepaw_daily_available(healer, day) and phase in HEALER_PLOT_PHASES:
        _mark_firepaw_daily(healer, day)
        if healer["id"] != patient["id"]:
            kick = db.adjust_wolf_standing(
                healer["discord_id"], FIREPAW_PLOT_TREAT_STANDING
            )
            if kick == "kicked":
                lines.append("sypha's den trusts your touch — but the pack casts you out.")
            else:
                lines.append(
                    f"sypha's den trusts your touch (**+{FIREPAW_PLOT_TREAT_STANDING} standing**)."
                )
        else:
            mood = db.adjust_mood(healer["id"], FIREPAW_PLOT_TREAT_MOOD_SELF)
            lines.append(
                f"scent and touch steady you (**+{FIREPAW_PLOT_TREAT_MOOD_SELF} mood**, "
                f"now **{mood}**)."
            )

    if phase == 11:
        lines.append("ash naming at the creek; each wound closed is a name remembered.")
    elif phase in MILL_PHASES:
        lines.append("mill-road injuries keep the shelves bare; iron-scent on every paw.")

    return ("\n\n" + "\n".join(lines)) if lines else ""


def apply_plot_soot_treat_rewards(
    healer,
    patient,
    *,
    guild_id: int,
    day: int,
) -> str:
    """Standing, mood, and quest credit for Soot treatments during The Blinking."""
    if not soot_plot_active(healer, guild_id):
        return ""
    from config import (
        SOOT_PLOT_ROT_LUNG_HEAL_BONUS,
        SOOT_PLOT_TREAT_HEAL_BONUS,
        SOOT_PLOT_TREAT_MOOD_SELF,
        SOOT_PLOT_TREAT_STANDING,
    )
    from engine.diseases import parse_disease

    phase = plot_phase(guild_id)
    if phase not in SOOT_PLOT_PHASES:
        return ""
    lines: list[str] = []

    heal_note = f"**+{SOOT_PLOT_TREAT_HEAL_BONUS} hp** on healing outcomes"
    disease_raw = patient["disease"] if "disease" in patient.keys() else None
    key, _ = parse_disease(disease_raw)
    if key == "rot_lung":
        heal_note += f" (**+{SOOT_PLOT_ROT_LUNG_HEAL_BONUS}** more for rot-lung)"
    lines.append(f"plot heal bonus: {heal_note}.")

    if _soot_daily_available(healer, day):
        _mark_soot_daily(healer, day)
        if healer["id"] != patient["id"]:
            kick = db.adjust_wolf_standing(
                healer["discord_id"], SOOT_PLOT_TREAT_STANDING
            )
            if kick == "kicked":
                lines.append("mirewort's den trusts your hands — but the pack casts you out.")
            else:
                lines.append(
                    f"mirewort's den trusts your hands (**+{SOOT_PLOT_TREAT_STANDING} standing**)."
                )
        else:
            mood = db.adjust_mood(healer["id"], SOOT_PLOT_TREAT_MOOD_SELF)
            lines.append(
                f"swamp mist steadies you (**+{SOOT_PLOT_TREAT_MOOD_SELF} mood**, "
                f"now **{mood}**)."
            )

    if phase == 5:
        lines.append("the belly falls silent; rot-lung walks the reeds — your litter's ghost in every wheeze.")
    elif phase == 11:
        lines.append("ash naming at the creek; each fever cooled is a name remembered.")
    return ("\n\n" + "\n".join(lines)) if lines else ""


def apply_plot_firepaw_observe_rewards(medic, *, guild_id: int, day: int) -> str:
    if not firepaw_plot_active(medic, guild_id):
        return ""
    from config import FIREPAW_PLOT_OBSERVE_MOOD, FIREPAW_PLOT_OBSERVE_STRAIN_RELIEF
    from engine.character_traits import (
        encode_skill_strain_state,
        parse_skill_strain_state,
    )

    phase = plot_phase(guild_id)
    if phase not in HEALER_PLOT_PHASES:
        return ""

    mood = db.adjust_mood(medic["id"], FIREPAW_PLOT_OBSERVE_MOOD)

    strain_note = ""
    state = parse_skill_strain_state(
        medic["trait_failure_days"] if "trait_failure_days" in medic.keys() else "{}"
    )
    entry = state.get("medicine")
    if entry and int(entry.get("strain", 0)) > 0:
        entry["strain"] = max(
            0, int(entry["strain"]) - FIREPAW_PLOT_OBSERVE_STRAIN_RELIEF
        )
        if entry["strain"] <= 0:
            state.pop("medicine", None)
        else:
            state["medicine"] = entry
        db.update_user_by_id(
            medic["id"], trait_failure_days=encode_skill_strain_state(state)
        )
        strain_note = f" medicine strain **−{FIREPAW_PLOT_OBSERVE_STRAIN_RELIEF}**."

    return (
        f"\n\n**+{FIREPAW_PLOT_OBSERVE_MOOD} mood** (now **{mood}**). "
        f"apprentice hours count toward **blink_healer_touch**.{strain_note}"
    )


def apply_plot_soot_observe_rewards(medic, *, guild_id: int, day: int) -> str:
    if not soot_plot_active(medic, guild_id):
        return ""
    from config import SOOT_PLOT_OBSERVE_MOOD, SOOT_PLOT_OBSERVE_STRAIN_RELIEF
    from engine.character_traits import (
        encode_skill_strain_state,
        parse_skill_strain_state,
    )

    phase = plot_phase(guild_id)
    if phase not in SOOT_PLOT_PHASES:
        return ""

    mood = db.adjust_mood(medic["id"], SOOT_PLOT_OBSERVE_MOOD)

    strain_note = ""
    state = parse_skill_strain_state(
        medic["trait_failure_days"] if "trait_failure_days" in medic.keys() else "{}"
    )
    entry = state.get("medicine")
    if entry and int(entry.get("strain", 0)) > 0:
        entry["strain"] = max(
            0, int(entry["strain"]) - SOOT_PLOT_OBSERVE_STRAIN_RELIEF
        )
        if entry["strain"] <= 0:
            state.pop("medicine", None)
        else:
            state["medicine"] = entry
        db.update_user_by_id(
            medic["id"], trait_failure_days=encode_skill_strain_state(state)
        )
        strain_note = f" medicine strain **−{SOOT_PLOT_OBSERVE_STRAIN_RELIEF}**."

    return (
        f"\n\n**+{SOOT_PLOT_OBSERVE_MOOD} mood** (now **{mood}**). "
        f"mirewort's ward counts toward **blink_healer_touch**.{strain_note}"
    )


def try_plot_sniff_extras(user, guild_id: int, *, day: int = 0) -> str:
    phase = plot_phase(guild_id)
    if phase <= 0:
        return ""
    if day:
        increment_plot_sniff_quests(user, guild_id)
    healer_blocks: list[str] = []
    if day:
        firepaw_block = apply_plot_firepaw_sniff(user, guild_id, day)
        soot_block = apply_plot_soot_sniff(user, guild_id, day)
        rivershroud_block = apply_plot_rivershroud_sniff(user, guild_id, day)
        finnpelt_block = apply_plot_finnpelt_sniff(user, guild_id, day)
        for block in (firepaw_block, soot_block, rivershroud_block, finnpelt_block):
            if block:
                healer_blocks.append(block.strip().strip("_"))
    else:
        firepaw_block = ""
        soot_block = ""
    witness = try_plot_witness(user, guild_id, day, action="sniff") if day else ""
    if phase < 6:
        parts = []
        if healer_blocks:
            parts.append("_" + " ".join(healer_blocks) + "_")
        if witness:
            parts.append(witness)
        return "".join(parts) if parts else (firepaw_block or soot_block)
    lines: list[str] = []
    if phase in PARANOIA_PHASES and random.random() < 0.22:
        lines.append(
            "_limp rogue scent on the border — three-legged gait, fish-grease and guilt._"
        )
    if _is_plot_wolf(user, SPLINTER_NAME):
        lines.append("_your own trail doubles back; even you are not sure who you are stealing for._")
    if healer_blocks:
        lines.extend(healer_blocks)
    elif _is_plot_wolf(user, FIREPAW_NAME) and phase in PARANOIA_PHASES:
        lines.append("_you map patrol gait and rogue limp on the wind before any wolf speaks it._")
    elif _is_plot_wolf(user, SOOT_NAME) and phase in PARANOIA_PHASES:
        lines.append(
            "_mismatched eyes catch reed-shift and fever-breath on the border before patrol speaks it._"
        )
    if witness:
        lines.append(witness.strip())
    return ("\n\n" + "\n".join(lines)) if lines else witness


def try_plot_rogue_crime(
    interaction,
    user,
    *,
    day: int,
    gross: int,
) -> tuple[int, str, str | None]:
    """
    Rogue / loner crime during Border Paranoia+.
    Returns (gross_override or same, body_suffix, caught_override_message).
    """
    from engine.role_features import is_rogue_wolf

    guild_id = interaction.guild.id
    phase = plot_phase(guild_id)
    if phase < 6 or not is_rogue_wolf(user):
        return gross, "", None

    name = user["wolf_name"] or "rogue"
    is_splinter = name.lower() == SPLINTER_NAME.lower()

    if random.random() < 0.18:
        penalty = -4 if is_splinter else -3
        kick = db.adjust_wolf_standing(interaction.user.id, penalty)
        caught = (
            f"**{name}** is cornered on the **silverrush** shallows — patrol scent, no escape.\n"
            if is_splinter
            else f"border patrol catches **{name}** red-pawed at a rival mark.\n"
        )
        if kick == "kicked":
            caught += "**Cast out** as loner."
        else:
            caught += f"standing **{penalty}**."
        return 0, "", caught

    bonus = random.randint(4, 12) if is_splinter else random.randint(2, 8)
    new_gross = gross + bonus
    suffix = (
        f"\n\n_edge theft during **the blinking**; you slip away with **+{bonus}** extra bones "
        f"from the warm shallows._"
        if is_splinter
        else f"\n\n_paranoid borders make easy marks; **+{bonus}** extra bones._"
    )
    if is_splinter and random.random() < 0.15:
        db.adjust_mood(user["id"], -2)
        suffix += "\n_Guilt for the wolf you killed seasons ago gnaws louder than hunger (**−2 mood**)._"
    return new_gross, suffix, None


def try_plot_treat_extras(healer, patient, *, guild_id: int, day: int = 0) -> str:
    if not day:
        world = db.get_world(guild_id)
        day = int(world["day_number"])
    parts = [
        apply_plot_firepaw_treat_rewards(healer, patient, guild_id=guild_id, day=day),
        apply_plot_soot_treat_rewards(healer, patient, guild_id=guild_id, day=day),
        apply_plot_generic_healer_treat_rewards(
            healer, patient, guild_id=guild_id, day=day
        ),
        try_plot_witness(healer, guild_id, day, action="treat"),
    ]
    return "".join(part for part in parts if part)


def try_plot_observe_extras(medic, *, guild_id: int, day: int = 0) -> str:
    if not day:
        world = db.get_world(guild_id)
        day = int(world["day_number"])
    parts = [
        apply_plot_firepaw_observe_rewards(medic, guild_id=guild_id, day=day),
        apply_plot_soot_observe_rewards(medic, guild_id=guild_id, day=day),
        apply_plot_generic_healer_observe_rewards(medic, guild_id=guild_id, day=day),
        try_plot_witness(medic, guild_id, day, action="treat"),
    ]
    return "".join(part for part in parts if part)
