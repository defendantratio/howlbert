# server channel plan

full proposed structure, reconciling the real current server against everything in `docs/GROWTH_IDEAS.md`. existing channels are kept unless a change is called out; new channels are marked **new**; channels being renamed/repurposed instead of duplicated are marked **repurpose**.

rp finder (pings everyone when someone wants to start an rp) and session discussion (server wide talk about ongoing rp sessions) are both kept as is. they do different jobs than the bot's open-scenes index: rp finder is an active broadcast/ping, the index is a passive, always current list, and session discussion is conversation, not a listing. also different from fic-recs, which is finished/ongoing written scenes, not live session logistics.

---

## server info
- welcome
- goodbye
- rules
- announcements
- questions
- healer handbook
- lore (forum)
- terms
- advertisement

no changes.

## begin your journey
- how to verify
- role selection
- staff introductions
- introductions

no changes.

## ooc space
- general chat
- art sharing
- music
- suggestions
- support tickets
- hiatus notice
- leaving notice
- birthdays
- general voice

changes:
- **bot commands**: moves out, becomes part of the new howlbert category below (repurpose, not deleted; same channel, new home).

## characters
- character rules
- character permissions
- relation search
- qotd
- discuss

no changes.

## roleplay hub
- roleplay rules
- relationship rules
- dice and statistics guide
- examples (for dice and statistics)
- plot updates
- event request
- text rp
- rp finder
- session discussion
- in game roleplay chat
- roleplay voice

no changes. rp finder and session discussion stay; see note above on why they're not replaced by the bot index.

---

## howlbert, new category

pulls bot specific channels out of the general ooc catch all once there's more than one of them, so the bot's presence reads as intentional instead of tacked onto voice/birthdays/etc.

- **bot commands** (repurpose, moved from ooc space, unchanged otherwise)
- **#open-scenes** (**new**): the auto updating index the bot now maintains (`engine/open_scenes_index.py`). point `open_scenes_channel_id` at this channel. a passive list, not a ping; complements rp finder rather than replacing it.
- **#screenshot-showcase** (**new**): dump for dramatic `/vitals` panels, death saves, combat logs. raw material for the wolf of the week spotlight and caption this format (growth ideas sections 40, 43), which currently have nowhere to pull from.
- **#patron** (**new**, from growth ideas section 45): spells out what boosting/supporting actually grants (the bones/mood/standing rewards already auto fire on boost, this channel just makes that visible), plus public recognition: `/patron` status, referral leaderboard, kickstarter backer badge.

only worth breaking out as its own category once #open-scenes and #screenshot-showcase exist alongside bot commands. three related channels in a generic ooc category is exactly the clutter categories are for; two or fewer, leave them in ooc space.

## art, new category, start small

art sharing (staying in ooc space) is the general dump and doesn't get replaced. this wing is a specialization of it; only worth splitting off once art sharing volume actually justifies it. start with the two that have the clearest immediate payoff, add the rest later if it's warranted:

- **#commissions** (forum, **new**): real marketplace channel. where the micro influencer gifting play (section 8) and sofurry/vgen artist discovery (section 37) point once someone's interested, instead of dead ending in dms.
- **#art-of-the-week** (**new**): same mechanism as wolf of the week (already built), applied to art. could reuse the contest judging approach from section 18.

hold for later, add only as volume demands it:
- **#headcanons**: quick lore ideas/interpretations, low effort high frequency.
- **#free-to-use-images**: shared stock/asset folder (borders, dividers, textures).
- **#art-trade** / **#requests**: free exchange boards, distinct from paid commissions.
- **#adopts** (forum): character adoption marketplace.
- **#resources** (forum): tutorials, palettes, brush packs, reference sheets. forum type so posts stay individually findable instead of scrolling.
- **#server-art**: credited server/howlbert specific art (emojis, icons, banners), pinned "how to submit" post.
- **#server-directory**: affiliate/partner server links (sections 3, 13) in one place.
- **#neocities**: persistent link to the neocities site (social media doc section 15).
- partnership rules: a pinned doc/channel topic, not necessarily its own channel. the actual terms for affiliate swaps (section 3).

## also add, no category change needed
- **#fic-recs** (**new**, under roleplay hub or characters): distinct from headcanons (quick ideas) and session discussion (live logistics). actual longer written scenes/stories, the in server counterpart to the ao3 crosspost idea (section 23).

