import random



from engine.character import attr_modifier, get_attr

from engine.dice import roll_d20



# hazard_key → (label, attribute, env_bonus_severe, env_bonus_extreme)

WEATHER_HAZARDS = {

    "blizzard": ("Blizzard", "attr_con", 5, 8),

    "flood": ("Flood / Rapid River", "attr_str", 4, 8),

    "wildfire_smoke": ("Wildfire Smoke", "attr_con", 6, 6),

    "freezing_rain": ("Freezing Rain / Ice", "attr_dex", 4, 4),

    "extreme_heat": ("Extreme Heat", "attr_con", 5, 5),

    "thick_fog": ("Thick Fog", "attr_con", 4, 4),

    "thunderstorm": ("Thunderstorm", "attr_cha", 6, 6),

    "avalanche": ("Avalanche", "attr_dex", 8, 8),

    "deep_snow": ("Deep Snow", "attr_str", 3, 7),

    "quicksand": ("Quicksand / Mud Bog", "attr_str", 6, 6),

}



SEVERITY_CHOICES = {

    "moderate": 0,

    "severe": 1,

    "extreme": 2,

}



FAILURE_TEXT = {

    "blizzard": "gain 1 exhaustion; lose 1d4 hours.",

    "flood": "swept downstream: 1d4 damage, end 1d6 miles away.",

    "wildfire_smoke": "Disadvantage on Perception until clean air.",

    "freezing_rain": "Fall: 1d4 damage, speed halved 1 minute.",

    "extreme_heat": "Heat exhaustion until shade and water.",

    "thick_fog": "Lose 1d4 hours; may wander into hazard.",

    "thunderstorm": "Frightened; flee to cover, no actions 1 minute.",

    "avalanche": "2d6 damage, buried; Strength DC 15 to dig out.",

    "deep_snow": "1 exhaustion; speed halved for the day.",

    "quicksand": "Sink deeper; needs opposed Strength rescue.",

}





def hazard_failure_effects(hazard_key: str, *, failed: bool, critical: bool = False) -> dict:

    """Side effects applied on failed weather hazard rolls.

    A critical failure on top of exposure hazards risks a lasting injury,
    not just the usual exhaustion/mood hit.
    """

    if not failed:

        return {}

    effects: dict = {}

    if hazard_key in ("blizzard", "deep_snow", "freezing_rain", "quicksand"):

        effects = {"exhaustion": 1}

    elif hazard_key == "extreme_heat":

        effects = {"exhaustion": 1, "thirst_loss": 25}

    elif hazard_key == "wildfire_smoke":

        effects = {"smoke_debuff": 1, "mood_loss": 4}

    elif hazard_key == "thick_fog":

        effects = {"mood_loss": 4}

    elif hazard_key == "thunderstorm":

        effects = {"mood_loss": 6}

    if critical:

        if hazard_key == "extreme_heat":

            effects["injury"] = "heatstroke"

        elif hazard_key in ("blizzard", "deep_snow", "freezing_rain", "avalanche"):

            effects["injury"] = "hypothermia"

        elif hazard_key == "wildfire_smoke":

            effects["injury"] = "smoke_inhalation"

    return effects





def resolve_weather_hazard(user, hazard_key: str, severity: str = "severe") -> dict:

    label, attr_key, mod_mod, mod_ext = WEATHER_HAZARDS[hazard_key]

    sev_idx = SEVERITY_CHOICES.get(severity, 1)

    env_bonus = mod_mod if sev_idx == 1 else (mod_ext if sev_idx == 2 else mod_mod - 2)



    wolf_die = roll_d20()

    env_die = roll_d20()

    wolf_mod = attr_modifier(get_attr(user, attr_key.replace("attr_", "")))

    wolf_total = wolf_die + wolf_mod

    env_total = env_die + env_bonus



    if wolf_die == 1:

        outcome = "critical_failure"

        success = False

    elif wolf_die == 20 and env_die != 20:

        outcome = "critical_success"

        success = True

    elif env_die == 20 and wolf_die != 20:

        outcome = "critical_failure"

        success = False

    elif wolf_total >= env_total:

        outcome = "success"

        success = True

    else:

        outcome = "failure"

        success = False



    extra_damage = 0

    if not success and outcome == "failure":

        if hazard_key in ("flood", "freezing_rain"):

            extra_damage = random.randint(1, 4)

        elif hazard_key == "avalanche":

            extra_damage = random.randint(2, 12)



    effects = hazard_failure_effects(hazard_key, failed=not success, critical=outcome == "critical_failure")



    return {

        "hazard": label,

        "severity": severity,

        "wolf_die": wolf_die,

        "wolf_mod": wolf_mod,

        "wolf_total": wolf_total,

        "env_die": env_die,

        "env_bonus": env_bonus,

        "env_total": env_total,

        "success": success,

        "outcome": outcome,

        "failure_text": FAILURE_TEXT.get(hazard_key, "You suffer the hazard's consequences."),

        "damage": extra_damage,

        "effects": effects,

    }





def format_hazard_result(r: dict) -> str:

    lines = [

        f"**{r['hazard']}** ({r['severity']})",

        f"you: {r['wolf_die']} + {r['wolf_mod']} = **{r['wolf_total']}**",

        f"environment: {r['env_die']} + {r['env_bonus']} = **{r['env_total']}**",

    ]

    if r["outcome"] == "critical_success":

        lines.append("**critical success**; you weather it brilliantly.")

    elif r["outcome"] == "critical_failure":

        lines.append(f"**critical failure**; {r['failure_text']}")

    elif r["success"]:

        lines.append("**success**; no harm.")

    else:

        lines.append(f"**failure**; {r['failure_text']}")

        if r["damage"]:

            lines.append(f"take **{r['damage']}** damage.")

    effects = r.get("effects") or {}

    if effects.get("exhaustion"):

        lines.append(f"gain **{effects['exhaustion']}** exhaustion.")

    if effects.get("thirst_loss"):

        lines.append(f"**−{effects['thirst_loss']}** hydration; find shade and water.")

    if effects.get("mood_loss"):

        lines.append(f"**−{effects['mood_loss']}** mood.")

    if effects.get("smoke_debuff"):

        lines.append("_smoke in your lungs; disadvantage on perception until next sunrise._")

    return "\n".join(lines)

