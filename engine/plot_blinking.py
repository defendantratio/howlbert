"""Book One: The Blinking; plot phases with mechanical pressure (not lore-only)."""

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
        "mechanics": "Silverrush hydration −2 extra at sunrise; fishing −25%; pack fish rot 1 day faster.",
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
        "mechanics": "Quest **blink_ash_naming** (howl); creek drink +5 hydration for all; howl +1 unity bonus.",
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
MAGGOTBRAIN_NAME = "MaggotBrain"
VULCAN_NAME = "Vulcan Stonehide"
RIME_NAME = "Rime"
ROOT_NAME = "Root"
FROSTBURN_NAME = "Frostburn"
HOLLOWSTEM_NAME = "Hollowstem"
PUDDLEBANE_NAME = "Puddlebane"
GASP_NAME = "Gasp"
MIREWORT_NAME = "mirewort"
DRIFTPUP_NAME = "Driftpup"
PALESTEP_NAME = "Pale'Step"
BRACKENPELT_NAME = "Brackenpelt"
ICEFANG_NAME = "Icefang"
HEMLOCK_NAME = "Hemlock"
RIPPLE_NAME = "Ripple"
SYPHA_NAME = "Sypha"
MURKVEIN_NAME = "Murkvein"
AROMIS_NAME = "Aromis"
LUCID_NAME = "Lucid"
CLOVERFERN_NAME = "Cloverfern"
KANAMI_NAME = "Kanami"
SKYE_NAME = "Skye"
IRONJAW_NAME = "Ironjaw"
SLATE_NAME = "Slate"
SLUDGE_NAME = "Sludge"
CROAKER_NAME = "Croaker"
CURLGRIP_NAME = "Curlgrip"
MOSSGAZE_NAME = "Mossgaze"
THORN_NAME = "Thorn"
RIFT_NAME = "Rift"
SALTMUZZLE_NAME = "Saltmuzzle"
GRIM_NAME = "Grim"
STONEPIERCER_NAME = "Stonepiercer"
MOTH_NAME = "Moth"
SLEET_NAME = "Sleet"
PEBBLE_NAME = "Pebble"
REEDWHISPER_NAME = "Reedwhisper"
ASHBARK_NAME = "Ashbark"
CINDER_NAME = "Cinder"
ROTTEDDUST_NAME = "Rotteddust"
RIVENMAW_NAME = "Rivenmaw"
DUSK_NAME = "Dusk"
SCAB_NAME = "Scab"
TALUS_NAME = "Talus"
RAVEN_NAME = "Raven"
EBB_NAME = "Ebb"
YARROW_NAME = "Yarrow"
MOSSHEART_NAME = "Mossheart"
FERNSPOT_NAME = "Fernspot"
BARKHOLLOW_NAME = "Barkhollow"
MUDNOSE_NAME = "Mudnose"
THYME_NAME = "Thyme"
# named Book One pups; each grows a little steadier for living through the blinking
PLOT_PUP_NAMES = ("Cinderpup", "Harepup", "Ripplepup", "Mosspup", "Mudpup")

HEALER_PLOT_PHASES = frozenset(range(5, 12))
SOOT_PLOT_PHASES = frozenset(range(5, 12))
MAGGOTBRAIN_PLOT_PHASES = frozenset(range(5, 11))

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


def _mistmoor_canon_plot_active(user, guild_id: int, canon_name: str, role: str) -> bool:
    if plot_phase(guild_id) <= 0 or not _is_plot_wolf(user, canon_name):
        return False
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    if gp != "mistmoor":
        return False
    from engine.pack_leadership import wolf_role_key

    return wolf_role_key(user) == role


def maggotbrain_plot_active(user, guild_id: int) -> bool:
    return _mistmoor_canon_plot_active(user, guild_id, MAGGOTBRAIN_NAME, "hunter")


def _silverrush_canon_plot_active(user, guild_id: int, canon_name: str, role: str) -> bool:
    if plot_phase(guild_id) <= 0 or not _is_plot_wolf(user, canon_name):
        return False
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    if gp != "silverrush":
        return False
    from engine.pack_leadership import wolf_role_key

    return wolf_role_key(user) == role




def is_plot_healer_role(user) -> bool:
    from engine.role_features import has_any_role, is_full_medic

    return is_full_medic(user) or has_any_role(user, "medic_apprentice")


def increment_plot_sniff_quests(user, guild_id: int) -> None:
    """Progress phase-appropriate blink sniff quests (listen 1 to 5, witness 6+)."""
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
        f"\n\n_**the blinking**; {pack}, **{title}**: you mark the sunrise "
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
        kick = db.adjust_wolf_standing_by_id(healer["id"], PLOT_GENERIC_HEALER_STANDING)
        if kick == "kicked":
            return "\n\n_the den needed your hands; but the pack casts you out._"
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




def phase_meta(phase: int) -> dict[str, Any] | None:
    if phase <= 0 or phase > PLOT_MAX_PHASE:
        return None
    return PHASES[phase]


def plot_den_news_line(phase: int, day: int) -> str:
    meta = phase_meta(phase)
    if not meta:
        return ""
    return f"**the blinking** (phase {phase}, sunrise {day}); _{meta['news']}_"


