"""Great Pack rival standing; tags, mechanical gates, and UX text."""

from __future__ import annotations

import random

import database as db

HOSTILE_STANDING_THRESHOLD = 3
FRIENDLY_STANDING_THRESHOLD = 8
WAR_STANDING_THRESHOLD = 0
NEUTRAL_STANDING = 5

SNIFF_ENCOUNTER_HOSTILE = (
    "**{pack}** scent on the wind; **{name}** bares teeth — hostile ground, attack on sight.",
    "A **{pack}** patrol; **{name}** blocks the trail, hackles raised. Your dens are not friends.",
    "**{name}** of **{pack}** catches your mark and lunges; standing **{standing}/10** reads as open feud.",
)

SNIFF_ENCOUNTER_WAR = (
    "**{pack}** wolves on the war-line; **{name}** comes in low, already fighting.",
    "War-scent everywhere. **{name}** (**{pack}**) strikes before you finish reading the wind.",
)


def relation_tag(standing: int) -> str:
    if standing <= WAR_STANDING_THRESHOLD:
        return "war"
    if standing <= HOSTILE_STANDING_THRESHOLD:
        return "hostile"
    if standing >= FRIENDLY_STANDING_THRESHOLD:
        return "friendly"
    return "neutral"


def relation_tag_label(standing: int) -> str:
    tag = relation_tag(standing)
    if tag == "war":
        return "war; constant skirmishes"
    if tag == "hostile":
        return "hostile; attacks on sight"
    if tag == "friendly":
        return "friendly; may share hunting grounds"
    return "neutral"


def relation_effect_text(standing: int) -> str:
    tag = relation_tag(standing)
    if tag == "war":
        return (
            f"**war** (**{standing}/10**); border skirmishes, sniff fights, and treasury raids "
            "are expected. standing at **0** also opens an automatic territory war when no "
            "conflict is already active. `/pack share` and `/pack aid` won't land until standing rises."
        )
    if tag == "hostile":
        return (
            f"**hostile** (**{standing}/10**); rival wolves attack on sight on the trail. "
            "**medics** remain neutral; cross-pack `/medic` care still works."
        )
    if tag == "friendly":
        return (
            f"**friendly** (**{standing}/10**); may share hunting grounds and join each other's "
            f"**pack hunts** when standing stays **≥{FRIENDLY_STANDING_THRESHOLD}**."
        )
    return (
        f"**neutral** (**{standing}/10**); parley with `/pack howl`, `/pack share`, or `/pack aid`."
    )


def is_friendly_relation(standing: int) -> bool:
    return standing >= FRIENDLY_STANDING_THRESHOLD


def is_hostile_relation(standing: int) -> bool:
    return standing <= HOSTILE_STANDING_THRESHOLD


def is_war_relation(standing: int) -> bool:
    return standing <= WAR_STANDING_THRESHOLD


def pack_relation(guild_id: int, pack_a_id: int, pack_b_id: int) -> int:
    if not pack_a_id or not pack_b_id or int(pack_a_id) == int(pack_b_id):
        return NEUTRAL_STANDING
    return db.get_pack_relation(guild_id, int(pack_a_id), int(pack_b_id))


def cross_pack_relation(user, other, guild_id: int | None) -> int | None:
    """Standing between two wolves' Great Packs, or None if same pack / loner."""
    if not guild_id or not user or not other:
        return None
    a_pack = user["pack_id"] if "pack_id" in user.keys() else None
    b_pack = other["pack_id"] if "pack_id" in other.keys() else None
    if not a_pack or not b_pack or int(a_pack) == int(b_pack):
        return None
    return pack_relation(guild_id, int(a_pack), int(b_pack))


def can_share_territory(guild_id: int, pack_a_id: int, pack_b_id: int) -> tuple[bool, str]:
    standing = pack_relation(guild_id, pack_a_id, pack_b_id)
    if is_war_relation(standing):
        return False, (
            f"standing is **{standing}/10** (war). no shared ground until the border cools."
        )
    if is_hostile_relation(standing):
        return False, (
            f"standing **{standing}/10** is too hostile; they won't accept shared hunting ground."
        )
    return True, ""


def can_aid_rival(guild_id: int, pack_a_id: int, pack_b_id: int) -> tuple[bool, str]:
    standing = pack_relation(guild_id, pack_a_id, pack_b_id)
    if is_war_relation(standing):
        return False, (
            f"standing **{standing}/10**; your dens are at war — send aid after parley, not blades."
        )
    if is_hostile_relation(standing):
        return False, (
            f"standing **{standing}/10** is too hostile; they won't accept aid from your den."
        )
    return True, ""


