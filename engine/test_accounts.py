"""Detect and exclude bot unit-test registrations from public leaderboards."""

from __future__ import annotations

# Wolves created by local test runs; never show on /leaderboard or /halloffame.
TEST_WOLF_NAMES = frozenset(
    {
        "A",
        "TestWolf",
        "PactAlpha",
        "BondWolfA",
        "BondWolfB",
        "ChatWolf",
        "TestAlpha",
        "TestBeta",
        "Test",
        "TestLegend",
        "StarveWolf",
        "CollapseWolf",
        "TestDonor",
        "KsBacker",
    }
)

# Small fixed IDs used in tests (bonds, chat XP, cat pacts, …).
EXPLICIT_TEST_DISCORD_IDS = frozenset(
    {
        770001,
        770002,
        88010,
        888001,
        888002,
        888999,
    }
)


def is_test_discord_id(discord_id: int) -> bool:
    if discord_id in EXPLICIT_TEST_DISCORD_IDS:
        return True
    # Obvious fixtures (e.g. 99, 770001); not real Discord snowflakes.
    if discord_id < 1_000_000_000_000_000:
        return True
    # tests/test_*.py synthetic snowflakes: 18 digits starting with 9990-9993.
    text = str(discord_id)
    if len(text) == 18 and text.startswith(("9990", "9991", "9992", "9993")):
        return True
    return False


def is_test_wolf_name(name: str | None) -> bool:
    if not name:
        return False
    return name.strip() in TEST_WOLF_NAMES


def is_test_leaderboard_user(discord_id: int, wolf_name: str | None = None) -> bool:
    return is_test_discord_id(discord_id) or is_test_wolf_name(wolf_name)


def is_test_hall_account(discord_id: int) -> bool:
    return is_test_discord_id(discord_id)
