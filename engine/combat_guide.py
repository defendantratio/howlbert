"""Wolf combat fundamentals and maneuver reference (adapted from warrior RP guides)."""

from __future__ import annotations

COMBAT_GUIDE_TOPICS: dict[str, tuple[str, str]] = {
    "overview": (
        "Combat Overview",
        "Wolf combat blends instinct, pack tactics, and terrain. Use `/combat` for "
        "initiative fights, `/combat maneuver` for special techniques, and `/roll` for "
        "skill checks outside combat.\n\n"
        "**Pinning**; **Jump and Pin** / **Leap-and-Hold** pin a foe on a hit (they land "
        "**prone** on their back). Pinned wolves fight at disadvantage; attacks against them "
        "have advantage. While pinning, you can only bite/claw your pinned target. "
        "Escape with **Back Kick**, **Belly Rake**, **Half-Turn Belly Rake**, **Duck-and-Twist**, "
        "or **Play Dead** (must target your pinner). Lethal techniques work on a **pinned** "
        "foe or one below the listed HP threshold.\n\n"
        "**Foes**; `/combat npc` adds predators, **clan cats**, hearth-hounds, foxes, and badgers. "
        "**`/sniff`** can trigger a **border patrol** fight vs forest cats.\n\n"
        "**Topics:** `vulnerable` · `stance` · `awareness` · `defense` · `stamina` · "
        "`bestiary` · `maneuvers` · `killing` · `injuries` · `crits`",
    ),
    "vulnerable": (
        "Vulnerable Areas",
        "Certain parts of a wolf's body are very sensitive and should always be protected "
        "when possible:\n\n"
        "**Eyes**; Easily injured; a blow can disorient or temporarily blind.\n"
        "**Ears**; Thin tissue tears easily; damage can impair hearing.\n"
        "**Face / Muzzle**; Injuries here cause intense pain and can hinder breathing.\n"
        "**Throat**; Among the most fatal targets. Damage limits breathing and is often "
        "deadly in serious fights.\n"
        "**Spine**; Protects the nervous system; injury can cause paralysis or loss of movement.\n"
        "**Underside / Belly**; Soft, unprotected, holds vital organs. Strikes here cause major injury.\n\n"
        "Keep these guarded when you can. Striking them is more effective but demands "
        "precision and timing; a wild swing leaves you open to counterattacks.",
    ),
    "stance": (
        "Stance and Balance",
        "A proper stance is essential for stability and control. Keep your paws firmly "
        "planted and your weight evenly distributed; as in hunting, but stay upright so "
        "you are harder to tackle.\n\n"
        "Good balance lets you react to sudden movement, dodge incoming attacks, and keep "
        "your footing in close combat. Losing balance leaves you very vulnerable to strikes.",
    ),
    "awareness": (
        "Awareness",
        "Combat is not only strength; it is observation. Stay aware of your surroundings, "
        "your opponent, and escape routes.\n\n"
        "Watch for shifts in posture, tension in muscle, or changes in direction; these "
        "often signal an incoming attack. Awareness buys time to react and defend.",
    ),
    "defense": (
        "Defense",
        "Dodging and repositioning are key. Instead of absorbing every blow head-on, step "
        "aside, shift your weight, or move out of range.\n\n"
        "Staying mobile makes clean hits harder to land and lets you control the flow of "
        "the fight; often opening space for a counterattack.",
    ),
    "stamina": (
        "Energy and Stamina",
        "Combat is physically demanding; conserve energy when you can.\n\n"
        "Exhaustion slows reactions and weakens strikes, making defeat more likely. Know "
        "when to engage and when to disengage; an honorable warrior recovers when they must.",
    ),
    "bestiary": (
        "Bestiary; Forest Foes",
        "NPC opponents from **`/combat npc`** (recruitment phase):\n\n"
        "**Predators**; coyote, cougar, bears, wolverine, **fox**, **badger**, cornered deer/elk\n"
        "**Hearth-hounds**; feral, guard, hunting, fighting (Twoleg allies)\n"
        "**Clan cats**; warrior, deputy, rogue, loner, kittypet (Warrior Cats-style rivals)\n\n"
        "Cats are quick (high Dexterity) and favor **claw** attacks. Badgers are slow but "
        "brutal; use **Badger Defence** against them. Foxes hit-and-run.\n\n"
        "**Border patrols**; **`/sniff`** may start a live fight vs a patrol cat (~12% when "
        "no wolf encounter). Drive them off for **+standing**, **+mood**, and a small bone haul.\n"
        "**Cat pacts**; **`/pack pact`** (Alpha/Diplomat) lowers border fights; violating trust "
        "has consequences.\n\n"
        "See also: `/combat hazard` for Two-Legs, Thunderpath, traps, and fences.",
    ),
}

