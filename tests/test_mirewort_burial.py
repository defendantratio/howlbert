"""Mirewort grave-plant flavor and wolf transfer autoproxy migration."""

import database as db
from engine.mirewort_burial import (
    is_mirewort,
    mirewort_carcass_burial_note,
    mirewort_grave_rite,
)


def _row(wolf_name: str):
    return {"wolf_name": wolf_name}


def _insert_wolf(discord_id: int, wolf_name: str) -> int:
    with db.get_db() as conn:
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                hp, max_hp, hunger, thirst, exhaustion, condition, wolf_role
            ) VALUES (?, ?, NULL, 'hunter', datetime('now'), 20, 20, 80, 80, 0, 'healthy', 'hunter')
            """,
            (discord_id, wolf_name),
        )
    row = db.get_wolf_by_name(wolf_name)
    assert row is not None
    return int(row["id"])


def test_is_mirewort_case_insensitive():
    assert is_mirewort(_row("Mirewort"))
    assert is_mirewort(_row("  mirewort  "))
    assert not is_mirewort(_row("Soot"))


def test_mirewort_grave_rite_names_deceased():
    speech, journal = mirewort_grave_rite("Sedgepup", herb_key="marsh_mallow")
    assert "Sedgepup" in speech
    assert "Marsh-Mallow" in speech
    assert "Marsh-Mallow" in journal


def test_mirewort_grave_rite_keeps_custom_words():
    speech, _journal = mirewort_grave_rite(
        "Ash",
        custom_words="The den howls once.",
        herb_key="yarrow",
    )
    assert speech.startswith("The den howls once.")
    assert "Ash" in speech
    assert "Yarrow" in speech


def test_mirewort_carcass_burial_with_ritual_herb():
    note = mirewort_carcass_burial_note(ritual_herb_key="lavender")
    assert "Lavender" in note
    assert "grave will green" in note


def test_transfer_moves_autoproxy_to_new_owner():
    old_id, new_id = 7101, 7102
    wolf_id = _insert_wolf(old_id, "ProxyWolf")
    db.set_autoproxy_wolf(old_id, wolf_id)

    result = db.reassign_wolf_owner(wolf_id, new_id)
    assert result == "ok"
    assert db.get_autoproxy_wolf_id(old_id) is None
    assert db.get_autoproxy_wolf_id(new_id) == wolf_id


def test_transfer_leaves_unrelated_autoproxy():
    old_id, new_id = 7103, 7104
    keep_id = _insert_wolf(old_id, "KeepAuto")
    move_id = _insert_wolf(old_id, "MoveWolf")
    db.set_autoproxy_wolf(old_id, keep_id)

    db.reassign_wolf_owner(move_id, new_id)

    assert db.get_autoproxy_wolf_id(old_id) == keep_id
    assert db.get_autoproxy_wolf_id(new_id) is None
