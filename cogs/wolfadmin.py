import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import database as db
from cogs.profile import PACK_CHOICES, _pack_display
from engine.attraction import BIRTH_SEX_LABELS, SEXUALITY_LABELS, SEXUALITY_OPTIONS
from engine.aging import format_wolf_age, stage_for_age, stage_label
from engine.family import XP_PER_ROLE_FEATURE
from rpg_rules import ROLE_FEATURES, ROLE_LABELS
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, choice_label
from utils.permissions import is_howlbert_admin
from utils.notifications import try_dm_user
from engine.proxy import parse_bracket_string

async def _wolfadmin_wolf_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    from_player = getattr(interaction.namespace, 'from_player', None)
    player = from_player or getattr(interaction.namespace, 'player', None)
    if not player:
        return []
    wolves = db.list_user_wolves(player.id)
    needle = current.lower()
    choices = []
    for row in wolves:
        name = row['wolf_name']
        if needle and needle not in name.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(name), value=name))
    return choices[:25]

def _wolf_not_found_embed(player: discord.User, wolf_name: str) -> discord.Embed:
    body = db.explain_wolf_not_found(player.id, wolf_name, player_label=player.display_name)
    return howlbert_embed('Wolf Not Found', body, color=ERROR_COLOR)

def _resolve_player_wolf(player: discord.User, wolf_name: str | None):
    if wolf_name:
        return db.find_user_wolf(player.id, wolf_name)
    return db.get_user(player.id)

