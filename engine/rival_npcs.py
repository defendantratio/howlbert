"""Persistent rival NPCs; named troublemakers a wolf can build a grudge with.

Distinct from the player-vs-player wolf encounters in engine.sniff: rivals
here are static NPCs (not other players) tied to a Great Pack or to the
rogue underworld, surfaced through sniff's hostile-scent alert, border
fights, and hunts. Grudge builds per wolf-NPC pair and is visible via
`/rivals`.
"""

from __future__ import annotations

import random

import database as db

GRUDGE_MIN = 0
GRUDGE_MAX = 100
GRUDGE_PER_HOSTILE_ENCOUNTER = 8
GRUDGE_DECAY_ON_GOOD_STANDING = 3

GRUDGE_TIER_LABELS = (
    (15, "wary"),
    (40, "bad blood"),
    (70, "blood feud"),
    (101, "sworn enemy"),
)

# A small static roster per Great Pack, plus a rogue/independent pool.
# Threat is flavor-only (used to scale the cost of a loss slightly via
# existing combat systems, not a new stat block).
RIVAL_ROSTER: dict[str, tuple[dict, ...]] = {
    "greyspire": (
        {"key": "greyspire_korrig", "name": "Korrig", "threat": "high",
         "blurb": "a scarred Greyspire enforcer who treats every border line as a personal insult."},
        {"key": "greyspire_ashe", "name": "Ashe", "threat": "mid",
         "blurb": "a Greyspire scout who marks territory twice as often as she needs to, just to provoke."},
        {"key": "greyspire_brael", "name": "Brael", "threat": "mid",
         "blurb": "young, hot-tempered, and looking to make a name for himself at someone else's expense."},
    ),
    "mistmoor": (
        {"key": "mistmoor_sull", "name": "Sull", "threat": "high",
         "blurb": "a Mistmoor lowbelly who's lost too much to the swamp to play fair with outsiders."},
        {"key": "mistmoor_vey", "name": "Vey", "threat": "mid",
         "blurb": "quiet, patient, and always somehow already there when you cross the border."},
        {"key": "mistmoor_grul", "name": "Grul", "threat": "mid",
         "blurb": "claims the Maw favors him; picks fights to prove it."},
    ),
    "thistlehide": (
        {"key": "thistlehide_oren", "name": "Oren", "threat": "high",
         "blurb": "a Thistlehide hunter convinced your pack stole his territory generations ago."},
        {"key": "thistlehide_ilse", "name": "Ilse", "threat": "mid",
         "blurb": "sharp-tongued and sharper-clawed; holds grudges the way other wolves hold dens."},
        {"key": "thistlehide_dann", "name": "Dann", "threat": "mid",
         "blurb": "follows the old forest law to the letter, and uses it as an excuse to start trouble."},
    ),
    "silverrush": (
        {"key": "silverrush_nix", "name": "Nix", "threat": "high",
         "blurb": "fast, slippery, and always gone before anyone can call for backup."},
        {"key": "silverrush_pell", "name": "Pell", "threat": "mid",
         "blurb": "a Silverrush diplomat whose treaties always seem to favor Silverrush a little too much."},
        {"key": "silverrush_torrin", "name": "Torrin", "threat": "mid",
         "blurb": "still angry about a fight three winters ago that nobody else remembers."},
    ),
}

ROGUE_RIVALS: tuple[dict, ...] = (
    {"key": "rogue_marrow", "name": "Marrow", "threat": "high",
     "blurb": "a rogue who raids dens for sport and leaves a mark behind every time."},
    {"key": "rogue_thistle", "name": "Thistle-eye", "threat": "mid",
     "blurb": "one eye, no pack, and a long memory for anyone who's wronged her."},
)


def _field(user, key, default=None):
    if hasattr(user, "keys") and key in user.keys():
        return user[key]
    if isinstance(user, dict):
        return user.get(key, default)
    return default


def grudge_label(grudge: int) -> str:
    for threshold, label in GRUDGE_TIER_LABELS:
        if grudge < threshold:
            return label
    return GRUDGE_TIER_LABELS[-1][1]


def roster_for_pack_key(pack_key: str | None) -> tuple[dict, ...]:
    if pack_key and pack_key in RIVAL_ROSTER:
        return RIVAL_ROSTER[pack_key]
    return ()


def pick_rival_for_hostile_pack(guild_id: int, pack_id: int) -> tuple[dict, str] | None:
    """Pick a rival NPC tied to one of this pack's currently-hostile rivals.

    Returns (rival_dict, other_pack_name) or None if no hostile pack has a roster.
    """
    from engine.pack_relations import HOSTILE_STANDING_THRESHOLD

    candidates: list[tuple[dict, str]] = []
    for row in db.list_pack_relations(guild_id, pack_id):
        if int(row["standing"]) > HOSTILE_STANDING_THRESHOLD:
            continue
        other_pack = db.get_pack(int(row["other_pack_id"]))
        pack_key = other_pack["key"] if other_pack and "key" in other_pack.keys() else None
        roster = roster_for_pack_key(pack_key)
        for rival in roster:
            candidates.append((rival, row["other_pack_name"]))
    if not candidates:
        return None
    return random.choice(candidates)


