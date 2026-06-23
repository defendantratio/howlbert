"""Nursing helpers; logic tests without DB."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.conditions import herb_special_effect
from engine.nursing import is_nursery_caretaker, pup_fed_today, pup_needs_milk_today


class _Row(dict):
    def __getitem__(self, key):
        return super().__getitem__(key)

    def keys(self):
        return super().keys()


def test_is_nursery_caretaker():
    caretaker = _Row(wolf_role="caretaker", bonus_role_feature=None)
    apprentice = _Row(wolf_role="caretaker_apprentice", bonus_role_feature=None)
    hunter = _Row(wolf_role="hunter", bonus_role_feature=None)
    assert is_nursery_caretaker(caretaker)
    assert is_nursery_caretaker(apprentice)
    assert not is_nursery_caretaker(hunter)


def test_pup_milk_status():
    pup = _Row(age_months=3, condition="healthy", last_milk_day=5)
    assert pup_needs_milk_today(pup, 6)
    assert not pup_fed_today(pup, 6)
    pup["last_milk_day"] = 6
    assert not pup_needs_milk_today(pup, 6)
    assert pup_fed_today(pup, 6)


def test_honey_on_starving_pup():
    pup = _Row(age_months=3, hunger=10, thirst=80, exhaustion=2, disease="")
    assert herb_special_effect("honey", pup) == "feed_pup_honey"
    fed = _Row(age_months=3, hunger=80, thirst=80, exhaustion=0, disease="")
    assert herb_special_effect("honey", fed) == "honey_pup_not_depleted"


if __name__ == "__main__":
    test_is_nursery_caretaker()
    test_pup_milk_status()
    test_honey_on_starving_pup()
    print("ok")
