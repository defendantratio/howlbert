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
✦ **quests** progress from hunts, patrols, deposits, etc.; turn in with `/quest action:complete`  
✦ **mood / hunger / thirst** decay each sunrise; low stats block hunts and add exhaustion  
✦ **basil's rules** for attributes, skill checks, combat, herbs, disease, and pups; use `/help` in discord for the player guide

## commands

discord caps slash commands at 100; howlbert uses **hub commands** with an `action:` parameter. type `/` and pick a hub; discord autocompletes actions. full guide: `/help topic:overview`.

### hub commands


| hub          | actions (examples)                                                                                            |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| `/bones`     | `balance`, `daily`, `hunt`, `work`, `crime`, `shop`, `buy`, `sell`, `inventory`, `use`, `give`, `leaderboard` |
| `/field`     | `forage`, `verge`, `scavenge`, `track`, `fishing`, `sniff`                                                    |
| `/hoarding`  | `hoard`, `gift`, `shred`                                                                                      |
| `/playpen`   | `toys`, `play`, `playall`, `toystore`, `socialize`, `groom`                                                   |
| `/packlife`  | `feedall`, `drinkall`, `howl`                                                                                 |
| `/howl`      | pack howl (standalone; once per sunrise)                                                                      |
| `/world`     | `time`, `weather`, `forecast`, `cooldowns`                                                                    |
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
| `/vitals`    | `condition`, `rest`                                                                                           |


### standalone commands


| command                                                | what it does                                           |
| ------------------------------------------------------ | ------------------------------------------------------ |
| `/register`                                            | create a wolf; great pack, loner, or rogue             |
| `/profile`                                             | wolf sheet (`sheet:true` for lore; paginates if large) |
| `/wolves` `/switchwolf` `/rename` `/setfaction`        | multi-wolf and faction                                 |
| `/prey` `/eat` `/drink` `/salvage` `/preypile` `/bury` | prey hoard and survival                                |
| `/explore venture`                                     | dig, scent, investigate                                |
| `/scout rescout` `/survey` `/trail`                    | scout field commands                                   |
| `/pack …`                                              | treasury, stash, tax, territory, wars, unity           |
| `/combat …`                                            | initiative combat; `/combat encounter` for ambushes    |
| `/hazard`                                              | weather opposed roll                                   |
| `/medic action:quarantine`                               | isolate sick wolves (or `action:quarantine`)           |
| `/trade`                                               | player item and bone trades                            |
| `/patron` `/redeem`                                    | boosts, invites, supporter perks                       |
| `/help topic:<category>`                               | full command guide                                     |
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
| skill checks         | `/rpg action:roll`                                                             |
| combat               | `/combat start`, `join`, `begin`, `attack`, `status`, `end`                    |
| herbs                | `/field action:forage`, `action:verge`, `/herbs`, `/medic action:treat`        |
| conditions           | `/vitals action:condition`, `action:rest`; disease progresses each rollover    |
| death saves          | `/medic action:deathsaves`, `action:stabilize` at 0 hp                         |
| weather hazards      | `/hazard`                                                                      |
| xp                   | `/advance action:view`, `action:spend`                                         |
| mating and pups      | `/courtship`, `/pupcare`                                                       |


**hp** = 10 + str + survival (con score). **pack unity** (0–10) rises from quests and falls from wars. **lone wolves** cannot use `/pack`. **rogues** cannot draw `/bones action:daily`.

**herb compendium:** 90+ plants. `/field action:forage` in territory or `action:verge` at the thunderpath edge; `/herbs action:guide` for the guide.

illness blends wolvden / warriors fantasy with wolf-canid ecology. cough, distemper, rot-lung (mistmoor), milk-fever, shaking-sickness, chronic conditions, mental illness, and restricted poison herbs are all wired to real mechanics. see `/help topic:vitals` in discord for the full list.

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

legacy grows from **completing quests** and `**/prestige action:retire`**. bone bonus is permanent on hunts and daily.


| tier | name             | total bone bonus |
| ---- | ---------------- | ---------------- |
| 1    | the named        | +5%              |
| 2    | the story-weaver | +15%             |
| 3    | the claimed      | +30%             |
| 7    | the sunderer     | +145%            |


`/prestige action:require` shows exact thresholds.

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
