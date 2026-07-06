"""IC slash lines, whispers, location, journal (read-only), grief vigil, and signs."""
from __future__ import annotations
import logging
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from config import RP_LOCATIONS
from engine.journal_backfill import backfill_wolf_journal
from engine.wolf_journal import format_journal_embed_chunks
from utils.embeds import EMBED_COLOR, ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, PlayerEmbed, choice_label
from utils.replies import reply_ephemeral
from utils.wolf_autocomplete import make_member_wolf_autocomplete
logger = logging.getLogger('howlbert')
_MAX_SAY = 500
_MAX_WHISPER = 1000
_MAX_LOCATION = 120

_member_wolf_autocomplete = make_member_wolf_autocomplete("member")

async def _other_wolf_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    active = db.get_user(interaction.user.id)
    if not active:
        return []
    choices = []
    for wolf in db.list_user_wolves(interaction.user.id):
        if wolf['id'] == active['id']:
            continue
        name = wolf['wolf_name']
        if current and current.lower() not in name.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(name), value=name))
    return choices[:25]

def _resolve_own_wolf(discord_id: int, name: str):
    rows = db.list_user_wolves(discord_id)
    return next((w for w in rows if w['wolf_name'].lower() == name.strip().lower()), None)

def _active_wolf(interaction: discord.Interaction):
    return db.get_user(interaction.user.id)

def _wolf_avatar(wolf, member: discord.Member | None) -> str | None:
    url = wolf['avatar_url'] if 'avatar_url' in wolf.keys() else None
    if url:
        return url
    if member:
        return member.display_avatar.url
    return None

def _ic_location_line(wolf) -> str | None:
    loc = wolf['ic_location'] if 'ic_location' in wolf.keys() else None
    if loc and str(loc).strip():
        return f'📍 {str(loc).strip()}'
    return None

async def _location_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    needle = current.lower()
    choices = [loc for loc in RP_LOCATIONS if needle in loc.lower()]
    return [app_commands.Choice(name=choice_label(loc), value=loc) for loc in choices[:25]]

