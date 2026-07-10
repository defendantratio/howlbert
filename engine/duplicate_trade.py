"""Detect and move duplicate hoard items (keep one of each)."""

from __future__ import annotations

from dataclasses import dataclass, field

import database as db


@dataclass
class DuplicateBundle:
    inventory: list[tuple[int, int, str]] = field(default_factory=list)  # item_id, qty, name
    amusement_ids: list[int] = field(default_factory=list)
    amusement_labels: list[str] = field(default_factory=list)
    herb_ids: list[int] = field(default_factory=list)
    herb_labels: list[str] = field(default_factory=list)

    @property
    def total_items(self) -> int:
        inv = sum(q for _, q, _ in self.inventory)
        return inv + len(self.amusement_ids) + len(self.herb_ids)

    def is_empty(self) -> bool:
        return self.total_items == 0


def collect_duplicates(wolf_id: int) -> DuplicateBundle:
    """extra inventory qty, toy stacks, and herb stacks beyond one per type."""
    bundle = DuplicateBundle()

    with db.get_db() as conn:
        inv_rows = conn.execute(
            """
            SELECT inv.item_id, inv.quantity, i.name
            FROM inventory inv
            JOIN items i ON i.id = inv.item_id
            WHERE inv.wolf_id = ? AND inv.quantity > 1
            """,
            (wolf_id,),
        ).fetchall()
        for row in inv_rows:
            dupes = int(row["quantity"]) - 1
            if dupes > 0:
                bundle.inventory.append((int(row["item_id"]), dupes, row["name"]))

    from engine.amusement_items import amusement_meta

    stacks = db.get_amusement_stacks(wolf_id)
    by_key: dict[str, list] = {}
    for stack in stacks:
        by_key.setdefault(stack["item_key"], []).append(stack)
    for key, group in by_key.items():
        if len(group) <= 1:
            continue
        group.sort(key=lambda s: (-int(s["uses_left"]), int(s["id"])))
        for extra in group[1:]:
            meta = amusement_meta(extra["item_key"])
            bundle.amusement_ids.append(int(extra["id"]))
            bundle.amusement_labels.append(meta["name"])

    herb_rows = db.get_herb_stacks(wolf_id)
    by_herb: dict[tuple[str, str], list] = {}
    for stack in herb_rows:
        key = (stack["herb_key"], stack["form"])
        by_herb.setdefault(key, []).append(stack)
    for (_hk, _form), group in by_herb.items():
        if len(group) <= 1:
            continue
        group.sort(key=lambda s: (-int(s["potency"]), int(s["id"])))
        for extra in group[1:]:
            from herbs import HERBS

            label = HERBS.get(extra["herb_key"], {}).get("name", extra["herb_key"])
            bundle.herb_ids.append(int(extra["id"]))
            bundle.herb_labels.append(f"{label} ({extra['form']})")

    return bundle


def format_duplicate_summary(bundle: DuplicateBundle) -> str:
    if bundle.is_empty():
        return "no duplicates; you keep one of each item, toy stack, and herb stack."
    lines: list[str] = []
    for _iid, qty, name in bundle.inventory:
        lines.append(f"**{name}** x{qty}")
    for label in bundle.amusement_labels:
        lines.append(f"toy: **{label}**")
    for label in bundle.herb_labels:
        lines.append(f"herb: **{label}**")
    return "\n".join(lines)


def transfer_duplicates(from_wolf_id: int, to_wolf_id: int, bundle: DuplicateBundle) -> tuple[bool, str]:
    if from_wolf_id == to_wolf_id:
        return False, "can't trade duplicates to yourself."
    if bundle.is_empty():
        return False, "nothing duplicate to trade."

    from database import _move_item_conn

    moved: list[str] = []
    with db.get_db() as conn:
        for item_id, qty, name in bundle.inventory:
            if not _move_item_conn(conn, from_wolf_id, to_wolf_id, item_id, qty):
                conn.rollback()
                return False, f"transfer failed on **{name}**; try again."
            moved.append(f"**{name}** x{qty}")

        for stack_id in bundle.amusement_ids:
            stack = conn.execute(
                "SELECT * FROM amusement_stacks WHERE id = ?", (stack_id,)
            ).fetchone()
            if not stack or int(stack["wolf_id"]) != from_wolf_id:
                continue
            from engine.amusement_items import amusement_meta

            meta = amusement_meta(stack["item_key"])
            cur = conn.execute(
                "UPDATE amusement_stacks SET wolf_id = ? WHERE id = ? AND wolf_id = ?",
                (to_wolf_id, stack_id, from_wolf_id),
            )
            if cur.rowcount != 1:
                conn.rollback()
                return False, f"couldn't pass toy **{meta['name']}**."
            moved.append(f"toy **{meta['name']}**")

        for stack_id in bundle.herb_ids:
            stack = conn.execute(
                "SELECT * FROM herb_stacks WHERE id = ?", (stack_id,)
            ).fetchone()
            if not stack or int(stack["wolf_id"]) != from_wolf_id:
                continue
            from herbs import HERBS

            label = HERBS.get(stack["herb_key"], {}).get("name", stack["herb_key"])
            cur = conn.execute(
                "UPDATE herb_stacks SET wolf_id = ? WHERE id = ? AND wolf_id = ?",
                (to_wolf_id, stack_id, from_wolf_id),
            )
            if cur.rowcount != 1:
                conn.rollback()
                return False, f"couldn't pass **{label}**."
            moved.append(f"herb **{label}** ({stack['form']})")

    body = "\n".join(f"• {line}" for line in moved[:20])
    if len(moved) > 20:
        body += f"\n_…and {len(moved) - 20} more._"
    return True, body


