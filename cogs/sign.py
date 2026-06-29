"""`/sign`; body / visual language so wolves can speak without a howl."""
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.signing import BASE_PHRASES, FIELD_PHRASES, MOTION_PHRASES, SIGNAL_CATALOG, execute_read, execute_sign
from utils.embeds import choice_label

_SIGNAL_CHOICES = [app_commands.Choice(name=choice_label(f"{info['name']} — {info['summary']}"), value=key) for key, info in SIGNAL_CATALOG.items()] + [app_commands.Choice(name=choice_label('read den signals — answer a denmate'), value='read')]
_BASE_CHOICES = [app_commands.Choice(name=choice_label(name), value=key) for key, name in BASE_PHRASES.items()]
_MOTION_CHOICES = [app_commands.Choice(name=choice_label(name), value=key) for key, name in MOTION_PHRASES.items()]
_FIELD_CHOICES = [app_commands.Choice(name=choice_label(name), value=key) for key, name in FIELD_PHRASES.items()]

async def _own_wolf_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    rows = db.list_user_wolves(interaction.user.id)
    cur = (current or '').lower()
    out = []
    for w in rows:
        name = w['wolf_name']
        if cur in name.lower():
            out.append(app_commands.Choice(name=choice_label(name), value=name))
        if len(out) >= 20:
            break
    return out

class Sign(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='sign', description='speak with body language; alert, rally, play, soothe, nuzzle, stretch, or read the den.')
    @app_commands.describe(signal="the body-language signal to give (or read the den's signals)", wolf='target denmate (player) for a directed signal', own_wolf='target one of your own wolves for a directed signal', message='optional roleplay line', base='ASL-style: which body part leads (close/exact combo with motion+field = bond or standing)', motion='ASL-style: how it moves (close/exact combo with base+field = bond or standing)', field='ASL-style: where it is aimed (close/exact combo with base+motion = bond or standing)')
    @app_commands.choices(signal=_SIGNAL_CHOICES, base=_BASE_CHOICES, motion=_MOTION_CHOICES, field=_FIELD_CHOICES)
    @app_commands.autocomplete(own_wolf=_own_wolf_autocomplete)
    async def sign(self, interaction: discord.Interaction, signal: app_commands.Choice[str], wolf: discord.Member | None=None, own_wolf: str | None=None, message: str | None=None, base: app_commands.Choice[str] | None=None, motion: app_commands.Choice[str] | None=None, field: app_commands.Choice[str] | None=None):
        if signal.value == 'read':
            await execute_read(interaction)
            return
        await execute_sign(
            interaction, signal.value, wolf=wolf, own_wolf=own_wolf, message=message,
            base=base.value if base else None, motion=motion.value if motion else None,
            field=field.value if field else None,
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Sign(bot))