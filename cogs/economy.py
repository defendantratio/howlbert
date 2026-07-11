import discord
from discord import app_commands
from discord.ext import commands
import database as db
from config import CURRENCY_LABEL
from engine.activities import try_daily, try_hunt, try_work
from engine.shop_items import RABBIT_PELT_GIFT_BONES, RABBIT_PELT_STANDING, USABLE_ITEM_KEYS
from utils.currency import format_bones
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label
from utils.wolf_autocomplete import make_member_wolf_autocomplete
from engine.trade import build_trade_embed
from utils.trade_views import TRADE_DYNAMIC_ITEMS, make_trade_view
from utils.views import build_shop_embed, make_hunt_followup_view, make_shop_view
from utils.combat_views import make_combat_view

_wolf_name_autocomplete = make_member_wolf_autocomplete("wolf")

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

async def _hunt_territory_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if not interaction.guild:
        return []
    territories = db.get_territories(interaction.guild.id)
    choices = []
    for t in territories:
        label = f"{t['name']} ({t['key']})"
        if current and current.lower() not in label.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(label), value=t['key']))
    return choices[:25]

def _resolve_own_wolf(discord_id: int, name: str):
    rows = db.list_user_wolves(discord_id)
    return next((w for w in rows if w['wolf_name'].lower() == name.strip().lower()), None)

def _resolve_gift_recipient(interaction: discord.Interaction, user, wolf: discord.Member | None, own_wolf: str | None, wolf_name: str | None = None) -> tuple[object | None, str | None]:
    if wolf and own_wolf:
        return (None, 'Pick either another **player** or `own_wolf`; not both.')
    if own_wolf:
        recipient = _resolve_own_wolf(interaction.user.id, own_wolf)
        if not recipient:
            return (None, 'No wolf with that name on your account. Check `/wolves`.')
        if recipient['id'] == user['id']:
            return (None, 'Switch to another wolf with `/switchwolf`, or pick a different `own_wolf`.')
        return (recipient, None)
    if wolf:
        if wolf.bot or wolf.id == interaction.user.id:
            return (None, 'Use another **player**, or your other wolf via `own_wolf`.')
        if wolf_name:
            recipient = db.find_user_wolf(wolf.id, wolf_name)
        else:
            recipient = db.get_user(wolf.id)
        if not recipient:
            return (None, f"{wolf.display_name} hasn't registered a wolf yet.")
        return (recipient, None)
    return (None, 'Pick another **player** or one of your wolves with `own_wolf`.')