def next_blinking_prompt_line(guild_id: int, phase: int) -> str:
    """The phase's rp scene prompt for this sunrise, walked in order (one per
    rollover, restarting at the first prompt when the phase advances)."""
    from engine.rp_prompts import BLINKING_PROMPTS

    prompts = BLINKING_PROMPTS.get(phase)
    if not prompts:
        return ""
    idx = db.next_plot_prompt_index(guild_id)
    return f"**the blinking; scene prompt**: _{prompts[idx % len(prompts)]}_"


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


def _named_wolf_blink_presence(conn: sqlite3.Connection, day: int) -> str:
    """
    Every canonical named wolf is part of Book One, not just the handful with
    deep bespoke lanes (Soot, Finnpelt, RiverShroud, Firepaw, MaggotBrain); a
    small, real mood lift for whoever is currently playing a canon name while
    the plot runs, plus an occasional den-news name-drop, so the rest of the
    canon roster isn't purely decorative once the plot goes live.
    """
    from config import NAMED_WOLF_BLINK_MOOD
    from engine.character_lore_data import CHARACTER_LORE_BY_NAME

    canon_lower = [name.lower() for name in CHARACTER_LORE_BY_NAME]
    if not canon_lower:
        return ""
    placeholders = ", ".join("?" for _ in canon_lower)
    rows = conn.execute(
        f"""
        SELECT id, wolf_name FROM users
        WHERE LOWER(wolf_name) IN ({placeholders})
          AND condition NOT IN ('dead', 'dying')
          AND (last_named_wolf_blink_day IS NULL OR last_named_wolf_blink_day < ?)
        """,
        (*canon_lower, day),
    ).fetchall()
    if not rows:
        return ""
    ids = [row["id"] for row in rows]
    id_placeholders = ", ".join("?" for _ in ids)
    conn.execute(
        f"""
        UPDATE users
        SET mood = MIN(100, mood + ?), last_named_wolf_blink_day = ?
        WHERE id IN ({id_placeholders})
        """,
        (NAMED_WOLF_BLINK_MOOD, day, *ids),
    )

    spotlight = random.choice(rows)
    raw = next(
        (raw for key, raw in CHARACTER_LORE_BY_NAME.items() if key.lower() == spotlight["wolf_name"].lower()),
        None,
    )
    blurb = ""
    if raw:
        from engine.character_lore import parse_character_lore

        lore = parse_character_lore(raw) or {}
        personality = lore.get("personality", "")
        blurb = personality.split(".")[0].strip()
    if blurb:
        return f"**{spotlight['wolf_name']}** is felt in the blinking: _{blurb}._"
    return f"**{spotlight['wolf_name']}** is felt in the blinking."


