"""Wolf combat fundamentals and maneuver reference (adapted from warrior RP guides)."""

from __future__ import annotations

COMBAT_GUIDE_TOPICS: dict[str, tuple[str, str]] = {
    "overview": (
        'combat overview',
        'wolf combat blends instinct, pack tactics, and terrain. use `/combat` for initiative fights, `/combat maneuver` for special techniques, and `/rpg action:roll` for skill checks outside combat.\n\n**pinning**; **jump and pin** / **leap-and-hold** pin a foe on a hit (they land **prone** on their back). pinned wolves fight at disadvantage; attacks against them have advantage. while pinning, you can only bite/claw your pinned target. escape with **back kick**, **belly rake**, **half-turn belly rake**, **duck-and-twist**, or **play dead** (must target your pinner). lethal techniques work on a **pinned** foe or one below the listed hp threshold.\n\n**foes**; `/combat npc` adds predators, **clan cats**, hearth-hounds, foxes, and badgers. **`/field action:sniff`** can trigger a **border patrol** fight vs forest cats.\n\n**topics:** `vulnerable` · `stance` · `awareness` · `defense` · `stamina` · `bestiary` · `maneuvers` · `killing` · `injuries` · `crits`',
    ),
    "vulnerable": (
        'vulnerable areas',
        "certain parts of a wolf's body are very sensitive and should always be protected when possible:\n\n**eyes**; easily injured; a blow can disorient or temporarily blind.\n**ears**; thin tissue tears easily; damage can impair hearing.\n**face / muzzle**; injuries here cause intense pain and can hinder breathing.\n**throat**; among the most fatal targets. damage limits breathing and is often deadly in serious fights.\n**spine**; protects the nervous system; injury can cause paralysis or loss of movement.\n**underside / belly**; soft, unprotected, holds vital organs. strikes here cause major injury.\n\nkeep these guarded when you can. striking them is more effective but demands precision and timing; a wild swing leaves you open to counterattacks.",
    ),
    "stance": (
        'stance and balance',
        'a proper stance is essential for stability and control. keep your paws firmly planted and your weight evenly distributed; as in hunting, but stay upright so you are harder to tackle.\n\ngood balance lets you react to sudden movement, dodge incoming attacks, and keep your footing in close combat. losing balance leaves you very vulnerable to strikes.',
    ),
    "awareness": (
        'awareness',
        'combat is not only strength; it is observation. stay aware of your surroundings, your opponent, and escape routes.\n\nwatch for shifts in posture, tension in muscle, or changes in direction; these often signal an incoming attack. awareness buys time to react and defend.',
    ),
    "defense": (
        'defense',
        'dodging and repositioning are key. instead of absorbing every blow head-on, step aside, shift your weight, or move out of range.\n\nstaying mobile makes clean hits harder to land and lets you control the flow of the fight; often opening space for a counterattack.',
    ),
    "stamina": (
        'energy and stamina',
        'combat is physically demanding; conserve energy when you can.\n\nexhaustion slows reactions and weakens strikes, making defeat more likely. know when to engage and when to disengage; an honorable warrior recovers when they must.',
    ),
    "bestiary": (
        'bestiary; forest foes',
        'npc opponents from **`/combat npc`** (recruitment phase):\n\n**predators**; coyote, cougar, bears, wolverine, **fox**, **badger**, cornered deer/elk\n**hearth-hounds**; feral, guard, hunting, fighting (twoleg allies)\n**clan cats**; warrior, deputy, rogue, loner, kittypet (warrior cats-style rivals)\n**reptiles & vermin**; water snake, garter snake, skink, wolf spider (pack-weighted on hunt/explore/patrol)\n\ncats are quick (high dexterity), use **claw** attacks, and fight with maneuvers (forepaw slash, badger defence, rakes); they **cannot pin** adult wolves. badgers are slow but brutal; use **badger defence** against them. foxes hit-and-run.\n\n**size**; only same-size or larger fighters can **pin**. pups and juveniles count as **small**.\n\n**border patrols**; **`/field action:sniff`** may start a live fight vs a patrol cat (~12% when no wolf encounter). drive them off for **+standing**, **+mood**, and a small bone haul.\n**cat pacts**; **`/pact`** (alpha/diplomat) lowers border fights; violating trust has consequences.\n\nsee also: `/combat hazard` for two-legs, thunderpath, traps, and fences.',
    ),
}

