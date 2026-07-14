# server channel plan

full proposed structure, reconciling the real current server against everything in `docs/GROWTH_IDEAS.md`. existing channels are kept unless a change is called out; new channels are marked **new**; channels being renamed/repurposed instead of duplicated are marked **repurpose**.

RP finder (pings everyone when someone wants to start an RP) and session discussion (server wide talk about ongoing RP sessions) are both kept as is. they do different jobs than the bot's open-scenes index: RP finder is an active broadcast/ping, the index is a passive, always current list, and session discussion is conversation, not a listing. also different from fic-recs, which is finished/ongoing written scenes, not live session logistics.

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

## OOC space
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
- plot updates
- event request
- text RP
- RP finder
- session discussion
- in game roleplay chat
- roleplay voice

RP finder and session discussion stay; see note above on why they're not replaced by the bot index. **examples (for dice and statistics)** is removed as its own channel; worked examples now belong inside the dice and statistics guide content itself (see the lore forum section below), not a separate channel.

---

## howlbert, new category

pulls bot specific channels out of the general OOC catch all once there's more than one of them, so the bot's presence reads as intentional instead of tacked onto voice/birthdays/etc.

- **bot commands** (repurpose, moved from OOC space, unchanged otherwise)
- **#open-scenes** (**new**): the auto updating index the bot now maintains (`engine/open_scenes_index.py`). point `open_scenes_channel_id` at this channel. a passive list, not a ping; complements RP finder rather than replacing it.
- **#screenshot-showcase** (**new**): dump for dramatic `/vitals` panels, death saves, combat logs. raw material for the wolf of the week spotlight and caption this format (growth ideas sections 40, 43), which currently have nowhere to pull from.
- **#patron** (**new**, from growth ideas section 45): spells out what boosting/supporting actually grants (the bones/mood/standing rewards already auto fire on boost, this channel just makes that visible), plus public recognition: `/patron` status, referral leaderboard, kickstarter backer badge.

only worth breaking out as its own category once #open-scenes and #screenshot-showcase exist alongside bot commands. three related channels in a generic OOC category is exactly the clutter categories are for; two or fewer, leave them in OOC space.

## art, new category, start small

