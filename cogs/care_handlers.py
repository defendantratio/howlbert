"""Shared care command handlers (herbs, medic treatment, rites)."""

from __future__ import annotations

import json
import random

import discord

import database as db
from engine.role_privileges import treat_limit_reached
from utils.embeds import ERROR_COLOR, SUCCESS_COLOR, howlbert_embed


async def herbbag(interaction: discord.Interaction):
    user = db.get_user(interaction.user.id)
    if not user:
        await interaction.response.send_message("Use `/register` first.", ephemeral=True)
        return
    if not interaction.guild:
        await interaction.response.send_message("Use this in a server.", ephemeral=True)
        return
    from engine.herb_storage import list_herb_bag_summary
    from engine.restricted_herbs import herbbag_hoard_warning

    world = db.get_world(interaction.guild.id)
    body = list_herb_bag_summary(user["id"], world["day_number"])
    hoard_warn = herbbag_hoard_warning(user)
    stacks = db.get_herb_stacks(user["id"])
    spoiling = sum(
        1
        for s in stacks
        if s["form"] == "fresh"
        and world["day_number"] - int(s["acquired_day"]) >= 1
    )
    spoil_note = (
        f"\n\n**{spoiling}** stack(s) spoiling; `/herbs action:dryall` or prepare **dry** today."
        if spoiling
        else ""
    )
    embed = howlbert_embed(
        f"{user['wolf_name']}: Forage Herb Bag",
        body
        + spoil_note
        + hoard_warn
        + "\n\n`/herbs action:prepare` or **`action:dryall`**: forage **stack:ID** or **inventory** herb (`herb_arnica`)"
        + "\n**Dry all** processes your forage bag, `/inventory` herbs, and fresh stacks in the **healers' den store**."
        + "\nPrepared herbs land in this bag. Fresh forage stacks rot if not **dried** within 1 sunrise.",
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def prepare_herb(interaction: discord.Interaction, stack_id: int, prep_method: str):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
        return
    from engine.herb_preparation import prepare_herb_stack

    world = db.get_world(interaction.guild.id)
    ok, msg = prepare_herb_stack(
        user,
        stack_id,
        prep_method,
        day=world["day_number"],
        at_den=bool(user["pack_id"]),
    )
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed("Herb Preparation", msg, color=color))

async def dryall(interaction: discord.Interaction):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
        return
    from engine.herb_preparation import dry_all_fresh_herbs

    world = db.get_world(interaction.guild.id)
    ok, msg = dry_all_fresh_herbs(
        user,
        day=world["day_number"],
        guild_id=interaction.guild.id,
        at_den=bool(user["pack_id"]),
    )
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed("Dry All Herbs", msg, color=color))

async def prepare_herb_inventory(
    interaction: discord.Interaction, item_key: str, prep_method: str
):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
        return
    from engine.herb_preparation import prepare_herb_from_inventory

    world = db.get_world(interaction.guild.id)
    ok, msg = prepare_herb_from_inventory(
        user,
        item_key,
        prep_method,
        day=world["day_number"],
        guild_id=interaction.guild.id,
        at_den=bool(user["pack_id"]),
    )
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed("Herb Preparation", msg, color=color))

