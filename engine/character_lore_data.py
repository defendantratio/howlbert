"""Canonical character lore sheets; copied into users.character_lore on register/backfill."""

from engine.character_lore import encode_character_lore


def _sheet(**kwargs) -> str:
    return encode_character_lore(**kwargs)


CHARACTER_LORE_BY_NAME: dict[str, str] = {
    "Mirewort": _sheet(
        appearance=(
            "Lean and sinewy, built for crawling through cypress knees and sucking mud. "
            "Patchy olive-brown fur stained greenish-black from swamp tannins, with weeping "
            "bald spots where shelf-fungus has taken root. Pale, watery amber eyes, always "
            "slightly unfocused. Left half of muzzle scarred smooth from a rot-lung treatment "
            "gone wrong. Slight limp, favoring right foreleg; paw missing two toes (snapping "
            "turtle). When still, marsh grasses seem to grow toward him."
        ),
        personality=(
            "Patient, morbid, curious, detached, fervent. Speaks in a low, wet murmur. Never "
            "rushes; examines wounds from three angles before acting. Dark gallows humor; "
            "names each plant after a wolf he failed to save. Detachment is necessity, not cruelty. "
            "Feverishly devout beneath the stillness. Murkvein suspects his closeness to the Maw; "
            "Dusk watches his Belly-Rip visits. He does not explain himself to either."
        ),
        backstory=(
            "Born to a Bog-Born mother who died of milk-fever at three weeks. Raised by Hollowgaze, "
            "a Drown-Sick who taught by showing, not telling; dead two winters now under glow-fungus. "
            "Not nursery caretaker Hollowstem; the names confuse pups and elders alike. "
            "At two, a litter died of shaking-sickness from Belly-Rip water; last pup Sedgepup bled "
            "out in his jaws. He listened at the Belly-Rip and understood: the Maw digests, not hates. "
            "Buried each pup under herb plants. Murkvein named him Mirewort after the bitter root when "
            "she rose to Rotmother. Now trains Mosspup, Soot, and Rotteddust; and keeps the pack "
            "alive through rot-lung seasons the swamp shows no mercy for."
        ),
        family_ties=(
            "Foster-mother Hollowgaze (deceased Drown-Sick; not Hollowstem). Apprentices; Mosspup, Soot, "
            "Rotteddust. Murkvein distrusts him; Dusk watches his Belly-Rip visits. No mate."
        ),
        rp_sample=(
            "The mud sucked at Mirewort's paws as he knelt beside Mosspup, rust-wound weeping yellow. "
            "\"Open your mouth,\" he murmured; not threatening, explaining. He cut the rot out while the "
            "pup screamed and whispered to the wound: \"Hear him, Maw. He's still chewing back.\""
        ),
        open_plots=(
            "Rot-lung cure needs Belly-Rip fungus; wants a twoleg surgical knife; Dusk suspects his "
            "oracle visits; Murkvein's jealousy over the Maw's favor; Sedgepup's grave disturbed again."
        ),
    ),
    "Splinter": _sheet(
        appearance=(
            "Lean, scarred, dirty gray-brown coat like rotted wood; patchy, matted, ribs showing. "
            "Pale wild yellow eyes. Left foreleg missing below the elbow (Twoleg trap). Surprisingly "
            "fast on three legs. Torn ears, muzzle crisscrossed with old bite scars. Smells of "
            "carrion and Twoleg refuse."
        ),
        personality=(
            "Cunning, bitter, desperate, unpredictable, secretly ashamed. Once Greyspire; exiled "
            "for killing a packmate over fresh-kill. Survives by stealing from territory edges. "
            "Not brave; hungry. Attacks only when cornered."
        ),
        backstory=(
            "Born Greyspire to a Lowbelly mother who died when he was a pup. Too small, too weak. "
            "One starving winter he killed a fellow Lowbelly for meat and was exiled. Two years "
            "wandering; no pack will take him."
        ),
        rp_sample=(
            "Splinter limped toward the Silverrush border, stole a fish from the shallows, ate "
            "beneath a fallen log, and dreamed of the wolf he killed; as he always does."
        ),
        open_plots=(
            "Book One (*The Blinking*): rogue `/crime` border branch (phase 6+); `/sniff` may catch his "
            "limp scent; `/explore investigate` mill tooth; redemption via returned prey + standing, or "
            "death by patrol/combat; quest **blink_rogue_ledger**."
        ),
    ),
    "Moth": _sheet(
        appearance=(
            "Small, pale-furred wolf; dusty gray and white like moth wings. Thin soft fur; "
            "presses flat when frightened. Large dark brown eyes always wide with fear. Intact "
            "ears (rare for a Lowbelly). Small notch in tail from frostbite. Trembles constantly."
        ),
        personality=(
            "Timid, desperate to please, clever, haunted, secretly hopeful. Watches Stoneguard, "
            "studies techniques, bides time for a challenge. Shares food with pups when starving. "
            "Grooms injured wolves unseen. Wants to be good; doesn't know how to escape Lowbelly life."
        ),
        backstory=(
            "Lowbelly mother killed by Stoneguard for stealing food; Moth watched. Never "
            "challenged anyone; practices fighting in secret. Dreams of Lowbellies rising up."
        ),
        rp_sample=(
            "Moth pressed against the cave wall as Stoneguard passed, crept to the fresh-kill "
            "pile, grabbed rabbit, retreated to her corner; invisible, as always."
        ),
        open_plots="Could succeed in a challenge; could be killed; could become a spy.",
    ),
    "Scab": _sheet(
        appearance=(
            "Thin, mange-ridden patchy brown-gray; fur falls out in clumps over scabbed skin. "
            "Dull yellow-brown eyes, permanent sneer on scarred muzzle. Broken crooked tail, "
            "ears torn to shreds. Smells of infection and old blood."
        ),
        personality=(
            "Bitter, desperate, cunning, unreliable, secretly terrified. Lowbelly his whole life. "
            "Hates the pack but too afraid to leave. Trades secrets for survival. Trusts no one."
        ),
        backstory=(
            "Lowbelly mother died of infection as a pup. Raised by caretakers who fed him last. "
            "Learned to fight dirty. Challenged twice for rank; second time Stoneguard captain "
            "broke his tail. Has not tried again."
        ),
        rp_sample=(
            "Scab stole meat from the fresh-kill pile during a distraction, ate in silence, "
            "licking blood from his paws. He did not thank the Maw. He thanked no one."
        ),
        open_plots="Killed for betrayal; might rise against the pack; exile.",
    ),
    "Sleet": _sheet(
        appearance=(
            "Lean silver-white wolf; winter mountains in fur, pale gray-blue in shadow. Thick "
            "double coat. Cool pale gray eyes. Small neat scar on upper lip (diplomatic mission "
            "gone wrong). Deliberate economical grace; tail level with spine."
        ),
        personality=(
            "Greyspire's voice to the outside; threatening and trustworthy at once. Speaks softly, "
            "offers fair terms, reminds others the teeth are always behind her. Respected, not liked. "
            "Believes harsh ways are necessary; unnecessary bloodshed is foolish inefficiency."
        ),
        backstory=(
            "Stoneguard father, diplomat mother. Learned words are weapons; read wolves, find fears, "
            "offer enough hope to prevent attack."
        ),
        rp_sample=(
            "Sleet sat across from the Thistlehide diplomat on neutral ground. \"Peace is not a "
            "commodity,\" she said softly. \"Try again, or I'll start thinking you're a deerheart.\" "
            "She could wait all day."
        ),
        open_plots="Negotiate with hostile packs; loyalty tested by a better offer.",
    ),
    "Harepup": _sheet(
        appearance=(
            "Slender long-legged pup, pale silver-gray and white like winter moss on granite. "
            "Short sleek fur, oversized swiveling ears. Bright curious amber eyes. Thin white "
            "scar across nose from a fox cub fight. Long expressive tail. Fastest pup in Greyspire."
        ),
        personality=(
            "Competitive, sharp-tongued, loyal, impatient, secretly lonely. Races everyone and crows "
            "when she wins; loud, brash, obnoxious. Other pups avoid her. Mother died at two moons; "
            "father distant. Learned the only way to be noticed is to be the best."
        ),
        backstory=(
            "Mother died of respiratory infection at two moons. Father Stoneguard Asphalt threw "
            "himself into duties; den-keepers raised her. Named for hare-like speed; elders say "
            "the Maw gifted her speed for small size."
        ),
        family_ties="Father; Stoneguard Asphalt. No living mother.",
        rp_sample=(
            "Harepup darted between rocks, outran yearlings, stuck out her tongue: \"Too slow, "
            "frog-guts!\" She won again; but curled up alone, victory hollow."
        ),
        open_plots="Needs friend or mentor; humbled by a loss; possible adoption.",
    ),
    "Cinderpup": _sheet(
        appearance=(
            "Soot-gray fluff ball, darker stripes, white-tipped tail. Thick woolly mountain fur. "
            "Pale stormy gray eyes. Notch in left ear from a rock tumble; worn with pride. "
            "Oversized paws. Clumsy headlong energy, always tripping."
        ),
        personality=(
            "Brave to foolishness, curious, loud, desperate for approval, secretly afraid of the dark. "
            "Wants to be Stoneguard; pounces pinecones, growls at shadows. Talks constantly about "
            "hunts never fought. At night presses to mother and pretends not to tremble."
        ),
        backstory=(
            "Only survivor of a litter of four; littermates died first moon. Named for gray coat "
            "and volcanic ashfall birth. Elders say ash-born wolves are Maw-touched."
        ),
        family_ties="Mother; Stoneguard Ashfall; Father; Hunter Grayrock.",
        rp_sample=(
            "Cinderpup pounced Flintpaw, bounced off, scrambled up: \"One day I'll knock you over!\" "
            "Flintpaw snorted. Cinderpup limped back, already planning the next attack."
        ),
        open_plots="Needs mentor; fear of heights exploited or cured; death by falling.",
    ),
    "Rime": _sheet(
        appearance=(
            "Gaunt scarred silver-gray and white; ice on stone. Thin patchy fur showing battle scars. "
            "Pale watery blue eyes. Missing chunk of left ear (frostbite). Long white whiskers. "
            "Slight limp from old hip injury. Voice a low rasping murmur."
        ),
        personality=(
            "Patient, stern, fair, deeply kind, exhausted. Raised more pups than any wolf in "
            "Greyspire; teaches old laws, border marks, bowing to Highfang. Does not coddle. "
            "Never lost a pup to cold or sickness. Tired but never shows weakness."
        ),
        backstory=(
            "Stoneguard father, caretaker mother. Took mother's place four years ago when she died "
            "of old age. Own litter stillborn; pours all mothering into pack pups."
        ),
        rp_sample=(
            "Cinderpup fell climbing; Rime's lip twitched. \"Get up,\" she called. \"Falling is not "
            "failing. Staying down is failing.\" She settled back, watching, waiting."
        ),
        open_plots="Killed defending den; retirement; stillbirth grief explored.",
    ),
    "Talus": _sheet(
        appearance=(
            "Lean long-limbed pale gray and white like shattered rock. Short thin fur. Bright amber "
            "eyes. V-shaped muzzle scar from fox fight. Long expressive tail. Bouncy eager energy, never still."
        ),
        personality=(
            "Energetic, curious, impulsive, loyal, easily distracted. Youngest hunter, desperate to "
            "prove herself. Volunteers for every hunt. Easily distracted by shiny rocks and birds: "
            "has cost hunts. Still feels like an imposter."
        ),
        backstory=(
            "Lowbelly mother died of illness when Talus was a pup. Raised by caretakers; fed last, "
            "hit often. Learned speed and quiet for survival. At two caught a hare no one else found; "
            "promoted to hunter apprentice."
        ),
        rp_sample=(
            "Talus missed the hare, watched the crevice; then spotted a shiny rock, picked it up, "
            "and forgot the hare entirely."
        ),
        open_plots="Distraction costs a hunt; accused of being a spy.",
    ),
    "Slate": _sheet(
        appearance=(
            "Compact muscular dark gray and charcoal; storm cloud over peaks. Thick coarse fur "
            "often snow-dusted. Pale flinty gray eyes. Deep scar across left shoulder (mountain "
            "goat's horn). Short bushy tail, heavily notched ears. Low ground-eating lope: "
            "efficient and silent."
        ),
        personality=(
            "Patient, competitive, grumpy, reliable, secretly soft. Three years hunting without "
            "missing a kill; not flashy, simply stalks and brings down prey. Respected, not liked. "
            "Secretly competitive with Ironjaw; trains harder in private."
        ),
        backstory=(
            "Stoneguard father, hunter mother. Chose hunting for time alone in mountains. At two, "
            "gored by a mountain goat; dragged back with horn still in shoulder. Hunts goats ever "
            "since, as if proving he is not afraid."
        ),
        rp_sample=(
            "Slate dropped onto a straggler goat, held through the kicks, dragged it toward den "
            "shoulder aching. Ironjaw: \"Good kill.\" Slate grunted and kept walking."
        ),
        open_plots="Rivalry with Ironjaw turns hostile; shoulder fails mid-hunt.",
    ),
    "Ironjaw": _sheet(
        appearance=(
            "Compact powerful smoky-gray coat lightening to silver on underbelly. Heavily muscled "
            "shoulders, thick neck, strong jaws. Rolls in volcanic ash from a nearby vent; "
            "permanent gray-white dusting that masks scent on the wind. Warm brown eyes (unusual for "
            "Greyspire), calm steady gaze. Left hind leg has a slight twist from an old poorly healed break."
        ),
        personality=(
            "Best hunter in Greyspire; does not brag or talk much. Prefers mountains to wolves. "
            "Kind by Greyspire standards: shares kills with Lowbellies unasked. Never challenged for "
            "rank. Content to simply be; but sadness and unnamed loneliness in his brown eyes."
        ),
        backstory=(
            "Stoneguard father, hunter mother. Chose hunting to spend less time around wolves; not "
            "antisocial, just cannot connect. At three, a goat kick sent him tumbling down a ravine; "
            "leg broke. Three days in snow before patrol found him. Leg healed wrong; ambush hunting "
            "now, never chases goats again."
        ),
        rp_sample=(
            "Ironjaw exploded from ash and snow, crushed the goat's windpipe, lay breathing blood "
            "and ash. A young wolf offered help; he shook his head. He wanted to be alone with the "
            "kill and the mountain. He never explained."
        ),
        open_plots=(
            "Someone breaks through his isolation; avalanche victim's family seeks revenge; "
            "rivalry with Slate."
        ),
    ),
    "Stonepiercer": _sheet(
        appearance=(
            "Lean angular mottled gray and white; fractured granite. Short rough fur dusted with "
            "rock powder. Pale piercing yellow eyes. Thin scar from left ear to jaw (ice fall). "
            "Unusually long bushy tail for balance. Jerky precise gait. Nonbinary (xe/xir)."
        ),
        personality=(
            "Observant, laconic, competitive, fair, secretly sentimental. Speaks little; words are "
            "sharp and exact. Prefers mountains to wolves. Can sit on a ridge all day without "
            "moving. Fiercely competitive with other scouts; never brags, lets results speak. "
            "Secret pouch of smooth stones from every successful patrol; touches them before sleep."
        ),
        backstory=(
            "Born Lowbelly, runt of five; littermates died in harsh leaf-bare. Survived in a warm "
            "vent crevice; found half-starved a moon later. Became scout because xe could not "
            "fight. At two, discovered a hidden pass that let Greyspire flank Silverrush; named "
            "Stonepiercer by the Highfang. Wears the name like armor."
        ),
        rp_sample=(
            "Stonepiercer watched Silverrush patrol from a ledge, counted them, slipped down silent "
            "as snowfall. Reported to Grim in three clipped sentences, then added a new stone to "
            "xir pouch."
        ),
        open_plots=(
            "Stone pouch stolen or discovered; forced to speak in crisis; hidden pass found by enemies."
        ),
    ),
    "Raven": _sheet(
        appearance=(
            "Slender dark-furred wolf; coat so black it absorbs light. Paws noticeably larger than "
            "his body (juvenile, not grown into yet). Bright curious amber eyes, ears constantly "
            "swiveling. Small notch in left ear from a fox dispute. Eager jittery energy, never still."
        ),
        personality=(
            "Young and knows it; talks too much, asks too many questions, smiles at wolves who'd "
            "rather eat him. Good at his job: large paws on loose stone, nearly invisible at night. "
            "Wants to be Stoneguard but runs ridges for news hoping Grim notices. Secretly terrified "
            "of the dark; shapes without form, eyes without faces; tells no one."
        ),
        backstory=(
            "Born to hunter and forager; runt, small and sickly. Grew unevenly; legs too long, paws "
            "too big. Could not fight but could run. Previous scout mentored him on ridges and wind. "
            "Mentor died last leaf-bare in a storm; Raven found the body, memorized the spot, kept running."
        ),
        rp_sample=(
            "Raven flattened against rock, counted Silverrush patrol below, stopped breathing when "
            "one looked up. Reported to Grim: extra patrols at mill ruins; they're scared. Grim: "
            "\"Good.\" Raven nodded and went to eat; always hungry."
        ),
        open_plots=(
            "Discovers something he should not; fear of the dark leads into danger; Grim takes notice."
        ),
    ),
    "Frostburn": _sheet(
        appearance=(
            "Broad-shouldered wolf with a coat of stark white and deep charcoal; like snow on "
            "volcanic rock. Thick double-layered fur makes hir look larger than ze is. Strange "
            "pinkish-red eyes (a rare albino trait). Cluster of old burn scars on hir left shoulder "
            "from a volcanic vent. Tail cropped short from frostbite. Nonbinary (ze/hir). Heavy, "
            "deliberate gait; each step a statement."
        ),
        personality=(
            "Silent, watchful, unexpectedly gentle, stubborn, haunted. Frostburn does not speak: "
            "not since hir litter died. Some say mute; others say ze simply has nothing to say. "
            "Communicates through gesture, posture, and a low rumbling growl that means different "
            "things depending on pitch. Terrifying to look at; pink eyes, burn scars, silence; "
            "but gentle with pups and Lowbellies, often sharing fresh-kill without being asked. "
            "Has never harmed a wolf who did not strike first."
        ),
        backstory=(
            "Born during a volcanic eruption. Hir litter; four pups; died of smoke inhalation. "
            "Ze survived because hir mother shoved ze into a crevice and sealed the entrance with "
            "hir own body. Ze emerged blind and burned, but alive. Grew up silent, watched, and "
            "strange. At two, ze saved a Stoneguard captain from an avalanche, dragging hir out "
            "of the snow with nothing but grit. The captain survived; Frostburn was given a guard "
            "position. Ze has never asked for anything else."
        ),
        rp_sample=(
            "Frostburn stood at the den entrance, hir pink eyes fixed on the darkening sky. Snow "
            "was coming; ze could smell it. The pups were inside, warm. Ze would not move until "
            "the storm passed. A young guard approached: \"Frostburn. Grim wants you at the high "
            "pass.\" Ze did not turn. Ze raised one paw and pointed at the nursery den. \"The pups?\" "
            "Ze nodded once. The young guard hesitated, then left. Frostburn stayed, silent as the "
            "mountain, watching the snow fall."
        ),
        open_plots=(
            "Hir silence could be broken; ze might be forced to kill; hir past could be revealed."
        ),
    ),
    "Hemlock": _sheet(
        appearance=(
            "Small for Greyspire; barely deer-meat weight. Reddish-brown coat fading to cream belly. "
            "Fur matted with dried herbs and blood. One eye clouded white (puphood cataract); head "
            "tilted to compensate. Paws stained dark green from mountain plants. Squirrel-hide neck "
            "pouch of precious remedies."
        ),
        personality=(
            "Only healer in Greyspire; hates the responsibility, screams, and deaths she cannot "
            "prevent, but cannot stop. Born with a gift for plants that saved her from the weak being "
            "killed. Sharp mocking wit keeps others at distance; insults Stoneguard then stitches them "
            "unasked. No one knows how to take her. She likes it that way."
        ),
        backstory=(
            "Healer line back to the Sundering. Never wanted the role; wanted to hunt. Rockslide at "
            "one year crushed her back leg; permanent limp. Mother taught herbs instead. Mother died "
            "of respiratory infection Hemlock could not cure; grief and relief. Last of her line; "
            "works in silence, dreams of running."
        ),
        rp_sample=(
            "Hemlock spat chewed moss into a Stoneguard's scratch: \"Hold still, vole-snoot, or I'll "
            "sew your mouth shut.\" She tied sinew, limped to herb storage. Leaf-bare coming; not ready."
        ),
        open_plots=(
            "Herb stores run out; patient she fails to save haunts her; wolf earns her respect."
        ),
    ),
    "Thorn": _sheet(
        appearance=(
            "Rangy and scarred, coat the color of dried blood; rusty red-brown that stands out against "
            "the mountain's gray. Fur thin and patchy in places, revealing old burns from a volcanic vent "
            "he fell into as a pup. Dark, almost black-brown eyes; nervous habit of licking his lips. "
            "Tail kinked at the tip; broken and healed wrong. Not large, but fast."
        ),
        personality=(
            "Not a natural Guard; too jumpy, reactive, and desperate for approval. Trains twice as hard "
            "as anyone else, runs twice as many patrols, volunteers for every dangerous assignment. Hopes "
            "that if he works hard enough, no one will notice his fear. Afraid of heights, darkness, other "
            "packs, the Maw, being alone, being forgotten; hides it behind bluster and bravado. It works "
            "on most wolves. It does not work on Hemlock, who sees right through him."
        ),
        backstory=(
            "His litter was thrown into a volcanic vent by a previous Highfang; a culling of weak blood. "
            "Thorn was the only survivor, crawling out with burns across half his body and a terror of heat "
            "that never left. Raised by a Lowbelly who found him, Cragheart, who taught him that survival "
            "is its own reward. Cragheart died last season of old age; Thorn was with him at the end and "
            "whispered, \"I'll make you proud.\" He has been trying ever since."
        ),
        family_ties="Foster-father Cragheart (deceased, last season). Littermates culled in volcanic vent as pups.",
        rp_sample=(
            "Thorn stood at the border, patchy fur bristling. The wind carried Mistmoor scent; rot and "
            "swamp and something watching. Icefang asked if anything moved; he jumped, said no, nothing, "
            "quiet. She left him alone until moonhigh. The mist thickened. He licked his lips and held "
            "his ground. At dawn he collapsed; but he had not run. That was what mattered."
        ),
        open_plots=(
            "Open to plots where his fear gets someone hurt, or where he finally confronts the wolf who "
            "threw his litter into the vent."
        ),
    ),
    "Icefang": _sheet(
        appearance=(
            "Lean and wiry; built for speed and precision rather than brute strength. Fur stark white-gray, "
            "almost luminous in moonlight, with darker gray points on ears and tail. All teeth filed to sharp "
            "points, a Stoneguard ritual; gums permanently raw, blood often on her lips. Flat pale blue eyes "
            "that show no emotion. No scars; not because she has never been wounded, but because she "
            "surgically removes scar tissue to keep her pelt smooth and her movements unhindered."
        ),
        personality=(
            "Does not speak unless necessary; short, clipped sentences when she does. Communicates through "
            "posture and gesture more than words. The perfect Stoneguard: obeys without question, kills "
            "without hesitation, feels nothing that would compromise duty. Young wolves find her terrifying; "
            "older wolves respect her. Grim trusts her as much as he trusts anyone. Beneath the ice, a strange "
            "tenderness for the mountains; grooms stone, clears lichen from sacred ledges, murmurs to peaks "
            "before a hunt. Loyalty is not to Grim but to Greyspire itself; if he ever betrayed the pack, "
            "she would kill him without blinking. Aromantic asexual."
        ),
        backstory=(
            "Rose through Stoneguard ranks on silence and precision. Underwent tooth-filing when she joined; "
            "endures the chronic pain without complaint. Removes her own scar tissue to stay smooth and fast. "
            "Grim's Stoneguard captain; Beta in all but name."
        ),
        family_ties="No living family on record. Devoted to Greyspire and the mountain.",
        rp_sample=(
            "The ridge was slick with frost, but Icefang did not slow. She flowed over the ice, filed teeth "
            "bared against the wind. Below, a patrol had cornered a Thistlehide scout; barely more than a "
            "pup, terror in his eyes. She dropped without a sound, landed behind him, and told her patrol "
            "to move back. \"Your alpha sent you,\" she said. It was not a question. She leaned in, breath "
            "cold, claw gentle on his throat: \"The mountain does not forgive. After the moon is whole again… "
            "we rend with teeth.\" She walked away. The scout collapsed."
        ),
        open_plots=(
            "Open to plots involving her loyalty being tested, or a wolf trying to reach the person beneath "
            "the ice."
        ),
    ),
    "Grim": _sheet(
        appearance=(
            "A mountain of a wolf even by Greyspire standards; broad-chested, thick-necked, gray-blue coat "
            "fading to near-black on paws and muzzle. Left ear torn to a ragged stump; a mesh of old scars "
            "crisscrosses his shoulders like a second pelt. Pale icy yellow eyes; habit of narrowing them to "
            "slits when judging another wolf's worth. A chunk of his tail missing; lost to a rockslide he "
            "survived as a young wolf. Moves with a deliberate, heavy gait, as if the mountain itself walks."
        ),
        personality=(
            "Did not become Highfang by being the strongest alone; though he is strong; but by being the "
            "cruelest at the right moments and the most generous at the right moments. The pack is a blade "
            "sharpened on the bones of the weak. Despises mercy; respects usefulness. Paranoid about other "
            "packs, especially after the mill expedition; believes the Pact of the Remembered is a Thistlehide "
            "trick to soften Greyspire's teeth. Secretly envies Finn'pelt's ability to inspire loyalty without "
            "fear. Rules through terror and bread, never showing the same face twice."
        ),
        backstory=(
            "Born a Lowbelly; lowest of the low. Mother was a Skeleton-Tooth elder culled during a hard "
            "leaf-bare; father unknown. Survived by being useful to the Stoneguard: carrying water, cleaning "
            "dens, eating last. At three, challenged a Stoneguard captain with a rock hidden in his paw; the "
            "captain died and Grim took his place. Previous Highfang Old Blight saw hunger in him, not honor. "
            "Grim killed Blight in his sleep on a blood-red moon, claiming fair challenge; no one disputed "
            "him. He has ruled four years; the mountains have never been quieter, or more tense."
        ),
        family_ties="No mate, no pups, no clear successor. Mother culled (Skeleton-Tooth elder); father unknown.",
        rp_sample=(
            "The cave was cold, but Grim did not shiver. He sat on the stone throne; a shelf worn smooth by "
            "generations of Highfangs; and watched the scout tremble. \"Repeat it,\" he said, voice gravel "
            "and frost. Finn'pelt was calling a gathering at the Sundering Stone to remember the dead. "
            "Grim's pale yellow eyes narrowed. \"The dead are carrion. The living are what matters.\" He "
            "stood, blocking the firelight. \"Send word to Silverrush. Tell their Current I want a private "
            "meeting before the gathering. And tell no one else.\" He stared at the cave wall, where a claw "
            "mark stood for every wolf he had killed. There were many."
        ),
        open_plots=(
            "Open to plots involving betrayal, succession crises, or secret alliances with Silverrush."
        ),
    ),
    "Cinder": _sheet(
        appearance=(
            "Dark ash-gray wolf with patchy, scarred coat; the result of a fire that killed his birth pack. "
            "Fur short and bristly, smelling faintly of smoke even now. Bright startling orange-yellow eyes "
            "like embers. One ear missing entirely (burned off); tail a stump; the rest lost to the same fire. "
            "Moves with jittery, nervous energy, as if he expects the world to catch flame at any moment."
        ),
        personality=(
            "Survivor, guilty, quiet, desperate to belong, secretly hopeful. The only survivor of a pack "
            "that burned in a human-caused wildfire; wandered alone for months before Silverrush found him "
            "half-starved and half-mad with grief on the riverbank. They took him in as Driftwood and gave "
            "him stones to carry; he carries them still. Does not speak much; voice hoarse and cracked from "
            "smoke inhalation. Flinches at sudden noises: snapping twigs, raised voices, crackle of dry leaves. "
            "Gentle and kind: shares food, grooms pups, wants to be good."
        ),
        backstory=(
            "Born in a small unnamed pack in the far north that did not believe in the Maw; they followed "
            "no god but the hunt. They were happy until humans left a campfire unattended. He does not "
            "remember the fire clearly; heat, screaming, burning fur, running until his paws bled. When he "
            "stopped, he was alone and never went back. Collapsed on Silverrush's riverbank; Ripple found "
            "him. Carrying stones is the first time he has felt useful."
        ),
        family_ties="Birth pack lost to wildfire; no survivors known. Taken in by Silverrush; Ripple found him.",
        rp_sample=(
            "Cinder carried the stone; a smooth river rock the size of his head; pressed against his chest "
            "from bank to bank. Aromis watched from the shore: \"You're good at that. Do you ever wonder "
            "why we make Driftwood carry stones?\" Cinder stopped, looked at the rock, then at him. \"To "
            "remind us,\" he said, voice cracked and quiet, \"that we are not the heaviest thing in the "
            "world.\" Aromis nodded and walked away. Cinder dropped the stone, picked up another, and kept "
            "carrying."
        ),
        open_plots=(
            "Open to plots where he must confront his past, or where his trauma is triggered at a critical moment."
        ),
    ),
    "Pebble": _sheet(
        appearance=(
            "Small, roundish wolf with a coat of soft gray and cream; like river stones smoothed by centuries "
            "of current. Fur short and sleek; always damp from nervous sweating, not swimming. Bright nervous "
            "hazel eyes, darting constantly. Small crooked scar on left hind leg (birth defect corrected by "
            "surgery as a pup). Ears slightly too large for his head, giving a perpetual look of surprise."
        ),
        personality=(
            "Anxious, meticulous, earnest, surprisingly brave, deeply lonely. Not a natural diplomat: "
            "stutters when nervous (which is always), forgets talking points, apologizes too much. Good at "
            "the job not because he is smooth but because he is honest; wolves trust him because he is too "
            "anxious to lie convincingly. Saltmuzzle chose him as the only wolf in Silverrush who "
            "volunteers for the role. He stumbles through negotiations, makes mistakes, learns, and somehow "
            "gets results."
        ),
        backstory=(
            "Born with a twisted leg; the pack healer said he would never walk properly. After three "
            "painful bite-and-hold surgeries he could run; never fast, but steady. Became a diplomat because "
            "he was not strong enough to hunt, not fast enough to scout, not brave enough to guard. Thought "
            "he would fail. Saltmuzzle gave him a chance. He has been failing upward ever since."
        ),
        family_ties="No family noted. Mentored by Saltmuzzle.",
        rp_sample=(
            "Pebble stood at the border, too-large ears swiveling. Greyspire envoy Sleet stared down at him. "
            "\"You wanted to discuss fishing rights,\" he said, voice cracking; the stretch near the mill "
            "ruins, fish back, both packs wanting access. \"I propose a rotation. One week Greyspire, one "
            "week Silverrush. Alternating. Starting with you. To show good faith.\" Silence. Then Sleet "
            "inclined her head: \"Acceptable.\" Pebble blinked. \"Really?\" \"Do you want me to change my "
            "mind?\" \"No! Thank you.\" He fled, nearly tripping. Behind him, Sleet almost smiled."
        ),
        open_plots=(
            "Open to plots where his anxiety is exploited, or where he must negotiate under threat of violence."
        ),
    ),
    "Driftpup": _sheet(
        appearance=(
            "Small scruffy pup with dusty gray and brown coat; like driftwood left too long in the sun. "
            "Fur patchy and thin; pale white blaze on forehead. Bright nervous hazel eyes, darting constantly. "
            "Short stubby tail (birth defect). Paws too large for his body, making him trip often. Smells "
            "faintly of smoke; remnant of the fire that killed his birth pack."
        ),
        personality=(
            "Anxious, quiet, grateful, easily startled, desperately eager to belong. Not born in Silverrush: "
            "found alone on the riverbank after wildfire destroyed his birth pack. Does not talk about it; "
            "does not talk much at all. Follows older Driftwood wolves, watching them carry stones, trying "
            "to imitate them. Wants to be useful; terrified of being thrown out. Flinches at loud noises: "
            "cracking sticks, raised voices, thunder. Sleeps curled tight under ferns. Gentle: shares food, "
            "grooms other pups, wants to be good."
        ),
        backstory=(
            "Birth pack lived far south in dry pine and scrub; loners, rogues, outcasts, not part of the "
            "four packs. Wildfire from twoleg carelessness swept their territory when he was one moon old; "
            "he was the only survivor. Wandered a quarter-moon on insects and puddles until he collapsed on "
            "Silverrush's riverbank. Ripple found him; the healer treated him. Ashpool allowed him to stay, "
            "but he is not Silverrush-born; Driftwood, an outsider always proving himself."
        ),
        family_ties="None living; birth pack dead. Found by Ripple; permitted to stay by Ashpool.",
        rp_sample=(
            "Driftpup sat at the river's edge, scruffy gray coat blending with driftwood. Silverrush-born "
            "pups splashed in the shallows; he wanted to join but did not dare. He picked up a small stone "
            "and carried it to the pile on the far bank; again and again. That was what Driftwood wolves "
            "did. A shadow fell; he flinched. Ripplepup stood dripping: \"Why aren't you playing?\" He did "
            "not answer. She grabbed a stone, carried it, came back, said nothing; just carried beside him. "
            "Driftpup's eyes burned. He blinked and kept carrying."
        ),
        open_plots=(
            "Trauma triggered during fire or Monster attack; possible adoption by a Silverrush wolf; "
            "villain arc if exploited."
        ),
    ),
    "Ripplepup": _sheet(
        appearance=(
            "Small sleek pup with pale silver and white coat; like moonlight on shallow water. Fur short "
            "and water-repellent; always damp from splashing in the shallows. Deep navy blue eyes, almost "
            "purple in certain light. Small dark patch on her hip shaped like a fish skeleton. Paws slightly "
            "webbed; strong Silverrush bloodline. Moves with wobbly, excited energy."
        ),
        personality=(
            "Energetic, fearless, nosy, loyal, easily distracted. The pup who asks strangers their names, "
            "tries to befriend crows, chases minnows until shivering with cold. Not afraid of deep water, "
            "older wolves, or Maw stories; her mother says she has no sense of self-preservation; Ripplepup "
            "thinks that is a compliment. Intensely curious about the mill ruins and the red river during "
            "the awakening. Collects rusted iron scraps in a hidden cache; drawn to them without knowing why."
        ),
        backstory=(
            "Born in Silverrush to hunter mother Minnow and diplomat father Pebble. Only surviving pup of "
            "her litter; siblings swept away by flash flood at two moons; she clung to a fallen log and "
            "does not remember it. Her mother does. Strange connection to the river: feels the current "
            "shift before it changes, knows when fish are coming. Elders say she is touched by the Maw; "
            "she likes the sound of that."
        ),
        family_ties="Mother; Minnow (Hunter). Father; Pebble (Diplomat). Littermates lost to flash flood.",
        rp_sample=(
            "Ripplepup splashed through the shallows, silver fur dark with water. Rusted iron glinted in the "
            "mud; she dove, grabbed it in her teeth, surfaced with a triumphant squeak. Driftpup watched "
            "from the bank: \"Another one?\" \"Another one!\" She paddled ashore and dropped the iron at "
            "Driftpup's paws. \"I'm going to build a mountain.\" \"It's just a pile of rust.\" \"It's a "
            "mountain; and when it's tall enough, I'm going to climb it and howl at the moon.\" Driftpup "
            "sighed, but helped carry the iron back to the hiding spot."
        ),
        open_plots=(
            "Iron collection could have supernatural consequences; drawn to mill ruins; possible drowning or rescue."
        ),
    ),
    "Riptide": _sheet(
        appearance=(
            "Small, roundish wolf with soft gray and cream coat; like river stones. Fur short and sleek; "
            "always damp from wading in the shallows to fetch floating pups. Warm hazel brown eyes; small "
            "white patch on chest. Ears slightly too large for his head, giving a perpetually worried look. "
            "Moves with a quick, bobbing gait, never still."
        ),
        personality=(
            "Anxious, nurturing, easily flustered, deeply loyal, secretly brave. Not a natural den-keeper: "
            "anxious, easily overwhelmed, cries when pups get hurt; but good at it anyway. Notices when a "
            "pup is sick before anyone else, stays up all night with colicky ones, finds lost pups in tall "
            "reeds. Fiercely loyal to Silverrush; born Driftwood, taken in by the pack; he will spend his "
            "life repaying that debt."
        ),
        backstory=(
            "Born to a rogue mother who died when he was a pup. Found alone on the riverbank, half-drowned, "
            "by a Silverrush patrol; Saltmuzzle allowed him to stay. First year carrying stones, proving "
            "himself. When the previous caretaker retired, Riptide volunteered; no one else wanted the job. "
            "Two years in and he still has no idea what he is doing."
        ),
        family_ties="Rogue mother (deceased). Taken in by Silverrush; mentored by Saltmuzzle.",
        rp_sample=(
            "Riptide splashed through the shallows, heart pounding; Driftpup had wandered off again. He "
            "followed tiny pawprints to a thick clump of reeds. \"Driftpup! Where are you?\" A small gray "
            "face poked out: \"Here.\" Riptide exhaled. \"Don't do that. You scared me.\" \"Why?\" \"Because; "
            "never mind. Just come back to the den.\" He nudged the pup toward shore, already planning to move "
            "the den farther from the water."
        ),
        open_plots=(
            "Could lose a pup to drowning; might be forced to fight for the den; his anxiety could be exploited."
        ),
    ),
    "Ebb": _sheet(
        appearance=(
            "Small scruffy wolf with pale gray and brown coat; like driftwood bleached by the sun. Fur "
            "patchy and thin; white blaze on chest. Pale watery blue eyes; missing chunk from left ear "
            "(Twoleg trap). Paws calloused but quick. Light, almost silent step; years of avoiding danger. "
            "Still carries scars from captivity."
        ),
        personality=(
            "Quiet, grateful, anxious, observant, desperately eager to belong. Not born in Silverrush: "
            "found on the riverbank alone, shivering, rusted trap still on aer leg. Ripple removed it and "
            "nursed ae back. Now serves as scout, using sharp eyes and cautious nature on borders. Does not "
            "speak much; voice soft and hesitant, afraid of taking up space. Watches other wolves closely: "
            "habits, moods, secrets. Wants to be useful; terrified of being thrown out."
        ),
        backstory=(
            "Born to a rogue mother who abandoned ae at birth. Raised by Twolegs as a prisoner; wire cage, "
            "scraps, traps set for wild wolves. Escaped when the cage rusted through. Wandered a moon on "
            "insects and puddles until ae collapsed on Silverrush's riverbank. Ripple found ae; Saltmuzzle "
            "allowed ae to stay. First carried stones like other Driftwood; pack noticed sharp senses and "
            "stealth. Ashpool promoted ae to scout. Still has nightmares about the cage."
        ),
        family_ties="Unknown birth mother (rogue). Cousin Fern (rogue; may appear later).",
        rp_sample=(
            "Ebb crouched low in the reeds, pale eyes fixed on the far bank. Wind carried Greyspire scent: "
            "sharp and cold. Ae held still until the patrol passed, then slipped into shadows to report. "
            "\"One patrol, three wolves,\" ae whispered to Saltmuzzle. \"Heading north. They seemed tired.\" "
            "Saltmuzzle nodded: \"Good work, Ebb.\" Ae ducked aer head, warmth blooming. Good work. Maybe ae "
            "did belong here after all."
        ),
        open_plots=(
            "Past with Twolegs could catch up; accused of spying; could find a protector or mate."
        ),
    ),
    "Curlgrip": _sheet(
        appearance=(
            "Lean muscular wolf with dark silver and white coat; like storm clouds over the river. Fur "
            "short and water-repellent, always slicked back. Striking mismatched green and blue eyes; deep "
            "curved scar on left shoulder (fishing line cut). Thick strong tail used as a rudder in fast "
            "water. Smells of river mint and wet stone."
        ),
        personality=(
            "Playful, competitive, restless, surprisingly philosophical, deeply loyal. Fastest swimmer in "
            "Silverrush; fae knows it, challenges other hunters to races, always winning, always laughing. "
            "Beneath playfulness, serious about the hunt; never lost a fish once jaws have locked on. Spends "
            "hours alone in shallows watching water, thinking. Theories the Maw is not hungry but lonely, "
            "that chewing is speech not hunger. Does not share often; wolves would think faer strange."
        ),
        backstory=(
            "Born in Silverrush to hunter mother and scout father. Sickly pup; ear infections and fevers. "
            "Learned to swim before fae could run; water was the only place fae felt strong. At two, "
            "single-pawedly brought down a sturgeon twice faer size; pack feasted a week. Saltmuzzle named "
            "faer Curlgrip for the way fae curls around struggling prey and never lets go."
        ),
        family_ties="Hunter mother and scout father (Silverrush-born).",
        rp_sample=(
            "Curlgrip floated in the shallows, mismatched eyes fixed on salmon. A fish broke from the school: "
            "fae lunged, jaws closing on silver scales, bit through the spine, paddled to shore. Fae laid the "
            "salmon on the bank and watched the water. \"You are not hungry,\" fae murmured. \"You are lonely. "
            "I understand.\" A passing wolf gave faer a strange look. Curlgrip smiled and carried the fish to "
            "the fresh-kill pile."
        ),
        open_plots=(
            "Heretical beliefs discovered; challenged for rank; mate who shares faer philosophy."
        ),
    ),
    "Churn": _sheet(
        appearance=(
            "Thick-necked, barrel-chested wolf with dark gray and white coat; like a storm cloud over the "
            "river. Fur short and water-repellent; always damp from swimming. Cold pale gray eyes; deep "
            "jagged scar across shoulder (beaver trap). Thick muscular tail used as a rudder in fast "
            "current. Rolling, powerful gait, never hurried."
        ),
        personality=(
            "Strongest swimmer in Silverrush, though he never brags. Hunts deep channels where current "
            "could drown a wolf, brings back the largest fish. Other hunters respect him; do not like him. "
            "Too quiet, too intense, too focused. Fiercely competitive with Aromis; does not hate him, "
            "simply cannot stand being second-best. Trains in secret, pushing harder, hoping to catch more "
            "fish, run faster, hunt longer."
        ),
        backstory=(
            "Born in Silverrush to hunter mother and guard father. Mother drowned in a flash flood that "
            "swept her off a sandbar when he was a pup; Churn watched it happen. Afraid of deep water "
            "ever since. Hides it by being the best; swims where others dare not, not from bravery but "
            "refusal to let the river win. Hunts in memory of his mother, hoping enough fish will let the "
            "Maw let her rest."
        ),
        family_ties="Mother drowned (flash flood). Guard father. Rivalry with hunter Aromis.",
        rp_sample=(
            "Churn stood at the river's edge, pale gray eyes on dark water. Current strong today; he did "
            "not hesitate, stepped in and let it take him. Swam deep, kicked with powerful hind legs, tail "
            "as rudder. A sturgeon three deer-lengths long; he dove, grabbed its tail, let it drag him, "
            "never let go. When it tired, he bit through its spine and paddled to bank. Aromis on the "
            "shore: \"Good catch.\" Churn did not answer. He needed the river to know he was not afraid."
        ),
        open_plots=(
            "Fear of deep water exposed; rivalry with Aromis becomes alliance or open feud."
        ),
    ),
    "Aromis": _sheet(
        appearance=(
            "Grey to dark grey wolf, face mostly consumed by a dim black mask grading into light grey and "
            "near-white along neck and chest. Fluffy fur from head to neck; beneath it, lean and bold in "
            "shape. Constant running and fighting built his strength; he would not call himself the best. "
            "Only noticeable scar on his neck; a bite mark from a past encounter, partially hidden as fur "
            "grows over it. Piercing near-magenta eyes stand out when sneaking or ambushing; often the first "
            "to be seen."
        ),
        personality=(
            "Stubborn, self-centered, lacking empathy (initially), slowly redeeming, calmer with time. "
            "Difficult traits from harsh upbringing; emotional coldness; yet slowly trying to alter them, "
            "learning connection, trust, and vulnerability."
        ),
        backstory=(
            "Never knew love or intense feeling. Mother abandoned him early; sire stern, cold, forcing beliefs "
            "on the pup. Grew emotionless and unempathetic. At one year he left his sire for individuality; "
            "some fighting and hunting knowledge the only things to thank him for. Then a strange wolf much "
            "larger and stronger grabbed him by the neck, sinking deep canines in. He hung in those jaws, "
            "reminisced one fleeting moment of happiness, then darkness. Woke alive among Silverrush wolves "
            "with white-grey coats; met with smiles, not judgment. Something new. Purpose unchanged: revenge "
            "on the wolf that marked him."
        ),
        family_ties="Unknown; never speaks of sire or mother. Searches for the wolf that scarred his neck.",
        rp_sample=(
            "Flashback; first days in Silverrush. Paws sank into sand; territory smelled of river, not salt. "
            "Hungry, he sought the den for leftover meat and found nothing. A calm older female approached: "
            "dark grey overtaken by grey and white, not much time left in this world. \"Are you hungry, my "
            "dear? If it is food you are looking for, you will find your luck in the river.\" She grinned "
            "softly, eyes closed. Aromis's ears perked. The river; sinister smells, yet the only source of "
            "food."
        ),
        open_plots=(
            "Revenge on the wolf that marked him; cold stares at unfamiliar wolves from other packs; "
            "redemption arc with Silverrush. RP: open to injury and combat with narrative consequence; "
            "no permanent death or fight-to-the-death without consent."
        ),
    ),
    "Ripple": _sheet(
        appearance=(
            "Slender graceful wolf with pale cream and soft gray coat; like sunlight on shallow water. "
            "Fur always damp even when she has not been swimming, clinging to her lean frame. Pale "
            "translucent green eyes, almost colorless in bright light. No visible scars; slight limp from "
            "a dislocated hip that healed wrong. Small rounded ears; habit of flattening them when thinking."
        ),
        personality=(
            "Not a healer because she wanted to be; because she cannot stand to see others suffer. Gift "
            "for easing pain, physical and deeper: grief, fear, loneliness. Wolves come for wounds and "
            "comfort; she gives freely, asking nothing. Anxious about the river's warmth; knows it means "
            "something beyond herbs and poultices. Prays to the Maw every night, nose to the water; the "
            "Maw does not answer. She keeps praying anyway."
        ),
        backstory=(
            "Born with dislocated hip; should have killed her. Healer mother refused to let her die; spent "
            "moons manipulating the joint, massaging muscles, teaching her to walk despite pain. By one year "
            "she could run, swim, and hunt; always with limp and dull ache. Mother died of heart attack when "
            "Ripple was two; Ripple found her in the herb den still clutching feverfew. Did not howl; sat "
            "beside her and finished grinding the herbs."
        ),
        family_ties="Healer mother (deceased, heart attack). Known for taking in riverbank strays.",
        rp_sample=(
            "Ripple chewed willow bark soft and pressed it into a wound. The young wolf whimpered but held "
            "still. \"Good,\" she murmured. \"You're doing good.\" She worked in silence, pale green eyes "
            "focused, damp fur dripping on the patient. The river burbled; same as always, but warmer. "
            "Hungrier. \"Healer? Is the Maw angry at us?\" Ripple paused. \"The Maw is hungry,\" she said. "
            "\"Not angry. There is a difference.\" She tied the bandage. The pup closed their eyes. Ripple "
            "stared at the steam rising and wondered if she was lying."
        ),
        open_plots=(
            "Must heal a wolf from another pack; faith tested by the warming river."
        ),
    ),
    "Rift": _sheet(
        appearance=(
            "Long lean wolf with pale silver-gray and white coat; like moonlight on shallow water. Fur "
            "thin and often wet, plastered to muscular frame. Pale icy blue eyes; deep jagged scar across "
            "chest (Greyspire raid). Unusually short tail; bitten off by a pike as a pup. Quiet liquid "
            "grace in motion; when still, utterly motionless, like a stone in the current."
        ),
        personality=(
            "Saltmuzzle's shadow. Does not speak much, but when he does, other wolves listen. Enforces her "
            "orders, breaks up fights, decides which border disputes are worth a rend. Not cruel: "
            "efficient. Respected; few like him. In love with Saltmuzzle for years, never told her; knows "
            "she still grieves her dead mate. Waits, watches, keeps her safe. That is enough."
        ),
        backstory=(
            "Born in Silverrush to hunter and scout. Mother drowned as a pup, swept by current; he learned "
            "to swim in that same current, refusing to let the river take him too. Became guard, then "
            "Saltmuzzle's second, by being the wolf who never drowned. Carries guilt for not saving "
            "Saltmuzzle's mate during a Greyspire raid; was there, too slow. Trying to make up for it ever "
            "since."
        ),
        family_ties="Mother drowned (current). Devoted to Saltmuzzle. Mate she lost; guilt over his death.",
        rp_sample=(
            "Rift stood at the river's edge, pale blue eyes on the far bank. Saltmuzzle behind him, speaking "
            "to a scout; he did not turn; knew her voice, scent, rhythm of breathing. \"Rift.\" Soft. Tired. "
            "\"Current.\" \"The Greyspire patrol is moving west. Take a team. Watch them. Do not engage.\" He "
            "nodded; wolves chosen, route scouted, always three steps ahead. Turning to leave, Saltmuzzle "
            "touched his shoulder with her nose: \"Be careful.\" He did not answer. He could not promise that."
        ),
        open_plots=(
            "Feelings for Saltmuzzle revealed; guilt drives him to sacrifice himself."
        ),
    ),
    "Saltmuzzle": _sheet(
        appearance=(
            "Striking wolf with coat the color of river stones; pale gray, silver, and white, darker "
            "speckles across shoulders. Fur short and sleek, perfect for swimming; webbed paws (rare in "
            "Silverrush). Deep calm blue eyes; habit of tilting her head when listening, as if hearing "
            "something far away. Left ear torn in two places; battle scars from a Greyspire raid years ago."
        ),
        personality=(
            "Led Silverrush three years since the previous Current drowned in flash flood. Did not want the "
            "role; was diplomat, peacemaker, hated violence; but the pack chose her. Leads with patience, "
            "negotiation, steady voice that does not waver. Tired: river's warmth, the mill, packs circling: "
            "too much. Misses when the biggest problem was a flooded den or stolen kill. Wonders if she is "
            "right for this moment. Does not say so aloud."
        ),
        backstory=(
            "Born in Silverrush, daughter of a Current who died young. Mother was a diplomat; Saltmuzzle "
            "followed; negotiation, truce, weight of a promise. Five years ago Greyspire raid killed her "
            "mate; a gentle forager who died protecting pups that were not his. She watched him fall, did "
            "not scream or fight, just carried on. That is what Silverrush wolves do. Has not taken another "
            "mate; does not think she ever will."
        ),
        family_ties="Current father (deceased young). Diplomat mother. Mate killed in Greyspire raid (forager). Beta Rift devoted to her protection.",
        rp_sample=(
            "Saltmuzzle stood at the river's edge, webbed paws in wet sand. Water too warm, faint iron "
            "smell; she had watched the current a quarter-moon. Aromis approached: \"Current. The patrol "
            "returned.\" \"What did they find?\" \"The tooth. In the mill. They brought back a piece.\" "
            "Saltmuzzle closed her eyes. \"Bring it to me. Then send word to the other packs. We need to "
            "talk.\" \"The other packs? After everything?\" She turned; blue eyes calm, something hard "
            "beneath. \"Especially after everything.\""
        ),
        open_plots=(
            "Choose between peace and war; mate's death avenged or forgiven."
        ),
    ),
    "Barkhollow": _sheet(
        appearance=(
            "Stout, round wolf with rough brown and gray coat; like tree bark. Fur thick and knotted, "
            "often covered in moss and leaf litter. Warm dark amber eyes; deep hollow-chested appearance "
            "(birth defect; lungs work harder). Wide calloused paws, good for digging. Smells of damp earth "
            "and rotting wood."
        ),
        personality=(
            "Slow, methodical, kind, forgetful, deeply wise. Moves at his own pace; does not hurry, panic, "
            "or raise her voice. Others find his slowness frustrating, but he never misses a root or mushroom; "
            "never returns empty-pawed. Forgetful about time and pouches, but remembers places flawlessly; "
            "every berry bush, nut tree, patch of feverfew."
        ),
        backstory=(
            "Born with hollow chest; lungs did not form properly. Mother expected her to die; he did not. "
            "Learned to move slowly, conserve breath, listen more than speak. At two, discovered a hidden "
            "grove of wintergreen berries that saved the pack during harsh Leaf-bare. Finn'pelt named him "
            "Barkhollow for rough coat and empty chest. Wears it with pride."
        ),
        family_ties="Mother; Mossroot (elder forager). Father; Fallow (deceased hunter).",
        rp_sample=(
            "Barkhollow knelt beside feverfew, wide paws parting leaves. He did not pick yet; first bowed "
            "her head. \"Thank you, Maw, for this gift. I will take only what I need.\" Three leaves into "
            "his pouch. A young wolf tapped impatiently: \"Barkhollow, the alpha is waiting.\" He stood "
            "slowly. \"The alpha can wait. The feverfew cannot.\" She shuffled toward the den, leaving the "
            "young wolf to sigh and follow."
        ),
        open_plots=(
            "Slowness could cost a life; left behind during fire; hidden grove found by Twolegs. "
            "RP: open to injury, emotional scenes, survival tension."
        ),
    ),
    "Fernspot": _sheet(
        appearance=(
            "Small roundish wolf with dusty brown and pale green coat; like dried ferns. Fur short and "
            "soft; darker spots scattered across shoulders. Warm frightened amber eyes; habit of looking "
            "over her shoulder constantly. Small neat paws. Nervous twitchy energy, never still."
        ),
        personality=(
            "Anxious, remorseful, secretive, soft-spoken, desperate for approval. She agreed to the "
            "abandonment; tells herself she had no choice, elders said the pup was cursed, the pack would "
            "starve; but knows she had a choice and made the wrong one. Cries in secret. Tried to approach "
            "Kanami twice and lost her nerve each time. Leaves small piles of edible roots near Kanami's "
            "hiding spots, pretending they are accidental."
        ),
        backstory=(
            "Born in Thistlehide to forager mother and hunter father. Never ambitious; wanted mate, litter, "
            "quiet life. When Kanami was born blind and marked, Fernspot felt love; then terror. Elders' "
            "words burned: curse, rot, death. She let Ashbark take the pup. Has not forgiven herself; does "
            "not expect Kanami to forgive her either."
        ),
        family_ties="Mate; Ashbark (same den, do not speak of Kanami). Forager mother, hunter father.",
        rp_sample=(
            "Fernspot crept through undergrowth, feverfew roots in her jaws. At a clearing's edge Kanami "
            "sat motionless beneath a hazel bush. Fernspot dropped the roots and backed away. A twig snapped. "
            "Kanami's head turned: \"Who's there?\" Fernspot froze, did not answer, could not; slipped into "
            "the ferns, heart pounding, leaving the roots behind."
        ),
        open_plots=(
            "Kanami discovers her offerings; Fernspot confesses; ostracized if truth comes out."
        ),
    ),
    "Mossgaze": _sheet(
        appearance=(
            "Small by Thistlehide standards; roughly half-grown deer weight; dusty russet-brown coat "
            "darkening to tawny on flanks and belly. Fur thick and shaggy in winter, short and sleek in "
            "summer. Pale washed-out amber eyes in a darker face, perpetually startled look. Thin white scar "
            "through left eyebrow and across nose bridge (childhood thorn thicket); left ear notched twice "
            "from brambles. Unusually large splayed paws; clumsy on flat ground, nimble on tangled root-heaves."
        ),
        personality=(
            "Watchful, quiet, brittle, loyal, self-effacing. Speaks in short bursts, often trails off mid-sentence. "
            "Tracks every exit, reads group mood before entering, calibrated to avoid attention. Competent but "
            "unremarkable among foragers; precise plant knowledge, confidence shattered by a harsh word. Around "
            "brother Finn'pelt she becomes almost invisible; strangers assume she fears him. She understands him "
            "perfectly and plays her role without complaint. Alone with him in deep mist before dawn, shoulders "
            "nearly touch; neither speaks. That is their conversation."
        ),
        backstory=(
            "Born in Thistlehide to low-ranking hunter mother who died of infection at six moons. Brother "
            "Finn'pelt already grown, carving reputation with scarred knuckles. Most assumed he would let the "
            "runt die; instead he left half-killed rabbits at the den; never seen, never acknowledged. At ten "
            "moons older pups cornered her in a ravine and forced foxglove; she vomited and survived but cracked; "
            "fear of other wolves, not death. Never told Finn'pelt. Yearling deadfall trap caught her leg; chewed "
            "fur off to escape; scar ring on right ankle. Never seen a living human."
        ),
        family_ties="Younger sibling of Finn'pelt; public coldness, secret hyper-protection. One of few who has seen him vulnerable.",
        rp_sample=(
            "Mossgaze knelt in wet moss, fingers parting fronds with practiced care. Pale amber eyes flicked "
            "to the clearing's exits, then back to the yarrow. She plucked three stems and dropped them in her "
            "pouch. A voice behind her; she flinched, nearly dropped the bundle. \"I; it's fine. I have enough.\" "
            "She did not turn around. She never turned around when she did not have to."
        ),
        open_plots=(
            "Any injury or witness to her bond with Finn'pelt forces him to choose reputation or loyalty. "
            "If he takes a mate, she will watch that wolf with quiet, terrible attention."
        ),
    ),
    "Thyme": _sheet(
        appearance=(
            "Small neat wolf with pale green-gray and soft cream coat; like thyme on limestone. Fur short "
            "and smooth, always immaculately clean. Bright intelligent hazel eyes; small precise scar on "
            "upper lip (diplomatic mission gone wrong). Long expressive tail, often curled over back. "
            "Dancer's grace; each step economical."
        ),
        personality=(
            "Witty, calm, perceptive, private, fiercely principled. Youngest diplomat in Thistlehide and "
            "already the most effective; listens more than ze speaks, asks questions that cut to the heart "
            "of disputes, finds compromises that leave both sides heard. Intensely private: no one knows where "
            "ze sleeps or if ze has a mate. Deflects personal questions with a smile. Some find zir cold; "
            "others find zir fascinating."
        ),
        backstory=(
            "Born to diplomat mother and hunter father. Mother taught ze to read wolves; postures, silences, "
            "lies. Father taught ze words are weapons. At two, negotiated truce between Thistlehide and "
            "Silverrush after a border fight killed three wolves; lasted a full year. Finn'pelt named ze "
            "diplomat on the spot. Has not failed a negotiation since."
        ),
        family_ties="Diplomat mother, hunter father.",
        rp_sample=(
            "Thyme sat across from Greyspire envoy Sleet, hazel eyes calm. She had been shouting five "
            "minutes. Ze let her finish, then spoke soft: \"You are angry because your pack is hungry. I "
            "understand. But shouting will not fill your bellies. Thistlehide has surplus roots. Silverrush "
            "has surplus fish. Stop raiding the southern pass and I can arrange a trade; or keep shouting. "
            "It is your choice.\" Sleet stared, then sat. \"What kind of trade?\" Thyme smiled. \"Let us "
            "discuss.\""
        ),
        open_plots=(
            "Negotiation turns violent; past revealed; forced to lie despite principles."
        ),
    ),
    "Root": _sheet(
        appearance=(
            "Stout thick-furred wolf with dark brown and deep gold coat; like old bark. Fur coarse and "
            "knotted, always covered in moss and twigs. Warm dark amber eyes; thick bushy tail she wraps "
            "around sleeping pups. Muzzle graying with age; left ear torn from a badger fight years ago. "
            "Slow deliberate gait, never hurrying."
        ),
        personality=(
            "Patient, wise, no-nonsense, deeply kind, stubborn. Has watched Thistlehide pups longer than "
            "any wolf remembers; teaches them to walk, eat solid food, recognize twoleg traps. Does not "
            "coddle: if a pup falls, they get up; if they cry, they learn to stop. Sits with sick ones "
            "through the night, warm belly to shivering bodies. Refused to let elders kill Kanami, threatening "
            "to leave; threat carried weight; she has raised every wolf in the pack."
        ),
        backstory=(
            "Born in Thistlehide to a long line of caretakers. Took over at three when mother died of old age; "
            "never left. Mate Thistleclaw (hunter) died ten years ago; still sleeps in their den alone. "
            "Outlived all her own pups: one sickness, two border fights, one left and never returned. Does not "
            "talk about them; shows love by raising the pack's pups as grandchildren."
        ),
        family_ties="Mate Thistleclaw (deceased). Caretaker mother (deceased). Own pups lost or gone.",
        rp_sample=(
            "Root sat in the nursery den, bushy tail wrapped around Pale'Step. The tiny white pup shivered, "
            "breath wheezing. Root pressed closer, warmth seeping into the fragile body. \"You'll be fine,\" "
            "she murmured. \"You're too stubborn to die.\" Pale'Step coughed and snuggled deeper into Root's "
            "fur. An hour passed. Another. Root did not move; she would stay all night if she had to."
        ),
        open_plots=(
            "Could die of old age leaving a gap; lost pup returns; forced to choose between Kanami and elders."
        ),
    ),
    "Mossheart": _sheet(
        appearance=(
            "Lean wiry wolf with golden-brown coat darkening to umber along spine. Fur thick and bristly "
            "like thistle, often tangled with burrs and twigs. Sharp intelligent green eyes; large ears "
            "constantly moving, tracking sounds. Thin white scar on cheek from a thorn bush that nearly took "
            "his eye."
        ),
        personality=(
            "The pack's best scout; not because he is brave, but because he is nervous. Always looking for "
            "danger, listening for threats, planning escape routes. Anxiety makes him excellent at his job "
            "and exhausting to be around. Keeps everything in order: den, herb pouch, patrol routes. Cannot "
            "stand mess or unpredictability. The blind pup, the mill, the Maw; pushed to the edge. Wants "
            "normal back; knows it never will."
        ),
        backstory=(
            "Born to scout mother and hunter father; both still alive, both deeply disappointed. Not strong "
            "enough to hunt, not brave enough to guard; only a scout, running from danger instead of toward "
            "it. Never told anyone he is in love with a Silverrush hunter met at the border three moons ago. "
            "They meet in secret, exchange news, share meals. Forbidden; he does not care. It is the only "
            "warmth in his life."
        ),
        family_ties="Scout mother and hunter father (both living, disappointed). Secret lover; Rivenmaw (Silverrush hunter).",
        rp_sample=(
            "Mossheart pressed his belly to the ground, bristly fur blending with thistle. Below, a Silverrush "
            "wolf sat alone. His heart raced. He crept forward. Green eyes met green eyes. \"You're late,\" "
            "Rivenmaw said. \"I know; there was a patrol. I had to hide.\" Rivenmaw nuzzled his cheek. "
            "\"You're always hiding.\" \"I'm a scout. It's what I do.\" They watched the sun set. Mossheart "
            "wanted to speak of the missing moon, the blind pup, the fear; but leaned into his warmth and "
            "pretended, for a moment, the world was not ending."
        ),
        open_plots=(
            "Secret romance discovered; anxiety gets someone killed."
        ),
    ),
    "Rivenmaw": _sheet(
        appearance=(
            "Medium-built grey wolf with a coat the color of a storm-cloud, darkening to charcoal along spine "
            "and muzzle, pale silver fur on chest and belly like river foam. Fur short and water-slick, often "
            "damp at the paws from constant work along the riverbanks. Striking green eyes; the same sharp "
            "hue as Mossheart's, though his gaze is steady where the Thistlehide scout's flinches. A crescent "
            "of old bite scars rings his right foreleg, a memento from a pike fight he lost as an apprentice. "
            "Moves with loose-limbed confidence on bank and stone, unhurried unless the current turns."
        ),
        personality=(
            "Dry-humored, loyal, outwardly unflappable, privately reckless. A wolf of few words in the den "
            "and many at the border, where news is currency and silence is suspicion. Not cruel, but practical "
            "- Silverrush taught him the river feeds the living, not the sentimental. Excellent hunter and "
            "reliable source of information, but careful distance between himself and the pack. Loyal to duty "
            "and packmates, yet holds a piece of himself back for the secret at the neutral bend. With "
            "Mossheart he softens without meaning to; teasing, patient; the first wolf in seasons who makes "
            "him feel seen rather than merely useful. Knows their meetings could cost everything; keeps coming "
            "anyway, driven by quiet hope that outweighs his pragmatism."
        ),
        backstory=(
            "Born in Silverrush to a hunter mother and Driftwood father who earned his name carrying stones "
            "until Saltmuzzle noticed his nose for fish. Childhood blended pack duty and the shallows; fast "
            "in water, faster with gossip from upstream. Average apprentice, quick wit over brawn; tracking "
            "skill and reading the river's moods earned his place in the hunting corps. Father's philosophy: "
            "worth measured by what you provide; became his own. Three moons ago Mossheart froze at the neutral "
            "bend; Rivenmaw sat, offered half a trout, waited. They meet in secret since, trading patrol "
            "timings and trust. Mossheart spoke of warming water and the strange tooth; Rivenmaw's faith cracked. "
            "He no longer prays for the river's favor but for one enemy wolf's safety. As a pup he glimpsed a "
            "lone trapper on the far bank; pale, strange, out of the river's order; a memory that now feels "
            "like premonition."
        ),
        family_ties="Hunter mother (alive). Driftwood-born father (alive). Secret lover; Mossheart (Thistlehide scout).",
        rp_sample=(
            "Rivenmaw waited at the neutral bend, tail curled over his paws. The Thistlehide side was late: "
            "again. Chill seeped into his bones; the river gurgled alone. When Mossheart slipped from bramble, "
            "fur bristling with burrs, Rivenmaw did not scold. \"You're late,\" he said gently. \"I know. "
            "Patrol.\" Mossheart's single word was heavy with exhaustion. Rivenmaw nuzzled his cheek: \"You're "
            "always hiding,\" a quiet tease. Mossheart's shoulders eased. They shared cold fish, watching the "
            "sun bleed through trees. Rivenmaw wanted to ask about the mill, warming water, the tooth; but "
            "Mossheart was shaking. So he stayed quiet, let the scout lean into him until the trembling stopped. "
            "The river burbled on, indifferent to two wolves caught between duty and something far more dangerous."
        ),
        open_plots=(
            "Border romance exposed; choose pack or Mossheart, or become unwilling informant. Rivalry with "
            "Churn over fishing spots complicated by secrecy. Warming water and the tooth challenge river "
            "packs' Maw-belief."
        ),
    ),
    "Kanami": _sheet(
        appearance=(
            "Delicate snow-white wolf with a rare birth defect that halted physical growth, leaving her "
            "permanently in a small fragile pup body. Pristine white coat beacons in dark Thistlehide woods; "
            "glassy milky-white eyes blind since birth. A dark soot-colored band wraps her lower left hind "
            "leg; superstitious packmates whisper it is the touch of a curse. Often called Kana."
        ),
        personality=(
            "Hyper-vigilant, stubbornly independent, quiet and guarded, omen-burdened, secretly fearless. "
            "An island of quiet resilience; uncanny ghostly movement through territory, fading into brush. "
            "Acutely aware of hatred directed at her; hears elders' mutterings, mothers pulling pups away. "
            "Insular and guarded, with iron-willed survival instinct. Does not beg for pity; silence is her "
            "shield."
        ),
        backstory=(
            "Birth met with horror; blind, white-coated, black leg band. Elders declared her a walking bad "
            "omen; her parents Fernspot and Ashbark abandoned her the day she opened sightless eyes. Survival "
            "viewed as dark magic, not miracle; hid in root systems, hunted tiny creatures by sound. Stopped "
            "growing entirely while littermates became hunters; failed hunts blamed on the White Omen. "
            "Finn'pelt found her on the fringes; elders wanted execution, he refused to kill a pack-born wolf "
            "who feeds herself. She stays on probation, one disaster from bark-burial."
        ),
        family_ties=(
            "Father; Ashbark. Mother; Fernspot. Both alive in pack; both pretend she does not exist. "
            "Finn'pelt allowed her to stay."
        ),
        rp_sample=(
            "The world was snaps, clicks, and rushing air. Kanami sat motionless beneath low ferns, snow-white "
            "fur blending poorly with dark loam, stillness keeping her hidden. Oversized ears twitched, filtering "
            "the alpha's distant howl, focusing on rhythmic heavy steps thirty paces ahead. A hoof on wet slate. "
            "A deer. She lowered her belly, paws pressing into cold moss. She could not see flank or coat, but "
            "knew height by sound angle. She slipped forward, weight shifted so no dry twig snapped beneath her "
            "black-banded hind leg."
        ),
        open_plots=(
            "Seeking a wolf who sees her as more than a curse; execution if pack disaster strikes; audio skills "
            "invaluable in crisis if anyone listens. RP: open to injury, emotional trauma, survival horror, "
            "close-calls; player open to character death if it serves the story."
        ),
    ),
    "Pale'Step": _sheet(
        appearance=(
            "Remarkably tiny, far smaller than peers due to fragile health. Fluffy white coat with light brown "
            "patches; stands out dangerously against the trees. Wide intensely alert bright blue eyes. Neat "
            "pink bows in her fur, groomed constantly to hide small scratches from thorns and brambles."
        ),
        personality=(
            "The High Spirit: resilient, kind, sweet to those she trusts. The Vain Shield: obsessed with pink "
            "bows and fur; if she looks perfect, she can pretend she is not a broken abandoned kit. The Mean "
            "Streak: harsh to wolves who take family or health for granted. The Tsundere: stomps and growls "
            "insults while craving parental warmth she never had. A tiny fiercely bitter ball of fur who lashes "
            "out before the world can hurt her; vanity is her armor."
        ),
        backstory=(
            "Born during a freezing winter storm, weakest of a litter her parents never wanted; wheezing lungs, "
            "weak heart, severe asthma. Before she was weaned, they abandoned her in sharp thistles near the "
            "forest edge. She wandered toward a twoleg campsite during an asthma flare; a twoleg pup tied pink "
            "bows in her fur and fed her scraps before she fled back to the trees. The bows became proof she "
            "could be precious. Foster guardian River'Shroud found her and took responsibility. She secretly "
            "follows the largest warriors, stomps pipeline stakes when un watched, keeps a soothing leaf tucked "
            "behind her bow for flare-ups."
        ),
        family_ties="Birth parents abandoned her. Foster guardian; River'Shroud (antlered hunter).",
        rp_sample=(
            "Safe under a jagged rock overhang, Pale'Step licked mud from her white-and-brown flank, forcing slow "
            "breaths. Down by the kill site, hunters howled joy; must be nice to have lungs for that. She watched "
            "a mother nuzzle a fat healthy pup. Stomping a tiny paw: \"Oh, shut up! Your singing sounds like a "
            "choking crow, you absolute babies!\" She bared small teeth, hackles raised. \"Keep your pathetic "
            "howling away from my clearing!\" She spun with a dramatic huff and retreated into the rocks, heart "
            "hammering, desperately wishing someone would chase after her anyway."
        ),
        open_plots=(
            "River'Shroud's protection tested; pipeline and twoleg encroachment; RP open to injury, emotional "
            "drama, survival close-calls."
        ),
    ),
    "Ashbark": _sheet(
        appearance=(
            "Lean dark-furred wolf; charcoal gray and soot-black, the color of burned wood. Fur thick and "
            "bristly, often tangled with ash from old burn scars on Thistlehide's southern edge. Flat pale "
            "brown eyes; deep scratch across muzzle from a hunting accident years ago. Heavily notched ears; "
            "thin whip-like tail. Moves with tense hunched posture, as if expecting a blow."
        ),
        personality=(
            "Guilty, avoidant, quiet, superstitious, secretly ashamed. Does not talk about Kanami; when wolves "
            "mention the White Omen, he lowers his head and walks away. He carried her to the thistles and left "
            "her there; tells himself the elders said she was cursed, that it was necessary. Dreams of her "
            "every night; not blind in the dreams, milky eyes asking \"Why?\" He has never answered."
        ),
        backstory=(
            "Born in Thistlehide to a long line of hunters; never exceptional, but reliable: fresh-kill, border "
            "guard, alpha's orders. When Kanami was born blind with the black leg band, elders declared her a "
            "curse; Ashbark did not argue. He took her to the thistles and left her. Regrets it every day. "
            "When Finn'pelt allowed her to stay on probation, Ashbark felt relief and terror; avoids her, "
            "cannot look at her, knows she knows who he is."
        ),
        family_ties="Mate; Fernspot (same den, cold and strained; do not speak of Kanami). Daughter; Kanami (abandoned).",
        rp_sample=(
            "Ashbark stood at the edge of the hunting party, dark coat blending with charred trees. He should "
            "have been watching for prey. Instead he watched Kanami alone near the healer's den, white fur "
            "glowing in dusk. She turned her blind face toward him. His heart stopped. \"Ashbark.\" The alpha's "
            "voice; he flinched. \"The deer. South ridge.\" He nodded and fled into the trees, not looking back."
        ),
        open_plots=(
            "Kanami could confront him; he might try to make amends; exile if abandonment becomes public scandal. "
            "Orthodox but fearful; prays for forgiveness he does not think he deserves."
        ),
    ),
    "Lucid": _sheet(
        appearance=(
            "Dark brown wolf whose coat blends into shadowed undergrowth. Fur thick and coarse, matted with burrs "
            "and dried mud. Amber eyes; left marred by milky haze, misshapen pupil from a twoleg beating as a pup; "
            "still tracks movement but cannot see detail. Faded band of scarred hairless skin wraps his right foreleg "
            "from the same humans; kept wrapped in chewed bark strip; not for bleeding, but pressure eases the old ache."
        ),
        personality=(
            "Helpful, self-sacrificing, anxious about failure, protective, quietly stubborn. First to volunteer for "
            "dangerous patrol, last to eat from fresh-kill, sits with injured packmates after the healer leaves. "
            "Terrified of failing others; too slow, too weak, too blind. Not the loudest or most skilled hunter, but "
            "reliable: guards a den until relieved, tracks a lost pup until paws bleed. Packmates sometimes take "
            "advantage of his generosity; he does not seem to notice, or does not care."
        ),
        backstory=(
            "Born south of Thistlehide territory to Twolegs; a hearth-hound pup taken from his mother too early, "
            "kept on a rope, fed scraps, beaten when he growled. They called him vicious for biting back; broke his "
            "leg with an iron pipe and left him in a ditch. A Thistlehide patrol found him three days later "
            "half-starved, leg swollen and black. Healer Thornroot wanted to leave him; a hearth-hound was not a "
            "wolf; but the alpha overruled. A full season to walk without limp; another to hunt: blind eye ruined "
            "depth perception, old leg ached in cold. He learned to ambush from the blind side, drive prey toward "
            "younger hunters. Never seen a twoleg since; dreams of iron, beer, the pipe, laughter; wakes grinding teeth."
        ),
        family_ties="None known. Rescued hearth-hound; some wolves still distrust his past.",
        rp_sample=(
            "Lucid limped toward the clearing center, dark coat blending with evening shadows. He dipped his head to "
            "Finn'pelt. \"The pups are hungry. We should hunt now, before moonhigh.\" Finn'pelt's golden eyes "
            "studied him; Lucid did not flinch. \"Take two hunters. Fresh-kill within a quarter-moon.\" Lucid nodded "
            "and turned; he would find them. Passing Mossgaze sorting roots, she dropped feverfew; he stopped, "
            "picked herbs with his teeth, placed them at her paws, and continued without waiting for thanks."
        ),
        open_plots=(
            "Seeking a hunter or scout who respects his skills despite hearth-hound past; tension with wolves who "
            "distrust him. Leg bandage changed every three days. RP: prefers narrative consequences over dice-less "
            "sparring; dislikes fighting RP until real mechanical combat between dens or animals."
        ),
    ),
    "RiverShroud": _sheet(
        appearance=(
            "Shockingly massive adult she-wolf, towering over most packmates; rare heavy-boned build, brick-like "
            "silhouette. Dense coarse fur patchwork of black, white, and deep slate gray, exceptionally thick in "
            "winter. Defining feature: darkened soot-stained deer antlers lodged atop her head, angled back like a "
            "crown from a solo stag kill; wedged into fur between ears, held by matted hair and dried sap, never "
            "removed. Broad muzzle and heavy chest crisscrossed with deep scars. Unblinking pale gray eyes like "
            "winter river ice."
        ),
        personality=(
            "Impossibly calm, stoic, severely shy and socially anxious, an unfazed anchor, fiercely protective, "
            "silent guardian. Ruined vocal cords; communicates through stares, chest rumbles, dismissive exhales. "
            "Uncomfortable in crowds; uses freezing silent aura to keep distance. Beneath intimidation: deep loyalty "
            "and desperate need to protect. Shows affection through action; standing between danger and loved ones, "
            "silently providing for foster pup Pale'Step."
        ),
        backstory=(
            "Born in Thistlehide. As a pup, brutal throat infection scarred her vocal cords; voice a faint raspy "
            "gravel she despises. Isolated youth poured into physical conditioning and silent border work. Seasons "
            "ago her mother was struck by logging trucks on the thunderpath, pinned under unstable wood; RiverShroud "
            "was not strong enough to lift it and watched her die. Failure drove obsessive strength-building. She "
            "raids pipeline survey camps, tears out white stakes. Solo stag kill near logging lines; snapped its "
            "neck, wedged antlers on that night. Recent pup death from poison baits pushes her to keep Pale'Step "
            "locked in hidden dens. Orthodox but silent; buries meat from every kill beneath oldest roots."
        ),
        family_ties="Foster ward; Pale'Step. Mother deceased (logging accident). Open to mate plots.",
        rp_sample=(
            "Mist hung cold over the Thistlehide border. RiverShroud stood motionless among ferns, antlered "
            "silhouette merging with twisted oak branches, pale gray eyes tracking the treeline. A twig snapped: "
            "she did not flinch; her chest rumbled a warning growl. A young scout emerged, saw her, froze. She "
            "tilted her head. \"G-Greyspire patrol,\" he stammered. \"Three wolves south. Finn'pelt wants you at "
            "the ridge.\" She stared, then padded toward the ridge, massive paws silent on wet earth; a sentinel "
            "carved from stone and grief."
        ),
        open_plots=(
            "Seeking Thistlehide hunters or warriors who communicate with her on borders; extreme protectiveness "
            "over Pale'Step. RP open to physical combat, injuries, dark/mature themes, mate plots."
        ),
    ),
    "Sypha": _sheet(
        appearance=(
            "Lean tan-furred she-wolf, silken coat shifting honey-gold to soft brown in light. Always wears a "
            "flower crown of wild roses and early blossoms; even in leaf-bare. Mismatched eyes: deep sapphire blue "
            "and warm amber-yellow, glowing with unsettling gentleness at dawn and dusk. Immaculately clean despite "
            "digging herb patches; fallen rose petals cling to her pelt. Smells of pine resin, spring lilies, crushed "
            "lavender. At moonrise she seems enchanted; a creature of old stories."
        ),
        personality=(
            "Gentle, polite, charming, quick-witted, profoundly intelligent, playfully mischievous. Lighthearted "
            "jokes and pranks until a wound needs stitching or poison identifying; then focused, sharp, methodical. "
            "Rarely boasts despite skill. Deeply loyal to Thistlehide. Grew up without tragedy; refreshing to some, "
            "unsettling to older wolves. Does not fully understand grief but eager to learn and become the healer "
            "her pack deserves."
        ),
        backstory=(
            "Born in Thistlehide to hunter Brackenpelt and forager Cloverfern. Small, sickly pup with mismatched "
            "eyes some called cursed; grew slowly like a root through stone. Chewed feverfew to cure her own cough "
            "as a pup; saved a litter from rot-lung as a yearling when the healer was away. Trained by elder "
            "Fur-Giver Old Moss; plants, poison, patience. Never met Twolegs up close; gathers herbs in deep woods "
            "far from thunderpaths. Flower crown renewed each morning; rose for healing, lavender for calm, clover "
            "for luck; each bloom carries meaning."
        ),
        family_ties="Father; Brackenpelt (hunter, alive). Mother; Cloverfern (forager, alive). Mentor; Old Moss (elder Fur-Giver).",
        rp_sample=(
            "Sypha trudged through deepening snow, flower crown wilted and frost-kissed. The blizzard swallowed "
            "familiar trails. She prayed in her chest: Maw, I was careless. Let me find the den. A shape loomed: "
            "the old split oak, two tail-lengths from the healer's den. She stumbled inside, shook snow from her fur, "
            "laid herbs to dry, paws trembling. \"Never again. I will mark every path.\" A pup shivered in the corner "
            "with a wounded paw. She smiled, gentle and warm, and knelt to work."
        ),
        open_plots=(
            "Seeking mentor among older healers; rivalry with another healer possible; fear of reptiles exploitable. "
            "Carries dried herbs, rose thorns for stitching, fresh crown each morning."
        ),
    ),
    "Brackenpelt": _sheet(
        appearance=(
            "Broad-shouldered wolf, deep umber and russet-brown coat like bracken ferns in late leaf-drop. Charcoal "
            "along spine and tail tip; paler chest and muzzle with early gray at temples. Short practical fur, "
            "often carrying burrs and pine needles from border runs. Steady hazel-brown eyes. Pale scar across left "
            "shoulder from boar tusk; right ear slightly torn from a thicket chase. Unhurried confidence; knows "
            "territory by scent and memory."
        ),
        personality=(
            "Steady, protective, plain-spoken, quietly proud, uncomfortable with fuss. Brings fresh-kill on schedule, "
            "holds southern border without complaint. Short sentences, action over debate. Softens with mate "
            "Cloverfern; fiercely proud and baffled by daughter Sypha; trusts her stitching hands if not her flower "
            "crowns. Not haunted like many Thistlehide wolves; ordinary hardship is his strength."
        ),
        backstory=(
            "Born in Thistlehide to hunter father and den-keeper mother. Ran southern woods where bracken grows thick. "
            "Average apprentice; boar gored him at three years; healed and returned. Took Cloverfern at four years; "
            "one surviving pup Sypha, sickly and strange-eyed; refused elders' curse talk. Since Sypha became Fur-Giver, "
            "takes extra southern patrols to keep logging lines and pipeline stakes in his sight, not hers."
        ),
        family_ties="Mate; Cloverfern (forager, alive). Daughter; Sypha (Fur-Giver, alive).",
        rp_sample=(
            "Brackenpelt dropped a hare at the fresh-kill pile. Sypha stitched a scout's foreleg, crown askew. \"You "
            "should eat,\" he said. \"You should sit; limping since sunhigh.\" \"I am not limping.\" \"That is your "
            "personality.\" Cloverfern pressed against his flank: \"Let her fuss.\" He watched Sypha tie the stitch, "
            "looked south toward the thunderpath. \"Tomorrow I run the ridge.\" Sypha: \"Take Lucid.\" Cloverfern's "
            "paw found his; three of them standing while the den bustled like weather."
        ),
        open_plots=(
            "Pipeline and logging on patrol stretch; tension if Sypha gathers near southern edge; mentorship of "
            "younger hunter who mistakes steadiness for weakness."
        ),
    ),
    "Cloverfern": _sheet(
        appearance=(
            "Medium she-wolf, soft moss-green and pale clover-white coat, darker fern-shadows along back and haunches. "
            "Thick neatly kept fur threaded with crushed blossoms. Warm leaf-green eyes, crinkled when she smiles. "
            "Earth-brown stained paws; short blunt claws from root work. Smells of wet loam, sweet clover, crushed "
            "plantain."
        ),
        personality=(
            "Warm, practical, observant, gently stubborn, quietly brave. Remembers which pup likes which root, which "
            "elder needs honeycomb, which yarrow blooms first after rain. Holds ground when hunters rush her from herb "
            "beds; corrected Finn'pelt twice without flinching. Worries about Brackenpelt and Sypha; tucks herbs in "
            "their pelts, renews Sypha's crown when she forgets. Chose love when Sypha was born despite fear and "
            "elders' whispers."
        ),
        backstory=(
            "Born in Thistlehide to forager mother and scout father. Learned plants before hunting songs; thank the "
            "Maw, leave a stem behind. Met Brackenpelt on shared patrol after frost killed the clover patch; paired "
            "within the season. Sypha's birth was hard; warmed her four moons, chewed plantain when fever rose. Wept "
            "in Old Moss's den when Sypha saved a litter from rot-lung. Still forages daily; supplies Sypha's satchel, "
            "Brackenpelt's patrol pack, half the nursery. Taught Sypha flower meanings before Old Moss taught poison."
        ),
        family_ties="Mate; Brackenpelt (hunter, alive). Daughter; Sypha (Fur-Giver, alive). Forager mother deceased.",
        rp_sample=(
            "Cloverfern knelt in the clover patch at dawn, yarrow and plantain sorted. Brackenpelt dropped a rabbit "
            "beside her. \"You should be sleeping.\" \"You should be in the nursery.\" She nosed the rabbit at him. "
            "He sighed and ate. She tucked lavender into his patrol wrap. \"She went south again.\" \"I know.\" "
            "Forehead to his shoulder: \"We raised her brave. We cannot punish her for it.\" Brackenpelt's tail brushed "
            "her flank; for a moment the forest felt worth holding."
        ),
        open_plots=(
            "Herb bed damage from logging; lazy forager stealing credit; Sypha's snake fear forcing Cloverfern into "
            "dens her daughter cannot; friendship with Mossgaze or Barkhollow over herb knowledge."
        ),
    ),
    "Skye": _sheet(
        appearance=(
            "Striking black-and-white piebald wolf with dire-wolf build; broad shoulders, thick neck, barrel chest. "
            "Patchy black over white undercoat. Mismatched eyes: deep green and pale blue. Blue ribbons woven at "
            "shoulders, flanks, and tail to hide old twoleg trap and hunter knife scars; not decoration, armor. "
            "Tattered ears; fire-scarred muzzle from puphood. Predator's grace with weariness in her bones."
        ),
        personality=(
            "Deep loyalties and deeper wounds. Loves late nights; quiet, stars, only wolf awake. Fiercely protective "
            "of pups, the weak, anyone she considers hers. Dark humor, laughs at inappropriate moments; nervous tic "
            "from trauma. Restless: paces borders, climbs ridges, swims rivers. Searching for belonging, a mate, a "
            "reason to stop running. Has not found it yet."
        ),
        backstory=(
            "Orphaned when parents died in a twoleg-caused wildfire. Raised alone, stealing from a nearby twoleg cabin "
            "- hunters caught her in traps, beat her, left scars hidden by ribbons. Escaped; wandered years, joining "
            "packs and cast out. True mate and pups; then he left with the pups and the pack threw her out. Alone "
            "until Finn'pelt offered Thistlehide border guard. Formerly Alpha's Guard in Silverrush. Watches for "
            "Greyspire raiders and twoleg monsters; wears ribbons like armor."
        ),
        family_ties="Lost mate and pups (whereabouts unknown). Taken in by Finn'pelt / Thistlehide.",
        rp_sample=(
            "Skye sat on a mossy rock at the Thistlehide border, mismatched eyes scanning the treeline, blue ribbons "
            "fluttering. A twig snapped; teeth bared instantly. A young scout emerged from ferns: \"Skye. Finn'pelt "
            "wants you at the den.\" \"Tell him I'll come when I'm done watching.\" \"He said urgent.\" Skye turned "
            "mismatched eyes on him; he flinched. \"Fine.\" She leaped off the rock. \"But if I miss a Greyspire "
            "raider because of this, I'm eating your share of fresh-kill.\""
        ),
        open_plots=(
            "Lost pups resurfacing; new mate; ribbons removed and scars revealed; trust tested by Thistlehide packmates."
        ),
    ),
    "Finnpelt": _sheet(
        appearance=(
            "Hulking broad-shouldered wolf built like an unyielding stone wall; anchors any clearing he enters. "
            "Incredibly thick ash-black coat slicked with natural river-oils; thorns, brambles, and enemy teeth slide "
            "off like armor. Cold unblinking stare from intense golden eyes; single jagged white scar cutting vertically "
            "through right eye; vision remains flawless."
        ),
        personality=(
            "Vigilant, stoic, strict, protective, emotionally oblivious. Pillar of rugged authority; rules through "
            "crushing reliability, not explosive rage. Pack drops heads when he enters. Strict on duties and borders; "
            "believes every gear must turn perfectly for Thistlehide to survive the Maw. Deep quiet kindness shown "
            "through action: patrols Greyspire border for days so young hunters sleep, leaves choice kill cuts at "
            "nursing dens. Breaks his own heart enforcing dark rules; believes it is the only way to save the pack."
        ),
        backstory=(
            "Born to high-ranking warrior during bitter starvation; weak drag down the whole, Alpha's word is law. "
            "Greyspire border conflict taught hesitation meant a shallow grave. Ambushed in high valley over water "
            "runoff; scar across eye, throat nearly torn; held the line alone until reinforcements. Earned name "
            "Finn'pelt for armor-like resilience. Rite of Broken Canine: shattered previous Alpha's jaw, spared him "
            "as Living Prisoner advisor. A year into rule, observed twoleg iron beasts tear ancient trees; forbade "
            "hunting near human paths. Dismisses dying elder rumors of living burials as feverish delusion."
        ),
        family_ties=(
            "Alpha of Thistlehide. Younger sibling; Mossgaze (forager). Secretly hyper-protective; treats her with "
            "extreme public coldness."
        ),
        rp_sample=(
            "Fog off the high valley tasted of wet slate and old blood. Finn'pelt stood motionless on the precipice, "
            "ash-black fur beaded with condensation, golden eyes scanning Greyspire border. A trembling hunter slid "
            "from briars: \"Alpha; Greyspire patrol shifted west. We lost scent near the rocks.\" Finn'pelt did not "
            "turn. \"Get back to the dens and eat. I will hold the ridge until sun breaks.\" He failed to register "
            "the wolf's terror; only that the border was vulnerable. He stepped into the cold wind, armored coat "
            "absorbing chill, ready to bleed for the dirt he ruled."
        ),
        open_plots=(
            "Needs a mate to cement alpha role. RP OK with death (plot progression), permanent scarring, political "
            "betrayal, psychological horror. NOT OK with unannounced insta-kill without mechanical thread or fair dice."
        ),
    ),
    "Puddlebane": _sheet(
        appearance=(
            "Squat thick-bodied wolf, dark brown and greenish-black coat like a rain-soaked log. Greasy matted fur, "
            "always dripping swamp water. Pale watery yellow eyes; large bulbous nose twitching constantly. Wide "
            "splayed paws for soft mud. Short stubby tail; birth defect. Smells of rotting vegetation and stagnant water."
        ),
        personality=(
            "The only wolf in Mistmoor who smiles; at everyone, even wolves who growl. Not naive; refuses to let the "
            "swamp make her miserable. Joy in rotting logs, glowing fungus, mist through cypress knees. Absent-minded "
            "about pouches and directions; remembers every plant; edible, medicinal, poisonous. Smells death-cap "
            "mushrooms from a tree-length away."
        ),
        backstory=(
            "Born in Mistmoor to Bog-Born mother and unknown father. Sickly pup; rot-lung and fevers until a healer "
            "saved her with poultice from rare fungus on drowned logs. Obsessed with plants since. No mate, no pups. "
            "Mother died two years ago. Lives alone in hollow cypress surrounded by drying herbs and rotting mushrooms. "
            "Content."
        ),
        family_ties="Bog-Born mother (deceased). Father unknown. No mate or pups.",
        rp_sample=(
            "Puddlebane waded through shallows, wide paws squelching. Violet mushrooms glowed under a fallen cypress. "
            "\"Hello, darlings; beautiful today.\" She sniffed: edible. Pulled three, left the rest to spore, tucked "
            "them in her gourd. Dusk stood on a log, golden-brown eyes flat: \"Rotmother wants you.\" \"Tell her I'll "
            "be there when I finish the feverfew.\" She smiled; he did not. \"Now.\" She sighed, dropped the gourd at "
            "his paws. \"Fine. But you're carrying my gourd.\" She walked away, still smiling."
        ),
        open_plots=(
            "Cheerfulness tested by tragedy; discovery of new dangerous plant; absent-mindedness causes pack trouble."
        ),
    ),
    "Mudnose": _sheet(
        appearance=(
            "Stocky thick-furred wolf, brown coat so dark it is almost black. Nose permanently stained dark brown "
            "from years of digging roots and tubers. Small dark eyes nearly invisible in broad face. Thick bushy tail "
            "slaps biting flies. Squat powerful build; made for rooting, not running."
        ),
        personality=(
            "The wolf every pack needs but no one notices. Digs, forages, patches dens; never complains, volunteers, "
            "or seeks attention. A fixture of the swamp like cypress knees and hanging moss. But he watches and "
            "listens. Knows where bodies are buried; digs graves for rot-lung dead, whispers names into soil. "
            "Remembers everyone. The pack's living memory, though no one knows it."
        ),
        backstory=(
            "Born in Mistmoor, never left. Bog-Born parents and grandparents back to the Sundering; native swamp "
            "wolf of Mistmoor's general rank. Content with mud, roots, and slow work keeping dens from collapsing. "
            "As a pup found a Drown-Sick dying in a sinkhole; she grabbed him and whispered a secret name and "
            "prophecy he has never shared. When the moon is right he returns and whispers back."
        ),
        family_ties="Bog-Born lineage (parents and grandparents Mistmoor). Gravedigger and root-digger. No mate or pups.",
        rp_sample=(
            "Mudnose dug; soil soft from last night's rain. He pulled a root, added it to the pile. Not exciting. "
            "The pack would eat. Mirewort stood watching: \"You dug up the grave.\" Mudnose looked at the hole; "
            "where he had buried Sedgepup. His paws had remembered. \"She was medicine. You said that.\" Mirewort sat "
            "beside the hole. \"Yes. She was.\" Two quiet wolves in the mud while the swamp breathed. Mudnose scraped "
            "earth over the root: \"Rest easy, little one.\""
        ),
        open_plots=(
            "Drown-Sick whisper revealed; forced to leave Mistmoor for the first time; secret endangers pack or saves it."
        ),
    ),
    "Reedwhisper": _sheet(
        appearance=(
            "Slender almost delicate wolf, pale tan and soft greenish-gray coat; camouflage among dead cattails and "
            "rotting logs. Short water-repellent fur; smells faintly of mint from chewed leaves masking swamp stench. "
            "Warm honey-brown eyes, disarming and gentle. No visible scars; left ear droops slightly from childhood "
            "nerve damage. Fluid sinuous grace like the swamp itself."
        ),
        personality=(
            "Gentle, perceptive, evasive, deeply loyal to Mistmoor, unexpectedly fierce. The face Mistmoor shows the "
            "world; calm, reasonable, almost sweet. Listens more than speaks; other diplomats underestimate her. "
            "Believes in the patient Maw that digests slowly, turns death into life; wants other packs to understand "
            "Mistmoor is not evil, only different. Temper when provoked by betrayal, cruelty to pups, or desecration "
            "of the dead; voice drops to whisper, honey eyes go flat."
        ),
        backstory=(
            "Born Bog-Born in Mistmoor, only survivor of a litter of five. Mother called her Reed; thin and flexible, "
            "bending without breaking. Grew up watching other packs fear Mistmoor; decided as a pup to change that. "
            "Volunteered as diplomat at three; youngest in Mistmoor history. First mission to Thistlehide over a berry "
            "patch: succeeded with feverfew wrapped in moss and a note for their healers. Thistlehide remembered."
        ),
        family_ties=(
            "Bog-Born family in Mistmoor. Mother called her Reed as a pup; not Gasp, the Drown-Sick who was "
            "Bog-Born Reed before the fall. Mother alive. No mate or pups."
        ),
        rp_sample=(
            "Reedwhisper sat on a fallen log, honey-brown eyes on the Greyspire envoy Sleet, who had shouted about "
            "Mistmoor's poison water. She let him finish, then smiled. \"You are afraid. That is why you shout, you "
            "oak-head.\" Sleet's jaws snapped shut. \"The water is not poisoned; it is different, as mountain air "
            "differs from mist.\" Silence stretched. \"Let us try again. What does Greyspire actually need?\""
        ),
        open_plots=(
            "Temper exposed; must choose between Mistmoor secrets and greater peace; Thistlehide or Greyspire diplomacy tested."
        ),
    ),
    "Mosspup": _sheet(
        appearance=(
            "Small lean pup, pale tan and soft green coat like dead cattails and fresh algae. Short water-repellent "
            "fur, always damp. Warm honey-brown eyes; small dark leaf-shaped spot on nose. Large expressive ears "
            "flatten when thinking. Thin whip-like tail."
        ),
        personality=(
            "Curious, talkative, empathetic, easily frightened, desperately eager to help. Asks questions constantly: "
            "why is the water warm, where does mist come from, what does the Maw taste like. Other pups avoid her; "
            "she does not care. Cries when pups fall or hunters return empty-mouthed. Wants to be a healer like "
            "Mirewort but happier. Collects leaves and mushrooms, presses them between stones to dry."
        ),
        backstory=(
            "Born in Mistmoor. Nearly died of rot-lung at three moons; Mirewort saved her with marsh-mallow root "
            "and feverfew. Follows him since, asking questions, watching his paws. He pretends annoyance; she knows "
            "he is not."
        ),
        family_ties="No named family in lore.",
        rp_sample=(
            "Mosspup crouched beside Mirewort, watching his paws grind dried leaves. She held back questions; he "
            "worked better in silence. \"You want to ask something,\" he said. \"Is it true the Maw talks to you in "
            "dreams?\" His paws paused, then continued. \"Sometimes.\" \"What does it say?\" Long silence. \"It says "
            "I am not alone.\" She did not understand but nodded and filed it away for when she was older."
        ),
        open_plots=(
            "Mirewort's apprentice in training; illness testing her skills; curiosity leading into danger."
        ),
    ),
    "Mudpup": _sheet(
        appearance=(
            "Solid thick-bodied pup, dark brown and greenish-black coat like wet peat. Fur always caked with mud "
            "despite grooming. Pale watery yellow eyes; white chest patch shaped like a paw print. Wide splayed paws "
            "for soft ground. Smells of earth and fungus."
        ),
        personality=(
            "Quiet, observant, stubborn, surprisingly gentle, deeply superstitious. Low mumbling murmur other pups "
            "find creepy. Sits at nursery edge watching mist through cypress knees; not lonely, listening. Hears "
            "Belly-Rip whispers, swamp breathing, faint chewing from nowhere. Leaves rotten meat offerings at the "
            "Belly-Rip; refuses certain moss patterns; sleeps only with glowing fungus beside him."
        ),
        backstory=(
            "Born in Mistmoor. Learned self-sufficiency early. At two moons wandered too close to the Belly-Rip "
            "and fell in; a Drown-Sick pulled him out. Remembers the chewing; not scary, friendly. Different ever "
            "since."
        ),
        family_ties="No named family in lore. Raised in the nursery under Hollowstem.",
        rp_sample=(
            "Mudpup sat at the Belly-Rip edge, wide paws dangling over dark water. Chewing loud today; wet rhythmic "
            "grinding. He closed his eyes and listened. \"Mudpup!\" Hollowstem's voice, sharp with fear. \"Get back!\" "
            "He did not move. \"It's hungry.\" \"I don't care. Get back.\" He sighed, stood, turned from the sinkhole, "
            "walked to the den paws squelching, curled in his nest. The chewing followed him into dreams."
        ),
        open_plots=(
            "Possible Drown-Sick transformation if he falls again; superstitions exploited; might become an oracle."
        ),
    ),
    "Hollowstem": _sheet(
        appearance=(
            "Tall thin wolf, pale tan and greenish-gray coat like dead reeds. Short water-repellent fur, always "
            "damp. Warm honey-brown eyes; long narrow face with perpetually gentle expression. Large ears swivel "
            "constantly listening for pups in trouble. Long flexible paws for digging out stuck pups. Smells of mud "
            "and milk."
        ),
        personality=(
            "Patient, soft-spoken, fiercely protective, quietly clever, deeply maternal. Opposite of Mistmoor's grim "
            "reputation; warm, gentle, endlessly forgiving. Pups love her; adults find her strange. Smiles because "
            "pups need her to; hides sadness. Stood between a rogue and the nursery despite no fighting skill; did "
            "not win, but bought time for guards."
        ),
        backstory=(
            "Born in Mistmoor to Bog-Born mother and Drown-Sick oracle father lost in his own mind; mother raised "
            "her alone. Learned to be soft in a hard world. Mate died of rot-lung before they could have pups; "
            "became den-keeper instead, raising other wolves' pups as her own."
        ),
        family_ties=(
            "Mate deceased (rot-lung). No pups of her own. Nursery caretaker for Mosspup, Mudpup, and others. "
            "Not to be confused with Hollowgaze; the deceased Drown-Sick who fostered Mirewort."
        ),
        rp_sample=(
            "Hollowstem sat in the nursery den, Mudpup curled at her side, Mosspup nestled between her paws. Damp and "
            "dark, but the pups were warm. She hummed a low tuneless lullaby her mother used to sing. Mudpup's ears "
            "twitched: \"The Maw is chewing tonight.\" \"Is it?\" \"Yes. Loud.\" She did not know what to say; kept "
            "humming, hoping the sound would drown out the chewing."
        ),
        open_plots=(
            "Could adopt a pup from another pack; mate's death avenged; might be corrupted by the Belly-Rip."
        ),
    ),
    "Yarrow": _sheet(
        appearance=(
            "Small wiry wolf, pale green-gray and cream coat like the underside of a lily pad. Short slick fur, "
            "always damp. Bright curious green eyes; small white star on forehead. Large floppy ears; short blunt "
            "tail. Quick darting gait, always looking over his shoulder."
        ),
        personality=(
            "Eager, nervous, talkative, loyal, easily startled. Youngest scout in Mistmoor; terrified of failing. "
            "Checks patrol routes twice, reports three times, apologizes constantly. Older wolves find him annoying; "
            "he knows and cannot stop. Shares every patrol detail whether anyone wants it; working on quieter, not "
            "good at it yet."
        ),
        backstory=(
            "Born in Mistmoor. Lost his mother to rot-lung as a pup; grew up under harsh scout expectations to be "
            "better, faster, quieter. Youngest scout in the pack; fears disappointing the wolves who trained him "
            "more than anything else."
        ),
        family_ties="No named family in lore.",
        rp_sample=(
            "Yarrow crept through reeds, heart pounding. Supposed to be quiet; never quiet. A twig snapped; he "
            "froze, listened, nothing. \"You are so loud,\" he whispered to himself. He kept moving, wincing at "
            "every rustle. By the border he had memorized every sound he made. He would apologize to the Rotmother "
            "later. She would sigh. She always sighed."
        ),
        open_plots=(
            "Talkativeness could get someone killed; desperate for approval makes him easy to manipulate; disowned or "
            "demoted if he fails a critical patrol."
        ),
    ),
    "Gasp": _sheet(
        appearance=(
            "Gaunt skeletal wolf, pale gray and greenish-white coat like bleached bones and swamp mist. Patchy thin "
            "fur revealing translucent skin and visible ribs. Milky clouded white eyes; completely blind but seem to "
            "look anyway. Mouth hangs slightly open; soft wet gasping sound every breath. Long bony paws with too "
            "many toes; birth defect. Smells of stagnant water and decay."
        ),
        personality=(
            "Eerie, detached, prophetic, gentle in a strange way, deeply lonely. Fell into the Belly-Rip two years "
            "ago for three days; longer than any other Drown-Sick. Speaks in riddles, answers unasked questions, "
            "no memory before the fall. Answers to Gasp now; barely remembers being Reed, and the name sits wrong "
            "when wolves confuse them with Reedwhisper's childhood nickname. Other wolves avoid them; blind staring, "
            "prophecies that come true, laughter at unheard whispers. Never cruel; never hurt anyone. Wants to be left alone."
        ),
        backstory=(
            "Before the fall, quiet unremarkable Bog-Born wolf named Reed; no special skills, ambitions, or mates. "
            "Slipped on a wet log into the Belly-Rip. Three days floating in the dark, listening to the chewing. "
            "Emerged not Reed but Gasp; oracle ever since."
        ),
        family_ties="Formerly Bog-Born Reed; now Gasp only. No mate. No named family.",
        rp_sample=(
            "Gasp sat at the Belly-Rip edge, blind eyes toward dark water. Chewing loud; wet rhythmic grinding. They "
            "pressed nose to mud and listened. \"Gasp. The Rotmother wants a prophecy.\" They did not turn. \"Tell her "
            "the moon will blink twice before the snow melts.\" \"What does that mean?\" \"It means she will understand "
            "when it happens.\" The messenger left. Gasp stayed, listening, waiting for the next whisper."
        ),
        open_plots=(
            "Prophecies drive major plot; killed or corrupted further; could regain memory of past life as Reed."
        ),
    ),
    "Croaker": _sheet(
        appearance=(
            "Small wiry wolf, barely coyote-sized, pale speckled brown and greenish-gray coat like a leopard frog's "
            "back. Smooth damp fur; bright bulging yellow-green eyes that seem to look different directions. Long "
            "flexible toes splay to grip wet logs. Small upturned nose; nervous twitching tail. Soft croaking sound "
            "in throat when concentrating."
        ),
        personality=(
            "Specialist hunter; frogs, fish, water-rat, occasional snake. Best in Mistmoor at slippery small prey "
            "that feeds pups when large hunts fail. Mocked for size and croaking; does not care. Deeply uncomfortable "
            "with violence; never in a rend, never killed a wolf. Avoids border patrols, hides from Greyspire raiders. "
            "Some call him deerheart; he lets them."
        ),
        backstory=(
            "Runt of a large litter; mother abandoned him at two moons. Survived on frogs and insects, hiding in hollow "
            "logs. Bog-Born found him half-starved and brought him to the den; small-prey hunter ever since. Mimics "
            "frog and bird calls to lure prey; some think magic, he says practice."
        ),
        family_ties="No named family. Abandoned as runt; raised by pack after Bog-Born rescue.",
        rp_sample=(
            "Croaker crouched on a mossy log, speckled coat blending with lichen. A bullfrog called jug-o-rum below; "
            "he called back; same rhythm, same pitch. The frog surfaced confused; his paw shot out, swallowed in one "
            "gulp. He croaked softly, scanning for another. Mudpup crept up behind him: \"Croaker? The Rotmother wants "
            "you at the border.\" Croaker jumped, nearly fell. \"Don't do that. I was hunting.\" \"You were eating "
            "frogs.\" \"That's hunting.\" He hopped off the log. \"Fine. Lead the way. But if I miss a frog because "
            "of you, you're bringing me one from the fresh-kill cache.\""
        ),
        open_plots=(
            "Mimicry mistaken for magic; forced into a fight he cannot win; border duty despite his fear."
        ),
    ),
    "Gristle": _sheet(
        appearance=(
            "Thick-necked broad-chested wolf, coarse wiry fur like dead bracken; brown, gray, faded orange. Fur "
            "crusted with dried blood and mud he does not clean. Flat dark brown eyes deep in a scarred face. Left ear "
            "ragged stump from a boar; muzzle crossed with old bite scars. Missing three claws on right forepaw from "
            "leaf-bare frostbite. Smells of old carrion and swamp gas."
        ),
        personality=(
            "Not subtle; charges, crashes through reeds, splashes shallows, drags prey down with raw strength. Other "
            "hunters despise him for scaring prey; when the pack starves, Gristle brings meat. Foul-mouthed, "
            "ill-tempered; calls pups frog-guts and vole-snouts as endearments. Picks fights with larger wolves, "
            "loses, gets up, does it again. Not smart, not graceful; useful."
        ),
        backstory=(
            "Born a Lowbelly in Greyspire; fled to Mistmoor six years ago half-dead. Does not say why; rumors of "
            "killing a Stoneguard or stealing from fresh-kill. Rotmother took him in; he repaid with meat a hundred "
            "times. Still feels outsider, expects exile, hunts harder than anyone hoping usefulness earns his place."
        ),
        family_ties="No named family. Former Greyspire Lowbelly; exile or flight.",
        rp_sample=(
            "Gristle charged. The boar heard him; sounded like a rockslide; and turned tusks lowered. Gristle did "
            "not slow. A tusk went deep in his shoulder; he clamped jaws on the boar's throat and held through mud "
            "and thrashing. When it collapsed he snarled at hunters watching from safety: \"Fresh-kill. Now help me "
            "drag it, you scat-lickers.\" He limped back bleeding, never asked for the healer."
        ),
        open_plots=(
            "Greyspire past catches up; refusal to ask for help finally kills him; hunted with Croaker causes prey scare-offs."
        ),
    ),
    "Sludge": _sheet(
        appearance=(
            "Low-slung heavy-bodied wolf, coat like stagnant pond water; muddy brown, greenish-gray, black streaked "
            "like oil. Fur permanently matted with wet clay drying into cracked plates. Pale murky yellow eyes deep in "
            "broad flat skull. One hind leg slightly shorter; rolling side-to-side gait on land, nearly silent in "
            "shallow water. Teeth stained dark brown from chewing rotten wood to mask scent."
        ),
        personality=(
            "Does not chase; waits. Motionless in reed beds entire days, submerged to the nose. Unsettling because "
            "he is still: does not twitch or blink, becomes part of the swamp. Every successful hunt a Maw gift, "
            "every failure punishment for impatience. Prays before eating, nose to mud; leaves first bite of every "
            "fresh-kill at the Belly-Rip."
        ),
        backstory=(
            "Born with twisted leg; Bog-Born mother expected him to die. Learned ambush hunting; prey did not hear him "
            "because he could not run; he appeared from the mud. At two years caught in a twoleg trap in shallows; "
            "chewed through paw to escape but lost two toes on left forepaw. Still hunts. Still waits."
        ),
        family_ties="Bog-Born mother (unnamed). No mate.",
        rp_sample=(
            "Sludge had been in the water since moonrise, nose the only thing above green scum. A deer drank three "
            "deer-lengths away; an hour of watching. He moved smooth: pawstep, pause, pawstep. One hare-hop away he "
            "exploded from the water, jaws on throat, weight dragging it into shallows. When it went still he pressed "
            "nose to mud: \"Thank you, Maw. I was patient.\" He dragged fresh-kill back limping, trail of blood and water."
        ),
        open_plots=(
            "Superstition aborts critical hunt; missing toes fail at lunge; contrast with loud Gristle on shared territory."
        ),
    ),
    "Rotteddust": _sheet(
        appearance=(
            "Small hunched wolf, greenish-brown and sickly yellow coat like rotting fungus. Patchy moist fur, always "
            "smells of decay. Pale cloudy amber eyes; permanent tremor in left paw from spider bite nerve damage. "
            "Ragged bitten ears. Slow shuffling gait, often stopping to examine rotting logs or mushroom patches. "
            "Pronouns: ey/em."
        ),
        personality=(
            "Obsessive, brilliant, socially awkward, gentle, morbid. Fascinated by death as decay; never hurt another "
            "wolf. Studies how bodies return to swamp, fungus blooms from rot, Maw digests what it is given. Collects "
            "dead beetles, frogs, mice; dries and stores them in a hollow log. Unsettling to others; ey does not mind."
        ),
        backstory=(
            "Born with a tremor. Bog-Born mother tried to drown em as a pup; too strange, too creepy. Survived by "
            "biting her nose and escaping into reeds. Mirewort found em half-drowned clutching a dead frog, took em back "
            "without questions, began teaching rot-lung herbs. Apprentice ever since. Aromantic asexual."
        ),
        family_ties="Mother (Bog-Born); attempted infanticide; whereabouts unknown. Mentor; Mirewort.",
        rp_sample=(
            "Rotteddust knelt in mud, trembling paw hovering over death-cap mushrooms; white gills, sickly stem, faint "
            "green glow. Beautiful. \"Rotteddust. The patient needs stitching.\" Mirewort's voice. Ey did not look up. "
            "\"The patient can wait. The fungus is blooming.\" \"The patient is bleeding.\" Ey sighed, tucked a sample "
            "into eir gourd, shuffled back. The bleeding wolf would live. The fungus might not bloom until next season."
        ),
        open_plots=(
            "Obsession costs a life; accused of poison-craft; mother returns; Mirewort's patience tested."
        ),
    ),
    "Soot": _sheet(
        appearance=(
            "Small scruffy wolf, charcoal-black coat with white socks on all four paws. Striking mismatched eyes: "
            "blue left, amber right; some call blessing, others curse. Fur always tangled with burrs and mud. Nervous "
            "habit of chewing her tail; tip perpetually bald."
        ),
        personality=(
            "Wants to be a healer like Mirewort; does not care he is strange or that Rotmother suspects him. He saved "
            "her life from rot-lung when her litter died. Clumsy: trips, drops herbs, mixes poultices backward; but "
            "learns. Watches his every move, asks constant questions, practices on carrion when unseen. Will be good "
            "someday; needs time."
        ),
        backstory=(
            "Entire litter died of rot-lung at three moons; only survivor because Mirewort sat three days and nights "
            "dripping tea, willow bark and cold mud against fever. When she woke he said only: \"You owe me.\" She has "
            "followed him since. Mismatched eyes give strange depth vision; trips often but sees light through mist and "
            "insect movements that reveal hidden paths. Mirewort calls it the Maw's second sight."
        ),
        family_ties="Litter deceased (rot-lung). Mentor; Mirewort.",
        rp_sample=(
            "Soot balanced a gourd on her nose, mismatched eyes crossed. Mirewort: \"Don't spill it.\" She spilled it. "
            "\"Sorry! I'll get more-\" She knocked three containers, face-first in stinging nettle. Mirewort sighed, "
            "helped her up, picked nettles from her fur. \"You're hopeless, you little vole-snout.\" \"I know.\" "
            "\"Good. Hopeless wolves live longer.\" Was that encouragement? He did not send her away. That was enough."
        ),
        open_plots=(
            "Must heal someone alone; mismatched eyes reveal something supernatural; attachment to Mirewort tested."
        ),
    ),
    "Dusk": _sheet(
        appearance=(
            "Solid muscular wolf, dark gray coat fading to black on legs and muzzle. Warm almost golden-brown eyes: "
            "the only warm thing about him. Scar across throat from a Greyspire raid; should have killed him. Cannot "
            "howl properly; voice a rasping whisper (Whisper-Jaw). Heavily notched ears; teeth obsessively cleaned "
            "white with abrasive reeds."
        ),
        personality=(
            "Enforcer of Murkvein's will; does not like the role, would rather hunt, but good at it. Watches, reports, "
            "executes; hates himself more each time. Murkvein set him on Mirewort too; Belly-Rip visits, late returns, "
            "whispers to wounds; he files it all and rarely acts, hating that he spies on a wolf pups trust. Fiercely "
            "protective of pups who do not fear him; tells stories in his rasping whisper, voices all characters. No "
            "one else sees this side; he prefers it."
        ),
        backstory=(
            "Born Bog-Born, unknown father. Large quiet pup who did not speak until nearly a year old; listening first. "
            "Voice always a rasp from hidden throat infection as a pup; Greyspire raid scarred his throat further. "
            "Rose to Second; Murkvein's Whisper-Jaw."
        ),
        family_ties="Bog-Born mother (unnamed). Father unknown. Second to Murkvein. Watches Mirewort on her orders.",
        rp_sample=(
            "Dusk crouched in reeds watching Yarrow steal from the storage den a third time. He slid out; the young "
            "scout froze. \"Whisper-Jaw. I… I can explain-\" Dusk raised a paw. Yarrow fell silent. \"You are hungry,\" "
            "Dusk rasped. \"I know. We are all hungry. But you took from the pups.\" Yarrow's eyes filled with tears. "
            "\"I'm sorry. I'm so sorry.\" Dusk studied him, walked away. \"Tomorrow you hunt for the pups and do not "
            "eat until they have; understood, frog-gut?\" Yarrow nodded frantically. Dusk disappeared into mist. He did "
            "not report the theft. Hunger made wolves do terrible things. He was not their judge; just the one who watched."
        ),
        open_plots=(
            "Loyalty tested; secret kindness to pups discovered; guilt over executions; cannot howl in crisis."
        ),
    ),
    "Murkvein": _sheet(
        appearance=(
            "Gaunt long-limbed wolf, coat the color of stagnant water; greenish-gray streaked with darker patches "
            "like oil slicks. Fur sparse and greasy; skin shows through in places, skeletal. Pale luminous green eyes. "
            "No tail; lost to rot-lung necrosis in youth. Sinuous boneless grace that unsettles other wolves. Teeth "
            "yellowed and worn; bite still fast. Ritual cuts on her belly, each a prophecy received."
        ),
        personality=(
            "Ruled Mistmoor five years; longer than any Rotmother in recent memory. Patient: waits for rivals to "
            "mistake, then drowns them in the Belly-Rip. Believes the Maw speaks through her dreams. Not insane, or "
            "if she is, her insanity is useful; predicted the red river, the missing moon chunk, the blind pup in "
            "Thistlehide. Wolves fear her and trust her. She has never been wrong."
        ),
        backstory=(
            "Born to a previous Rotmother who died before naming an heir; the pack tore itself apart in succession wars. "
            "Murkvein survived a year at the Belly-Rip's edge on fungus and warm salt-tinged water. When she emerged "
            "she was changed; tail gone, eyes green, voice a whisper that carried across the swamp. Challenged the "
            "Rotmother and won through certainty, not strength: the Maw had chosen her. Kept the pack through famine, "
            "Twoleg encroachment, and the Belly-Rip's silence. Old now, tired; waiting for one last prophecy that "
            "tells her how to die."
        ),
        family_ties="Daughter of a previous Rotmother (deceased). Second; Dusk (Whisper-Jaw). No mate named.",
        rp_sample=(
            "Murkvein sat at the Belly-Rip edge, green eyes reflecting dark water. The chewing had resumed; slower, "
            "but present. She touched the sinkhole's lip. \"You spoke to him. Mirewort. Things you never told me.\" "
            "The water bubbled; she took it as reply. \"I am not jealous,\" she lied. \"I am curious. Why him? Why not "
            "your faithful daughter?\" No answer; chewing continued, indifferent. She stood, gaunt frame swaying. "
            "\"Fine. Keep your secrets. I have my own.\" She limped toward the dens, missing tail leaving an unbalanced "
            "trail in the mud."
        ),
        open_plots=(
            "Leadership challenged; final prophecy revealed; rivalry with Mirewort over the Maw's favor."
        ),
    ),
    "Eltanin": _sheet(
        appearance=(
            "Rich earthy brown coat with creamy face and crown; deep chocolate back and shoulders "
            "fading to cream behind the shoulders and under the chest. Strong muscular huntress build. "
            "Stern calculating green eyes. Old gash above the left eye from an elk hunt; healed clean, "
            "no sight penalty. Often carries burrs and pine sap from border runs."
        ),
        personality=(
            "Loyal, observant, bold, quiet. Deeply loyal to Thistlehide and fiercely protective of wolves "
            "she holds dear. Bold on the hunt; takes risks to feed the den, not from recklessness. "
            "Reserved; rarely drops her walls. Values dedication and loyalty; little patience for laziness "
            "or liars."
        ),
        backstory=(
            "Born in Thistlehide during a storm; only pup in her litter to survive. Littermates culled "
            "for deformity. Mother died of birth trauma. Raised by the den; spent puphood watching and "
            "stalking small prey instead of playing. Still distant as an adult but socializes when duty "
            "calls. Raised around Maw belief but is agnostic; not hostile, unconvinced, keeps doubt private. "
            "Avoids Twolegs and thunder-sticks; refuses to range near logging scars when shots carry on the wind."
        ),
        family_ties="Mother (hunter, died at her birth). No surviving littermates. Father not in her life.",
        rp_sample=(
            "The nursery hush was wrong. Eltanin had been washing blood from her paws at the creek when "
            "fear-scent hit her: a pup missing from the moss nest. A caretaker burst out, voice cracking. "
            "Eltanin cut her off: \"Left paw. Small. Heading toward the elder-stones.\" She was already "
            "moving into the bracken without waiting for permission. Boldness was doing first what the den "
            "could not afford to do second."
        ),
        open_plots=(
            "Twoleg activity on eastern patrol; private Maw doubt if rot-season worsens; mistaken for cold "
            "because of silence; quietly watches over a caretaker or pup she will not admit to guarding."
        ),
    ),
    "Firepaw": _sheet(
        appearance=(
            "Thick fiery-orange fur streaked with deep brown and rusty red, warm as late leaf-fall. "
            "Strong slim build, broad shoulders, sharp claws, bright amber eyes clouded milky-white; "
            "blind since puphood. Lighter markings ring her paws and back. Pale bones laced along her "
            "torso like a ribcage, curving shoulder to flank, with more along one shoulder; worn as "
            "adornment over her pelt."
        ),
        personality=(
            "Sharp, defensive, impatient with doubt; snaps when wolves treat her blindness as weakness. "
            "Harsh tone protects pride more than true cruelty. With the injured she becomes calm, gentle, "
            "and focused; patience and quiet compassion she rarely shows elsewhere. Razor hearing maps "
            "leaves, snow, and breathing; navigates by scent, sound, and memory. In healing she relies "
            "on touch and smell, making her precise with herbs and dressings."
        ),
        backstory=(
            "Born in Thistlehide without sight; elders whispered she would never hunt. Rejection sharpened "
            "her instead of breaking her. She learned herbs at Sypha's side, proving herself by touch when "
            "others demanded eyes. Still a Medic Apprentice; the den tests her temper as often as her skill. "
            "She refuses pity and takes unnecessary risks to prove she belongs at the healer's shelves."
        ),
        family_ties="Mentor; Sypha (Fur-Giver, alive). Pack; Thistlehide. No mate.",
        rp_sample=(
            "The den was dark and tense. Firepaw listened as Sypha worked on a wolf injured on patrol, "
            "handing dried herbs when asked, nose finding bundles too far for her mentor to reach. "
            "\"Would this work?\" she asked quietly, setting cobweb and yarrow beside Sypha's paws. "
            "\"Yes, perfect. Thank you.\" Sypha's voice was steady. Firepaw nosed the ground where she "
            "had been told to find feverfew, tail twitching until an approving howl made it wag despite "
            "herself. Later, when another wolf limped in whining, anger still hot from being shoved aside, "
            "she put it down anyway: guided him to a quiet nook, lifted the paw, smelled warmth over the "
            "torn pad, and dressed it by touch while Sypha watched. \"You did good,\" Sypha said at last. "
            "\"Maybe you can help after all.\""
        ),
        open_plots=(
            "Book One (*The Blinking*): Sypha's den runs hot in phases 5–11; `/medic action:treat` and "
            "`action:observe` add Firepaw flavor (+standing/mood during border-paranoia phases). "
            "Earn full Medic rank; temper costs allies; rivalry or friendship with Mossgaze over herbs."
        ),
    ),
}




