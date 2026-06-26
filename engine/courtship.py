"""Court difficulty from standing and court failure penalties."""

from __future__ import annotations

import database as db
from config import (
    COURT_FAIL_MOOD_LOSS,
    COURT_HOSTILE_FAIL_MOOD_LOSS,
    COURT_SUCCESS_MOOD_GAIN,
)
from engine.family import COURTSHIP_DCS, courtship_check
from engine.pack_relations import (
    FRIENDLY_STANDING_THRESHOLD,
    HOSTILE_STANDING_THRESHOLD,
    cross_pack_relation,
    relation_tag,
)


def suggest_court_difficulty(courter, target, guild_id: int | None) -> str:
    """Pick friendly / neutral / hostile from pack relations or personal standing."""
    c_pack = courter["pack_id"] if "pack_id" in courter.keys() else None
    t_pack = target["pack_id"] if "pack_id" in target.keys() else None
    if c_pack and t_pack and c_pack != t_pack and guild_id:
        rel = db.get_pack_relation(guild_id, c_pack, t_pack)
        if rel <= HOSTILE_STANDING_THRESHOLD:
            return "hostile"
        if rel >= FRIENDLY_STANDING_THRESHOLD:
            return "friendly"
        return "neutral"
    standing = int(target["standing"]) if "standing" in target.keys() else 5
    if standing <= HOSTILE_STANDING_THRESHOLD:
        return "hostile"
    if standing >= FRIENDLY_STANDING_THRESHOLD:
        return "friendly"
    return "neutral"


def resolve_court_difficulty(courter, target, guild_id: int | None, chosen: str) -> tuple[str, str | None]:
    """Return (effective difficulty, optional footnote when overriding standing suggestion)."""
    suggested = suggest_court_difficulty(courter, target, guild_id)
    if chosen == "auto":
        return suggested, None
    if chosen != suggested:
        dc = COURTSHIP_DCS.get(chosen, 15)
        sdc = COURTSHIP_DCS.get(suggested, 15)
        return chosen, (
            f"_Standing suggests **{suggested}** (DC {sdc}); you chose **{chosen}** (DC {dc})._"
        )
    return chosen, None


def apply_court_bond(user, target_user, result: dict, difficulty: str, *, day: int) -> str | None:
    """Friendship bond strength from a successful court."""
    if not result["success"]:
        return None
    delta = 15 if result["outcome"] == "critical_success" else 10
    if difficulty == "friendly":
        delta += 5
    row = db.adjust_bond_strength(user["id"], target_user["id"], "friendship", delta, day=day)
    if not row:
        return None
    from engine.bonds import strength_bar, strength_tier

    return (
        f"Friendship with **{target_user['wolf_name']}** "
        f"{strength_bar(row['strength'])} ({strength_tier(row['strength'])})."
    )


def apply_court_outcome(
    user,
    target_user,
    result: dict,
    difficulty: str,
    *,
    guild_id: int | None = None,
    day: int = 0,
) -> str:
    """Mood changes for court success or failure. Returns extra lines for the embed."""
    lines: list[str] = []
    if result["success"]:
        your_mood = db.adjust_mood(user["id"], COURT_SUCCESS_MOOD_GAIN)
        their_mood = db.adjust_mood(target_user["id"], COURT_SUCCESS_MOOD_GAIN)
        lines.append(
            f"**+{COURT_SUCCESS_MOOD_GAIN} mood** each "
            f"(you: **{your_mood}**, them: **{their_mood}**)."
        )
        bond_line = apply_court_bond(user, target_user, result, difficulty, day=day)
        if bond_line:
            lines.append(bond_line)
        standing = cross_pack_relation(user, target_user, guild_id)
        if standing is not None and difficulty == "hostile" and relation_tag(standing) in (
            "hostile",
            "war",
        ):
            pack_a = int(user["pack_id"])
            pack_b = int(target_user["pack_id"])
            new_rel = db.adjust_pack_relation(guild_id, pack_a, pack_b, -1)
            lines.append(
                f"Cross-pack court on hostile ground; den standing **−1** (now **{new_rel}/10**)."
            )
        return "\n".join(lines)
    loss = COURT_HOSTILE_FAIL_MOOD_LOSS if difficulty == "hostile" else COURT_FAIL_MOOD_LOSS
    your_mood = db.adjust_mood(user["id"], -loss)
    lines.append(f"**−{loss} mood** for you (**{your_mood}**).")
    if difficulty == "hostile":
        their_mood = db.adjust_mood(target_user["id"], -2)
        lines.append(f"**−2 mood** for them (**{their_mood}**); offense taken.")
    return "\n".join(lines)


def run_court_check(user, difficulty: str) -> dict:
    return courtship_check(user, difficulty)