def pick_rogue_rival() -> dict:
    return random.choice(ROGUE_RIVALS)


def _milestone_tiers() -> tuple[str, ...]:
    return tuple(label for _threshold, label in GRUDGE_TIER_LABELS if label not in ("wary",))


def _maybe_log_rivalry_milestone(wolf_id: int, rival_key: str, old_grudge: int, new_grudge: int) -> None:
    old_tier = grudge_label(old_grudge)
    new_tier = grudge_label(new_grudge)
    if old_tier == new_tier or new_tier not in _milestone_tiers():
        return
    wolf = db.get_user_by_id(wolf_id)
    if not wolf:
        return
    rival_name = _rival_display_name(rival_key)
    from engine.wolf_journal import log_rivalry_milestone

    log_rivalry_milestone(wolf_id, wolf["wolf_name"], rival_name, new_tier)


def record_rival_encounter(wolf_id: int, rival_key: str, *, day: int, delta: int = GRUDGE_PER_HOSTILE_ENCOUNTER) -> int:
    existing = db.get_wolf_rivalry(wolf_id, rival_key)
    old_grudge = int(existing["grudge"]) if existing else 0
    new_grudge = db.adjust_wolf_rivalry_grudge(
        wolf_id, rival_key, delta, day=day, grudge_min=GRUDGE_MIN, grudge_max=GRUDGE_MAX
    )
    _maybe_log_rivalry_milestone(wolf_id, rival_key, old_grudge, new_grudge)
    return new_grudge


def find_rival_meta(rival_key: str) -> dict | None:
    for roster in RIVAL_ROSTER.values():
        for rival in roster:
            if rival["key"] == rival_key:
                return rival
    for rival in ROGUE_RIVALS:
        if rival["key"] == rival_key:
            return rival
    return None


def pack_key_for_rival(rival_key: str) -> str | None:
    for pack_key, roster in RIVAL_ROSTER.items():
        for rival in roster:
            if rival["key"] == rival_key:
                return pack_key
    return None


def highest_grudge_rival_for_pack_key(wolf_id: int, pack_key: str) -> dict | None:
    """The wolf's most-grudged existing rival tied to a given pack, if any."""
    best = None
    for row in db.list_wolf_rivalries(wolf_id):
        if pack_key_for_rival(row["rival_key"]) != pack_key:
            continue
        if best is None or int(row["grudge"]) > int(best["grudge"]):
            best = row
    if best is None:
        return None
    meta = find_rival_meta(best["rival_key"])
    if not meta:
        return None
    return {**meta, "grudge": int(best["grudge"])}


PLAYER_RIVAL_PREFIX = "player:"


def is_player_rival_key(rival_key: str) -> bool:
    return rival_key.startswith(PLAYER_RIVAL_PREFIX)


def player_rival_wolf_id(rival_key: str) -> int | None:
    if not is_player_rival_key(rival_key):
        return None
    try:
        return int(rival_key[len(PLAYER_RIVAL_PREFIX):])
    except ValueError:
        return None


def record_player_rivalry(
    wolf_id: int, other_wolf_id: int, *, day: int, delta: int = GRUDGE_PER_HOSTILE_ENCOUNTER, mutual: bool = True
) -> int:
    """Build grudge between two real wolves after a hostile encounter; returns this wolf's new grudge."""
    key_a = f"{PLAYER_RIVAL_PREFIX}{other_wolf_id}"
    existing_a = db.get_wolf_rivalry(wolf_id, key_a)
    old_a = int(existing_a["grudge"]) if existing_a else 0
    grudge = db.adjust_wolf_rivalry_grudge(
        wolf_id, key_a, delta, day=day, grudge_min=GRUDGE_MIN, grudge_max=GRUDGE_MAX
    )
    _maybe_log_rivalry_milestone(wolf_id, key_a, old_a, grudge)
    if mutual:
        key_b = f"{PLAYER_RIVAL_PREFIX}{wolf_id}"
        existing_b = db.get_wolf_rivalry(other_wolf_id, key_b)
        old_b = int(existing_b["grudge"]) if existing_b else 0
        new_b = db.adjust_wolf_rivalry_grudge(
            other_wolf_id, key_b, delta, day=day, grudge_min=GRUDGE_MIN, grudge_max=GRUDGE_MAX
        )
        _maybe_log_rivalry_milestone(other_wolf_id, key_b, old_b, new_b)
    return grudge


def _rival_display_name(rival_key: str) -> str:
    other_id = player_rival_wolf_id(rival_key)
    if other_id is not None:
        other = db.get_user_by_id(other_id)
        return other["wolf_name"] if other else "a wolf no longer on howlbert"
    meta = find_rival_meta(rival_key)
    return meta["name"] if meta else rival_key


def rival_status_lines(wolf_id: int) -> list[str]:
    rows = db.list_wolf_rivalries(wolf_id)
    if not rows:
        return []
    lines = []
    for row in rows:
        name = _rival_display_name(row["rival_key"])
        grudge = int(row["grudge"])
        lines.append(
            f"**{name}** — grudge **{grudge}/100** ({grudge_label(grudge)}); "
            f"{int(row['encounters'])} encounter(s)"
        )
    return lines
