"""Restricted herb standing penalties for non-Medic misuse and hoarding."""

from __future__ import annotations

import random

import database as db
from config import (
    RESTRICTED_HERB_GROOM_CATCH_CHANCE,
    RESTRICTED_HERB_GROOM_CAUGHT_TEXT,
    RESTRICTED_HERB_HOARD_CATCH_CHANCE,
    RESTRICTED_HERB_HOARD_CAUGHT_TEXT,
    RESTRICTED_HERB_HOARD_STANDING,
    RESTRICTED_HERB_HOARD_WARN,
    RESTRICTED_HERB_MEDIC_ROUNDS_CATCH_CHANCE,
    RESTRICTED_HERB_MISUSE_STANDING,
    RESTRICTED_HERB_SNIFF_CATCH_CHANCE,
    RESTRICTED_HERB_SNIFF_CAUGHT_TEXT,
)
from engine.role_features import is_full_medic
from herbs import HERBS

RESTRICTED_HERBS = frozenset(
    {
        "bloodroot",
        "deadly_nightshade",
        "deathberries",
        "foxglove",
        "holly_berries",
        "oleander",
        "poison_ivy",
        "water_hemlock",
        "wintergreen",
        "wolfsbane",
    }
)


def is_restricted_herb(herb_key: str) -> bool:
    if herb_key in RESTRICTED_HERBS:
        return True
    meta = HERBS.get(herb_key, {})
    return meta.get("rarity") == "restricted"


def format_herb_names(keys: set[str] | frozenset[str]) -> str:
    return ", ".join(
        HERBS.get(k, {}).get("name", k.replace("_", " ").title()) for k in sorted(keys)
    )


def restricted_held_by_user(user) -> set[str]:
    if not user:
        return frozenset()
    held: set[str] = set()
    for row in db.get_inventory_for_wolf(user["id"]):
        if not row["key"].startswith("herb_"):
            continue
        herb_key = row["key"].replace("herb_", "", 1)
        if is_restricted_herb(herb_key) and int(row["quantity"]) > 0:
            held.add(herb_key)
    return frozenset(held)


def format_standing_penalty(kick_msg: str, delta: int) -> str:
    sign = "−" if delta < 0 else "+"
    note = f"standing **{sign}{abs(delta)}**."
    if kick_msg:
        return f"{note} {kick_msg}"
    return note


def roll_restricted_hoard_caught(chance: float | None = None) -> bool:
    odds = RESTRICTED_HERB_HOARD_CATCH_CHANCE if chance is None else chance
    return random.random() < odds


def penalize_restricted_misuse(wolf_id: int, reason: str) -> str:
    """apply standing loss when a non-medic misuses a restricted herb. returns kick text."""
    _ = reason
    return db.adjust_wolf_standing_by_id(wolf_id, RESTRICTED_HERB_MISUSE_STANDING)


def penalize_restricted_hoarding(wolf_id: int) -> str:
    """Apply standing loss when a non-Medic is caught hoarding restricted herbs."""
    return db.adjust_wolf_standing_by_id(wolf_id, RESTRICTED_HERB_HOARD_STANDING)


def apply_caught_hoarding(
    user,
    held: set[str],
    *,
    flavor: str,
) -> str:
    """Penalize a caught hoarder; returns user-facing note."""
    kick = penalize_restricted_hoarding(user["id"])
    standing = format_standing_penalty(kick, RESTRICTED_HERB_HOARD_STANDING)
    return f"**caught hoarding poison herbs**; {flavor}\n{standing}"


def medic_rounds_scan_hoarders(pack_id: int) -> tuple[list[dict], list[str]]:
    """
    Medicine den walk: roll catch per hoarder; missed rolls become suspicious scent notes.
    Returns (caught entries with standing applied, suspicious lines without penalty).
    """
    wolves = db.get_pack_den_wolves(pack_id)
    caught: list[dict] = []
    suspicious: list[str] = []
    for wolf in wolves:
        if is_full_medic(wolf):
            continue
        held = restricted_held_by_user(wolf)
        if not held:
            continue
        names = format_herb_names(held)
        if roll_restricted_hoard_caught(RESTRICTED_HERB_MEDIC_ROUNDS_CATCH_CHANCE):
            flavor = (
                f"**den checkup** found **{names}** in **{wolf['wolf_name']}**'s inventory; "
                "poison plants belong in the healers' store."
            )
            note = apply_caught_hoarding(wolf, held, flavor=flavor)
            caught.append(
                {
                    "wolf_name": wolf["wolf_name"],
                    "discord_id": wolf["discord_id"],
                    "note": note,
                }
            )
        else:
            suspicious.append(
                f"**{wolf['wolf_name']}**: bitter poison-scent near the bedding "
                f"({names} suspected; stash not opened)"
            )
    return caught, suspicious


