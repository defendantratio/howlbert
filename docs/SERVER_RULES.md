# server rules

howlbert (our Discord wolf-RP bot) is the **main mode of roleplay** on this server. your wolf is a
real character in the bot, created, aged, fed, healed, mated, and (permanently) killed through
slash commands, and roleplay is posted in-character on top of it. these rules say how the two fit
together. commands look like `/command` (for example `/register`, `/combat`, `/medic`); run `/help`
for the full list.

---

# [🧑] Character Rules

## Appearance & Realism

* Wolves are wolves, not anime wolf-people. No unnatural colors (pink, blue, neon). Acceptable
  coats: gray, black, white, brown, tawny, reddish, and blends thereof. (Coat is free-text in your
  `/profile`.)
* Scars, deformities, and missing parts are allowed and encouraged (this is a brutal world), and
  the bot makes them real: `/register genetic:` lets you start with blindness, deafness, a missing
  leg, muteness, spine conditions, and more; wounds leave permanent scars and limps through play.
  See Unique Physical Traits below.
* Eye colors: yellow, amber, gold, brown, gray, pale blue. No red or glowing eyes unless
  Maw-corrupted (staff approval). Corruption is a real state the bot tracks (`maw_karma`, spirit
  rites via `/medic`); the glowing-eye look is a narrative flourish on top.

## Starting Slots

* You may keep up to **ten (10)** wolves per player, the bot's cap. Make one with `/register`, list
  them with `/wolves`, and swap which you are playing with `/switchwolf`.
* Staff may ask brand-new members to start with a couple of wolves and grow into more as they settle
  in, but that is onboarding guidance, not a hard limit; the real ceiling is the bot's 10.

## Slot Usage Rules

* Characters must be in **different packs**, set with `/setfaction`. No two of your wolves in the
  same pack (prevents conflict of interest and metagaming).
* Exception: if a pack has fewer than three active players, you may temporarily run two characters
  there with moderator approval.
* Loners count toward your slot total and require special approval. (Walk a wolf as a loner via
  `/setfaction`, then leave; most loners die, see Pack Allegiance.)

## Inactive Characters

* The bot auto-marks a wolf **dormant or away** after a stretch of inactivity, which stops their
  rollover decay (they will not starve or sicken while you are gone), so idle wolves are paused, not
  punished.
* Characters inactive **60+ days** may be **archived** to free a slot.
* Archived characters can be reactivated within **90 days** (`/switchwolf`). After that they are
  **forgotten, dead to the Maw**, unless you reapply.
* Players who leave the server permanently forfeit their characters to the narrative (NPC'd, killed,
  or exiled at moderator discretion).

## Name Structure

* Wolf names are generally two-part compound names (Warrior-Cats-adjacent but darker). Set with
  `/register` and change with `/rename` (see Name Changes). Acceptable formats:
  * **Adjective plus Body Part:** Rivenmaw, Ironjaw, Softstep, Shallowclaw
  * **Noun plus Noun:** Throatmoss, Stoneguard, Weepstone, Bogwhisper, Shallow-Grave, Mourning-Tide
  * **Verb plus Noun:** Howlwind, Bitefrost, Driftshadow
  * **Possessive plus Noun:** Sorrowvein, Salt-Tongue, Bitterroot

## Prohibited Names

* Canon names from popular IPs (Ghost, Nymeria, WhiteFang).
* Names referencing real-world brands or memes.

## Name Changes

* A wolf may earn a new name IC through notable deeds (for example Softpaw becomes Ironjaw after
  killing a bear). Apply it with `/rename` after moderator approval and an IC scene.
* No frivolous changes.

## Realistic Wolf Anatomy

* Wolves are large canines, not monsters, not magical beasts (unless corrupted by specific plot
  events).
* **Size** is a real combat stat: set `combat size` (small, medium, or large) via `/character`. Use
  it to reflect your pack. **Mistmoor** wolves smaller, **Greyspire** wolves larger:
  * Weight (narrative): 60 to 180 lbs (27 to 82 kg). Mistmoor 60 to 100 lbs (small); Greyspire 120
    to 180 lbs (large); Thistlehide and Silverrush average (medium).
  * Height (narrative): 26 to 32 inches at the shoulder.
