"""Healer's Code; cannot refuse the sick (soft nudges)."""

from __future__ import annotations

import database as db
from engine.role_features import is_full_medic

HEALER_REFUSAL_TEXT = (
    "_**healer's code:** a packmate is **dying** in the den. "
    "you cannot refuse the sick; `/medic action:stabilize` or urge `/medic action:deathsaves`._"
)


def dying_packmates(pack_id: int, *, exclude_wolf_id: int | None = None) -> list:
    if not pack_id:
        return []
    out = []
    for wolf in db.get_pack_den_wolves(pack_id):
        if exclude_wolf_id and wolf["id"] == exclude_wolf_id:
            continue
        cond = wolf["condition"] if "condition" in wolf.keys() else "healthy"
        hp = int(wolf["hp"]) if "hp" in wolf.keys() else 10
        if cond == "dying" or (hp <= 0 and cond != "dead"):
            out.append(wolf)
    return out


def healer_refusal_reminder(user, *, pack_id: int | None = None) -> str | None:
    if not is_full_medic(user):
        return None
    pid = pack_id or (user["pack_id"] if "pack_id" in user.keys() else None)
    if not pid:
        return None
    dying = dying_packmates(pid, exclude_wolf_id=user["id"])
    if not dying:
        return None
    names = ", ".join(f"**{w['wolf_name']}**" for w in dying[:3])
    extra = f" (+{len(dying) - 3} more)" if len(dying) > 3 else ""
    return HEALER_REFUSAL_TEXT.replace("a packmate", names + extra)


def rot_lung_outbreak_news(pack_id: int, *, threshold: int = 2) -> str | None:
    """Seasonal den news when rot-lung spreads in the pack."""
    if not pack_id:
        return None
    from engine.diseases import parse_disease

    count = 0
    for wolf in db.get_pack_den_wolves(pack_id):
        key, _ = parse_disease(wolf["disease"] if "disease" in wolf.keys() else None)
        if key == "rot_lung":
            count += 1
    if count < threshold:
        return None
    return (
        f"**rot-lung** weighs on **{count}** den-mates; mullein and marsh-mallow courses, "
        "strict rest, and quarantine before the mire claims more breath."
    )