COMBAT_MANEUVER_LIST: list[dict] = [
    {'key': 'head_butt', 'name': 'head butt', 'summary': "drive your skull into the opponent's chest or shoulder to stagger them.", 'attr': 'str', 'damage_die': 4, 'attack_bonus': 0, 'lethal': False, 'requires_self_unpinned': True},
    {'key': 'back_kick', 'name': 'back kick', 'summary': 'while pinned, thrust hind legs backward into your pinner.', 'attr': 'dex', 'damage_die': 6, 'attack_bonus': 1, 'lethal': False, 'requires_self_pinned': True, 'target_must_be_pinner': True, 'clears_self_pin_on_hit': True},
    {'key': 'belly_rake', 'name': 'belly rake', 'summary': "while pinned, rake hind claws across the pinner's underside.", 'attr': 'dex', 'damage_die': 8, 'attack_bonus': 0, 'lethal': False, 'requires_self_pinned': True, 'target_must_be_pinner': True, 'clears_self_pin_on_hit': True},
    {'key': 'front_paw_blow', 'name': 'front paw blow', 'summary': 'bring a forepaw down on the head or shoulders to interrupt movement.', 'attr': 'str', 'damage_die': 6, 'attack_bonus': 0, 'lethal': False, 'requires_self_unpinned': True},
    {'key': 'forepaw_slash', 'name': 'forepaw slash', 'summary': 'swipe across the face or upper body to create an opening.', 'attr': 'dex', 'damage_die': 6, 'attack_bonus': 0, 'lethal': False, 'requires_self_unpinned': True},
    {'key': 'leap_and_hold', 'name': 'leap-and-hold', 'summary': "leap onto the opponent's back and pin them.", 'attr': 'dex', 'damage_die': 4, 'attack_bonus': 2, 'lethal': False, 'requires_self_unpinned': True, 'requires_no_active_pin': True, 'requires_target_unpinned': True, 'applies_pin_on_hit': True},
    {'key': 'duck_and_twist', 'name': 'duck-and-twist', 'summary': 'while pinned, roll to throw your pinner off and break free.', 'attr': 'dex', 'damage_die': 4, 'attack_bonus': 2, 'defense_bonus': 2, 'lethal': False, 'requires_self_pinned': True, 'target_must_be_pinner': True, 'clears_self_pin_on_hit': True},
    {'key': 'play_dead', 'name': 'play dead', 'summary': 'while pinned, go limp; break free when the pinner loosens up.', 'attr': 'cha', 'damage_die': 0, 'attack_bonus': -2, 'lethal': False, 'requires_self_pinned': True, 'target_must_be_pinner': True, 'clears_self_pin_on_hit': True},
    {'key': 'scruff_shake', 'name': 'scruff shake', 'summary': 'grip the scruff and shake; best on smaller opponents.', 'attr': 'str', 'damage_die': 6, 'attack_bonus': 0, 'prof_skill': 'hunting', 'lethal': False, 'requires_self_unpinned': True, 'requires_smaller_target': True},
    {'key': 'tail_yank', 'name': 'tail yank', 'summary': 'pull the tail to disrupt balance and movement.', 'attr': 'dex', 'damage_die': 4, 'attack_bonus': 1, 'lethal': False, 'requires_self_unpinned': True},
    {'key': 'teeth_grip', 'name': 'teeth grip', 'summary': 'bite and hold scruff, limb, or ear while paws stay free.', 'attr': 'str', 'damage_die': 4, 'attack_bonus': 0, 'lethal': False, 'requires_self_unpinned': True},
    {'key': 'upright_lock', 'name': 'upright lock', 'summary': 'rear on hind legs and wrestle for balance at close range.', 'attr': 'str', 'damage_die': 6, 'attack_bonus': 0, 'lethal': False, 'requires_self_unpinned': True},
    {'key': 'half_turn_belly_rake', 'name': 'half-turn belly rake', 'summary': "while pinned, half-turn and rake the pinner's belly to escape.", 'attr': 'dex', 'damage_die': 8, 'attack_bonus': 0, 'lethal': False, 'requires_self_pinned': True, 'target_must_be_pinner': True, 'clears_self_pin_on_hit': True},
    {'key': 'badger_defence', 'name': 'badger defence', 'summary': 'leap aside then strike limbs; used against larger opponents.', 'attr': 'dex', 'damage_die': 6, 'attack_bonus': 2, 'lethal': False, 'requires_self_unpinned': True},
    {'key': 'jump_and_pin', 'name': 'jump and pin', 'summary': "rebound off terrain onto an opponent's back and pin them.", 'attr': 'dex', 'damage_die': 6, 'attack_bonus': 2, 'lethal': False, 'requires_self_unpinned': True, 'requires_no_active_pin': True, 'requires_target_unpinned': True, 'applies_pin_on_hit': True},
    {'key': 'low_dodge', 'name': 'low dodge', 'summary': 'drop low and slip under a high strike.', 'attr': 'dex', 'damage_die': 0, 'attack_bonus': -4, 'defense_bonus': 4, 'lethal': False, 'requires_self_unpinned': True},
    {'key': 'duo_fight', 'name': 'duo fight', 'summary': 'back-to-back with packmates to cover blind spots (requires allies in rp).', 'attr': 'wis', 'damage_die': 4, 'attack_bonus': 1, 'lethal': False, 'requires_self_unpinned': True},
    {'key': 'killing_bite', 'name': 'killing bite', 'summary': 'a crushing throat bite; only when life is on the line.', 'attr': 'str', 'damage_die': 12, 'attack_bonus': 2, 'prof_skill': 'hunting', 'vulnerable': True, 'lethal': True, 'min_defender_hp_pct': 0.35, 'requires_self_unpinned': True},
    {'key': 'spine_bite', 'name': 'spine bite', 'summary': 'clamp the upper spine; high risk, potentially paralyzing.', 'attr': 'str', 'damage_die': 10, 'attack_bonus': 0, 'prof_skill': 'hunting', 'vulnerable': True, 'lethal': True, 'min_defender_hp_pct': 0.5, 'requires_self_unpinned': True},
    {'key': 'neck_snap', 'name': 'neck snap', 'summary': 'twist sharply at the neck from a secure hold.', 'attr': 'str', 'damage_die': 10, 'attack_bonus': 1, 'lethal': True, 'min_defender_hp_pct': 0.4, 'requires_self_unpinned': True},
    {'key': 'skull_smash', 'name': 'skull smash', 'summary': 'drive forepaws or body onto the head, slamming into ground or stone.', 'attr': 'str', 'damage_die': 12, 'attack_bonus': 0, 'vulnerable': True, 'lethal': True, 'min_defender_hp_pct': 0.45, 'requires_self_unpinned': True},
]

