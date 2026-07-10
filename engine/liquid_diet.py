"""Liquid diet: broth and non-wolf milk.

Sentient wolves can sip liquids to stave off starvation when they cannot or will
not eat solid prey (a broken jaw, wasting sickness, or simply no kill). Liquids
never trigger the broken-jaw eating pain the way solid meat does.

Realism built in:
 ; Liquids only partially satiate: hunger from liquids alone is capped at
    LIQUID_HUNGER_CAP. A wolf cannot get truly full, or stay alive indefinitely,
    on broth and milk; a carnivore needs meat (see meatless wasting in the
    rollover). They keep you going, not thriving.
 ; Milk + lactose intolerance: pups still nurse and digest milk fine, but most
    weaned wolves lose the ability. An adult without the `lactase_persistent`
    genetic trait gets the drink's fluid but an upset gut (diarrhea) and little
    nourishment from it.
"""

from __future__ import annotations


import database as db

LIQUID_HUNGER_CAP = 60

# lapping milk as a grown wolf is undignified; costs personal standing
MILK_STANDING_LOSS = 2

# boiling bones into broth at the den
BROTH_BONE_COST = 3

# type -> (item_key, base_hunger, thirst, label)
LIQUIDS = {
    "broth": ("liquid_broth", 15, 8, "warm broth"),
    "milk": ("liquid_milk", 18, 10, "milk"),
}


def is_lactose_intolerant(user) -> bool:
    """Pups nurse fine; weaned wolves are intolerant unless lactase-persistent."""
    from engine.aging import stage_for_age
    from engine.genetics import parse_genetic_conditions

    age = int(user["age_months"]) if "age_months" in user.keys() else 24
    if stage_for_age(age) == "pup":
        return False
    genetics = parse_genetic_conditions(user["genetic_conditions"] if "genetic_conditions" in user.keys() else None)
    return "lactase_persistent" not in genetics


def brew_broth(user) -> tuple[bool, str]:
    """Boil hoarded bones down into broth at the den. Returns (ok, message)."""
    discord_id = int(user["discord_id"])
    bones = int(user["bones"]) if "bones" in user.keys() else 0
    if bones < BROTH_BONE_COST:
        return False, f"boiling broth needs **{BROTH_BONE_COST}** bones (you have **{bones}**)."
    item = db.get_item_by_key("liquid_broth")
    if not item:
        return False, "broth cannot be made yet."
    if not db.deduct_bones(discord_id, BROTH_BONE_COST):
        return False, f"boiling broth needs **{BROTH_BONE_COST}** bones (you have **{bones}**)."
    db.grant_item(discord_id, item["id"])
    return True, (
        f"you simmer bones over the den's cold hearth into **broth** "
        f"(−{BROTH_BONE_COST} bones). sip it with `/drink type:broth`."
    )


def drink_liquid(user, liquid_key: str) -> tuple[bool, str]:
    """Consume a liquid food from inventory. Returns (ok, message)."""
    spec = LIQUIDS.get(liquid_key)
    if not spec:
        return False, "that isn't a liquid you can sip."
    if user["condition"] in ("dead", "dying"):
        return False, "too far gone to sip anything; a medic must stabilize you first."

    item_key, base_hunger, thirst_gain, label = spec
    item = db.get_item_by_key(item_key)
    if not item:
        return False, "that liquid doesn't exist yet."
    discord_id = int(user["discord_id"])
    if db.get_inventory_quantity(discord_id, item["id"]) < 1:
        if liquid_key == "milk":
            return False, "you have no **milk**; barter it from a cat clan (`/pact action:receive`) or raid a settlement (`/faction action:raid`)."
        return False, "you have no **broth**; buy it at the trading post (`/bones action:shop`) or boil your own (`/hoarding action:craft recipe:broth`)."

    hunger = int(user["hunger"]) if "hunger" in user.keys() else 0

    # milk + lactose intolerance
    upset_note = ""
    hunger_gain = base_hunger
    if liquid_key == "milk" and is_lactose_intolerant(user):
        hunger_gain = max(0, base_hunger // 3)
        from engine.disease_contract import try_contract_disease
        got = try_contract_disease(user, "diarrhea", chance=0.6)
        upset_note = "\n_your gut cramps; weaned wolves cannot stomach milk._"
        if got:
            upset_note += f"\n{got}"

    # liquids cannot push hunger past the cap
    if hunger >= LIQUID_HUNGER_CAP:
        capped_hunger = hunger  # already above what liquids can achieve
        cap_note = "\n_you are as full as liquids can make you; only real meat will truly satisfy._"
    else:
        capped_hunger = min(LIQUID_HUNGER_CAP, hunger + hunger_gain)
        cap_note = ""
        if capped_hunger == LIQUID_HUNGER_CAP and hunger_gain > 0:
            cap_note = "\n_filling, but liquids can only take you so far; you still need meat._"

    if not db.consume_item(discord_id, item["id"]):
        return False, f"could not find the **{label}** in your bag."

    new_hunger = db.adjust_hunger(user["id"], capped_hunger - hunger) if capped_hunger != hunger else hunger
    new_thirst = db.adjust_thirst(user["id"], thirst_gain)

    # a grown wolf lapping milk loses face
    standing_note = ""
    if liquid_key == "milk":
        result = db.adjust_wolf_standing(discord_id, -MILK_STANDING_LOSS)
        standing_note = f"\n_a grown wolf lapping milk; the pack notices. standing **-{MILK_STANDING_LOSS}**._"
        if result == "kicked":
            standing_note += "\n_your standing sinks too low; you are cast out._"

    gained = capped_hunger - hunger
    hunger_bit = f"hunger **{new_hunger}** (+{gained})" if gained > 0 else f"hunger **{new_hunger}**"
    msg = f"you lap up **{label}**; {hunger_bit}, hydration **{new_thirst}** (+{thirst_gain}).{cap_note}{upset_note}{standing_note}"
    return True, msg