class Economy(commands.Cog):
    trade = app_commands.Group(name='trade', description='offer items and bones to another wolf (they must accept).')

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.add_dynamic_items(*TRADE_DYNAMIC_ITEMS)

    async def _require_registered(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed('Not Registered', 'Use `/register` before using economy commands.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return None
        return user

    def _require_guild(self, interaction: discord.Interaction) -> int | None:
        if interaction.guild:
            return interaction.guild.id
        return None

    async def _inventory_item_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        items = db.get_inventory(interaction.user.id)
        choices = []
        for row in items:
            if current and current.lower() not in row['key'] and (current.lower() not in row['name'].lower()):
                continue
            choices.append(app_commands.Choice(name=choice_label(f"{row['name']} x{row['quantity']} ({row['key']})"), value=row['key']))
        return choices[:25]

    async def _all_item_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        items = db.get_all_items()
        choices = []
        for row in items:
            if current and current.lower() not in row['key'] and (current.lower() not in row['name'].lower()):
                continue
            choices.append(app_commands.Choice(name=choice_label(f"{row['name']} ({row['key']})"), value=row['key']))
        return choices[:25]

    @app_commands.command(name='bones', description='balance, daily, hunt, shop, inventory, work, give, and more.')
    @app_commands.describe(action='see dropdown for the full action list', amount='bones amount (give)', wolf='recipient player (give / giveitem / use)', wolf_name="specific wolf from that player's roster (give/giveitem)", own_wolf='your other wolf (give / giveitem / use)', item='item key (giveitem/buy/sell/use)', quantity='item quantity', collaborate='call a pack hunt (hunt only; same great pack joins via buttons)', territory='territory to hunt in (hunt only; boosts home turf/ally bonuses on that ground)', scene='optional rp scene note (work only)', staff='flag for staff to weave your rp scene (work only)')
    @app_commands.choices(action=[app_commands.Choice(name='balance', value='balance'), app_commands.Choice(name='daily stipend', value='daily'), app_commands.Choice(name='hunt for bones', value='hunt'), app_commands.Choice(name='pray before hunt', value='pray'), app_commands.Choice(name='give bones', value='give'), app_commands.Choice(name='give item', value='giveitem'), app_commands.Choice(name='leaderboard', value='leaderboard'), app_commands.Choice(name='work', value='work'), app_commands.Choice(name='shop', value='shop'), app_commands.Choice(name='buy item', value='buy'), app_commands.Choice(name='sell item', value='sell'), app_commands.Choice(name='inventory', value='inventory'), app_commands.Choice(name='use item', value='use')])
    @app_commands.autocomplete(item=_inventory_item_autocomplete, own_wolf=_other_wolf_autocomplete, territory=_hunt_territory_autocomplete, wolf_name=_wolf_name_autocomplete)
    async def bones(self, interaction: discord.Interaction, action: str, amount: int | None=None, wolf: discord.Member | None=None, wolf_name: str | None=None, own_wolf: str | None=None, item: str | None=None, quantity: int=1, collaborate: bool=False, territory: str | None=None, scene: str | None=None, staff: bool=False):
        if action == 'balance':
            await self._balance(interaction)
        elif action == 'daily':
            await self._daily(interaction)
        elif action == 'hunt':
            if collaborate:
                from cogs.collab_hunt import post_collab_hunt_call
                await post_collab_hunt_call(interaction, self.bot)
            else:
                await self._hunt(interaction, territory=territory)
        elif action == 'pray':
            await self._pray(interaction)
        elif action == 'give':
            if amount is None:
                await interaction.response.send_message(player_message('Provide `amount`.'), ephemeral=reply_ephemeral())
                return
            await self._give(interaction, amount, wolf, own_wolf, wolf_name=wolf_name)
        elif action == 'giveitem':
            if not item:
                await interaction.response.send_message(player_message('Provide `item`.'), ephemeral=reply_ephemeral())
                return
            await self._giveitem(interaction, item, wolf, own_wolf, quantity, wolf_name=wolf_name)
        elif action == 'leaderboard':
            await self._leaderboard(interaction)
        elif action == 'work':
            await self._work(interaction, scene=scene, staff=staff)
        elif action == 'shop':
            await self._shop(interaction)
        elif action == 'buy':
            if not item:
                await interaction.response.send_message(player_message('Provide `item`.'), ephemeral=reply_ephemeral())
                return
            await self._buy(interaction, item, quantity)
        elif action == 'sell':
            if not item:
                await interaction.response.send_message(player_message('Provide `item`.'), ephemeral=reply_ephemeral())
                return
            await self._sell(interaction, item, quantity)
        elif action == 'inventory':
            await self._inventory(interaction)
        elif action == 'use':
            if not item:
                await interaction.response.send_message(player_message('Provide `item`.'), ephemeral=reply_ephemeral())
                return
            await self._use(interaction, item, wolf, own_wolf)

    async def _balance(self, interaction: discord.Interaction):
        user = await self._require_registered(interaction)
        if not user:
            return
        embed = howlbert_embed('Your Stores', color=SUCCESS_COLOR)
        embed.add_field(name=CURRENCY_LABEL, value=format_bones(user['bones']), inline=False)
        embed.set_footer(text='/bones action:hunt · action:work · /checklist')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _daily(self, interaction: discord.Interaction):
        embed = try_daily(interaction)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _hunt(self, interaction: discord.Interaction, territory: str | None=None):
        if not interaction.guild:
            await interaction.response.send_message(embed=howlbert_embed('Server Only', 'Hunt in a server channel.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        await interaction.response.defer(thinking=False)
        embed, show_prey, combat_enc = try_hunt(interaction, territory=territory)
        if not embed:
            await interaction.followup.send(embed=howlbert_embed('Hunt Failed', 'Something went wrong.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if combat_enc:
            view = make_combat_view(combat_enc, self.bot)
            if not view:
                db.rebuild_encounter_initiative(combat_enc)
                view = make_combat_view(combat_enc, self.bot)
            if not view:
                embed.description = (embed.description or '') + f'\n\n_Combat panel failed to attach; use `/combat status encounter:{combat_enc}` or `/combat attack encounter:{combat_enc}` on your turn._'
                await interaction.followup.send(embed=embed)
                return
            await interaction.followup.send(embed=embed, view=view)
            return
        if show_prey and embed.color != ERROR_COLOR:
            await interaction.followup.send(embed=embed, view=make_hunt_followup_view())
        else:
            await interaction.followup.send(embed=embed)

    async def _pray(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(embed=howlbert_embed('Server Only', 'Pray in a server channel.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        user = await self._require_registered(interaction)
        if not user:
            return
        world = db.get_world(interaction.guild.id)
        from engine.hunt_prayer import try_hunt_prayer
        embed = try_hunt_prayer(interaction.user.id, user, world['day_number'])
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _give(self, interaction: discord.Interaction, amount: int, wolf: discord.Member | None=None, own_wolf: str | None=None, *, wolf_name: str | None=None):
        user = await self._require_registered(interaction)
        if not user:
            return
        recipient, err = _resolve_gift_recipient(interaction, user, wolf, own_wolf, wolf_name)
        if err:
            embed = howlbert_embed('Invalid Target', err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if amount <= 0:
            embed = howlbert_embed('Invalid Amount', 'Give at least 1 bone.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if user['bones'] < amount:
            embed = howlbert_embed('Not Enough Bones', 'Your stash is too light.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not db.transfer_bones_by_wolf_id(user['id'], recipient['id'], amount):
            embed = howlbert_embed('Transfer Failed', 'Could not move bones to that wolf.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Bones Gifted', color=SUCCESS_COLOR)
        embed.add_field(name='To', value=recipient['wolf_name'], inline=True)
        embed.add_field(name='Amount', value=format_bones(amount), inline=True)
        embed.set_footer(text='/bones action:balance · /trade offer')
        await interaction.response.send_message(embed=embed)

    async def _giveitem(self, interaction: discord.Interaction, item: str, wolf: discord.Member | None=None, own_wolf: str | None=None, quantity: int=1, *, wolf_name: str | None=None):
        user = await self._require_registered(interaction)
        if not user:
            return
        recipient, err = _resolve_gift_recipient(interaction, user, wolf, own_wolf, wolf_name)
        if err:
            embed = howlbert_embed('Invalid Target', err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if quantity <= 0:
            embed = howlbert_embed('Invalid Quantity', 'Give at least 1.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        shop_item = db.get_item_by_key(item.strip())
        if not shop_item:
            embed = howlbert_embed('Unknown Item', 'Check `/bones action:inventory` for valid keys.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        owned = db.get_inventory_quantity(interaction.user.id, shop_item['id'])
        if owned < quantity:
            embed = howlbert_embed('Not Enough', f"You only carry **{owned}**; can't give **{quantity}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not db.transfer_item_by_wolf_id(user['id'], recipient['id'], shop_item['id'], quantity):
            embed = howlbert_embed('Transfer Failed', 'Could not move that item to the recipient.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Item Gifted', color=SUCCESS_COLOR)
        embed.add_field(name='To', value=recipient['wolf_name'], inline=True)
        embed.add_field(name='Item', value=f"{shop_item['name']} x{quantity}", inline=True)
        await interaction.response.send_message(embed=embed)

    @trade.command(name='offer', description='propose a trade; items and/or bones.')
    @app_commands.describe(wolf='wolf to trade with', wolf_name="specific wolf from that player's roster", offer_item='item you give (key from `/bones action:inventory`)', offer_quantity='how many you give (default 1)', offer_bones='bones you give (default 0)', for_item='item you want from them (optional)', for_quantity='how many you want (default 1)', for_bones='bones you want from them (default 0)')
    @app_commands.autocomplete(offer_item=_inventory_item_autocomplete, for_item=_all_item_autocomplete, wolf_name=_wolf_name_autocomplete)
    async def trade_offer(self, interaction: discord.Interaction, wolf: discord.Member, wolf_name: str | None=None, offer_item: str | None=None, offer_quantity: int=1, offer_bones: int=0, for_item: str | None=None, for_quantity: int=1, for_bones: int=0):
        user = await self._require_registered(interaction)
        if not user:
            return
        if wolf.bot or wolf.id == interaction.user.id:
            embed = howlbert_embed('Invalid Target', 'Choose another wolf.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if wolf_name:
            target = db.find_user_wolf(wolf.id, wolf_name)
        else:
            target = db.get_user(wolf.id)
        if not target:
            embed = howlbert_embed('Not Registered', f"{wolf.display_name} hasn't registered a wolf yet.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if offer_bones < 0 or for_bones < 0:
            embed = howlbert_embed('Invalid Amount', "Bones can't be negative.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        offer_row = db.get_item_by_key(offer_item.strip()) if offer_item else None
        if offer_item and (not offer_row):
            embed = howlbert_embed('Unknown Item', 'Check `/bones action:inventory` for your offer item.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        want_row = db.get_item_by_key(for_item.strip()) if for_item else None
        if for_item and (not want_row):
            embed = howlbert_embed('Unknown Item', 'Check item keys with `/bones action:inventory`.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        gives_item = offer_row is not None and offer_quantity > 0
        if not gives_item and offer_bones <= 0:
            embed = howlbert_embed('Nothing Offered', 'Include an `offer_item` and/or `offer_bones` greater than 0.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if offer_row and offer_quantity <= 0:
            embed = howlbert_embed('Invalid Quantity', 'Offer quantity must be at least 1.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if want_row and for_quantity <= 0:
            embed = howlbert_embed('Invalid Quantity', 'Requested quantity must be at least 1.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if offer_row:
            owned = db.get_inventory_quantity(interaction.user.id, offer_row['id'])
            if owned < offer_quantity:
                embed = howlbert_embed('Not Enough', f'You only carry **{owned}** of that item.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
        if offer_bones > 0 and user['bones'] < offer_bones:
            embed = howlbert_embed('Not Enough Bones', 'Your stash is too light.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        trade_id = db.create_pending_trade(interaction.user.id, wolf.id, from_item_id=offer_row['id'] if offer_row else None, from_item_qty=offer_quantity if offer_row else 0, from_bones=offer_bones, to_item_id=want_row['id'] if want_row else None, to_item_qty=for_quantity if want_row else 0, to_bones=for_bones)
        if not trade_id:
            embed = howlbert_embed('Trade Failed', 'That trade could not be completed.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        trade = db.get_pending_trade(trade_id)
        embed = build_trade_embed(trade)
        embed.description = f'{wolf.mention}; accept or decline below. Offer expires in 10 minutes.'
        view = make_trade_view(trade_id)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        db.set_pending_trade_message_id(trade_id, msg.id)

    @trade.command(name='duplicates', description='give all duplicate hoard items to another wolf (unlimited; cross-pack standing once a sunrise).')
    @app_commands.describe(wolf='wolf to receive extras (keeps one of each type for you)', wolf_name="specific wolf from that player's roster", own_wolf='your other wolf to receive extras')
    @app_commands.autocomplete(own_wolf=_other_wolf_autocomplete, wolf_name=_wolf_name_autocomplete)
    async def trade_duplicates(self, interaction: discord.Interaction, wolf: discord.Member | None = None, wolf_name: str | None = None, own_wolf: str | None = None):
        user = await self._require_registered(interaction)
        if not user:
            return
        guild_id = self._require_guild(interaction)
        if not guild_id:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        recipient, err = _resolve_gift_recipient(interaction, user, wolf, own_wolf, wolf_name)
        if err:
            await interaction.response.send_message(embed=howlbert_embed('Invalid Target', err, color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        world = db.get_world(guild_id)
        from engine.duplicate_trade import trade_duplicates_between_wolves
        ok, msg = trade_duplicates_between_wolves(user, recipient, guild_id=guild_id, day=world['day_number'], require_pack_trade=False)
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed('Duplicate Trade' if ok else 'Trade Failed', msg, color=color)
        if ok:
            embed.set_footer(text='/pack tradepack · cross-pack · /pact action:trade · cat barter')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @trade.command(name='cancel', description='cancel your outgoing trade offer.')
    async def trade_cancel(self, interaction: discord.Interaction):
        user = await self._require_registered(interaction)
        if not user:
            return
        db.cancel_pending_trades_for_user(interaction.user.id)
        embed = howlbert_embed('Trade Cancelled', 'Your pending trade offers are cancelled.', color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _leaderboard(self, interaction: discord.Interaction):
        rows = db.get_leaderboard(10)
        if not rows:
            embed = howlbert_embed('Leaderboard', 'No wolves registered yet.')
            await interaction.response.send_message(embed=embed)
            return
        lines = []
        for i, row in enumerate(rows, 1):
            medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(i, f'**{i}.**')
            lines.append(f"{medal} {row['wolf_name']}; {format_bones(row['bones'])}")
        embed = howlbert_embed('Bone Leaderboard', '\n'.join(lines))
        await interaction.response.send_message(embed=embed)

    async def _work(self, interaction: discord.Interaction, scene: str | None=None, staff: bool=False):
        embed = try_work(interaction, scene=scene, staff=staff)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _shop(self, interaction: discord.Interaction):
        items = db.get_shop_items()
        if not items:
            embed = howlbert_embed('Trading Post', 'The shelves are bare.')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = build_shop_embed(items, page=0)
        view = make_shop_view(items, page=0)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=reply_ephemeral())

    async def _buy(self, interaction: discord.Interaction, item: str, quantity: int=1):
        user = await self._require_registered(interaction)
        if not user:
            return
        shop_item = db.get_item_by_key(item)
        if not shop_item:
            embed = howlbert_embed('Unknown Item', 'Check `/bones action:shop` for valid item keys.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if shop_item['price'] <= 0:
            embed = howlbert_embed('Not For Sale', "That isn't sold at the trading post. Wild herbs come from `/field action:forage`; food and toys use keys like `prey_vole` or `toy_bone`.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if quantity <= 0:
            embed = howlbert_embed('Invalid Quantity', 'Buy at least 1.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        total_price = shop_item['price'] * quantity
        if user['bones'] < total_price:
            embed = howlbert_embed('Not Enough Bones', 'Your stash is too light.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.shop_purchase import purchase_shop_item
        guild_id = interaction.guild.id if interaction.guild else None
        day = db.get_world(guild_id)['day_number'] if guild_id else 0
        note = ''
        for _ in range(quantity):
            ok, note, _ = purchase_shop_item(interaction.user.id, item, guild_id=guild_id, day=day)
            if not ok:
                break
        if not ok:
            if note == 'Not enough bones.':
                embed = howlbert_embed('Not Enough Bones', 'Your stash is too light.', color=ERROR_COLOR)
            elif note:
                embed = howlbert_embed("Can't Buy", note, color=ERROR_COLOR)
            else:
                embed = howlbert_embed('Purchase Failed', 'That purchase could not be completed.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        updated = db.get_user(interaction.user.id)
        embed = howlbert_embed('Purchased', note, color=SUCCESS_COLOR)
        embed.add_field(name='Item', value=shop_item['name'], inline=True)
        embed.add_field(name='Spent', value=format_bones(total_price), inline=True)
        if quantity > 1:
            embed.add_field(name='Quantity', value=str(quantity), inline=True)
        embed.add_field(name='Balance', value=format_bones(updated['bones']), inline=True)
        key = shop_item['key']
        footer_bits = ['/bones action:inventory']
        if key.startswith('prey_'):
            footer_bits.append('/food')
        elif key.startswith('toy_'):
            footer_bits.append('/playpen action:toys')
        elif key.startswith('herb_'):
            footer_bits.append('/herbs action:dryall · action:prepare')
        elif key in ('herb_bundle', 'prey_bundle', 'den_charm'):
            footer_bits.append('/bones action:use item:<key>')
        embed.set_footer(text=' · '.join(footer_bits))
        await interaction.response.send_message(embed=embed)

    async def _sell(self, interaction: discord.Interaction, item: str, quantity: int=1):
        user = await self._require_registered(interaction)
        if not user:
            return
        raw = (item or '').strip()
        if raw.lower().startswith('stack:') or raw.startswith('#') or raw.isdigit():
            embed = howlbert_embed('Herb Bag Removed', 'Forage herbs live in `/bones action:inventory`. Sell with **`/bones action:sell item:herb_arnica`**.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        shop_item = db.get_item_by_key(item)
        if not shop_item:
            embed = howlbert_embed('Unknown Item', 'Check `/bones action:shop` for valid keys.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        qty = db.get_inventory_quantity(interaction.user.id, shop_item['id'])
        if qty < 1:
            embed = howlbert_embed('Not In Pack', "You don't carry that item.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if shop_item['sell_price'] <= 0:
            embed = howlbert_embed("Can't Sell", "The den won't buy that back.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        db.sell_item(interaction.user.id, shop_item['id'], shop_item['sell_price'])
        updated = db.get_user(interaction.user.id)
        embed = howlbert_embed('Sold', color=SUCCESS_COLOR)
        embed.add_field(name='Item', value=shop_item['name'], inline=True)
        embed.add_field(name='Received', value=format_bones(shop_item['sell_price'], signed=True), inline=True)
        embed.add_field(name='Balance', value=format_bones(updated['bones']), inline=True)
        await interaction.response.send_message(embed=embed)

    async def _inventory(self, interaction: discord.Interaction):
        user = await self._require_registered(interaction)
        if not user:
            return
        items = db.get_inventory(interaction.user.id)
        stacks = db.get_prey_stacks(user['id']) if interaction.guild else []
        toys = db.get_amusement_stacks(user['id'])
        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day = world['day_number'] if world else 0
        if not items and (not stacks) and (not toys):
            embed = howlbert_embed('Your Pack', "You're carrying nothing but scent and grit.")
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        sections = []
        if stacks:
            from engine.prey_storage import format_prey_hoard_line
            prey_lines = [format_prey_hoard_line(s, day) for s in stacks]
            sections.append('**Food hoard**\n' + '\n'.join(prey_lines))
        if toys:
            from engine.amusement_storage import format_amusement_line
            toy_lines = [format_amusement_line(s) for s in toys]
            sections.append('**Amusement**\n' + '\n'.join(toy_lines))
        if items:
            item_lines = [f"**{row['name']}** x{row['quantity']} (`{row['key']}`)" for row in items]
            sections.append('**Items**\n' + '\n'.join(item_lines))
        embed = howlbert_embed('Your Pack', '\n\n'.join(sections))
        footer_bits = []
        if stacks:
            footer_bits.append('prey: /eat · /preypile · rotting → /salvage · /bury')
        if toys:
            footer_bits.append('toys: /playpen action:play · action:toystore')
        if any((row['key'].startswith('herb_') for row in items)):
            footer_bits.append('herbs: /bones action:inventory · action:dryall · `/bones action:sell item:stack:ID`')
        if any((row['key'] in USABLE_ITEM_KEYS for row in items)):
            footer_bits.append('/bones action:use item:<key>')
        if footer_bits:
            embed.set_footer(text=' · '.join(footer_bits))
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _use_item_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        items = db.get_inventory(interaction.user.id)
        choices = []
        for row in items:
            if row['key'] not in USABLE_ITEM_KEYS:
                continue
            if current and current.lower() not in row['key'] and (current.lower() not in row['name'].lower()):
                continue
            choices.append(app_commands.Choice(name=choice_label(f"{row['name']} ({row['key']})"), value=row['key']))
        return choices[:25]

    async def _use(self, interaction: discord.Interaction, item: str, recipient: discord.Member | None=None, own_recipient: str | None=None):
        user = await self._require_registered(interaction)
        if not user:
            return
        key = item.strip().lower()
        shop_item = db.get_item_by_key(key)
        if not shop_item or key not in USABLE_ITEM_KEYS:
            embed = howlbert_embed("Can't Use That", 'Check `/bones action:inventory`; usable keys: `herb_bundle`, `prey_bundle`, `den_charm`, `rabbit_pelt`. `lucky_tooth` is passive on `/bones action:hunt`. `safe_roll` works with `/rpg action:roll use_safe_roll:true`. `extra_paw` works with `/bones action:work` or `/crime`.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if db.get_inventory_quantity(interaction.user.id, shop_item['id']) < 1:
            embed = howlbert_embed('Not In Pack', f"You don't carry **{shop_item['name']}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if key == 'herb_bundle':
            from engine.shop_items import use_herb_bundle
            ok, msg, fields = use_herb_bundle(user, interaction.user.id)
            if not ok:
                embed = howlbert_embed('Herb Bundle', msg, color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            db.consume_item(interaction.user.id, shop_item['id'])
            if fields:
                db.update_user(interaction.user.id, **fields)
            embed = howlbert_embed('Herb Bundle', msg, color=SUCCESS_COLOR)
            embed.set_footer(text='/bones action:inventory · /bones action:inventory')
            await interaction.response.send_message(embed=embed)
            return
        if key == 'prey_bundle':
            if not interaction.guild:
                await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
                return
            from engine.shop_items import grant_prey_bundle
            day = db.get_world(interaction.guild.id)['day_number']
            _, summary = grant_prey_bundle(user['id'], guild_id=interaction.guild.id, day=day)
            db.consume_item(interaction.user.id, shop_item['id'])
            embed = howlbert_embed('Prey Bundle', f'Fresh-kill wrapped for the hoard:\n{summary}\n\nCheck **`/food`**.', color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            return
        if key == 'den_charm':
            if not interaction.guild:
                await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
                return
            if not user['pack_id']:
                embed = howlbert_embed('No Den', 'Lone wolves have no pack den to hang a charm at. Join a Great Pack first.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            day = db.get_world(interaction.guild.id)['day_number']
            pack = db.get_pack(user['pack_id'])
            db.consume_item(interaction.user.id, shop_item['id'])
            db.adjust_pack_unity(user['pack_id'], 1)
            db.update_user(interaction.user.id, last_den_charm_day=day)
            pack = db.get_pack(user['pack_id'])
            unity = pack['pack_unity'] if pack else 5
            embed = howlbert_embed('Den Charm Hung', f"You hang the charm at **{(pack['name'] if pack else 'your den')}** entrance. Pack unity rises to **{unity}/10**.", color=SUCCESS_COLOR)
            embed.set_footer(text='/pack · buy another charm to hang again')
            await interaction.response.send_message(embed=embed)
            return
        if key == 'rabbit_pelt':
            if recipient and own_recipient:
                await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use `wolf` or `own_wolf`; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if own_recipient:
                target_rows = db.list_user_wolves(interaction.user.id)
                active = user
                target = next((w for w in target_rows if w['wolf_name'].lower() == own_recipient.strip().lower() and w['id'] != active['id']), None)
                if not target:
                    embed = howlbert_embed('Unknown Wolf', f'No wolf named **{own_recipient}** on your account.', color=ERROR_COLOR)
                    await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                    return
                pelt_discord_id = target['discord_id']
            elif recipient and not (recipient.bot or recipient.id == interaction.user.id):
                target = db.get_user(recipient.id)
                if not target:
                    embed = howlbert_embed('Not Registered', f"{recipient.display_name} hasn't registered a wolf yet.", color=ERROR_COLOR)
                    await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                    return
                pelt_discord_id = recipient.id
            else:
                embed = howlbert_embed('Need a Packmate', 'Use `/bones action:use item:rabbit_pelt wolf:@player` or `own_wolf:` to trade the pelt.', color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            db.consume_item(interaction.user.id, shop_item['id'])
            db.add_bones(pelt_discord_id, RABBIT_PELT_GIFT_BONES)
            db.adjust_wolf_standing(interaction.user.id, RABBIT_PELT_STANDING)
            embed = howlbert_embed('Pelt Traded', color=SUCCESS_COLOR)
            embed.add_field(name='To', value=target['wolf_name'], inline=True)
            embed.add_field(name='They Received', value=format_bones(RABBIT_PELT_GIFT_BONES), inline=True)
            embed.add_field(name='Your Standing', value=f'+{RABBIT_PELT_STANDING}', inline=True)
            embed.set_footer(text='/bones action:balance · /profile')
            await interaction.response.send_message(embed=embed)
            return
async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))