COMBAT_MANEUVERS = {m['key']: m for m in COMBAT_MANEUVER_LIST}

COMBAT_GUIDE_TOPICS["maneuvers"] = (
    "combat maneuvers",
    "use `/combat maneuver` during your turn (or the **maneuver** menu in combat). "
    "each technique has its own risk and reward.\n\n"
    + "\n".join(
        f"**{m['name']}**; {m['summary']}"
        for m in COMBAT_MANEUVER_LIST
        if not m.get("lethal")
    ),
)

COMBAT_GUIDE_TOPICS["killing"] = (
    "⚠️ lethal techniques",
    "use these **only** in life-threatening situations. they carry grave consequences "
    "in rp and may draw elder scrutiny.\n\n"
    + "\n".join(
        f"**{m['name']}**; {m['summary']}"
        for m in COMBAT_MANEUVER_LIST
        if m.get("lethal")
    ),
)

MANEUVER_DETAIL: dict[str, str] = {
    "head_butt": "lower your head and drive into the opponent's chest or shoulder. useful to stagger and interrupt a charge.",
    "back_kick": 'while **pinned**, shift weight forward and thrust hind legs into your pinner. on a hit you break free.',
    "belly_rake": "while **pinned**, rake hind claws across your pinner's underside. on a hit you break free.",
    "front_paw_blow": 'raise a forepaw and bring it down on the head or shoulders to stagger or interrupt movement.',
    "forepaw_slash": 'swipe across the face or upper body instead of striking downward; creates openings or pushes the opponent back.',
    "leap_and_hold": "leap onto the opponent's back. on a hit they are **pinned** beneath you.",
    "duck_and_twist": 'while **pinned**, twist and roll to throw your pinner off. on a hit you break free.',
    "play_dead": 'while **pinned**, go completely still until the pinner loosens up. on a successful feint you break free.',
    "scruff_shake": 'grip the scruff and shake firmly to disorient a smaller opponent or reposition them.',
    "tail_yank": 'grab and pull the tail to disrupt balance and create space for a follow-up.',
    "teeth_grip": 'bite and hold scruff, limb, or ear while keeping forepaws free for another action.',
    "upright_lock": 'both wolves rear on hind legs and wrestle for balance and positioning.',
    "half_turn_belly_rake": "while **pinned**, turn onto your side and rake your pinner's belly. on a hit you break free.",
    "badger_defence": 'against larger opponents: leap aside from direct strikes, then target limbs to limit their mobility.',
    "jump_and_pin": "use trees, rocks, or rises to rebound onto an opponent's back. on a hit they are **pinned**.",
    "low_dodge": 'drop closer to the ground and slip under a high swing or paw attack.',
    "duo_fight": 'stand back-to-back with packmates to cover blind spots. can expand into a circle against surrounding threats.',
    "killing_bite": 'a crushing bite at the throat until breathing stops. **only in life-threatening situations.**',
    "spine_bite": 'lunge onto the back and clamp the upper spine. a finishing move when the opponent is already weakened; high risk of spinal injury.',
    "neck_snap": 'from a secure hold, twist sharply at the neck with jaws and forepaws.',
    "skull_smash": 'drive forepaws or your full weight onto the head, slamming into ground or stone.',
}

