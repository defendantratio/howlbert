"""
Static-analysis regression test; run: python -m tests.test_static_analysis

Catches the exact bug class that broke /profile, /family, /medic action:ritual
and action:lay_to_rest, /pack audit, and every proxy webhook message all at
once: a constant or helper defined under one name (e.g. MAW_BELIEF_LABELS)
and referenced under another (maw_belief_labels). pyflakes' static checker
catches this without ever running the code, so it belongs in the suite
itself rather than waiting for someone to hit the crash in production.

Also fails on: redefining a name before its first use (almost always a
leftover/duplicate import), and a dict literal with the same key twice
(the second value silently wins, dropping the first).
"""

from __future__ import annotations

import ast
from pathlib import Path

from pyflakes.checker import Checker
from pyflakes.messages import (
    DuplicateArgument,
    MultiValueRepeatedKeyLiteral,
    RedefinedWhileUnused,
    UndefinedExport,
    UndefinedLocal,
    UndefinedName,
)

ROOT = Path(__file__).resolve().parents[1]

# Directories to scan; mirrors what ships with the bot (no venv/vcs/cache noise).
SCAN_DIRS = ("cogs", "engine", "scripts", "tests", "tools", "utils")
SCAN_ROOT_FILES = ("main.py", "database.py", "config.py", "rpg_rules.py", "herbs.py", "herbs_compendium.py")

# Message classes worth failing the build over; each one is either a
# guaranteed crash (UndefinedName/UndefinedLocal/UndefinedExport,
# DuplicateArgument) or silently-wrong behavior (RedefinedWhileUnused,
# MultiValueRepeatedKeyLiteral). Deliberately excludes lower-signal/cosmetic
# pyflakes categories (unused imports, f-strings without placeholders, etc.)
# so this test doesn't become noisy enough to ignore.
FATAL_MESSAGE_TYPES = (
    UndefinedName,
    UndefinedLocal,
    UndefinedExport,
    DuplicateArgument,
    RedefinedWhileUnused,
    MultiValueRepeatedKeyLiteral,
)

_pass = 0
_fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _pass, _fail
    if cond:
        _pass += 1
        print(f"  OK  {name}")
    else:
        _fail += 1
        print(f" FAIL {name}" + (f" - {detail}" if detail else ""))


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for dirname in SCAN_DIRS:
        d = ROOT / dirname
        if not d.is_dir():
            continue
        files.extend(sorted(d.rglob("*.py")))
    for name in SCAN_ROOT_FILES:
        f = ROOT / name
        if f.is_file():
            files.append(f)
    return files


def _fatal_messages_for(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"SyntaxError: {exc}"]
    checker = Checker(tree, filename=str(path))
    return [
        str(msg)
        for msg in checker.messages
        if isinstance(msg, FATAL_MESSAGE_TYPES)
    ]


def main() -> None:
    files = _iter_python_files()
    check("found python files to scan", len(files) > 50, f"only found {len(files)}")

    all_problems: list[str] = []
    for path in files:
        problems = _fatal_messages_for(path)
        all_problems.extend(problems)

    if all_problems:
        detail = "\n".join(all_problems)
        check(
            f"no undefined-name / redefinition / duplicate-key issues across {len(files)} files",
            False,
            f"{len(all_problems)} issue(s):\n{detail}",
        )
    else:
        check(f"no undefined-name / redefinition / duplicate-key issues across {len(files)} files", True)

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
