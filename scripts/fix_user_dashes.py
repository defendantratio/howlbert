"""Replace em/en dashes and clause-separator ' - ' in user-facing string literals."""
from __future__ import annotations

import re
import sys
import tokenize
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TARGET_DIRS = [ROOT / "engine", ROOT / "cogs"]
TARGET_FILES = [ROOT / "herbs.py", ROOT / "database.py", ROOT / "docs" / "BASIL_RULES.md"]

STRING_TYPES = {
    tokenize.STRING,
    getattr(tokenize, "FSTRING_START", None),
    getattr(tokenize, "FSTRING_MIDDLE", None),
    getattr(tokenize, "FSTRING_END", None),
}
STRING_TYPES.discard(None)

SKIP_STRING_RE = re.compile(
    r"(?:UPDATE\s+\w+\s+SET|MAX\(0,\s*\w+\s*-|bones\s*-\s*\?|treasury\s*-\s*\?|"
    r"quantity\s*-\s*\?|xp\s*-\s*\?|remnants\s*-\s*\?|mood\s*-\s*\?|"
    r"hunger\s*-\s*\?|thirst\s*-\s*\?)",
    re.IGNORECASE,
)

COLON_SUFFIX_RE = re.compile(
    r"(?:"
    r"Explore|Herb Guide|Role Quests|Wolves|Relation|Hunter|Found family|First kill|"
    r"Peak nursing|Canid bite|Rabid bite|Killer's Instinct|"
    r"Sunrise \d+|Tier \d+|Next: Tier \d+|Round \d+|"
    r"vs DC \d+|Medicine check: .+ vs DC \d+"
    r")$"
)

COLON_LABEL_RE = re.compile(
    r"^(?:Pup|Juvenile|Young adult|Adult|Elder|Swept downstream|Fall)$"
)

BOLD_TAIL_RE = re.compile(r"\*\*[^*]+\*\*(\s*\([^)]+\))?$")


def _choose_separator(before: str, after: str) -> str:
    b = before.rstrip()
    a = after.lstrip()

    if COLON_SUFFIX_RE.search(b):
        return ": "
    if COLON_LABEL_RE.match(b.split("\n")[-1].strip()):
        return ": "
    if BOLD_TAIL_RE.search(b):
        return ": "
    if re.search(r"\)\s*$", b) and re.search(r"\(rolled \d+\)", b):
        return ": "
    if re.search(r"\*\*[^*]+\*\*\s*\(`[^`]+`\)\s*$", b):
        return ": "
    if re.search(r"\([^)]+\)\s*$", b) and re.search(r"title|difficulty|key", b, re.I):
        return ": "
    if re.search(r"\d+\.\s+[^.]+$", b):
        return ": "

    tail = b.split(".")[-1].strip() if "." in b else b.strip()
    if len(tail) <= 55:
        if re.match(r"^[\−+\d/]", a) or re.match(r"^\d", a):
            return ": "
        if re.match(r"^[A-Z]", tail) and len(tail.split()) <= 7:
            return ": "

    return "; "


def _replace_spaced_dash(text: str) -> str:
    parts = text.split(" - ")
    if len(parts) == 1:
        return text
    out = parts[0]
    for part in parts[1:]:
        out += _choose_separator(out, part) + part
    return out


def _replace_in_literal(raw: str) -> tuple[str, int]:
    """Transform a quoted/f-string token; return (new_raw, change_count)."""
    prefix = ""
    body = raw
    suffix = ""

    if raw.startswith(("f", "F", "r", "R", "b", "B", "u", "U")):
        for i, ch in enumerate(raw):
            if ch in "\"'":
                prefix = raw[:i]
                body = raw[i:]
                break

    quote = body[0] if body else ""
    if quote in "\"'":
        suffix = quote * (3 if body[:3] == quote * 3 else 1)
        inner = body[len(suffix) : -len(suffix)]
    else:
        inner = body

    if SKIP_STRING_RE.search(inner):
        return raw, 0

    original = inner
    inner = inner.replace(" — ", "; ")
    inner = inner.replace(" – ", "; ")
    inner = _replace_spaced_dash(inner)

    if inner == original:
        return raw, 0
    changes = sum(1 for a, b in zip(original, inner) if a != b)
    if len(original) != len(inner):
        changes = max(changes, abs(len(original) - len(inner)))
    return prefix + suffix + inner + suffix, changes


def _pos_to_offset(text: str, pos: tuple[int, int]) -> int:
    """Match tokenize line/col on CRLF or LF files (lines split on \\n only)."""
    line_no, col = pos
    lines = text.split("\n")
    if line_no < 1 or line_no > len(lines):
        return len(text)
    return sum(len(lines[i]) + 1 for i in range(line_no - 1)) + col


def _process_python(path: Path) -> int:
    source_bytes = path.read_bytes()
    source_text = source_bytes.decode("utf-8")
    tokens = list(tokenize.tokenize(BytesIO(source_bytes).readline))
    if not tokens:
        return 0

    edits: list[tuple[int, int, str, int]] = []
    for tok in tokens:
        if tok.type not in STRING_TYPES:
            continue
        new_raw, n = _replace_in_literal(tok.string)
        if not n:
            continue
        start = _pos_to_offset(source_text, tok.start)
        end = _pos_to_offset(source_text, tok.end)
        edits.append((start, end, new_raw, n))

    if not edits:
        return 0

    edits.sort(key=lambda e: e[0], reverse=True)
    total = 0
    result = source_text
    for start, end, new_raw, n in edits:
        result = result[:start] + new_raw + result[end:]
        total += n

    path.write_text(result, encoding="utf-8")
    return total


def _process_markdown(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    total = 0
    out: list[str] = []
    for line in lines:
        if re.match(r"^\s*>\s*-\s", line) or re.match(r"^\s*-\s", line):
            out.append(line)
            continue
        if re.search(r"\d+–\d+", line):
            out.append(line)
            continue
        original = line
        line = line.replace(" — ", "; ")
        line = line.replace(" – ", "; ")
        if " - " in line:
            line = _replace_spaced_dash(line)
        if line != original:
            total += 1
        out.append(line)
    if total:
        path.write_text("".join(out), encoding="utf-8")
    return total


def main() -> int:
    files: list[Path] = []
    for d in TARGET_DIRS:
        if d.is_dir():
            files.extend(sorted(d.rglob("*.py")))
    for f in TARGET_FILES:
        if f.is_file():
            files.append(f)

    grand = 0
    changed: list[tuple[str, int]] = []
    for path in files:
        if ".venv" in path.parts:
            continue
        if path.suffix == ".py":
            n = _process_python(path)
        elif path.suffix == ".md":
            n = _process_markdown(path)
        else:
            continue
        if n:
            changed.append((str(path.relative_to(ROOT)), n))
            grand += n

    print(f"Changed {len(changed)} files, ~{grand} token edits")
    for rel, n in changed:
        print(f"  {rel}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
