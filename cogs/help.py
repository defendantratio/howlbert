import discord

from discord import app_commands

from discord.ext import commands



from config import BOT_DISPLAY_NAME

from utils.embeds import EMBED_COLOR, embed_footer, howlbert_embed



CREDITS_TEXT = (

    f"**{BOT_DISPLAY_NAME}** was built for wolf RP on Discord.\n\n"

    "**Inspired by** (not affiliated):\n"

    "• [Wolvden](https://www.wolvden.com/); wolf sim & pack life\n"

    "• [Warrior Cats](https://warriors.fandom.com/wiki/Main_Page); den life, herbs, and cough lore\n"

    "• [The Whispering Wild](https://www.roblox.com/games/1625049462/The-Whispering-Wild-Wolf-RPG); wolf RPG on Roblox\n"

    "• [UnbelievaBoat](https://unbelievaboat.com/); economy & shop bots\n"

    "• Quest Bot; quest board workflows\n\n"

    "Rules & herbs follow **Basil's wolf TTRPG** homebrew."

)



HELP_TOPICS = {

    "overview": (

        f"{BOT_DISPLAY_NAME}; Wolf RP",

        f"**{BOT_DISPLAY_NAME}** tracks your wolf, bones, quests, pack, and legacy across the wild.\n\n"

        "**Quick start**\n"

        "1. `/register`; create your wolf; pick a Great Pack or walk as a lone wolf\n"

        "2. `/bones action:hunt` and `/bones action:work`; earn 🦴 bones (`/bones action:daily` draws from pack treasury if you're in a Great Pack)\n"

        "3. `/quest action:board`; accept den board quests\n"

        "4. `/profile`; view your sheet (`sheet:true` for lore)\n"

        "5. `/terms` or `/help topic:terms`; wolf tongue glossary (fresh-kill, Newgrowth, insults)\n\n"

        "`/ping`; bot health check\n\n"

        "Use `/help topic:getting-started` for your first week.\n"

        "Use `/help topic:<category>` for more.\n"

        "Type `/` in chat; Discord autocompletes all commands.",

    ),

    "getting-started": (

        "Getting started",

        "**Day 1**; `/register` → `/bones action:hunt` or `action:work` → `/profile` → `/world action:cooldowns`\n"

        "**Pack life**; `/bones action:daily` · `/pack treasury` · `/playpen action:socialize` · `/pack stash`\n"

        "**Juveniles (6-24 moons)**; hunt for practice; first kill earns **blooding**; then `/role action:event`\n"

        "**Life**; `/courtship action:court` → `action:mate` (spring) · `action:pregnancy` · `/pupcare action:birth names:…` · `action:feed` · `action:save` · `action:list`\n"

        "**Adopt**; bonded mates use `/pupcare action:adopt`; other players accept via button or `respond:`\n"

        "**Survival**; `/eat` from `/prey`, `/drink` at the creek; watch hunger/thirst on `/vitals action:condition`; `/medic action:deathsaves` at 0 HP\n"

        "**Help**; `/help topic:hunting` · `life` · `pack` · `world`",

    ),

    "profile": (

        "Profile",

        "`/register`; create wolf; optional **starting_age** and **genetic** (blind, half_blind, deaf, missing_leg, no_tail, …)\n"

        "`/wolves`; list your wolves\n"

        "`/switchwolf`; change active wolf\n"

        "`/setfaction`; join/switch Great Packs or go loner (🦴 500 to switch between packs)\n"

        "`/rename`; change wolf name\n"

        "`/profile sheet:true`; view wolf sheet with lore (attributes, HP, skills)\n"

        "`/rpg action:setstats`; assign attributes within role range\n"

        "Roles include **Pup**, **Juvenile**, apprentice ranks (**Hunter/Medic/Scout/Diplomat/Caretaker/Forager Apprentice**), and full adult roles.\n"

        "Pups cannot hunt or mate; juveniles can hunt but not mate. **Apprentice** roles are valid from juvenile age; stepping stones to full rank.\n"

        "Use `/help topic:roles` for mechanical role perks.\n"

        "Life stages: **under 6 moons** (pup) · **6-24 moons** (juvenile) · **24-59 moons** (adult) · "

        "**60+ moons** (elder).\n"

        "Each `/rollover` is **one sunrise** (hunger/thirst decay, long rest). With **lunar birth aging** "

        "(default), wolves gain **+1 moon** only when the real sky matches their birth phase "

        "(**new**, **half**, or **full**). `/world action:time` shows tonight's moon.\n"

        "Set `AUTO_ROLLOVER_ENABLED=true` in `.env` for a daily sunrise at `ROLLOVER_HOUR` "

        "in `ROLLOVER_TIMEZONE` (default US Eastern). If the bot was offline, missed sunrises "

        "catch up on the next startup (up to 31 days).\n"

        "Hunger **−12** and thirst **−14** each sunrise; below **30** each adds **+1 exhaustion** (both low = +2). "

        "Low mood below **30** also adds **+1 exhaustion**. Exhaustion **6 = death**. "

        "At **0** hunger or thirst, wolves **collapse** into dying.\n"

        "Wolves at **120 moons** pass from **old age** on the next sunrise.\n"

        "**Standing** can go negative; at **−5** you are cast out as a **loner** "

        "(an **Alpha** at **−5** triggers the **Rite of the Broken Canine** instead; `/pack brokenrite`).\n"

        "`/vitals action:condition`; injuries, disease, exhaustion, mood, hunger & thirst (bleeding/infection progress each `/rollover`); **3-step treatment plan** embed\n"

        "**Disease**; Wolvden illnesses + Warriors cough stages (`/vitals action:condition` · `/medic action:treat`):\n"

        "• **Whitecough** = **Green-cough (Mild)** (`cough:mild`); see `/terms`\n"

        "• **Cough** (green/white → black → red); rare **Green-cough** mold from rotten meat; **14%** den spread/rollover\n"

        "• **Diarrhea**; rotting meat or rolling in filth (`/playpen`, awkward `/playpen action:socialize`, bad explore)\n"

        "• **Influenza** (50% den spread); failed blizzard, freezing rain, or deep snow `/hazard`\n"

        "• **Fleas / hepatitis / distemper**; carrion and `/field action:scavenge`; **mange**; mangy den sites\n"

        "• **Pox**; den filth; hits pups harder; spreads by den contact\n"

        "• **Distemper**; sick canid carrion, hearth-hound bites, den contact\n"

        "• **Yellowcough**; epidemic plague; **45%** den spread; lethal without **mullein** or **lungwort**\n"

        "• **Redscratch**; mating STI; blocks conception; **lavender** or **chervil**\n"

        "• **Rot-Lung** (Mistmoor); fever → wheeze → necrosis; **42%** den spread; "

        "**marsh-mallow**, **feverfew**, **mullein**, **lungwort**, or **belly-rip fungus** (necrosis)\n"

        "• **Milk-Fever**; eclampsia 1-3 sunrises after `/pupcare action:birth` (peak nursing); **parsley**, **saffron**, or **feverfew**\n"

        "• **Nursing**; mothers **`/pupcare action:feed`** each sunrise until pups reach **6 moons**; **honey** in inventory auto-sweetens the meal (**+10** hunger); unfed pups lose extra hunger at `/rollover`\n"

        "• **Lone mothers**; no pack caretaker; nurse daily or **`/medic action:treat`** with **honey** on the pup\n"

        "• **Shaking-Sickness** (Mistmoor); Belly-Rip bad water; tremors → hemorrhage; **sweet sedge**, **yarrow**, or **cobwebs**\n"

        "**Chronic illness**; progressive, often elder-onset (`/vitals action:condition` · `/medic action:treat`):\n"

        "• **Rabies**; feral hearth-hound / wolf bites; incubation → frenzy → death; **boneset** or **goldenrod** slow early stages (no cure)\n"

        "• **Wasting sickness**; carrion or old age; hunger drain → cachexia; **borage** or **parsley**\n"

        "• **Growth-sickness**; rare in elders who outlive the wild; hidden lump → spreading; **mullein** or **lungwort**\n"

        "**Paralysis**; **spinal injury** (temporary, spine bite) or **paralyzed** (permanent); "

        "comfrey + bindweed splint; blocks hunt/patrol/explore\n"

        "**Mental illness**; insomnia, anxiety, grief, delirium, pack madness, obsession, night terrors, chronic stress, eating distress; "

        "calming herbs (**chamomile**, **valerian**, **poppy**, **lavender**, **passionflower**, **skullcap**) have real cure/buff paths via `/medic action:treat`\n"

        "**Mental degeneration**; dementia (forgetful → lost) and feral shift → **Mind-Fracture** (unsentient; **RP fantasy**); "

        "**chamomile** or **dried skullcap** may slow decline; unsentient wolves keep `/vitals`, `/eat`, `/drink` but lose field commands\n"

        "**Restricted herbs**; poison plants (bloodroot, foxglove, wolfsbane, …): **−4** if caught using; hoarding risks **−3 if caught**; `/herbs action:turnin` (**+1 standing**, **10🦴** from pack treasury when funded)\n"

        "Illnesses can pass during **`/mate`** (close contact): respiratory diseases most easily, "

        "then fleas/mange/pox; diarrhea at low risk. Den rollover and groom/socialize still apply.\n"

        "Groom & socialize can pass illness immediately; packmates catch it each `/rollover`.\n"

        "`/medic action:quarantine`; Medics, Alpha, or Advisor isolate sick wolves (blocks spread & activities)\n"

        "`/vitals action:rest`; short rest (comfrey heal, 3/sunrise); long rest is automatic each rollover\n"

        "`/medic action:treat herb:`; inventory herb **or** forage `stack:ID` (**Medics**: unlimited; **`patient:`** treats packmate from your bag)\n"

        "`/herbs action:store mode:`; pack herb store — anyone: **deposit** / **depositall** "
        "(forage bag + inventory); Medics/Foragers: **withdraw**\n"

        "`/herbs action:turnin`; any wolf: hand **restricted poison** herbs to the healers' den (**+1 standing**)\n"

        "`/medic action:ritual` · `action:naming` · `action:lay_to_rest` · `action:swim`; spirit rites & swim therapy\n"

        "`/herbs action:prepare`; dry / poultice / tonic / decoction on a forage stack or inventory herb\n"

        "`/herbs action:dryall`; dry every fresh forage stack, `herb_*` in `/inventory`, and fresh den store stacks\n"

        "`/herbs action:bag`; fresh & prepared herbs (foraged; rot if not dried)\n"

        "`/herbs action:guide`; paginated herb guide (gathering, effects, treat keys)\n"

        "`/rpg action:delete confirm:DELETE`; remove active wolf (keeps prestige)",

    ),

    "economy": (

        "Economy",

        "`/bones action:balance`; your bones\n"

        "`/bones action:daily`; sunrise stipend from **pack treasury** (25🦴 base + prestige; loners ineligible)\n"

        "`/bones action:give`; gift bones (`@wolf` or `own_wolf:`)\n"

        "`/bones action:giveitem`; gift herbs or shop items from `/bones action:inventory`\n"

        "`/trade offer`; propose items/bones; recipient accepts or declines\n"

        "`/trade cancel`; cancel your pending offers\n"

        "`/bones action:leaderboard`; richest wolves\n"

        "`/bones action:shop` · `action:buy` · `action:sell` · `action:inventory` · `action:use`; trading post\n"

        "`/bones action:sell item:stack:ID`; sell a forage herb stack for bones (rarity-based; poison herbs use turn-in)\n"

        "`/bones action:work` · `action:crime`; earn bones once per rollover\n"

        "Shop: utility items plus **prey carcasses** (`prey_vole`, `prey_hare`, …) and **toys** "

        "(`toy_bone`, `toy_feather`, …); carcasses go to `/prey`, toys to `/playpen action:toys`.\n"

        "Also: **Vitality Salve** (550🦴) · **Lucky Tooth** · **Herb Bundle** · **Prey Bundle** · **Den Charm** · "

        "**Rabbit Pelt** · **An Extra Paw** · **Safe Roll** · food/toys as `prey_*` / `toy_*` keys\n"

        "**Vitality Salve**; `/pupcare action:save name:<pup>` on the **same sunrise** a lethal-at-birth pup is born\n"

        "**Revive** ($35 Ko-fi); same wolf back from death · **Reincarnation** ($28 Ko-fi): "

        "new name, juvenile age, keep stats\n"

        "Retire a wolf: `/rpg action:delete confirm:DELETE`",

    ),

    "hunting": (

        "Hunting & foraging",

        "All once per rollover. Weather and **season** affect bone payouts; check `/world action:weather` and `action:time`.\n\n"

        "`/bones action:hunt`; main hunt; carcass goes to **prey hoard** (`/prey`)\n"

        "`/bones action:hunt collaborate:true`; **pack hunt**: call the den, packmates join via buttons, set out together "

        f"(+bones per extra wolf; large prey & ambushes possible; party fights together; fresh-kill to `/preypile`)\n"

        "`/scout survey collaborate:true`; **pack patrol**: scouts join via buttons, stealth sweep together "

        f"(+bones per extra scout; ambushes possible; counts as survey)\n"

        "`/scout trail collaborate:true`; **pack trail**: scouts join via buttons, tracking sweep together "

        f"(+bones per extra scout; prey to caller; ambushes possible; counts as trail)\n"

        "`/pack patrol collaborate:true`; **war patrol**: packmates join during a territory war "

        f"(combined war points; counts as your daily patrol)\n"

        "Juveniles (6-24 moons) earn **blooding** on first successful hunt (+8 mood, +1 standing)\n"

        "`/field action:track`; trail-age Tracking DC (fresh DC 8 → faint DC 25); weather affects scent\n"

        "`/field action:fishing` · `action:scavenge`; more carcasses\n"

        "`/prey`; view hoard · `/eat` · `/drink` (hourly) · `/salvage` rotting meat · `/field action:sniff` once per sunrise\n"

        "Combat kills (coyotes, cats, hearth-hounds, …) go to your hoard too. **Wolf carcasses** are edible; "

        "private `/eat` always costs mood and may get you caught; `/preypile`, `/pack stash deposit`, "

        "or serving wolf meat at `/packlife feedall` **always** costs standing.\n"

        "`/preypile`; lay a **today's** fresh carcass at the den cache for the pack\n"

        "`/field action:forage`; gather herbs in pack territory (**Foragers** unlimited; harder in Leaf-bare; crit → rare herb + season blurb)\n"

        "`/field action:compendium`; read-only herb browser (same data as `/herbs action:guide`)\n"

        "`/field action:verge`; **Thunderpath** or **Twoleg fence-line** herbs (once/sunrise; riskier)\n"

        "`/world action:cooldowns`; what's ready this sunrise",

    ),

    "wolvden": (

        "Wolvden-style",

        "Inspired by [Wolvden](https://www.wolvden.com/); explore, hoard, mood, and trade.\n\n"

        "**Prey hoard**; `/prey` `/eat` `/drink` `/preypile` `/salvage` `/bury` · **hunger & thirst** slip each sunrise\n"

        "**Hoard**; `/hoarding action:hoard` · `action:shred` toys → remnants\n"

        "**Explore**; `/explore venture` (dig · follow · investigate; **Scouts: unlimited**)\n"

        "**Scout**; `/scout rescout` · `/scout survey` · `/scout trail` · `collaborate:true` on survey/trail for pack parties\n"

        "**Amusement**; `/playpen action:toys` · `action:play` · `action:toystore` · `action:playall` (Alpha) · `/hoarding action:gift`\n"

        "**Pack**; `/playpen action:socialize` · `action:groom` · `/pack stash` · `/packlife action:feedall` · `action:drinkall` (Alpha)\n"

        "**Bonds**; `/bonds` friendships, rivalries, kin, mentors · found families (`/playpen action:socialize` & `action:groom` deepen ties)\n"

        "**Raccoon**; `/raccoon sell` · `/raccoon buy` bundles · `/raccoon offer` acorn\n"

        "**Creek**; `/drink` once per hour (+thirst, +hunger, small heal)\n"

        "**Survival**; at **0** hunger or thirst wolves **collapse** (death saves via `/medic action:deathsaves`)\n"

        "**Sniff**; `/field action:sniff` wind-read once per sunrise\n"

        "**Patron**; `/patron` invites, boost & donor status · Kickstarter backer badge · `/redeem` gift codes",

    ),

    "unbelievaboat": (

        "UnbelievaBoat-style economy",

        "Inspired by [UnbelievaBoat](https://unbelievaboat.com/) shop bots: bones, shop, sell-back, and daily payouts.\n\n"

        "**Balance**; `/bones action:balance` · `action:leaderboard`\n"

        "**Income**; `action:hunt` · `action:work` · `action:crime` (once per sunrise each)\n"

        "**Pack pay**; `/bones action:daily` draws from **pack treasury** (Great Pack members only)\n"

        "**Shop**; `action:shop` · `action:buy` prey (`prey_vole`) and toys (`toy_bone`) into `/prey` and `/playpen action:toys`\n"

        "**Sell**; `action:sell item:herb_arnica` (inventory herbs) or **`item:stack:ID`** (forage bag stacks)\n"

        "**Poison bounty**; `/herbs action:turnin` pays **10🦴** from treasury + standing (restricted herbs only)\n"

        "**Trade**; `/trade offer` · `/bones action:give` · `action:giveitem`\n"

        "_Not affiliated with UnbelievaBoat; similar command feel only._",

    ),

    "whispering": (

        "Whispering Wild",

        "Inspired by [The Whispering Wild](https://www.roblox.com/games/1625049462/The-Whispering-Wild-Wolf-RPG) "

        "wolf RPG on Roblox; fog spirits and swamp unease.\n\n"

        "**Fog & storm**; `/field action:sniff` in **fog**, **rain**, or **storm** may bring spirit whispers\n"

        "**Mistmoor & Drown-Sick**; higher chance of **anxiety** from whispers on the wind\n"
        "**Spirit curse**; rare in fog if whispers turn cruel; **−1** spiritual checks until broken "
        "(wolfsbane, swamp milkweed, cleansing ritual, `/skills` spirit_cleanse)\n"

        "**Pack madness**; mental illness from paranoia and den stress; treat via calming herbs\n"

        "**Whispering Rot**; Guard role event in Mistmoor fog (betrayal temptation)\n"

        "_Not affiliated with the Roblox game; shared wolf-RP mood only._",

    ),

    "quests": (

        "Quests",

        "`/quest action:board`; den board (accept with buttons)\n"

        "`/quest action:daily`; easy / medium / hard (auto each rollover)\n"

        "`/quest action:accept`; take a quest\n"

        "`/quest action:progress`; active objectives\n"

        "`/quest action:complete`; turn in finished quest\n"

        "`/quest action:abandon`; drop a quest\n"

        "`/quest action:log`; completed history\n\n"

        "Objectives track automatically when you hunt, patrol, deposit, explore, etc.\n"

        "`/role action:quests`; quests only your **role** can take\n"

        "`/role action:event`; once-per-rollover role scene (skill check + reward)",

    ),

    "roles": (

        "Role features",

        "Your **role** on `/profile` grants mechanical perks. Purchased extras show as **Bonus feature**.\n\n"

        "**Alpha**; **Commanding Howl**: `/howl` grants packmates advantage on their next "

        "skill check or attack.\n"

        "**Advisor (Beta)**; **Blood Oath**: advantage on one Charisma check per sunrise "

        "(role events, forage, `/rpg action:roll`, cat pacts, etc.).\n"

        "**Guard**; **Defender's Resolve**: attackers have disadvantage when striking anyone else in the same combat.\n"

        "**Hunter**; **Killer's Instinct**: +1d6 damage vs prone/pinned foes; **3 hunts per sunrise**.\n"

        "**Medic**; **Green Tongue**: unlimited `/medic action:treat` and comfrey heals per sunrise.\n"

        "**Scout**; **Unseen Paw**: hidden in fog/mist on successful `/scout survey` or `/field action:sniff`; "

        "attackers have disadvantage against hidden scouts in combat.\n"

        "**Forager**; **Nose of the Land**: auto-herb each sunrise; unlimited forage.\n"

        "**Caretaker**; **Soothing Lick**: `/playpen action:groom` clears **distressed** and gives **+12 mood** when target mood is below 30.\n"

        "**Diplomat**; **Silver Tongue**: `/rpg action:roll use_role_reroll:true` on failed Charisma checks.\n"

        "**Elder**; **Wisdom of Years**: `/rpg action:roll use_role_reroll:true` on any failed skill check.\n"

        "**Drown-Sick**; +2 Perception in fog/swamp; −35% hunt bones; `/role action:prophecy`.\n"

        "**Rogue**; no `/bones action:daily`; Stealth advantage crossing borders.\n"

        "**Bog-Born**; Survival/Herblore advantage in Mistmoor swamp.\n\n"

        "Spend XP at `/advance action:spend purchase:role_feature` to **request** a bonus role feature "

        "(10 XP; **requires admin approval** via `/wolfadmin approvefeature`).",

    ),

    "lore": (

        "Maw faith & oracles",

        "All Four Packs share the faith of **the Maw**; the living ancestor whose body is the land.\n\n"

        "`/role action:prophecy`; Drown-Sick only: draw a cryptic prophecy (once per rollover)\n\n"

        "_When the Teeth drink the Tears, when the Fur chokes the Belly…_",

    ),

    "pack": (

        "Pack & warfare",

        "Your **Great Pack**; Greyspire, Mistmoor, Thistlehide, or Silverrush.\n"

        "All wolves in the same Great Pack share treasury, tax, wars, and unity.\n"

        "**Lone wolves** register as **Loners**; apart from packs, not Rogues (`/setfaction` to join a Great Pack).\n\n"

        "`/pack treasury` `/deposit` `/withdraw`; communal bones\n"

        "`/pack stash list` `/deposit` `/withdraw`; shared food reserve (rots slower)\n"

        "**Hunters** depositing to `/pack stash` feed the healer den: **+1 unity** & **+1 standing** once per sunrise\n"

        "`/packlife action:feedall`; communal meal from reserve — **Alpha** (once per pack per sunrise)\n"

        "`/packlife action:drinkall`; creek drink for whole den — **Alpha** (once per pack per sunrise)\n"

        "`/playpen action:playall`; den romp mood boost — **Alpha** (uses your toys or den toy store)\n"

        "`/playpen action:toystore mode:`; den toy store (list · deposit · depositall · withdraw)\n"

        "`/pack taxrate` `/settax`; hunt tax (Alpha, 0-25%)\n"

        "`/pack territory`; territory map\n"

        "`/pack challenge territory`; declare war (Alpha)\n"

        "`/pack brokenrite`; latest **Rite of the Broken Canine** (leadership challenge)\n"

        "`/pack patrol` `/pack patrol collaborate:true` `/scout`; earn war points during conflict\n"

        "`/pack resolvewar`; **Alpha** or **Diplomat** ends an active war and awards territory by score\n"

        "`/pack unity`; pack unity **−5 to 10**; low unity hurts hunts; **−5 dissolves** the den\n"

        "`/howl`; once per sunrise; raises unity (**Alpha** or **Beta/Advisor** rally when unity ≤ 0). "

        "**Alpha** howls grant **Commanding Howl**; packmates gain advantage on their next check or attack.\n"

        "`/pack relations` `/relation`; rival den standing\n"

        "`/pack pact`; **Warrior Cats** clan treaties (Alpha or **Diplomat**): "
        "ThunderClan, ShadowClan, WindClan, RiverClan\n"
        "`action:receive`; collect **Clan patrol** goods at the scent-line (trust 35+, once/sunrise)\n"
        "`action:trade`; barter **duplicates** for Clan prey, herbs, toys + trust\n"
        "`/trade duplicates`; give all extras to another wolf (once per sunrise)\n\n"

        "Lake territory · warrior patrols, deputies, rogues, loners, kittypets · "
        "seasonal **Gathering** at Fourtrees (unity/standing when treaties active)\n"
        "tribute from treasury · Charisma parley · fewer `/field action:sniff` border fights while active\n\n"

        "Breaking a pact or killing an allied **warrior patrol** costs **trust**, **unity**, and **standing**",

    ),

    "world": (

        "World & rollover",

        "`/world action:time`; sunrise, season, time of day\n"

        "`/setseason`; **admin**; jump season\n"

        "`/world action:weather` · `action:forecast`; current weather and hunt effects\n"

        "`/world action:cooldowns`; what's ready this sunrise\n"

        "`/wilderness action:travel` · `action:encounter` · `action:omen`; travel hazards, border encounters, **StarClan** omens\n"
        "`territory:twolegplace`; Thunderpath monsters, Twoleg nests, pet dogs\n\n"

        "`/medic action:sacred`: Medic half-moon visit; ancestors speak + **+2 standing**, "
        "**+5 mood**, **+1 pack unity**, next Medicine/Herblore **+2** (miss: **−2** standing)\n"

        "`/rollover`; advance one sunrise (admin)\n"

        "`/hazard`; weather hazard opposed roll\n"

        "`/terms` · `/help topic:terms`; wolf tongue glossary\n"

        "`/ping`; bot health check\n\n"

        "One rollover = **one sunrise**. Seasons: Newgrowth, Highsun, Leaf-drop, Leaf-bare.",

    ),

    "terms": (

        "Wolf tongue",

        f"`/terms topic:` or `/help topic:terms`; glossary used in **{BOT_DISPLAY_NAME}**\n"

        "• **overview**; quick map (sunrise, fresh-kill, loner vs rogue)\n"

        "• **basic**; fresh-kill, sharing tongues, Thunderpath, Twolegs…\n"

        "• **seasons**; Newgrowth, Moonhigh, quarter-moon…\n"

        "• **measurements**; pawstep, deer-length, tail-length…\n"

        "• **insults**; deerheart, carrion-breath, pup-brain…",

    ),

    "prestige": (

        "Prestige & legacy",

        "`/prestige action:view`; your tier and bone bonus\n"

        "`/prestige action:require`; next tier requirements\n"

        "`/prestige action:bonus`; unlocked tiers\n"

        "`/prestige action:legacy`; legacy score and dynasty\n"

        "`/prestige action:retire`; add wolf to dynasty (+legacy)\n"

        "`/prestige action:halloffame`; top legacy scores\n\n"

        "Higher tiers grant permanent +% bones on hunts and daily.",

    ),

    "rpg": (

        "RPG rolls (Basil rules)",

        "**HP** = 10 + Strength + Survival (Constitution score). Example: 10 + 7(Str) + 5(Survival) = **22**.\n"

        "Roll **1d20 + attribute modifier + character traits** (weaknesses subtract).\n"
        "Failed **skill** rolls (`/skills`, `/rpg action:roll skill:…`) build practice strain before traits slip.\n"

        "Nat 1 = critical failure · Nat 20 = critical success.\n\n"

        "`/rpg action:roll skill:tracking dc:15`; skill check\n"

        "`/rpg action:roll attribute:wisdom dc:12`; raw attribute check\n"

        "`/rpg action:roll use_safe_roll:true`; reroll a failed check with **Safe Roll** (not combat)\n"

        "`/rpg action:roll use_role_reroll:true`; **Elder**/**Diplomat** reroll on failure (once/sunrise)\n\n"

        "`/combat start` `/join` `/list` `/npc` `/begin` `/attack` `/maneuver` `/npcattack` `/yield` `/status` `/end`\n"

        "`/combat encounter`; random ambush (90 min cooldown; also triggers on hunt/explore)\n"

        "Yielding may be **caught** (~35%); **−2 standing** if you're still in a den.\n"

        "`/combat npc`; add a predator, **clan cat**, hearth-hound, fox, or badger from the bestiary (not custom HP)\n"

        "`/combat hazard topic:`; Two-Legs, Thunderpath, traps, fences, **fire fear**, wildfire\n"

        "`/combat guide topic:bestiary`; cats, foxes, badgers, border patrols\n"

        "`/combat guide topic:`; vulnerable areas, stance, maneuvers, injuries, crits\n"

        "**Injuries**; 1d10 on crit or dropping to 0 HP · **Crit/fumble**; nat 20/1 rolls 1d4 extra\n"

        "**Pin**; pin sets **prone**; pinning wolf shown as `pinning`. "
        "Only **same size or larger** fighters can pin (cats cannot pin wolves). "
        "Clan **cats** use maneuvers in NPC fights (rakes, Badger Defence); no pinning wolves.\n"

        "After `/combat begin`; **Pick a target** from the dropdown, then **Bite** / **Claw** / **Maneuver**\n"

        "Several fights can run in one channel; each has a **fight #**. `/combat list` shows them; "
        "`/combat join` works mid-fight (rolls initiative). Pass `encounter:` when several are open.\n"

        "Target lock is saved; any combat message in the channel works after a bot restart\n"

        "Player turn → target + **Bite** / **Claw** / **Maneuver** · NPC turn → **NPC attack** menu or `/combat npcattack`\n"

        "DC tiers: Easy 10 · Moderate 15 · Hard 20 · Legendary 25\n\n"

        "`/skills`; run catalogued Basil checks (tracking, stealth, social, survival, herb prep, …)\n"

        "`/skilllist`; reference DCs by category · Freeform: `/rpg action:roll`",

    ),

    "skills": (

        "Skill checks (Basil catalog)",

        "**69** scripted checks from the Basil rules; run with `/skills category:… check:…`.\n\n"

        "**Categories:** tracking · stealth · howling · social · spiritual · survival · "

        "herb_prep · crafting · navigation\n\n"

        "`/skilllist category:tracking`; list DCs without rolling\n"

        "`/skills group:true`; pack group check (half must pass)\n"

        "`/skills helper:@wolf`; assisted check (helper DC 10 → your advantage)\n"

        "`/field action:track trail_age:…`; daily hunt alternative using tracking DCs\n"

        "Opposed checks need `/skills opponent:` (packmate or rival wolf).\n"

        "Tracking scent decay: rain/snow/wind raise DC; use `rained:true` when relevant.\n"

        "Moonhigh **night** adds **+2 DC** to tracking and stealth; half-light **+1**.\n"

        "**Long-term injuries** (limp, scars, chronic pain) show on `/vitals action:condition`; "

        "cure with wolfsbane or swamp milkweed.\n"

        "Full Basil reference: `docs/BASIL_RULES.md`.\n\n"

        "**Herb loop:** `/field action:forage` → fresh stack in `/herbs action:bag` → "

        "`/herbs action:prepare` or **`action:dryall`** (bag + `/inventory` + den store) → `/medic action:treat` with `stack:ID`.\n"

        "Stock the healers' den: `/herbs action:store mode:depositall`. Fresh forage stacks rot after **1 sunrise** if not dried.\n"

        "Shop/inventory herbs are stable; dry or deposit them when ready.",

    ),

    "life": (

        "Life & advancement",

        "**Death**; at 0 HP: `/medic action:deathsaves` (3 rounds DC 10/12/15). All pass → 1 HP. Any fail → death.\n"

        "`/medic action:stabilize`; ally Medicine DC 15; cobwebs auto-stabilize (**Medics**; unlimited per sunrise).\n"

        "`/medic action:surgery`; **Medic** or **medic apprentice** (+2 DC): stitch, set bone, extract, amputate "

        "(herbs from bag/inventory; **stick** from patient or Medic: **2 sticks** for set bone; "

        "optional `use_meadowsweet`, `use_loosestrife`, `use_plantain`, `use_poppy`, `use_rush_stalks`; "

        "optional `helper:` Medic for assisted surgery; once per sunrise).\n"

        "`/medic action:observe`; apprentice/senior observe a case (quest progress; no surgery cooldown)\n"

        "`/medic action:checkup`; **full Medic only** — once-per-sunrise den scan (contagion, mind & spirit, bleeding, dying, herb bags; **~52%** catch poison hoarders)\n\n"

        "**XP**; +1 from daily, quest complete, and den chat (once per sunrise). "

        "`/advance action:spend` for +1 attribute, **+1 earned skill trait** "
        "(max +3 from play; stacks with lore traits on `/skills` checks); "
        "**failed skill rolls** build **practice strain** (close misses are nerves only); "
        "at **3 strain** you lose earned trait progress or gain a setback — "
        "success and `/rollover` rest ease strain; "

        "`purchase:role_feature` submits a bonus role-feature request (**admin approval**).\n"

        "`/wolfset`; update birth sex, sexuality, Maw belief, or **combat size** (small / medium / large).\n\n"

        "**Mating**; `/courtship action:court` then `action:mate` (spring). "

        "`/courtship action:rival`; spring physical or vocal challenge for mating access.\n"

        "**Medics**; Healer's Code is not enforced by the bot; if caught courting/mating **−3 standing**. "

        "Bearing or adopting pups **exiles the litter and the healer**.\n"

        "Cross-player mating needs partner **Accept** (button or `respond:`). "

        "Failure **−4 mood** ( **−7** if hostile). Mating **+12 mood** each.\n"

        "`/courtship action:pregnancy`; yours or your bonded mate's. `/pupcare action:birth names:…` · "

        "`action:feed` (mothers nurse; **Caretakers** mash-feed pack pups once per sunrise) · "

        "`action:save` with **Vitality Salve** · `action:adopt` · `action:list`. "

        "Juveniles: first hunt kill = **blooding**, then `/role action:event`.",

    ),

    "admin": (

        "Admin",

        "Requires `ADMIN_IDS` in `.env` or server Administrator.\n\n"

        "`/rollover`; advance the game day\n"

        "`/wolfadmin assign`; create a wolf for a player\n"

        "`/wolfadmin transfer`; move a wolf between players\n"

        "`/wolfadmin possess` / `release`; steer another player's wolf for RP\n"

        "`/wolfadmin list`; inspect a player's wolves\n"

        "`/wolfadmin setage`; set a wolf's age in moons (0-120)\n"

        "`/wolfadmin featurepending`; list pending bonus role-feature requests\n"

        "`/wolfadmin approvefeature`; approve a request (spends 10 XP)\n"

        "`/wolfadmin denyfeature`; deny a request (no XP spent)\n"

        "`/questadmin create`; post a custom quest\n"

        "`/questadmin list`; all board quests\n"

        "`/questadmin remove`; delete a quest\n"

        "`/patronadmin code`; create a donation redeem code\n"

        "`/patronadmin grant`; manually grant donor rewards\n"

        "`/patronadmin kickstarter grant`; Kickstarter backer badge\n"

        "`/patronadmin kickstarter tier2`; Tier 2 bundle (badge + 75 bones + item)\n"

        "`/patronadmin orders`; pending Ko-fi shop orders\n"

        "`/patronadmin fulfill`; mark a shop order delivered",

    ),

    "credits": ("Credits", CREDITS_TEXT),

}