art sharing (staying in OOC space) is the general dump and doesn't get replaced. this wing is a specialization of it; only worth splitting off once art sharing volume actually justifies it. start with the two that have the clearest immediate payoff, add the rest later if it's warranted:

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
> full attribute ranges and role features (commanding howl, green tongue, killer's instinct, and the rest) live on the site's [packs page](https://howlbert.neocities.org/packs.html), not repeated here.

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
> full appearance, culture, hierarchy, and relations detail for each pack lives on the site's [packs page](https://howlbert.neocities.org/packs.html).

### the green tongue: restricted herbs

> a medic's knowledge is political power. a medic who withholds a cure can blackmail an alpha. a forager who lies about a rare herb's location can send a rival pack into a death trap.
>
> most herbs are common knowledge among adults: yarrow for bleeding, juniper berries for bellyaches. a handful are restricted, known and handled only by the medic:
>
> - **wolfsbane**: the only plant that can permanently kill a spirit cursed wolf. touching it without ritual cleansing is believed to taint the wolf's soul.
> - **water hemlock**: used for executions. a single leaf in a piece of meat kills in hours; the medic prepares it in secret, then the alpha feeds it to the condemned.
>
> full herb, disease, and dosage detail lives on the site's [illness and herbs page](https://howlbert.neocities.org/illness.html), including which restricted herbs actually exist in the game's compendium (wolfsbane and water hemlock among them).

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

every named place a wolf can actually be sent, raided at, or exiled to, pulled straight from the game's own location list, grouped by den. use these as RP settings; several already carry weight from other pinned lore (the weeping deep is where silverrush drowns its alphas, the sog grave is where mistmoor executes its worst).

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

**forest cat territory**, not wolf ground, but real RP locations where border scenes and diplomacy actually happen:
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

not added to the server's RP location map itself since it's already crowded; this list exists for lore reference and border/diplomacy scenes only.

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

## healer handbook: full herb compendium & treatment flows

everything below is pulled straight from the game's actual data (`herbs_compendium.py`'s `HERBS` dict and `herbs.py`'s `INJURIES` dict), not condensed or reinterpreted; this is what `/herbs action:guide` and `/medic action:treat` actually check against. meant to live in the **healer handbook** channel (server info), since that's the one channel already scoped for exactly this.

### how treatment actually works, mechanically

1. **forage**: `/bones action:forage` pulls from the territory's herb table at a DC set by rarity (common **8**, uncommon **12**, rare **15**, very rare **20**), modified by season. restricted herbs (poisons) don't show up on a normal forage roll.
2. **prepare**: `/herbs action:prepare herb:<inventory herb>` turns a raw herb into a usable form; prep method depends on the herb (dry, poultice, raw, tea, gargle, sweeten, ointment, sap, pelt rub, cooked, simmered in milk). most herbs only work prepared one specific way, and the wrong method isn't just wasteful, it can genuinely hurt the patient: eating something meant to stay external, or pressing a toxic herb straight onto an open wound, can deal real HP damage on the spot (a con save can avoid it, and a skilled preparer halves the odds it happens at all, but it's a live risk, not flavor text).
3. **treat**: `/medic action:treat herb:<prepared herb>` applies it to a patient (self or packmate) against whatever injury or disease is active. field dressing (cobwebs) and wound wash (dock/horsetail) exist as lighter, faster options for the two most common battlefield injuries; deep gash and infected wound.
4. **the harder injuries need a real medicine check, not just the right herb**: infected wound (DC 14), festering wound (DC 15), snake venom (DC 14), sun-sick (DC 12), wrenched joint (DC 15), blood-within (DC 15), and thorn-stuck (DC 10) only clear on a successful medicine check against their listed DC; fail it and the herb doesn't consume, nothing happens, try again. every other injury still just clears the moment the right herb is applied, no roll.
5. **surgery**: anything marked "surgery only" below (bruised lung, snapped sinew, torn gristle, and a few others) can't be herb-cured at all; it needs `/medic action:surgery procedure:<stitch|set_bone|extract|amputate>`, usually with a medicine check, sometimes with a helper for advantage.
6. **restricted herbs**: wolfsbane and water hemlock are medic-only by lore and by mechanic; every other poison in the table below exists purely as a hazard (accidental ingestion, execution, hunting cats) with no legitimate treatment use.

### the healer's code

not a mechanic, an in-world ethic every medic character should actually carry, drawn from what the pack roles and restricted-herb rules already imply about the role:

- **the green tongue is a sacred right, not a convenience.** a forager collects; only the medic treats. a forager who treats anyway is overstepping a real boundary in-world, not just skipping a formality.
- **neutrality is the job.** medics are forbidden to mate specifically so their scent stays neutral enough to treat any wolf in the den without triggering dominance aggression; a medic who breaks that neutrality is breaking the thing that lets them do the job at all.
- **restricted herbs are restricted for a reason.** wolfsbane and water hemlock sit outside normal treatment entirely; a medic character who hands them to an untrained wolf, or uses them outside their real purpose (spirit-curse removal, execution), is writing a serious plot event, not a routine one.
- **knowledge is power, and medics know it.** a medic who withholds a cure, or a forager who lies about where a rare herb grows, is playing with real leverage over an alpha or a rival den; that's intended as a plot hook, not an exploit.
- **the wrong dose is a real death.** given the mechanical harm above, an in-world medic who's careless, or cruel, with preparation isn't just failing a roll, they're a wolf other characters have a real reason to fear or distrust.

### injury table

- **broken tooth**: permanent; permanent, no heal time.
- **torn claw**: horsetail poultice · 1 week natural heal; treat herbs: horsetail; 7 days to heal.
- **deep gash**: yarrow + cobwebs (or cattail/oak bark) stops bleeding; treat herbs: yarrow, oak bark, cattail, cobwebs; heal time varies.
- **sprained leg**: comfrey poultice · 1 week rest; treat herbs: comfrey, arnica, tansy; 7 days to heal.
- **fractured rib**: comfrey poultice · 2 weeks rest; treat herbs: comfrey, bindweed, broom; 14 days to heal.
- **skull-ring (concussion)**: skullcap · 1 week sleep; treat herbs: skullcap; 7 days to heal.
- **punctured paw**: heals in 1 week; oak bark binding halves time; treat herbs: oak bark, dock, plantain; 7 days to heal.
- **infected wound**: yarrow or goldenrod poultice; medicine check required (DC 14) for the herb to actually clear it, not just applying it; treat herbs: yarrow, goldenrod, burdock root, wild garlic; heal time varies.
- **torn ear / lost eye**: torn ear heals cosmetically; penalty remains. lost eye: no cure; permanent, no heal time.
- **broken jaw**: broth/milk · comfrey poultice reduces to 2 weeks; treat herbs: comfrey, bindweed, slippery elm; 21 days to heal.
- **spinal injury**: comfrey poultice · bindweed splint · 28 days rest; treat herbs: comfrey, bindweed, broom; 28 days to heal.
- **paralyzed (permanent)**: no cure; lifelong den care; permanent, no heal time.
- **festering wound**: yarrow tea · goldenrod tea · urgent medic care; medicine check required (DC 15); treat herbs: yarrow, goldenrod, burdock root; 7 days to heal.
- **scorched hide (burn)**: cobwebs dressing · 7 days full rest; no herb cure; treat herbs: cobwebs, common mallow; 7 days to heal.
- **bruised lung (pulmonary contusion)**: surgery (set_bone); no herb cure; 14 days to heal.
- **swollen eye**: celandine or feverfew poultice; treat herbs: celandine, feverfew, witch hazel; 5 days to heal.
- **blood loss**: 3 full rests; clears automatically; 3 days to heal.
- **snake venom**: snakeroot poultice may slow progression; feverfew reduces fever; medicine check required (DC 14) for any of the treat herbs to actually clear it. no guaranteed cure; treat herbs: blackberry, snakeroot, sticklewort, adders tongue, feverfew; 5 days to heal.
- **insect sting**: dock leaf or burdock poultice reduces swelling. clears in 3 days; treat herbs: dock, burdock root, blackberry, jewelweed; 3 days to heal.
- **lost eye**: permanent; permanent, no heal time.
- **dead-limb (nerve damage)**: no cure; can compensate with training; permanent, no heal time.
- **caved-chest (flail chest)**: surgery only; 6 weeks rest; comfrey poultice for pain; treat herbs: comfrey, willow bark; 42 days to heal.
- **sun-sick (heatstroke)**: cool water; rest; feverfew; medicine check required (DC 12); can be fatal if untreated; treat herbs: feverfew, watermint, willow bark; 3 days to heal.
- **chill-bite (hypothermia)**: warmth; honey; rest; avoid extreme cold; treat herbs: honey, pine bark; 3 days to heal.
- **smoke-lung (smoke inhalation)**: mullein or lungwort tea; rest; avoid smoke; treat herbs: mullein, lungwort, pine needle; 7 days to heal.
- **snapped sinew (ruptured tendon)**: surgery only; long healing (6 weeks); no herb cure; 42 days to heal.
- **wrenched joint (dislocated shoulder)**: pop back in (medicine DC 15); then rest 1-2 weeks; willow bark for pain; treat herbs: willow bark, comfrey, arnica; 10 days to heal.
- **mangled paw (crushed paw)**: comfrey poultice + splint; 3 weeks rest; dock leaf for swelling; treat herbs: comfrey, dock, plantain, bindweed; 21 days to heal.
- **blood-within (internal bleeding)**: shepherd's purse + yarrow tea; requires medicine check DC 15 to stop; otherwise fatal; treat herbs: shepherds purse, yarrow, horsetail; 5 days to heal.
- **pus-pocket (abscess)**: hot compress + burdock root; lance with stick (surgery); treat herbs: burdock root, dock, wild garlic; 5 days to heal.
- **pulled sinew (muscle strain)**: rest 3 days; comfrey poultice reduces to 1 day; treat herbs: comfrey, arnica, meadowsweet; 3 days to heal.
- **torn gristle (ligament tear)**: surgery needed; long recovery (4 weeks); no simple herb cure; 28 days to heal.
- **thorn-stuck (splinter)**: remove with stick (survival/medicine DC 10); then dock leaf; treat herbs: dock, plantain; 2 days to heal.

### the full herb compendium

sorted by rarity, common first. "pack" is the territory it's native to; "any territory" means it isn't pack-locked. "cures" lists the injuries/diseases it treats; restricted (poison) herbs have no cures, they're hazards, not medicine.

**common**
- **adder's tongue** (any territory): reroll failed poison save with advantage if within 1 minute of sting. cures: sting-swell (mild poison), swollen eye, deep gash, shaking-sickness (seizure disorder). preparation: fresh roots or leaves simmered in milk; chewed into a poultice for eyes and wounds.
- **beech leaves** (any territory): carry herbs. cures: leaf-bare cough (cold/chill), infected wound. preparation: leaves used in teas; ointments for burns, sores, and ulcers.
- **bindweed vines** (any territory): relieves gut complaints and urinary problems; the tough vines themselves lash splints to broken bones, speeding supported breaks (bone healing minus 7 days), the actual splint-binding herb in the compendium. cures: the refusing (eating distress), water-scorch (urinary infection), shiver-fever (influenza), gut-stone (constipation). preparation: leaves may be cooked to reduce oxalic acid; seeds used as purgative.
- **blackberry (bramble)** (any territory): soothes insect stings and ends non-magical venom. cures: gut-run (diarrhea), the refusing (eating distress), infected wound, sting-swell (mild poison). preparation: leaves chewed into a poultice and applied to stings; root bark eaten raw or as tea.
- **boneset** (mistmoor): reroll failed disease save with advantage. cures: shiver-fever (influenza), leaf-bare cough (cold/chill). preparation: leaves and flowers eaten fresh or dried.
- **borage** (any territory): extra milk for nursing mother. cures: shiver-fever (influenza), leaf-bare cough (cold/chill), the skitters (anxiety), the low-spirit (depression). preparation: must be used fresh, never dried; leaves and roots eaten raw.
- **broom** (any territory): anti-inflammatory poultice for the bruising and sprains that come with a fracture; doesn't do the physical splinting itself, that's bindweed's job, broom just treats the injury alongside it. cures: fractured rib, sprained leg, broken jaw. preparation: chewed and applied as poultice.
- **burdock root** (any territory): poultice draws infection from bites and open wounds after 24h rest. cures: infected wound, deep gash, scratch-bare (mange), growth-sickness (cancer). preparation: root dug up, washed, and chewed into a poultice for bites and wounds.
- **burnet** (any territory): leaf applied to cuts staunches bleeding. cures: sprained leg, gut-run (diarrhea), deep gash. preparation: applied as poultice; root used as astringent tea.
- **catchweed burrs** (any territory): burrs hold poultices in place. cures: water-scorch (urinary infection). preparation: burrs attached to pelt over poultices.
- **cattail** (silverrush, mistmoor): pollen is hemostatic. cures: deep gash, sprained leg, infected wound. preparation: pollen eaten raw; young shoots and rhizomes eaten cooked.
- **celandine** (any territory): removes eye swelling and restores eyesight within 1 hour. cures: swollen eye, partial blindness, yellow-eye (hepatitis), leaf-bare cough (cold/chill), belly-grind (gallstones). preparation: leaves chewed into a poultice and held gently against the eye.
- **chamomile** (any territory): advantage on wisdom saves vs fear for 1 hour. cures: the skitters (anxiety), the sleepless (insomnia), the refusing (eating distress), shiver-fever (influenza), the hollowing (grief), fever-wander (delirium). preparation: leaves and flowers eaten raw; tea made from flowers.
- **chervil** (any territory): removes nausea. cures: infected wound, gut-run (diarrhea), redscratch, the refusing (eating distress), wasting-sickness (chronic wasting). preparation: poultice applied to wounds or eaten raw for bellyache.
- **chickweed** (any territory): ends green-cough (3 doses per 24 hours). cures: green-cough (mild respiratory), leaf-bare cough (cold/chill), infected wound. preparation: used as tea or poultice application.
- **chicory** (any territory): settles gut upset, diarrhea, and eating distress. cures: gut-run (diarrhea), the refusing (eating distress), yellow-eye (hepatitis). preparation: root eaten raw or as tea.
- **cobnuts** (any territory): +1 stealth when approaching prey; restores +8 satiety on patrol. no listed cures; utility use. preparation: eaten raw or cooked.
- **cobwebs** (any territory): auto-stabilize dying wolf. cures: dying, deep gash, shaking-sickness (seizure disorder), scorched hide. preparation: gathered in a swath and applied to bleeding wound; wrapped around injury.
- **coltsfoot** (any territory): ends green-cough after 1 dose. cures: green-cough (mild respiratory), leaf-bare cough (cold/chill), punctured paw, chestbind (asthma). preparation: leaves eaten raw for shortness of breath.
- **common mallow** (any territory): poultice for scraped and scorched pads. cures: punctured paw, leaf-bare cough (cold/chill), the refusing (eating distress), scorched hide, chestbind (asthma). preparation: tea, poultice.
- **coneflower (echinacea)** (greyspire): advantage on infection saves within 1h of injury. cures: infected wound, shiver-fever (influenza), leaf-bare cough (cold/chill). preparation: tea, or root dried for later use.
- **daisy** (any territory): ignore arthritis and joint pain penalties for 8 hours. cures: deep gash, leaf-bare cough (cold/chill), infected wound, the sleepless (insomnia), sprained leg, joint-rot (arthritis). preparation: tea, poultice.
- **dandelion** (any territory): soothes stings and flushes fever. cures: the refusing (eating distress), yellow-eye (hepatitis), shiver-fever (influenza), foulwater rot (leptospirosis), sting-swell (mild poison). preparation: leaves and stems eaten; root made into tea.
- **dock** (any territory): restores cracked paw pads after 1 day rest. cures: leaf-bare cough (cold/chill), yellow-eye (hepatitis), gut-run (diarrhea), punctured paw, infected wound. preparation: leaf chewed into a poultice and applied to scratches; root dug and steeped into a tea for liver and gut complaints.
- **douglas' sagewort** (greyspire): prevents infection 24h. cures: leaf-burn (poison ivy), infected wound, sting-swell (mild poison). preparation: leaves and stems dried, used as rub or tea.
- **elder (external)** (any territory, poison): treats sprains. cures: sprained leg. preparation: bark and leaf prepared as a poultice; requires careful preparation, unripe or uncooked parts are toxic.
- **fennel** (any territory): extra day without food before exhaustion sets in. cures: the refusing (eating distress), leaf-bare cough (cold/chill), gutknot (bloat), infected wound. preparation: seeds eaten fresh, or steeped as tea.
- **feverfew** (any territory): reduces inflammation and fever. cures: shiver-fever (influenza), redscratch, the spotting (pox), rot-lung (swamp fever), milk-fever (eclampsia), swollen eye, leaf-bare cough (cold/chill). preparation: fresh or dried leaf eaten.
- **garden mint** (any territory): ends nausea in minutes. cures: the refusing (eating distress), gut-run (diarrhea), gutknot (bloat), infected wound. preparation: tea, eaten raw.
- **garlic mustard** (any territory): rub through pelt to drive off fleas. cures: leaf-bare cough (cold/chill), infected wound, sting-swell (mild poison), burrfever (lyme), belly-worm (worms). preparation: young leaves eaten; poultice; rubbed through the pelt for fleas.
- **heather** (any territory): sweetens bitter herb mixtures. cures: gut-run (diarrhea), leaf-bare cough (cold/chill), the skitters (anxiety). preparation: tender tops and flowers made into tea; roots in milk for diarrhea.
- **honey** (any territory): feeds starving pups (+10 satiety, -1 exhaustion). cures: leaf-bare cough (cold/chill), deep gash. preparation: eaten raw, or used to sweeten teas and gargles.
- **horsetail** (any territory): +3 medicine to stabilize dying. cures: deep gash, torn claw, punctured paw, water-scorch (urinary infection). preparation: tea or poultice.
- **ivy vines** (any territory): preserves dried herbs 2 extra weeks; not a splinting herb, its actual use is respiratory (thins chest mucus, opens airways) plus a minor-skin-irritation poultice. cures: leaf-bare cough (cold/chill), shiver-fever (influenza), chestbind (asthma). preparation: leaves steeped as tea, often sweetened with honey, or crushed and applied as poultice.
- **jewelweed** (any territory): sap neutralizes poison-ivy rash. cures: leaf-burn (poison ivy), sting-swell (mild poison), yellow-eye (hepatitis), gut-run (diarrhea). preparation: sap applied directly; tea.
- **juniper berries** (any territory): neutralizes mild poison. cures: sting-swell (mild poison), gut-run (diarrhea), water-scorch (urinary infection), infected wound. preparation: berries eaten raw; leaves used as tea for respiratory issues.
- **knotgrass** (any territory): cures diarrhea. cures: gut-run (diarrhea), the itch (fleas), leaf-bare cough (cold/chill), water-scorch (urinary infection), belly-worm (worms). preparation: eaten fresh several times a day; tea for kidney and bladder conditions.
- **labrador tea** (any territory): ends wheezing for 4 hours. cures: leaf-bare cough (cold/chill), gut-run (diarrhea), chestbind (asthma). preparation: dried leaves brewed as tea; maximum one cup per day.
- **lamb's ear** (any territory): fuzzy leaves pressed on wounds stop bleeding and soothe insect stings. cures: infected wound, sting-swell (mild poison). preparation: fuzzy leaves applied directly to skin as a poultice.
- **lavender** (any territory): cures fever and chills. cures: shiver-fever (influenza), the skitters (anxiety), the sleepless (insomnia), the hollowing (grief), the screaming-sleep (night terrors). preparation: leaves or flowers eaten raw; used as rub or tea.
- **lizard's tail** (mistmoor): removes 1 fever exhaustion. cures: shiver-fever (influenza), water-scorch (urinary infection). preparation: dried roots eaten raw; steeped as tea.
- **mountain ash (rowan)** (any territory): bitter bark eases fever and weeping-scale, soothes liver complaints. cures: shiver-fever (influenza), weeping-scale (distemper), yellow-eye (hepatitis). preparation: bark as tea; berries require caution.
- **oak bark** (thistlehide): stops bleeding. cures: deep gash, infected wound, gut-run (diarrhea). preparation: tea for diarrhea; chewed as poultice for wounds.
- **oxeye daisy** (any territory): eases joint ache and sprains. cures: sprained leg, leaf-bare cough (cold/chill), shiver-fever (influenza), yellow-eye (hepatitis), water-scorch (urinary infection). preparation: young leaves eaten raw; tea.
- **parsley** (any territory): ends lactation within 6 hours. cures: milk-fever (eclampsia), wasting-sickness (chronic wasting), the refusing (eating distress), water-scorch (urinary infection). preparation: eaten raw or as tea.
- **pine bark** (greyspire): inner bark eases leaf-bare cough and frost-nipped paws. cures: leaf-bare cough (cold/chill), punctured paw, chestbind (asthma). preparation: inner bark eaten raw or steeped as tea.
- **pine needles** (greyspire): tea ends coughing after 1 dose. cures: green-cough (mild respiratory), leaf-bare cough (cold/chill), water-scorch (urinary infection), chestbind (asthma). preparation: tea from fresh or dried needles.
- **poppy seeds** (any territory): sedative and pain relief. cures: the sleepless (insomnia), the skitters (anxiety), heart-shock (emotional shock), the hollowing (grief). preparation: seeds, petals, and leaves eaten raw; petals and leaves used for sleep.
- **purple loosestrife** (silverrush): staunches bleeding on stitched wounds. cures: deep gash, gut-run (diarrhea), infected wound. preparation: tea; flowering tops dried.
- **purslane** (any territory): fleshy leaves hold ditch-water. cures: the refusing (eating distress), the skitters (anxiety). preparation: fleshy leaves eaten raw.
- **ragweed** (any territory): 3 leaves removes 1 exhaustion. cures: leaf-bare cough (cold/chill), yellow-eye (hepatitis). preparation: tea; caution, highly allergenic.
- **ragwort** (any territory): elder hunts at full speed for 1 day. cures: sprained leg. preparation: avoid; no safe preparation.
- **raspberry leaves** (any territory): advantage on birth hemorrhage saves. cures: gut-run (diarrhea), leaf-bare cough (cold/chill). preparation: tea.
- **rosemary** (any territory): hides death-scent at burial. cures: the hollowing (grief), the long-forgetting (dementia), the fraying (chronic stress), the skitters (anxiety), the fixing (obsession). preparation: eaten fresh, or steeped as tea.
- **rush stalks** (mistmoor, silverrush): hard stalks bind broken bones. cures: fractured rib, broken jaw, sprained leg. preparation: stalks steeped as tea for diuretic use; also used as splint material.
- **saffron** (any territory): auto-stabilize postpartum hemorrhage. cures: dying, milk-fever (eclampsia), leaf-bare cough (cold/chill), the skitters (anxiety), the hollowing (grief). preparation: petals eaten fresh or dried.
- **sage** (any territory): soothes sore throat. cures: leaf-bare cough (cold/chill), the refusing (eating distress), gut-run (diarrhea), infected wound. preparation: tea, gargle, eaten raw.
- **shepherd's purse** (any territory): hemostatic. cures: deep gash, internal bleeding. preparation: tea, or fresh leaves eaten raw.
- **skunk cabbage** (any territory): treats severe cough and blackcough. cures: green-cough (mild respiratory), leaf-bare cough (cold/chill), chestbind (asthma). preparation: dried root eaten raw or steeped as tea; dried form only.
- **snakeroot** (any territory): advantage vs snake venom saves. cures: the skitters (anxiety), the sleepless (insomnia), sting-swell (mild poison). preparation: dried root eaten raw, in small amounts.
- **sorrel** (any territory): stops heavy bleeding from deep wounds. cures: deep gash, leaf-bare cough (cold/chill), sprained leg, water-scorch (urinary infection), the refusing (eating distress). preparation: leaves used fresh or cooked.
- **sticklewort** (any territory): neutralizes snake venom. cures: gut-run (diarrhea), leaf-bare cough (cold/chill), infected wound, sting-swell (mild poison), yellow-eye (hepatitis). preparation: tea, gargle, poultice.
- **stinging nettle** (any territory): with comfrey -1 broken bone healing day. cures: fractured rib, sprained leg, the itch (fleas), water-scorch (urinary infection), burrfever (lyme), joint-rot (arthritis). preparation: dried or cooked form safe; tea, or eaten cooked.
- **straight stick** (any territory): thin twig for wolves in pain to bite during deep treatment. no listed cures; utility use. preparation: gathered from any woody area.
- **sweet sedge** (any territory): ends mild gut infection in 1 day. cures: gut-run (diarrhea), shaking-sickness (seizure disorder), the refusing (eating distress), gutknot (bloat). preparation: avoid; no safe preparation.
- **tansy** (any territory): halves sprain recovery time. cures: sprained leg, the itch (fleas), leaf-bare cough (cold/chill), belly-worm (worms). preparation: leaves, flowers, and stems eaten raw together; extreme caution.
- **thyme** (any territory): ends minor pain for 2 hours. cures: the skitters (anxiety), the sleepless (insomnia), leaf-bare cough (cold/chill), chestbind (asthma). preparation: eaten raw; tea.
- **tormentil** (any territory): +2 medicine for any injury. cures: gut-run (diarrhea), leaf-bare cough (cold/chill), infected wound. preparation: tea, or root chewed into a poultice and applied to the skin.
- **valerian** (any territory): calms shock. cures: the skitters (anxiety), the sleepless (insomnia), feral shift, the refusing (eating distress), the hollowing (grief), heart-shock (emotional shock). preparation: root eaten raw, or steeped as tea.
- **watermint** (any territory): removes nausea in 10 minutes. cures: leaf-bare cough (cold/chill), infected wound, gut-run (diarrhea), the refusing (eating distress), yellow-eye (hepatitis), gutknot (bloat), foulwater rot (leptospirosis). preparation: leaves eaten raw; tea from fresh or dried leaves.
- **wild cherry bark** (any territory): stops coughing for 2 hours, even blackcough. cures: green-cough (mild respiratory), leaf-bare cough (cold/chill), gut-run (diarrhea), the skitters (anxiety). preparation: bark eaten raw or steeped as tea; short-term use only.
- **wild garlic** (any territory): advantage vs vermin disease 24h. cures: leaf-bare cough (cold/chill), the itch (fleas), infected wound, yellow-eye (hepatitis), foulwater rot (leptospirosis). preparation: eaten raw or cooked; tea.
- **willow bark** (mistmoor, silverrush): pain relief 1 sunrise. cures: shiver-fever (influenza), sprained leg, fractured rib, burrfever (lyme), joint-rot (arthritis). preparation: bark eaten raw in small amounts for pain; steeped as tea.
- **witch hazel** (any territory): astringent and hemostatic. cures: swollen eye, infected wound, leaf-burn (poison ivy), leaf-bare cough (cold/chill), sting-swell (mild poison). preparation: bark or leaves chewed into a poultice and applied to the skin; tea with caution for internal use.
- **wood sorrel** (any territory): steadies a queasy stomach. cures: shiver-fever (influenza), the refusing (eating distress). preparation: small amounts as tea; poultice.
- **yarrow** (any territory): +2 medicine to stabilize. cures: deep gash, infected wound, shaking-sickness (seizure disorder), torn claw, gut-run (diarrhea). preparation: tea, or leaves chewed into a poultice and applied to wounds.

**uncommon**
- **alder bark** (mistmoor): chewed and applied to wounds. cures: root-rot (tooth infection), infected wound, gut-run (diarrhea). preparation: bark chewed directly or applied as poultice; gargled for tooth and gum pain.
- **catmint tea** (any territory): cures severe blackcough (2 doses per 24 hours). cures: green-cough (mild respiratory), leaf-bare cough (cold/chill), the skitters (anxiety), the sleepless (insomnia), the refusing (eating distress), chestbind (asthma). preparation: leaves and flowers for congestion and coughs; tea.
- **comfrey** (thistlehide): poultice heals 1d4 HP on deep wounds. cures: fractured rib, broken jaw, sprained leg, deep gash. preparation: roots chewed into poultice and applied externally.
- **skullcap** (any territory): sedative rest for skull-ring (concussion) recovery. cures: skull-ring (concussion), the long-forgetting (dementia), feral shift, the skitters (anxiety), fever-wander (delirium), the fixing (obsession), den-madness (paranoia), the sleepless (insomnia), the hollowing (grief). preparation: dried herb steeped in water.
- **marsh-mallow root** (mistmoor): soothes rot-lung fever and wheeze. cures: rot-lung (swamp fever), leaf-bare cough (cold/chill), sprained leg, chestbind (asthma). preparation: tea, poultice.
- **meadowsweet** (silverrush): ignore 1 pain exhaustion for 4 hours. cures: sprained leg, gut-run (diarrhea), the refusing (eating distress), shiver-fever (influenza), burrfever (lyme), joint-rot (arthritis). preparation: tea from the flower or dried herb.
- **mugwort** (any territory): rub through pelt to drive off fleas. cures: the itch (fleas), gut-run (diarrhea), the refusing (eating distress). preparation: tea, rubbed through the pelt; use with caution.
- **passionflower** (any territory): eases racing thoughts and insomnia. cures: the skitters (anxiety), the sleepless (insomnia), feral shift. preparation: tea from the dried vine and flower.
- **plantain** (thistlehide): gentle wound remedy. cures: leaf-bare cough (cold/chill), deep gash, punctured paw, torn claw, chestbind (asthma), bronchitis. preparation: tea, or leaves chewed into a poultice.
- **slippery elm** (thistlehide): eat or drink without pain for 8 hours. cures: broken jaw, gut-run (diarrhea), the refusing (eating distress), the skitters (anxiety), water-scorch (urinary infection). preparation: inner bark eaten raw, or steeped as tea.

**rare**
- **arnica** (greyspire): halves bruise and sprain recovery (external only). cures: sprained leg, punctured paw, joint-rot (arthritis). preparation: external use only; chewed into a poultice or rubbed on as ointment.
- **belly-rip fungus** (mistmoor): glow-fungus from the belly-rip sinkhole. cures: rot-lung (swamp fever). preparation: applied directly to necrotic tissue as a poultice; healer's discretion.
- **death-cap mushroom** (mistmoor, poison): pale mushroom found only in the rotting mere. no cures; hazard only. preparation: no safe preparation; experimental use only by experienced healers.
- **elderberry** (mistmoor): advantage on disease saves for 3 sunrises. cures: weeping-scale (distemper), shiver-fever (influenza), leaf-bare cough (cold/chill). preparation: must be cooked; raw or unripe berries are toxic.
- **goldenrod** (any territory): +2 HP per 8h rest. cures: infected wound, deep gash, water-scorch (urinary infection), burrfever (lyme). preparation: tea, or poultice from bruised leaves.
- **lungwort** (greyspire, mistmoor): also heals yellowcough and rot-lung when mullein is scarce. cures: yellowcough, rot-lung (swamp fever), growth-sickness (cancer), chestbind (asthma), bronchitis. preparation: tea, or leaves chewed into a poultice and applied to the skin.
- **mullein** (greyspire, mistmoor): heals yellowcough and rot-lung lung damage. cures: yellowcough, rot-lung (swamp fever), growth-sickness (cancer), chestbind (asthma), bronchitis. preparation: tea, or dried leaf eaten raw.
- **prickly ash** (greyspire): ends frozen-paw numbness. cures: root-rot (tooth infection), punctured paw, joint-rot (arthritis). preparation: bark and berries eaten raw or as tea.

**very rare**
- **edelweiss** (greyspire): ends bellyache and eating troubles. cures: gut-run (diarrhea), the refusing (eating distress), leaf-bare cough (cold/chill). preparation: eaten raw.
- **swamp milkweed** (mistmoor): breaks curses. cures: the spotting (pox), the spirit-eaten (spirit curse). preparation: dried roots eaten, medic-supervised only given the toxicity.
- **wolfsbane** (greyspire, poison): removes spirit curse (DC 20 medicine check). cures: the spirit-eaten (spirit curse). preparation: steeped into a strong tea by a trained medic and given directly to the patient; no way to lessen the risk, only a steady hand and a fast attempt.

**restricted (poison; medic-handled only)**: no herb in this tier has a listed preparation; a real method here would imply a safe way to use it, and there isn't one. these exist purely as hazards.
- **bloodroot** (any territory, poison): 3d6 poison damage (DC 16 half). no cures; hazard only.
- **deadly nightshade** (any territory, poison): confusion then paralysis (wis DC 15). no cures; hazard only.
- **deathberries (yew)** (any territory, poison): mercy killing. no cures; hazard only.
- **foxglove** (any territory, poison): deadly heart poison (DC 18 or die in 1d4 min). no cures; hazard only.
- **holly berries** (any territory, poison): 2d4 poison (DC 12 half). no cures; hazard only.
- **oleander** (any territory, poison): 4d6 poison, no antidote (DC 18 half). no cures; hazard only.
- **poison ivy** (any territory, poison): contact: -1d4 cha, disadvantage stealth 3 days. no cures; hazard only.
- **water hemlock** (any territory, poison): lethal poison (DC 20 half, still 6d6). no cures; hazard only.
- **wintergreen** (any territory, poison): often misidentified. no cures; hazard only.

full mechanical detail (exact HP/exhaustion math, prep methods per herb, side effects) lives on the site's [illness and herbs page](https://howlbert.neocities.org/illness.html); this is the reference version for quick lookup in-server.

---

## dice and statistics guide: content

pulled from `rpg_rules.py` and `engine/dice.py`; this is the actual math behind every `/rpg action:roll` and skill check in the game, not a simplified version of it. meant to live in the **dice and statistics guide** channel; the separate **examples** channel is folded into this instead (see below), rather than being a second channel.

### the core roll

every check is **d20 + attribute modifier + situational modifiers**, compared against a difficulty class (DC):

- **natural 1**: automatic failure, regardless of modifiers.
- **natural 20**: automatic success, regardless of modifiers.
- **advantage**: roll twice, take the higher.
- **disadvantage**: roll twice, take the lower. advantage and disadvantage cancel out if a wolf has sources of both on the same roll; they don't stack in the same direction either (two sources of advantage is still just advantage once).

### DC tiers

- **easy**: DC 10, routine.
- **moderate**: DC 15, challenging.
- **hard**: DC 20, desperate.
- **legendary**: DC 25, nearly impossible.

### attribute modifiers

attributes run 1 to 10. the modifier added to a roll isn't the raw score, it's this:

- score 1: -3 modifier
- score 2: -2 modifier
- score 3: -2 modifier
- score 4: -1 modifier
- score 5: 0 modifier
- score 6: +1 modifier
- score 7: +1 modifier
- score 8: +2 modifier
- score 9: +2 modifier
- score 10: +3 modifier

### the six attributes and eight skills

attributes: strength, dexterity, survival (constitution), intelligence, charisma, wisdom.

- **herblore**: governed by intelligence.
- **hunting**: governed by strength, dexterity.
- **stealth**: governed by dexterity.
- **tracking**: governed by intelligence.
- **intimidation**: governed by charisma.
- **persuasion**: governed by charisma.
- **survival**: governed by constitution, strength.
- **medicine**: governed by wisdom.

a role's proficiencies (below) determine which skills it rolls best at; every role has two.

### role attribute ranges and proficiencies

distribute points across all six attributes; the total must fall within the role's range. this is also the fastest way to see which two skills a role leans on.

- **alpha**: 30 to 35 points; proficient in intimidation, persuasion.
- **alpha's guard / advisor**: 27 to 32 points; proficient in intimidation, tracking.
- **medic**: 20 to 25 points; proficient in herblore, medicine.
- **guard**: 18 to 22 points; proficient in intimidation, survival.
- **hunter**: 16 to 20 points; proficient in hunting, stealth.
- **scout**: 16 to 20 points; proficient in stealth, tracking.
- **forager**: 15 to 20 points; proficient in herblore, survival.
- **diplomat**: 15 to 20 points; proficient in persuasion, intimidation.
- **elder**: 15 to 20 points; proficient in medicine, herblore.
- **caretaker**: 12 to 18 points; proficient in persuasion, medicine.
- **juvenile**: 12 to 16 points; proficient in hunting, survival.
- **pup**: 8 to 12 points; proficient in survival.
- **rogue**: 15 to 20 points; proficient in stealth, tracking.
- **lowbelly**: 12 to 18 points; proficient in stealth, persuasion.
- **bog-born**: 15 to 20 points; proficient in herblore, survival.
- **drown-sick oracle**: 12 to 18 points; proficient in stealth, tracking.

apprentice variants (hunter apprentice, scout apprentice, forager apprentice, diplomat apprentice, caretaker apprentice, medic apprentice) sit a tier below their full role, both in point range and in what they're allowed to do solo; see `rpg_rules.py`'s `ROLE_FEATURES` for the exact caps.

### where modifiers actually come from

beyond the base d20 + attribute modifier, a real roll can pick up adjustments from (in the order the code checks them): injury, disease, genetics, character traits, herb buffs, frostbite, role features, long-term injuries, fear triggers, fire phobia, age (very young or very old), and omens (a good or bad omen from the previous sunrise grants advantage or disadvantage outright). weather and season modify tracking/scent dcs specifically, and now so do a handful of specific RP locations (the open moors and sunningrocks add +2 to scent dcs; see the gazetteer above).

### HP and combat

HP is **10 + strength score + survival (constitution) score**, using the raw attribute score, not the modifier (`engine/character.py`); a str 7, con 5 wolf has 22 HP.

- **initiative**: 1d20 + dexterity modifier.
- **bite**: attacker rolls strength modifier + hunting proficiency (+ trait mods) vs the defender's dexterity modifier; a hit deals 1d6 + strength modifier.
- **claw**: both sides roll dexterity modifier; a hit deals 1d4 + dexterity modifier.
- a natural 20 on the attack roll is an automatic hit (crit); a natural 1 is an automatic miss (fumble). a defender's natural 1 is an automatic hit against them (no crit); a defender's natural 20 is an automatic miss.
- **crit** (1d4): 1 extra 1d4 damage, 2 knocks the target prone, 3 disarms, 4 applies a 3-round bleed (1 HP/round).
- **fumble** (1d4): 1 grants the enemy a free attack, 2 gives disadvantage on your next attack, 3 knocks you prone, 4 has you bite your own tongue for 1 self-damage.
- **maneuvers**: `/combat maneuver` covers 18 named moves (`engine/combat_guide.py`), including four lethal finishers only usable once the defender is already badly hurt: killing bite (1d12+2, defender at or below 35% HP), spine bite (1d10, 50%), neck snap (1d10+1, 40%), skull smash (1d12, 45%).
- **NPCs**: `/combat npc` pulls from a real bestiary (`engine/bestiary.py`); predators, hearth-hounds, and clan cats all have full attribute blocks and use the same HP formula as player wolves.

### death and dying

a wolf at 0 HP is dying, not dead. `/medic action:deathsaves` rolls constitution against an escalating DC each round: **10, then 12, then 15** (`engine/death_saves.py`). three rounds survived without a fail stabilizes at 1 HP; a single fail is death. a natural 1 is an automatic fail, a natural 20 an automatic stabilize.

a medic or packmate can stabilize someone else directly with `/medic action:stabilize`: wisdom + medicine proficiency vs DC 15, with yarrow, oak bark, or cattail each adding +2 if used. cobwebs skip the roll entirely and auto-stabilize. there's no mercy-kill mechanic in the bot; a wolf being allowed to die is purely a roleplay choice, not a command.

### exhaustion

exhaustion runs 0 to 10 (`EXHAUSTION_MAX`, `engine/exhaustion_effects.py`), not the shorter 6-level track some older references use:

- **6 or higher**: max HP is halved.
- **8 or higher**: cannot move or take field actions.
- **10**: death at the next sunrise.

a long rest relieves exhaustion; `/vitals action:rest` is the command. there's a separate, smaller **pain exhaustion** track (0 to 5) that adds disadvantage at its cap; herbs and treatment relieve it independently of the main exhaustion track.

### disease

diseases don't share one universal progression formula; each of the 25+ diseases in `engine/diseases.py` has its own per-stage DC and its own effect (HP loss, mood loss, hunger loss, exhaustion gain, hunt penalty, and so on). a mild/severe/deadly disease like cough happens to run DC 12 → 15 → 18, but that's that disease's own numbers, not a fixed rule; check `/skilllist` or the specific disease entry rather than assuming a pattern.

### mating, pregnancy, and litters

- **courtship**: `/courtship action:court` rolls a charisma-based check; success marks the target receptive for the next 7 days.
- **mating**: `/courtship action:mate` requires both wolves' players to confirm; neither side can commit the other alone.
- **conception**: checked at DC 15 (`engine/mating.py`).
- **gestation**: 63 days; the final 21 days count as late pregnancy, with hunt yield cut 20% at the midpoint and 35% in the final stretch (`engine/pregnancy.py`).
- **litter size**: 1d4+1 (2 to 5 pups), adjusted down for the mother's condition, floor of 1.
- **inheritance**: each pup's starting score per attribute is `(parent a + parent b) // 2 + 1d4 - 2`, clamped 1 to 10, then the whole spread is rebalanced to a pup-appropriate total (`engine/family.py`).
- raspberry leaves are a real mechanic here too: they grant advantage on the next birth-related hemorrhage save, not just flavor text.

### pack unity and bonds

pack unity runs **-5 to 10**; collaborative hunts and patrols raise it, paranoia-triggered raids, pack schisms, and broken cat pacts lower it (`config.py`, `db.adjust_pack_unity`). there's no separate numeric "rival pack standing" scale; rivalry between individual wolves is tracked as a bond-strength type (`db.adjust_bond_strength`), raised by things like food theft or jealousy, not a per-pack diplomacy meter.

### fire, weather, and travel hazards

- **fire fear** is real: within range of open flame, a wolf rolls a wisdom save at DC 12 or is frightened (disadvantage while the fire's in view); wildfire specifically also forces a survival/constitution save at DC 15 each round or 1d4 heat damage. an ally can talk a frightened wolf through it with a persuasion check at DC 14 (`engine/fire_fear.py`).
- **territory hazards** (`engine/travel_hazards.py`): river DC 12, swamp DC 15, mountain DC 18, forest DC 10, twolegplace DC 14; river crossings get +2 DC in spring runoff.
- **twoleg-world failures** on a bad hazard roll: thunderpath (3d8), a twoleg nest (1d4), a dog (2d6), or a trap (no damage, but you're caught).

### seasonal modifiers

season shifts real numbers, not just flavor text (`config.py`):

- **hunt payout**: spring +5%, summer +10%, autumn -5%, winter -20%.
- **forage DC**: spring -2, summer +0, autumn +2, winter +5.

### advancement

XP comes from daily play, quest completion, and den chat. spending it (`/advance action:spend`): 5 XP for +1 to an attribute (capped at 10), 5 XP for an earned skill trait (capped at +3 total from XP), 10 XP to request a bonus role feature, which still needs admin approval.

### the skill check catalog

`/skills` and `/skilllist` are the real DC reference for everything not covered above: 9 categories (tracking, stealth, howling, social, spiritual, survival, herb_prep, crafting, navigation) covering the basil rules' full scripted check list. use those commands for a specific DC rather than guessing from an old flat table; a lot of the numbers floating around predate the bot and don't match what's actually coded anymore.

a note on scope: an older, pre-bot version of this guide included a standalone "NPC generator" and a page of GM random-event tables. those were tools for a live human game master rolling dice by hand; howlbert resolves NPCs through the real bestiary above and doesn't need a manual random-event table, since every relevant roll already happens inside a command. neither has a bot equivalent, so neither is reproduced here.

### worked examples

- **a hunter (dex 7, +1 mod) tries a hunting check at moderate DC (15\)**, no other modifiers: needs to roll a 14+ on the d20 to succeed (14 + 1 = 15).
- **that same hunter is exhausted (disadvantage) but has a good omen active (advantage)**: they cancel out; the hunter rolls once, normally.
- **a scout (dex 6, +1 mod) tracks a fresh trail in rain**: rain adds +3 to the DC, but a fresh trail only takes half that penalty (trail-age scaling), so the actual DC goes up by ~2, not 3.
- **a medic (wis 7, +2 mod) treats an infected wound (cure DC 14) with yarrow**: 2 mod + whatever the die rolls; a natural 12 or higher succeeds outright, a natural 1 fails regardless of the math.

---

## adoptables guide: content

meant to live in **#adopts**, pinned or as the forum's guide post.

### what are adoptables?

an adoptable is a character someone else offers up for another player to take on. there are two real kinds, and they claim differently:

- **a concept, not yet registered**: a partial character idea (a sibling, a rival, a litter-mate) posted for someone else to design the rest of and bring into the game themselves. nothing is real until whoever claims it actually runs `/register` and builds the wolf.
- **an existing wolf, already registered and fully statted**: a pup from a litter the parent doesn't plan to keep playing, or a character a player no longer wants but doesn't want to see die off. this wolf already has real stats, skills, and history in the bot; claiming it doesn't create a new wolf, it hands over an existing one.

either kind is different from an NPC on the wolves page: an NPC is staff-made and already registered whether or not a player has claimed it. an adoptable is offered up by another *player*, whether or not it happens to already exist in-game.

### what to include for adoptables

for a not-yet-registered concept, include whatever information the adoptee needs to finish making the character:

- pack/allegiance
- character name
- character age
- character gender
- relation to your character
- character looks
- any other important details you deem necessary

mark clearly which of these are locked and which the adoptee is free to customize.

for an already-registered wolf, post its real sheet instead: pull straight from `/profile sheet:true` (attributes, hp, skills, role, lore) so whoever claims it knows exactly what they're taking on, plus anything the previous owner wants to note about its history or relationships.

### to get started

1. name the adoptable, preferably in relation to your character (example: OC's brother, or OC's kit); or, for an already-registered wolf, just use its real name.
2. include any necessary information about the character (see above; a concept needs its set/customizable traits, an existing wolf needs its real sheet).
3. let them know what's free to customize, if anything.
4. post it.

### claiming adoptables

- comment in the adoptable's thread to claim it.
- **for a concept**: once claimed, register the actual wolf yourself with `/register`; the set traits above become that command's starting details (name, starting age, and any genetic condition like blind, deaf, or missing a limb all have real `/register` parameters), and the customizable traits are yours to decide before or during registration.
- **for an already-registered wolf**: claiming it doesn't move ownership by itself; a mod needs to run `/wolfadmin transfer` to actually hand the wolf from the old owner's account to the new one. comment to claim, then flag a mod to make the transfer real.
- claiming an adoptable doesn't reserve it forever; if you don't follow through (registering the concept, or getting the transfer done), the poster can reopen it for someone else to claim.

### adoptable example

**sibling for my OC**

set traits:
- looks:
- age:
- pack:

customizable traits:
- gender:
- personality:
- name:

---

## neocities guide: content

meant to live in **#neocities**, as a pinned post; a persistent link to the site, not a live feed, so this only needs to explain what's there and why it's worth the click.

### what is it?

[howlbert.neocities.org](https://howlbert.neocities.org) is the world bible: the deep, evergreen lore and reference material that doesn't fit a chat channel or a social post, hosted as a free static site on [neocities](https://neocities.org/site/howlbert). no login, no cookie banner, nothing to install; just pages to read.

### why a neocities site and not another discord channel?

channels scroll; this doesn't. the world's lore, the pack write-ups, and the herb/disease reference all change slowly and get referenced constantly, which is exactly what a wiki-style site is for and a chat channel is bad at. it's also just the aesthetic: neocities leans into a dark, atmospheric, old-web feel that suits a field-journal-for-a-dying-wild tone better than a discord embed does.

### what's actually on it

- **[the world](https://howlbert.neocities.org/world.html)**: the setting itself, the maw, and the shape of the wild the four packs share.
- **[the four packs](https://howlbert.neocities.org/packs.html)**: full appearance, culture, hierarchy, and relations detail for greyspire, mistmoor, thistlehide, and silverrush, plus the real role features (commanding howl, green tongue, killer's instinct, and the rest).
- **[illness & herbs](https://howlbert.neocities.org/illness.html)**: the full mechanical reference, exact hp/exhaustion math, every herb's real preparation method and side effects, and which restricted herbs actually exist in the compendium.
- **[the wolves](https://howlbert.neocities.org/characters.html)**: the character roster, claimed and adoptable alike.
- **[the human world](https://howlbert.neocities.org/twolegs.html)**: twolegs, thunderpath, and the rest of what's dangerous on the other side of the tree line.
- **[how to play](https://howlbert.neocities.org/play.html)**: a plain-language onboarding page for anyone who lands on the site before ever opening discord.
- **[wolf name generator](https://howlbert.neocities.org/namegen.html)**: exactly what it says.
- **[book one: the blinking](https://howlbert.neocities.org/bookone.html)**: the server's actual ongoing plot, the way a reader (not a player) would encounter it.
- **[first sunrise](https://howlbert.neocities.org/first-sunrise.html)**: a short playable choice-based teaser, one wolf's first hunt, that ends by linking straight to the discord invite. built to give a visitor something to *do* before they ever open discord.
- **[credits](https://howlbert.neocities.org/credits.html)**: who made what.

### how it stays honest

the site is a reference, not a second source of truth; where it and the bot disagree, the bot's actual code wins, and the site gets corrected to match, not the other way around. if you spot a mismatch (an herb's prep method, a disease's cure, a stat that doesn't add up), flag it; it's a real bug in the docs, not flavor.

---

## more channel ideas: additions, changes, removals

**addition, #in-memoriam** (server info or its own small category). the permadeath/obituary system (`engine/obituary.py`) already writes a real, specific line for every wolf that dies (cause plus a pulled highlight from their own journal), and today that only surfaces once, buried in the rollover crisis "losses" embed. a dedicated channel the bot also posts every obituary line to turns something that currently scrolls past once into a permanent, browsable memorial, which matters more here than in most RP servers, since death is actually permanent. cheap: one more `send()` call at the same point `rollover_announce.py` already fires.

**change, reconcile advertisement with #server-directory.** these aren't quite duplicates but they're close enough to cause confusion once both exist. **advertisement** (server info) reads as outbound: the server's own pinned ad copy for other servers to see. **#server-directory** (art wing, held for later tier) is inbound: the curated list of partner/affiliate servers this server is pointing members toward. worth a one line pinned note in each clarifying which direction it faces, or just merging server directory's job into advertisement's channel topic instead of adding a new channel at all.

**change, consider merging hiatus notice and leaving notice.** both are low traffic, single purpose status announcements with the same audience and the same "post once, mods see it" shape. not urgent, but if OOC space ever feels crowded, this is the safest pair to fold into one **#member-status** channel without losing anything.

**not recommending, per pack text channels.** worth naming since it's the obvious next idea once the great packs lore above exists in one place: a channel per pack (#greyspire, #silverrush, etc.) for in den OOC chat. holding off on this one specifically; it fragments an already small server's OOC conversation four ways, which is the opposite of what a 24 member server needs. the affiliation is already expressed in character through RP channels and pack roles; a fifth OOC chat shaped channel per pack isn't worth the dilution at this size. revisit only if the server genuinely outgrows a single general chat.
