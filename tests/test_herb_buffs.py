"""Herb buff and supplemental treatment mechanics."""

from engine.herb_buffs import (
    apply_supplemental_herb,
    disease_save_uses_advantage,
)
from engine.conditions import treat_with_herb
from herbs import HERBS


class Row:
    def __init__(self, **kw):
        self._d = kw

    def __getitem__(self, k):
        return self._d[k]

    def keys(self):
        return self._d.keys()


def test_saffron_stabilizes_dying():
    user = Row(hp=0, condition="dying", disease="", active_injuries="[]")
    assert treat_with_herb(user, "saffron", HERBS["saffron"]) == "stabilized"


def test_elderberry_grants_three_day_advantage():
    user = Row(
        disease="",
        disease_save_buff=0,
        disease_save_buff_days=0,
        herb_buffs="{}",
        last_rest_day=5,
        mood=50,
    )
    effect = apply_supplemental_herb("elderberry", user, day=5, outcome="symptom_ease")
    assert effect is not None
    assert effect["fields"]["disease_save_buff_days"] == 3
    assert effect["fields"]["disease_save_buff"] == 1


def test_disease_save_advantage_flag():
    user = Row(disease_save_buff=1, disease_save_buff_days=0)
    assert disease_save_uses_advantage(user)


def test_witch_hazel_astringent():
    user = Row(
        disease="",
        active_injuries='["sprained_leg"]',
        herb_buffs="{}",
        last_rest_day=5,
        mood=50,
        exhaustion=0,
    )
    effect = apply_supplemental_herb("witch_hazel", user, day=10, outcome="symptom_ease")
    assert effect is not None
    assert "swelling" in effect["message"].lower()
    assert effect["fields"].get("herb_buffs")
    assert "venom_save_advantage" in effect["fields"]["herb_buffs"] or "pain_relief" in effect["fields"]["herb_buffs"]


def test_lung_herbs_grant_save():
    user = Row(
        disease="rot_lung:fever",
        herb_buffs="{}",
        last_rest_day=5,
        mood=50,
        exhaustion=2,
    )
    effect = apply_supplemental_herb("marsh_mallow", user, day=10, outcome="symptom_ease")
    assert effect is not None
    assert effect["fields"].get("disease_save_buff") == 1