def format_standing_war_flash(
    guild_id: int,
    pack_a_id: int,
    pack_b_id: int,
    new_standing: int,
) -> str:
    """UX line when standing hits war and a border war opens (or can't yet)."""
    if not is_war_relation(new_standing):
        return ""
    war = db.get_active_war_between_packs(guild_id, int(pack_a_id), int(pack_b_id))
    if war:
        return (
            f"\n\n**territory war declared** over **{war['territory_name']}**. "
            "earn points with `/pack patrol` and `/pack scout`."
        )
    if db.get_active_war_for_pack(guild_id, int(pack_a_id)) or db.get_active_war_for_pack(
        guild_id, int(pack_b_id)
    ):
        return (
            "\n\n_standing **0** (war), but your den is already tied up in another border fight._"
        )
    return (
        "\n\n_standing **0** (war). a territory war opens automatically when contested "
        "ground exists and neither den is already fighting._"
    )


def can_join_friendly_pack_hunt(
    user,
    hunt,
    *,
    guild_id: int,
) -> tuple[bool, str | None]:
    """Cross-pack join when standing ≥ friendly threshold."""
    if not db.row_val(user, "pack_id") or not db.row_val(hunt, "pack_id"):
        return False, None
    if int(user["pack_id"]) == int(hunt["pack_id"]):
        return True, None
    standing = pack_relation(guild_id, int(user["pack_id"]), int(hunt["pack_id"]))
    if not is_friendly_relation(standing):
        return False, None
    other = db.get_pack(int(hunt["pack_id"]))
    name = other["name"] if other else "that den"
    return True, f"_friendly standing **{standing}/10** with **{name}**; allied hunt._"


def _bonded_enough_to_skip_fight(user, other) -> bool:
    from engine.bonds import has_strong_positive_bond

    return has_strong_positive_bond(user["id"], other["id"])


def sniff_encounter_lines(
    user,
    other,
    *,
    guild_id: int,
    channel_id: int,
    day: int = 0,
) -> tuple[str, int | None]:
    """
    Flavor for a wolf sniff encounter and optional combat id for hostile/war rivals.
    Returns (extra body text, encounter_id).
    """
    from config import GREAT_PACKS

    standing = cross_pack_relation(user, other, guild_id)
    if standing is None:
        return "", None

    gp = other["great_pack"] if "great_pack" in other.keys() and other["great_pack"] else None
    pack_name = GREAT_PACKS[gp]["name"] if gp and gp in GREAT_PACKS else "a rival den"

    if (is_war_relation(standing) or is_hostile_relation(standing)) and not _bonded_enough_to_skip_fight(user, other):
        pool = SNIFF_ENCOUNTER_WAR if is_war_relation(standing) else SNIFF_ENCOUNTER_HOSTILE
        line = random.choice(pool).format(
            name=other["wolf_name"],
            pack=pack_name,
            standing=standing,
        )
        if day > 0:
            from engine.rival_npcs import record_player_rivalry

            grudge = record_player_rivalry(user["id"], other["id"], day=day)
            line += f"\nyour grudge with **{other['wolf_name']}**: **{grudge}/100** (`/rivals`)."
        enc_id = start_rival_wolf_skirmish(
            user,
            other,
            guild_id=guild_id,
            channel_id=channel_id,
        )
        if enc_id:
            line += "\n\n_Combat is live; drive them off or break away via the panel._"
        return f"\n\n{line}", enc_id

    if is_war_relation(standing) or is_hostile_relation(standing):
        # bonded enough to skip the fight, but the encounter still matters.
        return (
            f"\n\n_despite **{pack_name}**'s feud with your den, **{other['wolf_name']}** "
            f"lowers their hackles when they catch your scent; whatever you are to each "
            f"other outweighs the border tonight._",
            None,
        )

    if is_friendly_relation(standing):
        from config import WOLF_NOTORIETY_SNIFF_MOOD, WOLF_NOTORIETY_STANDING_THRESHOLD

        other_standing = int(other["standing"]) if "standing" in other.keys() else 0
        notoriety_note = ""
        if other_standing >= WOLF_NOTORIETY_STANDING_THRESHOLD:
            new_mood = db.adjust_mood(user["id"], WOLF_NOTORIETY_SNIFF_MOOD)
            notoriety_note = (
                f"\n_word of **{other['wolf_name']}**'s name has clearly reached this far; "
                f"**+{WOLF_NOTORIETY_SNIFF_MOOD} mood** crossing paths with them (now **{new_mood}**)._"
            )
        return (
            f"\n\n_a **{pack_name}** wolf on the wind; standing **{standing}/10** — "
            f"friendly enough to share the trail today._{notoriety_note}",
            None,
        )
    return "", None


