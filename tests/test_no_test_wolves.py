"""Guard: the live database must not carry leftover test wolves.

Unit-test runs and manual bot testing can register wolves with fake Discord IDs
(small fixture ints, or the 9990-9993 synthetic snowflakes). Those are excluded
from leaderboards at read time, but they should never persist in the live roster.
This test fails the full suite if any remain, so cleanup can't be forgotten.

Unlike the rest of the suite (which runs against an isolated temp DB per the
autouse fixture in conftest), this test reads the *live* fable.db directly and
read-only, and skips cleanly when that file isn't present (fresh clone / CI).
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from engine.test_accounts import is_test_discord_id, is_test_wolf_name

# resolved independently of config.DB_PATH / HOWLBERT_DB_PATH, both of which the
# conftest fixture repoints at a temp file. override with HOWLBERT_LIVE_DB_PATH.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_LIVE_DB = Path(os.getenv("HOWLBERT_LIVE_DB_PATH", _REPO_ROOT / "fable.db"))


def _live_wolves() -> list[tuple[int, str]]:
    conn = sqlite3.connect(f"file:{_LIVE_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT discord_id, wolf_name FROM users").fetchall()
    finally:
        conn.close()
    return [(int(r["discord_id"]), r["wolf_name"]) for r in rows]


def test_no_test_wolves_in_live_db() -> None:
    if not _LIVE_DB.exists():
        pytest.skip(f"no live database at {_LIVE_DB}; nothing to guard")

    offenders = [
        f"{name!r} (id {did})"
        for did, name in _live_wolves()
        if is_test_discord_id(did) or is_test_wolf_name(name)
    ]

    assert not offenders, (
        f"{len(offenders)} test wolf/wolves left in the live roster: "
        + ", ".join(offenders)
        + ". remove them from the live db before committing."
    )
