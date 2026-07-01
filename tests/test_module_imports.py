"""
Module-import smoke test; run: python -m tests.test_module_imports

pyflakes (tests/test_static_analysis.py) only checks names *within* a single
file's scope — it never verifies that `from engine.role_privileges import
is_guard` actually resolves to a real symbol in that target module. A symbol
renamed or removed in one file while another file still imports it under the
old name is invisible to that check and only blows up at runtime (this broke
`/field action:sniff` and every auto-rollover: `engine/pack_raid_ecology.py`
imported `is_guard` from `engine/role_privileges` after a rename/revert left
it missing). The only static way to catch that is to actually import every
module and let Python's real import machinery resolve every name.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Mirrors what ships with the bot; same directories test_static_analysis.py scans.
SCAN_DIRS = ("cogs", "engine", "utils")
SCAN_ROOT_MODULES = ("main", "database", "config", "rpg_rules", "herbs", "herbs_compendium")

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


def _module_names() -> list[str]:
    names: list[str] = []
    for dirname in SCAN_DIRS:
        d = ROOT / dirname
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*.py")):
            rel = f.relative_to(ROOT).with_suffix("")
            names.append(".".join(rel.parts))
    names.extend(SCAN_ROOT_MODULES)
    return names


def main() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    names = _module_names()
    check("found modules to import", len(names) > 50, f"only found {len(names)}")

    problems: list[str] = []
    for name in names:
        if name.endswith("__init__"):
            continue
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - we want every importable module to actually import
            problems.append(f"{name}: {type(exc).__name__}: {exc}")

    if problems:
        detail = "\n".join(problems)
        check(f"all {len(names)} modules import cleanly", False, f"{len(problems)} issue(s):\n{detail}")
    else:
        check(f"all {len(names)} modules import cleanly", True)

    print(f"\n{_pass} passed, {_fail} failed")
    if _fail:
        raise SystemExit(1)


def test_main() -> None:
    """pytest entry point; this module's checks otherwise only run via `python -m`."""
    main()


if __name__ == "__main__":
    main()