* No wings, no unnatural body modifications.

## Age & Life Stages

* howlbert measures age in moons (months) and sets your life stage automatically from it; age
  advances on `/world rollover` (a "sunrise"). Set or adjust with `/character` (`age`, `birthday`).
  The bot's thresholds:
  * **Pup:** under **6 moons**. Cannot hold rank, cannot fight serious combat, must have an adult
    guardian.
  * **Juvenile or young wolf:** **6 to 24 moons**. Can hold low ranks; approaching full maturity.
  * **Adult:** **24 to 59 moons**. Prime.
  * **Elder:** **60+ moons**. Rare and respected; the bot applies elder stat drift and frailty. An
    elder wants a backstory for how they survived this world. (Realistic: wild wolves rarely pass 6
    to 8 years, so a wolf of 5+ years is genuinely old here.)

## Minimum Backstory Requirements

Your character's backstory must answer:

* **Origin:** born in the pack? Joined later? From where?
* **The Wound:** what loss, betrayal, or failure shaped them? (Emotional or physical.)
* **The Maw:** do they believe? Why or why not? Have they felt the Maw's presence? (Set their stance
  with `/character maw belief`; the bot tracks `maw_favor` and `maw_karma`.)
* **Humans:** have they met humans? How did it go? (Human factions are real, see `/faction`.)

## Personality & Flaws Requirement

* Every character must have at least **two visible flaws** (reckless, distrustful, cowardly,
  obsessive, volatile) that affect their decisions in RP.
* "Flawless" or "perfectly noble" characters are not allowed. This is a brutal world.
* Personality must be consistent with backstory (a wolf who lost their pack to betrayal should show
  guardedness).

## Character Relationships & Pre-Existing Connections

* You may establish pre-existing relationships (family, rivalry, past alliance) with other players'
  characters, both parties must consent and document it. Record them in the bot with `/bonds` (kin,
  friendships, rivalries, mentors, romances, found families) and view lineage with `/family`.
* New characters cannot automatically know or be trusted by established pack leaders without an IC
  reason or scene.
* Family trees must be approved by staff to prevent lore contradictions.

## Pack Transfer & Loyalty Rules

* A character may leave their pack and join another via `/setfaction`, but this requires:
  * An IC scene showing the departure and its reasons.
  * Staff approval (fits the lore, does not disrupt pack dynamics).
* No switching packs more than once every 30 days without special permission.
* Betraying a pack and joining an enemy carries severe IC consequences (hostility, exile, or death
  from the old pack; the bot tracks exile and rejoin cooldowns, `/pack pardon` can lift them).

## Pups & Breeding Rules

* Pups **inherit a mix of both parents' traits**. The bot rolls appearance and genetics at birth
  (`/courtship` to mate and check pregnancy; `/pupcare` to birth and raise a litter). They follow
  the age rules above.
* No more than **three (3) living, played pups** per character at a time. (A litter is larger, see
  Pregnancy & Birth, but you only play up to 3.)
* Pups need an adult guardian (a parent or designated caretaker) and are nursed until they leave the
  pup stage (`/pupcare`, `/drink type:milk`).

## Healing & Injury Realism

* The bot enforces realistic healing. You literally cannot shake off a serious injury. Wounds
  persist across sunrises and only clear through `/medic` (clinical care, herb treatment, spirit
  rites) or herbs; broken bones and deep wounds take real in-game time.
* Untreated wounds get worse: left alone, injuries develop complications or convert to permanent
  chronic conditions (limp, chronic pain, scarring). Reflect it in your RP (limping, favoring a leg,
  slower reactions). The bot already is.
* Staff may enforce additional cooldowns on heavily injured characters for realism.

## Unique Physical Traits & Mutations

* Minor unique traits, some registrable at creation via `/register genetic:`:
  * Heterochromia (two eye colors)
  * Piebald or vitiligo-like markings (narrative)
  * Coat dilution (Washed-Hide), albinism, melanism
  * Unusually large or small size (`/character combat size`, within realistic bounds)
