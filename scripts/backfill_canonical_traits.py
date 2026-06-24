"""Backfill canonical lore, traits, and register defaults for named character wolves.

Usage:
  python scripts/backfill_canonical_traits.py              # fill missing only
  python scripts/backfill_canonical_traits.py --dry-run    # preview
  python scripts/backfill_canonical_traits.py --force      # overwrite lore + traits
  python scripts/backfill_canonical_traits.py --force-defaults  # overwrite role/belief/size too
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database as db
from engine.character_lore_data import CHARACTER_LORE_BY_NAME


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing to the database.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing character_lore and character_traits.",
    )
    parser.add_argument(
        "--force-defaults",
        action="store_true",
        help="Overwrite wolf_role, maw_belief, and size_class even when already set.",
    )
    args = parser.parse_args()

    db.init_db()
    canonical = {name.lower() for name in CHARACTER_LORE_BY_NAME}
    touched = 0
    skipped = 0

    with db.get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM users ORDER BY wolf_name COLLATE NOCASE"
        ).fetchall()

    print(f"Scanning {len(rows)} wolf(s); {len(canonical)} canonical names on file.")

    for row in rows:
        name = (row["wolf_name"] or "").strip()
        if name.lower() not in canonical:
            continue

        changes = db.backfill_canonical_character_sheet(
            row,
            force_lore=args.force,
            force_traits=args.force,
            force_defaults=args.force_defaults,
            dry_run=args.dry_run,
        )

        if changes:
            touched += 1
            tag = "would update" if args.dry_run else "updated"
            print(f"  {tag}: {name} (id={row['id']}) - {', '.join(changes)}")
        else:
            skipped += 1

    mode = "Dry run" if args.dry_run else "Done"
    print(f"{mode}. Canonical wolves touched: {touched}; already complete: {skipped}.")


if __name__ == "__main__":
    main()
