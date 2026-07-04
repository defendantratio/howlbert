"""Bot-startup smoke test: load every cog the way the bot does, offline.

This is the closest thing to "actually running the bot" without a Discord
connection. It builds a real discord.py Bot, loads every extension listed in
main.py's setup_hook, and assembles the application-command tree. That exercises
the code paths that only fail at startup and that no other test touches:

  - a cog module that imports fine in isolation but errors when its setup()
    runs and registers commands,
  - two commands registered under the same name (CommandAlreadyRegistered),
  - a broken command/group decorator,
  - a description or choice string over Discord's length limits surfacing when
    the tree is built.

It does NOT connect to Discord (no token, no bot.start), so it is safe and fast
in CI. The cog list is read from main.py so this test stays in sync with what
the bot actually loads.
"""

from __future__ import annotations

import asyncio
import re
import pathlib
import tempfile

import discord
from discord.ext import commands

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _use_temp_db() -> None:
    """Point the database at a throwaway file and create the schema, exactly as
    the bot's setup_hook does (db.init_db() before any cog loads). Some cogs
    query their tables in setup(), so the schema must exist first, and we must
    never touch the real dev database."""
    import database as db

    tmp = pathlib.Path(tempfile.gettempdir()) / "howlbert_startup_smoke.db"
    if tmp.exists():
        tmp.unlink()
    db.DB_PATH = str(tmp)  # get_db() reads this module global
    db.init_db()


def _cog_extensions() -> list[str]:
    """The exact extensions main.py loads, in order."""
    main_src = (ROOT / "main.py").read_text(encoding="utf-8")
    return re.findall(r'load_extension\(\s*["\']([^"\']+)["\']\s*\)', main_src)


def _build_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.members = True
    intents.guilds = True
    return commands.Bot(command_prefix="!", intents=intents)


async def _load_all(bot: commands.Bot, extensions: list[str]) -> None:
    for ext in extensions:
        await bot.load_extension(ext)


def test_bot_loads_all_cogs_and_builds_command_tree() -> None:
    extensions = _cog_extensions()
    assert len(extensions) > 20, f"expected many cog extensions in main.py, found {len(extensions)}"

    _use_temp_db()  # schema first, like the real setup_hook
    bot = _build_bot()
    try:
        # any import error, bad decorator, or duplicate command name raises here
        asyncio.run(_load_all(bot, extensions))
        # the assembled application-command tree should hold the real commands
        commands_in_tree = list(bot.tree.walk_commands())
        assert len(commands_in_tree) > 20, (
            f"command tree looks too small ({len(commands_in_tree)} commands); "
            "a cog may have failed to register."
        )
    finally:
        try:
            asyncio.run(bot.close())
        except Exception:  # noqa: BLE001 - closing an unstarted bot is best-effort
            pass


_TESTS = [test_bot_loads_all_cogs_and_builds_command_tree]


def main() -> None:
    passed = failed = 0
    for fn in _TESTS:
        try:
            fn()
            print(f"  OK  {fn.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f" FAIL {fn.__name__} - {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