def apply_plot_rollover_effects(
    conn: sqlite3.Connection, guild_id: int, day: int, phase: int
) -> list[str]:
    """Sunrise plot pressure; returns den-wide note lines."""
    if phase <= 0:
        return []
    notes: list[str] = []

    if phase == 1:
        # a pup guardian in the den spares that pack's pups the moon's weight.
        guardians: dict[str, str] = {}
        for name, pack in (
            (RIME_NAME, "greyspire"),
            (FROSTBURN_NAME, "greyspire"),
            (ROOT_NAME, "thistlehide"),
        ):
            if pack in guardians:
                continue
            watching = conn.execute(
                """
                SELECT 1 FROM users
                WHERE LOWER(wolf_name) = LOWER(?)
                  AND great_pack = ?
                  AND condition NOT IN ('dead', 'dying')
                LIMIT 1
                """,
                (name, pack),
            ).fetchone()
            if watching:
                guardians[pack] = name
        shielded_packs = list(guardians.keys())
        if shielded_packs:
            placeholders = ", ".join("?" for _ in shielded_packs)
            conn.execute(
                f"""
                UPDATE users
                SET mood = MAX(0, mood - 1)
                WHERE condition NOT IN ('dead', 'dying')
                  AND NOT (wolf_role = 'pup' AND great_pack IN ({placeholders}))
                """,
                tuple(shielded_packs),
            )
        else:
            conn.execute(
                """
                UPDATE users
                SET mood = MAX(0, mood - 1)
                WHERE condition NOT IN ('dead', 'dying')
                """
            )
        notes.append("The bitten moon weighs on every wolf; **−1 mood**.")
        for pack, name in guardians.items():
            notes.append(f"**{name}** keeps the {pack.capitalize()} pups close; they are spared the moon's weight.")

    # Hollowstem gathers the Mistmoor pups close through the blinking (any phase).
    hollowstem = conn.execute(
        """
        SELECT 1 FROM users
        WHERE LOWER(wolf_name) = LOWER(?)
          AND great_pack = 'mistmoor'
          AND condition NOT IN ('dead', 'dying')
        LIMIT 1
        """,
        (HOLLOWSTEM_NAME,),
    ).fetchone()
    if hollowstem:
        conn.execute(
            """
            UPDATE users
            SET mood = MIN(100, mood + 2)
            WHERE great_pack = 'mistmoor'
              AND wolf_role = 'pup'
              AND condition NOT IN ('dead', 'dying')
            """
        )
        notes.append("**Hollowstem** gathers the Mistmoor pups close; the youngest feel safe, **+2 mood**.")

    # named wolves who steady themselves through the blinking.
    #   (name, pack or None for any, mood, only_phase or None, flavor)
    from config import PLOT_PUP_MOOD

    mood_lanes = [
        (PUDDLEBANE_NAME, "mistmoor", 2, None, "**Puddlebane** works the bog with quiet purpose; **+2 mood**."),
        (GASP_NAME, "mistmoor", 3, 5, "**Gasp** feels the belly-rip go quiet and grows calm as the others fret; **+3 mood**."),
    ]
    # named plot pups grow a little steadier for living through the blinking.
    for pup in PLOT_PUP_NAMES:
        mood_lanes.append((pup, None, PLOT_PUP_MOOD, None, f"**{pup}** weathers another sunrise of the blinking; **+{PLOT_PUP_MOOD} mood**."))
    for name, pack, amt, only_phase, flavor in mood_lanes:
        if only_phase is not None and phase != only_phase:
            continue
        if pack:
            row = conn.execute(
                "SELECT id FROM users WHERE LOWER(wolf_name) = LOWER(?) AND great_pack = ? "
                "AND condition NOT IN ('dead', 'dying') LIMIT 1",
                (name, pack),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM users WHERE LOWER(wolf_name) = LOWER(?) "
                "AND condition NOT IN ('dead', 'dying') LIMIT 1",
                (name,),
            ).fetchone()
        if row:
            conn.execute("UPDATE users SET mood = MIN(100, mood + ?) WHERE id = ?", (amt, row["id"]))
            notes.append(flavor)

    # Dusk (mistmoor beta) turns up a hidden cache some sunrises.
    dusk = conn.execute(
        "SELECT id FROM users WHERE LOWER(wolf_name) = LOWER(?) AND great_pack = 'mistmoor' "
        "AND condition NOT IN ('dead', 'dying') LIMIT 1",
        (DUSK_NAME,),
    ).fetchone()
    if dusk:
        from config import DUSK_PLOT_CACHE_BONES, DUSK_PLOT_CACHE_CHANCE
        if random.random() < DUSK_PLOT_CACHE_CHANCE:
            conn.execute("UPDATE users SET bones = bones + ? WHERE id = ?", (DUSK_PLOT_CACHE_BONES, int(dusk["id"])))
            notes.append(f"**Dusk** noses out a hidden cache in the reeds; **+{DUSK_PLOT_CACHE_BONES} bones**.")

    if phase in WARM_RIVER_PHASES:
        vulcan_watching = conn.execute(
            """
            SELECT 1 FROM users
            WHERE LOWER(wolf_name) = LOWER(?)
              AND great_pack = 'silverrush'
              AND wolf_role = 'hunter'
              AND condition NOT IN ('dead', 'dying')
            LIMIT 1
            """,
            (VULCAN_NAME,),
        ).fetchone()
        pup_shield = " AND wolf_role != 'pup'" if vulcan_watching else ""
        conn.execute(
            f"""
            UPDATE users
            SET thirst = MAX(0, thirst - 2)
            WHERE great_pack = 'silverrush'
              AND condition NOT IN ('dead', 'dying')
              {pup_shield}
            """
        )
        notes.append("Silverrush wolves feel the warm river; **−2 hydration**.")
        if vulcan_watching:
            notes.append(
                "**Vulcan Stonehide** keeps watch over the den's youngest; Silverrush pups are spared the hydration."
            )
        driftpup = conn.execute(
            """
            SELECT id FROM users
            WHERE LOWER(wolf_name) = LOWER(?)
              AND great_pack = 'silverrush'
              AND condition NOT IN ('dead', 'dying')
            LIMIT 1
            """,
            (DRIFTPUP_NAME,),
        ).fetchone()
        if driftpup:
            conn.execute(
                "UPDATE users SET mood = MIN(100, mood + 1) WHERE id = ?",
                (driftpup["id"],),
            )
            notes.append(
                "**Driftpup** keeps carrying stones across the warm shallows, proving himself stone by stone; **+1 mood**."
            )

    if phase == 5:
        notes.extend(_mistmoor_silence_disease_pressure(conn))

    if phase in range(6, 10):
        _adjust_all_cat_trust(conn, guild_id, -3)

    if phase == 10:
        _adjust_all_cat_trust(conn, guild_id, -2)
        # a steady alpha holds their den together through the blame spiral.
        unity_mitigators = {"silverrush": SALTMUZZLE_NAME, "mistmoor": MURKVEIN_NAME}
        for key in GREAT_PACKS:
            pack = db.get_pack_by_key(key)
            if not pack:
                continue
            mitigator = unity_mitigators.get(key)
            if mitigator:
                held = conn.execute(
                    """
                    SELECT 1 FROM users
                    WHERE great_pack = ? AND LOWER(wolf_name) = LOWER(?)
                      AND condition NOT IN ('dead', 'dying') LIMIT 1
                    """,
                    (key, mitigator),
                ).fetchone()
                if held:
                    notes.append(f"**{mitigator}** holds **{pack['name']}** together through the blame; unity steady.")
                    continue
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

    named_note = _named_wolf_blink_presence(conn, day)
    if named_note:
        notes.append(named_note)

    return notes


