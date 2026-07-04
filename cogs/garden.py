"""Pack herb garden: sow seeds, tend plots, and harvest at the den."""
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from config import GARDEN_HARVEST_SEED_MAX, GARDEN_HARVEST_SEED_MIN, GARDEN_MAX_PLOTS, GARDEN_SEED_BONE_COST, GARDEN_TEND_HEALTH_RESTORE
from engine.herb_growing import can_cultivate, cultivable_herbs, evaluate_growth, growing_blurb, growing_profile, harvest_yield
from herbs import HERBS
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, choice_label
from utils.replies import reply_ephemeral
STAGE_ICONS = {'seed': '·', 'sprout': '🌱', 'growing': '🌿', 'mature': '🌼', 'wilted': '🥀', 'dead': '💀'}

def _herb_name(herb_key: str) -> str:
    meta = HERBS.get(herb_key, {})
    return meta.get('name', herb_key.replace('_', ' ').title())

def _tick(planting, season: str, day: int):
    """Evaluate one planting, persist any health/death changes, return result."""
    result, updates = evaluate_growth(herb_key=planting['herb_key'], planted_day=int(planting['planted_day']), last_tended_day=int(planting['last_tended_day']), last_eval_day=int(planting['last_eval_day']), health=int(planting['health']), season=season, current_day=day)
    if updates:
        db.update_herb_planting(planting['id'], **updates)
    return result

