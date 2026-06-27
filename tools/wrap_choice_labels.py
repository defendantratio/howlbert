"""Wrap dynamic app_commands.Choice name= with choice_label()."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "cogs" / "life.py",
    ROOT / "cogs" / "pack.py",
    ROOT / "cogs" / "wolfadmin.py",
    ROOT / "cogs" / "profile.py",
    ROOT / "cogs" / "wolvden.py",
    ROOT / "cogs" / "skills.py",
    ROOT / "cogs" / "pact.py",
    ROOT / "cogs" / "hunting.py",
    ROOT / "cogs" / "explore.py",
    ROOT / "cogs" / "economy.py",
    ROOT / "cogs" / "combat.py",
    ROOT / "cogs" / "bonds.py",
    ROOT / "utils" / "herb_autocomplete.py",
]

IMPORT_LINE = "from utils.embeds import choice_label\n"
IMPORT_RE = re.compile(r"from utils\.embeds import ([^\n]+)")

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"app_commands\.Choice\(name=name\[:100\],"),
        "app_commands.Choice(name=choice_label(name),",
    ),
    (
        re.compile(r"app_commands\.Choice\(name=label\[:100\],"),
        "app_commands.Choice(name=choice_label(label),",
    ),
    (
        re.compile(r"app_commands\.Choice\(name=([a-zA-Z_][\w]*)\[:100\],"),
        r"app_commands.Choice(name=choice_label(\1),",
    ),
]


def ensure_import(text: str) -> str:
    if "choice_label" in text:
        return text
    m = IMPORT_RE.search(text)
    if m:
        names = [n.strip() for n in m.group(1).split(",")]
        if "choice_label" not in names:
            names.append("choice_label")
            return text[: m.start()] + f"from utils.embeds import {', '.join(names)}" + text[m.end() :]
    # after first import block
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("from utils.embeds import "):
            lines[i] = line.rstrip("\n") + ", choice_label\n"
            return "".join(lines)
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            continue
        lines.insert(i, IMPORT_LINE)
        return "".join(lines)
    return IMPORT_LINE + text


def fix_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = original
    for pattern, repl in PATTERNS:
        text = pattern.sub(repl, text)
    if text == original:
        return False
    text = ensure_import(text)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    changed = [str(p.relative_to(ROOT)) for p in FILES if p.exists() and fix_file(p)]
    print(f"updated {len(changed)} files")
    for c in changed:
        print(" ", c)


if __name__ == "__main__":
    main()