def _mistmoor_silence_disease_pressure(conn: sqlite3.Connection) -> list[str]:
    """low chance mistmoor wolves contract rot-lung when the belly falls silent."""
    from engine.diseases import encode_disease, spread_stage_for

    notes: list[str] = []
    mirewort_tending = conn.execute(
        """
        SELECT 1 FROM users
        WHERE LOWER(wolf_name) = LOWER(?)
          AND great_pack = 'mistmoor'
          AND condition NOT IN ('dead', 'dying')
        LIMIT 1
        """,
        (MIREWORT_NAME,),
    ).fetchone()
    chance = 0.03 if mirewort_tending else 0.05
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
        if random.random() >= chance:
            continue
        encoded = encode_disease("rot_lung", spread_stage_for("rot_lung"))
        conn.execute("UPDATE users SET disease = ? WHERE id = ?", (encoded, row["id"]))
        notes.append(f"**{row['wolf_name']}**: rot-lung in the belly's silence.")
    if not notes:
        notes.append("Mistmoor dens hold their breath; disease pressure rises.")
    if mirewort_tending:
        notes.append("**mirewort** works the swamp's medicine against the silence; the worst of it is held back.")
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
        pack_id = int(row["pack_id"])
        pack_delta = delta
        # Sleet (greyspire diplomat) softens the paranoia trust loss for her den.
        if delta < 0:
            has_sleet = conn.execute(
                """
                SELECT 1 FROM users
                WHERE pack_id = ? AND LOWER(wolf_name) = LOWER(?)
                  AND great_pack = 'greyspire' AND condition NOT IN ('dead', 'dying')
                LIMIT 1
                """,
                (pack_id, SLEET_NAME),
            ).fetchone()
            if has_sleet:
                from config import SLEET_PLOT_CAT_TRUST_RELIEF

                pack_delta = min(0, delta + SLEET_PLOT_CAT_TRUST_RELIEF)
        db.adjust_cat_pact_trust(pack_id, row["clan_name"], pack_delta)


def plot_rank_dispute_standing(winner, guild_id: int | None) -> int:
    """Moth (greyspire lowbelly) climbs on a rank-dispute win during the blinking."""
    if not guild_id or plot_phase(guild_id) <= 0:
        return 0
    if not _is_plot_wolf(winner, MOTH_NAME):
        return 0
    if (winner["great_pack"] if "great_pack" in winner.keys() else None) != "greyspire":
        return 0
    from config import MOTH_PLOT_RANK_STANDING

    return MOTH_PLOT_RANK_STANDING


