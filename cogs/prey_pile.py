import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.conditions import apply_meal_energy
from engine.prey_pile import PREY_CHOICES, apply_prey_choice, choice_outcome_message, format_response_summary
from utils.currency import format_bones
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, embed_footer, howlbert_embed, player_message, choice_label
BUTTON_STYLES = {'eat': discord.ButtonStyle.primary, 'share': discord.ButtonStyle.success, 'den': discord.ButtonStyle.secondary, 'guard': discord.ButtonStyle.secondary, 'pass': discord.ButtonStyle.secondary}

def build_prey_pile_embed(pile) -> discord.Embed:
    summary = db.get_prey_pile_response_summary(pile['id'])
    total = db.count_prey_pile_responses(pile['id'])
    embed = howlbert_embed('Fresh-kill Cache', f"**{pile['hunter_name']}** dragged **{pile['prey_label']}** to the clearing; fresh-kill for the den.\nThe haul is worth roughly **{format_bones(pile['prey_bones'])}**.\n\nElders, pups, and sick wolves eat first by custom. **How do you respond?**\n_Each wolf may respond once; pick a character if you own several._", color=SUCCESS_COLOR)
    embed.add_field(name='Responses', value=format_response_summary(summary), inline=False)
    embed.set_footer(text=embed_footer(f'{total} wolf(s) responded'))
    return embed

async def _apply_prey_choice(interaction: discord.Interaction, pile_id: int, choice: str, wolf, *, pile=None) -> None:
    pile = pile or db.get_prey_pile(pile_id)
    if not pile or pile['status'] != 'open':
        embed = howlbert_embed('Pile Gone', 'This prey pile has been cleared or the den rolled over.', color=ERROR_COLOR)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())
        else:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if db.get_prey_pile_response(pile_id, wolf['id']):
        embed = howlbert_embed('Already Chosen', f"**{wolf['wolf_name']}** already responded to this prey pile.", color=ERROR_COLOR)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())
        else:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if not interaction.response.is_done():
        await interaction.response.defer(thinking=False)
    effects = apply_prey_choice(choice, pile['prey_bones'])
    hp_gain = 0
    exhaustion_delta = 0
    hunger_gain = 0
    thirst_gain = 0
    if effects.get('restore_energy'):
        from engine.injury_effects import meal_jaw_pain_note
        from engine.hunger import meal_hunger_gain
        from engine.prey_items import prey_key_from_label
        from engine.thirst import meal_thirst_gain
        jaw_note = meal_jaw_pain_note(wolf)
        new_hp, new_exhaustion, hp_gain = apply_meal_energy(wolf, pile['prey_bones'])
        exhaustion_delta = new_exhaustion; int(wolf['exhaustion'])
        prey_key = prey_key_from_label(pile['prey_label'])
        if prey_key:
            hunger_gain = meal_hunger_gain(prey_key)
            thirst_gain = meal_thirst_gain(prey_key)
            db.adjust_hunger(wolf['id'], hunger_gain)
            db.adjust_thirst(wolf['id'], thirst_gain)
        db.set_user_conditions(wolf['discord_id'], wolf_id=wolf['id'], hp=new_hp, exhaustion=new_exhaustion)
    dispute_note = ''
    skirmish_id = None
    hunter = db.get_user_by_id(pile['hunter_wolf_id'])
    if hunter and hunter['id'] != wolf['id']:
        from engine.pack_relations import cross_pack_prey_dispute
        dispute_note, skirmish_id = cross_pack_prey_dispute(hunter, wolf, guild_id=interaction.guild.id if interaction.guild else pile['guild_id'], channel_id=interaction.channel_id if interaction.channel else pile['channel_id'], choice=choice)
    if effects.get('bones'):
        db.add_bones(wolf['discord_id'], effects['bones'], wolf_id=wolf['id'])
    if effects.get('standing'):
        db.adjust_wolf_standing_by_id(wolf['id'], effects['standing'])
    if effects.get('treasury_bones') and wolf['pack_id']:
        db.add_pack_treasury(wolf['pack_id'], effects['treasury_bones'])
        db.adjust_pack_unity(wolf['pack_id'], 1)
    if effects.get('quest_objective'):
        db.increment_quest_progress(wolf['discord_id'], effects['quest_objective'], wolf_id=wolf['id'], guild_id=interaction.guild.id if interaction.guild else None)
    db.record_prey_pile_response(pile_id, wolf['id'], wolf['wolf_name'], choice)
    outcome_body = choice_outcome_message(choice, bones=effects.get('bones', 0), standing=effects.get('standing', 0), treasury=effects.get('treasury_bones', 0), hp_gain=hp_gain, exhaustion_delta=exhaustion_delta, hunger_gain=hunger_gain, thirst_gain=thirst_gain)
    if effects.get('restore_energy'):
        from engine.prey_items import prey_key_from_label
        from engine.cannibalism import cannibalism_eat_consequences
        prey_key = prey_key_from_label(pile['prey_label'])
        if prey_key:
            outcome_body += cannibalism_eat_consequences(wolf, prey_key)
    if effects.get('treasury_bones') and wolf['pack_id']:
        from engine.pack_food import pack_treasury_pinch_line
        pinch = pack_treasury_pinch_line(wolf['pack_id'])
        if pinch:
            outcome_body += pinch
    if dispute_note:
        outcome_body += dispute_note
    if effects.get('restore_energy') and jaw_note:
        outcome_body += jaw_note
    result_embed = howlbert_embed(f"{wolf['wolf_name']}; Response", outcome_body, color=SUCCESS_COLOR)
    if interaction.response.is_done():
        await interaction.followup.send(embed=result_embed, ephemeral=reply_ephemeral())
    else:
        await interaction.response.send_message(embed=result_embed, ephemeral=reply_ephemeral())
    if skirmish_id and interaction.channel:
        from utils.combat_views import make_combat_view
        view = make_combat_view(skirmish_id, interaction.client)
        if view:
            await interaction.channel.send(embed=howlbert_embed('Fresh-Kill Skirmish', '_Hostile rivals contest the pile; combat is live._', color=ERROR_COLOR), view=view)
    if pile['message_id'] and interaction.channel:
        try:
            updated = db.get_prey_pile(pile_id)
            message = await interaction.channel.fetch_message(pile['message_id'])
            await message.edit(embed=build_prey_pile_embed(updated))
        except discord.HTTPException:
            pass

