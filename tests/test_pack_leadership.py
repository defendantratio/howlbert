"""Great Pack alpha leadership checks."""

from engine.pack_leadership import can_act_as_pack_alpha, is_pack_alpha


class Row(dict):
    def keys(self):
        return super().keys()


def test_great_pack_alpha_by_role_not_stale_alpha_id():
    silverrush = Row(id=5, key="silverrush", alpha_id=999999999999999999)
    saltmuzzle = Row(
        id=132,
        discord_id=1056053114177855548,
        pack_id=5,
        wolf_role="alpha",
    )
    assert is_pack_alpha(saltmuzzle, silverrush)
    assert can_act_as_pack_alpha(saltmuzzle, silverrush)


def test_player_pack_still_requires_alpha_id_seat():
    pack = Row(id=99, key=None, alpha_id=111)
    leader = Row(id=1, discord_id=111, pack_id=99, wolf_role="alpha")
    other = Row(id=2, discord_id=222, pack_id=99, wolf_role="alpha")
    assert is_pack_alpha(leader, pack)
    assert not is_pack_alpha(other, pack)


def test_admin_bypass():
    pack = Row(id=99, key=None, alpha_id=111)
    user = Row(id=2, discord_id=222, pack_id=99, wolf_role="hunter")
    assert can_act_as_pack_alpha(user, pack, discord_admin=True)
