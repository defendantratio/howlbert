"""Backfill wolf journals from stored lore, lineage, bonds, and gameplay.

Usage:
  python scripts/backfill_wolf_journals.py
  python scripts/backfill_wolf_journals.py --wolf Mirewort
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database as db
from engine.journal_backfill import backfill_all_wolf_journals, backfill_wolf_journal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wolf", help="Only backfill one wolf by name")
    args = parser.parse_args()

    db.init_db()

    if args.wolf:
        row = db.get_wolf_by_name(args.wolf)
        if not row:
            print(f"No wolf named {args.wolf!r}")
            sys.exit(1)
        added = backfill_wolf_journal(row["id"])
        print(f"{row['wolf_name']}: added {added} journal entries")
        return

    total = backfill_all_wolf_journals()
    print(f"Done. Added {total} journal entries across all wolves.")


if __name__ == "__main__":
    main()
