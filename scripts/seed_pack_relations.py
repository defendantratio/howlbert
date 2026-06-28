"""Seed lore-accurate opening pack_relations standings for a guild.

Only touches pack pairs still sitting at the untouched default (5/10); never
overwrites diplomacy that's already been played out in-game.

Usage:
  python scripts/seed_pack_relations.py --guild 1501605895837057174
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database as db
from engine.pack_relations import seed_lore_pack_relations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guild", type=int, required=True, help="discord guild id")
    args = parser.parse_args()

    db.init_db()

    changes = seed_lore_pack_relations(args.guild)
    if not changes:
        print("No changes; all pairs already customized away from the default.")
        return
    for line in changes:
        print(line)
    print(f"Done. Seeded {len(changes)} pack relation(s).")


if __name__ == "__main__":
    main()