def medic_rounds_catch_hoarders(pack_id: int) -> list[dict]:
    """backward-compatible wrapper returning only caught wolves."""
    caught, _ = medic_rounds_scan_hoarders(pack_id)
    return caught


def try_catch_restricted_hoarder(
    user,
    *,
    chance: float | None = None,
    flavor_pool: tuple[str, ...] | list[str] | None = None,
    flavor_kwargs: dict | None = None,
) -> str | None:
    """
    Roll whether a non-Medic hoarding restricted herbs is caught.
    Returns standing note or None if not hoarding, exempt, or not caught.
    """
    if not user or is_full_medic(user):
        return None
    held = restricted_held_by_user(user)
    if not held:
        return None
    if not roll_restricted_hoard_caught(chance):
        return None
    pool = flavor_pool or RESTRICTED_HERB_HOARD_CAUGHT_TEXT
    kwargs = {"herbs": format_herb_names(held)}
    if flavor_kwargs:
        kwargs.update(flavor_kwargs)
    flavor = random.choice(pool).format(**kwargs)
    return apply_caught_hoarding(user, held, flavor=flavor)


def on_restricted_herb_acquired(user, herb_key: str) -> str:
    """
    call when a restricted herb enters a wolf's personal forage bag.
    no automatic standing loss; warn non-medics to turn herbs in.
    """
    if not user or not is_restricted_herb(herb_key):
        return ""
    if is_full_medic(user):
        return ""
    name = HERBS.get(herb_key, {}).get("name", herb_key.replace("_", " ").title())
    return (
        f"**{name}** is medic knowledge. {RESTRICTED_HERB_HOARD_WARN}\n"
        "_use `/herbs action:turnin` to hand it to the healers' den safely._"
    )


def on_restricted_herb_treat(healer, herb_key: str) -> str:
    """Standing penalty when a non-Medic uses a restricted herb via /treat (always caught)."""
    if not healer or not is_restricted_herb(herb_key):
        return ""
    if is_full_medic(healer):
        return ""
    kick = penalize_restricted_misuse(healer["id"], "treat")
    return format_standing_penalty(kick, RESTRICTED_HERB_MISUSE_STANDING)


def herbbag_hoard_warning(user) -> str:
    """footer note when a non-medic's bag still holds restricted herbs."""
    if not user or is_full_medic(user):
        return ""
    held = restricted_held_by_user(user)
    if not held:
        return ""
    names = format_herb_names(held)
    return (
        f"\n\n⚠ **restricted in inventory:** {names}.\n"
        f"{RESTRICTED_HERB_HOARD_WARN}\n"
        "_use `/herbs action:turnin` before a patrol catches the scent._"
    )


def try_catch_hoarder_on_sniff(user) -> str | None:
    """Wolvden-style: poison scent on the wind may expose a hoarder."""
    return try_catch_restricted_hoarder(
        user,
        chance=RESTRICTED_HERB_SNIFF_CATCH_CHANCE,
        flavor_pool=RESTRICTED_HERB_SNIFF_CAUGHT_TEXT,
    )


def try_catch_hoarder_on_groom(groomer, target) -> str | None:
    """Warriors-style: close grooming may reveal poison herbs on the target's coat."""
    groomer_name = groomer["wolf_name"] if groomer else "A packmate"
    return try_catch_restricted_hoarder(
        target,
        chance=RESTRICTED_HERB_GROOM_CATCH_CHANCE,
        flavor_pool=RESTRICTED_HERB_GROOM_CAUGHT_TEXT,
        flavor_kwargs={"groomer": groomer_name},
    )


def audit_restricted_hoarding(user) -> str | None:
    """Rollover: chance a non-Medic hoarding restricted herbs is caught at the den."""
    return try_catch_restricted_hoarder(user)


def apply_restricted_hoard_audit_on_rollover(conn) -> list[dict]:
    """roll catch checks for non-medics still hoarding restricted herbs each sunrise."""
    rows = conn.execute(
        """
        SELECT DISTINCT u.id AS wolf_id
        FROM users u
        JOIN inventory i ON i.wolf_id = u.id
        JOIN items it ON it.id = i.item_id
        WHERE it.key LIKE 'herb_%' AND i.quantity > 0
        """
    ).fetchall()
    notes: list[dict] = []
    seen: set[int] = set()
    for row in rows:
        wolf_id = int(row["wolf_id"])
        if wolf_id in seen:
            continue
        seen.add(wolf_id)
        user = db.get_user_by_id(wolf_id)
        if not user:
            continue
        msg = audit_restricted_hoarding(user)
        if msg:
            notes.append(
                {
                    "wolf_name": user["wolf_name"],
                    "discord_id": user["discord_id"],
                    "note": msg,
                }
            )
    return notes
