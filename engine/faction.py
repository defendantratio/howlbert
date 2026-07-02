"""Human faction system: observe, approach, trade, raid, sabotage."""
from __future__ import annotations

import random

import database as db
from engine.dice import roll_d20

FACTIONS = {
    "lowland_settlements": "Lowland Settlements",
    "thorne_lumber": "Thorne Lumber",
    "river_mill": "River Mill",
    "the_crows": "The Crows",
    "university_expedition": "University Expedition",
}

OAK_KNOT_THRESHOLD = 5

_OBSERVE_FLAVOR: dict[str, list[str]] = {
    "lowland_settlements": [
        "A cluster of smoke-stacks visible through the pines. Humans move between buildings in the early light, voices carrying on the wind.",
        "Children play at the settlement's edge, kicking rocks into the mud. The smell of cooked meat drifts toward you.",
        "A dog barks somewhere inside the fence line, then stops. No alarm is raised.",
        "The settlement has added a new outbuilding since you last watched. Something changes there, slowly.",
    ],
    "thorne_lumber": [
        "The chain-saw sound starts before dawn. By the time you reach the ridge, three more trees have come down.",
        "A crew of humans in orange vests marks trees with orange paint at the edge of Thistlehide territory.",
        "The log stacks grow taller each day. The Thunderpath is busier. The forest remembers none of it.",
        "Their machines sleep tonight. The humans eat beside a fire. The silence after a day of cutting is strange and wrong.",
    ],
    "river_mill": [
        "The water downstream runs grey-green. Whatever they're putting in it, your throat closes when you sniff too close.",
        "The mill runs through the night now. The wheel turns and turns, and the river bends around it like a scar.",
        "You count six humans on-site, one asleep in the cab of a rusted machine. The smell of rot comes from the outflow pipe.",
        "A fish turns belly-up in the current below the mill. First of the day. Unlikely to be the last.",
    ],
    "the_crows": [
        "Three crows settle in a line on the old fence post. They tilt their heads at you. One of them has something shiny in its beak.",
        "The Crows' camp is quiet today, but the smoke still rises. Someone is home.",
        "You catch a whiff of something rancid. The Crows have made a meal of another pack's loss. Business as usual.",
        "One of them watches you from the road sign, not moving. You get the feeling they know exactly who you are.",
    ],
    "university_expedition": [
        "They have set up a camera trap near the east border. The light blinks red in the dark.",
        "The expedition tent is larger than last week. More of them have arrived. One has binoculars.",
        "The researcher with the red jacket is taking samples from the creek bed again. She doesn't look up.",
        "Their notebook — left open on a rock — shows a sketch of wolf tracks. Your tracks, probably.",
    ],
}

_APPROACH_SUCCESS: dict[str, list[str]] = {
    "lowland_settlements": [
        "You sit, visible, at the field's edge at dusk. A farmer watches from the porch, then goes back inside. No shouting. Progress.",
        "A child leaves a meat scrap near the fence line. Whether it was for you is unclear. You accept it anyway.",
    ],
    "thorne_lumber": [
        "You let a logging crew pass without challenge. One of them looks back. The truce is wordless, and that makes it real.",
    ],
    "river_mill": [
        "You appear on the mill bank, visible in broad daylight, then vanish. The workers talk about it. It unsettles something in them.",
    ],
    "the_crows": [
        "The crow on the fence drops the bottle-cap at your feet and waits. You sit. It ruffles its feathers and regards you with something like respect.",
        "They leave a small cache of bones and metal scraps near the usual crossing. The message is clear enough.",
    ],
    "university_expedition": [
        "The researcher with the red jacket sets down her clipboard, holds perfectly still, and watches you for six minutes. You don't run. She smiles.",
        "They photograph you at forty meters. You don't flee. In their notebook this becomes a 'trust event.' Whatever that means.",
    ],
}

_APPROACH_FAIL: dict[str, list[str]] = {
    "lowland_settlements": [
        "A man with a rifle comes to the porch. You leave before it becomes a problem.",
        "The settlement dogs lose their minds and you retreat with your ears back.",
    ],
    "thorne_lumber": [
        "A logger throws a stone. You go. No blood, but no ground gained either.",
    ],
    "river_mill": [
        "The workers run an engine at you. The sound is wrong in your skull and you bolt before you mean to.",
    ],
    "the_crows": [
        "Three of them mob you until you clear the territory. Tomorrow, maybe. Not today.",
    ],
    "university_expedition": [
        "You get too close. The researcher startles, drops her camera, and shouts. You're gone before she recovers, but she saw you up close.",
    ],
}

