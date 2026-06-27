"""`/proxy`; tupperbox-style speak-as-your-wolf proxying + Tupperbox import."""
from __future__ import annotations
import logging
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.avatar_crop import validate_avatar_upload
from engine.proxy_avatar_ui import AvatarCropView
from engine.proxy import get_proxy_webhook, parse_bracket_string, parse_tupperbox_export, sanitize_webhook_name
from engine.proxy_ooc import split_ooc
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label
from utils.replies import reply_ephemeral
logger = logging.getLogger('howlbert')
_MAX_PROXY_ATTACH = 8 * 1024 * 1024

async def _own_wolf_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    rows = db.list_user_wolves(interaction.user.id)
    cur = (current or '').lower()
    out = []
    for w in rows:
        if cur in w['wolf_name'].lower():
            out.append(app_commands.Choice(name=w['wolf_name'], value=w['wolf_name']))
        if len(out) >= 20:
            break
    return out

def _resolve_wolf(interaction: discord.Interaction, own_wolf: str | None):
    if own_wolf:
        wolf = db.find_user_wolf(interaction.user.id, own_wolf)
        if not wolf:
            return (None, 'No wolf with that name on your account. Check `/wolves`.')
        return (wolf, None)
    wolf = db.get_user(interaction.user.id)
    if not wolf:
        return (None, '__not_registered__')
    return (wolf, None)

