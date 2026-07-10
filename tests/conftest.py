"""Pytest hooks; isolated DB per test function."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_test_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point Howlbert at a fresh SQLite file for each test."""
    db_file = tmp_path / "howlbert_test.db"
    monkeypatch.setenv("HOWLBERT_DB_PATH", str(db_file))

    import config

    monkeypatch.setattr(config, "DB_PATH", db_file)

    import database as db

    monkeypatch.setattr(db, "DB_PATH", db_file)
    db.init_db()
    yield
