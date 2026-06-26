"""Seed gameplay bonds from canonical lore when both wolves are registered.

Usage:
  python scripts/backfill_canonical_bonds.py
  python scripts/backfill_canonical_bonds.py --refresh-notes
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database as db
from engine.canonical_bonds import backfill_all_canonical_bonds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-notes",
        action="store_true",
        help="Overwrite bond notes with canonical lore text.",
    )
    args = parser.parse_args()

    db.init_db()
    added = backfill_all_canonical_bonds(refresh_notes=args.refresh_notes)
    print(f"Done. {added} new canonical bond(s) inserted; existing pairs upgraded in place.")


if __name__ == "__main__":
    main()
