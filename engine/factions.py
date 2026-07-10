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


def resolve_faction(key) -> dict | None:
    """Descriptor for a canonical or founded faction, or None if the key is not
    a faction (loner / rogue / unknown)."""
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
                "pack_trait": "**Founders' Grit**: a young pack forged from lone wolves who chose each other.",
                "founded": True,
                "pack_id": pid,
            }
    return None


def is_faction(key) -> bool:
    """True for a canonical great pack or a live founded pack (not loner/rogue)."""
    return resolve_faction(key) is not None


def faction_name(key, default: str = "a rival den") -> str:
    info = resolve_faction(key)
    return info["name"] if info else default
