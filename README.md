# howlbert

discord bot for realistic sentient wolf rp. economy uses **🦴 bones** only.

## quick start

```bash
git clone https://github.com/defendantratio/howlbert howlbert
cd howlbert
python3 -m venv .venv
source .venv/bin/activate   # windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: DISCORD_TOKEN (required)
python main.py
```

✦ copy `.env.example` to `.env` and set `DISCORD_TOKEN`

**one instance only.** a second `python main.py` causes interaction failures. howlbert writes `.howlbert.lock` and exits if another copy is running.

## keeping the bot online

the bot only runs while its process is alive. closing the terminal stops slash commands until it starts again.

✦ **local dev:** keep the terminal open  
✦ **vps:** systemd or screen (~$5/mo providers work fine)  
✦ **paas:** railway, fly.io, render with `DISCORD_TOKEN` in env  
✦ **auto rollover:** set `AUTO_ROLLOVER_ENABLED=true`; missed sunrises catch up on the next startup (up to 31 days)

### restarting

stop the running process first; only one instance may run (`.howlbert.lock`). if the bot crashed and won't start, delete a stale lock only when no `python main.py` is still running.

**windows (powershell, local dev):**

```powershell
cd C:\path\to\howlbert
# stop: Ctrl+C in the bot terminal, or:
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "howlbert" } | Stop-Process
# stale lock after a crash (only if start still says another instance is running):
Remove-Item -Force .howlbert.lock -ErrorAction SilentlyContinue
.\.venv\Scripts\Activate.ps1
python main.py
```

**linux / mac (local dev):**

```bash
cd ~/howlbert
# stop: Ctrl+C, or find and kill the process
pkill -f "python main.py"   # only if you're sure it's this bot
rm -f .howlbert.lock        # stale lock only
source .venv/bin/activate
python main.py
```

**vps with systemd** (see `docs/DEPLOY.md`):

```bash
sudo systemctl restart howlbert
sudo systemctl status howlbert
journalctl -u howlbert -f    # live logs
```

after slash-command or cog changes, restart so discord picks up updates. `/ping` should answer once the bot is back online.

## design

✦ **rollover** = one in-game sunrise (`/rollover` for admins, or auto via `.env`)  
✦ **four great packs** at `/register`: greyspire, mistmoor, thistlehide, silverrush; or **loner / rogue**  
✦ each great pack shares one treasury, tax, territory, and wars  
✦ **quests** progress from hunts, patrols, deposits, etc.; rewards grant automatically when finished (no manual turn-in)  
✦ **mood / hunger / hydration** decay continuously through the day, not only at sunrise; low stats add exhaustion and cut hunt yield  
✦ **genetic conditions** (blindness, partial blindness, deafness, muteness, brachycephaly, lstv, spinal arthritis, inbreeding depression, adhd, autism, and more) are inherited or rolled at birth; each has real mechanical penalties; hunt multipliers, attribute disadvantage, pain exhaustion gain, skill bonuses/penalties, or increased disease susceptibility  
✦ **recessive traits carry silently**: blindness, partial blindness, deafness, and albinism are recessive; a pup with one affected allele is a hidden **carrier** (stored separately, unexpressed) that can pass the trait to its own pups, so a defect can skip generations and resurface when two carriers breed  
✦ **litter size tracks the dam's condition**: a well-fed mother (high hunger) carries a fuller litter and a starving one loses or reabsorbs pups, instead of litter size being purely random  
✦ **cat clans**: trade meat and forage, and form pacts via `/pack pact` (see `docs/CAT_CLANS.md`)  
✦ **forage food** (berries, windfall fruit, roots, greens) drops from `/field forage` and `scavenge`; it ripens then overripens, just like meat rots  
✦ **the rotting mere** (mistmoor location): set ic location to "the rotting mere" and `/field forage` yields marsh-mallow, belly-rip fungus, or death-cap mushroom; each forage has a chance of maw-contact flavor, swamp disease exposure, and (mistmoor wolves only) rare drown-sick transformation  
✦ **passive scavenge**: unfed wolves forage a little each sunrise so neglect bites without instantly starving the den  
✦ **death log**: `/wolfadmin deaths` records cause of death each rollover  
✦ **admin tooling**: `/wolfadmin assign` registers a wolf to a player (paste sheets directly in chat); `/wolfadmin arrival` posts the arrival/birth scene for an already-registered wolf so it grants its long-term trait properly; `/wolfadmin dormant` exempts admin-held npc wolves from vitals decay until claimed; `/wolfadmin execute` marks a wolf dead with a lore-flavored cause  
✦ **pack-specific plot quests**: each great pack has its own gated board quest tied to its lore (e.g. silverrush's dam sabotage, greyspire's mining-camp raid)  
✦ **basil's rules** for attributes, skill checks, combat, herbs, disease, and pups; use `/help` in discord for the player guide