async def treat(
    interaction: discord.Interaction,
    herb: str,
    patient: discord.Member | None = None,
    ):
    import json
    import random

    user = db.get_user(interaction.user.id)
    if not user:
        embed = howlbert_embed("Not Registered", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    from engine.herb_storage import parse_herb_stack_id

    stack_id = parse_herb_stack_id(herb)
    if stack_id is not None:
        if treat_limit_reached(user) and not patient:
            embed = howlbert_embed(
                "Limit Reached",
                "You can only **/treat** **3 times per sunrise** (Medics unlimited).",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        from engine.herb_treat import treat_from_herb_stack

        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day = world["day_number"] if world else 0
        treat_patient = None
        if patient:
            from engine.plot_blinking import firepaw_can_treat_patient
            from engine.role_privileges import is_medic

            if not is_medic(user) and not (
                interaction.guild
                and firepaw_can_treat_patient(user, interaction.guild.id)
            ):
                await interaction.response.send_message(
                    embed=howlbert_embed(
                        "Medic Only",
                        "Only **Medics** may treat a **patient** from their herb bag.\n\n"
                        "_**Firepaw** (Medic Apprentice) may treat packmates during "
                        "Book One phases **5–11**._",
                        color=ERROR_COLOR,
                    ),
                    ephemeral=True,
                )
                return
            target = db.get_user(patient.id)
            if not target:
                await interaction.response.send_message(
                    embed=howlbert_embed("Not Registered", "Patient is not on Howlbert.", color=ERROR_COLOR),
                    ephemeral=True,
                )
                return
            treat_patient = target
        ok, msg = treat_from_herb_stack(
            user,
            stack_id,
            day=day,
            patient=treat_patient,
            guild_id=interaction.guild.id if interaction.guild else None,
        )
        if ok and interaction.guild:
            from engine.plot_blinking import try_plot_treat_extras

            patient_row = treat_patient or user
            msg += try_plot_treat_extras(
                user, patient_row, guild_id=interaction.guild.id, day=day
            )
        color = SUCCESS_COLOR if ok else ERROR_COLOR
        embed = howlbert_embed("Treatment", msg, color=color)
        if ok:
            db.update_user(
                interaction.user.id,
                wolf_id=user["id"],
                herb_treats_today=int(
                    user["herb_treats_today"] if "herb_treats_today" in user.keys() else 0
                )
                + 1,
            )
            db.increment_quest_progress(interaction.user.id, "treat")
        await interaction.response.send_message(embed=embed)
        return

    item = db.get_item_by_key(herb.strip().lower())
    if not item or (not item["key"].startswith("herb_") and item["key"] != "stick"):
        embed = howlbert_embed(
            "Unknown Herb",
            "Use an herb from `/inventory` (keys like `herb_yarrow` or `stick`).",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    qty = db.get_inventory_quantity(interaction.user.id, item["id"])
    if qty < 1:
        embed = howlbert_embed("Not In Inventory", f"You don't have **{item['name']}**.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if treat_limit_reached(user):
        embed = howlbert_embed(
            "Limit Reached",
            "You can only **/treat** with herbs **3 times per sunrise**. "
            "**Medics** have no cap; promote to full Medic rank or wait for the next `/rollover`.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    from herbs import HERBS
    from engine.conditions import medicine_check, parse_injuries, treat_with_herb, herb_special_effect

    herb_key = "stick" if item["key"] == "stick" else item["key"].replace("herb_", "", 1)
    meta = HERBS.get(herb_key, {"cures": (), "effect": item["description"]})
    special = herb_special_effect(herb_key, user, inventory_qty=qty)
    world = db.get_world(interaction.guild.id) if interaction.guild else None
    treat_day = world["day_number"] if world else int(user["last_rest_day"] or 0)
    if special == "ragweed_need_three":
        embed = howlbert_embed(
            "Not Enough Ragweed",
            "Ragweed needs **3 leaves** in inventory to remove 1 exhaustion.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if special == "honey_needs_depletion":
        embed = howlbert_embed(
            "Not Depleted Enough",
            "Honey only shakes off **starvation exhaustion**; your hunger and thirst "
            "must be low first.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if special == "honey_pup_not_depleted":
        embed = howlbert_embed(
            "Not Depleted Enough",
            "Honey feeds starving pups; hunger or thirst must be low first.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if special == "feed_pup_honey":
        if not db.consume_item(interaction.user.id, item["id"], quantity=1):
            embed = howlbert_embed(
                "Not In Inventory", f"You don't have enough **{item['name']}**.", color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        world = db.get_world(interaction.guild.id) if interaction.guild else None
        day_number = world["day_number"] if world else None
        from config import HONEY_PUP_HUNGER_BONUS
        from engine.nursing import apply_honey_to_pup

        fields = apply_honey_to_pup(user, day_number=day_number)
        db.update_user(interaction.user.id, wolf_id=user["id"], **fields)
        ex_note = ""
        if "exhaustion" in fields:
            ex_note = f" Exhaustion **→ {fields['exhaustion']}**."
        msg = (
            f"**{item['name']}**: warm sweetness (**+{HONEY_PUP_HUNGER_BONUS}** hunger)."
            f"{ex_note}"
        )
        embed = howlbert_embed("Honey", msg, color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)
        return

    outcome = treat_with_herb(user, herb_key, meta)

    if special == "reduce_exhaustion" and int(user["exhaustion"]) <= 0:
        embed = howlbert_embed(
            "No Effect",
            f"**{item['name']}**: you aren't carrying exhaustion to shed.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if special == "hunger_shield" and int(
        user["hunger_exhaustion_skip"] if "hunger_exhaustion_skip" in user.keys() else 0
    ):
        embed = howlbert_embed(
            "Already Shielded",
            "Fennel's hunger shield is already active for the next sunrise.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if special == "march_shield" and int(
        user["march_exhaustion_skip"] if "march_exhaustion_skip" in user.keys() else 0
    ):
        embed = howlbert_embed(
            "Already Shielded",
            "Burnet's march ward is already active for the next sunrise.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if outcome == "no_effect" and not special and herb_key not in ("comfrey", "cobwebs"):
        check = medicine_check(user, dc=15)
        from engine.herb_buffs import consume_herb_check_buffs

        consume_fields = consume_herb_check_buffs(user, skill_key="medicine")
        if consume_fields:
            db.update_user(interaction.user.id, wolf_id=user["id"], **consume_fields)
        if not check["success"]:
            embed = howlbert_embed(
                "Treatment Failed",
                f"Medicine check: {check['total']} vs DC 15; no effect.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed)
            return

    use_qty = 3 if herb_key == "ragweed" and special == "reduce_exhaustion" else 1
    if not db.consume_item(interaction.user.id, item["id"], quantity=use_qty):
        embed = howlbert_embed("Not In Inventory", f"You don't have enough **{item['name']}**.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    injuries = parse_injuries(user["active_injuries"])
    msg = ""

    if special == "reduce_exhaustion":
        old_ex = int(user["exhaustion"])
        new_ex = max(0, old_ex - 1)
        db.set_user_conditions(interaction.user.id, exhaustion=new_ex)
        msg = f"**{item['name']}**: exhaustion **{old_ex}** → **{new_ex}**."
    elif special == "hunger_shield":
        db.update_user(interaction.user.id, wolf_id=user["id"], hunger_exhaustion_skip=1)
        msg = (
            f"**{item['name']}**: you won't gain hunger exhaustion on the next sunrise "
            "(thirst still applies)."
        )
    elif special == "march_shield":
        db.update_user(interaction.user.id, wolf_id=user["id"], march_exhaustion_skip=1)
        msg = (
            f"**{item['name']}**: ignore the first **+1 exhaustion** from strain "
            "on the next sunrise."
        )
    elif special == "jaw_meal_shield":
        db.update_user(interaction.user.id, wolf_id=user["id"], jaw_meal_shield=1)
        msg = (
            f"**{item['name']}**: you can eat and drink without pain until the next sunrise."
        )
        if outcome == "cured_injury":
            for inj in meta.get("cures", ()):
                if inj in injuries:
                    injuries.remove(inj)
                    db.clear_injury_since(user["id"], inj)
            db.set_user_conditions(
                interaction.user.id,
                active_injuries=json.dumps(injuries),
                condition="healthy" if not injuries else user["condition"],
            )
            msg += " Broken jaw treated."
    elif special == "purslane_thirst":
        thirst = db.adjust_thirst(user["id"], 12)
        msg = f"**{item['name']}**: chewed leaves restore thirst **{thirst}** (+12)."
    elif special == "sorrel_restore":
        from config import HUNGER_MAX

        new_hunger = min(HUNGER_MAX, int(user["hunger"]) + 18)
        had_gash = "deep_gash" in injuries
        fields: dict = {"hunger": new_hunger}
        if had_gash:
            injuries.remove("deep_gash")
            db.clear_injury_since(user["id"], "deep_gash")
            fields["active_injuries"] = json.dumps(injuries)
            if not injuries:
                fields["condition"] = "healthy"
        db.update_user(interaction.user.id, wolf_id=user["id"], **fields)
        msg = f"**{item['name']}**: appetite returns (**hunger {new_hunger}**)."
        if had_gash:
            msg += " Bleeding staunched."
    elif outcome == "cured_disease":
        db.set_user_conditions(interaction.user.id, clear_disease=True, condition="healthy")
        msg = f"**{meta.get('name', item['name'])}** cured your disease."
    elif outcome == "rabies_ease":
        from engine.herb_buffs import grant_disease_save_advantage

        db.update_user(
            interaction.user.id,
            wolf_id=user["id"],
            **grant_disease_save_advantage(user),
        )
        msg = (
            f"**{item['name']}**: herbs slow early rabies; **advantage** on your next disease save "
            "(one sunrise). Rabies is not cured."
        )
    elif outcome == "cured_injury":
        for inj in meta.get("cures", ()):
            if inj in injuries:
                injuries.remove(inj)
                db.clear_injury_since(user["id"], inj)
        db.set_user_conditions(
            interaction.user.id,
            active_injuries=json.dumps(injuries),
            condition="healthy" if not injuries else user["condition"],
        )
        msg = f"**{item['name']}** treated your injury."
    elif outcome == "cured_genetic":
        from engine.genetics import genetic_keys_matching_cures, remove_genetic_keys

        matched = genetic_keys_matching_cures(user, meta.get("cures", ()))
        new_genetics = remove_genetic_keys(user, matched)
        db.update_user(interaction.user.id, wolf_id=user["id"], genetic_conditions=new_genetics)
        names = ", ".join(m.replace("_", " ").title() for m in matched)
        msg = f"**{item['name']}** eased or corrected **{names}**."
    elif outcome == "symptom_ease":
        msg = f"**{item['name']}**: {meta.get('effect', 'symptoms ease for now')}."
    elif outcome == "poison_herb":
        msg = (
            f"**{item['name']}**: restricted poison; no safe cure applied. "
            "Medic knowledge only."
        )
    elif outcome == "healed" or herb_key == "comfrey":
        from engine.exhaustion_effects import effective_max_hp

        heal = random.randint(1, 4)
        cap = effective_max_hp(user)
        new_hp = min(cap, user["hp"] + heal)
        db.set_user_conditions(interaction.user.id, hp=new_hp)
        msg = f"Comfrey poultice healed **{heal} HP**."
    elif outcome == "stabilized":
        db.set_user_conditions(interaction.user.id, hp=1, condition="stable")
        msg = (
            f"**{item['name']}** stabilized you at 1 HP."
            if herb_key != "cobwebs"
            else "Cobwebs stabilized you at 1 HP."
        )

    from engine.herb_buffs import apply_supplemental_herb

    supplemental = apply_supplemental_herb(herb_key, user, day=treat_day, outcome=outcome)
    if supplemental:
        kind = supplemental["kind"]
        sfields = supplemental.get("fields") or {}
        if kind == "mercy":
            db.set_user_conditions(interaction.user.id, condition="dead", hp=0)
            msg = f"**{item['name']}**: {supplemental['message']}"
        elif kind == "stabilize" and outcome != "stabilized":
            db.set_user_conditions(interaction.user.id, hp=1, condition="stable")
            msg = f"**{item['name']}**: {supplemental['message']}"
        else:
            if sfields:
                db.update_user(interaction.user.id, wolf_id=user["id"], **sfields)
            extra = supplemental["message"]
            if not msg:
                msg = f"**{item['name']}**; {extra}"
            elif kind in ("disease_save_buff", "minor_relief", "heal", "symptom_relief"):
                msg += f" {extra}"

    if not msg:
        msg = f"Applied **{item['name']}**: {meta.get('effect', 'minor relief')}."

    embed = howlbert_embed("Treatment", msg, color=SUCCESS_COLOR)
    db.update_user(
        interaction.user.id,
        wolf_id=user["id"],
        herb_treats_today=int(
            user["herb_treats_today"] if "herb_treats_today" in user.keys() else 0
        )
        + 1,
    )
    db.increment_quest_progress(interaction.user.id, "treat")
    await interaction.response.send_message(embed=embed)

async def herb_guide(interaction: discord.Interaction, herb_filter: str = "all"):
    from engine.herb_guide import build_herb_guide_embed
    from utils.herb_views import make_herb_guide_view

    if herb_filter not in ("all", "wild", "roadside", "compound"):
        herb_filter = "all"
    title, body = build_herb_guide_embed(page=0, filter_key=herb_filter)
    embed = howlbert_embed(title, body)
    embed.set_footer(text="Herb guide · /herbs action:guide")
    view = make_herb_guide_view(page=0, filter_key=herb_filter)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def denstore(
    interaction: discord.Interaction,
    mode: str,
    store_stack: str | None,
    herb: str | None,
    ):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
        return
    if not user["pack_id"]:
        await interaction.response.send_message(
            embed=howlbert_embed("No Pack", "Join a pack to use the healers' herb store.", color=ERROR_COLOR),
            ephemeral=True,
        )
        return
    from engine.pack_herb_store import (
        can_manage_den_herbs,
        deposit_all_herbs_to_store,
        deposit_herb_to_store,
        deposit_inventory_herb_to_store,
        list_pack_herb_store,
        withdraw_herb_from_store,
    )

    world = db.get_world(interaction.guild.id)
    if mode == "list":
        body = list_pack_herb_store(user["pack_id"], world["day_number"])
        embed = howlbert_embed(f"Healers' Herb Store", body)
        embed.set_footer(
            text="Anyone: `mode:deposit` / `depositall` · Medics & Foragers: `mode:withdraw`"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    if mode == "depositall":
        ok, msg = deposit_all_herbs_to_store(
            user,
            pack_id=user["pack_id"],
            guild_id=interaction.guild.id,
            day=world["day_number"],
        )
    elif mode == "deposit":
        from engine.herb_storage import parse_herb_stack_id

        raw = (store_stack or herb or "").strip()
        if raw.lower().startswith("herb_"):
            ok, msg = deposit_inventory_herb_to_store(
                user,
                raw.lower(),
                pack_id=user["pack_id"],
                guild_id=interaction.guild.id,
                day=world["day_number"],
            )
        else:
            stack_id = parse_herb_stack_id(raw)
            if stack_id is None:
                await interaction.response.send_message(
                    "Pick a forage **stack:ID** or inventory **`herb_arnica`** key to deposit.",
                    ephemeral=True,
                )
                return
            ok, msg = deposit_herb_to_store(
                user,
                stack_id,
                pack_id=user["pack_id"],
                guild_id=interaction.guild.id,
                day=world["day_number"],
            )
    elif mode == "withdraw":
        if not can_manage_den_herbs(user):
            await interaction.response.send_message(
                embed=howlbert_embed(
                    "Medic / Forager Only",
                    "Only **Medics** and **Foragers** may withdraw from the healers' store.",
                    color=ERROR_COLOR,
                ),
                ephemeral=True,
            )
            return
        try:
            sid = int((store_stack or herb or "").strip().lstrip("#"))
        except (ValueError, TypeError):
            await interaction.response.send_message(
                "Enter store stack **`#ID`** from `/herbs action:store mode:list`.",
                ephemeral=True,
            )
            return
        ok, msg = withdraw_herb_from_store(
            user,
            sid,
            pack_id=user["pack_id"],
            guild_id=interaction.guild.id,
            day=world["day_number"],
        )
    else:
        await interaction.response.send_message(
            "Pick **list**, **deposit**, **depositall**, or **withdraw**.", ephemeral=True
        )
        return
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed("Den Herb Store", msg, color=color))

async def turnin_restricted(interaction: discord.Interaction, store_stack: str | None):
    user = db.get_user(interaction.user.id)
    if not user or not interaction.guild:
        await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
        return
    if not user["pack_id"]:
        await interaction.response.send_message(
            embed=howlbert_embed("No Pack", "Join a pack to turn poison herbs in.", color=ERROR_COLOR),
            ephemeral=True,
        )
        return
    from engine.herb_storage import parse_herb_stack_id
    from engine.pack_herb_store import turnin_restricted_herb

    sid = parse_herb_stack_id(store_stack)
    if not sid:
        await interaction.response.send_message(
            "Enter your forage **`stack:ID`** for the restricted herb to turn in.",
            ephemeral=True,
        )
        return
    world = db.get_world(interaction.guild.id)
    ok, msg = turnin_restricted_herb(
        user,
        sid,
        pack_id=int(user["pack_id"]),
        guild_id=interaction.guild.id,
        day=world["day_number"],
    )
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed("Poison Herb Turn-In", msg, color=color))

async def sacred_visit(interaction: discord.Interaction):
    user = db.get_user(interaction.user.id)
    if not user:
        await interaction.response.send_message("Use `/register` first.", ephemeral=True)
        return
    if not interaction.guild:
        await interaction.response.send_message("Use this in a server.", ephemeral=True)
        return
    world = db.get_world(interaction.guild.id)
    from engine.sacred_visits import record_sacred_visit

    ok, body = record_sacred_visit(user, day=world["day_number"])
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed("Sacred Visit", body, color=color))

async def spirit_ritual(
    interaction: discord.Interaction,
    patient: discord.Member | None,
    ritual_herb: str | None,
    ):
    medic = db.get_user(interaction.user.id)
    if not medic or not interaction.guild:
        await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
        return
    if not patient:
        await interaction.response.send_message("Pick a **patient** for the cleansing ritual.", ephemeral=True)
        return
    if not ritual_herb:
        await interaction.response.send_message(
            "Pick **douglas_sagewort**, **lavender**, or **mountain_ash** (rowan).", ephemeral=True
        )
        return
    target = db.get_user(patient.id)
    if not target:
        await interaction.response.send_message("Patient is not on Howlbert.", ephemeral=True)
        return
    world = db.get_world(interaction.guild.id)
    from engine.medical_care import run_spirit_ritual

    ok, body = run_spirit_ritual(medic, target, ritual_herb, day=world["day_number"])
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed("Spirit Ritual", body, color=color))
    if ok:
        db.increment_quest_progress(interaction.user.id, "treat")

async def naming_ceremony(
    interaction: discord.Interaction,
    patient: discord.Member | None,
    ):
    medic = db.get_user(interaction.user.id)
    if not medic or not interaction.guild:
        await interaction.response.send_message("Use `/register` in a server.", ephemeral=True)
        return
    if not patient:
        await interaction.response.send_message("Pick the **pup** (`patient`) for the naming rite.", ephemeral=True)
        return
    pup = db.get_user(patient.id)
    if not pup:
        await interaction.response.send_message("That wolf is not on Howlbert.", ephemeral=True)
        return
    world = db.get_world(interaction.guild.id)
    from engine.medical_care import run_naming_ceremony

    ok, body = run_naming_ceremony(medic, pup, day=world["day_number"])
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed("Naming Ceremony", body, color=color))

async def lay_to_rest(
    interaction: discord.Interaction,
    deceased: discord.Member | None,
    lay_herb: str | None,
    ):
    medic = db.get_user(interaction.user.id)
    if not medic:
        await interaction.response.send_message("Use `/register` first.", ephemeral=True)
        return
    if not deceased or not lay_herb:
        await interaction.response.send_message(
            "Pick **deceased** and **lay_herb** (rosemary, lavender, mint).", ephemeral=True
        )
        return
    target = db.get_user(deceased.id)
    if not target:
        await interaction.response.send_message("That wolf is not on Howlbert.", ephemeral=True)
        return
    from engine.medical_care import run_lay_to_rest

    world = db.get_world(interaction.guild.id) if interaction.guild else None
    day = world["day_number"] if world else 0
    ok, body = run_lay_to_rest(medic, target, lay_herb, day=day)
    color = SUCCESS_COLOR if ok else ERROR_COLOR
    await interaction.response.send_message(embed=howlbert_embed("Lay to Rest", body, color=color))



async def quarantine_command(
    interaction: discord.Interaction,
    wolf: discord.Member | None = None,
    own_wolf: str | None = None,
    release: bool = False,
):
    from engine.diseases import disease_display
    from engine.quarantine import can_manage_quarantine, is_quarantined

    actor = db.get_user(interaction.user.id)
    if not actor:
        embed = howlbert_embed("Not Registered", "Use `/register` first.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if wolf and own_wolf:
        embed = howlbert_embed(
            "Pick One Target",
            "Choose another **player** or `own_wolf`; not both.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    pack = db.get_pack(actor["pack_id"]) if actor["pack_id"] else None

    if not wolf and not own_wolf:
        if is_quarantined(actor):
            embed = howlbert_embed(
                "Quarantined",
                f"**{actor['wolf_name']}** is isolated in the sick den.",
                color=SUCCESS_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if pack and can_manage_quarantine(actor, pack):
            rows = db.list_pack_quarantined(pack["id"])
            if not rows:
                embed = howlbert_embed(
                    "Sick Den",
                    "No wolves are quarantined in your pack.",
                    color=SUCCESS_COLOR,
                )
            else:
                lines = [f"**{r['wolf_name']}**" for r in rows]
                embed = howlbert_embed(
                    "Sick Den: Quarantined",
                    "\n".join(lines),
                    color=SUCCESS_COLOR,
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        embed = howlbert_embed(
            "Quarantine",
            "Pick a **wolf** to isolate, or use `release:true` to free someone.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if own_wolf:
        rows = db.list_user_wolves(interaction.user.id)
        target = next(
            (w for w in rows if w["wolf_name"].lower() == own_wolf.strip().lower()),
            None,
        )
        if not target:
            embed = howlbert_embed("Unknown Wolf", f"No wolf named **{own_wolf}**.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
    else:
        target = db.get_user(wolf.id)
        if not target:
            embed = howlbert_embed("Not Registered", "That wolf isn't registered.", color=ERROR_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

    if not pack:
        embed = howlbert_embed("No Pack", "Quarantine is a pack sick-den measure.", color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if target["pack_id"] != pack["id"]:
        embed = howlbert_embed(
            "Wrong Pack",
            "**{0}** isn't in your pack.".format(target["wolf_name"]),
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not can_manage_quarantine(actor, pack):
        embed = howlbert_embed(
            "Not Authorized",
            "Only **Medics**, **Alphas**, and **Advisors** can manage quarantine.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if release:
        if not is_quarantined(target):
            embed = howlbert_embed(
                "Not Quarantined",
                f"**{target['wolf_name']}** isn't in isolation.",
                color=ERROR_COLOR,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        db.set_quarantined(target["discord_id"], False, wolf_id=target["id"])
        embed = howlbert_embed(
            "Released",
            f"**{target['wolf_name']}** may leave the sick den.",
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed)
        return

    if is_quarantined(target):
        embed = howlbert_embed(
            "Already Quarantined",
            f"**{target['wolf_name']}** is already isolated.",
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    db.set_quarantined(target["discord_id"], True, wolf_id=target["id"])
    illness = disease_display(target)
    extra = ""
    if illness:
        extra = f"\n\nIllness: **{illness[0]}**: {illness[1]}"
    embed = howlbert_embed(
        "Quarantined",
        f"**{target['wolf_name']}** is isolated in the sick den. "
        f"They cannot spread illness or join pack activities until released.{extra}",
        color=SUCCESS_COLOR,
    )