class Roleplay(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    location = app_commands.Group(name='location', description='set where your wolf is in-character.')

    @app_commands.command(name='say', description='post a one-line in-character line (no proxy intent needed).')
    @app_commands.describe(line='what your wolf says or does (one line)')
    async def say(self, interaction: discord.Interaction, line: str):
        wolf = _active_wolf(interaction)
        if not wolf:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        text = line.strip()
        if not text:
            await interaction.response.send_message(embed=howlbert_embed('Empty', 'Say something.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if len(text) > _MAX_SAY:
            text = text[:_MAX_SAY - 1] + '…'
        embed = PlayerEmbed(description=f'*"{text}"*', color=EMBED_COLOR)
        avatar = _wolf_avatar(wolf, interaction.user if isinstance(interaction.user, discord.Member) else None)
        embed.set_author(name=wolf['wolf_name'], icon_url=avatar)
        loc = _ic_location_line(wolf)
        if loc:
            embed.set_footer(text=loc)
        if interaction.channel:
            db.mark_collab_hunt_rp_said(wolf['id'], interaction.channel.id)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='whisper', description="send an in-character private message to another player's dms.")
    @app_commands.describe(member='who receives the whisper', message='in-character message')
    async def whisper(self, interaction: discord.Interaction, member: discord.Member, message: str):
        if member.bot:
            await interaction.response.send_message(embed=howlbert_embed('No', "You can't whisper bots.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if member.id == interaction.user.id:
            await interaction.response.send_message(embed=howlbert_embed('No', 'Whisper someone else.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        wolf = _active_wolf(interaction)
        if not wolf:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        text = message.strip()
        if not text:
            await interaction.response.send_message(embed=howlbert_embed('Empty', 'Write a whisper.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if len(text) > _MAX_WHISPER:
            text = text[:_MAX_WHISPER - 1] + '…'
        embed = PlayerEmbed(title=f"🤫 whisper from {wolf['wolf_name']}", description=text, color=EMBED_COLOR)
        avatar = _wolf_avatar(wolf, interaction.user)
        embed.set_author(name=wolf['wolf_name'], icon_url=avatar)
        embed.set_footer(text=f'to {member.display_name} · reply in-character in server')
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message(embed=howlbert_embed('DMs Closed', f"Couldn't reach **{member.display_name}**; their DMs may be off.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        await interaction.response.send_message(embed=howlbert_embed('Whisper Sent', f"**{wolf['wolf_name']}** whispered to **{member.display_name}**.", color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @app_commands.command(name='weep', description='silverrush only: release grief alone at the weep stone (unlimited; repeats soothe less).')
    async def weep(self, interaction: discord.Interaction):
        wolf = _active_wolf(interaction)
        if not wolf:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        if wolf['great_pack'] != 'silverrush':
            await interaction.response.send_message(embed=howlbert_embed('not your stone', 'the weep stone belongs to silverrush; other packs grieve their own way.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.vitals import living_wolf_block
        block = living_wolf_block(wolf)
        if block:
            await interaction.response.send_message(embed=howlbert_embed('cannot weep', block, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        from engine.diminishing import next_use_multiplier
        _weep_mult, _weep_n = next_use_multiplier(wolf, 'weep', day)
        db.update_user(interaction.user.id, last_weep_day=day, wolf_id=wolf['id'])
        _weep_gain = max(1, int(10 * _weep_mult))
        mood = db.adjust_mood(wolf['id'], _weep_gain)
        lines = [f"**{wolf['wolf_name']}** goes alone to the weep stone; no one watches. the river takes the rest.", f"mood **{mood}** (+{_weep_gain})."]
        from engine.diseases import parse_disease
        key, stage = parse_disease(wolf['disease'] if 'disease' in wolf.keys() else None)
        if key == 'grief_melancholy':
            db.set_user_conditions(interaction.user.id, wolf_id=wolf['id'], clear_disease=True)
            lines.append('_the grief breaks loose and washes downstream. you feel it; for now._')
        if _weep_n > 1:
            lines.append(f'_wept **{_weep_n}x** this sunrise; the stone soothes less each time (**{int(_weep_mult * 100)}%**)._')
        embed = howlbert_embed('weep stone', '\n'.join(lines), color=SUCCESS_COLOR)
        embed.set_footer(text='it is forbidden to watch another wolf weep · unlimited, repeats soothe less')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @location.command(name='set', description="mark your wolf's current in-character location.")
    @app_commands.describe(place='where you are ic (pick a suggestion or type your own)')
    @app_commands.autocomplete(place=_location_autocomplete)
    async def location_set(self, interaction: discord.Interaction, place: str):
        wolf = _active_wolf(interaction)
        if not wolf:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        cleaned = place.strip()[:_MAX_LOCATION]
        if not cleaned:
            await interaction.response.send_message(embed=howlbert_embed('Empty', 'Name a place.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.set_ic_location(interaction.user.id, wolf['id'], cleaned)
        await interaction.response.send_message(embed=howlbert_embed('Location Set', f"**{wolf['wolf_name']}** is at **{cleaned}**.", color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @location.command(name='clear', description="clear your wolf's ic location.")
    async def location_clear(self, interaction: discord.Interaction):
        wolf = _active_wolf(interaction)
        if not wolf:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        db.set_ic_location(interaction.user.id, wolf['id'], None)
        await interaction.response.send_message(embed=howlbert_embed('Location Cleared', f"**{wolf['wolf_name']}**'s whereabouts are unstated.", color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @location.command(name='show', description="show your or another wolf's ic location.")
    @app_commands.describe(member='whose wolf to check (defaults to you)', own_wolf='your other wolf to check (multi-wolf players)', member_wolf="specific wolf from that player's roster")
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, member_wolf=_member_wolf_autocomplete)
    async def location_show(self, interaction: discord.Interaction, member: discord.Member | None = None, own_wolf: str | None = None, member_wolf: str | None = None):
        if own_wolf:
            wolf = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not wolf:
                await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', 'No wolf with that name on your account. Check `/wolves`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            is_own = True
        else:
            target = member or interaction.user
            if member and member_wolf:
                wolf = db.find_user_wolf(member.id, member_wolf)
            else:
                wolf = db.get_user(target.id)
            if not wolf:
                msg = "You haven't registered yet." if target == interaction.user else f'{target.display_name} has no wolf.'
                await interaction.response.send_message(embed=howlbert_embed('No Wolf', msg, color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            is_own = (target == interaction.user)
        loc = wolf['ic_location'] if 'ic_location' in wolf.keys() else None
        if not loc:
            await interaction.response.send_message(embed=howlbert_embed('No Location', f"**{wolf['wolf_name']}** hasn't set a location (`/location set`).", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        await interaction.response.send_message(embed=howlbert_embed(f"📍 {wolf['wolf_name']}", str(loc), color=SUCCESS_COLOR), ephemeral=reply_ephemeral() if not is_own else False)

    @app_commands.command(name='journal', description="read your wolf's automatic life journal (major events only).")
    @app_commands.describe(member="another player's active wolf (optional)", own_wolf='your other wolf to read (multi-wolf players)', member_wolf="specific wolf from that player's roster")
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, member_wolf=_member_wolf_autocomplete)
    async def journal(self, interaction: discord.Interaction, member: discord.Member | None = None, own_wolf: str | None = None, member_wolf: str | None = None):
        if own_wolf:
            wolf = _resolve_own_wolf(interaction.user.id, own_wolf)
            if not wolf:
                await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', 'No wolf with that name on your account. Check `/wolves`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            is_own = True
        else:
            target = member or interaction.user
            if member and member_wolf:
                wolf = db.find_user_wolf(member.id, member_wolf)
            else:
                wolf = db.get_user(target.id)
            if not wolf:
                await interaction.response.send_message(embed=howlbert_embed('No Wolf', 'No registered wolf.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            is_own = (target == interaction.user)
        backfill_wolf_journal(wolf['id'])
        chunks = format_journal_embed_chunks(wolf['id'], limit=200)
        embeds: list[discord.Embed] = []
        for i, body in enumerate(chunks[:10]):
            title = f"📓 {wolf['wolf_name']}'s Journal" if i == 0 else f"📓 {wolf['wolf_name']}'s Journal (cont.)"
            embed = howlbert_embed(title, body, color=EMBED_COLOR)
            embeds.append(embed)
        if len(chunks) > 10:
            embeds[-1].set_footer(text='showing first 10 pages · older entries omitted')
        elif embeds:
            embeds[-1].set_footer(text='recorded automatically · backfilled from lore and gameplay')
        await interaction.response.send_message(embeds=embeds, ephemeral=reply_ephemeral() if not is_own else False)

async def setup(bot: commands.Bot):
    await bot.add_cog(Roleplay(bot))