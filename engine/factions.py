"""Faction resolver: canonical great packs *and* player-founded packs.

The four canonical great packs live in ``config.GREAT_PACKS`` keyed by a static
key. A pack founded by two lone wolves (see engine.found_pack) is a real row in
the ``packs`` table; its wolves carry the faction key ``founded_<pack_id>``.
``resolve_faction`` turns either kind of key into the same descriptor shape
(name / path / motto / pack_trait), so display, standing, and relations treat a
founded pack as a first-class faction instead of falling back to "loner".
"""

from __future__ import annotations

FOUNDED_PREFIX = "founded_"


def is_founded_key(key) -> bool:
    return isinstance(key, str) and key.startswith(FOUNDED_PREFIX)


def founded_pack_id(key) -> int | None:
    if is_founded_key(key):
        try:
            return int(key[len(FOUNDED_PREFIX):])
        except (TypeError, ValueError):
            return None
    return None


def founded_key_for(pack_id: int) -> str:
    return f"{FOUNDED_PREFIX}{int(pack_id)}"


FOUNDERS_GRIT = "**Founders' Grit**: a young pack forged from lone wolves who chose each other."


def resolve_faction(key) -> dict | None:
    """Descriptor for a canonical or founded faction, or None if the key is not
    a faction (loner / rogue / unknown). Cheap: no per-member query (this is
    called from hot paths like combat/activities). For the blended heritage
    trait shown on a founded pack's profile, see ``founded_pack_heritage_trait``."""
    from config import GREAT_PACKS

    if key in GREAT_PACKS:
        return GREAT_PACKS[key]
    pid = founded_pack_id(key)
    if pid is not None:
        import database as db

        pack = db.get_pack(pid)
        if pack:
            return {
                "name": pack["name"],
                "path": "a founded pack; dispersers who raised their own den",
                "motto": "we made our own way",
                "pack_trait": FOUNDERS_GRIT,
                "founded": True,
                "pack_id": pid,
            }
    return None


def founded_pack_heritage_keys(pack_id: int) -> set[str]:
    """Great pack keys currently represented in the den, drawn from every
    living member's former_great_pack (see assign_pack_affiliation) — not
    just the two original founders, so this grows and shrinks as membership
    changes. Used both for display (founded_pack_heritage_trait) and for the
    mechanical effects in engine.pack_traits."""
    import database as db

    keys: set[str] = set()
    for member in db.get_pack_members(pack_id):
        gp_key = member["former_great_pack"] if "former_great_pack" in member.keys() else None
        if gp_key:
            keys.add(gp_key)
    return keys


def founded_pack_heritage_trait(pack_id: int) -> str:
    """Founders' Grit plus a line for each great pack trait represented in
    the den right now (see founded_pack_heritage_keys)."""
    from config import GREAT_PACKS

    traits = [FOUNDERS_GRIT]
    for gp_key in GREAT_PACKS:
        if gp_key in founded_pack_heritage_keys(pack_id):
            traits.append(f"**{GREAT_PACKS[gp_key]['name']} heritage**: {GREAT_PACKS[gp_key]['pack_trait']}")
    return "\n".join(traits)


def is_faction(key) -> bool:
    """True for a canonical great pack or a live founded pack (not loner/rogue)."""
    return resolve_faction(key) is not None


def faction_name(key, default: str = "a rival den") -> str:
    info = resolve_faction(key)
    return info["name"] if info else default


def resolve_pack_target(target: str) -> tuple[int | None, str] | None:
    """Resolve a raid/relation target named by faction key OR pack name to
    ``(pack_id, faction_key)``; handles the four canonical great packs and any
    founded pack. Returns None if no such faction is found."""
    from config import GREAT_PACKS
    import database as db

    t = (target or "").strip().lower()
    if not t:
        return None
    for k, info in GREAT_PACKS.items():
        if t == k or t == info["name"].lower():
            row = db.get_pack_by_key(k)
            return (row["id"] if row else None, k)
    if is_founded_key(target):
        pid = founded_pack_id(target)
        if pid and db.get_pack(pid):
            return (pid, target)
    row = db.get_pack_by_name(target.strip())
    if row:
        key = row["key"] if "key" in row.keys() else None
        if not key:  # a founded pack carries no canonical key
            return (row["id"], founded_key_for(row["id"]))
    return None
