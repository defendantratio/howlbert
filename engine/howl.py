"""Pack and lone howls; unity, standing, Commanding Howl buffs."""

from __future__ import annotations

import random

import discord

import database as db
from engine.character import attr_modifier
from engine.group_checks import pack_howl_range
from engine.pack_unity import (
    compute_howl_unity_gain,
    format_howl_carry,
    format_unity_meter,
    pick_howl_flavor,
    unity_effect_text,
    unity_is_broken,
)
from utils.replies import reply_ephemeral
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed


async def execute_howl(interaction: discord.Interaction, message: str | None = None) -> None:
    """Run `/howl` or `/packlife action:howl` logic."""
    user = db.get_user(interaction.user.id)
    if not user:
        embed = howlbert_embed("not registered", "use `/register` first.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    if not interaction.guild:
        await interaction.response.send_message("use this in a server.", ephemeral=reply_ephemeral())
        return

    world = db.get_world(interaction.guild.id)
    day = world["day_number"]
    wolf_name = user["wolf_name"]

    from engine.diminishing import diminishing_note, next_use_multiplier

    howl_mult, howl_n = next_use_multiplier(user, "howl", day)

    from engine.character_traits import trait_blocks_howl
    from engine.genetics import genetic_blocks_howl

    blocked, trait_name = trait_blocks_howl(user)
    if not blocked:
        blocked, trait_name = genetic_blocks_howl(user)
    if blocked:
        embed = howlbert_embed(
            "cannot howl",
            f"**{wolf_name}**'s throat will not answer the pack; **{trait_name}** silences the call.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
        return

    echo_count = 0

    if user["pack_id"]:
        pack = db.get_pack(user["pack_id"])
        if not pack:
            embed = howlbert_embed("pack not found", "that great pack isn't in this den.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=reply_ephemeral())
            return

        unity_before = int(pack["pack_unity"])
        echo_count = db.record_pack_howl(
            pack["id"], interaction.guild.id, day, interaction.user.id
        )
        unity_gain = compute_howl_unity_gain(user, pack, unity_before, echo_count)
        muted = unity_gain == 0 and unity_is_broken(unity_before)
        from engine.plot_blinking import apply_plot_howl_mood_cost, plot_howl_unity_bonus

        plot_unity = plot_howl_unity_bonus(interaction.guild.id, user=user)
        if plot_unity and unity_gain and not muted:
            unity_gain += plot_unity
        moon_note = ""
        if unity_gain and not muted:
            from engine.moon_phase import full_moon_rally_unity_bonus

            moon_bonus = full_moon_rally_unity_bonus()
            if moon_bonus:
                unity_gain += moon_bonus
                moon_note = f"\nfull moon: the call carries further (**+{moon_bonus}** unity)."
            from engine.pack_unity import howl_weather_muffle_note

            unity_gain, muffle_note = howl_weather_muffle_note(unity_gain, world["weather"])
            if muffle_note:
                moon_note = f"{moon_note}\n{muffle_note}" if moon_note else f"\n{muffle_note}"
        _mood_cost, mood_note = apply_plot_howl_mood_cost(user, pack, interaction.guild.id)
        flavor = pick_howl_flavor(echo_count=echo_count, muted=muted)

        if unity_gain:
            unity_gain = max(1, int(unity_gain * howl_mult))
        dissolve = ""
        if unity_gain:
            dissolve = db.adjust_pack_unity(pack["id"], unity_gain)

        pack = db.get_pack(pack["id"])
        unity = int(pack["pack_unity"]) if pack else unity_before
        standing_gain = 2 if echo_count >= 3 else 1
        if muted:
            standing_gain = 1
        standing_gain = max(1, int(standing_gain * howl_mult))

        kick = db.adjust_wolf_standing(interaction.user.id, standing_gain)
        db.update_user(interaction.user.id, last_howl_day=day)
        db.increment_quest_progress(interaction.user.id, "howl", guild_id=interaction.guild.id)
        for rel in db.list_pack_relations(interaction.guild.id, pack["id"]):
            if int(rel["standing"]) <= 3:
                db.update_user(interaction.user.id, howl_exposed_day=day)
                break

        if dissolve == "dissolved":
            body = (
                f"**{wolf_name}** howls; and the den **fractures**.\n"
                f"{flavor}\n\n"
                "Unity hit **−5**. Every wolf is cast to **loner** until they `/setfaction` again."
            )
            if message:
                body += f"\n\n_{message.strip()}_"
            embed = howlbert_embed("pack dissolved", body, color=ERROR_COLOR)
            embed.set_footer(text="/setfaction to rejoin a great pack")
            await interaction.response.send_message(embed=embed)
            return

        body = f"**{wolf_name}** howls for **{pack['name'] if pack else 'the pack'}**.\n{flavor}"
        if muted:
            body += (
                "\n\n_the den is too broken for your howl to raise **unity**; "
                "an **alpha** or **beta (advisor)** must rally first._"
            )
        if message:
            body += f"\n\n_{message.strip()}_"
        if mood_note:
            body += f"\n\n_{mood_note}_"
        if moon_note:
            body += f"\n{moon_note}"
        dim_note = diminishing_note(howl_n)
        if dim_note:
            body += f"\n\n_{dim_note}_"
        from engine.plot_blinking import try_plot_witness

        body += try_plot_witness(user, interaction.guild.id, day, action="howl")

        from engine.role_features import can_grant_commanding_howl, grant_commanding_howl_buffs

        commanding_note = ""
        if can_grant_commanding_howl(user, pack):
            allies = grant_commanding_howl_buffs(pack["id"], exclude_wolf_id=user["id"])
            if allies:
                commanding_note = (
                    f"\n\n_**commanding howl**; **{allies}** packmate"
                    f"{'s' if allies != 1 else ''} gain advantage on their next check or attack._"
                )
                body += commanding_note

        embed = howlbert_embed("pack howl", body, color=SUCCESS_COLOR)
        if unity_gain:
            embed.add_field(
                name="pack unity",
                value=f"+{unity_gain} → **{format_unity_meter(unity)}**",
                inline=True,
            )
        else:
            embed.add_field(name="pack unity", value=format_unity_meter(unity), inline=True)
        embed.add_field(
            name="standing",
            value=(
                "**cast out**; loner"
                if kick == "kicked"
                else ("**Rite of the Broken Canine**" if kick == "broken_rite" else f"+{standing_gain}")
            ),
            inline=True,
        )
        if echo_count >= 2:
            embed.add_field(
                name="chorus",
                value=f"**{echo_count}** wolves have howled this sunrise.",
                inline=False,
            )

        howler_ids = db.get_pack_howl_discord_ids(pack["id"], interaction.guild.id, day)
        best_total = 0
        nat_20 = False
        for hid in howler_ids:
            w = db.get_user(hid)
            if not w:
                continue
            die = random.randint(1, 20)
            total = die + attr_modifier(w["attr_cha"])
            if total > best_total:
                best_total = total
                nat_20 = die == 20
        if best_total:
            pack_size = len(db.get_pack_den_wolves(pack["id"]))
            reach = pack_howl_range(best_total, pack_size, natural_20=nat_20)
            embed.add_field(
                name="on the wind",
                value=format_howl_carry(reach, natural_20=nat_20),
                inline=True,
            )
        footer = unity_effect_text(unity)
        if commanding_note:
            footer += " · commanding howl buff active for packmates"
        embed.set_footer(text=footer)
        await interaction.response.send_message(embed=embed)
        return

    lone_standing_gain = max(1, int(1 * howl_mult))
    kick = db.adjust_wolf_standing(interaction.user.id, lone_standing_gain)
    db.update_user(interaction.user.id, last_howl_day=day)
    body = (
        f"**{wolf_name}** howls alone; no den answers, only wind.\n"
        f"{pick_howl_flavor(echo_count=0)}"
    )
    if message:
        body += f"\n\n_{message.strip()}_"
    dim_note = diminishing_note(howl_n)
    if dim_note:
        body += f"\n\n_{dim_note}_"
    embed = howlbert_embed("lone howl", body, color=SUCCESS_COLOR)
    embed.add_field(
        name="standing",
        value=(
            "**cast out**; loner"
            if kick == "kicked"
            else ("**Rite of the Broken Canine**" if kick == "broken_rite" else f"+{lone_standing_gain}")
        ),
        inline=True,
    )
    embed.set_footer(text="join a great pack with `/setfaction` to raise pack unity.")
    await interaction.response.send_message(embed=embed)
