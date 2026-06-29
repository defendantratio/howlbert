import database as db
from config import WEATHER_HUNT_MODIFIERS
from engine.mood import HUNT_ACTIVITIES, apply_mood_bone_penalty, user_mood
from engine.hunger import apply_hunger_bone_penalty, user_hunger
from engine.thirst import apply_thirst_bone_penalty, user_thirst
from engine.movement_penalties import apply_movement_hunt_penalty
from engine.pack_unity import apply_unity_to_hunt_amount
from engine.prestige import apply_bone_bonus
from engine.season_effects import apply_season_hunt, season_hunt_modifier_label
from engine.shop_items import lucky_tooth_hunt_bonus


def apply_weather(amount: int, weather: str) -> int:
    if amount <= 0:
        return 0
    modifier = WEATHER_HUNT_MODIFIERS.get(weather, 0)
    return max(0, int(amount * (100 + modifier) / 100))


def weather_hunt_modifier_label(weather: str) -> str | None:
    mod = WEATHER_HUNT_MODIFIERS.get(weather, 0)
    if mod == 0:
        return None
    return f"{mod:+d}% hunt bones ({weather})"


def apply_pack_tax(amount: int, pack_id: int | None) -> tuple[int, int]:
    if amount <= 0 or not pack_id:
        return amount, 0
    pack = db.get_pack(pack_id)
    if not pack or pack["tax_rate"] <= 0:
        return amount, 0
    tax = int(amount * pack["tax_rate"] / 100)
    if tax > 0:
        db.add_pack_treasury(pack_id, tax)
    return amount - tax, tax


def pack_tax_treasury_note(tax: int, pack_id: int | None) -> str:
    """Short footer fragment when hunt/work earnings include pack tax."""
    if tax <= 0:
        return ""
    if pack_id:
        pack = db.get_pack(pack_id)
        if pack:
            return f"{tax}🦴 to {pack['name']} treasury (`/pack treasury`)"
    return f"{tax}🦴 to den treasury (`/pack treasury`)"


def award_bones(
    user,
    gross_amount: int,
    weather: str,
    activity: str,
    *,
    season: str | None = None,
    guild_id: int | None = None,
    day: int | None = None,
) -> tuple[int, int, int, int, str, str, str, str, str]:
    """Returns (net, tax, gross_after_modifiers, lucky_bonus, mood_note, hunger_note, thirst_note, exhaustion_note, season_note)."""
    account = db.get_account(user["discord_id"])
    amount = apply_weather(gross_amount, weather)
    season_note = ""
    if activity in HUNT_ACTIVITIES and season:
        before = amount
        amount = apply_season_hunt(amount, season)
        if amount != before:
            season_note = season_hunt_modifier_label(season)
    if activity in HUNT_ACTIVITIES and guild_id is not None:
        from engine.plot_blinking import plot_activity_payout_mult

        gp = user["great_pack"] if "great_pack" in user.keys() else None
        mult, plot_note = plot_activity_payout_mult(guild_id, activity, great_pack=gp)
        if mult != 1.0:
            amount = max(0, int(amount * mult))
        if plot_note:
            season_note = f"{season_note} · {plot_note}" if season_note else plot_note
    amount = apply_bone_bonus(amount, account["prestige_tier"])
    mood_note = ""
    hunger_note = ""
    thirst_note = ""
    exhaustion_note = ""
    if activity in HUNT_ACTIVITIES:
        amount, mood_note = apply_mood_bone_penalty(amount, user_mood(user))
        amount, hunger_note = apply_hunger_bone_penalty(amount, user_hunger(user))
        amount, thirst_note = apply_thirst_bone_penalty(amount, user_thirst(user))
        amount, exhaustion_note = apply_movement_hunt_penalty(amount, user)
    lucky_bonus = 0
    if activity == "hunt":
        amount, lucky_bonus = lucky_tooth_hunt_bonus(user["discord_id"], amount)
        if user["pack_id"]:
            unity = db.get_pack_unity(user["pack_id"])
            amount = apply_unity_to_hunt_amount(amount, unity)
            if guild_id is not None and day is not None:
                from engine.territory_marking import home_turf_hunt_bonus

                gp = user["great_pack"] if "great_pack" in user.keys() else None
                turf_mult, turf_note = home_turf_hunt_bonus(int(user["pack_id"]), gp, guild_id, day)
                if turf_mult != 1.0:
                    amount = int(amount * turf_mult)
                    season_note = f"{season_note} · {turf_note}" if season_note else turf_note
            if day is not None:
                from engine.pack_unity import overhunting_hunt_multiplier

                hunts_today = db.record_pack_hunt_and_get_count(int(user["pack_id"]), day)
                over_mult, over_note = overhunting_hunt_multiplier(hunts_today)
                if over_mult != 1.0:
                    amount = int(amount * over_mult)
                    season_note = f"{season_note} · {over_note}" if season_note else over_note
    net, tax = apply_pack_tax(amount, user["pack_id"])
    if net > 0:
        db.add_bones(user["discord_id"], net, wolf_id=user["id"])
    if activity not in ("work", "crime"):
        db.increment_quest_progress(user["discord_id"], activity, wolf_id=user["id"], guild_id=guild_id)
    if activity == "hunt":
        db.record_hunt(user["discord_id"])
    tax_note = pack_tax_treasury_note(tax, user["pack_id"])
    if tax_note:
        season_note = f"{season_note} · {tax_note}" if season_note else tax_note
    return net, tax, amount, lucky_bonus, mood_note, hunger_note, thirst_note, exhaustion_note, season_note


def roll_range(bounds: tuple[int, int]) -> int:
    import random
    return random.randint(bounds[0], bounds[1])