def plot_prophecy_standing(user, guild_id: int | None) -> int:
    """Gasp earns standing when the den heeds her prophecy during the blinking."""
    if not guild_id or plot_phase(guild_id) <= 0:
        return 0
    if not _is_plot_wolf(user, GASP_NAME):
        return 0
    from config import GASP_PLOT_PROPHECY_STANDING

    return GASP_PLOT_PROPHECY_STANDING


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
    guild_id: int, activity: str, *, great_pack: str | None, user=None
) -> tuple[float, str]:
    """Return (multiplier, footer note) for hunt/fish/scavenge payouts."""
    phase = plot_phase(guild_id)
    if phase <= 0:
        return 1.0, ""
    gp = great_pack or ""
    if activity == "fishing" and phase in WARM_RIVER_PHASES:
        if gp == "silverrush":
            if user and _is_plot_wolf(user, AROMIS_NAME):
                from config import AROMIS_PLOT_FISHING_MULT
                return AROMIS_PLOT_FISHING_MULT, "blinking; Aromis refuses to let the warm water win (**+15%** fish)."
            if user and _is_plot_wolf(user, CROAKER_NAME) and phase in (4, 8):
                from config import CROAKER_PLOT_FISHING_MULT
                return CROAKER_PLOT_FISHING_MULT, "blinking; Croaker knows exactly where the fish hide (**+30%** fish)."
            if user and _is_plot_wolf(user, CURLGRIP_NAME) and phase in (4, 8):
                from config import CURLGRIP_PLOT_FISHING_MULT
                return CURLGRIP_PLOT_FISHING_MULT, "blinking; Curlgrip works the warm shallows (**+20%** fish)."
            return 0.70, "blinking; warm silverrush water (**−30%** fish)."
        return 0.85, "blinking; river sickness (**−15%** fish)."
    # named greyspire hunters stack their bonus on top of the phase-3 pack bonus
    if activity in ("hunt", "scavenge") and gp == "greyspire" and user and _is_plot_wolf(user, IRONJAW_NAME) and phase in (3, 9):
        from config import IRONJAW_PLOT_HUNT_MULT
        mult = round(IRONJAW_PLOT_HUNT_MULT * (1.10 if phase == 3 else 1.0), 3)
        return mult, "blinking; Ironjaw hunts the ridge like no other (**+15%**)."
    if activity == "hunt" and gp == "greyspire" and user and _is_plot_wolf(user, SLATE_NAME) and phase in (3, 7):
        from config import SLATE_PLOT_HUNT_MULT
        mult = round(SLATE_PLOT_HUNT_MULT * (1.10 if phase == 3 else 1.0), 3)
        return mult, "blinking; Slate presses the hunt (**+10%**)."
    if activity == "hunt" and gp == "mistmoor" and user and _is_plot_wolf(user, SLUDGE_NAME):
        from config import SLUDGE_PLOT_HUNT_MULT
        return SLUDGE_PLOT_HUNT_MULT, "blinking; Sludge takes the swamp's water-prey (**+20%** hunt)."
    if activity == "hunt" and gp == "greyspire" and user and _is_plot_wolf(user, TALUS_NAME):
        from config import TALUS_PLOT_HUNT_MULT
        return TALUS_PLOT_HUNT_MULT, "blinking; Talus keeps the ridge fed (**+10%** hunt)."
    if activity == "hunt" and gp == "thistlehide" and phase in PARANOIA_PHASES and user and _is_plot_wolf(user, RIVENMAW_NAME):
        from config import RIVENMAW_PLOT_HUNT_MULT
        return RIVENMAW_PLOT_HUNT_MULT, "blinking; Rivenmaw hunts the tense border hard (**+10%**)."
    if activity in ("hunt", "scavenge", "track") and phase == 3 and gp == "greyspire":
        return 1.10, "blinking; iron-scented ridge (**+10%** hunt)."
    if activity == "track" and phase in PARANOIA_PHASES and gp == "thistlehide":
        if user and _is_plot_wolf(user, LUCID_NAME):
            from config import LUCID_PLOT_TRACK_MULT
            return LUCID_PLOT_TRACK_MULT, "blinking; Lucid reads the border where others hesitate (**+10%** track)."
    if activity == "scavenge" and phase > 0 and gp == "thistlehide":
        if user and _is_plot_wolf(user, CLOVERFERN_NAME):
            from config import CLOVERFERN_PLOT_SCAVENGE_MULT
            return CLOVERFERN_PLOT_SCAVENGE_MULT, "blinking; Cloverfern finds what the forest is still willing to give (**+10%** scavenge)."
        if user and _is_plot_wolf(user, MOSSGAZE_NAME):
            from config import MOSSGAZE_PLOT_SCAVENGE_MULT
            return MOSSGAZE_PLOT_SCAVENGE_MULT, "blinking; Mossgaze knows the forest's quiet larders (**+10%** scavenge)."
        if user and (_is_plot_wolf(user, FERNSPOT_NAME) or _is_plot_wolf(user, BARKHOLLOW_NAME)):
            from config import FORAGER_PLOT_SCAVENGE_MULT
            return FORAGER_PLOT_SCAVENGE_MULT, "blinking; the forest's foragers still find what it will give (**+10%** scavenge)."
    if activity == "scavenge" and phase > 0 and gp == "silverrush":
        if user and _is_plot_wolf(user, CINDER_NAME):
            from config import CINDER_PLOT_SCAVENGE_MULT
            return CINDER_PLOT_SCAVENGE_MULT, "blinking; Cinder, driftwood-born, scavenges the banks well (**+10%**)."
    if activity == "scavenge" and phase > 0 and gp == "greyspire":
        if user and _is_plot_wolf(user, SCAB_NAME):
            from config import SCAB_PLOT_SCAVENGE_MULT
            return SCAB_PLOT_SCAVENGE_MULT, "blinking; Scab knows which scraps go unwatched (**+15%** scavenge)."
    if activity == "scavenge" and phase > 0 and gp == "mistmoor":
        if user and _is_plot_wolf(user, MUDNOSE_NAME):
            from config import FORAGER_PLOT_SCAVENGE_MULT
            return FORAGER_PLOT_SCAVENGE_MULT, "blinking; Mudnose roots up the bog's hidden food (**+10%** scavenge)."
    return 1.0, ""


_COMBAT_PLOT_NAMES = {n.casefold() for n in (ICEFANG_NAME, THORN_NAME, RIFT_NAME)}


def _living_ally_present(fighters, attacker_f) -> bool:
    """A living non-npc packmate stands in the fight beside the attacker."""
    for f in fighters:
        if f["id"] == attacker_f["id"] or f["npc_name"]:
            continue
        if int(f["hp"]) > 0:
            return True
    return False


def _named_ally_present(fighters, attacker_f, canon_name: str) -> bool:
    """A specific named wolf is a living fighter beside the attacker."""
    for f in fighters:
        if f["id"] == attacker_f["id"] or f["npc_name"] or int(f["hp"]) <= 0:
            continue
        wid = f["wolf_id"] if "wolf_id" in f.keys() else None
        if not wid:
            continue
        w = db.get_user_by_id(wid)
        if w and (w["wolf_name"] or "").strip().casefold() == canon_name.casefold():
            return True
    return False


def plot_combat_bonus(attacker, attacker_f, attack_type: str) -> tuple[int, int, str]:
    """Book One combat lanes: returns (attack_bonus, damage_bonus, note).

    Icefang bites harder in border fights; Thorn fights harder with a packmate
    beside him; Rift throws himself in when Saltmuzzle is in the fight. All only
    during border paranoia (phases 6 to 10)."""
    if not attacker_f:
        return 0, 0, ""
    name = ((db.row_val(attacker, "wolf_name", "") or "").strip().casefold())
    if name not in _COMBAT_PLOT_NAMES:
        return 0, 0, ""
    enc = db.get_encounter(attacker_f["encounter_id"])
    if not enc:
        return 0, 0, ""
    guild_id = enc["guild_id"] if "guild_id" in enc.keys() else None
    if not guild_id or plot_phase(guild_id) not in PARANOIA_PHASES:
        return 0, 0, ""
    gp = db.row_val(attacker, "great_pack", "") or ""
    if _is_plot_wolf(attacker, ICEFANG_NAME) and gp == "greyspire":
        is_border = bool(enc["is_border_fight"]) if "is_border_fight" in enc.keys() else False
        if attack_type == "bite" and is_border:
            return 0, 2, "blinking; Icefang bites like the mountain's will (**+2 dmg**)."
        return 0, 0, ""
    fighters = db.get_combat_fighters(attacker_f["encounter_id"])
    if _is_plot_wolf(attacker, THORN_NAME) and gp == "greyspire":
        if _living_ally_present(fighters, attacker_f):
            return 2, 0, "blinking; Thorn fights harder with a packmate beside him (**+2 atk**)."
        return 0, 0, ""
    if _is_plot_wolf(attacker, RIFT_NAME) and gp == "silverrush":
        if _named_ally_present(fighters, attacker_f, SALTMUZZLE_NAME):
            return 2, 0, "blinking; Rift throws himself between Saltmuzzle and the teeth (**+2 atk**)."
        return 0, 0, ""
    return 0, 0, ""


