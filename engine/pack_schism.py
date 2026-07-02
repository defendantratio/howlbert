"""Pack schism; den splits when unity collapses and a faction leader emerges."""

from __future__ import annotations

import database as db

SCHISM_UNITY_THRESHOLD = 30
SCHISM_MIN_PACK_SIZE = 4
SCHISM_BOND_THRESHOLD = 55
SCHISM_UNITY_PENALTY = 20
SCHISM_STARTING_STANDING = 3
SCHISM_LEADER_STANDING_GAIN = 3
SCHISM_OLD_ALPHA_STANDING_LOSS = 2


def can_schism(user, pack) -> tuple[bool, str]:
    """Check whether this wolf can lead a schism right now."""
    from engine.role_restrictions import wolf_role
    role = wolf_role(user)
    if role in ("pup",):
        return False, "pups don't lead schisms."
    unity = int(pack["pack_unity"]) if "pack_unity" in pack.keys() else 100
    if unity > SCHISM_UNITY_THRESHOLD:
        return False, (
            f"the den is too unified to fracture — pack unity **{unity}/100**. "
            f"a schism needs unity below **{SCHISM_UNITY_THRESHOLD}**."
        )
    with db.get_db() as conn:
        member_count = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE pack_id = ? AND condition NOT IN ('dead', 'dying')",
            (pack["id"],),
        ).fetchone()["c"]
    if member_count < SCHISM_MIN_PACK_SIZE:
        return False, f"the den is too small to split — need at least **{SCHISM_MIN_PACK_SIZE}** wolves."
    return True, ""


def execute_schism(
    leader,
    *,
    pack,
    guild_id: int,
    new_pack_name: str,
    day: int,
) -> tuple[bool, str]:
    """
    Split the pack. The leader takes bonded wolves, a treasury share,
    and hostile standing with the old den.
    """
    ok, block = can_schism(leader, pack)
    if not ok:
        return False, block

    old_pack_id = int(pack["id"])
    old_alpha_id = int(pack["alpha_id"]) if pack["alpha_id"] else None

    with db.get_db() as conn:
        members = conn.execute(
            "SELECT * FROM users WHERE pack_id = ? AND condition NOT IN ('dead', 'dying')",
            (old_pack_id,),
        ).fetchall()

    followers = []
    for m in members:
        if int(m["id"]) == int(leader["id"]):
            continue
        bond = db.get_bond(leader["id"], m["id"], "romance") or \
               db.get_bond(leader["id"], m["id"], "friendship") or \
               db.get_bond(leader["id"], m["id"], "kin")
        if bond and int(bond["strength"]) >= SCHISM_BOND_THRESHOLD:
            followers.append(m)

    faction_size = 1 + len(followers)
    old_size = len(members)
    treasury = int(pack["treasury"]) if "treasury" in pack.keys() else 0
    split_treasury = int(treasury * faction_size / max(1, old_size))

    new_pack_id = db.create_pack(new_pack_name.strip(), leader["id"])

    with db.get_db() as conn:
        conn.execute(
            "UPDATE users SET pack_id = ?, wolf_role = 'alpha' WHERE id = ?",
            (new_pack_id, leader["id"]),
        )
        for f in followers:
            conn.execute(
                "UPDATE users SET pack_id = ? WHERE id = ?",
                (new_pack_id, f["id"]),
            )
        if split_treasury > 0:
            conn.execute("UPDATE packs SET treasury = treasury - ? WHERE id = ?", (split_treasury, old_pack_id))
            conn.execute("UPDATE packs SET treasury = ? WHERE id = ?", (split_treasury, new_pack_id))
        conn.execute(
            "UPDATE packs SET pack_unity = MAX(0, pack_unity - ?) WHERE id = ?",
            (SCHISM_UNITY_PENALTY, old_pack_id),
        )
        conn.execute(
            "UPDATE packs SET pack_unity = ? WHERE id = ?",
            (max(0, 50 - SCHISM_UNITY_PENALTY), new_pack_id),
        )

    db.adjust_pack_relation(guild_id, old_pack_id, new_pack_id, -(10 - SCHISM_STARTING_STANDING))
    db.adjust_wolf_standing(leader["discord_id"], SCHISM_LEADER_STANDING_GAIN)
    if old_alpha_id and old_alpha_id != leader["id"]:
        old_alpha = db.get_user_by_id(old_alpha_id)
        if old_alpha:
            db.adjust_wolf_standing(old_alpha["discord_id"], -SCHISM_OLD_ALPHA_STANDING_LOSS)

    follower_names = [f["wolf_name"] for f in followers]
    body = (
        f"**{leader['wolf_name']}** leads a schism from **{pack['name']}**, "
        f"founding **{new_pack_name}**."
    )
    if follower_names:
        body += f"\n\nFollowers: **{', '.join(follower_names)}**."
    else:
        body += "\n\n_No packmates bonded deeply enough to follow — you walk alone into this new den._"
    body += (
        f"\n\nTreasury split: **{split_treasury:,}** bones carried over. "
        f"Standing between **{pack['name']}** and **{new_pack_name}**: **{SCHISM_STARTING_STANDING}/10** (hostile). "
        f"Pack unity in **{pack['name']}**: **−{SCHISM_UNITY_PENALTY}**."
    )
    return True, body