def start_rival_wolf_skirmish(
    user,
    rival,
    *,
    guild_id: int,
    channel_id: int | None,
) -> int | None:
    """Begin an active PvP skirmish between two wolves (hostile border)."""
    if not channel_id:
        return None
    if rival["condition"] in ("dead", "dying"):
        return None
    if int(user["hp"]) <= 0 or int(rival["hp"]) <= 0:
        return None

    from engine.combat import roll_initiative

    enc_id = db.create_encounter(guild_id, channel_id, user["discord_id"])
    with db.get_db() as conn:
        conn.execute(
            """
            UPDATE combat_encounters
            SET is_border_fight = 1, hunter_discord_id = ?, hunter_wolf_id = ?
            WHERE id = ?
            """,
            (user["discord_id"], user["id"], enc_id),
        )

    f1 = db.add_combat_fighter(
        enc_id,
        discord_id=user["discord_id"],
        wolf_id=user["id"],
        hp=int(user["hp"]),
        max_hp=int(user["max_hp"]),
    )
    f2 = db.add_combat_fighter(
        enc_id,
        discord_id=rival["discord_id"],
        wolf_id=rival["id"],
        hp=int(rival["hp"]),
        max_hp=int(rival["max_hp"]),
    )

    rolls: list[tuple[int, int]] = []
    for fighter_id, wolf in ((f1, user), (f2, rival)):
        _die, _mod, total = roll_initiative(wolf)
        db.set_fighter_initiative(fighter_id, total)
        rolls.append((fighter_id, total))
    order = [fid for fid, _ in sorted(rolls, key=lambda x: -x[1])]
    db.start_combat_encounter(enc_id, order)
    return enc_id


def cross_pack_social_risk(
    user, partner, *, guild_id: int | None, channel_id: int | None
) -> tuple[bool, int | None]:
    """
    Shared gate for /playpen socialize/groom and /sign across Great Packs.
    Cross-pack interaction always works on friendly/neutral ground. On
    hostile or war ground there's a real CROSS_PACK_SOCIAL_COMBAT_CHANCE
    that it breaks into a border skirmish instead of going through.
    Returns (combat_triggered, encounter_id).
    """
    from config import CROSS_PACK_SOCIAL_COMBAT_CHANCE

    standing = cross_pack_relation(user, partner, guild_id)
    if standing is None or not is_hostile_relation(standing):
        return False, None

    from engine.bonds import has_strong_positive_bond

    if has_strong_positive_bond(user["id"], partner["id"]):
        # a real friendship, romance, kinship, or mentorship outweighs den
        # politics; Mossheart and Rivenmaw don't risk a fight every time
        # they meet just because their packs are feuding.
        return False, None

    if random.random() >= CROSS_PACK_SOCIAL_COMBAT_CHANCE:
        return False, None
    enc_id = start_rival_wolf_skirmish(user, partner, guild_id=guild_id, channel_id=channel_id)
    return True, enc_id


def _pick_border_war_territory(guild_id: int, pack_a_id: int, pack_b_id: int):
    """contested tile held by a rival, else first unclaimed ground between dens."""
    territories = db.get_territories(guild_id)
    for owner_id in (pack_b_id, pack_a_id):
        for terr in territories:
            if terr["owner_pack_id"] and int(terr["owner_pack_id"]) == int(owner_id):
                if not db.territory_has_active_war(guild_id, terr["id"]):
                    return terr
    for terr in territories:
        if not terr["owner_pack_id"] and not db.territory_has_active_war(guild_id, terr["id"]):
            return terr
    return None


def maybe_declare_relation_war(
    guild_id: int,
    pack_a: int,
    pack_b: int,
    day: int,
) -> int | None:
    """
    When rival standing hits 0, start a border war if neither den is already fighting.
    Returns war id or None.
    """
    if not pack_a or not pack_b or int(pack_a) == int(pack_b):
        return None
    standing = pack_relation(guild_id, int(pack_a), int(pack_b))
    if not is_war_relation(standing):
        return None
    if db.get_active_war_for_pack(guild_id, int(pack_a)) or db.get_active_war_for_pack(
        guild_id, int(pack_b)
    ):
        return None

    terr = _pick_border_war_territory(guild_id, int(pack_a), int(pack_b))
    if not terr:
        return None

    owner = int(terr["owner_pack_id"]) if terr["owner_pack_id"] else None
    if owner == int(pack_b):
        attacker, defender = int(pack_a), int(pack_b)
    elif owner == int(pack_a):
        attacker, defender = int(pack_b), int(pack_a)
    elif owner:
        attacker, defender = int(pack_a), owner
    else:
        attacker, defender = int(pack_a), int(pack_b)

    return db.start_war(guild_id, terr["id"], attacker, defender, day)


