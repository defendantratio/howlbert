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
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*howlbert*" } | Stop-Process
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
✦ **mood / hunger / thirst** decay each sunrise; low stats block hunts and add exhaustion  
✦ **genetic conditions** (blindness, deafness, muteness, and more) are inherited or rolled at birth; some block howls, hunts, or perception  
✦ **cat clans**: trade meat and forage, and form pacts via `/pack pact` (see `docs/CAT_CLANS.md`)  
✦ **forage food** (berries, windfall fruit, roots, greens) drops from `/field forage` and `scavenge`; it ripens then overripens, just like meat rots  
✦ **passive scavenge**: unfed wolves forage a little each sunrise so neglect bites without instantly starving the den  
✦ **death log**: `/wolfadmin deaths` records cause of death each rollover  
✦ **admin tooling**: `/wolfadmin assign` registers a wolf to a player (paste sheets directly in chat); `/wolfadmin arrival` posts the arrival/birth scene for an already-registered wolf so it grants its long-term trait properly; `/wolfadmin dormant` exempts admin-held NPC wolves from vitals decay until claimed; `/wolfadmin execute` marks a wolf dead with a lore-flavored cause  
✦ **pack-specific plot quests**: each great pack has its own gated board quest tied to its lore (e.g. Silverrush's dam sabotage, Greyspire's mining-camp raid)  
✦ **basil's rules** for attributes, skill checks, combat, herbs, disease, and pups; use `/help` in discord for the player guide

## realism mechanics

howlbert leans toward measurable, granular wolf-ecology effects over flavor text — every system below changes a number, not just a description.

✦ **breeding season**: courtship and bonding work year-round, but conception only succeeds in **winter** — `/courtship action:mate` outside winter forms a bond with no pregnancy roll. rival challenges for mating access are also winter-only  
✦ **pregnancy costs food**: pregnant wolves burn extra hunger/thirst each sunrise, and hunt/fish/scavenge yield drops **−10%** in early pregnancy, **−20%** mid-to-late; the final third blocks strenuous activity outright. nursing mothers burn extra hunger/thirst per pup  
✦ **injuries cost yield, not just combat**: non-blocking injuries (sprained leg, punctured paw, concussion, deep gash, infected wound, torn claw, broken tooth, torn ear) reduce hunt/fish/scavenge yield, stacking up to **−50%**. severe injuries (fractured rib, spinal injury, paralysis) still block field commands outright  
✦ **injury at the den vs. in the field**: patrolling while hurt earns a standing **bonus** (up to +2) for putting the pack first — but if the patrol goes wrong (spotted, ambushed) an injured wolf takes **extra** standing loss on top, since the injury is why they couldn't get away clean  
✦ **disease needs real contact**: den-spread illness at sunrise checks whether a wolf was actually in the field that day — wolves who hunted, patrolled, scouted, or tracked have **−50%** exposure to respiratory disease and **−25%** to contact disease versus one who stayed denbound all day. trail/border encounters in `/field action:sniff` can also pass illness directly, same as `/playpen action:socialize` and `/explore`  
✦ **long-term marks aren't just injuries**: the `long_term_injuries` system also stores permanent non-injury traits like arrival choices (bold/quiet/wary) and birth circumstances — a +1 skill bonus that follows a wolf for life

## commands

discord caps slash commands at 100; howlbert uses **hub commands** with an `action:` parameter. type `/` and pick a hub; discord autocompletes actions. full guide: `/help topic:overview`.

### hub commands


