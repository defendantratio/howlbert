# Basil Pack Survival Rules (Howlbert)

Reference for Basil's tabletop rules wired into Howlbert. Use slash commands where noted; everything else is in `/skills`, `/skilllist`, or GM discretion.

## Long-Term Injuries

Permanent marks after healing; roleplay plus minor mechanics. Shown on `/vitals action:condition`.

| Injury | Effect |
|--------|--------|
| **Limp** | Movement −¼; −1 Dexterity when running |
| **Scarring** | +1 Intimidation when scar is visible |
| **Chronic pain** | Disadvantage on first Str/Dex check on cold or rainy days |
| **Fear of [trigger]** | Wisdom DC 12 or frightened 1 round when faced |

- Assigned on failed `/skills` **Set bone without comfrey** (crit fail → limp).
- Cured with **wolfsbane** (spirit curse; 2 to 6 poison damage) or **swamp milkweed** via `/medic action:treat`.
- Otherwise months of rest at GM discretion.

## Fear of Fire

Wolves fear open flame (campfires, torches, wildfires).

| Command | What it does |
|---------|----------------|
| `/combat hazard topic:fire` | Wisdom DC 12 within 10 ft |
| `/combat hazard topic:wildfire` | Fear at 20 ft + Survival/Constitution DC 15 or 1d4 heat |
| `/combat hazard topic:fire_stand` | Charisma + Intimidation DC 15: ignore fear 1 round |
| `/combat hazard topic:fire_encourage ally:@wolf` | Charisma + Persuasion DC 14: remove frightened |

- **Guard** role: one failed save reroll per sunrise.
- **Frightened**: cannot move closer; disadvantage on attacks/checks while fire in sight until 30+ ft away or extinguished.

## Rival Challenge (mating access)

`/courtship action:rival target:@defender rival_mode:physical|vocal favor_challenger:true`

- **Physical**: opposed Strength + Hunting; pin; loser retreats or submits.
- **Vocal**: opposed Charisma + Intimidation; loser cannot approach female rest of day.
- Female may give +2 to favored challenger. **Winner is not guaranteed mating.**

## Rival Pack Standing (0 to 10)

`/pack relations` · `/pack relation pack_name:`

- Starts at **5** (neutral).
- **≥8**: share hunts / help in fights · **≤3**: attack on sight · **0**: war.
- +1 share territory · +2 help vs enemy · +1 diplomatic howl · −1 fight prey · −2 scent over-mark · −3 kill rival.

## Skill Checks

`/skills` and `/skilllist`: tracking, stealth, howling, social, spiritual, survival, herb prep, crafting, navigation (69+ scenarios).

**Opposed & group** (engine: `engine/group_checks.py`):

- Opposed: higher total wins; nat 20 beats unless both 20; nat 1 loses badly.
- Group: half must succeed.
- Assist: helper DC 10 → primary rolls twice, takes higher.
- Pack howl range: highest Charisma + 1 per 3 wolves; nat 20 doubles range.

## Travel & Omens

`/wilderness action:travel territory:river|swamp|mountain|forest`

| Territory | DC | Failure |
|-----------|-----|---------|
| River | 12 | +1 exhaustion or lose herb bundle |
| Swamp | 15 | Poisoned 1d4/hr |
| Mountain | 18 | Frostbite −1 Dex |
| Forest | 10 | Lose 1d4 hours |

`/wilderness action:encounter`: d20: 1 to 5 encounter, 6 to 15 quiet, 16 to 20 find useful.

`/wilderness action:omen`: nat 1 bad omen (disadvantage first roll next sunrise); nat 20 advantage.

## Seasons

Shown on `/world action:time`. Mechanical hooks in `config.py` and `engine/season_effects.py`.

- **Spring**: herbs +2 forage, rivers +2 DC.
- **Summer**: heat hazards, small prey hunt −2 DC, wildfire smoke.
- **Autumn**: hunt −1 DC, post-frost forage +2, cache +1 day food.
- **Winter**: forage +5 DC, hunt +2 DC, **+50% hunger decay** on rollover, cached meals from autumn apply.
- **Autumn**: successful `/bones action:hunt` caches **+1 day food** (`food_cache_meals`).

**Pack howl range** on `/packlife action:howl`: highest Charisma in today's chorus +1 per 3 wolves; nat 20 doubles reach.

## Human World

`/combat hazard`: Two-Legs, Thunderpath, traps, nests, fences (reference + rolls).

## Illnesses

