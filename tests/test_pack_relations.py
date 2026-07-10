"""Pack relation tags, gates, and war flash UX."""

from __future__ import annotations

from unittest.mock import patch

from engine.pack_relations import (
    can_aid_rival,
    can_join_friendly_pack_hunt,
    can_share_territory,
    format_standing_war_flash,
    is_friendly_relation,
    is_hostile_relation,
    is_war_relation,
    relation_tag,
)


def test_relation_tags():
    assert relation_tag(0) == "war"
    assert relation_tag(3) == "hostile"
    assert relation_tag(4) == "neutral"
    assert relation_tag(8) == "friendly"
    assert is_war_relation(0)
    assert is_hostile_relation(3)
    assert not is_hostile_relation(4)
    assert is_friendly_relation(8)


def test_can_share_blocks_war_and_hostile():
    ok, _ = can_share_territory(1, 1, 2)
    with patch("engine.pack_relations.pack_relation", return_value=0):
        ok, msg = can_share_territory(1, 1, 2)
        assert not ok and "war" in msg.lower()
    with patch("engine.pack_relations.pack_relation", return_value=2):
        ok, msg = can_share_territory(1, 1, 2)
        assert not ok and "hostile" in msg.lower()


def test_can_aid_blocks_war_and_hostile():
    with patch("engine.pack_relations.pack_relation", return_value=0):
        ok, msg = can_aid_rival(1, 1, 2)
        assert not ok and "war" in msg.lower()
    with patch("engine.pack_relations.pack_relation", return_value=2):
        ok, msg = can_aid_rival(1, 1, 2)
        assert not ok and "hostile" in msg.lower()
    with patch("engine.pack_relations.pack_relation", return_value=5):
        ok, _ = can_aid_rival(1, 1, 2)
        assert ok


def test_friendly_pack_hunt_gate():
    user = {"pack_id": 2}
    hunt = {"pack_id": 1, "guild_id": 99}
    with patch("engine.pack_relations.pack_relation", return_value=7):
        ok, note = can_join_friendly_pack_hunt(user, hunt, guild_id=99)
        assert not ok and note is None
    with patch("engine.pack_relations.pack_relation", return_value=8):
        with patch("engine.pack_relations.db.get_pack", return_value={"name": "Greyspire"}):
            ok, note = can_join_friendly_pack_hunt(user, hunt, guild_id=99)
            assert ok and note and "8/10" in note


def test_war_flash_when_war_exists():
    fake_war = {"territory_name": "Pine Ridge", "attacker_pack_id": 1, "defender_pack_id": 2}
    with patch("engine.pack_relations.db.get_active_war_between_packs", return_value=fake_war):
        msg = format_standing_war_flash(1, 1, 2, 0)
        assert "territory war declared" in msg.lower()
        assert "Pine Ridge" in msg


def test_war_flash_when_already_fighting_elsewhere():
    with patch("engine.pack_relations.db.get_active_war_between_packs", return_value=None):
        with patch("engine.pack_relations.db.get_active_war_for_pack", return_value={"id": 1}):
            msg = format_standing_war_flash(1, 1, 2, 0)
            assert "already tied up" in msg


def test_war_flash_neutral_standing():
    assert format_standing_war_flash(1, 1, 2, 5) == ""


if __name__ == "__main__":
    test_relation_tags()
    test_can_share_blocks_war_and_hostile()
    test_can_aid_blocks_war_and_hostile()
    test_friendly_pack_hunt_gate()
    test_war_flash_when_war_exists()
    test_war_flash_when_already_fighting_elsewhere()
    test_war_flash_neutral_standing()
    print("test_pack_relations: ok")