def plot_drink_thirst_bonus(guild_id: int, great_pack: str | None) -> tuple[int, str]:
    phase = plot_phase(guild_id)
    if phase == 11:
        return 5, "ash naming; the creek answers (**+5** hydration restore)."
    if phase in WARM_RIVER_PHASES and great_pack == "silverrush":
        return -3, "blinking; the creek runs unnaturally warm (**−3** hydration restore)."
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


def plot_sniff_border_mult(guild_id: int, user=None) -> float:
    phase = plot_phase(guild_id)
    if phase in PARANOIA_PHASES:
        if user and _is_plot_wolf(user, KANAMI_NAME):
            from config import KANAMI_PLOT_BORDER_MULT
            return KANAMI_PLOT_BORDER_MULT
        if user and _is_plot_wolf(user, SKYE_NAME):
            from config import SKYE_PLOT_BORDER_MULT
            return SKYE_PLOT_BORDER_MULT
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
        from config import (
            BRACKENPELT_PLOT_PATROL_STANDING,
            FINNPELT_PLOT_PATROL_STANDING,
            RIVERSHROUD_PLOT_PATROL_STANDING,
        )
        from engine.pack_leadership import wolf_role_key

        role = wolf_role_key(user)
        if _is_plot_wolf(user, RIVERSHROUD_NAME) and role == "alpha":
            bonus += RIVERSHROUD_PLOT_PATROL_STANDING
        elif _is_plot_wolf(user, FINNPELT_NAME) and role == "hunter":
            bonus += FINNPELT_PLOT_PATROL_STANDING
        elif _is_plot_wolf(user, BRACKENPELT_NAME):
            bonus += BRACKENPELT_PLOT_PATROL_STANDING
        elif _is_plot_wolf(user, ASHBARK_NAME):
            from config import ASHBARK_PLOT_PATROL_STANDING
            bonus += ASHBARK_PLOT_PATROL_STANDING
    if user and great_pack == "greyspire" and plot_phase(guild_id) in PARANOIA_PHASES:
        if _is_plot_wolf(user, ICEFANG_NAME):
            from config import ICEFANG_PLOT_PATROL_STANDING

            bonus += ICEFANG_PLOT_PATROL_STANDING
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
    odds = 0.45
    if _is_plot_wolf(user, PALESTEP_NAME):
        odds = 0.65
    if random.random() > odds:
        return ""
    bones = random.randint(15, 35)
    if _is_plot_wolf(user, PALESTEP_NAME):
        bones += 10
    db.add_bones(user["discord_id"], bones, wolf_id=user["id"])
    standing = db.adjust_wolf_standing_by_id(user["id"], 2)
    kick = " standing **+2**" if standing != "kicked" else " (**cast out**)"
    iron_note = (
        "\n_**Pale'Step**'s nose for iron finds it before anyone else even smells the rust._"
        if _is_plot_wolf(user, PALESTEP_NAME)
        else ""
    )
    return (
        f"\n\n_under the mill timbers you uncover a **fossil tooth** wrapped in rust._{iron_note}\n"
        f"**+{bones}** bones{kick}; report with `/world action:plot`."
    )


def firepaw_plot_active(user, guild_id: int) -> bool:
    if plot_phase(guild_id) <= 0 or not _is_plot_wolf(user, FIREPAW_NAME):
        return False
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    return gp == "thistlehide"


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


def _pack_healer_plot_bonus(healer, guild_id: int | None, canon_name: str, pack: str, config_key: str) -> int:
    if not guild_id or plot_phase(guild_id) not in HEALER_PLOT_PHASES:
        return 0
    if not _is_plot_wolf(healer, canon_name):
        return 0
    gp = healer["great_pack"] if "great_pack" in healer.keys() else None
    if gp != pack:
        return 0
    import config as _cfg
    return getattr(_cfg, config_key, 0)


def _pack_healer_rot_lung_bonus(healer, patient, guild_id, canon_name, pack, config_key) -> int:
    """Extra heal a rot-lung specialist adds when the patient has rot-lung."""
    if not guild_id or plot_phase(guild_id) not in HEALER_PLOT_PHASES:
        return 0
    if not _is_plot_wolf(healer, canon_name):
        return 0
    if (healer["great_pack"] if "great_pack" in healer.keys() else None) != pack:
        return 0
    from engine.diseases import parse_disease
    key, _ = parse_disease(patient["disease"] if "disease" in patient.keys() else None)
    if key != "rot_lung":
        return 0
    import config as _cfg
    return getattr(_cfg, config_key, 0)


