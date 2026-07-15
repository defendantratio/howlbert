# Basil TTRPG rules; core mechanics for Howlbert

ATTRIBUTE_MODIFIERS = {
    # score - 5: every point matters (no dead levels), and a specialist truly
    # dominates its niche. midrange (3-6) is unchanged from the old curve, so DCs
    # stay roughly as tuned; only the high and low ends widen. see docs/CHANNELS.md.
    1: -4, 2: -3, 3: -2, 4: -1, 5: 0, 6: 1, 7: 2, 8: 3, 9: 4, 10: 5,
}

DC_TIERS = {
    "easy": 10,
    "moderate": 15,
    "hard": 20,
    "legendary": 25,
}

ROLE_ATTRIBUTE_RANGES = {
    "alpha": (30, 35),
    "advisor": (27, 32),
    "medic": (20, 25),
    "guard": (18, 22),
    "hunter": (16, 20),
    "hunter_apprentice": (14, 18),
    "scout": (16, 20),
    "scout_apprentice": (14, 18),
    "forager": (15, 20),
    "forager_apprentice": (13, 17),
    "diplomat": (15, 20),
    "diplomat_apprentice": (13, 17),
    "elder": (15, 20),
    "caretaker": (12, 18),
    "caretaker_apprentice": (10, 16),
    "juvenile": (12, 16),
    "pup": (8, 12),
    "drown_sick": (12, 18),
    "medic_apprentice": (16, 20),
    "rogue": (15, 20),
    "lowbelly": (12, 18),
    "bog_born": (15, 20),
}

ROLE_DEFAULT_STATS = {
    "alpha": dict(attr_str=7, attr_dex=6, attr_con=6, attr_int=5, attr_cha=6, attr_wis=5),
    "advisor": dict(attr_str=5, attr_dex=5, attr_con=5, attr_int=6, attr_cha=6, attr_wis=6),
    "medic": dict(attr_str=4, attr_dex=5, attr_con=5, attr_int=7, attr_cha=5, attr_wis=7),
    "guard": dict(attr_str=7, attr_dex=5, attr_con=7, attr_int=4, attr_cha=5, attr_wis=5),
    "hunter": dict(attr_str=6, attr_dex=5, attr_con=4, attr_int=1, attr_cha=1, attr_wis=1),
    "hunter_apprentice": dict(attr_str=5, attr_dex=4, attr_con=3, attr_int=2, attr_cha=2, attr_wis=2),
    "scout": dict(attr_str=4, attr_dex=7, attr_con=4, attr_int=5, attr_cha=3, attr_wis=6),
    "scout_apprentice": dict(attr_str=3, attr_dex=6, attr_con=3, attr_int=4, attr_cha=3, attr_wis=5),
    "forager": dict(attr_str=4, attr_dex=4, attr_con=5, attr_int=7, attr_cha=3, attr_wis=5),
    "forager_apprentice": dict(attr_str=3, attr_dex=3, attr_con=4, attr_int=6, attr_cha=3, attr_wis=4),
    "diplomat": dict(attr_str=3, attr_dex=4, attr_con=4, attr_int=5, attr_cha=7, attr_wis=5),
    "diplomat_apprentice": dict(attr_str=3, attr_dex=3, attr_con=3, attr_int=4, attr_cha=6, attr_wis=4),
    "elder": dict(attr_str=3, attr_dex=3, attr_con=4, attr_int=6, attr_cha=6, attr_wis=7),
    "caretaker": dict(attr_str=3, attr_dex=4, attr_con=5, attr_int=4, attr_cha=6, attr_wis=5),
    "caretaker_apprentice": dict(attr_str=3, attr_dex=3, attr_con=4, attr_int=3, attr_cha=5, attr_wis=4),
    "juvenile": dict(attr_str=3, attr_dex=4, attr_con=3, attr_int=2, attr_cha=2, attr_wis=3),
    "pup": dict(attr_str=1, attr_dex=2, attr_con=2, attr_int=2, attr_cha=2, attr_wis=2),
    "drown_sick": dict(attr_str=1, attr_dex=2, attr_con=2, attr_int=4, attr_cha=2, attr_wis=5),
    "medic_apprentice": dict(attr_str=3, attr_dex=4, attr_con=4, attr_int=6, attr_cha=4, attr_wis=6),
    "rogue": dict(attr_str=4, attr_dex=4, attr_con=5, attr_int=4, attr_cha=2, attr_wis=4),
    "lowbelly": dict(attr_str=2, attr_dex=5, attr_con=3, attr_int=4, attr_cha=4, attr_wis=4),
    "bog_born": dict(attr_str=4, attr_dex=3, attr_con=5, attr_int=4, attr_cha=2, attr_wis=4),
}

ROLE_LABELS = {
    "alpha": "Alpha",
    "advisor": "Alpha's Guard / Advisor",
    "medic": "Medic",
    "guard": "Guard",
    "hunter": "Hunter",
    "hunter_apprentice": "Hunter Apprentice",
    "scout": "Scout",
    "scout_apprentice": "Scout Apprentice",
    "forager": "Forager",
    "forager_apprentice": "Forager Apprentice",
    "diplomat": "Diplomat",
    "diplomat_apprentice": "Diplomat Apprentice",
    "elder": "Elder",
    "caretaker": "Caretaker",
    "caretaker_apprentice": "Caretaker Apprentice",
    "juvenile": "Juvenile",
    "pup": "Pup",
    "drown_sick": "Drown-Sick Oracle",
    "medic_apprentice": "Medic Apprentice",
    "rogue": "Rogue",
    "lowbelly": "Lowbelly",
    "bog_born": "Bog-Born",
}