async def _need_user_guild(interaction: discord.Interaction):
    user = db.get_user(interaction.user.id)
    if not user:
        await interaction.response.send_message(embed=howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
        return (None, None)
    if not interaction.guild:
        await interaction.response.send_message(embed=howlbert_embed('Server Only', 'Use the garden in a server.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
        return (None, None)
    return (user, db.get_world(interaction.guild.id))

async def _need_pack_garden(interaction: discord.Interaction):
    user, world = await _need_user_guild(interaction)
    if not user:
        return (None, None, None)
    pack_id = user['pack_id'] if 'pack_id' in user.keys() else None
    if not pack_id:
        await interaction.response.send_message(embed=howlbert_embed('No Pack', 'The herb garden is a **pack** plot. Join a pack first (`/pack action:join`).', color=ERROR_COLOR), ephemeral=reply_ephemeral())
        return (None, None, None)
    pack = db.get_pack(pack_id)
    if not pack:
        await interaction.response.send_message(embed=howlbert_embed('No Pack', 'Your pack record is missing.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
        return (None, None, None)
    return (user, world, pack)

def _pack_owns_plot(pack, planting) -> bool:
    pid = pack['id']
    if 'pack_id' in planting.keys() and planting['pack_id']:
        return int(planting['pack_id']) == int(pid)
    planter = db.get_user_by_id(planting['wolf_id'])
    return planter and planter['pack_id'] == pid

async def _owned_seed_autocomplete(interaction, current: str):
    user = db.get_user(interaction.user.id)
    if not user:
        return []
    out = []
    for row in db.get_herb_seeds(user['id']):
        name = f"{_herb_name(row['herb_key'])} seeds x{row['qty']}"
        if current and current.lower() not in name.lower() and (current.lower() not in row['herb_key']):
            continue
        out.append(app_commands.Choice(name=choice_label(name), value=row['herb_key']))
    return out[:25]

async def _cultivable_autocomplete(interaction, current: str):
    out = []
    for key in cultivable_herbs():
        name = _herb_name(key)
        if current and current.lower() not in name.lower() and (current.lower() not in key):
            continue
        out.append(app_commands.Choice(name=choice_label(f'{name} ({key})'), value=key))
    return out[:25]

class Garden(commands.Cog):
    garden = app_commands.Group(name='garden', description='pack herb garden; sow seeds, tend plots, and harvest.')

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @garden.command(name='plots', description="view your pack's herb garden and its growth.")
    async def plots(self, interaction: discord.Interaction):
        user, world, pack = await _need_pack_garden(interaction)
        if not user:
            return
        day, season = (world['day_number'], world['season'])
        plantings = db.get_pack_herb_plantings(pack['id'])
        if not plantings:
            await interaction.response.send_message(embed=howlbert_embed('Empty Garden', f"**{pack['name']}** has no herb plots yet. Forage or `/garden buy` for seeds, then `/garden plant`.", color=SUCCESS_COLOR), ephemeral=reply_ephemeral())
            return
        lines = []
        for p in plantings:
            res = _tick(p, season, day)
            icon = STAGE_ICONS.get(res.stage, '·')
            planter = db.get_user_by_id(p['wolf_id'])
            who = planter['wolf_name'] if planter else 'a packmate'
            if res.dead:
                lines.append(f"{icon} `#{p['id']}` **{_herb_name(p['herb_key'])}**; dead ({res.note}) · {who}")
            elif res.ready:
                lines.append(f"{icon} `#{p['id']}` **{_herb_name(p['herb_key'])}**; ready to harvest! · {who}")
            else:
                lines.append(f"{icon} `#{p['id']}` **{_herb_name(p['herb_key'])}**; {res.progress_pct}% · HP {res.health} · {res.note} · planted by {who}")
        body = '\n'.join(lines)
        embed = howlbert_embed(f"{pack['name']} Herb Garden", body, color=SUCCESS_COLOR)
        embed.set_footer(text=f'season: {season} · /garden tend · /garden harvest · {len(plantings)}/{GARDEN_MAX_PLOTS} plots')
        await interaction.response.send_message(embed=embed)

    @garden.command(name='seeds', description='show your seed pouch and where to get more.')
    async def seeds(self, interaction: discord.Interaction):
        user, world = await _need_user_guild(interaction)
        if not user:
            return
        rows = db.get_herb_seeds(user['id'])
        if not rows:
            body = f'Your seed pouch is empty.\n\nGet seeds by **foraging** (`/field action:forage`), buying a packet (`/garden buy`, **{GARDEN_SEED_BONE_COST} bones**), or **harvesting** a mature plant (keeps seeds for next time). Seeds are yours; plots belong to the pack.'
        else:
            body = '\n'.join((f"**{_herb_name(r['herb_key'])}** ×{r['qty']}; {growing_blurb(r['herb_key'])}" for r in rows))
        embed = howlbert_embed('Seed Pouch', body, color=SUCCESS_COLOR)
        embed.set_footer(text='/garden plant herb:<name> · /garden guide')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @garden.command(name='plant', description='sow a seed from your pouch into the pack garden.')
    @app_commands.describe(herb='which seed to sow')
    @app_commands.autocomplete(herb=_owned_seed_autocomplete)
    async def plant(self, interaction: discord.Interaction, herb: str):
        user, world, pack = await _need_pack_garden(interaction)
        if not user:
            return
        herb = herb.strip().lower()
        if not can_cultivate(herb):
            await interaction.response.send_message(embed=howlbert_embed("Can't Sow That", "That herb can't be grown in a garden.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if db.count_pack_herb_plantings(pack['id']) >= GARDEN_MAX_PLOTS:
            await interaction.response.send_message(embed=howlbert_embed('Garden Full', f"**{pack['name']}** can tend **{GARDEN_MAX_PLOTS}** plots at once. Harvest or clear one first.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if db.get_herb_seed_qty(user['id'], herb) <= 0:
            await interaction.response.send_message(embed=howlbert_embed('No Seeds', f'You have no **{_herb_name(herb)}** seeds. Try `/garden buy` or forage for some.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        day, season = (world['day_number'], world['season'])
        db.consume_herb_seed(user['id'], herb, 1)
        pid = db.add_herb_planting(user['id'], herb, pack_id=pack['id'], guild_id=interaction.guild.id, day=day, season=season)
        profile = growing_profile(herb)
        warn = ''
        if season not in profile.seasons:
            warn = "\n\n_⚠ Off-season sowing; it'll grow slowly_" if profile.hardy else '\n\n_⚠ Wrong season; it may struggle or die_'
        embed = howlbert_embed('Seed Sown', f"**{user['wolf_name']}** presses a **{_herb_name(herb)}** seed into **{pack['name']}**'s plot `#{pid}`.\n\n{growing_blurb(herb)}{warn}\n\n_Sowing isn't tending; water it with `/garden tend`._", color=SUCCESS_COLOR)
        embed.set_footer(text='/garden tend each sunrise · /garden plots')
        await interaction.response.send_message(embed=embed)

    @garden.command(name='tend', description='water and weed the pack garden (any wolf, any number of times).')
    async def tend(self, interaction: discord.Interaction):
        user, world, pack = await _need_pack_garden(interaction)
        if not user:
            return
        day, season = (world['day_number'], world['season'])
        plantings = db.get_pack_herb_plantings(pack['id'])
        living = [p for p in plantings if not p['dead']]
        if not living:
            await interaction.response.send_message(embed=howlbert_embed('Nothing to Tend', f"**{pack['name']}** has no living plots. Sow a seed with `/garden plant`.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        tended = 0
        for p in living:
            _tick(p, season, day)
            fresh = db.get_herb_planting(p['id'])
            if not fresh or fresh['dead']:
                continue
            new_health = min(100, int(fresh['health']) + GARDEN_TEND_HEALTH_RESTORE)
            db.update_herb_planting(p['id'], last_tended_day=day, last_eval_day=day, health=new_health)
            tended += 1
        db.mark_pack_garden_tended(pack['id'], day)
        body = f"**{user['wolf_name']}** waters and weeds **{pack['name']}**'s garden (**{tended}** plot(s))."
        await interaction.response.send_message(embed=howlbert_embed('Garden Tended', body, color=SUCCESS_COLOR))

    @garden.command(name='harvest', description='harvest mature plants (all ready, or one plot).')
    @app_commands.describe(plot='optional plot number to harvest')
    async def harvest(self, interaction: discord.Interaction, plot: int | None=None):
        user, world, pack = await _need_pack_garden(interaction)
        if not user:
            return
        day, season = (world['day_number'], world['season'])
        plantings = db.get_pack_herb_plantings(pack['id'])
        if plot is not None:
            plantings = [p for p in plantings if p['id'] == plot]
            if not plantings:
                await interaction.response.send_message(embed=howlbert_embed('No Such Plot', f"Plot `#{plot}` isn't in **{pack['name']}**'s garden.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
        from engine.herb_storage import grant_fresh_herb
        harvested, cleared, lines = (0, 0, [])
        for p in plantings:
            res = _tick(p, season, day)
            if res.dead:
                db.remove_herb_planting(p['id'])
                cleared += 1
                lines.append(f"💀 Cleared dead **{_herb_name(p['herb_key'])}** (plot `#{p['id']}`).")
                continue
            if not res.ready:
                continue
            profile = growing_profile(p['herb_key'])
            count = harvest_yield(profile, res.health)
            for _ in range(count):
                grant_fresh_herb(user['id'], herb_key=p['herb_key'], guild_id=interaction.guild.id, day=day, user=user)
            seeds_back = max(GARDEN_HARVEST_SEED_MIN, GARDEN_HARVEST_SEED_MAX if res.health >= 80 else GARDEN_HARVEST_SEED_MIN)
            db.add_herb_seeds(user['id'], p['herb_key'], seeds_back)
            db.remove_herb_planting(p['id'])
            harvested += 1
            lines.append(f"🌼 **{_herb_name(p['herb_key'])}**; {count} fresh stack(s) + {seeds_back} seed(s) to your pouch.")
        if not lines:
            await interaction.response.send_message(embed=howlbert_embed('Nothing Ready', 'No plots are mature yet. Check `/garden plots` and keep tending.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        title = 'Harvest' if harvested else 'Garden Cleared'
        embed = howlbert_embed(title, '\n'.join(lines), color=SUCCESS_COLOR)
        embed.set_footer(text='fresh herbs go to your bag; dry them with `/herbs action:dryall`.')
        await interaction.response.send_message(embed=embed)

    @garden.command(name='clear', description='pull up a plot (dead or unwanted).')
    @app_commands.describe(plot='plot number to clear')
    async def clear(self, interaction: discord.Interaction, plot: int):
        user, world, pack = await _need_pack_garden(interaction)
        if not user:
            return
        target = db.get_herb_planting(plot)
        if not target or not _pack_owns_plot(pack, target):
            await interaction.response.send_message(embed=howlbert_embed('No Such Plot', f"Plot `#{plot}` isn't in **{pack['name']}**'s garden.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.remove_herb_planting(plot)
        await interaction.response.send_message(embed=howlbert_embed('Plot Cleared', f"**{user['wolf_name']}** pulls up the **{_herb_name(target['herb_key'])}** in plot `#{plot}`.", color=SUCCESS_COLOR))

    @garden.command(name='buy', description=f'Buy a seed packet ({GARDEN_SEED_BONE_COST} bones).')
    @app_commands.describe(herb='which herb seeds to buy')
    @app_commands.autocomplete(herb=_cultivable_autocomplete)
    async def buy(self, interaction: discord.Interaction, herb: str):
        user, world = await _need_user_guild(interaction)
        if not user:
            return
        herb = herb.strip().lower()
        if not can_cultivate(herb):
            await interaction.response.send_message(embed=howlbert_embed('Unavailable', "Those seeds aren't sold here.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not db.deduct_bones(interaction.user.id, GARDEN_SEED_BONE_COST):
            await interaction.response.send_message(embed=howlbert_embed('Not Enough Bones', f'Seed packets cost **{GARDEN_SEED_BONE_COST} bones**.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.add_herb_seeds(user['id'], herb, 1)
        embed = howlbert_embed('Seeds Bought', f'You trade **{GARDEN_SEED_BONE_COST} bones** for a packet of **{_herb_name(herb)}** seeds.\n\n{growing_blurb(herb)}', color=SUCCESS_COLOR)
        embed.set_footer(text='/garden plant herb:' + herb)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @garden.command(name='guide', description='growing conditions for cultivable herbs.')
    @app_commands.describe(herb='optional herb to look up')
    @app_commands.autocomplete(herb=_cultivable_autocomplete)
    async def guide(self, interaction: discord.Interaction, herb: str | None=None):
        if herb:
            herb = herb.strip().lower()
            if not can_cultivate(herb):
                await interaction.response.send_message(embed=howlbert_embed('Not Cultivable', 'That herb is foraged from the wild, not grown.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            meta = HERBS.get(herb, {})
            body = f"{growing_blurb(herb)}\n\n_{meta.get('effect', '')}_"
            embed = howlbert_embed(f'Growing {_herb_name(herb)}', body, color=SUCCESS_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        keys = cultivable_herbs()[:40]
        lines = [f'**{_herb_name(k)}**; {growing_blurb(k)}' for k in keys]
        embed = howlbert_embed('Herb Growing Guide', '\n'.join(lines), color=SUCCESS_COLOR)
        embed.set_footer(text='/garden guide herb:<name> for one herb · /garden buy · /garden plant')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

async def setup(bot: commands.Bot):
    await bot.add_cog(Garden(bot))