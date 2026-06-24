import discord
from discord import app_commands
from discord.ext import commands

import database as db
from config import CURRENCY_LABEL, GREAT_PACKS
from engine.activities import try_daily, try_hunt, try_work, try_crime
from engine.shop_items import RABBIT_PELT_GIFT_BONES, RABBIT_PELT_STANDING, USABLE_ITEM_KEYS
from utils.currency import format_bones
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed
from engine.trade import build_trade_embed
from utils.trade_views import TRADE_DYNAMIC_ITEMS, make_trade_view
from utils.views import build_shop_embed, make_hunt_followup_view, make_shop_view
from utils.combat_views import make_combat_view


async def _other_wolf_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    active = db.get_user(interaction.user.id)
    if not active:
        return []
    choices = []
    for wolf in db.list_user_wolves(interaction.user.id):
        if wolf["id"] == active["id"]:
            continue
        name = wolf["wolf_name"]
        if current and current.lower() not in name.lower():
            continue
        choices.append(app_commands.Choice(name=name[:100], value=name))
    return choices[:25]


def _resolve_own_wolf(discord_id: int, name: str):
    rows = db.list_user_wolves(discord_id)
    return next((w for w in rows if w["wolf_name"].lower() == name.strip().lower()), None)


def _resolve_gift_recipient(
    interaction: discord.Interaction,
    user,
    wolf: discord.Member | None,
    own_wolf: str | None,
) -> tuple[object | None, str | None]:
    if wolf and own_wolf:
        return None, "Pick either another **player** or `own_wolf`; not both."
    if own_wolf:
        recipient = _resolve_own_wolf(interaction.user.id, own_wolf)
        if not recipient:
            return None, "No wolf with that name on your account. Check `/wolves`."
        if recipient["id"] == user["id"]:
            return None, "Switch to another wolf with `/switchwolf`, or pick a different `own_wolf`."
        return recipient, None
    if wolf:
        if wolf.bot or wolf.id == interaction.user.id:
            return None, "Use another **player**, or your other wolf via `own_wolf`."
        recipient = db.get_user(wolf.id)
        if not recipient:
            return None, f"{wolf.display_name} hasn't registered a wolf yet."
        return recipient, None
    return None, "Pick another **player** or one of your wolves with `own_wolf`."


