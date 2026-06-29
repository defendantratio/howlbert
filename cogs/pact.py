"""Top-level `/pact` — cat clan and wolf pack treaties."""
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.prey_items import is_forage_food, prey_meta
from utils.currency import format_bones
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label
from utils.replies import reply_ephemeral

def _require_pack(user):
    if not user or not user['pack_id']:
        return (None, None)
    pack = db.get_pack(user['pack_id'])
    if not pack:
        return (user, None)
    return (user, pack)

async def _food_stack_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[int]]:
    user = db.get_user(interaction.user.id)
    if not user:
        return []
    choices: list[app_commands.Choice[int]] = []
    for stack in db.get_prey_stacks(user['id']):
        meta = prey_meta(stack['prey_key'])
        kind = 'forage' if is_forage_food(stack['prey_key']) else 'meat'
        label = f"#{stack['id']} {meta['name']} ({stack['uses_left']} use, {kind})"
        if current and current.lower() not in label.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(label), value=int(stack['id'])))
    return choices[:25]

async def _pact_target_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    from config import GREAT_PACKS
    from engine.cat_clans import KNOWN_CAT_CLANS
    choices: list[app_commands.Choice[str]] = []
    for name in KNOWN_CAT_CLANS:
        if current and current.lower() not in name.lower():
            continue
        choices.append(app_commands.Choice(name=choice_label(f'{name} (cat clan)'), value=name))
    for _key, info in GREAT_PACKS.items():
        label = f"{info['name']} (wolf pack)"
        if current and current.lower() not in label.lower() and (current.lower() not in _key):
            continue
        choices.append(app_commands.Choice(name=choice_label(label), value=info['name']))
    return choices[:25]

