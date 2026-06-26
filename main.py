import asyncio
import logging
import os
import traceback

import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import DISCORD_TOKEN, STATUS_CHANNEL_ID, BOT_DISPLAY_NAME
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, howlbert_embed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("howlbert")

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.guilds = True
def _parse_test_guild_ids() -> list[int]:
    raw = os.getenv("TEST_GUILD_IDS") or os.getenv("TEST_GUILD_ID") or ""
    ids: list[int] = []
    seen: set[int] = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            guild_id = int(part)
            if guild_id not in seen:
                seen.add(guild_id)
                ids.append(guild_id)
    return ids


TEST_GUILD_IDS = _parse_test_guild_ids()


class HowlbertBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=INTENTS)
        self._shutdown_status_posted = False

    async def close(self) -> None:
        if not self._shutdown_status_posted:
            self._shutdown_status_posted = True
            await _post_shutdown_status(self)
        await super().close()

    async def _sync_app_commands(self) -> None:
        if TEST_GUILD_IDS:
            for guild_id in TEST_GUILD_IDS:
                self.tree.copy_global_to(guild=discord.Object(id=guild_id))
            try:
                # Guild-only sync: drop global commands so they don't appear twice
                # alongside guild commands in the same server.
                self.tree.clear_commands(guild=None)
                await self.tree.sync()
                for guild_id in TEST_GUILD_IDS:
                    synced = await self.tree.sync(guild=discord.Object(id=guild_id))
                    logger.info("Synced %s command(s) to guild %s.", len(synced), guild_id)
                return
            except discord.Forbidden:
                logger.error(
                    "Cannot sync commands to one or more guilds in TEST_GUILD_IDS (403 Missing Access). "
                    "Invite the bot to every listed server with bot + applications.commands scopes, "
                    "or remove TEST_GUILD_IDS from .env for global commands only. "
                    "Skipping command sync this startup to avoid duplicate registrations.",
                )
                return

        synced = await self.tree.sync()
        logger.info("Synced %s global command(s).", len(synced))

    async def add_cog(self, cog, /, **kwargs):
        if TEST_GUILD_IDS and "guild" not in kwargs and "guilds" not in kwargs:
            kwargs["guilds"] = [discord.Object(id=g) for g in TEST_GUILD_IDS]
        return await super().add_cog(cog, **kwargs)

    async def setup_hook(self):
        db.init_db()
        await self.load_extension("cogs.profile")
        await self.load_extension("cogs.economy")
        await self.load_extension("cogs.pack")
        await self.load_extension("cogs.howl")
        await self.load_extension("cogs.world")
        await self.load_extension("cogs.hunting")
        await self.load_extension("cogs.explore")
        await self.load_extension("cogs.scout")
        await self.load_extension("cogs.wolvden")
        await self.load_extension("cogs.patron")
        await self.load_extension("cogs.quests")
        await self.load_extension("cogs.wolfadmin")
        await self.load_extension("cogs.prestige")
        await self.load_extension("cogs.rpg")
        await self.load_extension("cogs.herbs")
        await self.load_extension("cogs.garden")
        await self.load_extension("cogs.combat")
        await self.load_extension("cogs.life")
        await self.load_extension("cogs.prey_pile")
        await self.load_extension("cogs.collab_hunt")
        await self.load_extension("cogs.collab_patrol")
        await self.load_extension("cogs.role")
        await self.load_extension("cogs.bonds")
        await self.load_extension("cogs.skills")
        await self.load_extension("cogs.help")
        await self.load_extension("cogs.lexicon")

        await self._sync_app_commands()

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        logger.error("Command /%s failed:", interaction.command.name if interaction.command else "?")
        logger.error("%s", "".join(traceback.format_exception(error)))

        message = f"Something went wrong on {BOT_DISPLAY_NAME}'s side. Check the bot terminal for details."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=reply_ephemeral())
        else:
            await interaction.response.send_message(message, ephemeral=reply_ephemeral())