| hub          | actions (examples)                                                                                            |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| `/bones`     | `balance`, `daily`, `hunt`, `work`, `crime`, `shop`, `buy`, `sell`, `inventory`, `use`, `give`, `leaderboard` |
| `/field`     | `forage`, `verge`, `scavenge`, `track`, `fishing`, `sniff`                                                    |
| `/hoarding`  | `hoard`, `gift`, `shred`                                                                                      |
| `/playpen`   | `toys`, `play`, `playall`, `toystore`, `socialize`, `groom`                                                   |
| `/raccoon`   | `sell`, `buy`, `offer`                                                                                        |
| `/packlife`  | `feedall`, `drinkall`, `howl`                                                                                 |
| `/howl`      | pack howl (standalone; once per sunrise)                                                                      |
| `/sign`      | body/visual language: `alert`, `rally`, `play`, `submit`, `soothe`, `threaten`, `freeze`, `track`, `greet`, `grieve`, `challenge`, `read` (unlimited; repeat signs on the same partner pay out less mood, down to 20%) |
| `/world`     | `time`, `weather`, `forecast`, `cooldowns`, `plot`, `hazard`, `travel`, `encounter`, `omen`                   |
| `/garden`    | `plots`, `seeds`, `plant`, `tend`, `harvest`, `clear`, `buy`, `guide` (grow your own herbs from seed)         |
| `/quest`     | `board`, `daily`, `accept`, `progress`, `complete`, `abandon`, `log`                                          |
| `/role`      | `quests`, `event`, `prophecy`                                                                         |
| `/prestige`  | `view`, `require`, `bonus`, `legacy`, `retire`, `halloffame`                                                  |
| `/courtship` | `court`, `mate`, `pregnancy`                                                                                  |
| `/pupcare`   | `birth`, `feed`, `list`, `save`, `adopt`                                                                      |
| `/wolfset`   | `birthsex`, `sexuality`, `mawbelief`, `size` (combat build)                                                    |
| `/advance`   | `view`, `spend` (attribute, **skill trait**, role feature)                                  |
| `/medic`     | `deathsaves`, `stabilize`, `surgery`, `treat`, `checkup`, `sacred`, `ritual`, `naming`, `lay_to_rest`, `swim`, `quarantine`, `observe` |
| `/herbs`     | `bag`, `guide`, `prepare`, `dryall`, `store`, `turnin`                                                      |
| `/rpg`       | `roll`, `setstats`, `delete`                                                                                  |
| `/skills`    | catalogued checks (`category:` · `check:` · `group:` · `helper:` · `opponent:`)                         |
| `/skilllist` | reference DCs by category                                                                                     |
| `/vitals`    | `condition`, `rest`                                                                                           |


### standalone commands