class Economy(commands.Cog):
    trade = app_commands.Group(
        name="trade",
        description="Offer items and bones to another wolf (they must accept).",
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.add_dynamic_items(*TRADE_DYNAMIC_ITEMS)

    async def _require_registered(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            embed = howlbert_embed(
                "Not Registered",
                "Use `/register` before using economy commands.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
        return user

    def _require_guild(self, interaction: discord.Interaction) -> int | None:
        if interaction.guild:
            return interaction.guild.id
        return None

    async def _inventory_item_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        items = db.get_inventory(interaction.user.id)
        choices = []
        for row in items:
            if current and current.lower() not in row["key"] and current.lower() not in row["name"].lower():
                continue
            choices.append(
                app_commands.Choice(
                    name=f"{row['name']} x{row['quantity']} ({row['key']})"[:100],
                    value=row["key"],
                )
            )
        return choices[:25]

    async def _all_item_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        items = db.get_all_items()
        choices = []
        for row in items:
            if current and current.lower() not in row["key"] and current.lower() not in row["name"].lower():
                continue
            choices.append(
                app_commands.Choice(name=f"{row['name']} ({row['key']})"[:100], value=row["key"])
            )
        return choices[:25]

    @app_commands.command(
        name="bones",
        description="Balance, daily, hunt, shop, inventory, work, crime, give, and more.",
    )
    @app_commands.describe(
        action="balance, daily, hunt, give, giveitem, leaderboard, work, crime, shop, buy, sell, inventory, or use",
        amount="Bones amount (give)",
        wolf="Recipient player (give / giveitem)",
        own_wolf="Your other wolf (give / giveitem)",
        item="Item key (giveitem, buy, sell, use)",
        quantity="Item quantity",
        new_name="Rename item (use)",
        collaborate="Call a pack hunt (hunt only; same Great Pack joins via buttons)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Balance", value="balance"),
            app_commands.Choice(name="Daily stipend", value="daily"),
            app_commands.Choice(name="Hunt for bones", value="hunt"),
            app_commands.Choice(name="Give bones", value="give"),
            app_commands.Choice(name="Give item", value="giveitem"),
            app_commands.Choice(name="Leaderboard", value="leaderboard"),
            app_commands.Choice(name="Work", value="work"),
            app_commands.Choice(name="Crime", value="crime"),
            app_commands.Choice(name="Shop", value="shop"),
            app_commands.Choice(name="Buy item", value="buy"),
            app_commands.Choice(name="Sell item", value="sell"),
            app_commands.Choice(name="Inventory", value="inventory"),
            app_commands.Choice(name="Use item", value="use"),
        ]
    )
    @app_commands.autocomplete(item=_inventory_item_autocomplete, own_wolf=_other_wolf_autocomplete)
    async def bones(
        self,
        interaction: discord.Interaction,
        action: str,
        amount: int | None = None,
        wolf: discord.Member | None = None,
        own_wolf: str | None = None,
        item: str | None = None,
        quantity: int = 1,
        new_name: str | None = None,
        collaborate: bool = False,
    ):
        if action == "balance":
            await self._balance(interaction)
        elif action == "daily":
            await self._daily(interaction)
        elif action == "hunt":
            if collaborate:
                from cogs.collab_hunt import post_collab_hunt_call

                await post_collab_hunt_call(interaction, self.bot)
            else:
                await self._hunt(interaction)
        elif action == "give":
            if amount is None:
                await interaction.response.send_message("Provide `amount`.", ephemeral=True)
                return
            await self._give(interaction, amount, wolf, own_wolf)
        elif action == "giveitem":
            if not item:
                await interaction.response.send_message("Provide `item`.", ephemeral=True)
                return
            await self._giveitem(interaction, item, wolf, own_wolf, quantity)
        elif action == "leaderboard":
            await self._leaderboard(interaction)
        elif action == "work":
            await self._work(interaction)
        elif action == "crime":
            await self._crime(interaction)
        elif action == "shop":
            await self._shop(interaction)
        elif action == "buy":
            if not item:
                await interaction.response.send_message("Provide `item`.", ephemeral=True)
                return
            await self._buy(interaction, item, quantity)
        elif action == "sell":
            if not item:
                await interaction.response.send_message("Provide `item`.", ephemeral=True)
                return
            await self._sell(interaction, item, quantity)
        elif action == "inventory":
            await self._inventory(interaction)
        elif action == "use":
            if not item:
                await interaction.response.send_message("Provide `item`.", ephemeral=True)
                return
            await self._use(interaction, item, None, new_name)

    async def _balance(self, interaction: discord.Interaction):
        user = await self._require_registered(interaction)
        if not user:
            return

        embed = howlbert_embed("Your Stores", color=SUCCESS_COLOR)
        embed.add_field(name=CURRENCY_LABEL, value=format_bones(user["bones"]), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _daily(self, interaction: discord.Interaction):
        embed = try_daily(interaction)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=embed.color == ERROR_COLOR)

    async def _hunt(self, interaction: discord.Interaction):
        embed, show_prey, combat_enc = try_hunt(interaction)
        if not embed:
            return
        if combat_enc:
            view = make_combat_view(combat_enc, self.bot)
            await interaction.response.send_message(embed=embed, view=view)
            return
        if show_prey and embed.color != ERROR_COLOR:
            await interaction.response.send_message(embed=embed, view=make_hunt_followup_view())
        else:
            await interaction.response.send_message(embed=embed, ephemeral=embed.color == ERROR_COLOR)

    async def _give(
        self,
        interaction: discord.Interaction,
        amount: int,
        wolf: discord.Member | None = None,
        own_wolf: str | None = None,
    ):
        user = await self._require_registered(interaction)
        if not user:
            return

        recipient, err = _resolve_gift_recipient(interaction, user, wolf, own_wolf)
        if err:
            embed = howlbert_embed("Invalid Target", err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if amount <= 0:
            embed = howlbert_embed("Invalid Amount", "Give at least 1 bone.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if user["bones"] < amount:
            embed = howlbert_embed("Not Enough Bones", "Your stash is too light.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not db.transfer_bones_by_wolf_id(user["id"], recipient["id"], amount):
            embed = howlbert_embed("Transfer Failed", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        embed = howlbert_embed("Bones Gifted", color=SUCCESS_COLOR)
        embed.add_field(name="To", value=recipient["wolf_name"], inline=True)
        embed.add_field(name="Amount", value=format_bones(amount), inline=True)
        await interaction.response.send_message(embed=embed)

    async def _giveitem(
        self,
        interaction: discord.Interaction,
        item: str,
        wolf: discord.Member | None = None,
        own_wolf: str | None = None,
        quantity: int = 1,
    ):
        user = await self._require_registered(interaction)
        if not user:
            return

        recipient, err = _resolve_gift_recipient(interaction, user, wolf, own_wolf)
        if err:
            embed = howlbert_embed("Invalid Target", err, color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if quantity <= 0:
            embed = howlbert_embed("Invalid Quantity", "Give at least 1.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        shop_item = db.get_item_by_key(item.strip())
        if not shop_item:
            embed = howlbert_embed("Unknown Item", "Check `/inventory` for valid keys.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        owned = db.get_inventory_quantity(interaction.user.id, shop_item["id"])
        if owned < quantity:
            embed = howlbert_embed(
                "Not Enough",
                f"You only carry **{owned}**; can't give **{quantity}**.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not db.transfer_item_by_wolf_id(user["id"], recipient["id"], shop_item["id"], quantity):
            embed = howlbert_embed("Transfer Failed", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = howlbert_embed("Item Gifted", color=SUCCESS_COLOR)
        embed.add_field(name="To", value=recipient["wolf_name"], inline=True)
        embed.add_field(name="Item", value=f"{shop_item['name']} x{quantity}", inline=True)
        await interaction.response.send_message(embed=embed)

    @trade.command(name="offer", description="Propose a trade; items and/or bones.")
    @app_commands.describe(
        wolf="Wolf to trade with",
        offer_item="Item you give (key from /inventory)",
        offer_quantity="How many you give (default 1)",
        offer_bones="Bones you give (default 0)",
        for_item="Item you want from them (optional)",
        for_quantity="How many you want (default 1)",
        for_bones="Bones you want from them (default 0)",
    )
    @app_commands.autocomplete(offer_item=_inventory_item_autocomplete, for_item=_all_item_autocomplete)
    async def trade_offer(
        self,
        interaction: discord.Interaction,
        wolf: discord.Member,
        offer_item: str | None = None,
        offer_quantity: int = 1,
        offer_bones: int = 0,
        for_item: str | None = None,
        for_quantity: int = 1,
        for_bones: int = 0,
    ):
        user = await self._require_registered(interaction)
        if not user:
            return

        if wolf.bot or wolf.id == interaction.user.id:
            embed = howlbert_embed("Invalid Target", "Choose another wolf.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        target = db.get_user(wolf.id)
        if not target:
            embed = howlbert_embed(
                "Not Registered",
                f"{wolf.display_name} hasn't registered a wolf yet.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if offer_bones < 0 or for_bones < 0:
            embed = howlbert_embed("Invalid Amount", "Bones can't be negative.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        offer_row = db.get_item_by_key(offer_item.strip()) if offer_item else None
        if offer_item and not offer_row:
            embed = howlbert_embed("Unknown Item", "Check `/inventory` for your offer item.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        want_row = db.get_item_by_key(for_item.strip()) if for_item else None
        if for_item and not want_row:
            embed = howlbert_embed("Unknown Item", "Check item keys with `/inventory`.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        gives_item = offer_row is not None and offer_quantity > 0
        wants_item = want_row is not None and for_quantity > 0
        if not gives_item and offer_bones <= 0:
            embed = howlbert_embed(
                "Nothing Offered",
                "Include an `offer_item` and/or `offer_bones` greater than 0.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if offer_row and offer_quantity <= 0:
            embed = howlbert_embed("Invalid Quantity", "Offer quantity must be at least 1.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if want_row and for_quantity <= 0:
            embed = howlbert_embed("Invalid Quantity", "Requested quantity must be at least 1.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if offer_row:
            owned = db.get_inventory_quantity(interaction.user.id, offer_row["id"])
            if owned < offer_quantity:
                embed = howlbert_embed(
                    "Not Enough",
                    f"You only carry **{owned}** of that item.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        if offer_bones > 0 and user["bones"] < offer_bones:
            embed = howlbert_embed("Not Enough Bones", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        trade_id = db.create_pending_trade(
            interaction.user.id,
            wolf.id,
            from_item_id=offer_row["id"] if offer_row else None,
            from_item_qty=offer_quantity if offer_row else 0,
            from_bones=offer_bones,
            to_item_id=want_row["id"] if want_row else None,
            to_item_qty=for_quantity if want_row else 0,
            to_bones=for_bones,
        )
        if not trade_id:
            embed = howlbert_embed("Trade Failed", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        trade = db.get_pending_trade(trade_id)
        embed = build_trade_embed(trade)
        embed.description = f"{wolf.mention}; accept or decline below. Offer expires in 10 minutes."
        view = make_trade_view(trade_id)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        db.set_pending_trade_message_id(trade_id, msg.id)

    @trade.command(name="cancel", description="Cancel your outgoing trade offer.")
    async def trade_cancel(self, interaction: discord.Interaction):
        user = await self._require_registered(interaction)
        if not user:
            return

        db.cancel_pending_trades_for_user(interaction.user.id)
        embed = howlbert_embed(
            "Trade Cancelled",
            "Your pending trade offers are cancelled.",
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _leaderboard(self, interaction: discord.Interaction):
        rows = db.get_leaderboard(10)
        if not rows:
            embed = howlbert_embed("Leaderboard", "No wolves registered yet.")
            await interaction.response.send_message(embed=embed)
            return

        lines = []
        for i, row in enumerate(rows, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"**{i}.**")
            lines.append(f"{medal} {row['wolf_name']}; {format_bones(row['bones'])}")

        embed = howlbert_embed("Bone Leaderboard", "\n".join(lines))
        await interaction.response.send_message(embed=embed)

    async def _work(self, interaction: discord.Interaction, scene: str | None = None, staff: bool = False):
        embed = try_work(interaction, scene=scene, staff=staff)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=embed.color == ERROR_COLOR)

    async def _crime(
        self,
        interaction: discord.Interaction,
        target_pack: str | None = None,
        scene: str | None = None,
        staff: bool = False,
    ):
        embed = try_crime(interaction, target_pack=target_pack, scene=scene, staff=staff)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=embed.color == ERROR_COLOR)

    async def _shop(self, interaction: discord.Interaction):
        items = db.get_shop_items()
        if not items:
            embed = howlbert_embed("Trading Post", "The shelves are bare.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = build_shop_embed(items, page=0)
        view = make_shop_view(items, page=0)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def _buy(self, interaction: discord.Interaction, item: str, quantity: int = 1):
        user = await self._require_registered(interaction)
        if not user:
            return

        shop_item = db.get_item_by_key(item)
        if not shop_item:
            embed = howlbert_embed("Unknown Item", "Check `/shop` for valid item keys.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if shop_item["price"] <= 0:
            embed = howlbert_embed(
                "Not For Sale",
                "That isn't sold at the trading post. Wild herbs come from `/forage`; food and toys use keys like `prey_vole` or `toy_bone`.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if user["bones"] < shop_item["price"]:
            embed = howlbert_embed("Not Enough Bones", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from engine.shop_purchase import purchase_shop_item

        guild_id = interaction.guild.id if interaction.guild else None
        day = db.get_world(guild_id)["day_number"] if guild_id else 0
        ok, note, _ = purchase_shop_item(
            interaction.user.id,
            item,
            guild_id=guild_id,
            day=day,
        )
        if not ok:
            if note == "Not enough bones.":
                embed = howlbert_embed("Not Enough Bones", color=ERROR_COLOR)
            elif note:
                embed = howlbert_embed("Can't Buy", note, color=ERROR_COLOR)
            else:
                embed = howlbert_embed("Purchase Failed", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        updated = db.get_user(interaction.user.id)
        embed = howlbert_embed("Purchased", note, color=SUCCESS_COLOR)
        embed.add_field(name="Item", value=shop_item["name"], inline=True)
        embed.add_field(name="Spent", value=format_bones(shop_item["price"]), inline=True)
        embed.add_field(name="Balance", value=format_bones(updated["bones"]), inline=True)
        await interaction.response.send_message(embed=embed)

    async def _sell(self, interaction: discord.Interaction, item: str, quantity: int = 1):
        user = await self._require_registered(interaction)
        if not user:
            return

        raw = (item or "").strip()
        if raw.lower().startswith("stack:") or raw.startswith("#") or raw.isdigit():
            from engine.herb_storage import parse_herb_stack_id
            from engine.herb_market import sell_forage_herb_stack

            sid = parse_herb_stack_id(raw)
            if not sid:
                embed = howlbert_embed(
                    "Bad Stack ID",
                    "Use **`stack:ID`** from `/herbs action:bag`.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if not interaction.guild:
                await interaction.response.send_message("Sell forage herbs in a server.", ephemeral=True)
                return
            world = db.get_world(interaction.guild.id)
            ok, msg, price = sell_forage_herb_stack(user, sid, day=world["day_number"])
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            embed = howlbert_embed("Trading Post", msg, color=color)
            if ok:
                updated = db.get_user(interaction.user.id)
                embed.add_field(name="Received", value=format_bones(price, signed=True), inline=True)
                embed.add_field(name="Balance", value=format_bones(updated["bones"]), inline=True)
            await interaction.response.send_message(embed=embed)
            return

        shop_item = db.get_item_by_key(item)
        if not shop_item:
            embed = howlbert_embed("Unknown Item", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        qty = db.get_inventory_quantity(interaction.user.id, shop_item["id"])
        if qty < 1:
            embed = howlbert_embed("Not In Pack", "You don't carry that item.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if shop_item["sell_price"] <= 0:
            embed = howlbert_embed("Can't Sell", "The den won't buy that back.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        db.sell_item(interaction.user.id, shop_item["id"], shop_item["sell_price"])
        updated = db.get_user(interaction.user.id)
        embed = howlbert_embed("Sold", color=SUCCESS_COLOR)
        embed.add_field(name="Item", value=shop_item["name"], inline=True)
        embed.add_field(name="Received", value=format_bones(shop_item["sell_price"], signed=True), inline=True)
        embed.add_field(name="Balance", value=format_bones(updated["bones"]), inline=True)
        await interaction.response.send_message(embed=embed)

    async def _inventory(self, interaction: discord.Interaction):
        user = await self._require_registered(interaction)
        if not user:
            return

        items = db.get_inventory(interaction.user.id)
        stacks = db.get_prey_stacks(user["id"]) if interaction.guild else []
        toys = db.get_amusement_stacks(user["id"])
        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day = world["day_number"] if world else 0

        if not items and not stacks and not toys:
            embed = howlbert_embed("Your Pack", "You're carrying nothing but scent and grit.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        sections = []
        if stacks:
            from engine.prey_storage import format_prey_hoard_line

            prey_lines = [format_prey_hoard_line(s, day) for s in stacks]
            sections.append("**Prey hoard**\n" + "\n".join(prey_lines))
        if toys:
            from engine.amusement_storage import format_amusement_line

            toy_lines = [format_amusement_line(s) for s in toys]
            sections.append("**Amusement**\n" + "\n".join(toy_lines))
        if items:
            item_lines = [
                f"**{row['name']}** x{row['quantity']} (`{row['key']}`)" for row in items
            ]
            sections.append("**Items**\n" + "\n".join(item_lines))

        embed = howlbert_embed("Your Pack", "\n\n".join(sections))
        footer_bits = []
        if stacks:
            footer_bits.append("prey: /eat · /preypile · rotting → /salvage · /bury")
        if toys:
            footer_bits.append("toys: /playpen action:play · action:toystore")
        if any(row["key"].startswith("herb_") for row in items):
            footer_bits.append(
                "herbs: /herbs action:dryall · action:store mode:depositall"
            )
        if any(row["key"] in USABLE_ITEM_KEYS for row in items):
            footer_bits.append("/use item:<key>")
        if footer_bits:
            embed.set_footer(text=" · ".join(footer_bits))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _use_item_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        items = db.get_inventory(interaction.user.id)
        choices = []
        for row in items:
            if row["key"] not in USABLE_ITEM_KEYS:
                continue
            if current and current.lower() not in row["key"] and current.lower() not in row["name"].lower():
                continue
            choices.append(app_commands.Choice(name=f"{row['name']} ({row['key']})", value=row["key"]))
        return choices[:25]

    async def _use(
        self,
        interaction: discord.Interaction,
        item: str,
        recipient: discord.Member | None = None,
        new_name: str | None = None,
    ):
        user = await self._require_registered(interaction)
        if not user:
            return

        key = item.strip().lower()
        if key == "reincarnation":
            key = "revive"
        shop_item = db.get_item_by_key(key)
        if not shop_item or key not in USABLE_ITEM_KEYS:
            embed = howlbert_embed(
                "Can't Use That",
                "Check `/inventory`; usable keys: `herb_bundle`, `prey_bundle`, `den_charm`, `rabbit_pelt`, "
                "`revive`, `reincarnation`. "
                "`lucky_tooth` is passive on `/bones action:hunt`. `safe_roll` works with `/rpg action:roll use_safe_roll:true`. "
                "`extra_paw` works with `/work` or `/crime`.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if db.get_inventory_quantity(interaction.user.id, shop_item["id"]) < 1:
            embed = howlbert_embed("Not In Pack", f"You don't carry **{shop_item['name']}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if key == "herb_bundle":
            from engine.shop_items import grant_herb_bundle

            _, summary = grant_herb_bundle(interaction.user.id)
            db.consume_item(interaction.user.id, shop_item["id"])
            embed = howlbert_embed(
                "Herb Bundle",
                f"You unpack dried herbs into your kit:\n{summary}",
                color=SUCCESS_COLOR,
            )
            await interaction.response.send_message(embed=embed)
            return

        if key == "prey_bundle":
            if not interaction.guild:
                await interaction.response.send_message("Use this in a server.", ephemeral=True)
                return
            from engine.shop_items import grant_prey_bundle

            day = db.get_world(interaction.guild.id)["day_number"]
            _, summary = grant_prey_bundle(
                user["id"],
                guild_id=interaction.guild.id,
                day=day,
            )
            db.consume_item(interaction.user.id, shop_item["id"])
            embed = howlbert_embed(
                "Prey Bundle",
                f"Fresh-kill wrapped for the hoard:\n{summary}\n\nCheck **`/prey`**.",
                color=SUCCESS_COLOR,
            )
            await interaction.response.send_message(embed=embed)
            return

        if key == "den_charm":
            if not interaction.guild:
                await interaction.response.send_message("Use this in a server.", ephemeral=True)
                return
            if not user["pack_id"]:
                embed = howlbert_embed(
                    "No Den",
                    "Lone wolves have no pack den to hang a charm at. Join a Great Pack first.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            day = db.get_world(interaction.guild.id)["day_number"]
            if user["last_den_charm_day"] >= day:
                embed = howlbert_embed(
                    "Already Hung",
                    "Your charm already steadies the den this rollover.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            pack = db.get_pack(user["pack_id"])
            db.adjust_pack_unity(user["pack_id"], 1)
            db.update_user(interaction.user.id, last_den_charm_day=day)
            pack = db.get_pack(user["pack_id"])
            unity = pack["pack_unity"] if pack else 5
            embed = howlbert_embed(
                "Den Charm Hung",
                f"You hang the charm at **{pack['name'] if pack else 'your den'}** entrance. "
                f"Pack unity rises to **{unity}/10**.",
                color=SUCCESS_COLOR,
            )
            await interaction.response.send_message(embed=embed)
            return

        if key == "rabbit_pelt":
            if not recipient or recipient.bot or recipient.id == interaction.user.id:
                embed = howlbert_embed(
                    "Need a Packmate",
                    "Use `recipient:@wolf` to trade the pelt with another registered wolf.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            target = db.get_user(recipient.id)
            if not target:
                embed = howlbert_embed(
                    "Not Registered",
                    f"{recipient.display_name} hasn't registered a wolf yet.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            db.consume_item(interaction.user.id, shop_item["id"])
            db.add_bones(recipient.id, RABBIT_PELT_GIFT_BONES)
            db.adjust_wolf_standing(interaction.user.id, RABBIT_PELT_STANDING)
            embed = howlbert_embed("Pelt Traded", color=SUCCESS_COLOR)
            embed.add_field(name="To", value=target["wolf_name"], inline=True)
            embed.add_field(name="They Received", value=format_bones(RABBIT_PELT_GIFT_BONES), inline=True)
            embed.add_field(name="Your Standing", value=f"+{RABBIT_PELT_STANDING}", inline=True)
            await interaction.response.send_message(embed=embed)
            return

        if key == "revive":
            if user["condition"] != "dead":
                embed = howlbert_embed(
                    "Still Breathing",
                    "**Revive** only works when your active wolf is **dead**. "
                    "Use `/vitals action:condition` to check; or `/rpg action:delete confirm:DELETE` / `/register` for a fresh wolf.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            wolf_name = user["wolf_name"]
            old_age = user["age_months"] if "age_months" in user.keys() else 24
            err = db.revive_wolf(interaction.user.id)
            if err:
                embed = howlbert_embed("Can't Revive", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            db.consume_item(interaction.user.id, shop_item["id"])
            revived = db.get_user(interaction.user.id)
            from config import MAX_WOLF_AGE_MOONS

            body = (
                f"Mist thins around **{wolf_name}**; breath returns, paws find earth again.\n"
                f"**1 HP** · hunger & thirst restored."
            )
            if old_age >= MAX_WOLF_AGE_MOONS and revived["age_months"] < old_age:
                body += (
                    f"\n\nAge reset to **{revived['age_months']} moons** "
                    f"(was **{old_age}**; too ancient to walk the wild unchanged)."
                )
            embed = howlbert_embed("Revived", body, color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed)
            return

        if key == "reincarnation":
            if user["condition"] != "dead":
                embed = howlbert_embed(
                    "Still Breathing",
                    "**Reincarnation** only works when your active wolf is **dead**.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if not new_name or not new_name.strip():
                embed = howlbert_embed(
                    "Need a New Name",
                    "Use `/use item:reincarnation new_name:<name>`; a new identity for the same soul.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            old_name = user["wolf_name"]
            err = db.reincarnate_as_new_life(interaction.user.id, new_name)
            if err == "not_dead":
                embed = howlbert_embed("Still Breathing", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if err == "same_name":
                embed = howlbert_embed(
                    "Same Name",
                    "Pick a **new** name; reincarnation is a new identity.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if err == "name_taken":
                embed = howlbert_embed(
                    "Name Taken",
                    "Another wolf already uses that name. Choose a different one.",
                    color=ERROR_COLOR,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if err and err.startswith("name:"):
                embed = howlbert_embed("Invalid Name", err[5:], color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            if err:
                embed = howlbert_embed("Can't Reincarnate", color=ERROR_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            db.consume_item(interaction.user.id, shop_item["id"])
            reborn = db.get_user(interaction.user.id)
            from config import REINCARNATION_START_AGE_MOONS
            from rpg_rules import ROLE_LABELS

            role_label = ROLE_LABELS.get(reborn["wolf_role"], reborn["wolf_role"])
            embed = howlbert_embed("Reincarnated", color=SUCCESS_COLOR)
            embed.description = (
                f"The mist takes **{old_name}**; **{reborn['wolf_name']}** wakes in a younger body.\n\n"
                f"**{REINCARNATION_START_AGE_MOONS} moons** · **{role_label}** · stats & standing kept\n"
                "Prey hoard & toys cleared · `/prey` `/toys`"
            )
            await interaction.response.send_message(embed=embed)
            return


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