def surrender_duplicates(wolf_id: int, bundle: DuplicateBundle) -> tuple[bool, str]:
    """remove duplicates (cat tribute); not recoverable."""
    if bundle.is_empty():
        return False, "no duplicates to offer."

    removed: list[str] = []
    for item_id, qty, name in bundle.inventory:
        if not db.consume_item_for_wolf(wolf_id, item_id, qty):
            return False, f"couldn't surrender **{name}**."
        removed.append(f"**{name}** x{qty}")

    for stack_id in bundle.amusement_ids:
        stack = db.get_amusement_stack(stack_id)
        if not stack or int(stack["wolf_id"]) != wolf_id:
            continue
        from engine.amusement_items import amusement_meta

        meta = amusement_meta(stack["item_key"])
        db.remove_amusement_stack(stack_id)
        removed.append(f"toy **{meta['name']}**")

    for stack_id in bundle.herb_ids:
        stack = db.get_herb_stack(stack_id)
        if not stack or int(stack["wolf_id"]) != wolf_id:
            continue
        from herbs import HERBS

        label = HERBS.get(stack["herb_key"], {}).get("name", stack["herb_key"])
        db.remove_herb_stack(stack_id)
        removed.append(f"herb **{label}** ({stack['form']})")

    body = "\n".join(f"• {line}" for line in removed[:20])
    if len(removed) > 20:
        body += f"\n_…and {len(removed) - 20} more._"
    return True, body


def duplicate_trust_gain(bundle: DuplicateBundle) -> int:
    from config import (
        CAT_PACT_DUP_TRUST_PER_ITEM,
        CAT_PACT_DUP_TRUST_MAX,
    )

    raw = bundle.total_items * CAT_PACT_DUP_TRUST_PER_ITEM
    return min(CAT_PACT_DUP_TRUST_MAX, max(0, raw))


def trade_duplicates_between_wolves(
    sender,
    recipient,
    *,
    guild_id: int,
    day: int,
    require_pack_trade: bool = False,
) -> tuple[bool, str]:
    """Move all duplicate hoard items to another wolf. Unlimited (you need
    duplicates on hand each time); only the first cross-pack trade of the sunrise
    lifts pack standing, so repeats can't farm relation."""
    if sender["id"] == recipient["id"]:
        return False, "can't trade duplicates to yourself."

    if require_pack_trade:
        from config import PACK_DUP_TRADE_MIN_RELATION, PACK_DUP_TRADE_RELATION_GAIN

        if not sender["pack_id"] or not recipient["pack_id"]:
            return False, "both wolves must belong to a great pack den."
        if sender["pack_id"] == recipient["pack_id"]:
            return False, "use `/trade duplicates` for packmates; pick a wolf from another den."
        standing = db.get_pack_relation(guild_id, sender["pack_id"], recipient["pack_id"])
        if standing < PACK_DUP_TRADE_MIN_RELATION:
            return False, (
                f"pack standing **{standing}/10** is too low; need at least "
                f"**{PACK_DUP_TRADE_MIN_RELATION}** (`/pack relation`)."
            )

    bundle = collect_duplicates(sender["id"])
    if bundle.is_empty():
        return False, f"no duplicates to trade.\n\n_{format_duplicate_summary(bundle)}_"

    ok, detail = transfer_duplicates(sender["id"], recipient["id"], bundle)
    if not ok:
        return False, detail

    from engine.energy import spend_energy

    already_traded_today = int(sender["last_duplicate_trade_day"]) >= day if "last_duplicate_trade_day" in sender.keys() else False
    db.update_user(sender["discord_id"], last_duplicate_trade_day=day, wolf_id=sender["id"])
    _new_energy, _had_energy, trade_penalty = spend_energy(sender, "duptrade")

    footer = ""
    if require_pack_trade and sender["pack_id"] and recipient["pack_id"]:
        if not already_traded_today:
            new_standing = db.adjust_pack_relation(
                guild_id, sender["pack_id"], recipient["pack_id"], PACK_DUP_TRADE_RELATION_GAIN
            )
            footer = f"\n\npack standing **+{PACK_DUP_TRADE_RELATION_GAIN}** (now **{new_standing}/10**)."
        else:
            footer = "\n\n_already traded across the border this sunrise; no extra pack standing from a repeat._"
    if trade_penalty:
        footer += f"\n\n_{trade_penalty}_"

    return True, (
        f"duplicates passed to **{recipient['wolf_name']}** "
        f"({bundle.total_items} item(s)).\n\n{detail}{footer}"
    )