def cross_pack_prey_dispute(
    hunter,
    rival,
    *,
    guild_id: int,
    channel_id: int | None,
    choice: str,
) -> tuple[str, int | None]:
    """
    Rival wolves contest fresh-kill (−1 standing). Returns (note, skirmish encounter id).
    """
    if choice not in ("eat", "guard"):
        return "", None
    standing = cross_pack_relation(hunter, rival, guild_id)
    if standing is None or not is_hostile_relation(standing):
        return "", None

    h_pack = hunter["pack_id"] if "pack_id" in hunter.keys() else None
    r_pack = rival["pack_id"] if "pack_id" in rival.keys() else None
    if not h_pack or not r_pack or int(h_pack) == int(r_pack):
        return "", None

    new_standing = db.adjust_pack_relation(guild_id, int(h_pack), int(r_pack), -1)
    note = (
        f"\n\n_rival fresh-kill; **{rival['wolf_name']}** contests the pile. "
        f"pack standing **−1** (now **{new_standing}/10**)._"
    )
    note += format_standing_war_flash(guild_id, int(h_pack), int(r_pack), new_standing)
    enc_id = start_rival_wolf_skirmish(
        hunter,
        rival,
        guild_id=guild_id,
        channel_id=channel_id,
    )
    if enc_id:
        note += "\n_Combat is live; drive them off or break away via the panel._"
    return note, enc_id


# Lore-grounded opening stances (0-10 scale; see HOSTILE/FRIENDLY/WAR thresholds
# above). Drawn from each Great Pack's "Relations with Other Packs" lore:
# Greyspire is wary-but-trading with Silverrush, disgusted by Mistmoor, and in
# open border dispute with Thistlehide; Silverrush is cautiously allied with
# Thistlehide (shared Twoleg threats) and trades reluctantly with Mistmoor for
# rot-cure knowledge; Thistlehide avoids Mistmoor entirely (a marsh separates
# them, so no active border friction). Only seeds pairs still at the untouched
# default of 5, so it never overwrites diplomacy that's already been played out.
LORE_OPENING_STANDINGS: dict[frozenset[str], int] = {
    frozenset({"greyspire", "silverrush"}): 6,  # wary but trade fish for herbs
    frozenset({"greyspire", "mistmoor"}): 2,  # "belly-lickers"; disgust
    frozenset({"greyspire", "thistlehide"}): 3,  # open border dispute, high valley
    frozenset({"silverrush", "mistmoor"}): 4,  # distrust, but reluctant trade
    frozenset({"silverrush", "thistlehide"}): 8,  # cautious alliance vs Twolegs
    frozenset({"thistlehide", "mistmoor"}): 3,  # avoidance; marsh keeps borders apart
}


def seed_lore_pack_relations(guild_id: int) -> list[str]:
    """
    Apply LORE_OPENING_STANDINGS for a guild's four Great Packs. Only touches
    pairs still sitting at the untouched default (5); returns a list of
    human-readable change lines for anything it actually set.
    """
    changes: list[str] = []
    for pair_keys, standing in LORE_OPENING_STANDINGS.items():
        key_a, key_b = sorted(pair_keys)
        pack_a = db.get_pack_by_key(key_a)
        pack_b = db.get_pack_by_key(key_b)
        if not pack_a or not pack_b:
            continue
        current = db.get_pack_relation(guild_id, int(pack_a["id"]), int(pack_b["id"]))
        if current != NEUTRAL_STANDING:
            continue
        db.adjust_pack_relation(guild_id, int(pack_a["id"]), int(pack_b["id"]), standing - NEUTRAL_STANDING)
        changes.append(f"{pack_a['name']} <-> {pack_b['name']}: {NEUTRAL_STANDING} -> {standing}")
    return changes


def court_relation_note(courter, target, guild_id: int | None, effective: str) -> str | None:
    """footer line when cross-pack standing shaped court difficulty."""
    standing = cross_pack_relation(courter, target, guild_id)
    if standing is None:
        return None
    tag = relation_tag(standing)
    if effective == "friendly" and tag == "friendly":
        return f"_rival standing **{standing}/10** (friendly) eased the approach._"
    if effective == "hostile" and tag in ("hostile", "war"):
        return (
            f"_rival standing **{standing}/10** ({tag}); the den reads your court as a challenge._"
        )
    if tag == "neutral":
        return f"_cross-pack standing **{standing}/10** (neutral)._"
    return None
