"""Import-smoke test: every shipping module must import without error.

Complements test_static_analysis.py. Static analysis parses the AST and runs
pyflakes, but a file can be perfectly valid Python and still blow up the moment
it is imported: a helper that references a name that was moved or deleted from
another module (this exact bug once broke 12 tests at once when
pain_exhaustion_check_adjustments went missing from engine.exhaustion_effects),
a mangled f-string, a module-level call that now raises, etc. Text-only edits
like a hyphen sweep are especially prone to this. Actually importing every
module catches it before it reaches production.

cogs/ and main.py are intentionally excluded here; they need discord and are
covered by test_bot_startup.py (which loads them the way the bot does). tools/
is excluded because those are dev scripts that execute on import.
"""

from __future__ import annotations

import importlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# packages whose every module must import cleanly
SCAN_DIRS = ("engine", "utils")
# top-level modules that ship with the bot
ROOT_MODULES = ("config", "rpg_rules", "herbs", "herbs_compendium", "database")


def _all_module_names() -> list[str]:
    mods: list[str] = []
    for dirname in SCAN_DIRS:
        d = ROOT / dirname
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*.py")):
            if f.name == "__init__.py":
                continue
            rel = f.relative_to(ROOT).with_suffix("")
            mods.append(".".join(rel.parts))
    mods.extend(ROOT_MODULES)
    return mods


def test_all_modules_import() -> None:
    mods = _all_module_names()
    assert len(mods) > 100, f"expected to scan many modules, found only {len(mods)}"

    failures: list[str] = []
    for name in mods:
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - we want every failure, not just one
            failures.append(f"{name}: {type(exc).__name__}: {exc}")

    assert not failures, "modules failed to import:\n" + "\n".join(failures)


def main() -> None:
    try:
        test_all_modules_import()
        print(f"  OK  all {len(_all_module_names())} modules import")
        print("\n1 passed, 0 failed")
    except AssertionError as exc:
        print(f" FAIL import smoke\n{exc}")
        print("\n0 passed, 1 failed")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
