import re
import logging
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.activities import accept_quest, complete_quest
from utils.currency import format_bones
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label
from utils.permissions import is_howlbert_admin
from utils.views import make_quest_accept_view, make_quest_complete_view
QUEST_OBJECTIVES = ('hunt', 'scavenge', 'track', 'fishing', 'forage', 'treat', 'patrol', 'deposit', 'explore', 'survey', 'trail', 'sniff', 'howl', 'crime')
QUEST_KEY_RE = re.compile('^[a-z0-9_]{2,32}$')
logger = logging.getLogger(__name__)

class Quests(commands.Cog):
    questadmin = app_commands.Group(name='questadmin', description='admin; post and manage den board quests.')

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _require_admin(self, interaction: discord.Interaction) -> bool:
        if is_howlbert_admin(interaction):
            return True
        embed = howlbert_embed('Denied', 'Admins only.', color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return False

    def _guild_day(self, interaction: discord.Interaction) -> int | None:
        if not interaction.guild:
            return None
        return db.get_world(interaction.guild.id)['day_number']

    @app_commands.command(name='quest', description='den board; view, accept, progress, complete, abandon, daily, or log.')
    @app_commands.describe(action='board, daily, accept, progress, complete, abandon, or log', quest='quest key (for accept, complete, abandon)')
    @app_commands.choices(action=[app_commands.Choice(name='view board', value='board'), app_commands.Choice(name='daily quests', value='daily'), app_commands.Choice(name='accept', value='accept'), app_commands.Choice(name='progress', value='progress'), app_commands.Choice(name='complete', value='complete'), app_commands.Choice(name='abandon', value='abandon'), app_commands.Choice(name='quest log', value='log')])
    async def quest(self, interaction: discord.Interaction, action: str, quest: str | None=None):
        if action == 'board':
            await self._quests_board(interaction)
        elif action == 'daily':
            await self._dailyquests(interaction)
        elif action == 'accept':
            if not quest:
                await interaction.response.send_message(player_message('Provide a `quest` key.'), ephemeral=reply_ephemeral())
                return
            await self._accept(interaction, quest)
        elif action == 'progress':
            await self._progress(interaction)
        elif action == 'complete':
            await self._complete(interaction, quest)
        elif action == 'abandon':
            if not quest:
                await interaction.response.send_message(player_message('Provide a `quest` key.'), ephemeral=reply_ephemeral())
                return
            await self._abandon(interaction, quest)
        elif action == 'log':
            await self._questlog(interaction)

    async def _quests_board(self, interaction: discord.Interaction):
        if not db.get_user(interaction.user.id):
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        rows = db.get_available_quests(interaction.user.id, guild_id=interaction.guild.id if interaction.guild else None)
        if not rows:
            embed = howlbert_embed('Den Board', 'No new quests on the board right now.')
            await interaction.response.send_message(embed=embed)
            return
        embed = howlbert_embed('Den Board', 'Accept a quest with the buttons below.')
        from engine.quest_rewards import format_quest_reward_line
        for q in rows[:10]:
            reward_line = format_quest_reward_line(q['key'], q['reward_bones'], difficulty=q['difficulty'])
            embed.add_field(name=f"{q['title']} ({q['difficulty']}); {reward_line}", value=f"`{q['key']}`; {q['description']}", inline=False)
        embed.set_footer(text='/quest action:progress · rewards grant automatically when the objective is finished · buttons accept below')
        view = make_quest_accept_view(rows[:10])
        await interaction.response.send_message(embed=embed, view=view)

    async def _dailyquests(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id)
        if not user:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        day = self._guild_day(interaction)
        if day is None:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        rows = db.ensure_daily_quests(interaction.user.id, day)
        from engine.quest_rewards import format_quest_reward_line
        embed = howlbert_embed(f'Daily Quests; Day {day}')
        for q in rows:
            status = 'done' if q['status'] == 'completed' else f"{q['progress']}/{q['objective_count']}"
            key = q['quest_key'] if 'quest_key' in q.keys() else q['key']
            reward_line = format_quest_reward_line(key, q['reward_bones'], difficulty=q['difficulty'])
            embed.add_field(name=f"[{q['difficulty'].title()}] {q['title']}; {reward_line}", value=f"{q['description']}\nProgress: **{status}**", inline=False)
        embed.set_footer(text='daily quests reset each sunrise · +1 xp default · hard dailies +2 xp')
        await interaction.response.send_message(embed=embed)

    async def _accept(self, interaction: discord.Interaction, quest: str):
        embed = accept_quest(interaction, quest)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _progress(self, interaction: discord.Interaction):
        rows = db.get_user_active_quests(interaction.user.id)
        if not rows:
            embed = howlbert_embed('Quest Log', 'No active quests.')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Active Quests')
        from engine.quest_rewards import format_quest_reward_suffix
        trophies = [q for q in rows if q['quest_type'] == 'achievement']
        quests = [q for q in rows if q['quest_type'] != 'achievement']
        for q in quests:
            extra = format_quest_reward_suffix(q['quest_key'], difficulty=q['difficulty'] if 'difficulty' in q.keys() else None)
            reward_note = f"\nRewards: {format_bones(q['reward_bones'])}"
            if extra:
                reward_note += f' · {extra}'
            embed.add_field(name=q['title'], value=f"{q['progress']}/{q['objective_count']} ({q['objective_type']})\n`{q['quest_key']}`{reward_note}", inline=False)
        if trophies:
            lines = [f"**{t['title']}**; {t['progress']}/{t['objective_count']}" for t in trophies]
            embed.add_field(name='Trophies in progress', value='\n'.join(lines), inline=False)
        embed.set_footer(text='rewards grant automatically when finished · abandon with action:abandon quest:<key> · trophies never expire')
        view = make_quest_complete_view(rows)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=reply_ephemeral())

    async def _complete(self, interaction: discord.Interaction, quest: str | None=None):
        embed = complete_quest(interaction, quest)
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _abandon(self, interaction: discord.Interaction, quest: str):
        if not db.abandon_quest(interaction.user.id, quest):
            embed = howlbert_embed("Can't Abandon", 'No active quest with that key.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Quest Abandoned', 'The den board will wait.', color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    async def _questlog(self, interaction: discord.Interaction):
        rows = db.get_user_questlog(interaction.user.id)
        if not rows:
            embed = howlbert_embed('Quest Log', 'No completed quests yet.')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        from engine.quest_rewards import format_quest_reward_line
        lines = [f"**{r['title']}**; {format_quest_reward_line(r['quest_key'], r['reward_bones'], difficulty=r['difficulty'])} ({r['difficulty']})" for r in rows]
        embed = howlbert_embed('Quest Log', '\n'.join(lines))
        embed.set_footer(text='/quest action:board · action:daily')
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @questadmin.command(name='create', description='post a new quest on the den board.')
    @app_commands.describe(key='unique id (e.g. moon_hunt); lowercase, no spaces', title='quest name shown on the board', description='what the wolf must do', objective='what action completes the quest', count='how many times', reward='bone reward', standing='standing reward (optional)', quest_type='static = repeatable per wolf after abandon; unique = once ever', difficulty='easy, medium, or hard')
    @app_commands.choices(objective=[app_commands.Choice(name=o, value=o) for o in QUEST_OBJECTIVES], quest_type=[app_commands.Choice(name='static (repeatable)', value='static'), app_commands.Choice(name='unique (one-time)', value='unique'), app_commands.Choice(name='seasonal', value='seasonal')], difficulty=[app_commands.Choice(name='easy', value='easy'), app_commands.Choice(name='medium', value='medium'), app_commands.Choice(name='hard', value='hard')])
    async def questadmin_create(self, interaction: discord.Interaction, key: str, title: str, description: str, objective: str, count: app_commands.Range[int, 1, 99], reward: app_commands.Range[int, 1, 9999], standing: app_commands.Range[int, 0, 100]=0, quest_type: str='static', difficulty: str='easy'):
        if not await self._require_admin(interaction):
            return
        key = key.strip().lower()
        if not QUEST_KEY_RE.match(key):
            embed = howlbert_embed('Invalid Key', 'Use 2-32 characters: lowercase letters, numbers, underscores only.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if db.get_quest_by_key(key):
            embed = howlbert_embed('Key Taken', f'`{key}` already exists.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if len(title.strip()) < 2 or len(description.strip()) < 5:
            embed = howlbert_embed('Too Short', 'Title and description need more detail.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        try:
            db.create_quest(key, title, description, objective, count, reward, standing_reward=standing, quest_type=quest_type, difficulty=difficulty)
        except Exception:
            logger.exception('questadmin create_quest failed key=%s', key)
            embed = howlbert_embed('Failed', 'Could not create quest.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Quest Posted', color=SUCCESS_COLOR)
        embed.add_field(name='Key', value=f'`{key}`', inline=True)
        embed.add_field(name='Objective', value=f'{objective} x{count}', inline=True)
        embed.add_field(name='Reward', value=format_bones(reward), inline=True)
        embed.set_footer(text='wolves can `/quest action:accept` and `/quest action:complete` now.')
        await interaction.response.send_message(embed=embed)

    @questadmin.command(name='list', description='list all den board quests (admin).')
    async def questadmin_list(self, interaction: discord.Interaction):
        if not await self._require_admin(interaction):
            return
        rows = db.list_board_quests()
        if not rows:
            embed = howlbert_embed('Den Board', 'No quests posted.')
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('All Board Quests')
        for q in rows[:15]:
            embed.add_field(name=f"`{q['key']}`; {q['title']}", value=f"{q['objective_type']} x{q['objective_count']} · {format_bones(q['reward_bones'])} · {q['quest_type']}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

    @questadmin.command(name='remove', description='remove a quest from the den board.')
    @app_commands.describe(key='quest key to remove')
    async def questadmin_remove(self, interaction: discord.Interaction, key: str):
        if not await self._require_admin(interaction):
            return
        if not db.delete_quest_by_key(key):
            embed = howlbert_embed("Can't Remove", 'Quest not found, or a wolf still has it active. Use `/quest action:abandon` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        embed = howlbert_embed('Quest Removed', f'`{key.strip().lower()}` cleared from the board.', color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())

async def setup(bot: commands.Bot):
    await bot.add_cog(Quests(bot))