from herbs import INJURIES, INJURY_TABLE

_INJURY_LINES = "\n".join(
    f"**{i}. {INJURIES[key]['name']}**; {INJURIES[key]['effect']}"
    for i, key in enumerate(INJURY_TABLE, start=1)
)

COMBAT_GUIDE_TOPICS["injuries"] = (
    "injury table (1d10)",
    "roll **1d10** whenever a wolf **drops to 0 hp** or takes a **critical hit**.\n\n"
    + _INJURY_LINES
    + "\n\n**spine bite** (`/combat maneuver`) can inflict **spinal injury** (temporary; str/dex at disadvantage, but you can still range out) "
    "or **paralyzed** (permanent; den-bound) instead of the table roll.\n\n"
    "deep gashes bleed each sunrise until bandaged. infected wounds need a daily save. "
    "treat with `/medic action:treat` and herbs from `/bones action:inventory`.",
)

COMBAT_GUIDE_TOPICS["crits"] = (
    "critical hits & fumbles",
    "**natural 20 (critical hit)**; roll 1d4 for extra effect:\n"
    "1. bonus damage (+1d4)\n"
    "2. knock target prone\n"
    "3. off balance; a solid hit knocks the target off its footing, its next claw swipe weaker\n"
    "4. temporary bleed: 1 hp/round for 3 rounds (3 hp applied in combat)\n\n"
    "**natural 1 (critical fumble)**; roll 1d4:\n"
    "1. drop guard; enemy gets a free attack on you\n"
    "2. strain muscle; disadvantage on your next attack roll\n"
    "3. stumble; you fall prone\n"
    "4. bite own tongue: 1 damage; cannot speak or use vocal skills for 1 round",
)