_TRADE_LINES: dict[str, list[str]] = {
    "the_crows": [
        "The crow's cache contains a tangle of wire, half a glove, and three shining stones. Useful in ways you can't quite name yet.",
        "They leave behind a coil of something useful. You leave bones. The exchange is silent, dignified, and entirely strange.",
    ],
    "lowland_settlements": [
        "You leave the deer haunch near the barn. By morning it's gone. A bucket of clean water sits in its place. You drink.",
        "The offering is received. An old woman watches from the window. She nods, once, slowly.",
    ],
    "university_expedition": [
        "You allow the researcher to take a hair sample from a fence-snag. She leaves meat. It's a transaction you both pretend means nothing else.",
    ],
    "thorne_lumber": [
        "You patrol the cutting edge without engaging. The crew watches. The trees at the very edge stay standing. For now.",
    ],
    "river_mill": [
        "You let the mill workers pass through your stretch of river unmarked. They don't notice. Tolerance is its own kind of trade.",
    ],
}

_RAID_SUCCESS: dict[str, list[str]] = {
    "thorne_lumber": [
        "You harass the night crew until they pack up and leave the ridge three days early. The trees on that slope stand another season.",
        "One coordinated rush sends the machinery crew back to their vehicles. They radio in. The cut stops. For now.",
    ],
    "river_mill": [
        "You spook the horses pulling supply carts. Three hours of delay. The outflow pipe sits quiet while they chase them down.",
        "The mill's dog is chased into the river and has to be fished out. Operations halt. You count it as a win.",
    ],
    "lowland_settlements": [
        "The chickens scatter and the humans spend the afternoon rounding them up. You cost them a day's work.",
    ],
    "the_crows": [
        "You drive them from the old fence post. They regroup two fields over. Their operation shifts.",
    ],
    "university_expedition": [
        "You harass their camp enough that two researchers pack up and leave early. The data they gathered is incomplete.",
    ],
}

_RAID_FAIL: dict[str, list[str]] = {
    "thorne_lumber": [
        "The crew had dogs. You got closer than you should have before pulling back.",
        "The machinery doesn't scare. You do.",
    ],
    "river_mill": [
        "The workers light flares. You weren't ready for that. The raid falls apart at the first flash.",
    ],
    "lowland_settlements": [
        "The rifle comes out faster than you expected. No blood, but your nerves are in pieces.",
    ],
    "the_crows": [
        "The murder assembles faster than you can count. You retreat with more dignity than you feel.",
    ],
    "university_expedition": [
        "They had a horn. The sound carried your retreat further than you'd like.",
    ],
}

_SABOTAGE_SUCCESS_THORNE = [
    "You gnaw through the guide rope on their largest machine. By morning it lists at an unworkable angle. The cut stops.",
    "You collapse the equipment shed's support beam in the night. It takes them two days to clear and rebuild. Two silent days in the forest.",
    "You contaminate the fuel storage with creek mud. The machines seize. The silence that follows is worth it.",
    "The Memory-Knot remembers. Another notch in the bark. The oak bends but has not yet broken.",
]

_SABOTAGE_SUCCESS_MILL = [
    "You block the intake pipe with debris. The wheel stalls. The grey water stops flowing for a night.",
    "You destroy the secondary coupling on the outflow. Repairs take three days. The river runs clear until then.",
]

_SABOTAGE_FAIL = [
    "The attempt fails — heard, spotted, or simply wrong-timed. You pull back with nothing to show.",
    "A guard catches your scent before you reach the objective. You scatter into the dark.",
]

_ELIZA_HARROW_LINES = [
    "A woman in field gear crouches over her notes. You can read, just barely: **'Skye = Bitterroot'** — a name for a plant, or for a wolf. Hard to say.",
    "The researcher you know as **Eliza Harrow** is here again. She speaks quietly into a recorder, says the name *Skye* twice, pauses, then writes something down.",
    "She hasn't seen you. Her notebook is open. The page header reads: **E. HARROW — SILVERRUSH TERRITORY SURVEY**. One line is circled: *Bitterroot stands at the crossing.*",
]

_LUCID_LINES = [
    "A dog emerges from the shadow of the wheel-house. **Not feral — domestic.** Collar, clipped nails, fed. It looks at you the way a wolf looks at a wolf. Then it sits. Then it leaves.",
    "The mill's dog is not like other dogs. It holds your gaze for fifteen seconds before turning away. Its name, you somehow know without knowing, is **Lucid**.",
    "The domestic dog — Lucid, the workers call it — plants itself between you and the outflow pipe. Not aggressive. Just present. Like it's been waiting.",
]


def standing_label(standing: int) -> str:
    if standing >= 20:
        return "revered"
    if standing >= 10:
        return "trusted"
    if standing >= 1:
        return "cautious peace"
    if standing == 0:
        return "neutral"
    if standing >= -10:
        return "wary"
    if standing >= -20:
        return "hostile"
    return "hunted"


def faction_display_name(faction: str) -> str:
    return FACTIONS.get(faction, faction.replace("_", " ").title())


def try_faction_observe(user, faction: str) -> tuple[str, int]:
    """Returns (flavor_text, standing_change). Observe never costs standing."""
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    standing = db.get_faction_standing(gp or "", faction) if gp else 0
    pool = _OBSERVE_FLAVOR.get(faction, ["You watch from a distance. Nothing extraordinary."])
    line = random.choice(pool)
    extra = ""
    if standing >= 10:
        extra = "\n_Your pack's standing grants you better reads on their intent._"
    return line + extra, 0