---

## not adding (already covered)
- ~~#new-member-intro~~: **introductions** already exists.
- ~~#suggestions~~: **suggestions** already exists.
- ~~#howlbert~~: folded into **bot commands** above instead of a duplicate channel.

---

## lore forum: starter posts

pulled straight from what's already canon in the code (`config.py`'s `great_packs`/`prestige_tiers`/`rp_locations`, `engine/broken_canine.py`, `engine/character_lore_data.py`, `engine/pack_traits.py`). nothing here is new worldbuilding, it's making existing lore that currently only surfaces piecemeal (a pack trait tooltip here, a prestige tier line there) legible as a single reference. one forum post each, pinned.

### the great maw

> before the four packs, before the paths, there was the maw. not a wolf, not quite a place; the maw is the world itself, living, wounded, and hungry. the swamp is its belly. the river carries its tears. the forest wears its fur. the mountain is its mouth.
>
> the maw does answer prayers, in its way. pray before a hunt and it listens: a wolf who does walks away blessed for the day's hunts, and the maw remembers the gesture as favor, standing earned slowly through prayer, rites, and offerings. it also watches. wolves who break oaths, defile the healer's den, or otherwise cross lines the pack itself can't punish sometimes find the maw's eye doesn't leave them, a weight that isn't a curse exactly, just the sense of being seen by something very old and very patient. every wolf is given a name the world has never carried before; every wolf, eventually, gives it back.

### seven ways to believe in a hungry god

> every wolf picks a belief at registration, and it isn't flavor text; it's how they read every bad sunrise that follows. no belief is "correct." the maw doesn't reward one over another.
>
> - **orthodox**: the maw is what is. wounded, hungry, neither good nor evil. the default faith, and the one that asks the least of a wolf.
> - **orthodox, pragmatic**: the maw's hunger justifies the strong eating the weak. not cruelty; just an honest read of the world as it is.
> - **zealot**: every illness is the maw's question. every cure is the wolf's answer. suffering isn't senseless here, it's a conversation.
> - **doubter**: wants to believe in justice. hasn't seen much of it. still prays anyway, most sunrises.
> - **agnostic**: has seen too much suffering to claim certainty either way, and has made a kind of peace with not knowing.
> - **atheist**: no god would let wolves suffer the way they do. prays to no one, and means it.
> - **heretic**: whispers that the maw doesn't just endure its hunger, it chooses it. and enjoys the watching.
>
> a wolf's belief colors how they pray, not whether prayer works; the maw hears the orthodox and the atheist's silence both the same.

### maw favor

> pray before a hunt and something changes. not the odds, exactly, the pack still comes home empty-pawed sometimes, but the day feels blessed regardless: the kill that follows tastes like it was owed to you.
>
> the maw keeps count. every prayer earns favor, standing with something that doesn't hand out titles or territory, only the sense that it noticed. favor doesn't buy anything a hungry wolf can eat. wolves chase it anyway; the ones who pray every sunrise say it isn't about the hunt bonus at all, it's about being the kind of wolf the maw bothers to remember. the heretics call this vanity. they pray too.
>
> the dead don't get to earn favor. the maw doesn't hear a prayer from a wolf already gone; whatever standing you have when your name is spoken for the last time is the only standing that ever mattered.

### the sundering

> ask any elder where the four packs came from and they'll tell you: before the sundering, there was one pack, and then there wasn't. what actually happened depends who's telling it: a war, a plague, a betrayal at the sundering stone, the maw waking up hungry. no two dens agree, and that's the point. the sundering isn't a date, it's the line every family history gets measured against. "bog born back to the sundering" is about as deep a claim to belonging as a mistmoor wolf can make.
>
> the sundering stone itself still stands, neutral ground no pack claims and no pack quite trusts, kept for gatherings to remember the dead. wolves who trace their line back far enough sometimes carry the weight of it without knowing why.

### the four great packs