COMBAT_MANEUVER_LIST: list[dict] = [
    {
        "key": "head_butt",
        "name": "Head Butt",
        "summary": "Drive your skull into the opponent's chest or shoulder to stagger them.",
        "attr": "str",
        "damage_die": 4,
        "attack_bonus": 0,
        "lethal": False,
        "requires_self_unpinned": True,
    },
    {
        "key": "back_kick",
        "name": "Back Kick",
        "summary": "While pinned, thrust hind legs backward into your pinner.",
        "attr": "dex",
        "damage_die": 6,
        "attack_bonus": 1,
        "lethal": False,
        "requires_self_pinned": True,
        "target_must_be_pinner": True,
        "clears_self_pin_on_hit": True,
    },
    {
        "key": "belly_rake",
        "name": "Belly Rake",
        "summary": "While pinned, rake hind claws across the pinner's underside.",
        "attr": "dex",
        "damage_die": 8,
        "attack_bonus": 0,
        "lethal": False,
        "requires_self_pinned": True,
        "target_must_be_pinner": True,
        "clears_self_pin_on_hit": True,
    },
    {
        "key": "front_paw_blow",
        "name": "Front Paw Blow",
        "summary": "Bring a forepaw down on the head or shoulders to interrupt movement.",
        "attr": "str",
        "damage_die": 6,
        "attack_bonus": 0,
        "lethal": False,
        "requires_self_unpinned": True,
    },
    {
        "key": "forepaw_slash",
        "name": "Forepaw Slash",
        "summary": "Swipe across the face or upper body to create an opening.",
        "attr": "dex",
        "damage_die": 6,
        "attack_bonus": 0,
        "lethal": False,
        "requires_self_unpinned": True,
    },
    {
        "key": "leap_and_hold",
        "name": "Leap-and-Hold",
        "summary": "Leap onto the opponent's back and pin them.",
        "attr": "dex",
        "damage_die": 4,
        "attack_bonus": 2,
        "lethal": False,
        "requires_self_unpinned": True,
        "requires_no_active_pin": True,
        "requires_target_unpinned": True,
        "applies_pin_on_hit": True,
    },
    {
        "key": "duck_and_twist",
        "name": "Duck-and-Twist",
        "summary": "While pinned, roll to throw your pinner off and break free.",
        "attr": "dex",
        "damage_die": 4,
        "attack_bonus": 2,
        "defense_bonus": 2,
        "lethal": False,
        "requires_self_pinned": True,
        "target_must_be_pinner": True,
        "clears_self_pin_on_hit": True,
    },
    {
        "key": "play_dead",
        "name": "Play Dead",
        "summary": "While pinned, go limp; break free when the pinner loosens up.",
        "attr": "cha",
        "damage_die": 0,
        "attack_bonus": -2,
        "lethal": False,
        "requires_self_pinned": True,
        "target_must_be_pinner": True,
        "clears_self_pin_on_hit": True,
    },
    {
        "key": "scruff_shake",
        "name": "Scruff Shake",
        "summary": "Grip the scruff and shake; best on smaller opponents.",
        "attr": "str",
        "damage_die": 6,
        "attack_bonus": 0,
        "prof_skill": "hunting",
        "lethal": False,
        "requires_self_unpinned": True,
    },
    {
        "key": "tail_yank",
        "name": "Tail Yank",
        "summary": "Pull the tail to disrupt balance and movement.",
        "attr": "dex",
        "damage_die": 4,
        "attack_bonus": 1,
        "lethal": False,
        "requires_self_unpinned": True,
    },
    {
        "key": "teeth_grip",
        "name": "Teeth Grip",
        "summary": "Bite and hold scruff, limb, or ear while paws stay free.",
        "attr": "str",
        "damage_die": 4,
        "attack_bonus": 0,
        "lethal": False,
        "requires_self_unpinned": True,
    },
    {
        "key": "upright_lock",
        "name": "Upright Lock",
        "summary": "Rear on hind legs and wrestle for balance at close range.",
        "attr": "str",
        "damage_die": 6,
        "attack_bonus": 0,
        "lethal": False,
        "requires_self_unpinned": True,
    },
    {
        "key": "half_turn_belly_rake",
        "name": "Half-Turn Belly Rake",
        "summary": "While pinned, half-turn and rake the pinner's belly to escape.",
        "attr": "dex",
        "damage_die": 8,
        "attack_bonus": 0,
        "lethal": False,
        "requires_self_pinned": True,
        "target_must_be_pinner": True,
        "clears_self_pin_on_hit": True,
    },
    {
        "key": "badger_defence",
        "name": "Badger Defence",
        "summary": "Leap aside then strike limbs; used against larger opponents.",
        "attr": "dex",
        "damage_die": 6,
        "attack_bonus": 2,
        "lethal": False,
        "requires_self_unpinned": True,
    },
    {
        "key": "jump_and_pin",
        "name": "Jump and Pin",
        "summary": "Rebound off terrain onto an opponent's back and pin them.",
        "attr": "dex",
        "damage_die": 6,
        "attack_bonus": 2,
        "lethal": False,
        "requires_self_unpinned": True,
        "requires_no_active_pin": True,
        "requires_target_unpinned": True,
        "applies_pin_on_hit": True,
    },
    {
        "key": "low_dodge",
        "name": "Low Dodge",
        "summary": "Drop low and slip under a high strike.",
        "attr": "dex",
        "damage_die": 0,
        "attack_bonus": -4,
        "defense_bonus": 4,
        "lethal": False,
        "requires_self_unpinned": True,
    },
    {
        "key": "duo_fight",
        "name": "Duo Fight",
        "summary": "Back-to-back with packmates to cover blind spots (requires allies in RP).",
        "attr": "wis",
        "damage_die": 4,
        "attack_bonus": 1,
        "lethal": False,
        "requires_self_unpinned": True,
    },
    {
        "key": "killing_bite",
        "name": "Killing Bite",
        "summary": "A crushing throat bite; only when life is on the line.",
        "attr": "str",
        "damage_die": 12,
        "attack_bonus": 2,
        "prof_skill": "hunting",
        "vulnerable": True,
        "lethal": True,
        "min_defender_hp_pct": 0.35,
        "requires_self_unpinned": True,
    },
    {
        "key": "spine_bite",
        "name": "Spine Bite",
        "summary": "Clamp the upper spine; high risk, potentially paralyzing.",
        "attr": "str",
        "damage_die": 10,
        "attack_bonus": 0,
        "prof_skill": "hunting",
        "vulnerable": True,
        "lethal": True,
        "min_defender_hp_pct": 0.5,
        "requires_self_unpinned": True,
    },
    {
        "key": "neck_snap",
        "name": "Neck Snap",
        "summary": "Twist sharply at the neck from a secure hold.",
        "attr": "str",
        "damage_die": 10,
        "attack_bonus": 1,
        "lethal": True,
        "min_defender_hp_pct": 0.4,
        "requires_self_unpinned": True,
    },
    {
        "key": "skull_smash",
        "name": "Skull Smash",
        "summary": "Drive forepaws or body onto the head, slamming into ground or stone.",
        "attr": "str",
        "damage_die": 12,
        "attack_bonus": 0,
        "vulnerable": True,
        "lethal": True,
        "min_defender_hp_pct": 0.45,
        "requires_self_unpinned": True,
    },
]

