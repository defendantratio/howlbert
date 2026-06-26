"""Season hunt/forage modifiers; run: python -m tests.test_season_effects"""

from config import SEASON_FORAGE_DC_MOD, SEASON_HUNT_MODIFIERS
from engine.season_effects import apply_season_hunt, season_forage_dc_mod


def test_hunt_modifiers_configured() -> None:
    assert SEASON_HUNT_MODIFIERS["winter"] < 0
    assert SEASON_HUNT_MODIFIERS["summer"] > 0
    assert apply_season_hunt(100, "winter") == 80
    assert apply_season_hunt(100, "summer") == 110
    assert apply_season_hunt(0, "winter") == 0


def test_forage_dc_winter_harder() -> None:
    assert season_forage_dc_mod("winter") > season_forage_dc_mod("spring")
    assert SEASON_FORAGE_DC_MOD["winter"] >= 5


def test_track_dc_by_season() -> None:
    from engine.season_effects import season_track_dc_mod

    assert season_track_dc_mod("summer") == -2
    assert season_track_dc_mod("autumn") == -1
    assert season_track_dc_mod("winter") == 2
    assert season_track_dc_mod("spring") == 0


if __name__ == "__main__":
    test_hunt_modifiers_configured()
    test_forage_dc_winter_harder()
    test_track_dc_by_season()
    print("OK")