class PreyWolfSelect(discord.ui.Select):

    def __init__(self, pile_id: int, choice: str, wolves: list):
        self.pile_id = pile_id
        self.choice = choice
        options = [discord.SelectOption(label=choice_label(w['wolf_name']), value=str(w['id']), description='respond as this wolf') for w in wolves[:25]]
        super().__init__(placeholder='Which wolf responds?', options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        wolf_id = int(self.values[0])
        wolf = db.get_user_by_id(wolf_id)
        if not wolf or wolf['discord_id'] != interaction.user.id:
            await interaction.response.send_message(player_message("That wolf isn't yours."), ephemeral=reply_ephemeral())
            return
        await _apply_prey_choice(interaction, self.pile_id, self.choice, wolf)

class PreyWolfSelectView(discord.ui.View):

    def __init__(self, pile_id: int, choice: str, wolves: list):
        super().__init__(timeout=120)
        self.add_item(PreyWolfSelect(pile_id, choice, wolves))

def make_prey_pile_view(pile_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    for key, info in PREY_CHOICES.items():
        custom_id = f'fable_prey:{pile_id}:{key}'

        async def callback(interaction: discord.Interaction, *, choice=key, cid=custom_id):
            await PreyPileCog.handle_prey_choice(interaction, pile_id, choice)
        button = discord.ui.Button(label=info['label'], emoji=info['emoji'], style=BUTTON_STYLES.get(key, discord.ButtonStyle.secondary), custom_id=custom_id)
        button.callback = callback
        view.add_item(button)
    return view

async def post_prey_pile_to_channel(bot: commands.Bot, channel: discord.abc.Messageable, user, *, prey_bones: int, prey_label: str, day_number: int) -> int:
    """Post a fresh-kill cache message. Returns pile id."""
    guild_id = channel.guild.id if hasattr(channel, 'guild') and channel.guild else db.row_val(user, 'guild_id')
    if not guild_id:
        raise ValueError('channel must be in a guild')
    pile_id = db.create_prey_pile(guild_id=guild_id, channel_id=channel.id, hunter_wolf_id=user['id'], hunter_name=user['wolf_name'], prey_label=prey_label, prey_bones=prey_bones, day_number=day_number)
    db.update_user(user['discord_id'], wolf_id=user['id'], last_prey_pile_day=day_number, last_hunt_yield=prey_bones, last_prey_label=prey_label)
    embed = build_prey_pile_embed(db.get_prey_pile(pile_id))
    view = make_prey_pile_view(pile_id)
    message = await channel.send(embed=embed, view=view)
    db.set_prey_pile_message(pile_id, message.id)
    bot.add_view(view, message_id=message.id)
    return pile_id

async def open_prey_pile(interaction: discord.Interaction, bot: commands.Bot) -> None:
    """Lay out today's hunt at the den (shared by /preypile and hunt buttons)."""
    from engine.activities import preypile_error
    err = preypile_error(interaction)
    if err:
        embed = howlbert_embed("Can't Share", err, color=ERROR_COLOR)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())
        else:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    user = db.get_user(interaction.user.id)
    world = db.get_world(interaction.guild.id)
    day = world['day_number']
    stack = db.pick_prey_stack_for_pile(user['id'], day)
    if not stack:
        from engine.prey_storage import fresh_kill_pile_block_message
        rotting_msg = fresh_kill_pile_block_message(user['id'], day)
        if rotting_msg:
            embed = howlbert_embed("Can't Share", rotting_msg, color=ERROR_COLOR)
        else:
            embed = howlbert_embed("Can't Share", 'No fresh carcass in your hoard; hunt, track, or fish first.', color=ERROR_COLOR)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=reply_ephemeral())
        else:
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return
    if not interaction.response.is_done():
        await interaction.response.defer(thinking=False)
    from engine.prey_items import prey_meta
    meta = prey_meta(stack['prey_key'])
    prey_label = meta['label']
    prey_bones = stack['bone_value']
    prey_key = stack['prey_key']
    db.remove_prey_stack(stack['id'])
    await post_prey_pile_to_channel(bot, interaction.channel, user, prey_bones=prey_bones, prey_label=prey_label, day_number=day)
    from engine.cannibalism import cannibalism_public_exposure
    exposure = cannibalism_public_exposure(user, prey_key, action='preypile')
    pile_note = 'The cache is open; packmates can respond on the message above.'
    if exposure:
        pile_note = exposure.lstrip('\n') + '\n\n' + pile_note
    await interaction.followup.send(embed=howlbert_embed('Fresh-kill Laid Out', pile_note, color=SUCCESS_COLOR), ephemeral=reply_ephemeral())

class PreyPileCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        for pile in db.get_open_prey_piles():
            self.bot.add_view(make_prey_pile_view(pile['id']), message_id=pile['message_id'])

    @staticmethod
    async def handle_prey_choice(interaction: discord.Interaction, pile_id: int, choice: str) -> None:
        pile = db.get_prey_pile(pile_id)
        if not pile or pile['status'] != 'open':
            embed = howlbert_embed('Pile Gone', 'This prey pile has been cleared or the den rolled over.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not db.get_user(interaction.user.id):
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if choice not in PREY_CHOICES:
            await interaction.response.send_message(player_message('Unknown choice.'), ephemeral=reply_ephemeral())
            return
        available = db.wolves_available_for_prey_pile(interaction.user.id, pile_id)
        hunter = db.get_user_by_id(pile['hunter_wolf_id'])
        pile_pack_id = int(hunter['pack_id']) if hunter and hunter['pack_id'] else None
        if pile_pack_id:
            available = [w for w in available if w['pack_id'] and int(w['pack_id']) == pile_pack_id]
        if not available:
            embed = howlbert_embed('Already Chosen', 'Every wolf on your account has already responded to this prey pile.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if len(available) == 1:
            await _apply_prey_choice(interaction, pile_id, choice, available[0], pile=pile)
            return
        info = PREY_CHOICES[choice]
        view = PreyWolfSelectView(pile_id, choice, available)
        await interaction.response.send_message(embed=howlbert_embed('Choose Your Wolf', f"**{info['label']}**; which character responds?", color=SUCCESS_COLOR), view=view, ephemeral=reply_ephemeral())

    @app_commands.command(name='preypile', description='lay fresh-kill at the cache; packmates choose how to respond.')
    async def preypile(self, interaction: discord.Interaction):
        if not db.get_user(interaction.user.id):
            embed = howlbert_embed('Not Registered', 'Use `/register` first.', color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        await open_prey_pile(interaction, self.bot)

async def setup(bot: commands.Bot):
    await bot.add_cog(PreyPileCog(bot))