class Help(commands.Cog):

    def __init__(self, bot: commands.Bot):

        self.bot = bot



    @app_commands.command(

        name="ping",

        description="Bot health check; latency and uptime.",

    )

    async def ping(self, interaction: discord.Interaction):

        latency_ms = round(self.bot.latency * 1000)

        embed = howlbert_embed(

            f"{BOT_DISPLAY_NAME} is awake",

            f"**Latency**; {latency_ms} ms\n"

            f"**Guilds**; {len(self.bot.guilds)}",

            color=EMBED_COLOR,

        )

        embed.set_footer(text=embed_footer("Use /help for commands"))

        await interaction.response.send_message(embed=embed, ephemeral=True)



    @app_commands.command(

        name="help",

        description="Learn how to use Howlbert; wolf RP commands and den mechanics.",

    )

    @app_commands.describe(topic="Category to read about")

    @app_commands.choices(

        topic=[

            app_commands.Choice(name="Overview", value="overview"),

            app_commands.Choice(name="Getting started", value="getting-started"),

            app_commands.Choice(name="Profile", value="profile"),

            app_commands.Choice(name="Economy", value="economy"),

            app_commands.Choice(name="Hunting", value="hunting"),

            app_commands.Choice(name="Wolvden (explore & mood)", value="wolvden"),

            app_commands.Choice(name="UnbelievaBoat (economy)", value="unbelievaboat"),

            app_commands.Choice(name="Whispering Wild (fog spirits)", value="whispering"),

            app_commands.Choice(name="Quests", value="quests"),

            app_commands.Choice(name="Role features", value="roles"),

            app_commands.Choice(name="Maw faith & oracles", value="lore"),

            app_commands.Choice(name="Wolf tongue / terms", value="terms"),

            app_commands.Choice(name="Pack & warfare", value="pack"),

            app_commands.Choice(name="World & rollover", value="world"),

            app_commands.Choice(name="Prestige & legacy", value="prestige"),

            app_commands.Choice(name="RPG rolls", value="rpg"),

            app_commands.Choice(name="Skill checks", value="skills"),

            app_commands.Choice(name="Life & advancement", value="life"),

            app_commands.Choice(name="Admin", value="admin"),

            app_commands.Choice(name="Credits", value="credits"),

        ]

    )

    async def help(

        self,

        interaction: discord.Interaction,

        topic: str | None = None,

    ):

        title, body = HELP_TOPICS.get(topic or "overview", HELP_TOPICS["overview"])

        embed = howlbert_embed(title, body, color=EMBED_COLOR)

        await interaction.response.send_message(embed=embed, ephemeral=True)





async def setup(bot: commands.Bot):

    await bot.add_cog(Help(bot))