| Name | Key | Notes |
|------|-----|-------|
| Pupcough | `pupcough` | Weak pups; may → weak lungs |
| Shock (emotional) | `shock_emotional` | Trauma; poppy, comfort, valerian |
| Insomnia | `insomnia` | Restless → sleepless → exhaustion; chamomile, lavender, valerian, poppy |
| Anxiety | `anxiety` | Uneasy → panic-prone; chamomile, catmint, passionflower, skullcap |
| Grief / melancholy | `grief_melancholy` | Mourning → hollow; chamomile, lavender, borage, rosemary |
| Delirium | `delirium` | Fever-dream confusion; dried skullcap, valerian |
| Pack madness | `pack_madness` | Paranoia; contagious at low rate; sagewort, skullcap |
| Obsession | `obsession` | Fixation → tunnel vision; rosemary, meadowsweet, skullcap |
| Night terrors | `night_terrors` | Screaming dreams; lavender, passionflower, valerian |
| Chronic stress | `chronic_stress` | Tense → frayed; meadowsweet, douglas sagewort |
| Eating distress | `eating_distress` | Refusal to eat; meadowsweet, borage, mint family |
| Shock (physical) | `shock_physical` | Blood loss; stabilize fast |
| Cloudmouth | `rabies` | Always fatal; no cure; sedate away from pack |

## Healer's Code

Medics are **not blocked** from courtship, mating, or pups; but the den punishes violations:

| Violation | If caught / discovered |
|-----------|------------------------|
| **Court** (success) | ~45% caught → **−3 standing**; existing pups exiled |
| **Mate** | ~45% caught → **−3 standing**; family exiled; cast out at **−5** standing |
| **Birth** | Always public → **−5 standing**; litter **exiled**; healer **exiled** |
| **Adopt** | Always public → same as birth |

`/medic action:sacred`: half-moon sacred visit (every **3** sunrises). Ancestors speak one line at the stone. Rewards: **+2 standing**, **+5 mood**, **+1 pack unity**, next Medicine/Herblore check **+2**, distress eased. Miss one: **−2 standing** on rollover. Reminder on `/profile`, `/vitals action:condition`, and `/world action:cooldowns`.

Apprentices observe; full **Medic** role bears the code.

## Surgery (`/medic action:surgery`)

> **A Note on Realism:** While we use real plants and their properties for inspiration, wolves can't perform complex surgery, set complex broken bones, or cure every ailment. This guide is designed to enhance storytelling, offering a grounded and believable framework for the struggles and triumphs of a pack's Healer.

**Medic** or medic apprentice (+2 DC) operates on a **patient** once per sunrise. Herbs are consumed from the Medic's forage bag or inventory; **sticks** (`stick` inventory key) may come from the **patient's** bag too (they bite one during painful work).

| Procedure | Injury | DC | Supplies |
|-----------|--------|-----|----------|
| **Stitch** | Deep gash, infected wound | 15 | Cobwebs + yarrow + **stick** (patient bites) |
| **Set bone** | Fractured rib, sprain, broken jaw, spinal | 20 | Comfrey + bindweed + **2 sticks** (bite + splint); optional flags below |
| **Extract** | Punctured paw | 12 | Yarrow (+ optional `use_plantain`) |
| **Amputate** | Infected limb, ruined leg/paw | 18 | Yarrow + **stick** (+ optional `use_poppy` +2) |

**Stick**: thin twig (`stick` in inventory; forage stacks use key `stick`). Given to wolves in pain to bite during stitch, bone-setting, and amputation. Set bone needs **two**: one between the jaws, one to align the splint.

**Optional surgery flags** (toggle on `/medic action:surgery`; herbs are **not** auto-used from the Medic bag):

| Flag | Bonus | Procedures |
|------|-------|------------|
| `use_meadowsweet` | +1 Medicine | Stitch, set bone, amputate |
| `use_loosestrife` | +1 Medicine | Stitch only |
| `use_plantain` | +1 Medicine | Extract only |
| `use_poppy` | +2 Medicine | Amputate only |

**Binding broken bones**: comfrey poultice on the break; straight **sticks** aligned along the limb; **bindweed** vines (or **rush_stalks** from river/swamp, when used) lash the splint. Patient must be conscious enough to bite the stick (not **dying**). Another Medic must operate; no self-surgery.

- Nat **1**: infection, shock, or permanent **limp** (set bone).
- Success clears the injury; stitch heals **1d4 HP**; amputation adds **scarring**.
- `/medic action:treat` handles minor wounds; surgery is for injuries herbs alone cannot fix.

