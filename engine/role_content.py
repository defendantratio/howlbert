"""Role-specific quests, events, prophecies, and Maw theology."""

import random

# --- Maw faith (shared across Great Packs) ---

MAW_FAITH = {
    "body": (
        "**The Maw's Body**\n"
        "The world is a living ancestor, wounded and hungry. Mountains are teeth. "
        "Forests are fur. Swamps are belly. Rivers are tears. "
        "The moon is the Maw's single eye, always watching. "
        "The sun is the Maw's breath; warm when it exhales, cold when it inhales."
    ),
    "death": (
        "**No Afterlife**\n"
        "When a wolf dies, their matter returns to the Maw: flesh to earth, breath to air, "
        "memory to water. They do not go to a happy hunting ground; they become the land. "
        "To be remembered by the living is the only immortality. "
        "A wolf whose name is never howled again dissolves into nothing: not even soil. "
        "This is the true death."
    ),
    "heresy": (
        "**The Heresy of the Maw's Hunger**\n"
        "Some wolves whisper that the Maw is not passive; that it chooses to hunger, "
        "that it enjoys watching wolves fight and die. "
        "Orthodox teaching holds the Maw is simply what is, neither good nor evil.\n\n"
        "But the **Drown-Sick** of Mistmoor and the **Tear-Drinkers** of Silverrush "
        "have started comparing notes. Something is changing in the land. "
        "The Maw's eye has seemed closer lately. Larger. More focused."
    ),
    "prophecy": (
        "**The Prophecy of the Sundering's End**\n"
        "_Carved into stone in neutral territory no pack dares enter:_\n\n"
        "When the Teeth drink the Tears,\n"
        "When the Fur chokes the Belly,\n"
        "When the Maw closes its eye,\n"
        "The pack that was one will remember why it split.\n"
        "And the hunger will end, or begin again.\n\n"
        "No one agrees on what this means. But the moon grows larger every night."
    ),
}

GASP_LORE = (
    "**Gasp**; Drown-Sick Oracle of Mistmoor _(NPC)_\n"
    "_They/them · 4 years · formerly Bog-Born wolf named Reed_\n\n"
    "Gaunt, pale gray-green fur like bleached bones and swamp mist. Milky blind eyes "
    "that seem to look anyway. A soft wet gasp with every breath.\n\n"
    "Reed fell into the **Belly-Rip** for three days; longer than any other Drown-Sick. "
    "They emerged as Gasp: riddles, prophecies that come true, laughter at whispers "
    "no one else hears. They are unsettling but never cruel.\n\n"
    "_\"Tell her the moon will blink twice before the snow melts.\"_\n"
    "_\"It means she will understand when it happens.\"_"
)

# Cryptic prophecies for Drown-Sick / Belly-Rip events
DROWN_PROPHECIES = (
    "The moon will blink twice before the snow melts.",
    "A tooth will break before the river runs backward.",
    "The chewing grows louder when the eye grows wide.",
    "Someone you have not met yet will howl your name at dawn.",
    "The Belly-Rip remembers what the Fur forgot.",
    "When fog tastes of iron, do not drink from still water.",
    "Three wolves will stand at the stone. Only one will leave unchanged.",
    "The hunger is not empty. It is waiting.",
    "Your shadow will arrive before you do.",
    "The Maw does not sleep. It listens.",
)

