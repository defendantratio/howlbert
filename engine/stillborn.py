"""Pending lethal-at-birth pups; saved with Vitality Salve (Wolvden-style)."""

from __future__ import annotations

import json

import database as db
from engine.genetics import GENETIC_CONDITIONS, encode_genetic_conditions


def format_stillborn_save_hint(pup_name: str, conditions: list[str]) -> str:
    label = GENETIC_CONDITIONS[conditions[0]]["name"] if conditions else "Lethal mutation"
    return (
        f"**{pup_name}**; **{label}**; fading fast. "
        f"Use **`/pupcare action:save name:{pup_name}`** with **Vitality Salve** from `/bones action:shop` "
        f"(same sunrise only)."
    )


def save_pending_stillborn(
    *,
    discord_id: int,
    mother_wolf_id: int,
    pup_name: str,
    genetic_conditions: list[str],
    stats: dict,
    father_wolf_id: int | None,
    pack_id: int | None,
    great_pack: str | None,
    birth_sex: str,
    born_day: int,
) -> int:
    return db.add_pending_stillborn(
        discord_id=discord_id,
        mother_wolf_id=mother_wolf_id,
        pup_name=pup_name,
        genetic_conditions=encode_genetic_conditions(genetic_conditions),
        stats_json=json.dumps(stats),
        father_wolf_id=father_wolf_id,
        pack_id=pack_id,
        great_pack=great_pack,
        birth_sex=birth_sex,
        born_day=born_day,
    )


def try_save_stillborn_pup(discord_id: int, pup_name: str, *, current_day: int) -> tuple[bool, str]:
    """Consume vitality_salve and register the pup. Returns (ok, message)."""
    row = db.get_pending_stillborn(discord_id, pup_name.strip())
    if not row:
        return False, f"No dying pup named **{pup_name}** awaiting neonatal care on your account."
    if int(row["born_day"]) != current_day:
        db.delete_pending_stillborn(row["id"])
        return False, (
            f"**{pup_name}** needed Vitality Salve on the sunrise they were born; "
            "the window has passed."
        )

    item = db.get_item_by_key("vitality_salve")
    if not item or db.get_inventory_quantity(discord_id, item["id"]) < 1:
        return False, (
            "You need **Vitality Salve** from `/bones action:shop` in your inventory. "
            f"Use **`/pupcare action:save name:{pup_name}`**."
        )

    if db.wolf_name_taken(pup_name) or db.pending_pup_name_taken(pup_name):
        db.delete_pending_stillborn(row["id"])
        return False, (
            f"The name **{pup_name}** is already taken or reserved for neonatal care."
        )

    stats = json.loads(row["stats_json"])
    db.consume_item(discord_id, item["id"])
    db.register_born_wolf(
        discord_id=discord_id,
        wolf_name=row["pup_name"],
        mother_wolf_id=row["mother_wolf_id"],
        father_wolf_id=row["father_wolf_id"],
        stats=stats,
        pack_id=row["pack_id"],
        great_pack=row["great_pack"],
        birth_sex=row["birth_sex"],
        genetic_conditions=row["genetic_conditions"],
    )
    db.delete_pending_stillborn(row["id"])
    genetics = json.loads(row["genetic_conditions"] or "[]")
    mut = ""
    if genetics:
        names = ", ".join(GENETIC_CONDITIONS[k]["name"] for k in genetics if k in GENETIC_CONDITIONS)
        mut = f" They carry **{names}**; alive, but changed."
    return True, (
        f"**Vitality Salve** steadies **{row['pup_name']}**'s breath.{mut} "
        "Use `/switchwolf` to play them."
    )