def try_faction_approach(user, faction: str, *, day: int) -> tuple[str, int]:
    """Roll approach. Returns (flavor, standing_delta)."""
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    die = roll_d20()
    attr_wis = int(user["attr_wis"]) if "attr_wis" in user.keys() else 0
    from engine.character import attr_modifier
    mod = attr_modifier(attr_wis)
    total = die + mod
    dc = 12
    if total >= dc + 5:
        pool = _APPROACH_SUCCESS.get(faction, ["A promising contact."])
        delta = 3
    elif total >= dc:
        pool = _APPROACH_SUCCESS.get(faction, ["A cautious contact."])
        delta = 1
    elif total >= dc - 5:
        pool = _APPROACH_FAIL.get(faction, ["They don't welcome you."])
        delta = -1
    else:
        pool = _APPROACH_FAIL.get(faction, ["A poor showing."])
        delta = -3
    text = random.choice(pool)
    roll_note = f"\n\n_roll: **{die}** + wis **{mod:+}** = **{total}** vs dc {dc}_ · standing change: **{delta:+}**"
    return text + roll_note, delta


def try_faction_trade(user, faction: str) -> tuple[str, int]:
    """Trade: costs 3 bones, guaranteed +2 standing if bones available."""
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    bones = int(user["bones"]) if "bones" in user.keys() else 0
    if bones < 3:
        return f"A trade requires **3 bones**; you have **{bones}**.", 0
    discord_id = int(user["discord_id"]) if "discord_id" in user.keys() else 0
    db.deduct_bones(discord_id, 3)
    pool = _TRADE_LINES.get(faction, ["The exchange is made, quietly."])
    text = random.choice(pool)
    delta = 2
    eliza = ""
    if faction == "university_expedition" and gp == "silverrush" and random.random() < 0.5:
        eliza = f"\n\n{random.choice(_ELIZA_HARROW_LINES)}"
    return text + eliza + f"\n\n_−3 bones · standing change: **+{delta}**_", delta


def try_faction_raid(user, faction: str) -> tuple[str, int, bool]:
    """
    Raid: roll d20 vs dc 13. Returns (flavor, standing_delta, caught).
    If caught, standing with ALL factions drops -1 (caller must handle).
    """
    die = roll_d20()
    attr_str = int(user["attr_str"]) if "attr_str" in user.keys() else 0
    from engine.character import attr_modifier
    mod = attr_modifier(attr_str)
    total = die + mod
    dc = 13
    if total >= dc:
        pool = _RAID_SUCCESS.get(faction, ["You drive them back."])
        delta = -2
        caught = False
    else:
        pool = _RAID_FAIL.get(faction, ["The raid fails."])
        delta = -1
        caught = True
    text = random.choice(pool)
    roll_note = f"\n\n_roll: **{die}** + str **{mod:+}** = **{total}** vs dc {dc}_"
    caught_note = "\n_word spreads — all factions note the aggression_ (−1 each)" if caught else ""
    return text + roll_note + caught_note, delta, caught


def try_faction_sabotage(user, faction: str, *, guild_id: int, day: int) -> tuple[str, int]:
    """
    Sabotage: roll d20 vs dc 15. Thistlehide/thorne_lumber increments oak_knot.
    Silverrush/river_mill has Lucid encounter chance.
    Returns (flavor, standing_delta).
    """
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    die = roll_d20()
    attr_dex = int(user["attr_dex"]) if "attr_dex" in user.keys() else 0
    from engine.character import attr_modifier
    mod = attr_modifier(attr_dex)
    total = die + mod
    dc = 15
    if total >= dc:
        if faction == "thorne_lumber":
            pool = _SABOTAGE_SUCCESS_THORNE
            oak = db.increment_world_oak_knot(guild_id)
            oak_note = (
                f"\n\n_Memory-Knot: **{oak}/{OAK_KNOT_THRESHOLD}** notches carved._"
                if oak < OAK_KNOT_THRESHOLD
                else "\n\n**The Memory-Knot is full.** Five sabotages complete. The forest has a long memory."
            )
        elif faction == "river_mill":
            pool = _SABOTAGE_SUCCESS_MILL
            oak_note = ""
        else:
            pool = [f"The {faction_display_name(faction)} operation is disrupted."]
            oak_note = ""
        text = random.choice(pool) + oak_note
        delta = -3
    else:
        text = random.choice(_SABOTAGE_FAIL)
        delta = -1
    lucid_note = ""
    if faction == "river_mill" and gp == "silverrush" and random.random() < 0.35:
        lucid_note = f"\n\n{random.choice(_LUCID_LINES)}"
    roll_note = f"\n\n_roll: **{die}** + dex **{mod:+}** = **{total}** vs dc {dc}_ · faction standing: **{delta:+}**"
    return text + lucid_note + roll_note, delta