| command                                                | what it does                                           |
| ------------------------------------------------------ | ------------------------------------------------------ |
| `/register`                                            | create a wolf; great pack, loner, or rogue             |
| `/profile`                                             | wolf sheet (`sheet:true` for lore; paginates if large) |
| `/character`                                           | set your wolf's pronouns, bio, birthday, avatar, ref image |
| `/family`                                              | family tree / relationship web rendered as a diagram   |
| `/scene`                                               | RP scenes in threads: `start`, `join`, `leave`, `here`, `poke`, `end` (pinned roster; auto-join on post) |
| `/say` `/whisper`                                      | quick IC lines and styled IC DMs (no message content intent needed) |
| `/location`                                            | set, clear, or show your wolf's in-character whereabouts |
| `/journal`                                             | read-only automatic life timeline (birth, pack, bonds, blooding, death, rites) |
| `/rite`                                                | den ceremonies: `naming`, `blooding`, `mourning` |
| `/npc`                                                 | server NPC registry (`add`/`remove` admin); `/npc say`, `/npc sign` (real mood/standing effects on the target's wolf), `/npc narrate` (admin; no named speaker) |
| `/weep`                                                 | silverrush only, once per sunrise: release grief at the weep stone |
| `/proxy`                                               | speak in-character as your wolves; import from Tupperbox |
| `/wolves` `/switchwolf` `/rename` `/setfaction`        | multi-wolf and faction                                 |
| `/prey` `/eat` `/drink` `/salvage` `/preypile` `/bury` | prey hoard and survival                                |
| `/explore venture`                                     | dig, scent, investigate                                |
| `/scout rescout` `/survey` `/trail`                    | scout field commands                                   |
| `/pack …`                                              | treasury, stash, tax, territory, wars, unity, `pact` (cat clans), `share`/`aid`, `tradepack`, `brokenrite` |
| `/bonds`                                               | friendships, rivalries, kin, mentors, found families   |
| `/sign`                                                | body/visual language; mute wolves rally without a howl; unlimited, diminishing returns on repeat partners |
| `/combat …`                                            | initiative combat; `/combat encounter` for ambushes    |
| `/hazard`                                              | weather opposed roll                                   |
| `/medic action:quarantine`                               | isolate sick wolves (or `action:quarantine`)           |
| `/trade`                                               | player item and bone trades                            |
| `/patron` `/redeem`                                    | boosts, invites, supporter perks                       |
| `/help topic:<category>`                               | full command guide                                     |
| `/skills` `/skilllist`                                 | basil's skill checks and DC reference                    |
| `/ping`                                                | bot health check                                       |


### collaborative pack activities

call the den with `collaborate:true`; **2–4 wolves** join via buttons, then the caller sets out.


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
| mating and pups      | `/courtship` (court year-round; **conception only in winter**), `/pupcare`    |


**hp** = 10 + str + survival (con score). **pack unity** (0–10) rises from quests and falls from wars. **lone wolves** cannot use `/pack`. **rogues** cannot draw `/bones action:daily`.

**herb compendium:** 90+ plants. `/field action:forage` in territory or `action:verge` at the thunderpath edge; `/herbs action:guide` for the guide.

**herb gardens:** grow your own with `/garden` — buy/find seeds (`seeds`, `buy`), `plant`, `tend` daily, then `harvest`; `/garden guide` lists each plant's growing conditions (light, water, season).

illness blends wolvden / warriors fantasy with wolf-canid ecology. cough, distemper, rot-lung (mistmoor), river rot (silverrush; sewage-tainted water, no known cure), milk-fever, shaking-sickness, chronic conditions, mental illness, and restricted poison herbs are all wired to real mechanics. see `/help topic:profile` in discord for the full list.

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

## prestige (tiers 0–7)

legacy grows from **completing quests** and `/prestige action:retire`. bone bonus is permanent on hunts and daily.


| tier | name             | total bone bonus |
| ---- | ---------------- | ---------------- |
| 1    | the named        | +5%              |
| 2    | the story-weaver | +15%             |
| 3    | the claimed      | +30%             |
| 7    | the sunderer     | +145%            |


`/prestige action:require` shows exact thresholds.

## roleplay & proxying

speak in-character as your wolves, tupperbox-style — plus slash tools that work without reading typed messages.

✦ `/character` sets a wolf's **pronouns, bio, birthday, avatar, and ref image** (shown on `/profile`)  
✦ `/proxy set tag:H:text` registers a proxy tag; typing `H:hello` reposts as that wolf via webhook and deletes your message  
✦ `/proxy avatar`, `/proxy list`, `/proxy clear`, `/proxy autoproxy` manage proxies; autoproxy posts all untagged messages as one wolf (`\` escapes a single message)  
✦ `/proxy import` migrates from **Tupperbox** (DM Tupperbox `tul!export`) or **PluralKit** exports, auto-linking to wolves by name  
✦ proxy **OOC markers**: wrap `((out of character))` or start a line with `//`; IC text posts as the wolf, OOC shows in the footer  
✦ `/say` and `/whisper` post one-line IC speech without the message content intent  
✦ `/location set` · `clear` · `show` — IC whereabouts on `/profile` and proxy footers  
✦ `/journal` reads your wolf's **automatic** timeline (register, birth, pack moves, bonds, blooding, death, rites); no player editing  
✦ `/scene start` opens a roleplay **thread** with a **pinned living roster**; posting auto-joins you (`/scene poke` pings the scene)  
✦ `/rite naming` · `blooding` · `mourning` — pack ceremonies in-channel  
✦ `/npc add` · `remove` · `list` (admin); `/npc say`, `/npc sign` (real effects on a player's wolf), `/npc narrate` (admin; no named speaker)  
✦ `/family` — relationship web rendered as a diagram, with the focus wolf's proxy avatar  
✦ `/sign` — body language when a wolf can't howl (mute rally, alert, play, freeze, track, greet, grieve, challenge, etc.); unlimited, but repeat signs on the same partner pay out less mood  
✦ `/weep` — silverrush only, once per sunrise: release grief alone at the weep stone (also eases the `grief_melancholy` condition)  
✦ **birthdays** are celebrated automatically in the sunrise den news whenever a wolf crosses a full year (12 moons)  
✦ optional **RP ambience**: set `RP_AMBIENCE_CHANNEL_IDS` in `.env` for sunrise season/weather/moon posts on rollover

**requirements:** typed proxy tags need the **Message Content Intent** in the Discord Developer Portal, plus **Manage Webhooks** + **Manage Messages** in RP channels. scenes need **Create Public Threads**.

## in discord

✦ `/help topic:<category>` — full command guide  
✦ `/credits` — inspiration sources  
✦ `/terms` — wolf tongue glossary

## credits

howlbert is not affiliated with these projects; they inspired features and feel:

✦ [wolvden](https://www.wolvden.com/) — wolf sim and pack life  
✦ [warrior cats](https://warriors.fandom.com/wiki/Main_Page) — den life, herbs, cough lore  
✦ [the whispering wild](https://www.roblox.com/games/1625049462/The-Whispering-Wild-Wolf-RPG) — wolf rpg on roblox  
✦ [unbelievaboat](https://unbelievaboat.com/) — economy bot patterns  

rpg rules and herbs follow **basil's wolf ttrpg** homebrew.