def plot_healer_heal_bonus(healer, patient, guild_id: int | None) -> int:
    """stacked book one heal bonuses for canon healer wolves."""
    bonus = plot_firepaw_heal_bonus(healer, guild_id) + plot_soot_heal_bonus(healer, patient, guild_id)
    bonus += _pack_healer_plot_bonus(healer, guild_id, HEMLOCK_NAME, "greyspire", "HEMLOCK_PLOT_TREAT_HEAL_BONUS")
    bonus += _pack_healer_plot_bonus(healer, guild_id, RIPPLE_NAME, "silverrush", "RIPPLE_PLOT_TREAT_HEAL_BONUS")
    bonus += _pack_healer_plot_bonus(healer, guild_id, SYPHA_NAME, "thistlehide", "SYPHA_PLOT_TREAT_HEAL_BONUS")
    # mistmoor's treat lane belongs to Mirewort the medic, not Murkvein the alpha.
    bonus += _pack_healer_plot_bonus(healer, guild_id, MIREWORT_NAME, "mistmoor", "MIREWORT_PLOT_TREAT_HEAL_BONUS")
    bonus += _pack_healer_plot_bonus(healer, guild_id, ROTTEDDUST_NAME, "mistmoor", "ROTTEDDUST_PLOT_TREAT_HEAL_BONUS")
    # rot-lung specialists heal it harder
    bonus += _pack_healer_rot_lung_bonus(healer, patient, guild_id, RIPPLE_NAME, "silverrush", "RIPPLE_PLOT_ROT_LUNG_HEAL_BONUS")
    bonus += _pack_healer_rot_lung_bonus(healer, patient, guild_id, MIREWORT_NAME, "mistmoor", "MIREWORT_PLOT_ROT_LUNG_HEAL_BONUS")
    return bonus


def plot_healer_observe_strain_relief(medic, guild_id: int | None) -> str:
    """Named Book One healers ease their own medicine strain when they observe."""
    if not guild_id or plot_phase(guild_id) not in HEALER_PLOT_PHASES:
        return ""
    from config import HEALER_PLOT_OBSERVE_STRAIN

    name = ((medic["wolf_name"] if "wolf_name" in medic.keys() else "") or "").strip().casefold()
    relief = {k.casefold(): v for k, v in HEALER_PLOT_OBSERVE_STRAIN.items()}
    amount = relief.get(name)
    if not amount:
        return ""
    from engine.character_traits import reduce_skill_strain

    removed = reduce_skill_strain(medic["id"], "medicine", amount)
    if removed:
        return f"\n\n_the blinking sharpens {name}'s eye; **−{removed} medicine strain**._"
    return ""


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


def _maggotbrain_daily_available(user, day: int) -> bool:
    last = (
        int(user["last_maggotbrain_reward_day"])
        if "last_maggotbrain_reward_day" in user.keys()
        else 0
    )
    return last < day


def _mark_maggotbrain_daily(user, day: int) -> None:
    db.update_user_by_id(user["id"], last_maggotbrain_reward_day=day)


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
            lines.append(f"antlered alpha on the ridge; {standing_note}.")
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
        kick = db.adjust_wolf_standing_by_id(user["id"], FINNPELT_PLOT_SNIFF_STANDING)
        standing_note = (
            f"**+{FINNPELT_PLOT_SNIFF_STANDING} standing**"
            if kick != "kicked"
            else "**cast out**"
        )
        lines.append(f"ridge held without the crown; {standing_note}.")
    return "\n\n_" + " ".join(lines) + "_"


def apply_plot_grim_sniff(user, guild_id: int, day: int) -> str:
    """Grim (greyspire highfang) reads a pack-wide omen on the border during
    paranoia; a chance to lift the whole pack's standing for the sunrise."""
    if not _is_plot_wolf(user, GRIM_NAME):
        return ""
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    if gp != "greyspire" or plot_phase(guild_id) not in PARANOIA_PHASES:
        return ""
    from config import GRIM_PLOT_OMEN_CHANCE, GRIM_PLOT_OMEN_STANDING

    if random.random() >= GRIM_PLOT_OMEN_CHANCE:
        return ""
    with db.get_db() as conn:
        conn.execute(
            "UPDATE users SET standing = standing + ? "
            "WHERE great_pack = 'greyspire' AND condition NOT IN ('dead', 'dying')",
            (GRIM_PLOT_OMEN_STANDING,),
        )
    return (
        f"\n\n_Grim reads a greyspire omen in the border scent; the whole pack stands "
        f"taller (**+{GRIM_PLOT_OMEN_STANDING} standing** to all of greyspire)._"
    )


def plot_work_mult(user, guild_id: int | None) -> float:
    """Moth (greyspire lowbelly) works twice as hard through the blinking."""
    if not guild_id or plot_phase(guild_id) <= 0:
        return 1.0
    if not _is_plot_wolf(user, MOTH_NAME):
        return 1.0
    if (user["great_pack"] if "great_pack" in user.keys() else None) != "greyspire":
        return 1.0
    from config import MOTH_PLOT_WORK_MULT

    return MOTH_PLOT_WORK_MULT


