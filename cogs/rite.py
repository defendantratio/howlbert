"""Pack ceremonies: naming, blooding, mourning."""
from __future__ import annotations
import logging
import discord
from discord import app_commands
from discord.ext import commands
import database as db
from engine.blooding import is_unblooded_juvenile
from engine.mirewort_burial import is_mirewort, mirewort_grave_rite
from engine.wolf_journal import log_blooded, log_rite
from utils.embeds import EMBED_COLOR, ERROR_COLOR, SUCCESS_COLOR, howlbert_embed, player_message, choice_label
from utils.permissions import is_howlbert_admin
from utils.replies import reply_ephemeral
from utils.wolf_autocomplete import make_member_wolf_autocomplete
logger = logging.getLogger('howlbert')

def _active_wolf(interaction: discord.Interaction):
    return db.get_user(interaction.user.id)

def _world_day(guild_id: int) -> int | None:
    world = db.get_world(guild_id)
    return int(world['day_number']) if world else None

_accused_wolf_autocomplete = make_member_wolf_autocomplete("accused")

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

class Rite(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    rite = app_commands.Group(name='rite', description='den ceremonies and rites.')

    @rite.command(name='naming', description='name a pup or youth in a den ceremony.')
    @app_commands.describe(wolf="the pup being named (your wolf or another member's)", words='optional words spoken at the rite')
    async def naming(self, interaction: discord.Interaction, wolf: str, words: str | None=None):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        actor = _active_wolf(interaction)
        if not actor:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        target_row = db.get_wolf_by_name(wolf)
        if not target_row:
            await interaction.response.send_message(embed=howlbert_embed('Not Found', 'No wolf by that name.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from config import PUP_MAX_MOONS
        age = int(target_row['age_months']) if 'age_months' in target_row.keys() else 24
        if age >= PUP_MAX_MOONS and (not ('is_born_pup' in target_row.keys() and target_row['is_born_pup'])):
            await interaction.response.send_message(embed=howlbert_embed('Too Old', 'Naming rites are for pups and very young wolves.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if target_row['discord_id'] != interaction.user.id and (not is_howlbert_admin(interaction)):
            await interaction.response.send_message(embed=howlbert_embed('Not Yours', "You can only hold a naming rite for your own pup unless you're admin.", color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        day = _world_day(interaction.guild.id)
        speech = words.strip() if words else '_The den speaks the name aloud._'
        embed = howlbert_embed(f"🌿 Naming Rite; {target_row['wolf_name']}", f"**{actor['wolf_name']}** leads the den in naming **{target_row['wolf_name']}**.\n\n{speech}", color=SUCCESS_COLOR)
        log_rite(target_row['id'], 'rite_naming', f"Naming rite led by **{actor['wolf_name']}**.", guild_id=interaction.guild.id, day=day)
        await interaction.response.send_message(embed=embed)

    @rite.command(name='blooding', description='hold a blooding ceremony for a juvenile.')
    @app_commands.describe(wolf='the juvenile (defaults to your active wolf)', words='optional words at the rite')
    async def blooding(self, interaction: discord.Interaction, wolf: str | None=None, words: str | None=None):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        actor = _active_wolf(interaction)
        if not actor:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if wolf:
            target = db.get_wolf_by_name(wolf)
        else:
            target = actor
        if not target:
            await interaction.response.send_message(embed=howlbert_embed('Not Found', 'No wolf by that name.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if target['discord_id'] != interaction.user.id and (not is_howlbert_admin(interaction)):
            await interaction.response.send_message(embed=howlbert_embed('Not Yours', 'You can only rite your own wolf.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if is_unblooded_juvenile(target) or not ('has_blooding' in target.keys() and target['has_blooding']):
            await interaction.response.send_message(embed=howlbert_embed('Not Yet', 'They must earn blooding on a hunt first (`/bones action:hunt`), then hold the rite.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        day = _world_day(interaction.guild.id)
        speech = words.strip() if words else '_Blood on muzzle, name on the wind; the den witnesses._'
        embed = howlbert_embed(f"🩸 Blooding Rite; {target['wolf_name']}", f"**{actor['wolf_name']}** calls the pack to witness **{target['wolf_name']}**'s blooding.\n\n{speech}", color=EMBED_COLOR)
        log_blooded(target['id'], target['wolf_name'], ceremonial=True)
        await interaction.response.send_message(embed=embed)

    @rite.command(name='mourning', description='hold a mourning rite for a fallen wolf.')
    @app_commands.describe(wolf='name of the wolf being mourned', words='optional words at the rite')
    async def mourning(self, interaction: discord.Interaction, wolf: str, words: str | None=None):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        actor = _active_wolf(interaction)
        if not actor:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        target = db.get_wolf_by_name(wolf)
        if not target:
            await interaction.response.send_message(embed=howlbert_embed('Not Found', 'No wolf by that name.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if target['condition'] != 'dead':
            await interaction.response.send_message(embed=howlbert_embed('Still Living', 'Mourning rites are for wolves who have passed.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        day = _world_day(interaction.guild.id)
        cause = target['cause_of_death'] if 'cause_of_death' in target.keys() else 'unknown'
        journal_note = f"Mourning rite led by **{actor['wolf_name']}**."
        if is_mirewort(actor):
            speech, grave_journal = mirewort_grave_rite(target['wolf_name'], custom_words=words)
            journal_note = f'{journal_note} {grave_journal}'
        else:
            speech = words.strip() if words else '_The den sits in silence._'
        embed = howlbert_embed(f"🕯 Mourning; {target['wolf_name']}", f"**{actor['wolf_name']}** leads mourning for **{target['wolf_name']}** _(died of {cause})_.\n\n{speech}", color=EMBED_COLOR)
        log_rite(target['id'], 'rite_mourning', journal_note, guild_id=interaction.guild.id, day=day)
        await interaction.response.send_message(embed=embed)

    @rite.command(name='trial', description='trial by combat to settle an accusation; the loser pays, win or lose as the accuser.')
    @app_commands.describe(accused='the wolf you accuse', claim='what you accuse them of', accused_wolf="specific wolf from that player's roster", own_accused='your other wolf to put on trial')
    @app_commands.autocomplete(own_accused=_other_wolf_autocomplete, accused_wolf=_accused_wolf_autocomplete)
    async def trial(self, interaction: discord.Interaction, accused: discord.Member | None, claim: str, accused_wolf: str | None = None, own_accused: str | None = None):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        accuser = _active_wolf(interaction)
        if not accuser:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        if accused and own_accused:
            await interaction.response.send_message(embed=howlbert_embed('Pick One', 'Use `accused` or `own_accused`; not both.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if not accused and not own_accused:
            await interaction.response.send_message(embed=howlbert_embed('Pick an Accused', 'Specify `accused` or `own_accused`.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if own_accused:
            rows = db.list_user_wolves(interaction.user.id)
            accused_row = next((w for w in rows if w['wolf_name'].lower() == own_accused.strip().lower() and w['id'] != accuser['id']), None)
            if not accused_row:
                await interaction.response.send_message(embed=howlbert_embed('Unknown Wolf', f'No wolf named **{own_accused}** on your account.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
        else:
            if accused.bot or accused.id == interaction.user.id:
                await interaction.response.send_message(embed=howlbert_embed('Pick Another Wolf', 'You cannot put yourself on trial.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
                return
            if accused_wolf:
                accused_row = db.find_user_wolf(accused.id, accused_wolf)
            else:
                accused_row = db.get_user(accused.id)
            if not accused_row:
                await interaction.response.send_message(player_message("They haven't registered a wolf."), ephemeral=reply_ephemeral())
                return

        from engine.dice import roll_d20
        from engine.character import attr_modifier
        from engine.character_traits import trait_combat_modifier

        def _trial_roll(wolf) -> tuple[int, dict]:
            die = roll_d20()
            mod = max(attr_modifier(int(wolf['attr_str'])), attr_modifier(int(wolf['attr_dex'])))
            trait_mod = trait_combat_modifier(wolf)
            total = die + mod + trait_mod
            return total, {'die': die, 'mod': mod, 'trait_mod': trait_mod}

        a_total, a_detail = _trial_roll(accuser)
        b_total, b_detail = _trial_roll(accused_row)
        note = ''
        if a_detail['die'] == 20 and b_detail['die'] != 20:
            winner, loser = accuser, accused_row
            note = ' (critical)'
        elif b_detail['die'] == 20 and a_detail['die'] != 20:
            winner, loser = accused_row, accuser
            note = ' (critical)'
        elif a_detail['die'] == 1 and b_detail['die'] != 1:
            winner, loser = accused_row, accuser
            note = ' (fumble)'
        elif b_detail['die'] == 1 and a_detail['die'] != 1:
            winner, loser = accuser, accused_row
            note = ' (fumble)'
        elif a_total >= b_total:
            winner, loser = accuser, accused_row
        else:
            winner, loser = accused_row, accuser

        from config import TRIAL_BY_COMBAT_LOSER_STANDING
        kick = db.adjust_wolf_standing_by_id(loser['id'], TRIAL_BY_COMBAT_LOSER_STANDING)
        standing_note = '**cast out**' if kick == 'kicked' else f'standing **{TRIAL_BY_COMBAT_LOSER_STANDING}**'
        day = _world_day(interaction.guild.id)
        body = (
            f"**{accuser['wolf_name']}** accuses **{accused_row['wolf_name']}**: _{claim.strip()[:200]}_\n\n"
            f"the den calls a trial by combat to settle it.\n"
            f"**{accuser['wolf_name']}** {a_total} vs **{accused_row['wolf_name']}** {b_total}{note}\n\n"
            f"**{winner['wolf_name']}** wins; the den sides with them. "
            f"**{loser['wolf_name']}** carries the loss; {standing_note}."
        )
        log_rite(winner['id'], 'rite_trial', f"Won a trial by combat against **{loser['wolf_name']}**.", guild_id=interaction.guild.id, day=day)
        log_rite(loser['id'], 'rite_trial', f"Lost a trial by combat against **{winner['wolf_name']}**.", guild_id=interaction.guild.id, day=day)
        embed = howlbert_embed('⚔ Trial by Combat', body, color=SUCCESS_COLOR if winner['id'] == accuser['id'] else ERROR_COLOR)
        await interaction.response.send_message(embed=embed)

    @rite.command(name='bone_gift', description='offer a bone-gift to a wolf you are courting (+5 mood, costs 3 bones).')
    @app_commands.describe(wolf='the wolf receiving the bone-gift')
    async def bone_gift(self, interaction: discord.Interaction, wolf: str):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        actor = _active_wolf(interaction)
        if not actor:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        target = db.get_wolf_by_name(wolf)
        if not target:
            await interaction.response.send_message(embed=howlbert_embed('Not Found', f'No wolf named **{wolf}**.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        if target['id'] == actor['id']:
            await interaction.response.send_message(embed=howlbert_embed('Cannot Self-Gift', 'You cannot offer a bone-gift to yourself.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        target_condition = target['condition'] if 'condition' in target.keys() else 'healthy'
        if target_condition in ('dead', 'dying'):
            await interaction.response.send_message(embed=howlbert_embed('Cannot Gift', f'**{target["wolf_name"]}** cannot receive a gift right now.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from config import BONE_GIFT_COST, BONE_GIFT_MOOD_GAIN
        actor_bones = int(actor['bones']) if 'bones' in actor.keys() else 0
        if actor_bones < BONE_GIFT_COST:
            await interaction.response.send_message(embed=howlbert_embed('Not Enough Bones', f'A bone-gift requires **{BONE_GIFT_COST} bones**; you have **{actor_bones}**.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.deduct_bones(interaction.user.id, BONE_GIFT_COST)
        new_mood = db.adjust_mood(target['id'], BONE_GIFT_MOOD_GAIN)
        new_favor = db.adjust_maw_favor(interaction.user.id, 1)
        day = _world_day(interaction.guild.id)
        log_rite(actor['id'], 'rite_bone_gift', f"Offered a bone-gift to **{target['wolf_name']}**.", guild_id=interaction.guild.id, day=day)
        body = (
            f"**{actor['wolf_name']}** lays a careful gift of bones before **{target['wolf_name']}**.\n"
            f"_An offering carried in the teeth, set gently at their paws._\n\n"
            f"**{target['wolf_name']}** mood: +{BONE_GIFT_MOOD_GAIN} → **{new_mood}** · "
            f"Maw Favor: +1 → **{new_favor}**"
        )
        embed = howlbert_embed('Bone-Gift', body, color=SUCCESS_COLOR)
        embed.set_footer(text=f"costs {BONE_GIFT_COST} bones · remaining: {actor_bones - BONE_GIFT_COST}")
        await interaction.response.send_message(embed=embed)

    @rite.command(name='joining_howl', description='announce your bond to the pack with a joining howl (+1 maw_favor each, once per pair).')
    async def joining_howl(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        actor = _active_wolf(interaction)
        if not actor:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        bonded_mate = db.get_bonded_mate(actor)
        if not bonded_mate:
            await interaction.response.send_message(embed=howlbert_embed('No Bonded Mate', 'A joining howl requires a bonded mate. Mate first, then howl.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        actor_done = int(actor['joining_howl_done']) if 'joining_howl_done' in actor.keys() else 0
        mate_done = int(bonded_mate['joining_howl_done']) if 'joining_howl_done' in bonded_mate.keys() else 0
        if actor_done or mate_done:
            await interaction.response.send_message(embed=howlbert_embed('Already Howled', f'**{actor["wolf_name"]}** and **{bonded_mate["wolf_name"]}** have already announced their bond. The pack heard it.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.set_joining_howl_done(actor['id'], bonded_mate['id'])
        favor_a = db.adjust_maw_favor(interaction.user.id, 1)
        mate_discord_id = int(bonded_mate['discord_id']) if 'discord_id' in bonded_mate.keys() and bonded_mate['discord_id'] else None
        favor_b = db.adjust_maw_favor(mate_discord_id, 1) if mate_discord_id else None
        pack_note = ''
        actor_pack = int(actor['pack_id']) if 'pack_id' in actor.keys() and actor['pack_id'] else None
        mate_pack = int(bonded_mate['pack_id']) if 'pack_id' in bonded_mate.keys() and bonded_mate['pack_id'] else None
        if actor_pack and actor_pack == mate_pack:
            db.adjust_pack_unity(actor_pack, 1)
            pack_note = ' · pack unity **+1**'
        day = _world_day(interaction.guild.id)
        log_rite(actor['id'], 'rite_joining_howl', f"Joining howl with **{bonded_mate['wolf_name']}**.", guild_id=interaction.guild.id, day=day)
        log_rite(bonded_mate['id'], 'rite_joining_howl', f"Joining howl with **{actor['wolf_name']}**.", guild_id=interaction.guild.id, day=day)
        favor_line = f"Maw Favor: +1 → **{favor_a}** (you)"
        if favor_b is not None:
            favor_line += f" · **{favor_b}** ({bonded_mate['wolf_name']})"
        body = (
            f"**{actor['wolf_name']}** throws back their head and calls; and **{bonded_mate['wolf_name']}** answers.\n"
            "_Two voices become one sound, rising until the trees hold it._\n\n"
            f"The pack hears. The Maw hears.\n\n{favor_line}{pack_note}"
        )
        embed = howlbert_embed('Joining Howl', body, color=SUCCESS_COLOR)
        embed.set_footer(text='a one-time rite · the bond is witnessed')
        await interaction.response.send_message(embed=embed)

    @rite.command(name='moon_witness', description='seal a mated bond under the full moon; true mateship (+2 maw_favor each, once per pair).')
    async def moon_witness(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(player_message('Use this in a server.'), ephemeral=reply_ephemeral())
            return
        actor = _active_wolf(interaction)
        if not actor:
            await interaction.response.send_message(player_message('Use `/register` first.'), ephemeral=reply_ephemeral())
            return
        bonded_mate = db.get_bonded_mate(actor)
        if not bonded_mate:
            await interaction.response.send_message(embed=howlbert_embed('No Bonded Mate', 'Moon\'s Witness requires a bonded mate.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        actor_done = int(actor['moon_witness_done']) if 'moon_witness_done' in actor.keys() else 0
        mate_done = int(bonded_mate['moon_witness_done']) if 'moon_witness_done' in bonded_mate.keys() else 0
        if actor_done or mate_done:
            await interaction.response.send_message(embed=howlbert_embed('Already Witnessed', f'**{actor["wolf_name"]}** and **{bonded_mate["wolf_name"]}** have already been witnessed by the moon.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        from engine.moon_phase import is_full_moon
        if not is_full_moon():
            await interaction.response.send_message(embed=howlbert_embed('Not Yet', 'The moon is not full. This rite must be performed under the full moon.', color=ERROR_COLOR), ephemeral=reply_ephemeral())
            return
        db.set_moon_witness_done(actor['id'], bonded_mate['id'])
        favor_a = db.adjust_maw_favor(interaction.user.id, 2)
        mate_discord_id = int(bonded_mate['discord_id']) if 'discord_id' in bonded_mate.keys() and bonded_mate['discord_id'] else None
        favor_b = db.adjust_maw_favor(mate_discord_id, 2) if mate_discord_id else None
        pack_note = ''
        actor_pack = int(actor['pack_id']) if 'pack_id' in actor.keys() and actor['pack_id'] else None
        mate_pack = int(bonded_mate['pack_id']) if 'pack_id' in bonded_mate.keys() and bonded_mate['pack_id'] else None
        if actor_pack and actor_pack == mate_pack:
            db.adjust_pack_unity(actor_pack, 2)
            pack_note = ' · pack unity **+2**'
        day = _world_day(interaction.guild.id)
        from engine.bonds import has_romance_bond
        bond_note = ''
        if has_romance_bond(actor['id'], bonded_mate['id']):
            row = db.adjust_bond_strength(actor['id'], bonded_mate['id'], 'romance', 10, day=day or 0)
            if row:
                bond_note = f" · romance bond → **{row['strength']}/100**"
        else:
            db.set_bond(actor['id'], bonded_mate['id'], 'romance', strength=20, note="Moon's Witness", day=day or 0)
            bond_note = ' · romance bond formed (**20/100**)'
        log_rite(actor['id'], 'rite_moon_witness', f"Moon's Witness with **{bonded_mate['wolf_name']}**.", guild_id=interaction.guild.id, day=day)
        log_rite(bonded_mate['id'], 'rite_moon_witness', f"Moon's Witness with **{actor['wolf_name']}**.", guild_id=interaction.guild.id, day=day)
        favor_line = f"Maw Favor: +2 → **{favor_a}** (you)"
        if favor_b is not None:
            favor_line += f" · **{favor_b}** ({bonded_mate['wolf_name']})"
        body = (
            f"**{actor['wolf_name']}** and **{bonded_mate['wolf_name']}** stand beneath the full moon, pelt to pelt.\n"
            "_No words. The light is enough. The Maw is watching and does not look away._\n\n"
            f"Their bond is witnessed. Not by pack or packmate; by the moon itself.\n\n"
            f"{favor_line}{pack_note}{bond_note}"
        )
        embed = howlbert_embed("Moon's Witness", body, color=SUCCESS_COLOR)
        embed.set_footer(text='true mateship sealed · once per pair · full moon required')
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Rite(bot))