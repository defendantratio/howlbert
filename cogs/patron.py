"""Discord events for invite tracking and server boost rewards."""
from __future__ import annotations
import logging
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.kickstarter import grant_tier2_rewards, kickstarter_badge_text
from engine.patron import grant_first_boost, grant_second_boost, patron_status_lines, record_invite_join, referral_leaderboard_lines
from engine.donor import apply_donation_grant, create_donation_code, donor_status_lines, redeem_code
from engine.kofi_shop import fulfill_shop_order, list_pending_shop_orders
from engine.kofi_webhook import start_kofi_webhook, stop_kofi_webhook
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message
from utils.permissions import is_howlbert_admin
logger = logging.getLogger('howlbert.patron')

class Patron(commands.Cog):
    patronadmin = app_commands.Group(name='patronadmin', description='admin; donation codes and manual grants.')
    kickstarter = app_commands.Group(name='kickstarter', description='admin; kickstarter backer badge and tier 2 fulfillment.', parent=patronadmin)

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._invite_cache: dict[int, dict[str, tuple[int, int | None]]] = {}

    async def cog_load(self):
        for guild in self.bot.guilds:
            await self._refresh_invites(guild)
        await start_kofi_webhook(self.bot)

    async def cog_unload(self):
        await stop_kofi_webhook()

    async def _require_admin(self, interaction: discord.Interaction) -> bool:
        if is_howlbert_admin(interaction):
            return True
        await interaction.response.send_message(embed=howlbert_embed('Denied', 'Admins only.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
        return False

    async def _refresh_invites(self, guild: discord.Guild) -> None:
        try:
            invites = await guild.invites()
            self._invite_cache[guild.id] = {inv.code: (inv.uses or 0, inv.inviter.id if inv.inviter else None) for inv in invites}
        except discord.Forbidden:
            self._invite_cache[guild.id] = {}
            logger.warning('No Manage Server permission to track invites in guild %s', guild.id)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        cache = self._invite_cache.setdefault(invite.guild.id, {})
        cache[invite.code] = (invite.uses or 0, invite.inviter.id if invite.inviter else None)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        cache = self._invite_cache.get(invite.guild.id, {})
        cache.pop(invite.code, None)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        try:
            invites = await guild.invites()
        except discord.Forbidden:
            return
        old = self._invite_cache.get(guild.id, {})
        inviter_id = None
        for inv in invites:
            prev_uses, _ = old.get(inv.code, (0, None))
            if (inv.uses or 0) > prev_uses:
                inviter_id = inv.inviter.id if inv.inviter else None
                break
        self._invite_cache[guild.id] = {inv.code: (inv.uses or 0, inv.inviter.id if inv.inviter else None) for inv in invites}
        if not inviter_id or inviter_id == member.id:
            return
        world = db.get_world(guild.id)
        day = world['day_number'] if world else 1
        record_invite_join(guild.id, member.id, inviter_id, day)
        logger.info('Invite tracked: %s invited %s to guild %s', inviter_id, member.id, guild.id)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.premium_since is None and after.premium_since is not None:
            note = grant_first_boost(after.id)
            if note:
                logger.info('First boost reward for %s: %s', after.id, note)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.type is not discord.MessageType.premium_guild_subscription:
            return
        if not message.guild or not message.author:
            return
        count = 1
        if message.content and str(message.content).isdigit():
            count = int(message.content)
        if count >= 2:
            note = grant_second_boost(message.author.id)
            if note:
                logger.info('Second boost reward for %s', message.author.id)

    @app_commands.command(name='patron', description='view invite & server boost rewards (booster perks are yours only).')
    async def patron_status(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        is_boosting = bool(interaction.user and isinstance(interaction.user, discord.Member) and interaction.user.premium_since)
        lines = patron_status_lines(interaction.user.id, is_boosting=is_boosting)
        lines.extend(donor_status_lines(interaction.user.id))
        embed = howlbert_embed('Patron & Invites', '\n'.join(lines), color=SUCCESS_COLOR)
        embed.set_footer(text='/redeem · ko-fi shop orders may need `/register` + discord id in the message')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @app_commands.command(name='referrals', description='see who brought the most wolves home to the den.')
    async def referral_leaderboard(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        lines = referral_leaderboard_lines(interaction.guild.id)
        embed = howlbert_embed('Den Builders', '\n'.join(lines), color=SUCCESS_COLOR)
        from config import INVITE_REFERRAL_ROLLOVERS
        embed.set_footer(text=f'invite a friend; welcome bones + a referrer payout after {INVITE_REFERRAL_ROLLOVERS} sunrises · `/patron` for your own totals')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='redeem', description='redeem a one-time donation or gift code.')
    @app_commands.describe(code='code from ko-fi, patreon, or an admin')
    async def redeem(self, interaction: discord.Interaction, code: str):
        ok, note = redeem_code(interaction.user.id, code)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = 'Code Redeemed' if ok else 'Redeem Failed'
        await interaction.response.send_message(embed=howlbert_embed(title, note, color=color), ephemeral=reply_ephemeral())

    @patronadmin.command(name='code', description='create a one-time or limited-use redeem code.')
    @app_commands.describe(bones='bones granted on redeem', max_uses='how many total redemptions (default 1)', tier='optional donor tier label: friend, benefactor, legend', mood='optional mood bonus', standing='optional standing bonus', supporter_days='days of +3 /bones action:daily supporter perk', note='internal note for this code')
    @app_commands.choices(tier=[app_commands.Choice(name='none', value=''), app_commands.Choice(name='den friend', value='friend'), app_commands.Choice(name='pack benefactor', value='benefactor'), app_commands.Choice(name='legend of the den', value='legend')])
    async def patronadmin_code(self, interaction: discord.Interaction, bones: app_commands.Range[int, 0, 5000], max_uses: app_commands.Range[int, 1, 100]=1, tier: app_commands.Choice[str] | None=None, mood: app_commands.Range[int, 0, 50]=0, standing: app_commands.Range[int, 0, 20]=0, supporter_days: app_commands.Range[int, 0, 365]=0, note: str=''):
        if not await self._require_admin(interaction):
            return
        tier_val = tier.value if tier else ''
        code = create_donation_code(bones=bones, donor_tier=tier_val, mood_bonus=mood, standing_bonus=standing, daily_bonus_days=supporter_days, max_uses=max_uses, note=note)
        await interaction.response.send_message(embed=howlbert_embed('Donation Code Created', f'**`{code}`**\n**{bones}** bones · max uses **{max_uses}**' + (f' · tier **{tier_val}**' if tier_val else '') + (f' · **{supporter_days}** supporter days' if supporter_days else ''), color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @patronadmin.command(name='grant', description='manually grant donor rewards to a player.')
    @app_commands.describe(player='discord member', bones='bones to grant', tier='optional donor tier', supporter_days='days of +3 /bones action:daily supporter perk')
    @app_commands.choices(tier=[app_commands.Choice(name='none', value=''), app_commands.Choice(name='den friend', value='friend'), app_commands.Choice(name='pack benefactor', value='benefactor'), app_commands.Choice(name='legend of the den', value='legend')])
    async def patronadmin_grant(self, interaction: discord.Interaction, player: discord.Member, bones: app_commands.Range[int, 0, 5000], tier: app_commands.Choice[str] | None=None, supporter_days: app_commands.Range[int, 0, 365]=0):
        if not await self._require_admin(interaction):
            return
        ok, note = apply_donation_grant(player.id, bones=bones, tier=tier.value if tier else '', supporter_days=supporter_days, count_toward_monthly_cap=False)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = 'Grant Applied' if ok else 'Grant Failed'
        await interaction.response.send_message(embed=howlbert_embed(title, f'{player.mention}: {note}', color=color), ephemeral=reply_ephemeral())

    async def _item_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        items = db.get_all_items()
        choices = []
        for row in items:
            if current and current.lower() not in row['key'] and current.lower() not in row['name'].lower():
                continue
            choices.append(app_commands.Choice(name=f"{row['name']} ({row['key']})", value=row['key']))
        return choices[:25]

    @patronadmin.command(name='item', description='manually grant any item (e.g. a chosen herb for a herb satchel order) to a player.')
    @app_commands.describe(player='discord member', item='item key, e.g. herb_yarrow', quantity='how many to grant')
    @app_commands.autocomplete(item=_item_autocomplete)
    async def patronadmin_item(self, interaction: discord.Interaction, player: discord.Member, item: str, quantity: app_commands.Range[int, 1, 20]=1):
        if not await self._require_admin(interaction):
            return
        if not db.get_user(player.id):
            await interaction.response.send_message(embed=howlbert_embed('No Wolf', f'{player.display_name} must `/register` before an item grant.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        item_row = db.get_item_by_key(item.strip().lower())
        if not item_row:
            await interaction.response.send_message(embed=howlbert_embed('Unknown Item', f'no item with key `{item}`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.grant_item(player.id, item_row['id'], quantity)
        await interaction.response.send_message(embed=howlbert_embed('Item Granted', f"{player.mention}: **{quantity}x {item_row['name']}** added to `/bones action:inventory`.", color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @patronadmin.command(name='spotlight', description='post this week\'s "wolf of the week" pick to this channel.')
    async def patronadmin_spotlight(self, interaction: discord.Interaction):
        if not await self._require_admin(interaction):
            return
        if not interaction.guild:
            await interaction.response.send_message(embed=howlbert_embed('Server Only', 'use this in a server.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        if not world:
            await interaction.response.send_message(embed=howlbert_embed('No World', 'run `/rollover` at least once first.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.spotlight import pick_wolf_of_the_week, format_spotlight_post
        pick = pick_wolf_of_the_week(interaction.guild.id, world['day_number'])
        if not pick:
            await interaction.response.send_message(embed=howlbert_embed('No Spotlight Yet', 'nothing noteworthy logged in the den journal this week; try again after more play.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        await interaction.response.send_message(embed=howlbert_embed('🐾 Wolf of the Week', format_spotlight_post(pick), color=SUCCESS_COLOR))

    @patronadmin.command(name='quietwolves', description='list players whose wolves have gone quiet (for a manual re-engagement dm).')
    @app_commands.describe(days='no tracked activity in this many sunrises (default 5)')
    async def patronadmin_quietwolves(self, interaction: discord.Interaction, days: app_commands.Range[int, 1, 60] = 5):
        if not await self._require_admin(interaction):
            return
        from config import QUIETWOLVES_COMMAND_ENABLED
        if not QUIETWOLVES_COMMAND_ENABLED:
            await interaction.response.send_message(embed=howlbert_embed('Dormant For Now', 'this command is intentionally turned off (`QUIETWOLVES_COMMAND_ENABLED` in config.py); a past activity-reminder dm landed poorly with the community, so this is waiting on player feedback before it goes live. flip the flag when ready.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(embed=howlbert_embed('Server Only', 'use this in a server.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(interaction.guild.id)
        if not world:
            await interaction.response.send_message(embed=howlbert_embed('No World', 'run `/rollover` at least once first.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.reengagement import find_quiet_wolves
        quiet = find_quiet_wolves(world['day_number'], threshold_days=days)
        if not quiet:
            await interaction.response.send_message(embed=howlbert_embed('Quiet Wolves', f'nobody has gone quiet for **{days}+** sunrises. den is active.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
            return
        lines = [f"<@{w['discord_id']}> — **{w['wolf_name']}**; quiet **{w['days_quiet']}** sunrises" for w in quiet[:25]]
        embed = howlbert_embed('Quiet Wolves', '\n'.join(lines), color=SUCCESS_COLOR)
        embed.set_footer(text='a friendly manual dm to a few of these goes a long way; docs/GROWTH_IDEAS.md section 18')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @kickstarter.command(name='grant', description='grant the permanent kickstarter backer badge.')
    @app_commands.describe(player='discord member who backed tier 2+')
    async def kickstarter_grant_badge(self, interaction: discord.Interaction, player: discord.Member):
        if not await self._require_admin(interaction):
            return
        if not db.get_user(player.id):
            await interaction.response.send_message(embed=howlbert_embed('No Wolf', f'{player.display_name} must `/register` before the badge is granted.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if db.grant_kickstarter_backer(player.id):
            note = f'{kickstarter_badge_text()}; visible on `/patron` and `/profile`.'
        else:
            note = f'{kickstarter_badge_text()} was already granted.'
        await interaction.response.send_message(embed=howlbert_embed('Kickstarter Backer', f'{player.mention}: {note}', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @kickstarter.command(name='tier2', description='fulfill tier 2 (bone pouch backer): badge, 75 bones, one bonus item.')
    @app_commands.describe(player='discord member', bonus_item='lucky tooth, den charm, or herb bundle')
    @app_commands.choices(bonus_item=[app_commands.Choice(name='lucky tooth', value='lucky_tooth'), app_commands.Choice(name='den charm', value='den_charm'), app_commands.Choice(name='herb bundle', value='herb_bundle')])
    async def kickstarter_tier2(self, interaction: discord.Interaction, player: discord.Member, bonus_item: app_commands.Choice[str]):
        if not await self._require_admin(interaction):
            return
        ok, note = grant_tier2_rewards(player.id, bonus_item=bonus_item.value)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        title = 'Tier 2 Fulfilled' if ok else 'Tier 2 Failed'
        await interaction.response.send_message(embed=howlbert_embed(title, f'{player.mention}: {note}', color=color), ephemeral=reply_ephemeral())

    @kickstarter.command(name='revoke', description='remove the kickstarter backer badge.')
    @app_commands.describe(player='discord member')
    async def kickstarter_revoke(self, interaction: discord.Interaction, player: discord.Member):
        if not await self._require_admin(interaction):
            return
        if db.revoke_kickstarter_backer(player.id):
            note = 'Kickstarter backer badge removed.'
        else:
            note = 'That player did not have the badge.'
        await interaction.response.send_message(embed=howlbert_embed('Kickstarter Backer', f'{player.mention}: {note}', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @patronadmin.command(name='orders', description='list pending ko-fi shop orders to fulfill.')
    async def patronadmin_orders(self, interaction: discord.Interaction):
        if not await self._require_admin(interaction):
            return
        rows = list_pending_shop_orders(limit=15)
        if not rows:
            await interaction.response.send_message(embed=howlbert_embed('Shop Orders', 'No pending orders.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
            return
        lines = []
        for row in rows:
            who = f"<@{row['discord_id']}>" if row['discord_id'] else row['email'] or '-'
            line = f"**#{row['id']}**; **{row['product_label']}** · {who} · ${int(row['amount_cents']) / 100:.2f} · {row['created_at'][:10]}"
            if row['notes']:
                line += f"\n> {row['notes'][:200]}"
            lines.append(line)
        await interaction.response.send_message(embed=howlbert_embed('Pending Shop Orders', '\n'.join(lines) + '\n\nMark done with `/patronadmin fulfill`.', color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

    @patronadmin.command(name='fulfill', description='mark a ko-fi shop order as fulfilled.')
    @app_commands.describe(order_id='order id from /patronadmin orders', notes='optional note')
    async def patronadmin_fulfill(self, interaction: discord.Interaction, order_id: app_commands.Range[int, 1, 999999], notes: str=''):
        if not await self._require_admin(interaction):
            return
        ok, note = fulfill_shop_order(order_id, notes=notes)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        await interaction.response.send_message(embed=howlbert_embed('Shop Fulfillment', note, color=color), ephemeral=reply_ephemeral())

async def setup(bot: commands.Bot):
    await bot.add_cog(Patron(bot))