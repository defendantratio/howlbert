"""Restore lowercase mistaken constant references (FOO_BAR defined but foo_bar used)."""
from __future__ import annotations

import re
import tokenize
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = [ROOT / "engine", ROOT / "cogs", ROOT / "utils", ROOT / "database.py", ROOT / "config.py"]

ASSIGN_RE = re.compile(r"^([A-Z][A-Z0-9_]*)\s*=")


def module_constants(text: str) -> set[str]:
    consts: set[str] = set()
    for line in text.splitlines():
        m = ASSIGN_RE.match(line.strip())
        if m:
            consts.add(m.group(1))
    return consts


def fix_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    consts = module_constants(original)
    if not consts:
        return False
    lower_map = {c.lower(): c for c in consts}
    try:
        tokens = list(tokenize.tokenize(BytesIO(original.encode("utf-8")).readline))
    except tokenize.TokenError:
        return False

    pieces: list[str] = []
    last_end = (1, 0)
    changed = False

    for tok in tokens:
        if tok.type == tokenize.ENDMARKER:
            break
        if tok.type in (tokenize.NL, tokenize.NEWLINE, tokenize.ENCODING):
            continue
        if tok.type == tokenize.ERRORTOKEN:
            continue

        (srow, scol) = tok.start
        (erow, ecol) = tok.end
        if (srow, scol) > last_end:
            gap_start = _offset(original, last_end)
            gap_end = _offset(original, (srow, scol))
            pieces.append(original[gap_start:gap_end])

        if tok.type == tokenize.NAME and tok.string in lower_map and tok.string != lower_map[tok.string]:
            pieces.append(lower_map[tok.string])
            changed = True
        else:
            pieces.append(tok.string)
        last_end = (erow, ecol)

    if last_end < (len(original.splitlines()), 0):
        pieces.append(original[_offset(original, last_end) :])

    if not changed:
        return False
    path.write_text("".join(pieces), encoding="utf-8")
    return True


def _offset(text: str, pos: tuple[int, int]) -> int:
    row, col = pos
    lines = text.splitlines(keepends=True)
    if row < 1 or row > len(lines):
        return len(text)
    return sum(len(lines[i]) for i in range(row - 1)) + col


def main() -> None:
    fixed: list[str] = []
    for base in SCAN:
        paths = [base] if base.is_file() else sorted(base.rglob("*.py"))
        for path in paths:
            if fix_file(path):
                fixed.append(str(path.relative_to(ROOT)))
    print(f"fixed {len(fixed)} files")
    for f in fixed:
        print(" ", f)


if __name__ == "__main__":
    main()
