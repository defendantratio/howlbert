"""Wrap remaining dynamic Choice name= with choice_label()."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = list((ROOT / "cogs").rglob("*.py")) + [ROOT / "utils" / "herb_autocomplete.py"]

IMPORT_RE = re.compile(r"(from utils\.embeds import [^\n]+)")
FSTRING_SLICE = re.compile(
    r"app_commands\.Choice\(name=(f(?:\"[^\"]*\"|'[^']*'))\[:100\],"
)
FSTRING_PLAIN = re.compile(
    r"app_commands\.Choice\(name=(f(?:\"[^\"]*\"|'[^']*')),"
)
NAME_VAR = re.compile(
    r"app_commands\.Choice\(name=([a-zA-Z_][\w]*)(?!\[),"
)


def ensure_import(text: str) -> str:
    if "choice_label" in text:
        return text
    m = IMPORT_RE.search(text)
    if m:
        line = m.group(1)
        if "choice_label" not in line:
            return text.replace(line, line.rstrip() + ", choice_label", 1)
    return text


def fix_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = original
    text = FSTRING_SLICE.sub(r"app_commands.Choice(name=choice_label(\1),", text)
    # only wrap f-strings not already wrapped
    text = re.sub(
        r"app_commands\.Choice\(name=choice_label\(",
        "app_commands.Choice(name=choice_label(",
        text,
    )
    for m in list(FSTRING_PLAIN.finditer(text)):
        frag = m.group(0)
        if "choice_label(" in frag:
            continue
        text = text.replace(frag, frag.replace("name=" + m.group(1), f"name=choice_label({m.group(1)})", 1), 1)
    text = ensure_import(text)
    if text == original:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    changed = [str(p.relative_to(ROOT)) for p in FILES if fix_file(p)]
    print(f"updated {len(changed)} files")


if __name__ == "__main__":
    main()