ROLE_FEATURES = {
    "alpha": "Commanding Howl; allies gain advantage on next attack or skill check.",
    "advisor": "Blood Oath; advantage on one Charisma check per sunrise.",
    "medic": "Green Tongue; Herblore substitutes for Medicine; never misidentify plants. No daily limit on treat/heal.",
    "medic_apprentice": "Apprentice Healer; learning poultices under a Medic; herb heals still capped until full rank.",
    "guard": "Defender's Resolve; impose disadvantage when adjacent packmate is attacked.",
    "hunter": "Killer's Instinct; +1d6 damage vs surprised or prone targets. Three hunts per sunrise.",
    "hunter_apprentice": "Blooding Lessons; run with hunters; earn the full Hunter rank through `/role action:event` and role quests.",
    "scout": "Unseen Paw; hide while lightly obscured.",
    "scout_apprentice": "Ridge Pup; border drills and scent-maps; earn Scout when the pack trusts your eyes.",
    "forager": "Nose of the Land; auto-find one common herb/day in pack territory. May forage without waiting for sunrise.",
    "forager_apprentice": "Green Pup; learn plants at a mentor's side; **one forage per sunrise** until full rank.",
    "diplomat": "Silver Tongue; reroll failed Charisma check once/session.",
    "diplomat_apprentice": "Message Carrier; watch parley and carry words between dens.",
    "elder": "Wisdom of Years; reroll any failed skill check once/day.",
    "caretaker": "Soothing Lick; `/playpen action:groom` clears fear/panic and gives **+12 mood** when target is distressed or below 30 mood.",
    "caretaker_apprentice": "Nursery Watch; tend pups and sick wolves under a Caretaker's eye.",
    "juvenile": (
        "Blooding Pending; must kill prey alone to earn an adult role. "
        "Forbidden to mate until then."
    ),
    "pup": (
        "Unnamed Wind; vulnerable; fed by the den. No hunt, combat, or mating. "
        "Survive the first moon to be named."
    ),
    "drown_sick": (
        "Belly-Rip Whispers; hear the Maw's chewing; `/role action:event` yields cryptic prophecy. "
        "Cannot hunt or fight effectively (frail). **+2 Perception** (tracking/stealth/Wisdom) in fog or swamp."
    ),
    "rogue": (
        "Border Thief; scrape by on stolen scraps and trespass; advantaged on Stealth "
        "when crossing pack lines. No den treasury or `/bones action:daily` stipend."
    ),
    "lowbelly": (
        "Invisible Hunger; eats last from the pile; advantage on Stealth when hiding "
        "in dens, caves, or among the pack. Greyspire's lowest rank; challenge to rise."
    ),
    "bog_born": (
        "Swamp Root; Mistmoor native wolf; advantage on Survival and Herblore in bog, "
        "mud, and cypress. Digs dens, graves, and tubers; the pack's quiet backbone."
    ),
}

SKILLS = {
    "herblore": (("attr_int",), "Herblore"),
    "hunting": (("attr_str", "attr_dex", "attr_wis"), "Hunting"),
    "stealth": (("attr_dex",), "Stealth"),
    "tracking": (("attr_wis", "attr_con"), "Tracking"),
    "intimidation": (("attr_cha",), "Intimidation"),
    "persuasion": (("attr_cha",), "Persuasion"),
    "survival": (("attr_con", "attr_str"), "Survival"),
    "medicine": (("attr_wis",), "Medicine"),
}

MAX_SKILL_RANK = 3  # max earned trait bonus per skill from XP / quests
SKILL_RANK_BONUS = 1  # legacy alias
XP_PER_SKILL_RANK = 5  # cost for +1 earned trait bonus
XP_PER_TRAIT = XP_PER_SKILL_RANK
MAX_EARNED_TRAIT_BONUS = MAX_SKILL_RANK
MAX_EARNED_TRAIT_SETBACK = MAX_SKILL_RANK
SKILL_STRAIN_THRESHOLD = 3

ROLE_PROFICIENCIES = {
    "alpha": ("intimidation", "persuasion"),
    "advisor": ("intimidation", "tracking"),
    "medic": ("herblore", "medicine"),
    "medic_apprentice": ("medicine",),
    "guard": ("intimidation", "survival"),
    "hunter": ("hunting", "stealth"),
    "hunter_apprentice": ("hunting",),
    "scout": ("stealth", "tracking"),
    "scout_apprentice": ("tracking",),
    "forager": ("herblore", "survival"),
    "forager_apprentice": ("herblore",),
    "diplomat": ("persuasion", "intimidation"),
    "diplomat_apprentice": ("persuasion",),
    "elder": ("medicine", "herblore"),
    "caretaker": ("persuasion", "medicine"),
    "caretaker_apprentice": ("persuasion",),
    "juvenile": ("hunting", "survival"),
    "pup": ("survival",),
    "drown_sick": ("stealth", "tracking"),
    "rogue": ("stealth", "tracking"),
    "lowbelly": ("stealth", "persuasion"),
    "bog_born": ("herblore", "survival"),
}