class Pact(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='pact', description='negotiate treaties with cat clans or other great wolf packs (alpha or diplomat).')
    @app_commands.describe(action='view, forge, renew, break, gift, trade, tradefood, receive, or raid', target='cat clan or great wolf pack (e.g. thunderclan, greyspire)', pact_type='treaty type when forging', terms='short rp terms (optional)', stack='food/forage stack to trade (for tradefood)', raid_type='what to steal: food, herbs, or amusement (raid only)', amount='bones to send as tribute, 0 or more; more bones = more trust/standing (gift only)')
    @app_commands.choices(action=[app_commands.Choice(name='view pacts', value='view'), app_commands.Choice(name='forge treaty', value='forge'), app_commands.Choice(name='renew treaty', value='renew'), app_commands.Choice(name='break treaty', value='break'), app_commands.Choice(name='send tribute gift', value='gift'), app_commands.Choice(name='trade duplicates', value='trade'), app_commands.Choice(name='trade food', value='tradefood'), app_commands.Choice(name='receive border goods', value='receive'), app_commands.Choice(name='raid camp/den', value='raid')], pact_type=[app_commands.Choice(name='border truce (12 sunrises)', value='truce'), app_commands.Choice(name='alliance (18 sunrises)', value='alliance'), app_commands.Choice(name='hunting rights (8 sunrises)', value='hunting_rights')], raid_type=[app_commands.Choice(name='food reserve', value='food'), app_commands.Choice(name='herb store', value='herbs'), app_commands.Choice(name='toy store', value='amusement')])
    @app_commands.autocomplete(target=_pact_target_autocomplete, stack=_food_stack_autocomplete)
    async def pact(self, interaction: discord.Interaction, action: str='view', target: str | None=None, pact_type: str | None=None, terms: str | None=None, stack: int | None=None, raid_type: str='food', amount: app_commands.Range[int, 0, None] | None=None):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(embed=howlbert_embed('not registered', 'use `/register` first.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        user, pack = _require_pack(user)
        if not pack:
            await interaction.response.send_message(embed=howlbert_embed('no pack', 'join a great pack with `/register` or `/setfaction` first.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('use this in a server.'), ephemeral=reply_ephemeral())
            return
        from engine.cat_pacts import break_cat_pact, forge_cat_pact, format_pacts_body, gift_cat_pact, receive_cat_goods, renew_cat_pact, trade_duplicates_cat_pact, trade_food_cat_pact
        from engine.wolf_pack_pacts import break_wolf_pack_pact, forge_wolf_pack_pact, gift_wolf_pack_pact, is_wolf_pack_target, receive_wolf_pack_goods, renew_wolf_pack_pact, trade_duplicates_wolf_pack_pact, trade_food_wolf_pack_pact
        world = db.get_world(interaction.guild.id)
        day = world['day_number']
        guild_id = interaction.guild.id
        if action == 'view':
            body = format_pacts_body(guild_id, pack['id'], day=day)
            embed = howlbert_embed(f"{pack['name']}; treaties", body)
            embed.set_footer(text=f"treasury: {format_bones(int(pack['treasury']))} · `/pact action:forge`")
            await interaction.response.send_message(embed=embed)
            return
        if not target:
            await interaction.response.send_message(embed=howlbert_embed('treaty target', 'name a **cat clan** or **great wolf pack** (greyspire, mistmoor, thistlehide, silverrush, thunderclan, …).', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        wolf_target = is_wolf_pack_target(target)
        if action == 'forge':
            if not pact_type:
                await interaction.response.send_message(embed=howlbert_embed('pact type', 'pick **truce**, **alliance**, or **hunting_rights**.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if wolf_target:
                ok, msg = forge_wolf_pack_pact(user, pack, guild_id=guild_id, target_pack=target, pact_type=pact_type, terms_note=terms or '', day=day)
            else:
                ok, msg = forge_cat_pact(user, pack, guild_id=guild_id, clan_name=target, pact_type=pact_type, terms_note=terms or '', day=day)
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            embed = howlbert_embed('treaty forged' if ok else 'parley failed', msg, color=color)
            if ok:
                updated = db.get_pack(pack['id'])
                embed.set_footer(text=f"treasury: {format_bones(updated['treasury'])}")
            await interaction.response.send_message(embed=embed, ephemeral=False if ok else reply_ephemeral())
            return
        if action == 'renew':
            if wolf_target:
                ok, msg = renew_wolf_pack_pact(user, pack, guild_id=guild_id, target_pack=target, day=day)
            else:
                ok, msg = renew_cat_pact(user, pack, guild_id=guild_id, clan_name=target, day=day)
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            await interaction.response.send_message(embed=howlbert_embed('renew treaty' if ok else 'renewal failed', msg, color=color), ephemeral=False if ok else reply_ephemeral())
            return
        if action == 'break':
            if wolf_target:
                ok, msg = break_wolf_pack_pact(user, pack, guild_id=guild_id, target_pack=target, day=day)
            else:
                ok, msg = break_cat_pact(user, pack, guild_id=guild_id, clan_name=target, day=day)
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            await interaction.response.send_message(embed=howlbert_embed('treaty broken' if ok else 'cannot break', msg, color=color))
            return
        if action == 'gift':
            if wolf_target:
                ok, msg = gift_wolf_pack_pact(user, pack, guild_id=guild_id, target_pack=target, day=day, amount=amount)
            else:
                ok, msg = gift_cat_pact(user, pack, guild_id=guild_id, clan_name=target, day=day, amount=amount)
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            await interaction.response.send_message(embed=howlbert_embed('tribute sent' if ok else 'gift failed', msg, color=color), ephemeral=False if ok else reply_ephemeral())
            return
        if action == 'trade':
            if wolf_target:
                ok, msg = trade_duplicates_wolf_pack_pact(user, pack, guild_id=guild_id, target_pack=target, day=day)
            else:
                ok, msg = trade_duplicates_cat_pact(user, pack, guild_id=guild_id, clan_name=target, day=day)
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            embed = howlbert_embed('border barter' if ok else 'barter failed', msg, color=color)
            if ok:
                embed.set_footer(text='/pact action:view · /pact action:receive')
            await interaction.response.send_message(embed=embed, ephemeral=False if ok else reply_ephemeral())
            return
        if action == 'tradefood':
            if stack is None:
                await interaction.response.send_message(embed=howlbert_embed('pick food to trade', 'choose a carcass or forage stack with the **stack** option (see `/food` for ids).', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if wolf_target:
                ok, msg = trade_food_wolf_pack_pact(user, pack, guild_id=guild_id, target_pack=target, stack_id=int(stack), day=day)
            else:
                ok, msg = trade_food_cat_pact(user, pack, guild_id=guild_id, clan_name=target, stack_id=int(stack), day=day)
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            embed = howlbert_embed('border food trade' if ok else 'trade failed', msg, color=color)
            if ok:
                embed.set_footer(text='/pact action:view · /food')
            await interaction.response.send_message(embed=embed, ephemeral=False if ok else reply_ephemeral())
            return
        if action == 'receive':
            if wolf_target:
                ok, msg = receive_wolf_pack_goods(user, pack, guild_id=guild_id, target_pack=target, day=day)
            else:
                ok, msg = receive_cat_goods(user, pack, guild_id=guild_id, clan_name=target, day=day)
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            embed = howlbert_embed('border goods' if ok else 'receive failed', msg, color=color)
            if ok:
                embed.set_footer(text='/food · /bones action:inventory · /playpen action:toys')
            await interaction.response.send_message(embed=embed, ephemeral=False if ok else reply_ephemeral())
            return
        if action == 'raid':
            if wolf_target:
                from config import GREAT_PACKS
                from engine.activities import try_crime

                gp_key = next((k for k, info in GREAT_PACKS.items() if target.strip().lower() in (k, info['name'].lower())), None)
                embed = try_crime(interaction, target_pack=gp_key, raid_type=raid_type)
                if embed:
                    await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
                return
            from engine.cat_pacts import raid_cat_clan

            ok, msg = raid_cat_clan(user, pack, guild_id=guild_id, clan_name=target, raid_type=raid_type, day=day)
            color = SUCCESS_COLOR if ok else ERROR_COLOR
            embed = howlbert_embed('raid successful' if ok else 'caught at the border', msg, color=color)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

async def setup(bot: commands.Bot):
    await bot.add_cog(Pact(bot))