* **Major mutations**, missing limbs, blindness or deafness from birth, spine malformations,
  dwarfism-like conditions, are real birth mutations the bot can assign, and require **extensive
  backstory justification and staff approval** to choose at register. Some only appear at birth, not
  on demand.

## Supernatural / Corrupted Characters

* Any character touched by the Maw or with supernatural abilities requires **staff approval before
  creation**. The Maw is a real system (`maw_favor`, `maw_karma`, divine wrath, spirit rites via
  `/medic`); it rewards the faithful and punishes the wicked.
* Corrupted wolves must have clear limitations and weaknesses (vulnerability to certain rituals,
  progressive degeneration).
* Abilities are limited to subtle effects (visions, whispers, unnatural resilience). No fireballs,
  telekinesis, or mind control.

## Death & Resurrection Policy

* **Character death is permanent.** When your wolf hits 0 HP it enters dying and rolls death saves
  (`/medic action:deathsaves`, or a medic's `/medic action:stabilize`); fail them and the bot marks
  the wolf **dead, no exceptions.** Resurrection happens only as part of a staff-run plot (for
  example the Maw raises a corrupted husk).
* You cannot "reroll" a dead character into a new one with the same name, personality, or backstory.
* If your character dies you may make a new one immediately (`/rpg action:delete` then `/register`,
  or just `/register` a fresh slot), but it must be a genuinely fresh character (no relation to the
  dead one unless approved).

## Activity & Participation Expectation

* Characters are expected to participate in pack life. A wolf that never interacts may be archived
  or NPC'd. If you join a pack you are expected to:
  * Attend pack meetings (when scheduled).
  * Respond to pack-wide events and threats (`/pack`, wars, `/preypile`, howls).
  * Engage with packmates in at least one thread per week (or per your availability).
* Chronic inactivity may lead to your character being written out of the pack. (The bot's dormancy
  system pauses idle wolves; staff decide when "paused" becomes "written out.")

---

# [🐺] Roleplay Rules

## Posting Format

* In-character posting runs through the bot: `/proxy` (Tupperbox-style, type and it posts as your
  wolf), `/say` (a one-line IC line), `/sign` (body language, whimper, growl, nuzzle, lick), and
  `/scene` (threaded scenes with a roster). `/whisper` sends an IC DM.
* **Third person, past tense** preferred. *Rivenmaw stalked through the snow, his breath frosting
  the air.*
* **No asterisk roleplay** (`*licks paw*`). Use full sentences for prose, and `/sign` for pure body
  language.
* Length: one paragraph to several. Quality over quantity. One-liners are discouraged but allowed
  for fast-paced scenes (that is what `/say` is for).

## Fighting Mechanics

* Combat runs on the bot: `/combat start`, then `/combat begin` (rolls initiative), then
  `/combat attack` (bite or claw), with `/combat maneuver`, `/combat npc` for predators, and
  `/combat yield` to surrender. HP, injuries, and size all matter mechanically.
* **Consent-based PvP:** player-versus-player fights need OOC agreement from everyone involved, or
  moderator oversight for plot-critical fights.
* **Death:** permanent death happens only if the player agrees or it is a moderated event with clear
  stakes (for example a challenge for Alpha). You will be warned OOC before a mod-approved death. The
  bot's death-save system (above) resolves the mechanics.
* **Injury:** your character can be injured without consent in moderated events, but not maimed or
  killed without it.
* **Hunting and NPC fights:** resolved by dice. `/combat` for fights, `/rpg roll` and `/skills` for
  checks, `/field` and `/bones` for hunting. Mods set difficulty numbers for plot-critical rolls.

## Pack Allegiance

* Your character must belong to one of the four great packs (join, switch, or leave with
  `/setfaction`):
  * **Greyspire** (mountain): harsh, meritocratic, scarred.
  * **Mistmoor** (swamp): strange, spiritual, rot-touched.
  * **Thistlehide** (forest): memory-driven, communal, herb-wise.
  * **Silverrush** (river): fluid, open-border, grief-healing.
* **Loners and Rogues:** allowed in limited numbers (`/setfaction`, then leave). Must have a
  compelling reason and moderator approval. Most loners die here; yours should be the exception. Two
  bonded loners can even `/foundpack` a new den (then recruit with `/packinvite` and `/packjoin`).

## Lore Compliance

* Your character must fit their pack's culture, hierarchy, and beliefs. A Greyspire wolf who rejects
  scar-oaths is possible but must be justified and will face IC consequences.
* The Great Maw is the dominant (not universal) belief system. Atheism exists but is rare. Your
  character can doubt, but cannot prove the Maw false.
* Human activity is real (`/faction`). Your wolf has probably met humans, raiders, traders, threats.

## No Spamming or Flooding

* Give others a chance to post. In a scene with 3+ people, wait for at least two others to post
  before replying (unless agreed otherwise). `/scene here` shows who is in the scene.

## Hierarchy & Challenges

* Pack ranks are IC. If your character challenges a higher rank, be prepared to lose, flee, or die,
  and the higher-ranked **player must agree OOC** unless it is a mod-run succession event.
* You cannot challenge a leader for their position without moderator approval. (Formal disputes run
  through `/role` and `/rite trial`.)

## Scene Location & Territory Respect

* Entering another pack's territory without IC permission is trespassing. Expect hostility. The bot
  tracks territory (`/pack territory`) and lets you sneak with `/disguise` (risky).
* Cross-territory scenes require OOC coordination with the other pack and, ideally, mod awareness.
* Claiming a neutral location (the Ripsnout, the Maw's Teeth) is fine, but neutral zones are often
  contested or dangerous. Mark where you are with `/location set`.

## IC Time Flow

* Scenes exist in a "time bubble." They progress at their own pace, and concurrent scenes may sit at
  different IC times.
* The **server clock** is the bot's (`/world` shows time, weather, season; sunrises advance on
  `/world rollover`). Major time-skips (healing, pregnancy, aging, large plot jumps) require
  moderator approval and are announced server-wide.
* Small skips (a few hours to a day) between scenes can be self-managed; keep consistency with
  ongoing plots.

## Realistic Combat Outcomes

* Numbers matter. A single wolf cannot easily beat three healthy opponents, and the bot's combat
  math backs that up. Be realistic about your limits.
* **Injury stacks:** entering a fight already wounded is a real mechanical disadvantage (the bot
  carries your injuries and HP into the encounter).
* Retreat is always valid (`/combat yield`). Survival is a win; not every conflict ends in death.

## Consequences of Actions

* IC actions have IC consequences. Murder, betrayal, theft (`/crime`), or treason ripple through the
  world. Reputation spreads, alliances shift, vendettas form (the bot tracks pack standing and
  `maw_karma`).
* "Murder-hobo" behavior (random killing, senseless violence) is discouraged and will draw IC
  punishment or mod intervention.
* Commit a major crime and be ready for the fallout: exile, execution, or being hunted.

## Supernatural / Maw Influence in RP

* The Maw's influence is **subtle**: whispers, visions, rotting prey, strange omens, not overt
  magic.
* You may weave Maw visions or corruption into your own RP, but major supernatural events
  (possessions, curses, manifested spirits) require mod oversight. The bot's Maw favor and karma and
  spirit rites (`/medic`) are the mechanical backbone.
* Characters who claim to speak for the Maw are met with IC skepticism unless proven through mod-run
  events. No psychic abilities, telepathy, or direct Maw communication without approval.

## Ghosting in RP Scenes

* If you leave a scene without warning (especially mid-fight or mid-confrontation), a mod may
  temporarily NPC your character to keep the scene moving (`/scene`, `/npc`).
* Repeated ghosting leads to a warning and possible restriction from high-stakes scenes.
* Need to step away? Use `((brb))`, `((pause))`, `/scene leave`, or DM your scene partner.
  Communication is key.

---

# [💕] Relationship Rules

## IC Relationship Categories

The server recognizes several IC bonds, most trackable with `/bonds`:

* **Pack Bonds:** loyalty (or disloyalty) between packmates; the strongest ties in a wolf's life.
* **Friendships:** voluntary bonds of trust and affection.
* **Rivalries:** competitive, antagonistic, hate-driven; often as intense as love.
* **Mates:** a bonded pair (rarely a trio) raising pups and sharing territory (`/courtship`, sealed
  by rites like `/rite joining_howl` and `/rite moon_witness`).
* **Flings and Courtship:** developing romantic connections short of mating (`/courtship`,
  `/rite bone_gift`).
* **Family:** blood relations (`/bonds` kin, `/family`).
* **Cross-Pack Ties:** relationships across borders. Taboo but not impossible.

## No NSFW Content in Relationships

* As per the server's core rules, **no sexual, adult, or NSFW roleplay anywhere**, including all
  relationship dynamics (mating, flings, courtship, intimate scenes).
* Romantic intimacy is portrayed through **fade-to-black, implication, or emotional connection**.
  Explicit content is strictly prohibited.
* Do not describe physical acts, bodily details, or sexual tension in explicit terms.
* **Violations result in an immediate ban.**

## OOC vs. IC Relationships

* Your character's feelings are not your feelings. IC rivalry is not OOC hostility.
* IC romance does not require OOC romance. It is collaborative storytelling.
* If OOC feelings interfere with IC dynamics, step back and talk to a moderator.

## Mating Rules

* Mating is an **IC commitment**, made through the bot (`/courtship`) and often a ceremony
  (`/rite joining_howl`, `/rite moon_witness`), or simply by choosing each other.
* Mates are expected to hunt together, share dens, and defend each other. Breaking a bond can have IC
  consequences (jealousy, exile, blood feuds).
* There is no "marriage." Mates stay together as long as both wish; separation is allowed but may be
  messy.

## Multiple Mates

* Wolves are not strictly monogamous. Polyamorous bonds (a triad) are permitted **with all players'
  consent**.
* A wolf may take a secondary mate while keeping a primary, but this needs IC negotiation and may
  cause drama.

## Cross-Pack Mating

* Allowed but carries heavy IC risk (and real border tension the bot tracks via pack relations):
  * **Greyspire** views cross-pack mates as traitors unless the other joins Greyspire.
  * **Mistmoor** may see it as stealing swamp secrets. Dangerous.
  * **Thistlehide** might remember the couple but not trust them.
  * **Silverrush** is most tolerant, but still wary.
* Cross-pack mates often become loners, outcasts, or must choose one pack. A major plot driver.

## Mating Rituals

Packs have different traditions (roleplayed; back them with rites like `/rite moon_witness`):

* **Greyspire:** hunt a dangerous prey together (mountain goat, bear cub) and return with scars.
* **Mistmoor:** drink from the Belly-Rip's edge and share a prophetic dream; if dreams align, mates.
* **Thistlehide:** howl their ancestors' names together, binding memories; the pack witnesses.
* **Silverrush:** swim the Ripsnout channel together; if both survive, mates.

## Breaking a Mating Bond

* Mates may separate IC: betrayal, dead pups, political necessity, or simply falling apart.
* Separated mates may stay in the same pack (awkward) or one may leave.
* A scorned mate may seek revenge. Allowed, but follows PvP consent rules.
* **No OOC harassment for IC breakups.**

## Pregnancy & Birth

* Pregnancy and birth run through the bot: `/courtship` to conceive and check status, `/pupcare` to
  birth and raise the litter. Gestation is tracked in-game (roughly nine weeks IC); you may time-skip
  or play through it.
* Litters are typically **4 to 6 pups** (the bot rolls size and genetics; conditions like
  Thin-Litter reduce it). You may name and play only **1 to 3** as characters or NPCs; the rest are
  NPCs who may survive or die as plot demands.

## Playing Pups

* Pups (under the pup stage) can be played but **cannot be involved in any sexual content** (see main
  rules).
* Pups are vulnerable; they can be killed in **moderated events only, with player consent**. The
  bot's pup-care system (`/pupcare save`) models dying newborns you must act to save.
* Pups age up over time via sunrises, but **aging a pup to a new life stage** for plot happens under
  mod-run time-skips. Do not fast-forward your pup arbitrarily.

## Adoption & Found Family

* Wolves may adopt orphaned pups, even from other packs (`/pupcare adopt`, `/foster` to send a pup to
  an allied pack). Adoption needs IC consent from active birth parents.
* Found family (non-blood bonds as strong as blood) is encouraged. Record it with `/bonds`. The Maw
  values memory, not genetics.

## Family Drama

* Sibling rivalries, parental favoritism, and inheritance disputes are highly encouraged.
* Patricide and matricide are allowed but follow combat and death rules (player consent or mod event).
* Family secrets ("your father was actually from Mistmoor") are great plot hooks.

## Spies & Traitors

* A wolf may betray their pack to another, a major plot point. The betraying player must **OOC inform
  moderators before acting.**
* Consequences are severe (exile, death, being forgotten).
* **No player may be forced to make their character a traitor.**

## Major NPC Relationships

* NPCs (run by mods via `/npc`, `/narrate`) may serve as mates, parents, rivals, or litter-mates.
  These develop through events.
* NPC deaths are not subject to player consent, but mods handle them fairly.

## Minor NPCs

* You may create minor NPCs (an unnamed packmate, a background elder) without approval.
* Minor NPCs cannot give your character unfair advantages ("my NPC friend gives me extra food").
* Minor NPCs can be killed or removed by mods as needed.

## Human Relationships

* Wolves may form relationships with specific humans (the Harrow Daughter, Silas Crow historically;
  human factions are real, `/faction`). These are complex and often tragic. Humans are NPCs, not
  playable characters.
* **Romantic or sexual relationships with humans are not allowed** (bestiality themes are prohibited).

## Dark Themes

* No glorification of abuse. It must be portrayed as tragic or villainous.

## Shipping & Pressure

* No pressuring others to ship their characters with yours. Shipping is collaborative, not coercive.
* If someone says "no" to a romantic plotline, accept it gracefully. Do not ask why. Move on.
* Public shipping channels or memes about IC couples are fine as long as everyone involved is
  comfortable.

## Arranged Mating & Forced Bonds

* Alphas may arrange matings for political reasons (strengthen alliances, settle disputes).
* Players must **OOC consent** before their character enters an arranged bond. No forced IC mating
  without OOC agreement.
* Arranged mates may grow to love, resent, or merely tolerate each other. All valid arcs.

## Casual Physical Intimacy

* Flings, casual courtship, and brief romantic encounters are allowed (`/courtship`,
  `/rite bone_gift`, `/sign` nuzzle or lick).
* **All parties must OOC consent** before any intimate IC scene (even kissing, cuddling, or sharing a
  den overnight). No assumptions. Ask first, even for a fling.

## Mentor / Protégé Bonds

* An older or more experienced wolf may take a student or guide (`/bonds` mentor; `/role` shadowing).
  This creates a power dynamic that should be respected IC.
* Mentor bonds can evolve into friendship or rivalry, but **romance is strictly prohibited** given
  the power imbalance and OOC-discomfort risk. If a dynamic drifts, discuss it OOC and involve staff
  if needed.

## Handling Jealousy (IC vs. OOC)

* IC jealousy is allowed and encouraged for drama.
* OOC jealousy must be kept separate. If you feel jealous of another player's IC relationship, step
  back, breathe, and talk to a mod.
* Do not use IC jealousy as an excuse for OOC hostility or passive-aggression.

## Reconciliation & Re-mating

* Broken bonds (mating, friendship, family) may mend over time.
* Reconciliation requires IC scenes showing rebuilt trust, and mutual player consent.
* Re-mating after a breakup is allowed but should not be rushed. Let the story breathe.

## Grief & Loss

* Losing a mate, pup, family member, or close friend is a major IC event (and the bot logs it in your
  `/journal`). Silverrush wolves can even `/weep` at the weep stone.
* Let your character grieve realistically: anger, withdrawal, depression, revenge are all valid.
* Do not rush a grieving player's character to "get over it." Respect their pacing. Grief fuels
  character growth and villain arcs alike.

## Hybrid Pups (Cross-Pack Offspring)

* Pups born to cross-pack mates are often viewed with suspicion by both packs.
* They may be claimed by either pack, rejected by both, or born outcasts.
* A hybrid pup's pack status requires staff approval and should be handled IC with care.
* These pups often face unique challenges: identity, belonging, loyalty conflicts.