async def main():
    if not DISCORD_TOKEN:
        raise SystemExit(
            "No DISCORD_TOKEN found. Copy .env.example to .env and paste your bot token."
        )

    from utils.instance_lock import acquire_bot_lock

    acquire_bot_lock()

    bot = HowlbertBot()

    @bot.tree.error
    async def on_tree_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        logger.error(
            "Command /%s failed:",
            interaction.command.qualified_name if interaction.command else "?",
        )
        logger.error("%s", "".join(traceback.format_exception(error)))

        if isinstance(error, app_commands.TransformerError):
            message = (
                "Could not resolve that user. Pick them from Discord's **user picker** "
                "(click the player field and select a name), not by typing a username alone."
            )
        elif isinstance(error, app_commands.CommandInvokeError) and error.original:
            orig = error.original
            if isinstance(orig, discord.NotFound) and getattr(orig, "code", None) == 10062:
                message = (
                    "That command timed out before Howlbert could answer. "
                    "Try again; if it keeps happening, make sure only **one** bot instance is running."
                )
            else:
                message = (
                    f"Something went wrong on {BOT_DISPLAY_NAME}'s side. "
                    "Check the bot terminal for details."
                )
        else:
            message = (
                f"Something went wrong on {BOT_DISPLAY_NAME}'s side. "
                "Check the bot terminal for details."
            )

        embed = howlbert_embed("Command Failed", message, color=ERROR_COLOR)
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())
            else:
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        except discord.HTTPException:
            pass

    @bot.event
    async def on_ready():
        logger.info("Logged in as %s (id: %s)", bot.user, bot.user.id)
        if TEST_GUILD_IDS:
            logger.info(
                "TEST_GUILD_IDS=%s; slash commands registered for these servers only (instant sync).",
                TEST_GUILD_IDS,
            )
            for guild_id in TEST_GUILD_IDS:
                in_guild = discord.utils.get(bot.guilds, id=guild_id) is not None
                if not in_guild:
                    logger.error(
                        "Bot is not in server %s. Invite it there or remove it from TEST_GUILD_IDS.",
                        guild_id,
                    )
            guild_set = set(TEST_GUILD_IDS)
            other = [g.id for g in bot.guilds if g.id not in guild_set]
            if other:
                logger.warning(
                    "Bot is also in %s other server(s) where slash commands will NOT appear "
                    "while TEST_GUILD_IDS is set: %s",
                    len(other),
                    other,
                )
        else:
            logger.info(
                "Global slash commands synced; they may take up to ~1 hour to appear in all servers."
            )
        from engine.view_restore import restore_pending_views
        from engine.rollover_announce import start_auto_rollover

        await restore_pending_views(bot)
        start_auto_rollover(bot)
        await _post_startup_status(bot)

    async with bot:
        await bot.start(DISCORD_TOKEN)


async def _resolve_status_channel(bot: HowlbertBot):
    if not STATUS_CHANNEL_ID or not str(STATUS_CHANNEL_ID).strip().isdigit():
        return None
    channel_id = int(STATUS_CHANNEL_ID)
    try:
        channel = bot.get_channel(channel_id)
        if channel is None:
            channel = await bot.fetch_channel(channel_id)
        return channel
    except discord.HTTPException as exc:
        logger.warning("Could not resolve STATUS_CHANNEL_ID %s: %s", channel_id, exc)
        return None


async def _post_startup_status(bot: HowlbertBot) -> None:
    channel = await _resolve_status_channel(bot)
    if not channel:
        return
    try:
        from utils.embeds import SUCCESS_COLOR, howlbert_embed

        guild_note = (
            f"guild sync `{','.join(str(g) for g in TEST_GUILD_IDS)}`"
            if TEST_GUILD_IDS
            else "global commands"
        )
        embed = howlbert_embed(
            f"{BOT_DISPLAY_NAME} Online",
            f"Logged in as **{bot.user}** · {guild_note} · pending consent views restored.",
            color=SUCCESS_COLOR,
        )
        await channel.send(embed=embed)
        logger.info("Posted startup status to channel %s.", channel.id)
    except discord.HTTPException as exc:
        logger.warning("Could not post startup status to channel %s: %s", channel.id, exc)


async def _post_shutdown_status(bot: HowlbertBot) -> None:
    channel = await _resolve_status_channel(bot)
    if not channel:
        return
    try:
        from utils.embeds import howlbert_embed

        embed = howlbert_embed(
            f"{BOT_DISPLAY_NAME} Offline",
            "The den is silent; bot stopped or reconnecting. Slash commands won't respond until **Online** returns.",
            color=discord.Color.from_rgb(120, 120, 120),
        )
        await channel.send(embed=embed)
        logger.info("Posted shutdown status to channel %s.", channel.id)
    except discord.HTTPException as exc:
        logger.warning("Could not post shutdown status to channel %s: %s", channel.id, exc)


if __name__ == "__main__":
    asyncio.run(main())
