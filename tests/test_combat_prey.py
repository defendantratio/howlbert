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
    # large_prey kills are already granted a carcass via the dedicated
    # hunt_combat victory path (is_hunt_prey_encounter short-circuits
    # try_grant_combat_kill_carcass before this lookup ever runs for it);
    # the lookup itself now falls back to "carrion" for any unmapped
    # template so no combat kill is ever silently carcass-less.
    assert prey_key_for_npc_template("large_prey") == "carrion"
    assert prey_key_for_npc_template("totally_unmapped_future_npc") == "carrion"


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
