"""Biome fishing catches; run: python -m tests.test_fishing"""

from engine.fishing import FISHING_CATCHES, pick_fishing_catch, is_fishing_prey
from engine.prey_items import prey_key_from_label, prey_meta


def test_fishing_always_fish_category() -> None:
    for pack in ("silverrush", "mistmoor", "thistlehide", "greyspire", None):
        for _ in range(40):
            catch = pick_fishing_catch(
                great_pack=pack,
                time_of_day="day",
                weather="clear",
            )
            assert catch["prey_key"] in FISHING_CATCHES
            assert catch["kind"] in ("fish", "turtle", "amphibian")
            assert catch["prey_key"] != "frog"


def test_turtles_in_catalog() -> None:
    for key in (
        "common_snapping_turtle",
        "painted_turtle",
        "bog_turtle",
        "alligator_snapping_turtle",
    ):
        assert key in FISHING_CATCHES
        assert FISHING_CATCHES[key]["kind"] == "turtle"


def test_silverrush_has_varied_fish() -> None:
    seen = {
        pick_fishing_catch(great_pack="silverrush", time_of_day="day", weather="clear")[
            "prey_key"
        ]
        for _ in range(120)
    }
    assert "bluegill" in seen or "perch" in seen
    assert len(seen) >= 4


def test_rain_unlocks_bullfrog_not_replacing_fish() -> None:
    hits = sum(
        1
        for _ in range(200)
        if pick_fishing_catch(
            great_pack="thistlehide",
            time_of_day="day",
            weather="rain",
        )["prey_key"]
        == "bullfrog"
    )
    fish_hits = sum(
        1
        for _ in range(200)
        if pick_fishing_catch(
            great_pack="thistlehide",
            time_of_day="day",
            weather="rain",
        )["kind"]
        == "fish"
    )
    assert fish_hits > hits


def test_prey_meta_fishing_catch() -> None:
    meta = prey_meta("walleye")
    assert meta["name"] == "Walleye"
    assert prey_key_from_label("a walleye") == "walleye"
    assert is_fishing_prey("shovelnose_sturgeon")


if __name__ == "__main__":
    test_fishing_always_fish_category()
    test_turtles_in_catalog()
    test_silverrush_has_varied_fish()
    test_rain_unlocks_bullfrog_not_replacing_fish()
    test_prey_meta_fishing_catch()
    print("OK")
