#!/usr/bin/env python3
"""Run the Howlbert test suite with an isolated database.

Usage:
    python run_tests.py           # pytest if installed, else per-module runner
    python run_tests.py --pytest  # force pytest
    python run_tests.py --modules # force python -m tests.test_* runner
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _use_pytest() -> bool:
    try:
        import pytest  # noqa: F401
    except ImportError:
        return False
    return True


def _isolated_env() -> tuple[dict[str, str], str]:
    fd, db_path = tempfile.mkstemp(suffix=".db", prefix="howlbert_test_")
    os.close(fd)
    env = os.environ.copy()
    env["HOWLBERT_DB_PATH"] = db_path
    return env, db_path


def _run_pytest() -> int:
    env, db_path = _isolated_env()
    try:
        return subprocess.call(
            [sys.executable, "-m", "pytest", "tests", "-q"],
            cwd=ROOT,
            env=env,
        )
    finally:
        try:
            os.remove(db_path)
        except OSError:
            pass


def _init_shared_db(db_path: str) -> None:
    """Create the schema once so modules that don't call init_db() still work."""
    import config

    config.DB_PATH = Path(db_path)
    import database as db

    db.DB_PATH = Path(db_path)
    db.init_db()


def _run_modules() -> int:
    env, db_path = _isolated_env()
    _init_shared_db(db_path)
    modules = sorted((ROOT / "tests").glob("test_*.py"))
    failed: list[str] = []
    try:
        for path in modules:
            module = f"tests.{path.stem}"
            result = subprocess.run(
                [sys.executable, "-m", module],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                if result.stdout:
                    print(result.stdout, end="")
                if result.stderr:
                    print(result.stderr, end="", file=sys.stderr)
                failed.append(module)
    finally:
        try:
            os.remove(db_path)
        except OSError:
            pass

    if failed:
        print(f"\n{len(failed)} module(s) failed:", ", ".join(failed), file=sys.stderr)
        return 1
    print(f"All {len(modules)} test modules passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Howlbert tests")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--pytest", action="store_true", help="Run with pytest")
    mode.add_argument("--modules", action="store_true", help="Run each tests.test_* module")
    args = parser.parse_args()

    if args.modules:
        return _run_modules()
    if args.pytest:
        if not _use_pytest():
            print("pytest not installed; use: pip install -r requirements-dev.txt", file=sys.stderr)
            return 1
        return _run_pytest()
    if _use_pytest():
        return _run_pytest()
    return _run_modules()


if __name__ == "__main__":
    raise SystemExit(main())