def plot_faction_approach_bonus(user, faction: str, guild_id: int | None) -> int:
    """Book One diplomats win extra ground on a successful faction approach.
    (name -> (pack, faction or None for any, extra standing))"""
    if not guild_id or plot_phase(guild_id) <= 0:
        return 0
    from config import (
        PEBBLE_PLOT_FACTION_STANDING,
        REEDWHISPER_PLOT_FACTION_STANDING,
        SLEET_PLOT_FACTION_STANDING,
    )

    table = {
        SLEET_NAME: ("greyspire", "thorne_lumber", SLEET_PLOT_FACTION_STANDING),
        PEBBLE_NAME: ("silverrush", None, PEBBLE_PLOT_FACTION_STANDING),
        REEDWHISPER_NAME: ("mistmoor", None, REEDWHISPER_PLOT_FACTION_STANDING),
        THYME_NAME: ("thistlehide", None, 1),
    }
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    for name, (pack, fac, bonus) in table.items():
        if _is_plot_wolf(user, name) and gp == pack and (fac is None or faction == fac):
            return bonus
    return 0


_SURVEY_SCOUTS = {
    STONEPIERCER_NAME: "greyspire",
    RAVEN_NAME: "greyspire",
    EBB_NAME: "silverrush",
    YARROW_NAME: "mistmoor",
    MOSSHEART_NAME: "thistlehide",
}


def plot_survey_standing_bonus(user, guild_id: int | None) -> int:
    """Book One scouts earn extra standing on a successful survey while the
    blinking is active."""
    if not guild_id or plot_phase(guild_id) <= 0:
        return 0
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    for name, pack in _SURVEY_SCOUTS.items():
        if _is_plot_wolf(user, name) and gp == pack:
            from config import PLOT_SURVEY_STANDING

            return PLOT_SURVEY_STANDING
    return 0


def apply_plot_maggotbrain_sniff(user, guild_id: int, day: int) -> str:
    """Rot-reading rewards for MaggotBrain on /sniff during Belly Silence through Blame Spiral."""
    if not maggotbrain_plot_active(user, guild_id):
        return ""
    from config import (
        MAGGOTBRAIN_PLOT_SNIFF_MOOD,
        MAGGOTBRAIN_PLOT_SNIFF_STANDING,
        SNIFF_HUNT_BONUS_PCT,
    )

    phase = plot_phase(guild_id)
    if phase not in MAGGOTBRAIN_PLOT_PHASES:
        return ""
    lines: list[str] = []

    mood = db.adjust_mood(user["id"], MAGGOTBRAIN_PLOT_SNIFF_MOOD)
    db.update_user(user["discord_id"], wolf_id=user["id"], sniff_bonus_day=day)
    lines.append(f"**+{MAGGOTBRAIN_PLOT_SNIFF_MOOD} mood** (now **{mood}**).")
    lines.append(
        f"**sniff bonus** active (**+{SNIFF_HUNT_BONUS_PCT}%** hunt/track); "
        "the rot tells you exactly where to look."
    )
    if _maggotbrain_daily_available(user, day):
        _mark_maggotbrain_daily(user, day)
        kick = db.adjust_wolf_standing_by_id(user["id"], MAGGOTBRAIN_PLOT_SNIFF_STANDING)
        standing_note = (
            f"**+{MAGGOTBRAIN_PLOT_SNIFF_STANDING} standing**"
            if kick != "kicked"
            else "**cast out**"
        )
        lines.append(f"a corpse found before the patrol smelled it; {standing_note}.")
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
        kick = db.adjust_wolf_standing_by_id(user["id"], FIREPAW_PLOT_SNIFF_STANDING)
        standing_note = (
            f"**+{FIREPAW_PLOT_SNIFF_STANDING} standing**"
            if kick != "kicked"
            else "**cast out**"
        )
        lines.append(
            f"border mapped by ear; {standing_note} · **+{FIREPAW_PLOT_SNIFF_MOOD_LATE} mood** "
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
        kick = db.adjust_wolf_standing_by_id(user["id"], SOOT_PLOT_SNIFF_STANDING)
        standing_note = (
            f"**+{SOOT_PLOT_SNIFF_STANDING} standing**"
            if kick != "kicked"
            else "**cast out**"
        )
        lines.append(
            f"mirewort's second sight on the border; {standing_note}."
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
                lines.append("sypha's den trusts your touch; but the pack casts you out.")
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
                lines.append("mirewort's den trusts your hands; but the pack casts you out.")
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
        lines.append("the belly falls silent; rot-lung walks the reeds; your litter's ghost in every wheeze.")
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
        maggotbrain_block = apply_plot_maggotbrain_sniff(user, guild_id, day)
        grim_block = apply_plot_grim_sniff(user, guild_id, day)
        for block in (firepaw_block, soot_block, rivershroud_block, finnpelt_block, maggotbrain_block, grim_block):
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
            "_limp rogue scent on the border; three-legged gait, fish-grease and guilt._"
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
    elif _is_plot_wolf(user, MAGGOTBRAIN_NAME) and phase in MAGGOTBRAIN_PLOT_PHASES:
        lines.append("_the rot names every wolf who passed before the patrol counts the tracks._")
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
            f"**{name}** is cornered on the **silverrush** shallows; patrol scent, no escape.\n"
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