> four dens, four paths, one broken pack behind them all.
>
> - **greyspire**: path of the teeth. mountain terrain, the mouth of the world. *"strength is truth. blood is law."* stone endurance runs in greyspire wolves; they shrug off wounds that would fell anyone else.
> - **silverrush**: path of the tears. river terrain, the maw's tears. *"the river flows. the stones weep."* alphas claim the seat through the drown rite, submerging in the weeping deep until the current turns. most come up unchanged. some come up seeing things others can't, and paying for it in how steady they seem afterward.
> - **mistmoor**: path of the belly. swamp terrain, the maw's belly. *"the swamp remembers. the maw chews."* rot doesn't take mistmoor wolves the way it takes everyone else; poison and disease slide off a den that's made peace with decay.
> - **thistlehide**: path of the fur. forest terrain, the maw's fur. *"the forest remembers the names of the dead."* the whisper tree stands at the heart of thistlehide territory; no mechanic, no roll, just a place wolves say the dead still answer if you ask the right question quietly enough.
>
> a fifth path exists for anyone who answers to neither pack nor prophecy: loners walk alone by choice, rogues by exile. the maw watches them just the same.

### the one pack (full history)

> long, long, long, long ago, there was the one pack. they lived in a valley where the mountain's shadow touched the river's edge, and the forest met the swamp. they were many. they were strong. they had a single alpha, chosen by the great maw's sign: a wolf born with a white paw like a moon claw. but the maw is hungry. always hungry.
>
> a sickness came, perhaps the wasting sickness, perhaps something older. the one pack split into four groups: those who fled to the mountains seeking high, clean air; those who sank into the swamp seeking the maw's belly for answers; those who vanished into the forest seeking cover; and those who followed the river seeking tears to match their grief. they never reunited. over generations they forgot each other's languages, though they can still understand enough to trade and fight. they became the four packs.
>
> each pack now guards its territory with teeth and fear. they trade, they fight, they scheme. but beneath it all, they remember, dimly, that they were once one. and the prophecy says they may be one again, when the hunger ends, or begins again.

### pack ranks and roles