## realism mechanics

howlbert leans toward measurable, granular wolf-ecology effects over flavor text; every system below changes a number, not just a description.

✦ **breeding is year-round**: courtship, bonding, mating, and conception can happen in **any season**; `/courtship action:rival` contests mating access at any time  
✦ **inbreeding is taboo, not blocked** (as in wolvden): kin can mate, but any completed kin pairing turns the den on the elder (**−8 standing**, expulsion if it sinks them past the threshold) and scars the younger wolf (**−15 mood**, distressed, and a **fear of mating** for 7 sunrises that rolls their own courtship at disadvantage)  
✦ **inbreeding has a biological cost too**: a kin litter surfaces the family's hidden recessives far more often, carries a heavier mutation load, is far likelier to be born with **inbreeding depression**, and runs a real stillbirth risk; the closer the blood, the worse the odds  
✦ **pups and juveniles are still growing**: physical (str/dex/con) checks take a fading penalty (**−2** under 12 moons, **−1** through juvenile, **0** at adulthood), the mirror of the very-old elder drift; mental and social checks are unaffected  
✦ **energy costs more when the body is taxed**: pregnancy, nursing, active illness, and winter cold all slow energy regen (they burn extra calories), stacking with the hunger coupling  
✦ **pregnancy costs food**: pregnant wolves burn extra hunger/hydration each sunrise, and hunt/fish/scavenge yield drops **−10%** in early pregnancy, **−20%** mid-to-late; the final third blocks strenuous activity outright. nursing mothers burn extra hunger/hydration per pup  
✦ **pain exhaustion is a separate tracker (0 to 5)**: distinct from main exhaustion (0 to 10); accumulates from painful injuries and diseases (deep gash, fractured rib, scorched hide, snake venom, trichinosis, lyme, cancer, and more) each sunrise. herbs like willow bark and poppy target this pool specifically. at 5 stacks it overflows into main exhaustion  
✦ **injuries cost yield, not just combat**: non-blocking injuries (sprained leg, punctured paw, concussion, deep gash, infected wound, snake venom, torn claw, broken tooth, torn ear) reduce hunt/fish/scavenge yield, stacking up to **−50%**. severe injuries (fractured rib, spinal injury, paralysis) still block field commands outright  
✦ **injury at the den vs. in the field**: patrolling while hurt earns a standing **bonus** (up to +2) for putting the pack first; but if the patrol goes wrong (spotted, ambushed) an injured wolf takes **extra** standing loss on top, since the injury is why they couldn't get away clean  
✦ **disease needs real contact**: den-spread illness at sunrise checks whether a wolf was actually in the field that day; wolves who hunted, patrolled, scouted, or tracked have **−50%** exposure to respiratory disease and **−25%** to contact disease versus one who stayed denbound all day. trail/border encounters in `/field action:sniff` can also pass illness directly, same as `/playpen action:socialize` and `/explore`  
✦ **signature pack prey**: hunt drops are weighted by territory; **greyspire** takes mountain goats in its highlands, **silverrush** turns up water rats along its banks, and mistmoor/silverrush pull frogs while thistlehide flushes lizards, on top of the shared prey table  
✦ **long-term marks aren't just injuries**: the `long_term_injuries` system also stores permanent non-injury traits like arrival choices (bold/quiet/wary) and birth circumstances; a +1 skill bonus that follows a wolf for life  
✦ **few hard blocks; energy, not cooldowns**: instead of "come back next sunrise" walls, every field/social/den action spends **energy** (shown on `/vitals action:condition`). energy never refuses a command; acting at **0** just adds exhaustion and costs mood, on top of the exhaustion/pain-exhaustion layer rather than replacing it. energy restores each **sunrise** sleep, from `/vitals action:rest`, and via a slow **real-time drip** while a wolf is idle during the day, all scaled by **hunger** (a starving wolf recovers less). separate from energy, **prey and forage** repeats still pay a **shrinking share** in one sunrise (over-worked land yields less; forage/verge climb the dc); only the long rest and daily stipend stay once-per-sunrise  
✦ **pup care is need-gated, not blocked**: each pup takes milk or nursery mash once a sunrise, so mothers and caretakers can feed as many pups as still need it (nursing costs the mother hunger), instead of one feed per feeder  
✦ **continuous hunger and hydration**: vitals drain in real time between sunrises (checked on `/vitals`, `/eat`, `/drink`), so neglect bites gradually rather than only at rollover  
✦ **liquid diet**: `/drink type:broth` or `type:milk` to sip when a broken jaw stops you chewing solid meat; liquids feed only partway (hunger caps at 60) and never fully satisfy a carnivore; broth is bought or den-brewed from bones, milk comes from cat clans or settlement raids  
✦ **carnivore nutrition**: a wolf survives short-term on forage and liquids, but a meat-free stretch of 8+ sunrises risks **wasting sickness**; weaned wolves are **lactose intolerant** (milk gives them an upset gut) unless they carry the **lactase persistence** trait  
✦ **herb side effects and addiction**: the compendium's warnings are mechanical, not flavor; eating an apply-only herb, pressing a skin-toxin into an open wound, or dosing a pregnant wolf backfires (hp loss, miscarriage risk, gut upset), and sedatives like poppy, valerian, and willow build **tolerance and withdrawal** with repeated use  
✦ **vomiting and cumulative organ damage**: nauseating herbs eaten internally can be **thrown back up** on a failed con save (−8 hunger, −6 hydration, −3 mood); and the "long-term use" warnings now bite — repeated internal doses of an organ-straining herb are tallied for life, and past a threshold become a **permanent long-term condition** shown on `/vitals` (The Sapping from potassium-wasting diuretics, Bitter-Water, Yellow-Wither, or The Trembles from thiamine loss), each a −1 to the relevant checks. vary your herbs  
✦ **cadaver dissection (medic apprentices)**: `/medic action:dissect` lets an apprentice study any dead wolf (their own pack's, a rival's, or a loner's) to learn anatomy — it needs an **alpha** or **full medic** in your den to sanction the training, and a body from another pack also needs that pack's **alpha** to release it; once per sunrise, up to 3 lessons total; a passed medicine check deepens the **medicine** skill (a natural 1 nicks a rib and risks infection). it is solemn medical work that costs **−5 mood** for a packmate (**−2** for a rival or loner) and **notifies the fallen wolf's player**. it's *how* a medic comes to understand the organs a random wolf only feels as symptoms  

**combat granularity:**  
✦ **scarred hide**: taking 3+ wounds in a single fight permanently hardens the hide; **+1 max hp**, **−1 cha** (tracked via `long_term_injuries`)  
✦ **throat grab**: str maneuver, 1d4 damage; on hit defender rolls con dc 13 or loses their next action (**suffocated**)  
✦ **shoulder check**: str maneuver, 1d6 damage; on hit the defender is knocked **prone** and loses their next action (**repositioning**)  
✦ **rear guard**: wis maneuver, no damage; covering packmates grants the next npc attacker **disadvantage** on their roll  
✦ **wound pressure**: using the same maneuver twice in a row deals **+1 bonus damage**  
✦ **rage state**: when a packmate is knocked out (0 hp), other player wolves roll wis dc 12 or enter rage; **+2 attack**, **−2 defense** for the remainder of the fight  
✦ **burn injuries**: being caught on a faction raid against thorne_lumber or river_mill (15% chance) inflicts **scorched_hide** (+1 exhaustion/sunrise, 7-day heal; cobwebs only)  
✦ **field dressing**: any wolf, survival dc 14; packs moss against a **deep gash** to suppress the sunrise bleed for one day (`/medic action:field_dressing`)  
✦ **herb tolerance**: using the same herb on the same injury within 3 days raises the treatment dc by **+2**; varied treatment is encouraged by yarrow/plantain also curing torn_claw  
✦ **bone-set failure**: bone injuries (fractured_rib, spinal_injury, sprained_leg, broken_jaw) left **untreated for 3+ sunrises** cause permanent **−1 attribute** malunion (`malunion_X` in long_term_injuries)  
✦ **medic overextension**: healing **5 or more wolves in one sunrise** adds **+1 exhaustion** on rollover  
✦ **spine slam**: str maneuver, 1d6 damage; only usable on **prone** targets; on hit defender rolls con dc 14 or gains **bruised lung** (surgery required; −1 str, −1 wis)  
✦ **eye rake**: dex maneuver, 1d4 damage; on hit defender gains **swollen_eye_combat**; attack disadvantage for the rest of the fight  
✦ **grab and throw**: str maneuver, 1d4 damage; breaks any active pin, leaves defender **repositioning** (loses next action)  
✦ **wound wash**: medic action, dc 10 medicine; dock leaves or horsetail flush an **infected wound** clean (`/medic action:wound_wash`)  
✦ **healer's instinct**: full medic earns **+1 wis** permanently after **20 successful treatments** (`healer_instinct` long-term trait)  
✦ **brittle bone**: str maneuver hit on a defender with a malunion long-term injury triggers a con dc 11 save; failure **re-fractures** the old bone  
✦ **recovery variance**: long rest hp gain is modified by active injury load (−1 per injury), hunger below 30 (−1), and winter season (+1)

## commands

discord caps slash commands at 100; howlbert uses **hub commands** with an `action:` parameter. type `/` and pick a hub; discord autocompletes actions. full guide: `/help topic:overview`.

### hub commands


| hub          | actions (examples)                                                                                            |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| `/bones`     | `balance`, `daily`, `hunt`, `pray` (hunt prayer; once/sunrise), `work`, `crime`, `shop`, `buy`, `sell`, `inventory`, `use`, `give`, `leaderboard` |
| `/field`     | `forage`, `verge`, `scavenge`, `track`, `fishing`, `sniff`                                                    |
| `/hoarding`  | `hoard`, `gift`, `shred`                                                                                      |
| `/playpen`   | `toys`, `play`, `playall`, `toystore`, `socialize`, `groom`                                                   |
| `/packlife`  | `feedall`, `drinkall`, `howl`                                                                                 |
| `/howl`      | pack howl (standalone; once per sunrise)                                                                      |
| `/sign`      | body/visual language: `alert`, `rally`, `play`, `submit`, `soothe`, `threaten`, `freeze`, `track`, `greet`, `grieve`, `challenge`, `whimper`, `growl`, `nuzzle`, `lick`, `read` (unlimited; repeat signs on the same partner pay out less mood, down to 20%) |
| `/world`     | `time`, `weather`, `forecast`, `cooldowns`, `plot`, `hazard`, `travel`, `encounter`, `omen`                   |
| `/garden`    | `plots`, `seeds`, `plant`, `tend`, `harvest`, `clear`, `buy`, `guide` (grow your own herbs from seed)         |
| `/role`      | `quests`, `event`, `prophecy`                                                                         |
| `/prestige`  | `view`, `require`, `bonus`, `legacy`, `retire`, `halloffame`                                                  |
| `/courtship` | `court`, `mate`, `pregnancy`                                                                                  |
| `/pupcare`   | `birth`, `feed`, `list`, `save`, `adopt`                                                                      |
| `/advance`   | `view`, `spend` (attribute, **skill trait**, role feature)                                  |
| `/medic`     | `deathsaves`, `stabilize`, `surgery`, `treat`, `field_dressing`, `wound_wash`, `checkup`, `sacred`, `ritual`, `naming`, `lay_to_rest`, `swim`, `quarantine`, `observe`; full medic: sick packmates show in `/checklist` |
| `/herbs`     | `bag`, `guide`, `prepare`, `dryall`, `store`, `turnin`                                                      |
| `/faction`   | human faction relations: `status` (standings overview) · `observe` (flavor; once/sunrise) · `approach` (roll wis vs dc 12; ±standing) · `trade` (costs 3 bones; +2 standing; pack-specific) · `raid` (roll str vs dc 13; −faction standing; if caught −1 all factions) · `sabotage` (thistlehide -> thorne_lumber; silverrush -> river_mill; dc 15; memory-knot tracker) |
| `/rpg`       | `roll`, `setstats`, `delete`                                                                                  |
| `/skills`    | catalogued checks (`category:` · `check:` · `group:` · `helper:` · `opponent:`)                         |
| `/skilllist` | reference dcs by category                                                                                     |
| `/vitals`    | `condition`, `rest`                                                                                           |


### standalone commands


| command                                                | what it does                                           |
| ------------------------------------------------------ | ------------------------------------------------------ |
| `/register`                                            | create a wolf; great pack, loner, or rogue             |
| `/profile`                                             | wolf sheet (`sheet:true` for lore; paginates if large) |
| `/character`                                           | set your wolf's identity: pronouns, bio, birthday, avatar, ref image, birth sex, sexuality, maw belief, combat size, age |
| `/family`                                              | family tree / relationship web rendered as a diagram   |
| `/scene`                                               | rp scenes in threads: `start`, `join`, `leave`, `here`, `poke`, `end` (pinned roster; auto-join on post) |
| `/say` `/whisper`                                      | quick ic lines and styled ic dms (no message content intent needed) |
| `/location`                                            | set, clear, or show your wolf's in-character whereabouts |
| `/journal`                                             | read-only automatic life timeline (birth, pack, bonds, blooding, death, rites) |
| `/rite`                                                | den ceremonies: `naming`, `blooding`, `mourning`, `trial` · mate rituals: `bone_gift` (costs 3 bones, +5 mood to target), `joining_howl` (one-time; +1 maw_favor each), `moon_witness` (full moon only; +2 maw_favor each, seals romance bond) |
| `/npc`                                                 | server npc registry (`add`/`remove` admin); `/npc say`, `/npc sign` (real mood/standing effects on the target's wolf), `/npc narrate` (admin; no named speaker) |
| `/weep`                                                 | silverrush only: release grief at the weep stone (unlimited; repeats soothe less) |
| `/proxy`                                               | speak in-character as your wolves; import from tupperbox |
| `/wolves` `/switchwolf` `/rename` `/setfaction`        | multi-wolf and faction                                 |
| `/food` `/eat` `/drink` `/salvage` `/preypile` `/bury` | prey hoard and survival                                |
| `/explore venture`                                     | dig, scent, investigate                                |
| `/scout rescout` `/survey` `/trail`                    | scout field commands                                   |
| `/pack …`                                              | treasury, stash, tax, territory, wars, unity, `pact` (cat clans), `share`/`aid`, `tradepack`, `brokenrite` |
| `/bonds`                                               | friendships, rivalries, kin, mentors, found families; fling auto-detected on profile when mated pair has no romance bond |
| `/sign`                                                | body/visual language; mute wolves rally without a howl; unlimited, diminishing returns on repeat partners |
| `/combat …`                                            | initiative combat; `/combat encounter` for ambushes; combat panel: **bite**, **claw**, **maneuver**, **run away**, **submit** (yield + submission/spare/finish mechanics) |
| `/hazard`                                              | weather opposed roll                                   |
| `/medic action:quarantine`                               | isolate sick wolves (or `action:quarantine`)           |
| `/trade`                                               | player item and bone trades                            |
| `/crime`                                               | petty theft, or raid a rival wolf-pack den / cat-clan camp |
| `/pact`                                                | negotiate treaties with cat clans or great wolf packs (alpha or diplomat) |
| `/disguise`                                            | roll in another pack's scent to cross their territory undetected (risky) |
| `/gossip`                                              | plant a damaging rumor about another wolf (once per sunrise; backfires if traced) |
| `/rivals`                                              | view your wolf's rival npcs and grudge levels          |
| `/foster`                                              | send a pup to an allied pack as a diplomatic gesture (alpha only) |
| `/tribute`                                             | send bones to another pack to clear blood debt (alpha/advisor) |
| `/schism`                                              | break from your pack and found a new den (pack unity below 30) |
| `/wilderness`                                          | travel hazards, random encounters, or rest omens       |
| `/rpprompt`                                            | get or suggest an rp scene prompt                      |
| `/patron` `/redeem`                                    | boosts, invites, supporter perks                       |
| `/help topic:<category>`                               | full command guide                                     |
| `/skills` `/skilllist`                                 | basil's skill checks and dc reference                    |
| `/ping`                                                | bot health check                                       |


### admin commands

for server admins and `admin_ids` in `.env`:


| command                        | what it does                                                 |
| ------------------------------ | ------------------------------------------------------------ |
| `/rollover`                    | advance one in-game sunrise                                  |
| `/setseason`                   | pin the in-game season, or return it to real-world sync      |
| `/wolfadmin …`                 | assign / transfer / possess wolves, deaths log, dormant, execute |
| `/narrate`                     | post anonymous scene narration (no named speaker)            |
| `/plotadvance` `/setplotphase` | advance or set the book one plot phase (0 to 12)             |
| `/patronadmin`                 | donation codes and manual donor grants                       |


### collaborative pack activities

call the den with `collaborate:true`; **2 to 4 wolves** join via buttons, then the caller sets out.


| command                               | who                | what                                                        |
| ------------------------------------- | ------------------ | ----------------------------------------------------------- |
| `/bones action:hunt collaborate:true` | great pack hunters | shared hunt; +bones per extra wolf; large prey and ambushes |
| `/scout survey collaborate:true`      | scouts             | stealth border patrol                                       |
| `/scout trail collaborate:true`       | scouts             | tracking sweep                                              |
| `/pack patrol collaborate:true`       | pack at war        | combined war points                                         |


on large prey or ambushes, party wolves join combat on initiative (+1 attack per living ally, max +3).

### patron and invites


| reward                                | who gets it                                |
| ------------------------------------- | ------------------------------------------ |
| **25 bones** on first `/register`     | invited new player (within 7 days of join) |
| **40 bones + 2 standing**             | inviter after invitee stays **3 sunrises** |
| **60 bones + 3 standing + 10 mood**   | first server boost (one-time)              |
| **40 bones**                          | second boost slot (one-time)               |
| **+5 bones on `/bones action:daily`** | while actively boosting                    |


use `/patron` to check status. the bot needs **manage server** to track invites.

### donations and shop

✦ ko-fi tips and memberships can grant bones when webhook is configured  
✦ `/redeem` for one-time gift codes when configured  
✦ players: `/patron` and `/help topic:patron` in discord

### kickstarter

a planned campaign funds keeping the den online, not pay-to-win.

✦ **base goal: $1,500 usd**; deliberately lean, covering one year of 24/7 hosting plus fees and a small buffer. because kickstarter is all-or-nothing, a low honest floor is safer to hit and funds faster  
✦ **stretch goals** fund the development roadmap in tranches (the gathering at the maw's throat, fourtrees diplomacy, combat and healing depth, a content drop); dev time is donated sweat equity at the base goal  
✦ **bigger expansions** (a second exploration biome, a full web app) are planned as a **separate future campaign** rather than piled onto this one  
✦ full plan and budget breakdown: `docs/KICKSTARTER.md`

## rpg system

howlbert implements basil's tabletop rules across creation, rolls, combat, herbs, and conditions.


| feature              | commands                                                                       |
| -------------------- | ------------------------------------------------------------------------------ |
| attributes and roles | `/register`, `/rpg action:setstats`, `/profile`                                |
| skill checks         | `/skills`, `/skilllist`, `/rpg action:roll`                                    |
| combat               | `/combat start`, `join`, `begin`, `attack`, `status`, `end`                    |
| herbs                | `/field action:forage`, `action:verge`, `/herbs`, `/medic action:treat`        |
| conditions           | `/vitals action:condition`, `action:rest`; disease progresses each rollover    |
| death saves          | `/medic action:deathsaves`, `action:stabilize` at 0 hp                         |
| weather hazards      | `/hazard`                                                                      |
| xp                   | `/advance action:view`, `action:spend`                                         |
| mating and pups      | `/courtship`, `/pupcare`    |


**hp** = 10 + str + survival (con score). **pack unity** (0 to 10) rises from quests and falls from wars. **lone wolves** cannot use `/pack`. **rogues** cannot draw `/bones action:daily`.

**herb compendium:** 100+ plants, each with real preparation, side effects, and (for sedatives) addiction. `/field action:forage` in territory or `action:verge` at the thunderpath edge; `/herbs action:guide` for the guide. **preparation** chains: dry a fresh herb, then turn the dried herb into a **tea, rub, juice, poultice, gargle, ointment, sap, simmered milk**, or eat it **raw/cooked**; a **tea** or **gargle** can be **sweetened**. some herbs (labrador tea, valerian, poppy, skullcap, snakeroot) have a **daily dose cap**; exceeding it is a soft overdose (you get sick), not a hard block.

**herb gardens:** grow your own with `/garden`; buy/find seeds (`seeds`, `buy`), `plant`, `tend` daily, then `harvest`; `/garden guide` lists each plant's growing conditions (light, water, season).

illness blends wolvden / warriors fantasy with wolf-canid ecology. 30+ conditions; cough, weeping-scale (canine distemper), rot-lung (mistmoor), river rot (silverrush; no known cure), milk-fever, shaking-sickness, trichinosis, toxoplasmosis, lyme, tuberculosis, snake venom, chronic conditions, mental illness, and more; each with daily penalties to hunger, hydration, hp, hunt yield, and pain exhaustion. restricted poison herbs wired to real mechanics. **chronic diseases** (wasting sickness, cancer, rabies, river rot, dementia, feral shift) can't always be cured, but the right herbs give **supportive care** (ease exhaustion and pain) and can **hold progression** at bay for a few sunrises. see `/help topic:profile` in discord for the full list.

## territory wars

✦ alpha runs `/pack challenge <territory_key>` (keys from `/pack territory`)  
✦ members `/pack patrol` and `/pack scout` once per rollover during the war  
✦ after **2 rollovers**, `/rollover` resolves; highest score wins  
✦ owned territories pay daily bones into pack treasury each sunrise

## great packs


| key           | name              | path              |
| ------------- | ----------------- | ----------------- |
| `greyspire`   | greyspire         | path of the teeth |
| `mistmoor`    | mistmoor          | path of the belly |
| `thistlehide` | thistlehide       | path of the fur   |
| `silverrush`  | silverrush        | path of the tears |
| `loner`       | lone wolf / rogue | no pack           |


pick one at `/register`. loners have no treasury or pack trait; join a great pack anytime with `/setfaction`.

## prestige (tiers 0 to 7)

legacy grows from **completing quests** and `/prestige action:retire`. bone bonus is permanent on hunts and daily.


| tier | name             | total bone bonus |
| ---- | ---------------- | ---------------- |
| 1    | the named        | +5%              |
| 2    | the story-weaver | +15%             |
| 3    | the claimed      | +30%             |
| 7    | the sunderer     | +145%            |


`/prestige action:require` shows exact thresholds.

## roleplay and proxying

speak in-character as your wolves, tupperbox-style, plus slash tools that work without reading typed messages.

✦ `/character` sets a wolf's **pronouns, bio, birthday, avatar, and ref image** (shown on `/profile`)  
✦ `/proxy set tag:H:text` registers a proxy tag; typing `H:hello` reposts as that wolf via webhook and deletes your message  
✦ `/proxy avatar`, `/proxy list`, `/proxy clear`, `/proxy autoproxy` manage proxies; autoproxy posts all untagged messages as one wolf (`\` escapes a single message)  
✦ `/proxy import` migrates from **tupperbox** (dm tupperbox `tul!export`) or **pluralkit** exports, auto-linking to wolves by name  
✦ proxy **ooc markers**: wrap `((out of character))` or start a line with `//`; ic text posts as the wolf, ooc shows in the footer  
✦ `/say` and `/whisper` post one-line ic speech without the message content intent  
✦ `/location set` · `clear` · `show`; ic whereabouts on `/profile` and proxy footers  
✦ `/journal` reads your wolf's **automatic** timeline (register, birth, pack moves, bonds, blooding, death, rites); no player editing  
✦ `/scene start` opens a roleplay **thread** with a **pinned living roster**; posting auto-joins you (`/scene poke` pings the scene)  
✦ `/rite naming` · `blooding` · `mourning` · `trial`; pack ceremonies in-channel  
✦ `/rite bone_gift` · `joining_howl` · `moon_witness`; mate rituals: bone-gift costs 3 bones and lifts mood; joining howl announces a bond publicly (+1 maw_favor each, once per pair); moon's witness seals true mateship under the full moon (+2 maw_favor each, romance bond sealed, once per pair)  
✦ `/npc add` · `remove` · `list` (admin); `/npc say`, `/npc sign` (real effects on a player's wolf), `/npc narrate` (admin; no named speaker)  
✦ `/family`; relationship web rendered as a diagram, with the focus wolf's proxy avatar  
✦ `/sign`; body language when a wolf can't howl (mute rally, alert, play, freeze, track, greet, grieve, challenge, whimper, growl, nuzzle, lick, etc.); unlimited, but repeat signs on the same partner pay out less mood  
✦ `/weep`; silverrush only: release grief alone at the weep stone (unlimited; each repeat soothes less; also eases the `grief_melancholy` condition)  
✦ **birthdays** are celebrated automatically in the sunrise den news whenever a wolf crosses a full year (12 moons)  
✦ optional **rp ambience**: set `RP_AMBIENCE_CHANNEL_IDS` in `.env` for sunrise season/weather/moon posts on rollover

## in discord

✦ `/help topic:<category>`; full command guide  
✦ `/help topic:credits`; inspiration sources  
✦ `/terms`; wolf tongue glossary

## credits

howlbert is not affiliated with these projects; they inspired features and feel:

✦ [wolvden](https://www.wolvden.com/) ; wolf sim and pack life  
✦ [warrior cats](https://warriors.fandom.com/wiki/Main_Page) ; den life, herbs, cough lore  
✦ [the whispering wild](https://www.roblox.com/games/1625049462/The-Whispering-Wild-Wolf-RPG) ; wolf rpg on roblox  
✦ [unbelievaboat](https://unbelievaboat.com/) ; economy bot patterns  

rpg rules and herbs follow **basil's wolf ttrpg** homebrew.
