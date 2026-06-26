"""Grow-your-own herb mechanics: profiles, growth, tending, harvest."""

import database as db
from engine.herb_growing import (
    can_cultivate,
    cultivable_herbs,
    effective_grow_days,
    evaluate_growth,
    growing_profile,
    harvest_yield,
    season_is_suitable,
    watering_overdue_penalty,
)


def _setup():
    db.init_db()
    with db.get_db() as conn:
        conn.execute("DELETE FROM herb_gardens")
        conn.execute("DELETE FROM herb_seeds")
        conn.commit()


def test_poison_and_bark_not_cultivable():
    assert not can_cultivate("deathberries")   # poison
    assert not can_cultivate("bloodroot")      # restricted
    assert not can_cultivate("oak_bark")       # tree bark
    assert not can_cultivate("honey")          # not a plant
    assert can_cultivate("daisy")
    assert can_cultivate("yarrow")


def test_cultivable_list_excludes_restricted():
    keys = cultivable_herbs()
    assert "daisy" in keys
    assert "deathberries" not in keys
    assert "stick" not in keys


def test_off_season_slows_hardy_and_kills_tender():
    yarrow = growing_profile("yarrow")  # hardy
    assert yarrow.hardy
    assert effective_grow_days(yarrow, "spring") == yarrow.grow_days
    assert effective_grow_days(yarrow, "autumn") > yarrow.grow_days

    daisy = growing_profile("daisy")  # not hardy
    assert effective_grow_days(daisy, "winter") == daisy.grow_days * 2


def test_season_suitability():
    yarrow = growing_profile("yarrow")
    assert season_is_suitable(yarrow, "spring")
    assert season_is_suitable(yarrow, "autumn")   # hardy tolerates
    assert not season_is_suitable(yarrow, "winter")


def test_high_water_herb_dies_when_neglected():
    profile = growing_profile("comfrey")  # high water
    assert watering_overdue_penalty(profile, 3) >= 90
    res, updates = evaluate_growth(
        herb_key="comfrey",
        planted_day=0,
        last_tended_day=0,
        last_eval_day=0,
        health=100,
        season="spring",
        current_day=4,  # 4 dry sunrises
    )
    assert res.dead
    assert updates.get("dead") == 1


def test_drought_hardy_herb_survives_neglect():
    res, _ = evaluate_growth(
        herb_key="yarrow",  # low water
        planted_day=0,
        last_tended_day=0,
        last_eval_day=0,
        health=100,
        season="spring",
        current_day=4,
    )
    assert not res.dead
    assert res.health == 100


def test_matures_after_grow_days():
    profile = growing_profile("daisy")
    res, _ = evaluate_growth(
        herb_key="daisy",
        planted_day=0,
        last_tended_day=5,
        last_eval_day=0,
        health=100,
        season="spring",
        current_day=profile.grow_days,
    )
    assert res.ready
    assert res.stage == "mature"


def test_not_ready_before_grow_days():
    res, _ = evaluate_growth(
        herb_key="yarrow",
        planted_day=0,
        last_tended_day=1,
        last_eval_day=0,
        health=100,
        season="spring",
        current_day=1,
    )
    assert not res.ready
    assert res.progress_pct < 100


def test_harvest_yield_scales_with_health():
    profile = growing_profile("daisy")

    class _R:
        def randint(self, a, b):
            return a

    healthy = harvest_yield(profile, 95, rng=_R())
    sick = harvest_yield(profile, 40, rng=_R())
    assert healthy > sick
    assert sick >= 1


def test_db_seed_and_planting_roundtrip():
    _setup()
    wolf_id = 4242
    db.add_herb_seeds(wolf_id, "daisy", 2)
    assert db.get_herb_seed_qty(wolf_id, "daisy") == 2
    assert db.consume_herb_seed(wolf_id, "daisy", 1)
    assert db.get_herb_seed_qty(wolf_id, "daisy") == 1
    assert not db.consume_herb_seed(wolf_id, "daisy", 5)

    pid = db.add_herb_planting(wolf_id, "daisy", guild_id=1, day=3, season="spring")
    assert db.count_herb_plantings(wolf_id) == 1
    planting = db.get_herb_planting(pid)
    assert planting["herb_key"] == "daisy"
    db.update_herb_planting(pid, health=20)
    assert db.get_herb_planting(pid)["health"] == 20
    db.remove_herb_planting(pid)
    assert db.count_herb_plantings(wolf_id) == 0


if __name__ == "__main__":
    _setup()
    test_poison_and_bark_not_cultivable()
    test_cultivable_list_excludes_restricted()
    test_off_season_slows_hardy_and_kills_tender()
    test_season_suitability()
    test_high_water_herb_dies_when_neglected()
    test_drought_hardy_herb_survives_neglect()
    test_matures_after_grow_days()
    test_not_ready_before_grow_days()
    test_harvest_yield_scales_with_health()
    test_db_seed_and_planting_roundtrip()
    print("OK")