COMBAT_MANEUVERS = {m["key"]: m for m in COMBAT_MANEUVER_LIST}

COMBAT_GUIDE_TOPICS["maneuvers"] = (
    "Combat Maneuvers",
    "Use `/combat maneuver` during your turn (or the **Maneuver** menu in combat). "
    "Each technique has its own risk and reward.\n\n"
    + "\n".join(
        f"**{m['name']}**; {m['summary']}"
        for m in COMBAT_MANEUVER_LIST
        if not m.get("lethal")
    ),
)
COMBAT_GUIDE_TOPICS["killing"] = (
    "⚠️ Lethal Techniques",
    "Use these **only** in life-threatening situations. They carry grave consequences "
    "in RP and may draw elder scrutiny.\n\n"
    + "\n".join(
        f"**{m['name']}**; {m['summary']}"
        for m in COMBAT_MANEUVER_LIST
        if m.get("lethal")
    ),
)

MANEUVER_DETAIL: dict[str, str] = {
    "head_butt": (
        "Lower your head and drive into the opponent's chest or shoulder. "
        "Useful to stagger and interrupt a charge."
    ),
    "back_kick": (
        "While **pinned**, shift weight forward and thrust hind legs into your pinner. "
        "On a hit you break free."
    ),
    "belly_rake": (
        "While **pinned**, rake hind claws across your pinner's underside. "
        "On a hit you break free."
    ),
    "front_paw_blow": (
        "Raise a forepaw and bring it down on the head or shoulders to stagger "
        "or interrupt movement."
    ),
    "forepaw_slash": (
        "Swipe across the face or upper body instead of striking downward; "
        "creates openings or pushes the opponent back."
    ),
    "leap_and_hold": (
        "Leap onto the opponent's back. On a hit they are **pinned** beneath you."
    ),
    "duck_and_twist": (
        "While **pinned**, twist and roll to throw your pinner off. "
        "On a hit you break free."
    ),
    "play_dead": (
        "While **pinned**, go completely still until the pinner loosens up. "
        "On a successful feint you break free."
    ),
    "scruff_shake": (
        "Grip the scruff and shake firmly to disorient a smaller opponent or "
        "reposition them."
    ),
    "tail_yank": (
        "Grab and pull the tail to disrupt balance and create space for a follow-up."
    ),
    "teeth_grip": (
        "Bite and hold scruff, limb, or ear while keeping forepaws free for "
        "another action."
    ),
    "upright_lock": (
        "Both wolves rear on hind legs and wrestle for balance and positioning."
    ),
    "half_turn_belly_rake": (
        "While **pinned**, turn onto your side and rake your pinner's belly. "
        "On a hit you break free."
    ),
    "badger_defence": (
        "Against larger opponents: leap aside from direct strikes, then target limbs "
        "to limit their mobility."
    ),
    "jump_and_pin": (
        "Use trees, rocks, or rises to rebound onto an opponent's back. "
        "On a hit they are **pinned**."
    ),
    "low_dodge": (
        "Drop closer to the ground and slip under a high swing or paw attack."
    ),
    "duo_fight": (
        "Stand back-to-back with packmates to cover blind spots. Can expand into "
        "a circle against surrounding threats."
    ),
    "killing_bite": (
        "A crushing bite at the throat until breathing stops. "
        "**Only in life-threatening situations.**"
    ),
    "spine_bite": (
        "Lunge onto the back and clamp the upper spine. A finishing move when the "
        "opponent is already weakened; high risk of spinal injury."
    ),
    "neck_snap": (
        "From a secure hold, twist sharply at the neck with jaws and forepaws."
    ),
    "skull_smash": (
        "Drive forepaws or your full weight onto the head, slamming into ground or stone."
    ),
}