async def _fetch_image_bytes(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            resp.raise_for_status()
            return await resp.read()

class Proxy(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    proxy = app_commands.Group(name='proxy', description='speak in-character as your wolves (tupperbox-style) and import from tupperbox.')

    @proxy.command(name='set', description='set a proxy tag so typed messages post as this wolf.')
    @app_commands.describe(tag="tag template using 'text' as the placeholder, e.g. h:text or [text]", own_wolf='which of your wolves (defaults to your active wolf)')
    @app_commands.autocomplete(own_wolf=_own_wolf_autocomplete)
    async def set_tag(self, interaction: discord.Interaction, tag: str, own_wolf: str | None=None):
        wolf, err = _resolve_wolf(interaction, own_wolf)
        if err == '__not_registered__':
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if err:
            await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        prefix, suffix = parse_bracket_string(tag)
        if not prefix and (not suffix):
            await interaction.response.send_message(embed=howlbert_embed('Bad Tag', 'Give a tag like `H:text`, `[text]`, or `text-h` (use `text` as the placeholder).', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.set_wolf_proxy(wolf['id'], prefix, suffix)
        example = f"{prefix or ''}hello{suffix or ''}"
        body = f"**{wolf['wolf_name']}** will now speak when you type `{example}`.\nSet an avatar with `/proxy avatar`. Bot needs **Manage Webhooks** + **Manage Messages** here."
        await interaction.response.send_message(embed=howlbert_embed('Proxy Tag Set', body, color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @proxy.command(name='avatar', description='set the avatar image a wolf proxies with.')
    @app_commands.describe(image='upload an image file (opens the crop editor)', url='or paste a direct image url (opens the crop editor)', clear="remove this wolf's proxy avatar", own_wolf='which of your wolves (defaults to your active wolf)')
    @app_commands.autocomplete(own_wolf=_own_wolf_autocomplete)
    async def set_avatar(self, interaction: discord.Interaction, image: discord.Attachment | None=None, url: str | None=None, clear: bool=False, own_wolf: str | None=None):
        wolf, err = _resolve_wolf(interaction, own_wolf)
        if err == '__not_registered__':
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if err:
            await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if clear:
            if image or url:
                await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use `clear:true` by itself, or provide an image — not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            db.set_wolf_identity(wolf['id'], avatar_url=None)
            await interaction.response.send_message(embed=howlbert_embed(f"{wolf['wolf_name']}", 'Proxy avatar cleared.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
            return
        if image and url:
            await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Attach an **image** or give a **url** — not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not image and (not url):
            await interaction.response.send_message(embed=howlbert_embed('No Image', 'Attach an **image** to this command, paste a direct **url**, or use `clear:true`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        await interaction.response.defer(ephemeral=reply_ephemeral())
        try:
            if image:
                data = await image.read()
                err_msg = validate_avatar_upload(data, content_type=image.content_type, filename=image.filename)
            else:
                if not url.lower().startswith(('http://', 'https://')):
                    await interaction.followup.send(embed=howlbert_embed('Bad URL', 'Give a direct `http(s)` image link.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                    return
                data = await _fetch_image_bytes(url)
                err_msg = validate_avatar_upload(data, filename=url)
        except (aiohttp.ClientError, TimeoutError):
            await interaction.followup.send(embed=howlbert_embed('Download Failed', 'Could not fetch that image URL.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        except Exception:
            logger.exception('Avatar load failed for user %s', interaction.user.id)
            await interaction.followup.send(embed=howlbert_embed('Read Failed', 'Could not read that image.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if err_msg:
            await interaction.followup.send(embed=howlbert_embed('Bad Image', err_msg, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.followup.send(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        view = AvatarCropView(self.bot, owner_id=interaction.user.id, wolf=wolf, source_bytes=data, guild=interaction.guild)
        await interaction.followup.send(embed=view._embed(), file=view._preview_file(), view=view, ephemeral=reply_ephemeral())

    @proxy.command(name='list', description="list your wolves' proxy tags and autoproxy state.")
    async def list_proxies(self, interaction: discord.Interaction):
        wolves = db.list_user_wolves(interaction.user.id)
        if not wolves:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        auto_id = db.get_autoproxy_wolf_id(interaction.user.id)
        lines = []
        for w in wolves:
            prefix = w['proxy_prefix'] or ''
            suffix = w['proxy_suffix'] or ''
            tag = f'`{prefix}text{suffix}`' if prefix or suffix else '_no tag_'
            star = ' ⭐ autoproxy' if auto_id == w['id'] else ''
            av = ' 🖼️' if w['avatar_url'] else ''
            lines.append(f"**{w['wolf_name']}** — {tag}{av}{star}")
        embed = howlbert_embed('Your Proxies', '\n'.join(lines), color=SUCCESS_COLOR)
        embed.set_footer(text='/proxy set · /proxy avatar · /proxy autoproxy · /proxy import')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @proxy.command(name='clear', description="remove a wolf's proxy tag.")
    @app_commands.describe(own_wolf='which of your wolves (defaults to your active wolf)')
    @app_commands.autocomplete(own_wolf=_own_wolf_autocomplete)
    async def clear_tag(self, interaction: discord.Interaction, own_wolf: str | None=None):
        wolf, err = _resolve_wolf(interaction, own_wolf)
        if err == '__not_registered__':
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if err:
            await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.clear_wolf_proxy(wolf['id'])
        if db.get_autoproxy_wolf_id(interaction.user.id) == wolf['id']:
            db.set_autoproxy_wolf(interaction.user.id, None)
        await interaction.response.send_message(embed=howlbert_embed(f"{wolf['wolf_name']}", 'Proxy tag removed.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @proxy.command(name='autoproxy', description='proxy all your untagged messages as one wolf (or turn it off).')
    @app_commands.describe(mode='on = proxy as the chosen wolf; off = stop autoproxy', own_wolf='wolf to autoproxy as (defaults to your active wolf)')
    @app_commands.choices(mode=[app_commands.Choice(name='on', value='on'), app_commands.Choice(name='off', value='off')])
    @app_commands.autocomplete(own_wolf=_own_wolf_autocomplete)
    async def autoproxy(self, interaction: discord.Interaction, mode: app_commands.Choice[str], own_wolf: str | None=None):
        if mode.value == 'off':
            db.set_autoproxy_wolf(interaction.user.id, None)
            await interaction.response.send_message(embed=howlbert_embed('Autoproxy Off', 'Untagged messages stay as you.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
            return
        wolf, err = _resolve_wolf(interaction, own_wolf)
        if err == '__not_registered__':
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if err:
            await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.set_autoproxy_wolf(interaction.user.id, wolf['id'])
        await interaction.response.send_message(embed=howlbert_embed('Autoproxy On', f"Untagged messages now post as **{wolf['wolf_name']}**. Start a message with `\\` to send as yourself once.", color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @proxy.command(name='import', description='import proxies from a tupperbox or pluralkit export file.')
    @app_commands.describe(file='your tupperbox export json (dm tupperbox `tul!export`) or pluralkit export', link_to_wolves='match imported names to your existing wolves (default: yes)')
    async def import_proxies(self, interaction: discord.Interaction, file: discord.Attachment, link_to_wolves: bool=True):
        await interaction.response.defer(ephemeral=reply_ephemeral())
        if not (file.filename.lower().endswith('.json') or 'json' in (file.content_type or '')):
            await interaction.followup.send(embed=howlbert_embed('Wrong File', 'Attach the `.json` export file.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        try:
            raw = (await file.read()).decode('utf-8', errors='replace')
            entries = parse_tupperbox_export(raw)
        except ValueError as exc:
            await interaction.followup.send(embed=howlbert_embed('Import Failed', str(exc), color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        except Exception:
            logger.exception('Proxy import parse failed for %s', interaction.user.id)
            await interaction.followup.send(embed=howlbert_embed('Import Failed', 'Could not read that export file.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not entries:
            await interaction.followup.send(embed=howlbert_embed('Nothing to Import', 'No proxies found in that file.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        wolves = {w['wolf_name'].lower(): w for w in db.list_user_wolves(interaction.user.id)}
        linked: list[str] = []
        unmatched: list[str] = []
        for entry in entries:
            if not (entry['prefix'] or entry['suffix']):
                continue
            wolf = wolves.get(entry['name'].lower()) if link_to_wolves else None
            if not wolf:
                unmatched.append(entry['name'])
                continue
            db.set_wolf_proxy(wolf['id'], entry['prefix'], entry['suffix'])
            fields = {}
            if entry.get('avatar_url'):
                fields['avatar_url'] = entry['avatar_url']
            if entry.get('bio'):
                fields['bio'] = entry['bio'][:1900]
            if entry.get('birthday'):
                fields['birthday'] = str(entry['birthday'])[:32]
            if fields:
                db.set_wolf_identity(wolf['id'], **fields)
            linked.append(wolf['wolf_name'])
        body = [f'Imported tags for **{len(linked)}** wolf(s).']
        if linked:
            body.append('✅ ' + ', '.join(linked[:25]))
        if unmatched:
            body.append(f"\n**{len(unmatched)}** export name(s) had no matching wolf (rename a wolf to match, then re-import): {', '.join(unmatched[:15])}")
        await interaction.followup.send(embed=howlbert_embed('Tupperbox Import', '\n'.join(body), color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.webhook_id is not None:
            return
        if message.guild is None or not isinstance(message.author, discord.Member):
            return
        content = message.content or ''
        if content.startswith(self.bot.command_prefix):
            return
        if content.startswith('\\'):
            return
        wolf = None
        inner = content
        match = db.match_proxy(message.author.id, content)
        if match:
            wolf, inner = match
        else:
            auto_id = db.get_autoproxy_wolf_id(message.author.id)
            if auto_id:
                wolf = db.get_user_by_id(auto_id)
                inner = content
        if not wolf:
            return
        if not inner and (not message.attachments):
            return
        await self._send_as_wolf(message, wolf, inner)

    async def _send_as_wolf(self, message: discord.Message, wolf, content: str) -> None:
        channel = message.channel
        thread = None
        if isinstance(channel, discord.Thread):
            thread = channel
            channel = channel.parent
        if not isinstance(channel, discord.TextChannel):
            return
        me = message.guild.me
        perms = channel.permissions_for(me)
        if not (perms.manage_webhooks and perms.manage_messages):
            return
        webhook = await get_proxy_webhook(channel)
        if webhook is None:
            return
        files = []
        for att in message.attachments:
            if att.size and att.size > _MAX_PROXY_ATTACH:
                continue
            try:
                files.append(await att.to_file())
            except (discord.HTTPException, discord.NotFound):
                pass
        username = sanitize_webhook_name(wolf['wolf_name'])
        avatar = wolf['avatar_url'] if 'avatar_url' in wolf.keys() else None
        ic_text, ooc_text = split_ooc(content)
        allowed = discord.AllowedMentions(everyone=False, users=True, roles=False)
        footer_bits: list[str] = []
        loc = wolf['ic_location'] if 'ic_location' in wolf.keys() else None
        if loc and str(loc).strip():
            footer_bits.append(f'📍 {str(loc).strip()}')
        if ooc_text:
            ooc_short = ooc_text if len(ooc_text) <= 180 else ooc_text[:177] + '…'
            footer_bits.append(f'OOC: {ooc_short}')
        try:
            kwargs = dict(username=username, content=ic_text or None, files=files or discord.utils.MISSING, allowed_mentions=allowed, wait=False)
            if avatar:
                kwargs['avatar_url'] = avatar
            if thread is not None:
                kwargs['thread'] = thread
            if footer_bits:
                kwargs['embeds'] = [discord.Embed(color=discord.Color.dark_grey()).set_footer(text=' · '.join(footer_bits))]
            await webhook.send(**kwargs)
        except discord.HTTPException:
            logger.info('Proxy webhook send failed in channel %s', channel.id)
            return
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(Proxy(bot))