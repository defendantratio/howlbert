"""Per-wolf `/checklist` command."""

import database as db
from engine.wolf_checklist import build_wolf_checklist, collect_wolf_checklist, format_wolf_checklist


def test_fresh_wolf_shows_setup_and_daily():
    user = {
        "id": 1,
        "age_months": 36,
        "last_hunt_day": 0,
        "wolf_role": "hunter",
        "pack_id": 1,
        "last_daily_day": 0,
        "last_work_day": 0,
        "last_sniff_day": 0,
        "last_howl_day": 0,
        "last_socialize_day": 0,
        "last_role_event_day": 0,
        "last_forage_day": 0,
        "last_explore_day": 0,
    }
    setup, today = collect_wolf_checklist(user, day=10)[:2]
    assert "set proxy tag" in setup[0].lower()
    assert any("hunt" in item.lower() for item in today)
    assert any("den work" in item.lower() for item in today)

    text = build_wolf_checklist(user, day=10)
    assert text
    assert "**setup**" in text
    assert "**today**" in text
    assert "☐" in text
    assert "☑" not in text


def test_setup_complete_hides_done_items():
    user = {
        "id": 2,
        "age_months": 48,
        "avatar_url": "https://example.com/a.png",
        "proxy_prefix": "F:",
        "pronouns": "she/her",
        "ic_location": "Greyspire border",
        "wolf_role": "diplomat",
        "pack_id": 1,
        "last_daily_day": 10,
        "last_hunt_day": 10,
        "last_work_day": 10,
        "last_sniff_day": 10,
        "last_fishing_day": 10,
        "last_howl_day": 10,
        "last_socialize_day": 10,
        "last_role_event_day": 10,
        "last_forage_day": 10,
        "last_explore_day": 10,
        "herb_buffs": '{"manual_long_rest_day": 10}',
    }
    setup, today = collect_wolf_checklist(user, day=10)[:2]
    assert setup == []
    assert today == []
    assert build_wolf_checklist(user, day=10) is None


def test_juvenile_blooding_in_setup_only():
    user = {
        "id": 3,
        "age_months": 12,
        "last_hunt_day": 0,
        "has_blooding": 0,
        "wolf_role": "juvenile",
        "pack_id": 1,
    }
    setup, _today = collect_wolf_checklist(user, day=5)[:2]
    assert any("blooding" in item.lower() for item in setup)
    assert not any("rite blooding" in item for item in setup)


def test_juvenile_blooded_needs_rite_until_done():
    wolf_id = 9001
    with db.get_db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO users (
                id, discord_id, wolf_name, age_months, last_hunt_day, has_blooding,
                wolf_role, hp, max_hp, mood, hunger, thirst, exhaustion, condition, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 80, 80, 0, 'healthy', datetime('now'))
            """,
            (wolf_id, 8001, "RitePup", 12, 3, 1, "juvenile", 20, 20, 50),
        )
    user = db.get_user_by_id(wolf_id)
    setup, _ = collect_wolf_checklist(user, day=1)[:2]
    assert any("rite blooding" in item for item in setup)

    db.add_wolf_journal_entry(wolf_id, "rite_blooding", "Ceremony held.", day=1)
    setup2, _ = collect_wolf_checklist(db.get_user_by_id(wolf_id), day=1)[:2]
    assert not any("rite blooding" in item for item in setup2)


def test_pup_shows_play_not_hunt():
    user = {
        "id": 4,
        "age_months": 3,
        "wolf_role": "pup",
        "pack_id": 1,
        "last_play_day": 0,
    }
    setup, today = collect_wolf_checklist(user, day=3)[:2]
    assert any("juvenile age" in item for item in setup)
    assert any("play" in item.lower() for item in today)
    assert not any(item.lower().startswith("hunt") or " hunt" in item.lower() for item in today)


def test_format_empty_returns_none():
    assert format_wolf_checklist([], []) is None