from herbs import INJURIES, INJURY_TABLE

_INJURY_LINES = "\n".join(
    f"**{i}. {INJURIES[key]['name']}**; {INJURIES[key]['effect']}"
    for i, key in enumerate(INJURY_TABLE, start=1)
)

COMBAT_GUIDE_TOPICS["injuries"] = (
    "Injury Table (1d10)",
    "Roll **1d10** whenever a wolf **drops to 0 HP** or takes a **critical hit**.\n\n"
    + _INJURY_LINES
    + "\n\n**Spine Bite** (`/combat maneuver`) can inflict **spinal injury** (temporary paralysis) "
    "or **paralyzed** (permanent) instead of the table roll.\n\n"
    "Deep gashes bleed each sunrise until bandaged. Infected wounds need a daily save. "
    "Treat with `/treat` and herbs from `/inventory`.",
)

COMBAT_GUIDE_TOPICS["crits"] = (
    "Critical Hits & Fumbles",
    "**Natural 20 (critical hit)**; roll 1d4 for extra effect:\n"
    "1. Bonus damage (+1d4)\n"
    "2. Knock target prone\n"
    "3. Disarm; target drops held item or loses grip\n"
    "4. Temporary bleed: 1 HP/round for 3 rounds (3 HP applied in combat)\n\n"
    "**Natural 1 (critical fumble)**; roll 1d4:\n"
    "1. Drop guard; enemy gets a free attack on you\n"
    "2. Strain muscle; disadvantage on your next attack roll\n"
    "3. Stumble; you fall prone\n"
    "4. Bite own tongue: 1 damage; cannot speak or use vocal skills for 1 round",
)
