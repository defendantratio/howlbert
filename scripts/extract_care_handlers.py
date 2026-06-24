"""One-off: extract care handlers from rpg.py into care_handlers.py."""
from pathlib import Path
import re

rpg_lines = Path("cogs/rpg.py").read_text(encoding="utf-8").splitlines()


def extract_method(start_line: int, end_line: int) -> str:
    chunk = rpg_lines[start_line - 1 : end_line - 1]
    out: list[str] = []
    for line in chunk:
        if line.startswith("    async def _"):
            line = re.sub(r"    async def (_\w+)\(self,", r"async def \1(", line)
            line = line.replace("async def _", "async def ")
        elif line.startswith("        "):
            line = line[4:]
        out.append(line)
    return "\n".join(out)


header = '''"""Shared care command handlers (herbs, medic treatment, rites)."""

from __future__ import annotations

import json
import random

import discord

import database as db
from engine.role_privileges import treat_limit_reached
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed


'''

ranges = {
    "herbbag": (690, 726),
    "prepare_herb": (727, 744),
    "dryall": (745, 761),
    "prepare_herb_inventory": (762, 782),
    "treat": (783, 1147),
    "herb_guide": (1148, 1159),
    "denstore": (1160, 1262),
    "turnin_restricted": (1263, 1294),
    "sacred_visit": (548, 562),
    "spirit_ritual": (1295, 1325),
    "naming_ceremony": (1326, 1348),
    "lay_to_rest": (1349, 1375),
}

parts = [header]
for _name, (s, e) in ranges.items():
    parts.append(extract_method(s, e))
    parts.append("\n\n")

body = "".join(parts)
replacements = [
    ("/vitals action:dryall", "/herbs action:dryall"),
    ("/vitals action:prepare", "/herbs action:prepare"),
    ("/vitals action:herbbag", "/herbs action:bag"),
    ("/vitals action:herbs", "/herbs action:guide"),
    ("/vitals action:denstore", "/herbs action:store"),
    ("/vitals action:turnin", "/herbs action:turnin"),
    ("Herb guide · /vitals action:herbs", "Herb guide · /herbs action:guide"),
]
for old, new in replacements:
    body = body.replace(old, new)

Path("cogs/care_handlers.py").write_text(body, encoding="utf-8")
print(f"Wrote cogs/care_handlers.py ({len(body)} chars)")