# Per-role daily events: narrative, optional skill check, rewards
# skill: None | skill name from rpg_rules SKILLS
ROLE_EVENTS = {
    "alpha": [
        {
            "title": "Word of Law",
            "text": (
                "Two wolves snarl over a stolen bone. The den falls silent; they wait for **your** judgment. "
                "Your word is law. Only the Rite of Broken Canine could challenge it."
            ),
            "skill": "intimidation",
            "dc": 12,
            "success": "Your growl ends the dispute. The pack remembers who holds the teeth.",
            "failure": "They part unsatisfied. A challenger watches from the shadows.",
            "bones": 15,
            "standing": 3,
        },
        {
            "title": "Bloodline Duty",
            "text": (
                "An elder whispers that you have no living offspring. A **hollow** Alpha can be challenged "
                "by any wolf of breeding age. The den's future is your first duty."
            ),
            "skill": "persuasion",
            "dc": 13,
            "success": "You secure a pairing that quiets the whispers; for now.",
            "failure": "The pack mutters. Someone circles closer to the Rite.",
            "bones": 12,
            "standing": 2,
        },
        {
            "title": "Claim of the Unmated",
            "text": (
                "An unmated wolf catches your eye. By right you may claim them; temporary or permanent. "
                "Refusal is treason. The den pretends not to listen."
            ),
            "skill": "persuasion",
            "dc": 14,
            "success": "They lower their ears. The bond is sealed without blood.",
            "failure": "They flee to the tree line. You'll need teeth, not words.",
            "bones": 10,
            "standing": 1,
        },
        {
            "title": "Rite of Broken Canine",
            "text": (
                "A rival challenges you; first blood or submission, sometimes death. "
                "The pack forms a ring. The Maw watches through the moon."
            ),
            "skill": "intimidation",
            "dc": 16,
            "success": "They yield before the killing bite. Your authority is absolute.",
            "failure": "You bleed first. Your crown feels lighter tonight.",
            "bones": 25,
            "standing": 5,
        },
    ],
    "advisor": [
        {
            "title": "Blood Oath Counsel",
            "text": (
                "You were spared when you failed your challenge; a living prisoner bound by oath. "
                "The Alpha snarls at a foolish order. They still listen to you. Sometimes."
            ),
            "skill": "persuasion",
            "dc": 13,
            "success": "Your whisper turns the decree. The den never knows how close war came.",
            "failure": "The Alpha acts alone. You taste your oath like rust.",
            "bones": 12,
            "standing": 2,
        },
        {
            "title": "Eat Before the Pack",
            "text": (
                "The kill is laid out. You eat after the Alpha and before the rest; "
                "the Guard's shadow, the Advisor's privilege. A young wolf watches too hungrily."
            ),
            "skill": "intimidation",
            "dc": 11,
            "success": "They look away. Hierarchy holds without a fight.",
            "failure": "A snap of teeth over scraps. You'll remember their scent.",
            "bones": 10,
            "standing": 2,
        },
        {
            "title": "Night in the Swamp",
            "text": (
                "Guard initiation is yours to endure again: one night alone in the swamp, "
                "resisting the **whispering rot** that tempts wolves to betray their pack."
            ),
            "skill": "survival",
            "dc": 14,
            "success": "Dawn finds you mud-caked but loyal. The rot spoke; you did not answer.",
            "failure": "You fled before sunrise. Some guards question your shadow.",
            "bones": 15,
            "standing": 3,
        },
        {
            "title": "Secret of the Alpha",
            "text": (
                "Your blood oath gives you one truth about the Alpha that no other wolf knows. "
                "Today someone pushes for an answer you cannot give."
            ),
            "skill": "intimidation",
            "dc": 12,
            "success": "They back down. Your silence is its own threat.",
            "failure": "Rumors spread anyway. The Alpha's ears flatten when they see you.",
            "bones": 8,
            "standing": 1,
        },
    ],
    "medic": [
        {
            "title": "Keeper of the Green Tongue",
            "text": (
                "Only you hold the full herb guide; territory plants, poisons, rituals. "
                "A wolf limps in with a wound that will fester without your hands."
            ),
            "skill": "medicine",
            "dc": 12,
            "success": "Your poultice holds. The Green Tongue does not lie.",
            "failure": "The wound worsens. You'll need rarer herbs by morning.",
            "bones": 12,
            "standing": 3,
        },
        {
            "title": "Neutral Scent",
            "text": (
                "Medics are forbidden to mate; your scent stays neutral so you can treat any wolf "
                "without triggering dominance rage. Tonight someone tests that boundary."
            ),
            "skill": "persuasion",
            "dc": 13,
            "success": "You hold the line. Your neutrality keeps the den safe.",
            "failure": "A growl you cannot soothe. Reported celibacy risks exile; or worse.",
            "bones": 8,
            "standing": 2,
        },
        {
            "title": "Dark Knowledge",
            "text": (
                "You know abortive herbs, paralytic brews, deathberries for mercy kills. "
                "The Alpha cannot openly kill a rival; but someone asks if you can."
            ),
            "skill": "herblore",
            "dc": 15,
            "success": "You refuse without witness. Your conscience stays your own.",
            "failure": "Word leaks. Wolves look at your paws like poison.",
            "bones": 10,
            "standing": 1,
        },
        {
            "title": "Swamp-Cough in the Nursery",
            "text": "A pup wheezes wet and shallow. The caretakers look to you; treatment is your sacred right, not theirs.",
            "skill": "medicine",
            "dc": 11,
            "success": "The pup sleeps. The den exhales.",
            "failure": "The cough lingers. You prepare a harder draught.",
            "bones": 10,
            "standing": 3,
        },
    ],
    "forager": [
        {
            "title": "The Medic's Paws",
            "text": (
                "You collect; you do not treat. That is the Medic's sacred right. "
                "Today's haul must stock the den before the frost."
            ),
            "skill": "herblore",
            "dc": 11,
            "success": "Skullcap, yarrow, witch hazel; mapped and gathered.",
            "failure": "You return with half-empty jaws. The Medic's glare is cold.",
            "bones": 10,
            "standing": 2,
        },
        {
            "title": "Patch of Water Hemlock",
            "text": (
                "A new stand of herbs after the rain. Every patch shifts each season: "
                "you must know where death grows beside healing."
            ),
            "skill": "survival",
            "dc": 12,
            "success": "You mark the hemlock and harvest the safe plants beside it.",
            "failure": "You misread a leaf. You spit out the bite before it takes you.",
            "bones": 8,
            "standing": 1,
        },
        {
            "title": "Lesson in Humility",
            "text": (
                "An elder accuses you of misidentifying a poisonous plant. "
                "Tradition says you should eat what you picked; a lesson in humility."
            ),
            "skill": "herblore",
            "dc": 14,
            "success": "You prove the plant safe. The elder grunts and walks away.",
            "failure": "You were wrong. The vomiting lasts all night.",
            "bones": 5,
            "standing": 0,
        },
        {
            "title": "Young Wolf's Training",
            "text": "A juvenile trails you, learning the Green Tongue. They point at the wrong plant with confident eyes.",
            "skill": "herblore",
            "dc": 10,
            "success": "You correct them before they touch it. The Medic nods approval.",
            "failure": "They gather poison. You'll answer for it at the den.",
            "bones": 8,
            "standing": 2,
        },
    ],
    "hunter": [
        {
            "title": "Sacred Violence",
            "text": (
                "Before the major hunt, you crush yarrow beneath your muzzle and howl a brief prayer "
                "to the Great Maw. The pack's belly depends on what follows."
            ),
            "skill": "hunting",
            "dc": 12,
            "success": "A clean kill. Meat for the den. The prayer still tastes of green.",
            "failure": "Empty jaws. Blood debt gathers like storm clouds.",
            "bones": 22,
            "standing": 2,
        },
        {
            "title": "Regurgitate for the Weak",
            "text": (
                "You eat after Alpha and Guard; but pups, elders, and den-bound wolves wait. "
                "You must bring the kill back and share what your stomach holds."
            ),
            "skill": "survival",
            "dc": 11,
            "success": "Full bellies whimper thanks. The hunt was sacred after all.",
            "failure": "You keep too much. Hungry eyes remember.",
            "bones": 15,
            "standing": 1,
        },
        {
            "title": "Blood Debt",
            "text": (
                "The hunt failed. As lead hunter you owe the pack; your portion goes to another, "
                "or in severe cases, exile waits."
            ),
            "skill": "hunting",
            "dc": 14,
            "success": "A desperate second chase saves your standing.",
            "failure": "You surrender your share. The shame clings like wet fur.",
            "bones": 12,
            "standing": 2,
            "standing_fail": -2,
        },
        {
            "title": "Ambush at Dusk",
            "text": "Fresh spoor; prey unaware, wind in your favor. Killer's instinct prickles along your spine.",
            "skill": "hunting",
            "dc": 12,
            "success": "Swift takedown. The den will eat tonight.",
            "failure": "The quarry bolts into bracken. Empty paws.",
            "bones": 18,
            "standing": 1,
        },
    ],
    "scout": [
        {
            "title": "Border Run",
            "text": (
                "You run the pack's edge; tail flicks and low whines, never a howl that betrays position. "
                "Rival scent crosses your path."
            ),
            "skill": "stealth",
            "dc": 13,
            "success": "You map their camp unseen. Intelligence worth more than teeth.",
            "failure": "A twig snaps. You run before they circle.",
            "bones": 14,
            "standing": 2,
        },
        {
            "title": "Captured Scent",
            "text": (
                "Enemy wolves once tortured scouts for information. You carry old scars: "
                "proof you'd die before you talk. Today they test the border again."
            ),
            "skill": "tracking",
            "dc": 14,
            "success": "You slip back with news and no new wounds.",
            "failure": "A close chase. You return bleeding but silent.",
            "bones": 12,
            "standing": 3,
        },
        {
            "title": "Tongue-Tied Report",
            "text": (
                "Back at the den, you must report without loud voice; only signs the Alpha reads. "
                "Miscommunication starts wars."
            ),
            "skill": "tracking",
            "dc": 11,
            "success": "The Alpha understands. Patrol shifts before dawn.",
            "failure": "They misread your signal. The wrong ridge is watched.",
            "bones": 10,
            "standing": 1,
        },
        {
            "title": "Suicide Trail",
            "text": (
                "The Alpha sends a juvenile on a dangerous route; some call it a suicide scout. "
                "You shadow them, silent, to see if they return."
            ),
            "skill": "stealth",
            "dc": 15,
            "success": "They live. You never reveal how close it was.",
            "failure": "They don't come back. You carry the scent home alone.",
            "bones": 8,
            "standing": 2,
        },
    ],
    "guard": [
        {
            "title": "Defender's Watch",
            "text": (
                "You defend the den site, the nursery, the Alpha's sleep. "
                "Something circles in the dark; older, larger, retired from the hunt but not from teeth."
            ),
            "skill": "intimidation",
            "dc": 12,
            "success": "Your growl sends it running. The pups never wake.",
            "failure": "It steals from the pile before you reach it.",
            "bones": 12,
            "standing": 2,
        },
        {
            "title": "Night Culling",
            "text": (
                "The Alpha whispers a name; deformed pup, refusing elder, liability. "
                "Guard duty includes kills done quietly, bodies fed to the swamp."
            ),
            "skill": "survival",
            "dc": 14,
            "success": "Quick. Quiet. The den sleeps through it.",
            "failure": "A pup wakes and cries. Eyes open. Ears remember.",
            "bones": 10,
            "standing": 1,
        },
        {
            "title": "Whispering Rot",
            "text": (
                "Your initiation night in the swamp returns in dreams; the rot that offers betrayal "
                "if you only listen. Tonight the fog is thick."
            ),
            "skill": "survival",
            "dc": 13,
            "success": "You hold the line. Loyalty is its own armor.",
            "failure": "You spoke to something in the mud. No one knows yet.",
            "bones": 8,
            "standing": 0,
        },
        {
            "title": "Adjacent Packmate",
            "text": "A rival lunges at a wolf beside you. Defender's Resolve; impose your body between them.",
            "skill": "intimidation",
            "dc": 13,
            "success": "The attacker breaks off. Your packmate breathes.",
            "failure": "Teeth find flesh anyway. You were too slow.",
            "bones": 14,
            "standing": 3,
        },
    ],
    "caretaker": [
        {
            "title": "First Licking",
            "text": (
                "A newborn shivers; cleaning, warmth, breath stimulation. "
                "You decide if this pup is strong enough to keep."
            ),
            "skill": "medicine",
            "dc": 11,
            "success": "The pup whines and latches. Life holds.",
            "failure": "It fades before the first moon. Wind that never howled.",
            "bones": 10,
            "standing": 2,
        },
        {
            "title": "Weaning Discipline",
            "text": (
                "A pup suckles past the allowed moon. Caretakers bite to teach submission early. "
                "Your jaws must be firm, not cruel."
            ),
            "skill": "persuasion",
            "dc": 12,
            "success": "They learn. The den's order is planted young.",
            "failure": "They yap and return. The Alpha's ears flatten.",
            "bones": 8,
            "standing": 1,
        },
        {
            "title": "Storm in the Nursery",
            "text": "Thunder rolls. Pups pile against you; frightened, stinking, alive.",
            "skill": "persuasion",
            "dc": 10,
            "success": "Your grooming calms the den within a den. Fear fades.",
            "failure": "They scatter into the roots. One goes missing until dawn.",
            "bones": 8,
            "standing": 2,
        },
        {
            "title": "Juvenile Blooding",
            "text": (
                "A juvenile must kill prey alone to earn an adult role. "
                "You watch from the brush; intervene only if death comes."
            ),
            "skill": "hunting",
            "dc": 13,
            "success": "They return with blood on their muzzle. The pack will name them soon.",
            "failure": "They fail. The Alpha considers a suicide scout instead.",
            "bones": 10,
            "standing": 2,
        },
    ],
    "elder": [
        {
            "title": "Fed Last",
            "text": (
                "The kill is divided. You wait; respected, not sentimental. "
                "Elders eat after hunters, after pups, after everyone."
            ),
            "skill": None,
            "dc": 0,
            "success": "Scraps enough. You've survived worse winters.",
            "failure": "",
            "bones": 8,
            "standing": 1,
        },
        {
            "title": "Whisperer's Dream",
            "text": (
                "You chew dried skunk cabbage carefully; vivid dreams, spirit interpretation. "
                "The Alpha awaits your vision before the border war."
            ),
            "skill": "herblore",
            "dc": 14,
            "success": "Your vision steadies the Alpha's paw. The pack moves wisely.",
            "failure": "The dream chokes you. The Alpha decides alone.",
            "bones": 12,
            "standing": 3,
        },
        {
            "title": "Long Nap",
            "text": (
                "Hard winter. The unspoken custom: elders walk into the snow so the young may eat. "
                "Tonight you feel the cold asking."
            ),
            "skill": "survival",
            "dc": 13,
            "success": "You return at dawn; the pack howled you back from the white.",
            "failure": "You walked farther than intended. Someone dragged you home.",
            "bones": 10,
            "standing": 4,
        },
        {
            "title": "Names of the Dead",
            "text": "A young wolf asks what the old wars meant; who was remembered, who dissolved.",
            "skill": "persuasion",
            "dc": 11,
            "success": "Your story plants memory. Immortality in howl-form.",
            "failure": "They walk away bored. Another name edges toward true death.",
            "bones": 8,
            "standing": 2,
        },
    ],
    "diplomat": [
        {
            "title": "Silver Tongue Between Packs",
            "text": (
                "Allied packs negotiate over hunting grounds. One wrong word starts a border war. "
                "The Alpha's Guard watches your throat."
            ),
            "skill": "persuasion",
            "dc": 14,
            "success": "Terms settled. Teeth stay sheathed.",
            "failure": "Insult lands. You'll repair this tomorrow or run.",
            "bones": 15,
            "standing": 4,
        },
        {
            "title": "Mate from Allied Pack",
            "text": (
                "The Alpha orders a pairing with a wolf from another Great Pack; bloodline politics. "
                "You carry the proposal."
            ),
            "skill": "persuasion",
            "dc": 13,
            "success": "They accept with ears low. The gene pool widens.",
            "failure": "Refusal humiliates your Alpha. You taste the fallout.",
            "bones": 12,
            "standing": 2,
        },
        {
            "title": "Grudge at the Den",
            "text": "Two packmates near blood over an old slight. Words before teeth; if you can.",
            "skill": "persuasion",
            "dc": 12,
            "success": "Peace holds for one more night.",
            "failure": "Fur and blood. You document who started it.",
            "bones": 10,
            "standing": 2,
        },
        {
            "title": "Rival Emissary",
            "text": "A lone wolf from a rival pack requests parley at neutral stone. Trap or treaty?",
            "skill": "intimidation",
            "dc": 13,
            "success": "You read their scent. Truth, for once. A fragile truce.",
            "failure": "Ambush. You escape with a story and a scar.",
            "bones": 14,
            "standing": 3,
        },
    ],
    "drown_sick": [
        {
            "title": "Belly-Rip Vigil",
            "text": (
                "You press your nose to the mud at the Belly-Rip. The chewing is loud today: "
                "a wet, rhythmic grinding that makes your bones ache. You listen."
            ),
            "skill": None,
            "dc": 0,
            "success": "A whisper rises from the dark water.",
            "failure": "",
            "bones": 15,
            "standing": 3,
            "prophecy": True,
        },
        {
            "title": "The Maw's Eye",
            "text": "The moon hangs low and swollen. It feels like it is watching only you.",
            "skill": None,
            "dc": 0,
            "success": "Vision cleaves through the fog.",
            "failure": "",
            "bones": 10,
            "standing": 2,
            "prophecy": True,
        },
        {
            "title": "Gasp's Footsteps",
            "text": "Gasp was here. The mud still holds their too-many-toed prints.",
            "skill": "stealth",
            "dc": 14,
            "success": "You follow the trail to a prophecy-stone, wet with swamp water.",
            "failure": "The trail dissolves into fog. Only the chewing remains.",
            "bones": 12,
            "standing": 2,
            "prophecy": True,
        },
        {
            "title": "Heresy Shared",
            "text": (
                "A Tear-Drinker from Silverrush meets you at the swamp edge. "
                "You compare notes on the Maw's hunger; something is changing."
            ),
            "skill": "tracking",
            "dc": 12,
            "success": "You hear what the river already knows. The eye grows wider.",
            "failure": "Their scent scatters. Only riddles remain.",
            "bones": 12,
            "standing": 2,
            "prophecy": True,
        },
    ],
    "pup": [
        {
            "title": "First Moon",
            "text": (
                "You have survived the first moon. The Alpha approaches; a single lick on your forehead, "
                "one word spoken. Your name. Pups who die unnamed are wind that never howled."
            ),
            "skill": None,
            "dc": 0,
            "success": "You have a name. The den howls it once. You exist in memory.",
            "failure": "",
            "bones": 20,
            "standing": 5,
        },
        {
            "title": "Caretaker's Warmth",
            "text": (
                "Cold seeps through the nursery roots. You whimper; too small to hunt, "
                "too new to understand the chewing in the distance."
            ),
            "skill": "survival",
            "dc": 10,
            "success": "A caretaker curls around you. Breath returns. You live another night.",
            "failure": "You shiver alone until dawn. The den was busy with blood elsewhere.",
            "bones": 8,
            "standing": 2,
        },
        {
            "title": "Crushed Underfoot",
            "text": (
                "The den stirs at night; adults moving, fighting, loving. "
                "You are small enough to be accidentally stepped on."
            ),
            "skill": "survival",
            "dc": 11,
            "success": "You yelp and roll clear. A guard grunts apology without stopping.",
            "failure": "Pain. A bruised rib. You learn to sleep at the edge.",
            "bones": 5,
            "standing": 1,
        },
        {
            "title": "Milk and Scraps",
            "text": (
                "Hunters return. You are last in line; regurgitated meat, warmth, a rough tongue. "
                "This is how pups eat."
            ),
            "skill": None,
            "dc": 0,
            "success": "Your belly is full enough. The Maw chews elsewhere tonight.",
            "failure": "",
            "bones": 10,
            "standing": 1,
        },
    ],
    "juvenile": [
        {
            "title": "The Blooding",
            "text": (
                "You must kill a rabbit; or larger prey; alone. No help. No teeth of elders. "
                "This is how you earn an adult role."
            ),
            "skill": "hunting",
            "dc": 13,
            "success": "Blood on your muzzle. The pack watches. You are no longer only practice.",
            "failure": "The prey escapes. The Alpha's eyes weigh your future.",
            "bones": 25,
            "standing": 4,
        },
        {
            "title": "Rank Fight",
            "text": (
                "Juvenile hierarchies are brutal. Another yearling challenges you over den position: "
                "fights for rank often leave scars."
            ),
            "skill": "intimidation",
            "dc": 12,
            "success": "They yield. Your place in the pile rises.",
            "failure": "You limp away. A scar for the season.",
            "bones": 10,
            "standing": 1,
            "standing_fail": -1,
        },
        {
            "title": "Practice on the Sick",
            "text": (
                "The den brings a sick animal for you to practice hunting; live prey, "
                "but already dying. This is juvenile training."
            ),
            "skill": "hunting",
            "dc": 11,
            "success": "You finish the kill cleanly. Hunters nod approval.",
            "failure": "It suffers too long. A medic glares.",
            "bones": 15,
            "standing": 2,
        },
        {
            "title": "Separate Den",
            "text": (
                "You sleep in the juvenile den; not with pups, not with adults. "
                "Tonight someone howls a challenge across the divide."
            ),
            "skill": "stealth",
            "dc": 12,
            "success": "You stay out of it. Dawn finds you intact.",
            "failure": "Dragged into a fight you didn't start. New scars.",
            "bones": 8,
            "standing": 0,
        },
        {
            "title": "Suicide Scout Shadow",
            "text": (
                "The Alpha sends a yearling on a dangerous border route. "
                "You are young, fast, and expendable in their eyes."
            ),
            "skill": "stealth",
            "dc": 14,
            "success": "You return with scent-maps and your life.",
            "failure": "You barely escape. The Alpha does not look at you.",
            "bones": 12,
            "standing": 2,
        },
    ],
}


def pick_role_event(role: str) -> dict:
    from engine.apprentice_roles import role_event_key

    key = role_event_key(role)
    pool = ROLE_EVENTS.get(role) or ROLE_EVENTS.get(key) or ROLE_EVENTS.get("hunter", [])
    return random.choice(pool)


def pick_prophecy() -> str:
    return random.choice(DROWN_PROPHECIES)