> every wolf in a pack has a role. rank sets who eats first, who patrols, and who answers for failure. the hierarchy is brutal, but it's the only thing that keeps a pack alive in a shrinking world.
>
> - **alpha**: absolute authority. their word is law. challenged only through the rite of broken canine.
> - **alpha's guard/advisor**: the alpha's teeth and shadow. they eat before the rest of the pack except the alpha.
> - **medic**: keeper of the green tongue. they alone know the full herb guide. forbidden to mate; a neutral scent lets them treat any wolf without triggering dominance aggression.
> - **forager**: the medic's paws. they collect herbs but don't treat; that's the medic's sacred right.
> - **hunter**: the pack's belly. eats first after the alpha and guard, but regurgitates for pups, elders, and the den bound.
> - **scout**: the pack's eyes. runs the borders, reads scent trails, spies on rival packs.
> - **guard**: defends the den site, the nursery, and the alpha. also handles culling.
> - **caretaker**: watches over pups, juveniles, and the den itself; often wolves who've never had litters of their own.
> - **juvenile**: not yet a full adult. must complete a blooding, a solo kill, to earn an adult role.
> - **pup**: vulnerable. not named until they survive the first moon.
> - **elder**: respected but not sentimental. fed last. if winter is hard, they walk into the snow, the long nap, to spare the pack.
> - **diplomat**: the pack's voice in negotiations with other packs, and the one who gathers secrets from outsiders.
>
> full attribute ranges and role features (commanding howl, green tongue, killer's instinct, and the rest) live on the site's [packs page](https://howlbert.straw.page/packs.html), not repeated here.

### pack law: mating, exile, and scent

> mating is not always romantic. it's political. the alpha chooses which wolves breed to produce strong, healthy pups. refusing a chosen mate is treason, exile, or death. wolves may form personal bonds, called tail twining, but these are informal and can be broken by the alpha at any time.
>
> the worst punishment isn't death, it's exile without a name. the wolf is driven out and the pack never speaks of them again. they become wind eater, a ghost the great maw doesn't remember. physical punishments include biting off a tail (loss of balance), breaking a paw (a limp for life), or slitting the tongue (can no longer howl, the ultimate shame). exiled wolves sometimes gather in cursed packs, broken, starving things that haunt the edges of territory.
>
> wolves identify each other primarily by scent. enemy packs deliberately rub themselves in wild garlic or rotting fish to confuse scent trails. a wolf who smells of another pack without permission is assumed to be a spy, and is executed.

### the naming, and wind that never howled

> a pup isn't a wolf yet. not to the den, and not to the maw. it takes a name to be either.
>
> pups aren't named until they survive the first moon; many don't. the ones who do get a single lick to the forehead from the alpha, and one word, spoken once, in front of the whole den. that word is the pup's name, and until that moment, it didn't exist. the world has never carried it before. this is why the naming ceremony draws every wolf who can walk to watch, even packs that hate each other's borders will occasionally let a naming pass unraided; not mercy, exactly, more a shared understanding that a name being spoken for the first time is the one kind of event the maw is definitely paying attention to.
>
> a pup who dies before that moon isn't mourned by name, because there isn't one yet. the den calls them wind that never howled, and doesn't speak of them again, not out of cruelty but because there's nothing left to speak: no name for the maw to have heard, nothing for the living to keep alive by saying it. this is the same true death that waits at the far end of a long life too, the one every pack fears more than dying: not the body failing, but the last wolf who remembers your name forgetting it, or dying themselves with nobody left to pass it to. bark burial, the weep stone, the moon-howl's bone draw, all of it exists to put off that second, quieter death as long as possible.

### the four packs, in full

> the short version lives above ("the four great packs"). the long version, for anyone building a character:
>
> **greyspire**, path of the teeth. *"strength is truth. blood is law."* rule by strength and timing; the highfang keeps the seat by being cruelest at the right moment and most generous at the next. weakness is culled, loyalty is bought in fresh kill and fear. thick grey and slate coats built for cold; blunt, hierarchical, brutally honest wolves who hold grudges for generations. the miners dig into the mountain below them (the screaming earth), and the crows, a band of scavenger twolegs, are the only humans any pack calls something close to friends.
>
> **silverrush**, path of the tears. *"the river flows. the stones weep."* grief carried like water; silverrush sends its mourners alone to the weep stone to release what they can't say. superstitious, secretive, prone to melancholy; sleek silver grey coats and webbed toes. it's the pack the human world touches first and worst: upstream sewage poisons the river with an incurable wasting sickness, and a dam upstream drowns litters without warning.
>
> **mistmoor**, path of the belly. *"the swamp remembers. the maw chews."* closest to the maw and its belly rip; the rotmother rules by patience, letting rivals mistake themselves into the mud. dark furred, riddling, unsettling to outsiders. practices rot feasts, deliberate carrion eating that builds disease resistance, and keeps the sog grave for its worst offenders. every other pack despises mistmoor, and mistmoor doesn't especially mind.
>
> **thistlehide**, path of the fur. *"the forest remembers the names of the dead."* memory and lineage; the dead aren't gone while the forest still holds their names. tawny, russet coats, pragmatic and blunt but fiercely loyal once bonds form; the pack that howls the most, for war, joy, grief, and the plain pleasure of sound. practices bark burial, and fights a slow war against logging trucks and pipeline surveyors at its borders.
>
> full appearance, culture, hierarchy, and relations detail for each pack lives on the site's [packs page](https://howlbert.straw.page/packs.html).

### the green tongue: restricted herbs

> a medic's knowledge is political power. a medic who withholds a cure can blackmail an alpha. a forager who lies about a rare herb's location can send a rival pack into a death trap.
>
> most herbs are common knowledge among adults: yarrow for bleeding, juniper berries for bellyaches. a handful are restricted, known and handled only by the medic:
>
> - **wolfsbane**: the only plant that can permanently kill a spirit cursed wolf. touching it without ritual cleansing is believed to taint the wolf's soul.
> - **water hemlock**: used for executions. a single leaf in a piece of meat kills in hours; the medic prepares it in secret, then the alpha feeds it to the condemned.
>
> full herb, disease, and dosage detail lives on the site's [illness and herbs page](https://howlbert.straw.page/illness.html), including which restricted herbs actually exist in the game's compendium (wolfsbane and water hemlock among them).

### current tensions

> the world is shrinking, and the packs are fracturing. pick one to hook a scene into, or bring your own:
>
> - **the dam sabotage**: a silverrush wolf is recruiting thistlehide volunteers (explosives knowledge from the mining camp) to destroy the dam. greyspire wants it gone too. mistmoor doesn't care, but they'll send a spy to watch.
> - **the pipeline survey**: thistlehide wolves are raiding the survey camps at night, stealing stakes and leaving mutilated twoleg dolls. the twolegs are responding with poison bait and leg holds.
> - **the rot feast festival**: once a year mistmoor invites one wolf from every other pack to witness a rot feast, a test of diplomacy and stomach. this year greyspire is sending a scarred old warrior instead of a diplomat, and no one knows why.
> - **the mining camp raid**: young greyspire wolves want to raid the miners' supply cache for explosives and guns. the elders forbid it. the beta is secretly supporting them anyway.
> - **the twoleg fishermen**: a silverrush she wolf is pregnant by a loner who eats twoleg food. the pack has to decide what happens to the pups, and to her.

### the pact of the remembered

> thistlehide called the first gathering three generations back, at the sundering stone, to remember the dead together instead of separately. the pitch was simple: once a season, every pack sends someone, unarmed, to speak the names of wolves lost since the last gathering, regardless of which den they died serving. no politics, no standing settled, nothing traded. just names, said out loud, so the maw hears them from more than one throat.
>
> it mostly works. mistmoor sends its rot king or rot queen more often than not, since remembering the dead is close enough to their own faith that it costs them nothing. silverrush comes to grieve properly, somewhere that isn't the weep stone, for once, with company. greyspire's attendance depends entirely on who's holding the seat: grim thinks the whole thing is a trick, thistlehide's way of making greyspire soft in front of witnesses, and sends whichever wolf he trusts least that season, which every other pack has noticed and nobody mentions to his face.
>
> nothing about the pact requires belief in the maw specifically, which is exactly why the doubters and the atheists show up for it as readily as the orthodox. it's the one place in this world where "remember the dead together" doesn't need a shared theology to mean something.

### the watching moon

> the moon is the maw's eye, and lately it hasn't looked away.
>
> nobody agrees on when it started. the drown-sick of mistmoor noticed first, the way they notice most things nobody wants to hear: the moon hangs lower some nights, larger than it has any right to be, and it doesn't feel like it's watching the world in general anymore. it feels like it's watching somebody specific. the tear-drinkers of silverrush started comparing notes with them, which is itself unusual; those two circles don't normally talk. what they've compared is unsettling: both packs have wolves reporting the same dream, more or less, on nights the moon looks wrong. no one will describe it fully. the ones who try stop partway through, every time, like the memory doesn't want to be finished out loud.
>
> the orthodox call it nothing, a trick of atmosphere, cold air bending light. the heretics call it exactly what they've been saying all along: the maw doesn't just endure its hunger, it enjoys the watching, and something has sharpened its attention. the sundering stone's prophecy says the hunger ends, or begins again, when the teeth drink the tears and the fur chokes the belly, whatever that means in practice. most wolves have never taken the prophecy seriously enough to wonder what "in practice" would even look like. lately, fewer wolves are laughing it off.

### a gazetteer of the four territories

every named place a wolf can actually be sent, raided at, or exiled to, pulled straight from the game's own location list, grouped by den. use these as rp settings; several already carry weight from other pinned lore (the weeping deep is where silverrush drowns its alphas, the sog grave is where mistmoor executes its worst).

**greyspire, the mouth of the world**
- **greyspire den**: the den proper, carved into rock.
- **greyspire high ridge**: the pack's highest lookout; sees the whole valley on a clear day.
- **the high pass**: the only way through to the far side of the mountain; narrow, easy to defend, easy to die in.
- **stoneguard watch**: a permanent sentry post over the approach.
- **the ice caves**: cold enough to keep a kill fresh for days; also where wolves go when they don't want to be found.
- **the volcanic vents**: warm ground in a cold place; steam and sulfur, strange for a mountain to have.
- **the narrow passes**: chokepoints along the border; where greyspire fights wars it can't win by numbers.
- **the high ledge**: where the pack leaves the exiled and the frozen; a death sentence dressed as a place name.
- **the miners' camp**: twoleg territory below the treeline; raided only during blizzards, and even then, at a cost.
- **the screaming earth**: the blast zone. dynamite echoes off the peaks for miles; the elders forbid going near it.

**silverrush, the maw's tears**
- **silverrush den**: riverside, built to flood and rebuilt anyway.
- **the river's edge**: where most of the pack's daily business happens; hunting, watching, waiting.
- **the sandbar**: exposed at low water, gone at high; a bad place to be caught mid crossing.
- **the deep channels**: the river at its most dangerous; strong current, stronger currents beneath it.
- **the rapids**: loud, fast, unforgiving; a warrior's proving ground as much as a hazard.
- **the shallows**: where warriors settle disputes; drowning is a common outcome, and everyone knows it going in.
- **the neutral bend**: a stretch of river no pack claims; used for parley.
- **the weeping deep**: the deep, dark pool where silverrush alphas drown themselves to claim the seat. see "the drown rite" below.
- **the weep stone**: a boulder by the river where wolves go to grieve alone. it's forbidden to watch another wolf weep here.
- **the dam**: twoleg built, upstream, changes the water level without warning. blamed for at least three drowned litters.
- **riverbank dens**: the overflow housing when the main den floods, which is often.

**mistmoor, the maw's belly**
- **mistmoor den**: built on the driest ground the swamp has to offer, which isn't saying much.
- **the belly rip**: a tear in the marsh floor; the ground itself sounds hollow here.
- **the rotting mere**: standing water thick with decay; a place, not an accident.
- **the bog**: the swamp at its most literal; slow, wet, patient.
- **glow fungus hollow**: bioluminescent fungus lights this pocket of the swamp after dark; beautiful and toxic in about equal measure.
- **the sick den**: where the pack keeps its wounded and its dying; not the same as the healer's den.
- **the sog grave**: a pit of acidic water that never freezes. wolves who break mistmoor's highest laws are lowered in on a rope of bark and left to dissolve over days. the pack calls it the maw's digestion.
- **the rot feast grounds**: where the pack deliberately eats old carrion to build disease resistance; also where the yearly rot feast festival humiliates a diplomat from every other den.
- **the sinkholes**: ground that isn't ground; step wrong here and you don't come back up easily.
- **the half sunken chapel**: a twoleg structure the swamp is slowly finishing off; the pack avoids it, believing the maw's belly eats memory as well as flesh.
- **the collapsed bridge**: another twoleg ruin, rusting quietly; a landmark more than a destination.
- **the brackish reach**: a stretch of stagnant water and cypress, mapped and named for a wolf who claimed it as their own.

**thistlehide, the maw's fur**
- **thistlehide den**: hidden well enough that the name is half the point.
- **the whisper tree**: the pack's heart; ancestor tree, meeting place, and, some elders swear, a place the dead still answer, if you ask quietly enough.
- **the thistle thicket**: thorn cover thick enough to lose a chase in; the pack's namesake landscape.
- **the sparring grounds**: where juveniles earn their scars the sanctioned way, before the forest gives them scars the other way.
- **the thunderpath**: the logging truck highway; wolves are hit occasionally, and the pack has learned to use that against rivals on purpose.
- **the pipeline stakes**: white survey markers driven through the forest, smelling faintly of a future none of the pack understands yet but all of them distrust.
- **the bark burial trees**: where thistlehide wedges its dead into the crevices of old trunks, believing the forest absorbs what the flesh leaves behind. one elder, in a fever, admitted the woodpeckers sometimes start before the wolf is entirely gone.
- **the high valley**: contested ground with greyspire; a border dispute old enough that neither side remembers exactly how it started.

**contestable territories** (see `default_territories`), held by whichever pack currently controls them, not permanently claimed by any:
- **pine ridge**
- **river crossing**
- **old quarry**
- **mistwood**
- **stoneroot**
- **deep furrow**

**shared and neutral ground**, no pack's alone, all packs' business:
- **the borderlands**: the general no wolf's land between territories.
- **neutral grounds**: where inter pack business happens without weapons drawn.
- **rogue camp**: not one place; scattered camps on the outskirts, wherever the packless can go unnoticed that season.
- **the sundering stone**: carved with the prophecy of the sundering's end; neutral ground no pack dares enter uninvited. see "the sundering," above.
- **the maw's throat**: the caldera, the collapsed scar where all four territories meet; the only ground no one owns and every pack fears.
- **the tongue-stone**: the warm black slab at the caldera's center, inside the maw's throat; sacred, unowned ground, and where the moon-howl happens under the full moon.

**forest cat territory**, not wolf ground, but real rp locations where border scenes and diplomacy actually happen:
- **the oak forest**: thunderclan's core territory; where most of the pack actually lives and hunts, as opposed to sunningrocks below, which is just their edge.
- **sunningrocks**: thunderclan's edge, where oak forest meets open rock; the most common thunderclan border encounter site.
- **snakerocks**: an old rockslide on thunderclan's far border, sharp footing and worse odds; a landmark, not a place either side lingers.
- **the abandoned twoleg nest**: a disused barn thunderclan uses for training; empty enough that a wolf could shelter there too, if desperate.
- **the pine shadows**: shadowclan's pine forest and marsh edge; dark, close cover, favors ambush.
- **the carrionplace**: a twoleg dump at shadowclan's territory edge; foul, scavenged, and the reason shadowclan cats smell the way they do to outsiders.
- **the open moors**: windclan's ground; wide, exposed, no cover for a wolf caught crossing it.
- **the horseplace**: a twoleg farm bordering the moor; windclan trades for herbs here, and it's the one patch of cat territory a wolf could plausibly wander into without meaning to.
- **the river gorge**: riverclan's river, gorge, and reed beds; contested with silverrush more than any other clan border.
- **the twoleg bridge**: a footbridge crossing riverclan's river; the closest thing to neutral ground on that border, since neither side can hold it for long.
- **fourtrees**: neutral hollow where all four clans gather under truce; the closest thing the cats have to the sundering stone, and the only cat ground a wolf diplomat might actually be invited onto.

not added to the server's rp location map itself since it's already crowded; this list exists for lore reference and border/diplomacy scenes only.

### the drown rite

> silverrush doesn't crown an alpha. it drowns one and sees who comes back.
>
> the ritual happens at the weeping deep, the deep pool downriver from the den where the current never quite behaves like current should. a wolf claiming the seat submerges and holds until the water decides to let go. most surface changed only by what the moment cost them. a smaller number surface *marked*, brilliant in ways that unsettle the wolves who weren't there to see it happen, and a little unsteady in the ways that used to come easy. silverrush doesn't consider this a warning. they consider it proof the maw was paying attention.

### the forest cats

> the packs aren't the only claws in this world. forest cat clans hold their own ground at the borders, and where wolf and cat territory overlap, den leadership has learned that raiding a clan out of habit costs more than it's worth. pacts exist: truces, alliances, hunting rights, brokered the slow way, tribute and patience and a diplomat willing to sit still long enough to be believed. cats are obligate carnivores; they'll trade for meat readily and shrug at anything green, which is the first thing every den's diplomat learns the hard way.
>
> greyspire's sleet, silverrush's pebble, and mistmoor's reedwhisper have each sat across from a clan envoy at one border table or another; three very different diplomats, three very different ideas of what "good faith" costs.

### walking the furrow: what prestige actually means

> the pack doesn't hand out reputation. it's earned the slow way: quests finished, hunts survived, legacy carried past your own death into whoever remembers you. the wolves who've walked that whole road long enough have a name for it: the furrow. most wolves live and die without the maw ever learning their name. the ones who don't get remembered differently, not as heroes necessarily, just as wolves the maw's eye lingers on a little longer than most.

---

## more channel ideas: additions, changes, removals

**addition, #in-memoriam** (server info or its own small category). the permadeath/obituary system (`engine/obituary.py`) already writes a real, specific line for every wolf that dies (cause plus a pulled highlight from their own journal), and today that only surfaces once, buried in the rollover crisis "losses" embed. a dedicated channel the bot also posts every obituary line to turns something that currently scrolls past once into a permanent, browsable memorial, which matters more here than in most rp servers, since death is actually permanent. cheap: one more `send()` call at the same point `rollover_announce.py` already fires.

**change, reconcile advertisement with #server-directory.** these aren't quite duplicates but they're close enough to cause confusion once both exist. **advertisement** (server info) reads as outbound: the server's own pinned ad copy for other servers to see. **#server-directory** (art wing, held for later tier) is inbound: the curated list of partner/affiliate servers this server is pointing members toward. worth a one line pinned note in each clarifying which direction it faces, or just merging server directory's job into advertisement's channel topic instead of adding a new channel at all.

**change, consider merging hiatus notice and leaving notice.** both are low traffic, single purpose status announcements with the same audience and the same "post once, mods see it" shape. not urgent, but if ooc space ever feels crowded, this is the safest pair to fold into one **#member-status** channel without losing anything.

**not recommending, per pack text channels.** worth naming since it's the obvious next idea once the great packs lore above exists in one place: a channel per pack (#greyspire, #silverrush, etc.) for in den ooc chat. holding off on this one specifically; it fragments an already small server's ooc conversation four ways, which is the opposite of what a 24 member server needs. the affiliation is already expressed in character through rp channels and pack roles; a fifth ooc chat shaped channel per pack isn't worth the dilution at this size. revisit only if the server genuinely outgrows a single general chat.