### Pack herb store (`/herbs action:store`)

Medics and Foragers deposit forage stacks into the **healers' den store** (shared `pack_herb_stacks` table).

| Mode | Who | Action |
|------|-----|--------|
| `list` | any packmate | View store |
| `deposit` | Medic / Forager | Forage `stack:ID` → den store |
| `withdraw` | Medic / Forager | Store `#ID` → your herb bag |

### Treatment checklist (`/vitals action:condition`)

Shows a **3-step care plan** embed field: suggested **herbs**, **surgery** need, and **rest days** for the active injury or disease.

### Treat packmates (`/medic action:treat patient:`)

**Medics** may treat a packmate using the **healer's** forage stack (`treat_from_herb_stack` with `patient`).

### Spirit ritual (`/medic action:ritual`)

**douglas_sagewort**, **lavender**, or **mountain_ash** (rowan) over a patient: Herblore DC 15; eases **shock (emotional)** or fulfills **spirit_cleanse** flavor.

### Naming & death rites

- **`/medic action:naming`**: Medic names pups ~3 weeks (under **1** moon) at the sacred place.
- **`/medic action:lay_to_rest`**: rosemary / lavender / mint over the dead (consumable).

### Swim therapy (`/medic action:swim`)

River territory once per sunrise; bonus recovery for **sprains**, **fractured ribs**, or **splint confinement** after bone-setting.

### Medic rounds & observe

- **`/medic action:rounds`**: den scan: contagious, bleeding, sacred visit due, low herb warnings.
- **`/medic action:observe`**: apprentice RP + quest progress; **no surgery cooldown**.

### Assisted surgery

- **`/medic action:surgery helper:`**: second Medic; helper Medicine DC **10** grants **advantage** on the surgeon's roll.
- **`use_rush_stalks:true`** on **set bone**: rush stalks **+2** (lashes splint).
- Successful **set bone** applies **splint confinement** (`bone_rest_until`, 7 sunrises); `/medic action:swim` may shorten.

### Group & assisted skill checks

- **`/skills group:true`**: `run_group_check` with all living pack den wolves.
- **`/skills helper:@wolf`**: `run_assisted_check` (helper DC 10 → primary advantage).

### Healer's Code: cannot refuse the sick

Soft reminder when a **dying** packmate is in the den (commands + rollover). **Whitecough** = **Green-cough (Mild)** in glossary (`/terms`).

### Herb compendium

- **`/herbs action:guide`** or **`/field action:compendium`**: read-only browser from `herbs_compendium.py` with habitat filter.

### Restricted herbs

**bloodroot**, **deadly nightshade**, **deathberries**, **foxglove**, **holly berries**, **oleander**, **poison ivy**, **water hemlock**, **wintergreen**, **wolfsbane** are Medic knowledge.

- Non-Medics who **use** a restricted herb via `/medic action:treat` take poison saves **and** lose **4 standing** (using poison is always witnessed).
- Non-Medics who **keep** restricted herbs in a personal forage bag risk **−3 standing if caught** (~38% rollover, sniff/groom, **~52% on Medic rounds**; missed rounds show **suspicious scent** only).
- **`/herbs action:turnin`**: hand poison herbs to the healers' den (**+1 standing**; **10🦴** from pack treasury when funded).
- **`/bones action:sell item:stack:ID`**: sell normal forage herbs at the trading post (UnbelievaBoat-style); restricted herbs cannot be sold.
- Turn poison finds in via **`/herbs action:store mode:deposit`** (Medic/Forager) or **turnin**; **deathberries** mercy remains Medic-only.
- **Hunters** who **`/pack stash deposit`** feed the healer den: **+1 pack unity** and **+1 standing** once per sunrise (Basil tradition).

### Forage crit flavor

Critical forage success may yield a **rare herb** plus a **seasonal blurb** (`season_activity_blurb`).

### Rot-lung den news

Rollover **season** line when **rot_lung** count in a pack exceeds threshold (default **2**).

### Herb gathering & storage

- `/field action:forage`: Survival check; fresh stack in `/herbs action:bag`.
- Fresh herbs **rot after 1 sunrise** unless dried via `/herbs action:prepare`.
- Shop or inventory herbs stay stable (dried). Foragers receive one common herb per sunrise in pack territory.

## Practices & Traditions

- Naming at sacred place (~3 weeks).
- Apprentices observe until instructed.
- Lifelong service; prior mates/pups allowed if mate is gone.
- Hunters feed the healer den.
