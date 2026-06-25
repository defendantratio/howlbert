"""Warrior Cats feature tests: Gathering, omens, patrol names, Twolegplace."""

from __future__ import annotations

import database as db
from engine.cat_clans import pick_border_cat_display_name
from engine.cat_clan_goods import medicine_herb_display, roll_clan_loot
from engine.cat_gathering import GATHERING_BY_SEASON, apply_gathering_on_season_change
from engine.starclan_omens import roll_rest_omen
from engine.travel_hazards import TERRITORY_HAZARDS, roll_wilderness_encounter


def test_gathering_seasons():
    assert len(GATHERING_BY_SEASON) == 4
    assert "Fourtrees" in GATHERING_BY_SEASON["spring"][1]


def test_gathering_rewards_pact_pack():
    db.init_db()
    guild_id = 99001
    pack = db.get_pack_by_name("Greyspire")
    assert pack
    day = 6000
    db.upsert_cat_pact(
        guild_id,
        pack["id"],
        "RiverClan",
        pact_type="truce",
        trust=50,
        tribute_paid=30,
        terms_note="",
        forged_day=day,
        expires_day=day + 12,
        forged_by_discord_id=1,
    )
    unity_before = int(pack["pack_unity"])
    with db.get_db() as conn:
        notes = apply_gathering_on_season_change(conn, guild_id, "summer", day + 1)
    assert any("Greenleaf" in n for n in notes)
    assert any("Greyspire" in n for n in notes)
    updated = db.get_pack(pack["id"])
    from config import PACK_UNITY_MAX

    expected = min(PACK_UNITY_MAX, unity_before + 2)
    assert int(updated["pack_unity"]) == expected


def test_border_cat_names():
    name = pick_border_cat_display_name("ThunderClan", "clan_deputy")
    assert name
    assert "ThunderClan" in name
    assert pick_border_cat_display_name("ThunderClan", "rogue_cat") is None


def test_allied_patrol_scent():
    from engine.cat_clans import sniff_cat_scent_line

    line = sniff_cat_scent_line(allied_clan="ThunderClan", allied_patrol=True)
    assert "ThunderClan" in line
    assert "Rival" not in line


def test_medicine_herb_labels():
    assert "cobweb" in medicine_herb_display("cobwebs")
    entries = roll_clan_loot("ShadowClan", pact_type="truce", count=5)
    assert len(entries) == 5


def test_starclan_omen_kinds():
    kinds = {roll_rest_omen()[0] for _ in range(200)}
    assert "neutral" in kinds


def test_twolegplace_territory():
    assert "twolegplace" in TERRITORY_HAZARDS
    kind, body = roll_wilderness_encounter()
    assert kind in ("encounter", "quiet", "find")
    assert body


if __name__ == "__main__":
    test_gathering_seasons()
    test_gathering_rewards_pact_pack()
    test_border_cat_names()
    test_allied_patrol_scent()
    test_medicine_herb_labels()
    test_starclan_omen_kinds()
    test_twolegplace_territory()
    print("test_cat_wc_features: ok")
