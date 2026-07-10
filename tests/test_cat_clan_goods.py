"""Clan goods receive/barter tests."""

from __future__ import annotations

import database as db
from engine.cat_clan_goods import (
    barter_loot_count,
    grant_clan_loot,
    receive_loot_count,
    roll_clan_loot,
)


def test_loot_counts():
    assert receive_loot_count(40, "truce") == 1
    assert receive_loot_count(75, "hunting_rights") >= 3
    assert barter_loot_count(6) == 3
    assert barter_loot_count(1) == 1


def test_roll_and_grant():
    db.init_db()
    db.register_user(88110, "ClanRecv", affiliation="greyspire")
    user = db.get_user(88110)
    assert user
    entries = roll_clan_loot("RiverClan", pact_type="hunting_rights", count=2)
    assert len(entries) == 2
    lines = grant_clan_loot(user, guild_id=88111, day=100, entries=entries)
    assert lines


if __name__ == "__main__":
    test_loot_counts()
    test_roll_and_grant()
    print("test_cat_clan_goods: ok")