class WolfAdmin(commands.Cog):
    wolfadmin = app_commands.Group(name='wolfadmin', description='admin; create or reassign wolf profiles for players.')

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _require_admin(self, interaction: discord.Interaction) -> bool:
        if is_howlbert_admin(interaction):
            return True
        embed = howlbert_embed('Denied', 'Admins only.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return False

    @wolfadmin.command(name='assign', description='create a wolf and assign it to a player.')
    @app_commands.describe(player='discord member who will own this wolf', name='wolf name', pack='great pack or loner', birth_sex='birth sex', sexuality='attraction', role='wolf role (stats and skills)', starting_age='starting age in moons, 0 to 120 (optional)', set_active='make this their active wolf immediately')
    @app_commands.choices(pack=PACK_CHOICES, birth_sex=[app_commands.Choice(name='female', value='female'), app_commands.Choice(name='male', value='male'), app_commands.Choice(name='intersex', value='intersex'), app_commands.Choice(name='nonbinary', value='nonbinary')], sexuality=[app_commands.Choice(name=choice_label(name), value=value) for name, value in SEXUALITY_OPTIONS], role=[app_commands.Choice(name=ROLE_LABELS[key], value=key) for key in ROLE_LABELS])
    async def wolfadmin_assign(self, interaction: discord.Interaction, player: discord.User, name: str, pack: str, birth_sex: str, sexuality: str, role: str='hunter', starting_age: app_commands.Range[int, 0, 120] | None=None, set_active: bool=True):
        if not await self._require_admin(interaction):
            return
        if player.bot:
            embed = howlbert_embed('Invalid Player', 'Bots cannot own wolves.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        wolf_name, name_err = db.validate_wolf_name_available(name, label='Wolf names')
        if name_err:
            title = 'Name Taken' if 'already taken' in name_err else 'Invalid Name'
            embed = howlbert_embed(title, name_err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        try:
            wolf_id = db.register_user(player.id, wolf_name, pack, wolf_role=role, birth_sex=birth_sex, sexuality=sexuality, age_months=starting_age, set_active=set_active)
        except ValueError as exc:
            msg = str(exc)
            title = 'Name Taken' if 'already taken' in msg or 'reserved' in msg else 'Invalid Name'
            embed = howlbert_embed(title, msg, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        user = db.get_user_by_id(wolf_id)
        embed = howlbert_embed('Wolf Assigned', color=SUCCESS_COLOR)
        embed.add_field(name='Player', value=player.mention, inline=True)
        embed.add_field(name='Wolf', value=wolf_name, inline=True)
        embed.add_field(name='Active', value='Yes' if set_active else 'No (use `/switchwolf`)', inline=True)
        embed.add_field(name='Birth Sex', value=BIRTH_SEX_LABELS.get(birth_sex, birth_sex.title()), inline=True)
        embed.add_field(name='Sexuality', value=SEXUALITY_LABELS.get(sexuality, sexuality.title()), inline=True)
        embed.add_field(name='Role', value=ROLE_LABELS.get(user['wolf_role'], user['wolf_role'].title()), inline=True)
        age_mo = user['age_months'] if 'age_months' in user.keys() else 24
        embed.add_field(name='Age', value=f'{format_wolf_age(age_mo)} ({stage_label(stage_for_age(age_mo))})', inline=True)
        embed.add_field(name='Pack', value=_pack_display(pack), inline=False)
        await interaction.response.send_message(embed=embed)

    @wolfadmin.command(name='arrival', description='post the arrival/birth scene for an already-registered wolf.')
    @app_commands.describe(wolf_name='wolf to post the scene for')
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_arrival(self, interaction: discord.Interaction, wolf_name: str):
        if not await self._require_admin(interaction):
            return
        wolf = db.get_wolf_by_name(wolf_name.strip())
        if not wolf:
            embed = howlbert_embed('Not Found', f'No wolf named **{wolf_name}** is registered.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.long_term_injuries import parse_long_term_injuries
        ARRIVAL_KEYS = {'bold_arrival', 'quiet_arrival', 'wary_arrival',
                        'bold_birth', 'quiet_birth', 'wary_birth'}
        current = parse_long_term_injuries(wolf['long_term_injuries'])
        cleaned = [e for e in current if e not in ARRIVAL_KEYS]
        import json
        db.update_user_by_id(wolf['id'], long_term_injuries=json.dumps(cleaned))
        from engine.aging import stage_for_age
        from config import UNAFFILIATED_KEYS
        age_mo = wolf['age_months'] if 'age_months' in wolf.keys() else 24
        pack = wolf['great_pack'] if 'great_pack' in wolf.keys() else None
        is_pup = stage_for_age(age_mo) == 'pup'
        is_loner = pack in UNAFFILIATED_KEYS if UNAFFILIATED_KEYS else False
        if is_pup and is_loner:
            title = 'how were they born?'
            desc = f'before **{wolf["wolf_name"]}** opens their eyes for good, no den walls around them yet.'
        elif is_pup:
            title = 'how were they born?'
            desc = f'before **{wolf["wolf_name"]}** opens their eyes for good, the litter takes shape.'
        else:
            title = 'how did they arrive?'
            desc = f'before **{wolf["wolf_name"]}** settles in, the den watches them come.'
        from utils.embeds import howlbert_embed
        from utils.views import make_arrival_scene_view
        scene_embed = howlbert_embed(title, desc)
        view = make_arrival_scene_view(wolf['id'], wolf['wolf_name'], wolf['discord_id'], pup=is_pup, loner=is_loner)
        await interaction.response.send_message(embed=scene_embed, view=view)

    @wolfadmin.command(name='transfer', description='move an existing wolf from one player to another.')
    @app_commands.describe(from_player='current owner', wolf_name='which wolf to move', to_player='new owner', set_active='make this their active wolf immediately')
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_transfer(self, interaction: discord.Interaction, from_player: discord.User, wolf_name: str, to_player: discord.User, set_active: bool=True):
        if not await self._require_admin(interaction):
            return
        if to_player.bot:
            embed = howlbert_embed('Invalid Player', 'Bots cannot own wolves.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        wolf = db.find_user_wolf(from_player.id, wolf_name)
        if not wolf:
            await interaction.response.send_message(embed=_wolf_not_found_embed(from_player, wolf_name), ephemeral=reply_ephemeral())
            return
        if from_player.id == to_player.id:
            embed = howlbert_embed('Same Player', 'Pick a different owner to transfer to.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        result = db.reassign_wolf_owner(wolf['id'], to_player.id, set_active=set_active)
        if result == 'same_owner':
            embed = howlbert_embed('Same Player', 'That wolf already belongs to the target player.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Wolf Transferred', color=SUCCESS_COLOR)
        embed.add_field(name='Wolf', value=wolf['wolf_name'], inline=True)
        embed.add_field(name='From', value=from_player.mention, inline=True)
        embed.add_field(name='To', value=to_player.mention, inline=True)
        embed.add_field(name='Active for new owner', value='Yes' if set_active else 'No', inline=True)
        await interaction.response.send_message(embed=embed)

    @wolfadmin.command(name='list', description='list all wolves registered to a player.')
    @app_commands.describe(player='discord member to inspect')
    async def wolfadmin_list(self, interaction: discord.Interaction, player: discord.User):
        if not await self._require_admin(interaction):
            return
        await interaction.response.defer()
        wolves = db.list_user_wolves(player.id)
        if not wolves:
            embed = howlbert_embed('No Wolves', f'**{player.display_name}** has no registered wolves.', color=ERROR_COLOR)
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())
            return
        active_id = db.get_active_wolf_id(player.id)
        lines = []
        for row in wolves:
            marker = ' *(active)*' if row['id'] == active_id else ''
            role_key = row['wolf_role'] if row['wolf_role'] else 'hunter'
            role = ROLE_LABELS.get(role_key, str(role_key).title())
            lines.append(f"**{row['wolf_name']}**; {role} (id `{row['id']}`){marker}")
        embed = howlbert_embed(f'Wolves: {player.display_name}', '\n'.join(lines), color=SUCCESS_COLOR)
        embed.set_footer(text=f'{len(wolves)} wolf(s) · discord id {player.id}')
        await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())

    @wolfadmin.command(name='possess', description="steer another player's wolf (all commands act as that character).")
    @app_commands.describe(player='wolf owner', wolf_name='which wolf (defaults to their active wolf)')
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_possess(self, interaction: discord.Interaction, player: discord.User, wolf_name: str | None=None):
        if not await self._require_admin(interaction):
            return
        if player.bot:
            embed = howlbert_embed('Invalid Player', 'Bots cannot own wolves.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        wolf, err = db.resolve_possessed_wolf(interaction.user.id, player.id, wolf_name)
        if err:
            embed = howlbert_embed('Wolf Not Found', err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        ok, msg = db.set_admin_possess(interaction.user.id, wolf['id'])
        if not ok:
            embed = howlbert_embed('Cannot Possess', msg, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Possessing Wolf', msg, color=SUCCESS_COLOR)
        embed.set_footer(text='use /wolfadmin release when done · /profile shows their sheet')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @wolfadmin.command(name='release', description="stop steering another player's wolf and return to your own.")
    async def wolfadmin_release(self, interaction: discord.Interaction):
        if not await self._require_admin(interaction):
            return
        ok, msg = db.clear_admin_possess(interaction.user.id)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = 'Released' if ok else 'Not Possessing'
        embed = howlbert_embed(title, msg, color=color)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @wolfadmin.command(name='refimage', description="set or clear a wolf's reference image (admin only).")
    @app_commands.describe(player='wolf owner', image_url='direct http(s) image url (omit to clear)', wolf_name='which wolf (defaults to their active wolf)')
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_refimage(self, interaction: discord.Interaction, player: discord.User, image_url: str | None=None, wolf_name: str | None=None):
        if not await self._require_admin(interaction):
            return
        if wolf_name:
            wolf = db.find_user_wolf(player.id, wolf_name)
            if not wolf:
                await interaction.response.send_message(embed=_wolf_not_found_embed(player, wolf_name), ephemeral=reply_ephemeral())
                return
        else:
            wolf = db.get_user(player.id)
            if not wolf:
                embed = howlbert_embed('No Wolf', f'**{player.display_name}** has no active wolf.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        if image_url is None:
            db.set_wolf_identity(wolf['id'], ref_image_url=None)
            await interaction.response.send_message(embed=howlbert_embed('Ref Image Cleared', f"**{wolf['wolf_name']}** ({player.mention}) no longer has a reference image.", color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
            return
        if not image_url.lower().startswith(('http://', 'https://')):
            await interaction.response.send_message(embed=howlbert_embed('Bad URL', '`image_url` needs a direct http(s) image link.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.set_wolf_identity(wolf['id'], ref_image_url=image_url)
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        db.set_wolf_ref_image_cache(wolf['id'], await resp.read())
        except Exception:
            pass
        embed = howlbert_embed('Ref Image Set', f"**{wolf['wolf_name']}** ({player.mention}) now has a reference image. See `/profile`.", color=SUCCESS_COLOR)
        embed.set_thumbnail(url=image_url)
        await interaction.response.send_message(embed=embed)

    @wolfadmin.command(name='dormant', description="toggle a wolf's dormant flag (exempt from hunger/thirst/mood decay on /rollover).")
    @app_commands.describe(player='wolf owner', state='dormant (no decay) or active (normal decay)', wolf_name='which wolf (defaults to their active wolf)')
    @app_commands.choices(state=[app_commands.Choice(name='dormant', value='dormant'), app_commands.Choice(name='active', value='active')])
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_dormant(self, interaction: discord.Interaction, player: discord.User, state: app_commands.Choice[str], wolf_name: str | None=None):
        if not await self._require_admin(interaction):
            return
        wolf = _resolve_player_wolf(player, wolf_name)
        if not wolf:
            if wolf_name:
                await interaction.response.send_message(embed=_wolf_not_found_embed(player, wolf_name), ephemeral=reply_ephemeral())
            else:
                await interaction.response.send_message(embed=howlbert_embed('No Wolf', f'**{player.display_name}** has no active wolf.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        is_dormant = state.value == 'dormant'
        db.set_wolf_dormant(wolf['id'], is_dormant)
        note = 'exempt from hunger/thirst/mood decay on `/rollover` until set back to active.' if is_dormant else 'hungers, thirsts, and moods normally again on `/rollover`.'
        embed = howlbert_embed('wolf marked dormant' if is_dormant else 'wolf marked active', f"**{wolf['wolf_name']}** ({player.mention}); {note}", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @wolfadmin.command(name='execute', description='mark a wolf dead with a lore-flavored cause (admin; severe rp punishment).')
    @app_commands.describe(player='wolf owner', wolf_name='which wolf (defaults to their active wolf)', method='execution style (sets the cause text)', cause='custom cause text (used when method is custom)')
    @app_commands.choices(method=[app_commands.Choice(name="sog grave (mistmoor's pit of acidic water)", value='sog_grave'), app_commands.Choice(name='high ledge (greyspire; left to freeze)', value='high_ledge'), app_commands.Choice(name='custom cause', value='custom')])
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_execute(self, interaction: discord.Interaction, player: discord.User, method: app_commands.Choice[str], wolf_name: str | None=None, cause: str | None=None):
        if not await self._require_admin(interaction):
            return
        wolf = _resolve_player_wolf(player, wolf_name)
        if not wolf:
            if wolf_name:
                await interaction.response.send_message(embed=_wolf_not_found_embed(player, wolf_name), ephemeral=reply_ephemeral())
            else:
                await interaction.response.send_message(embed=howlbert_embed('No Wolf', f'**{player.display_name}** has no active wolf.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if wolf['condition'] in ('dead', 'dying'):
            await interaction.response.send_message(embed=howlbert_embed('already gone', f"**{wolf['wolf_name']}** is already {wolf['condition']}.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        cause_text = {
            'sog_grave': "lowered into the sog grave on a rope of twisted bark; the maw's digestion",
            'high_ledge': 'left on a high ledge to freeze, still alive, as the ravens came',
        }.get(method.value)
        if cause_text is None:
            cause_text = (cause or 'executed by pack law').strip()[:120]
        guild_id = interaction.guild.id if interaction.guild else None
        day = int(db.get_world(guild_id)['day_number']) if guild_id else None
        db.mark_wolf_dead(wolf['id'], cause_text, guild_id=guild_id, day=day)
        embed = howlbert_embed('wolf executed', f"**{wolf['wolf_name']}** ({player.mention}); {cause_text}.", color=SUCCESS_COLOR)
        embed.set_footer(text='/wolfadmin deaths shows the full log')
        await interaction.response.send_message(embed=embed)

    async def _resolve_pending_role_feature(self, interaction: discord.Interaction, *, request_id: int | None, player: discord.User | None, wolf_name: str | None) -> sqlite3.Row | None:
        if request_id is not None:
            row = db.get_pending_role_feature(request_id)
            if not row:
                embed = howlbert_embed('Not Found', f'No request with id `{request_id}`.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return None
            return row
        if player and wolf_name:
            wolf = db.find_user_wolf(player.id, wolf_name)
            if not wolf:
                await interaction.response.send_message(embed=_wolf_not_found_embed(player, wolf_name), ephemeral=reply_ephemeral())
                return None
            row = db.get_open_pending_for_wolf(wolf['id'])
            if not row:
                embed = howlbert_embed('No Pending Request', f"No open role-feature request for **{wolf['wolf_name']}**.", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return None
            return row
        embed = howlbert_embed('Missing Parameters', 'Provide **request_id** or both **player** and **wolf_name**.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return None

    @wolfadmin.command(name='featurepending', description='list open bonus role-feature requests awaiting approval.')
    async def wolfadmin_featurepending(self, interaction: discord.Interaction):
        if not await self._require_admin(interaction):
            return
        guild_id = interaction.guild.id if interaction.guild else 0
        rows = db.list_open_pending_role_features(guild_id)
        if not rows:
            embed = howlbert_embed('No Pending Requests', 'No role-feature requests are waiting for approval.', color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        lines = []
        for row in rows:
            role_key = row['role_feature']
            role_label = ROLE_LABELS.get(role_key, role_key.title())
            lines.append(f"`{row['id']}`; **{row['wolf_name']}** (<@{row['discord_id']}>); **{role_label}**")
        embed = howlbert_embed('Pending Role Features', '\n'.join(lines), color=SUCCESS_COLOR)
        embed.set_footer(text='approve with /wolfadmin approvefeature')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @wolfadmin.command(name='approvefeature', description='approve a pending bonus role-feature request (spends 10 xp).')
    @app_commands.describe(request_id='pending request id (from featurepending)', player='player who submitted the request', wolf_name='wolf that requested the feature')
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_approvefeature(self, interaction: discord.Interaction, request_id: int | None=None, player: discord.User | None=None, wolf_name: str | None=None):
        if not await self._require_admin(interaction):
            return
        row = await self._resolve_pending_role_feature(interaction, request_id=request_id, player=player, wolf_name=wolf_name)
        if not row:
            return
        if row['status'] != 'pending':
            embed = howlbert_embed('Not Pending', f"Request `{row['id']}` is already **{row['status']}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        role_key = row['role_feature']
        if role_key not in ROLE_FEATURES:
            embed = howlbert_embed('Invalid Role', f"Request `{row['id']}` references unknown role **{role_key}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        wolf = db.get_user_by_id(row['wolf_id'])
        if not wolf:
            embed = howlbert_embed('Wolf Missing', f"Wolf id `{row['wolf_id']}` no longer exists.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        existing_bonus = wolf['bonus_role_feature'] if 'bonus_role_feature' in wolf.keys() and wolf['bonus_role_feature'] else None
        if existing_bonus == role_key:
            db.set_pending_role_feature_status(row['id'], 'denied', resolved_by_discord_id=interaction.user.id)
            embed = howlbert_embed('Already Granted', f"**{wolf['wolf_name']}** already has this feature; request denied.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        account = db.get_account(row['discord_id'])
        xp_val = account['xp'] if 'xp' in account.keys() else 0
        if xp_val < XP_PER_ROLE_FEATURE:
            embed = howlbert_embed('Not Enough XP', f"<@{row['discord_id']}> only has **{xp_val}** XP (need {XP_PER_ROLE_FEATURE}).", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not db.spend_xp(row['discord_id'], XP_PER_ROLE_FEATURE):
            embed = howlbert_embed('Spend Failed', 'Could not deduct XP; request left pending.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        db.update_user(row['discord_id'], wolf_id=row['wolf_id'], bonus_role_feature=role_key)
        db.set_pending_role_feature_status(row['id'], 'approved', resolved_by_discord_id=interaction.user.id)
        role_label = ROLE_LABELS.get(role_key, role_key.title())
        embed = howlbert_embed('Feature Approved', f"**{wolf['wolf_name']}** gained **{role_label}** bonus feature ({XP_PER_ROLE_FEATURE} XP spent from <@{row['discord_id']}>).", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        await try_dm_user(self.bot, row['discord_id'], embed=howlbert_embed('Bonus Role Feature Approved', f"**{wolf['wolf_name']}** gained **{role_label}**:\n{ROLE_FEATURES[role_key]}", color=SUCCESS_COLOR))

    @wolfadmin.command(name='denyfeature', description='deny a pending bonus role-feature request (no xp spent).')
    @app_commands.describe(request_id='pending request id (from featurepending)', player='player who submitted the request', wolf_name='wolf that requested the feature')
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_denyfeature(self, interaction: discord.Interaction, request_id: int | None=None, player: discord.User | None=None, wolf_name: str | None=None):
        if not await self._require_admin(interaction):
            return
        row = await self._resolve_pending_role_feature(interaction, request_id=request_id, player=player, wolf_name=wolf_name)
        if not row:
            return
        if row['status'] != 'pending':
            embed = howlbert_embed('Not Pending', f"Request `{row['id']}` is already **{row['status']}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        db.set_pending_role_feature_status(row['id'], 'denied', resolved_by_discord_id=interaction.user.id)
        role_label = ROLE_LABELS.get(row['role_feature'], row['role_feature'].title())
        embed = howlbert_embed('Feature Denied', f"Denied **{role_label}** for **{row['wolf_name']}** (<@{row['discord_id']}>, id `{row['id']}`). No XP spent.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @wolfadmin.command(name='proxy', description="set up a player's proxy tags or autoproxy (admin).")
    @app_commands.describe(player='wolf owner', action='set tag, clear tag, list proxies, or toggle autoproxy', tag='tag template for set (e.g. h:text or [text])', wolf_name='which wolf (defaults to their active wolf)', mode='for autoproxy: on or off')
    @app_commands.choices(action=[app_commands.Choice(name='set tag', value='set'), app_commands.Choice(name='clear tag', value='clear'), app_commands.Choice(name='list', value='list'), app_commands.Choice(name='autoproxy', value='autoproxy')], mode=[app_commands.Choice(name='on', value='on'), app_commands.Choice(name='off', value='off')])
    @app_commands.autocomplete(wolf_name=_wolfadmin_wolf_autocomplete)
    async def wolfadmin_proxy(self, interaction: discord.Interaction, player: discord.User, action: app_commands.Choice[str], tag: str | None=None, wolf_name: str | None=None, mode: app_commands.Choice[str] | None=None):
        if not await self._require_admin(interaction):
            return
        if player.bot:
            await interaction.response.send_message(embed=howlbert_embed('Invalid Player', 'Bots cannot own wolves.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if action.value == 'list':
            wolves = db.list_user_wolves(player.id)
            if not wolves:
                await interaction.response.send_message(embed=howlbert_embed('No Wolves', f'**{player.display_name}** has no registered wolves.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            auto_id = db.get_autoproxy_wolf_id(player.id)
            lines = []
            for w in wolves:
                prefix = w['proxy_prefix'] or ''
                suffix = w['proxy_suffix'] or ''
                tag_label = f'`{prefix}text{suffix}`' if prefix or suffix else '_no tag_'
                star = ' ⭐ autoproxy' if auto_id == w['id'] else ''
                av = ' 🖼️' if w['avatar_url'] else ''
                lines.append(f"**{w['wolf_name']}**; {tag_label}{av}{star}")
            embed = howlbert_embed(f'Proxies; {player.display_name}', '\n'.join(lines), color=SUCCESS_COLOR)
            embed.set_footer(text='player uses /proxy avatar for crop · /proxy import for tupperbox')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        wolf = _resolve_player_wolf(player, wolf_name)
        if not wolf:
            if wolf_name:
                await interaction.response.send_message(embed=_wolf_not_found_embed(player, wolf_name), ephemeral=reply_ephemeral())
            else:
                await interaction.response.send_message(embed=howlbert_embed('No Wolf', f'**{player.display_name}** has no active wolf.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if action.value == 'set':
            if not tag:
                await interaction.response.send_message(embed=howlbert_embed('Need Tag', 'Give a `tag` like `H:text` or `[text]` (use `text` as the placeholder).', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            prefix, suffix = parse_bracket_string(tag)
            if not prefix and (not suffix):
                await interaction.response.send_message(embed=howlbert_embed('Bad Tag', 'Use `text` as the placeholder, e.g. `H:text` or `[text]`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            db.set_wolf_proxy(wolf['id'], prefix, suffix)
            example = f"{prefix or ''}hello{suffix or ''}"
            embed = howlbert_embed('Proxy Tag Set', f"**{wolf['wolf_name']}** ({player.mention}) will speak when they type `{example}`.\nThey can set an avatar with `/proxy avatar`.", color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if action.value == 'clear':
            db.clear_wolf_proxy(wolf['id'])
            if db.get_autoproxy_wolf_id(player.id) == wolf['id']:
                db.set_autoproxy_wolf(player.id, None)
            await interaction.response.send_message(embed=howlbert_embed('Proxy Cleared', f"Removed the proxy tag on **{wolf['wolf_name']}** ({player.mention}).", color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
            return
        if not mode:
            await interaction.response.send_message(embed=howlbert_embed('Pick Mode', 'Choose `mode:on` or `mode:off` for autoproxy.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if mode.value == 'off':
            db.set_autoproxy_wolf(player.id, None)
            await interaction.response.send_message(embed=howlbert_embed('Autoproxy Off', f'Untagged messages from **{player.display_name}** stay as them.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
            return
        db.set_autoproxy_wolf(player.id, wolf['id'])
        await interaction.response.send_message(embed=howlbert_embed('Autoproxy On', f"**{player.display_name}**'s untagged messages now post as **{wolf['wolf_name']}**. They can escape once with `\\` at the start of a message.", color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @wolfadmin.command(name='deaths', description='death log: recent deaths and current dead wolves with causes.')
    @app_commands.describe(player="filter to one player's wolves (optional)", limit='how many log entries to show (default 20, max 50)')
    async def wolfadmin_deaths(self, interaction: discord.Interaction, player: discord.User | None=None, limit: app_commands.Range[int, 1, 50]=20):
        if not await self._require_admin(interaction):
            return
        guild_id = interaction.guild.id if interaction.guild else None
        discord_id = player.id if player else None
        current = db.list_current_dead_wolves(guild_id=guild_id, discord_id=discord_id)
        log_rows = db.list_death_log(guild_id=guild_id, discord_id=discord_id, limit=limit)
        sections: list[str] = []
        if current:
            lines = []
            for row in current:
                cause = row['cause_of_death'] or 'unknown'
                day = row['death_day']
                day_bit = f' · day **{day}**' if day else ''
                lines.append(f"**{row['wolf_name']}** (<@{row['discord_id']}>); {cause}{day_bit}")
            sections.append('**Currently dead**\n' + '\n'.join(lines))
        else:
            sections.append('_No wolves are dead right now._')
        if log_rows:
            log_lines = []
            for row in log_rows:
                day = row['day']
                day_bit = f'day **{day}** · ' if day else ''
                log_lines.append(f"`#{row['id']}` {day_bit}**{row['wolf_name']}** (<@{row['discord_id']}>); {row['cause']}")
            sections.append('**Death log**\n' + '\n'.join(log_lines))
        else:
            sections.append('_Death log is empty._')
        title = 'Death Log'
        if player:
            title = f'Death Log; {player.display_name}'
        embed = howlbert_embed(title, '\n\n'.join(sections), color=SUCCESS_COLOR)
        embed.set_footer(text='cause is recorded permanently at death.')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

async def setup(bot: commands.Bot):
    await bot.add_cog(WolfAdmin(bot))