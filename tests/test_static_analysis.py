"""
Static-analysis regression test; run: python -m tests.test_static_analysis

Catches the exact bug class that broke /profile, /family, /medic action:ritual
and action:lay_to_rest, /pack audit, and every proxy webhook message all at
once: a constant or helper defined under one name (e.g. MAW_BELIEF_LABELS)
and referenced under another (maw_belief_labels). pyflakes' static checker
catches this without ever running the code, so it belongs in the suite
itself rather than waiting for someone to hit the crash in production.

Also fails on: redefining a name before its first use (almost always a
leftover/duplicate import), a dict literal with the same key twice (the
second value silently wins, dropping the first), and any command/option
description or Choice name in cogs/ that exceeds Discord's length limits
(this took the whole bot down once: a >100-char /sign description made
the entire app_commands tree sync fail with CommandSyncFailure on startup,
not just that one command).
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


# Discord rejects the whole command tree sync (CommandSyncFailure, HTTP 400)
# if any single command/option/choice string exceeds these limits — this
# took the bot down once already (a >100-char `/sign` description). Caught
# here statically since these are literal strings, not runtime values.
DISCORD_NAME_LIMIT = 32
DISCORD_DESCRIPTION_LIMIT = 100


def _str_const(node: ast.AST) -> str | None:
    """Literal string from a Constant, or from a single-arg wrapper call
    like choice_label("..."); returns None for anything not staticly known
    (f-strings, variables, multi-arg calls)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Call) and len(node.args) == 1 and not node.keywords:
        return _str_const(node.args[0])
    return None


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _top_level_command_names_in_cog(path: Path) -> list[tuple[str, int]]:
    """Return (name, lineno) for every @app_commands.command in this cog file.

    Only matches `@app_commands.command(name='X')` — i.e., decorators where the
    receiver is exactly `app_commands`, not a group variable like `@pack.command`.
    Those are the only ones that register top-level slash commands and can collide.
    """
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    results: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call):
                continue
            func = deco.func
            if not (isinstance(func, ast.Attribute) and func.attr == "command"):
                continue
            if not (isinstance(func.value, ast.Name) and func.value.id == "app_commands"):
                continue
            for kw in deco.keywords:
                if kw.arg == "name":
                    name = _str_const(kw.value)
                    if name:
                        results.append((name, node.lineno))
    return results


def _discord_length_problems_for(path: Path, tree: ast.AST) -> list[str]:
    problems: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = _call_name(node)
        if callee == "command":
            for kw in node.keywords:
                if kw.arg not in ("name", "description"):
                    continue
                value = _str_const(kw.value)
                if value is None:
                    continue
                limit = DISCORD_NAME_LIMIT if kw.arg == "name" else DISCORD_DESCRIPTION_LIMIT
                if len(value) > limit:
                    problems.append(
                        f"{path}:{node.lineno}: command {kw.arg}= is {len(value)} chars "
                        f"(limit {limit}): {value[:60]!r}..."
                    )
        elif callee == "describe":
            for kw in node.keywords:
                value = _str_const(kw.value)
                if value is None:
                    continue
                if len(value) > DISCORD_DESCRIPTION_LIMIT:
                    problems.append(
                        f"{path}:{node.lineno}: describe({kw.arg}=...) is {len(value)} chars "
                        f"(limit {DISCORD_DESCRIPTION_LIMIT}): {value[:60]!r}..."
                    )
        elif callee == "Choice":
            for kw in node.keywords:
                if kw.arg != "name":
                    continue
                value = _str_const(kw.value)
                if value is None:
                    continue
                if len(value) > DISCORD_DESCRIPTION_LIMIT:
                    problems.append(
                        f"{path}:{node.lineno}: Choice(name=...) is {len(value)} chars "
                        f"(limit {DISCORD_DESCRIPTION_LIMIT}): {value[:60]!r}..."
                    )
    return problems


def _fatal_messages_for(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"SyntaxError: {exc}"]
    checker = Checker(tree, filename=str(path))
    problems = [
        str(msg)
        for msg in checker.messages
        if isinstance(msg, FATAL_MESSAGE_TYPES)
    ]
    if path.parent.name == "cogs" or path.name == "main.py":
        problems.extend(_discord_length_problems_for(path, tree))
    return problems


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

    # Command name collision check — catches CommandAlreadyRegistered at startup.
    cogs_dir = ROOT / "cogs"
    all_command_names: dict[str, list[str]] = {}
    for cog_path in sorted(cogs_dir.glob("*.py")):
        for cmd_name, lineno in _top_level_command_names_in_cog(cog_path):
            all_command_names.setdefault(cmd_name, []).append(f"{cog_path.name}:{lineno}")
    collisions = {n: locs for n, locs in all_command_names.items() if len(locs) > 1}
    if collisions:
        detail = "; ".join(
            f"'{n}' defined in {', '.join(locs)}" for n, locs in sorted(collisions.items())
        )
        check("no duplicate top-level @app_commands.command names across cogs", False, detail)
    else:
        check(
            f"no duplicate top-level @app_commands.command names across cogs"
            f" ({len(all_command_names)} commands checked)",
            True,
        )

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
