"""Combat kill prey mapping; run: python -m tests.test_combat_prey"""

from engine.combat_prey import prey_key_for_npc_template
from engine.cannibalism import cannibalism_public_exposure
from engine.prey_items import is_cannibal_prey


def test_npc_prey_map() -> None:
    assert prey_key_for_npc_template("coyote") == "coyote"
    assert prey_key_for_npc_template("clan_warrior") == "cat_carcass"
    assert prey_key_for_npc_template("kittypet") == "kittypet_carcass"
    assert prey_key_for_npc_template("water_snake") == "snake"
    assert prey_key_for_npc_template("garter_snake") == "snake"
    assert prey_key_for_npc_template("skink") == "lizard"
    assert prey_key_for_npc_template("large_prey") is None


def test_cannibal_flag() -> None:
    assert is_cannibal_prey("wolf_carcass")
    assert not is_cannibal_prey("hare")


def test_public_exposure_only_wolf() -> None:
    user = {"pack_id": 1, "discord_id": 1, "id": 1}
    assert cannibalism_public_exposure(user, "hare", action="stash") == ""
    assert cannibalism_public_exposure(user, "hare", action="preypile") == ""
    wolf_msg = cannibalism_public_exposure(user, "wolf_carcass", action="preypile")
    assert "caught" in wolf_msg.lower()
    assert "fresh-kill cache" in wolf_msg.lower() or "laid" in wolf_msg.lower()


if __name__ == "__main__":
    test_npc_prey_map()
    test_cannibal_flag()
    test_public_exposure_only_wolf()
    print("OK")
