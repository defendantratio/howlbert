# RP scene examples

howlbert plays like a tabletop game running quietly underneath your prose. you write the scene like you always would; when something mechanical happens (a bite lands, a wound gets treated, a pup is born), you drop in the matching command and let the bot roll it, then keep writing from what it gives back. this page walks through full scenes doing exactly that: prose, then command, then more prose reacting to the result.

---

## scene 1: a border skirmish

**setting:** thistlehide territory, near the greyspire border. mist in the pines, late afternoon.

first, the scene itself is opened so anyone can find it and join:

> `/scene start with_member:@grim's player location:greyspire_border topic:territory dispute`

river'shroud stood motionless on the ridge, her antlered silhouette merging with the mist, pale gray eyes fixed on the valley below. beside her, finn'pelt crouched low, ash-black coat beaded with condensation, ears flat.

a twig snapped. too close.

**river'shroud:** "greyspire. you've crossed the border."

**grim:** "thistlehide. you're on our land."

words won't settle this. time to actually fight, which means opening a real encounter instead of just narrating hits:

> `/combat start`

the bot opens fight **#12** for river'shroud and posts an embed telling everyone else to `/combat join`.

> `/combat join encounter:12`

grim's player joins the same fight. once everyone who's fighting has used `/combat join`, someone starts the clock:

> `/combat begin`

the bot rolls initiative for every fighter and posts the turn order in an embed, along with a `view` with buttons for the current turn. say the order comes out grim, then river'shroud. on grim's turn:

> `/combat attack target:river'shroud action:bite encounter:12`

the bot rolls the attack, rolls river'shroud's defense, and replies with something like:

> **attack**: grim's jaws snap for river'shroud's flank. hit! **6** damage. river'shroud: **16/22 HP**.

now you write the prose that fits what actually happened, not what you'd have preferred:

grim's jaws closed hard on river'shroud's shoulder, fur tearing under the pressure. she staggered back with a snarl, blood welling dark against her coat.

**river'shroud:** "you'll regret that."

on river'shroud's turn:

> `/combat attack target:grim action:claw encounter:12`

say this one rolls a critical hit; the bot's reply mentions a new injury getting added, something like:

> **attack**: river'shroud rakes across grim's ribs. critical hit! **9** damage, and the wound is deep enough to leave a mark. grim: **16/25 HP**. injury: **deep gash**.

river'shroud's claws found the gap in grim's guard, tearing deep. grim yelped, twisting away, blood already soaking into the pine needles underfoot.

the fight winds down from here (more attacks, a yield, whatever the scene calls for); when it's over:

> `/combat end`

this syncs both wolves' real HP and injuries back to their profiles, so the bite river'shroud took is now sitting on her character sheet, not just in the chat log.

---

## scene 2: treating the wound

river'shroud limps home with the bite from grim still aching. her pack's medic needs to actually clear it, not just have someone type that they helped:

> `/medic action:treat patient:@rivershroud's player herb:herb_yarrow`

sypha knelt beside river'shroud, her paws steady despite the blood. she chewed a mouthful of yarrow into a bitter, clotting paste and pressed it into the wound.

the bot resolves the treatment against river'shroud's actual `active_injuries` state and replies:

> **treated**: yarrow cures **deep gash**. river'shroud: bleeding stopped.

not every injury clears that easily. say river'shroud also picked up a **wrenched joint** (dislocated shoulder) this fight; that one needs a real medicine check to pop it back in, not just the right herb applied:

> `/medic action:treat patient:@rivershroud's player herb:herb_willow_bark`

if the roll misses the DC, the bot is explicit that nothing happened:

> **treatment failed**: wrenched joint needs a steadier hand; medicine check **11** vs DC **15**; no effect this time.

sypha's paws slipped on the joint, and river'shroud yelped, twisting away. "hold still," sypha growled. "or i do this twice."

she tries again next sunrise once the cooldown clears, and this time the check succeeds:

> **treated**: wrenched joint pops back into place. river'shroud: rest **10 days** to fully heal.

note what didn't happen anywhere in this scene: nobody typed "sypha heals river'shroud's shoulder" and had it just be true. the herb had to be in inventory, the command had to run, and the DC 15 check had to actually pass.

---

## scene 3: preparing an herb properly

some cures need a specific preparation, not just the raw plant. say a disease calls for tea, not a poultice; the medic has to actually prepare it first:

> `/herbs action:prepare herb:herb_chamomile prep_method:tea`

sypha steeped a handful of chamomile flowers in a hollowed stone bowl of creek water, waiting for the pale color to bloom through. 

the bot rolls a herblore check against the prep DC and, on success, turns the raw herb into a real "tea" stack she can now use in treatment.

only then does `/medic action:treat` actually work against a disease that requires that form:

> `/medic action:treat patient:@wolfname herb:herb_chamomile`

if she'd skipped the prep step and tried to treat with the raw flower, the bot would have told her the disease "needs preparation" and refused to apply anything.

---

## scene 4: courtship, mating, and a litter

not everything mechanical is violent. courtship still runs through real rolls and real state, layered under however tender or awkward you want the actual prose to be.

> `/scene start with_member:@rivershroud's player location:thistlehide_den topic:after the rains`

finn'pelt had been circling the idea for weeks; watching river'shroud from across the clearing, finding reasons to walk the same patrol route, never quite finding the nerve to close the distance. tonight the rain had finally broken, and the den smelled of wet moss and turned earth. he found her at the edge of the water, watching the current pull leaves downstream.

he sat beside her, close enough that his shoulder brushed hers, and said nothing for a long moment.

**finn'pelt:** "you've been alpha three moons now. you look tired."

**river'shroud:** "everyone looks tired in leaf-bare."

**finn'pelt:** "not like this."

he leaned in, nose brushing her jaw, an old and deliberate gesture. 

whatever came next wasn't going to be decided by how the scene read; it needed a real roll:

> `/courtship action:court partner:@rivershroud's player`

the bot rolls a charisma-based check against river'shroud's actual disposition and replies with something like:

> **courtship**: finn'pelt's approach lands. river'shroud is receptive for the next **7** days.

river'shroud went still under the touch, then, slowly, leaned back into it.

**river'shroud:** "you've been waiting to do that."

**finn'pelt:** "since before you were alpha."

a miss here wouldn't have ended the scene either; the bot would have just left her unreceptive, and finn'pelt would try again another sunrise, no less real for the wait.

weeks pass, the two of them falling into an easy rhythm; sharing kills, patrolling the same stretch of border without needing to discuss it. eventually the moment is right for something more, and it needs both of them to actually say so:

> `/courtship action:mate partner:@rivershroud's player`

river'shroud's player sees the prompt and has to accept it herself before anything is final; the bot doesn't let finn'pelt decide this alone, and it doesn't let one player's post carry it for both wolves.

> `/courtship action:mate partner:@finnpelt's player respond:accept`

the leaves had turned since the night at the water, and neither of them had said anything about it since, not directly. finn'pelt found her at the same stretch of creek, and this time neither of them hesitated.

seasons turn again. river'shroud starts turning down patrols, resting more than she used to, and it's time to check:

> `/courtship action:pregnancy`

this rolls and marks river'shroud's pregnancy state for real, tracked sunrise by sunrise from here, not just implied by a scene fading to black.

**sypha:** "you're carrying. i'd guess six, maybe seven weeks."

**river'shroud:** she pressed her nose to her own belly, something unreadable crossing her face. "does finn'pelt know?"

**sypha:** "you tell me."

months later, when the litter actually arrives:

> `/pupcare action:birth names:fern, briar, thistle`

the bot rolls a real birth event: litter size, genetics, and survival odds all come from the roll, not from what the players had planned going in. say it comes back three pups, all healthy. write the aftermath from whatever it hands back, the same way you would after a combat roll:

fern came first, small and squalling; then briar, quieter, already trying to nose her way toward warmth; then thistle, who took a long, terrible moment before he finally cried. river'shroud counted them twice, as if the number might change.

**river'shroud:** "three. we have three."

**finn'pelt:** he pressed close against her side, ash-black fur damp with the night air. "three."

if the roll had come back differently; fewer pups, a stillbirth, complications; the scene would be written from that instead. the bot decides what actually happened; the prose just has to catch up to it.

---

## scene 5: what stays purely freeform

not everything needs a command. general scene-setting, body language beyond the mechanical `/sign`, casual dialogue, describing the weather or a den's interior, arguing about politics that never touches `standing`; all of that is just prose, and it's most of what an actual scene is made of. the bot only needs to come in when something changes real state: HP, an injury, a disease, hunger, standing, a pregnancy, a death.

a normal scene thread mixes both freely:

> `/scene start with_member:@packmate location:thistlehide_den topic:evening at the den`

mossheart curled into the moss near the fire-pit, tail tucked over his nose. "rough season," he murmured, not really expecting an answer.

no command needed for that; it's just atmosphere. but mossheart is a scout, and if he wanted to actually walk the border before the scene continued:

> `/field action:sniff`

or, for a proper border sweep instead of the daily wind-read:

> `/scout survey`

either roll is real; whatever intel, bones, or standing it hands back is what actually happened on that patrol, not whatever would have made a better story.

---

## scene 6: spying on a rival den

not every conflict is a fight. say thistlehide wants to know what greyspire is planning before the next territory dispute. this is a real mechanic with real risk, not just narrating "my wolf sneaks into their camp":

> `/scene start with_member:@grim's player location:greyspire_border topic:something in the fog`

mossheart kept low, belly brushing the frost-hardened grass, easing past the scent-line one careful pace at a time. the greyspire den smelled of woodsmoke and old blood.

getting in isn't guaranteed just because the prose says he's careful:

> `/pact action:infiltrate target:greyspire`

the bot rolls against the den's actual watch and trust state and replies with something like:

> **infiltrate**: mossheart slips past the scent-line unnoticed.

on a worse roll, this could just as easily have come back caught, standing cost and all; the scene would be written from that instead. having gotten in clean, he still has to actually report back for any of it to count:

> `/pact action:report`

the bot rolls again, this time for whether the report itself draws attention, and hands back real intel (or, on a bad roll, exposes him):

> **report**: mossheart returns with word of greyspire's patrol routes. no one saw him leave.

mossheart slipped back through the mist before dawn, the shape of greyspire's patrols now fixed in his mind. river'shroud would want to hear this before the pack woke.

---

## scene 7: a warning, not a word

body language carries real weight here, the same way a bite or a herb does. say river'shroud needs to put down a challenge without a fight:

a young hunter has been mouthing off about her fitness to lead all week, and tonight he finally says it to her face in front of the den.

**river'shroud:** she doesn't answer him in words.

> `/sign signal:threaten wolf:@hunter's player`

the bot rolls the confrontation against both wolves' actual standing and mood, not just who wrote the more intimidating post, and replies with something like:

> **sign**: river'shroud's threaten lands. the hunter's mood drops sharply; he backs down.

her hackles rose, ears pinned flat, and a low sound built in her chest that wasn't quite a growl. the hunter's bravado folded before she'd so much as bared a tooth.

**river'shroud:** she held his gaze a moment longer, then turned and walked away, tail high.

if she'd lost that roll instead, the hunter's confidence would have grown and her own standing would have taken the hit; the sign is a real challenge, not a guaranteed win just because she's alpha.

---

## OOC markers

two things the bot (and your fellow players) actually recognize as out-of-character inside an IC post: double parentheses and a leading double-slash.

> `((need to step away for dinner, back in 20))`

> `// sorry, ignore that last line, wrong channel`

anything else in a proxied message is read as in-character prose. there's no third marker; brackets like `[ ]` are not parsed as OOC by anything in the bot.
