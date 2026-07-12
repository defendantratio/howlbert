# make-a-wolf picrew — asset checklist (full-body)

everything i'd need to **draw or commission** for a howlbert "make-a-wolf" maker (see
`docs/GROWTH_IDEAS.md` §50). the goal is that a player can build a wolf that matches one they'd
actually register — so in-game traits get matching art. built **full-body** so the missing-limb,
tail, pregnancy, and body-scar wolves can all be shown (a headshot couldn't).

## format

- **full-body, seated / curled pose, front-facing or 3⁄4.** a *sitting* or *curled* wolf is
  taller-than-wide, which is the only way to fit a whole wolf on meiker (see the width rule below).
  a classic standing side-profile is landscape and **won't fit** — so pose the wolf upright.
- **canvas: portrait, ~900×1200 px source** (draw big, downscale for posting). meiker's rule
  ([instructions](https://meiker.io/instructions)): height **800–1200 px**, **width ≤ height**
  (square or portrait only).
- export sizes: **9:16 — 540×960 px** (phone wallpaper / story — the natural fit for a full body)
  and **1:1 — 600×600 px** (square avatar). one meiker game = **one** canvas ratio, so build the
  portrait as the source of truth and treat the 1:1 as a **center/head crop** (or a second build if
  you want a true full-body square). note 600×600 is below meiker's 800 min, so the square is always
  a downscale of the ≥800 source.
- **non-negotiable watermark:** the howlbert mark is a **fixed, always-visible layer that can't be
  toggled off** (in meiker: a visible layer not in any folder), placed clear of both the 9:16 and
  the 1:1 head-crop safe areas. every shared wolf carries the brand — that's the point.

## platform — where to build this

**pick one and commit.** building the same maker on several platforms is overkill: it doubles
maintenance (every item drawn twice, two sets of terms) for almost no reach gain. draw **one**
source of truth (a single layered PSD) and publish it once. the layer spec below is
platform-agnostic, so the art carries over if i ever switch.

| option | how it works | AI? | ownership / commercial | cost / catch | best when |
|---|---|---|---|---|---|
| ⭐ **meiker.io** | upload a **labelled PSD**; folder tags (`[fixed]`/`[optional]`/`[mixed]`/`[color-picker]`/`[dynamic]`) become the menus. no coding. | **none** — pure layer compositor; the only automation is a deterministic hex-swatch reader for `[dynamic]` palettes, which never alters art. bans AI-generated *content*. | *"your artwork remains your property"*; meiker takes **no** license — a commissioned artist just grants **me** commercial rights, no extra platform hurdle | free, **ad-supported** | best **hosted** route; discoverable (Doll Divine runs on the meiker engine) |
| **self-built (HTML5/JS)** | a small layer-compositor i code (same PSD-layer logic in the browser) | none | **total** control + full commercial rights, my own watermark, no ads | i build + host it; can live on `howlbert.straw.page` or wire into the bot | best if i want zero ads / full control |
| **picrew.me** | japan-based maker; most name-recognition | none | maker terms default to **personal/non-commercial** — grey area for a monetized brand | free | only if raw discoverability outweighs the caveats |
| ~~Charat / Artbreeder / AI gens~~ | — | Charat = anime; **Artbreeder/AI gens are AI-based** | — | — | **avoid** — violate my no-AI policy (`docs/ARTIST_BEST_PRACTICES.md`) |

**working plan:** build the PSD to this spec, publish on **meiker.io** first. the hex ramps below
drop straight into meiker's `[color-picker]`/`[dynamic]` swatches (name a layer `#c8871f` and it
becomes that swatch). the same art ports to a self-built maker later if ads/control ever bite.

## meiker layer structure (back → front)

each is a PSD folder with a meiker tag. **scars** and **accessories** are `[mixed]` (stack many);
most others are `[fixed]` (pick one). silhouette-changing traits (missing limbs, tail, build,
pose) are **base variants**, not overlays — that's the extra art cost of going full-body.

1. **background** `[fixed]` — §A
2. **body base** `[fixed]` — whole seated wolf: build/size, sex, life stage, missing-limb variants — §B
3. **coat colour** `[dynamic]` palette on the body — §B3
4. **body condition** `[optional]` — gaunt / heavy overlay — §B5
5. **tail** `[fixed]` — incl. a no-tail option — §B6
6. **markings** `[mixed]` — face + body — §B4
7. **eyes** `[fixed]` — colour · state · expression — §C
8. **eyebrows** `[optional]` — §D
9. **mouth** `[fixed]` — expression + teeth/jaw — §E
10. **scars & marks** `[mixed]` — face + body — §F
11. **pregnancy** `[optional]` — belly overlay — §B5
12. **accessories** `[mixed]` — worn items, companions, insects — §G
13. *(fixed watermark — always-visible free layer, on top)*

**legend**
- 🎮 = a **real game trait** (register genetic, birth mutation, long-term injury, size, or life
  stage), from `engine/genetics.py`, `engine/long_term_injuries.py`, `engine/combat_size.py`,
  `config.py`.
- 🎨 = **cosmetic / RP palette** (coat + eye colour are free-text in-game, so *i* set the range).
- ⭐ = high priority (common, or the trait that makes a wolf recognisably *this* wolf).
- **hex** is a **shadow · base · highlight** ramp (core shade → local colour → rim/backlit edge) —
  starting swatches, nudge for taste. markings are coloured *relative to the coat underneath* (§B4)
  so one marking layer works on every pelt.

> **the only things a seated full-body still can't show:** a **true limp / gait** (limping is
> *movement* — a sitting wolf can show a *tucked or stiff* leg but not a limp in motion), and a
> **standing side-profile** (landscape, won't fit the canvas). also note **absolute size** doesn't
> read in a solo portrait (nothing to compare to), so small/large **build** must read as
> *proportion* — chunkier/leaner body, bigger/smaller paws & head — not literal scale. everything
> else (missing legs, missing tail, twisted leg, pregnancy, body scars, crooked spine) shows fine
> seated.

---

## §A. background 🎨 (slot 1)

keep backgrounds **simple and low-contrast** so the wolf stays the subject — a 2–3 colour wash +
one silhouette layer. hex is a **far · mid · near** depth ramp (light/back → dark/front).

### general 🎨

| background | far · mid · near |
|---|---|
| ⭐ forest (day) | `#8fa06a` · `#5c7040` · `#2f3d22` |
| moor / open grassland | `#c9c58a` · `#9a9a5c` · `#6d6a3a` |
| den mouth / cave | `#6a6258` · `#3d372f` · `#14110f` |
| snow / winter | `#eef2f5` · `#cdd6dd` · `#9fadb7` |
| riverbank / water | `#adc4c2` · `#6f9490` · `#3f5f5c` |
| ⭐ night + full moon (the brand shot) | `#2a3550` · `#161d30` · `#0a0d16` + moon `#f2ede0` |
| dawn / dusk warm light | `#f2c98a` · `#d98a5c` · `#8a4f4a` |
| storm / fog (eerie) | `#b8bcc0` · `#8a8f95` · `#5c6066` |
| flat colour / vignette (clean profile) | single wash + darker edge vignette |

### pack-specific 🎮

one signature backdrop per canon great pack (`config.py` `GREAT_PACKS`) — a pack-pride sharing hook.

| pack (terrain) | far · mid · near | signature detail |
|---|---|---|
| ⭐ **Greyspire** — Mountain | `#b8bcc4` · `#7f8590` · `#4c515c` | jagged grey peaks, thin snow, teeth-of-stone |
| ⭐ **Mistmoor** — Swamp | `#8f9c6e` · `#5c6b47` · `#33402a` | rotting fen, hanging mist, still black water |
| ⭐ **Thistlehide** — Forest | `#7f8f5a` · `#4f6338` · `#2b3a20` | dense old trees, a pale ancestor-tree behind |
| ⭐ **Silverrush** — River | `#bcd0ce` · `#7fa39d` · `#48706a` | rushing river, wet stones, silver light |

### lifestyle 🎮

| background | far · mid · near | notes |
|---|---|---|
| ⭐ **loner / rogue** — the wild edge | `#c4b48f` · `#8a7a58` · `#4a3f2c` | lone ridge at dusk, no den, one bare tree |
| pack den (generic) | `#8a7f6c` · `#5c5344` · `#2f2a22` | warm den mouth, worn earth, bones — belonging |

---

## §B. body base 🎮 + 🎨 (slots 2–6, 11)

the whole seated wolf and everything painted into it.

### B1. build / size 🎮

reads as **proportion**, not literal scale (see the note above). draw as body-base variants.

- [ ] ⭐ **medium** build (default) 🎮
- [ ] **small** build (leaner, finer, smaller paws/head — runt / small size-class) 🎮
- [ ] **large** build (chunkier, heavier, bigger paws/head — large size-class) 🎮
- [ ] ⭐ **masculine overlay** (broader muzzle + heavier neck ruff + thicker build); its **absence**
      reads as the leaner female/neutral form. that's the whole sex difference.

### B2. life stage 🎮

head + body proportion variants (`config.py`: pup <6 moons, juvenile 6–24, adult 24–59, elder 60+).

- [ ] ⭐ **adult** (prime — the default) 🎮
- [ ] **pup** (rounded, big paws/ears, soft) 🎮
- [ ] **juvenile / yearling** (leggy, half-grown) 🎮
- [ ] **elder** (greyed muzzle, sunken flanks, thinner ruff, stiffer seat) 🎮

### B3. base coat colour 🎨

the body/head/ruff colour. each pelt = a 3-stop ramp; shade with the shadow, catch fur edges with
the highlight. keep a warm undertone in the darks — pure neutral greys read plastic. (in meiker,
these become a `[dynamic]` palette so one body recolours to any pelt.)

| pelt | shadow | base | highlight |
|---|---|---|---|
| ⭐ black | `#0d0b09` | `#1a1714` | `#332e28` |
| ⭐ charcoal / dark grey | `#26241f` | `#3d3a36` | `#5c5851` |
| ⭐ grey (agouti "wolf grey") | `#5f584f` | `#8a8178` | `#b0a89d` |
| ⭐ silver / pale grey | `#9a9186` | `#c7c1b8` | `#e6e1d8` |
| ⭐ brown / tawny | `#513c27` | `#7a5c3e` | `#a07f5b` |
| ⭐ red / rust | `#6f3f24` | `#a5623a` | `#c78a5c` |
| cream / pale gold | `#b39c74` | `#d9c19a` | `#efe0c1` |
| white (off-white) | `#cfc8bb` | `#f2ede4` | `#ffffff` |
| sable (brown/black banded) | `#3a2c1e` | `#5c4632` | `#856848` |
| blue-grey (dilute) | `#4c4f54` | `#6f7278` | `#9498a0` |

**special coat genetics** 🎮:

| condition | shadow | base | highlight |
|---|---|---|---|
| ⭐ **albinism** ("Pale-Hide") 🎮 — + pink eyes | `#e4d9cf` | `#faf6ef` | `#ffffff` |
| ⭐ **melanism** ("Shadow-Hide") 🎮 | `#0a0906` | `#15130f` | `#2b2823` |

- [ ] **coat colour dilution** ("Washed-Hide") 🎮 — a **desaturation + slight-lighten overlay**
      (≈ −35% saturation, +8% lightness) over the chosen coat, not new swatches.

### B4. markings 🎨 (slot 6, `[mixed]`)

stack over the coat, so colour them as a **value shift of whatever coat is underneath** — one
marking layer then works on every pelt:

- **dark marking** = coat ×0.6 (or blend the coat's *shadow* stop ~70%)
- **light marking** = coat +25% lightness (or blend the coat's *highlight*)
- **true white** = fixed `#f2ede4` base · `#d8d1c4` shadow · `#ffffff` highlight (own layer; don't tint)

| marking | how to colour |
|---|---|
| ⭐ **agouti banding** (wild-type) | dark + light shift banded together |
| ⭐ **saddle / cape** (dark back) | dark marking over back & shoulders |
| ⭐ **countershading** (pale belly / throat / inner legs) | light marking underside |
| **facial mask** (muzzle / eye) | dark or light marking |
| **widow's peak / forehead** | dark marking |
| **dark points** (ears / muzzle / paws / tail) | dark marking |
| **piebald / white patches** (chest blaze, socks, tail tip, belly) | true-white layer |
| **ticking / roaning** (flecked) | true-white or dark flecks, low opacity |
| **grizzled / grey-flecked** (also elder ageing) | `#c7c1b8` flecks, low opacity |
| **coat texture** (thick winter / sleek summer / patchy mid-shed) | ragged tufting overlay |

### B5. body condition & pregnancy 🎮 (slots 4 & 11, `[optional]` overlays)

- [ ] body condition: **gaunt / starved** (ribs, sharp hips) — ties to hunger/wasting
- [ ] body condition: **heavy / well-fed** (fuller barrel)
- [ ] *(lean/normal = the default base, no overlay)*
- [ ] ⭐ **pregnant** belly overlay (rounded barrel, heavier teats) — for expecting dams 🎮

### B6. tail 🎮 (slot 5, `[fixed]`)

seated pose curls the tail around the paws — a good showcase spot.

- [ ] ⭐ full brush tail (default) — carries coat + tail-tip marking
- [ ] **missing tail** ("Missing Tail" genetic) 🎮 — stub / none
- [ ] tail carriage: relaxed-curled / tucked-fearful / raised (crosses with mood)

### B7. legs, paws & posture 🎮 (base variants)

silhouette changes → drawn as alternate seated bases, not overlays.

- [ ] ⭐ four-legged seated (default) 🎮
- [ ] **missing foreleg** (seated, one front leg absent) 🎮
- [ ] **missing hindleg** (seated, one hind leg tucked/absent) 🎮
- [ ] **twisted leg** (a malformed, bent limb visible in the seat) 🎮
- [ ] **stiff / tucked leg** — the closest a seated pose gets to **limp / arthritis** (a favoured,
      drawn-in leg); note a true moving limp can't be shown seated 🎮
- [ ] **crooked / hunched spine** (hemivertebra, LSTV, spinal conditions — curved seated back) 🎮
- [ ] **flat-skull / short muzzle** (brachycephaly) 🎮
- [ ] **crooked jaw** (overbite/underbite — muzzle silhouette) 🎮
- [ ] ear set: neutral / forward / pinned-back / one-torn

---

## §C. eyes 🎨 + 🎮 (slot 7)

iris ramp = **shadow** (upper iris/lash shadow) · **base** (local colour) · **highlight**
(glint-adjacent). always add a separate near-white specular dot on top.

| eye | shadow · base · highlight | notes |
|---|---|---|
| ⭐ amber / gold 🎨 | `#8f5c12` · `#c8871f` · `#e6ab45` | |
| ⭐ yellow 🎨 | `#9c7d1f` · `#d8b23a` · `#f0d572` | |
| ⭐ brown 🎨 | `#48301a` · `#6b4a2b` · `#8f6a43` | |
| pale yellow / ice 🎨 | `#b6a86a` · `#e6dca0` · `#f6efc8` | |
| green 🎨 | `#54622f` · `#7a8a4e` · `#a0ad74` | |
| blue 🎨 | `#3f5668` · `#5f7d92` · `#8aa3b4` | uncommon; keep muted |
| ⭐ pink / red (albino) 🎮 | `#9c4a4a` · `#c76b6b` · `#e29797` | pairs with albinism |
| ⭐ milky / blind ("Blindness") 🎮 | `#b0b1ab` · `#cfd0cb` · `#e8e9e4` | flat, no clear pupil |
| clouded / cataract (partial blindness) 🎮 | `#8f938f` · `#a9adaa` · `#c8ccc8` | hazy film **over** a normal iris |

- [ ] heterochromia 🎨 — any two of the above, one per eye
- [ ] **fading / dull eyes** (progressive retinal atrophy) 🎮 — desaturate the iris ≈ −40%, catchlight to half
- [ ] **eye-shape expressions** 🎨 — wide / neutral / narrowed / half-closed / squint-closed

---

## §D. eyebrows 🎨 (slot 8)

the brow ridge carries a lot of stylized emotion — worth its own slot.

- [ ] ⭐ neutral brow
- [ ] raised / worried (inner brow up)
- [ ] furrowed / angry (inner brow down)
- [ ] relaxed / soft
- [ ] **brow markings** ("eyebrow" points / dots above the eyes) 🎨 — light or dark marking (§B4)

---

## §E. mouth 🎨 + 🎮 (slot 9)

- [ ] ⭐ closed / neutral
- [ ] slight open / relaxed pant
- [ ] ⭐ **snarl** (lips curled, teeth bared — also shows dental traits)
- [ ] happy / tongue-out
- [ ] tongue lolling / heavy pant (hot / exhausted)
- [ ] grimace / sick (drooping)
- [ ] **crooked / missing teeth** (dental anomaly — visible in open/snarl mouths) 🎮

---

## §F. scars & marks 🎮 (slot 10, `[mixed]` — stack several)

from `engine/long_term_injuries.py` — marks a wolf earns and carries for life. now full-body, so
both face and torso are fair game. scar-tissue palette (deepen the shadow on pale pelts):
**old/silvered** `#b8a99a` · `#d8cabb` · `#efe6da`; **fresh/raw** `#a86a5e` · `#c98a7c` · `#e0a89b`.

- [ ] ⭐ **face scar** (muzzle / cheek / brow variants) 🎮 — silvered
- [ ] ⭐ **scarring** — body scar lines (flank / shoulder / haunch) 🎮 — silvered
- [ ] **scarred hide** (heavy multi-scar across the torso, battle-worn) 🎮 — silvered
- [ ] **torn / notched ear** 🎨
- [ ] **blind-in-one-eye clawed scar** (over a milky eye) 🎮 + 🎨 — fresh/raw across the eye
- [ ] **raw-lick patch** (lick granuloma — hairless/raw spot on a leg or flank) 🎮 — fresh/raw `#c98a7c`
- [ ] **scars-of-the-Maw / ritual glyph** (brow, shoulder, or flank) 🎮 — `#8a2b2b`, faint glow `#c24a4a`

---

## §G. accessories 🎨 (slot 12, `[mixed]` — stack several)

worn items, companions, and accents — the most-requested "personalise me" layer. hex is
**shadow · base · highlight** for each item's main material.

| accessory | shadow · base · highlight | notes |
|---|---|---|
| ⭐ **flower crown** | see bloom swatches below | spring / autumn / dried / single-stem variants |
| flowers behind ear / in ruff | — | reuse crown blooms |
| herb sprig in mouth (medic) | `#3f5a2b` · `#5f7d38` · `#86a45c` | nettle / marigold / poppy |
| leaf caught in fur (green) | `#4a5a26` · `#6d8236` · `#93a85e` | |
| leaf caught in fur (autumn) | `#7a3f1c` · `#a86428` · `#cf8a42` | |
| moss / lichen tuft | `#5c6b3a` · `#7f9155` · `#a7b57e` | |
| ⭐ **black raven feather** in ruff | `#0d0e12` · `#1c1e26` · `#3a3d49` | pairs with the raven below |
| pale / barred feather | `#7d766a` · `#a89f8f` · `#cfc7b8` | |
| **bone adornment** (necklace / worn in fur) | `#c8bda3` · `#e4dbc4` · `#f5efdd` | rib/claw/tooth; founder/alpha |
| beaded / twine cord | `#5a4632` · `#7d6142` · `#9e7f57` | add bead accent colours freely |
| simple leather collar | `#3e2c1d` · `#5e442c` · `#7f6142` | |
| war paint / ash streaks | `#3a3733` · `#565149` · dry-brush | ritual / Maw / battle |
| blood smear (fresh, muzzle / paws) | `#5e1414` · `#8a1f1f` · `#b23a3a` | just-fed / battle |
| bandage / poultice wrap (leg / torso) | `#c9c2b2` · `#e6e0d2` · `#f6f2e8` | wounded wolves; injury system |
| frost / snow on coat | `#c6ccd2` · `#e2e7ec` · `#ffffff` | low-opacity seasonal |
| rain droplets | translucent `#9fb0bb` glints | seasonal |

**companions** (kept realistic + lore-safe — no fox/snake, since **foxheart**/**snake** are insults
in this world; ravens genuinely follow wolf packs):

| companion | shadow · base · highlight |
|---|---|
| ⭐ **raven** (on shoulder / beside / overhead) | `#0b0c10` · `#191b22` · `#3d4658` sheen; beak/legs `#0d0d0d` |
| crow (smaller) | same, no sheen |
| magpie | black/white + `#2f5a7d` wing sheen |
| a lone pup at the wolf's side | a wolf — reuse pup base |

**insect accents** (realistic — insects land on animals; not "companions"):

| insect | shadow · base · highlight |
|---|---|
| butterfly (on nose / paw / back) | wings warm `#8a5a12` · `#c8871f` · `#f0d572` (recolourable) |
| moth (dusky) | `#4a4038` · `#6e6156` · `#948578` |
| beetle (iridescent) | `#0c1a12` · `#183226` · `#3f6b4e` sheen |
| dragonfly / firefly accent | body `#3a4a2e` · `#5c7444`; glow dot `#d8e08a` |

**flower-crown blooms** (shadow · base · highlight; mix into crowns / behind-ear sprigs):

| bloom | shadow · base · highlight |
|---|---|
| white daisy | `#d0c9ba` · `#f2ede2` · `#ffffff` + `#e0b437` centre |
| yellow buttercup / marigold | `#b8860f` · `#e6b325` · `#f7db6e` |
| pink wildflower | `#a24f6e` · `#cf7a99` · `#ecabc0` |
| purple heather / thistle | `#553a6b` · `#7d5a9c` · `#a98cc4` |
| red poppy | `#7a1414` · `#b52424` · `#e05555` + `#1a1714` centre |
| blue forget-me-not | `#3f5f86` · `#5f84b0` · `#8fb0d4` + `#e6c93a` eye |
| dried / autumn (withered) | `#6a4a2a` · `#916b3f` · `#b8905c` |
| green foliage / stems | `#3f5a2b` · `#5f7d38` · `#86a45c` |

---

## build order (suggested)

1. **one adult, medium, four-legged seated base + the layer registration** (get coat, markings,
   eyes, brows, mouth, scars, tail, accessories all landing correctly on *one* body first).
2. **the 🎮 base variants** — missing foreleg/hindleg, twisted leg, crooked spine, small/large
   build, life stages. these are the expensive silhouette redraws and the real differentiator; no
   other wolf maker lets you build a three-legged, pregnant, scarred survivor that maps to a real
   character.
3. **cosmetic breadth** (more coats, markings, eye colours, expressions) — easy wins once the system holds.
4. **backgrounds, companions, accessories** last.

## commission notes

- hand the artist **this checklist + the seated full-body brief + the two export sizes + the
  layer/stacking requirement** up front; a maker's cost is driven by the number of layers **and**
  the silhouette-changing base variants (missing limbs, builds, life stages each = a redraw), so an
  itemised, hex-spec'd list = an accurate quote. flag the base-variant count explicitly — it's the
  biggest line item in a full-body build.
- ⭐ items are the minimum viable maker; the rest can ship as v2 (meiker lets you add items later).
- **licensing:** whoever draws this (me or a commission), i need it cleared for howlbert's use and
  for players to make + share results. meiker takes no license to the art, so a commissioned artist
  just needs to grant **me** commercial rights. see `docs/ARTIST_BEST_PRACTICES.md` and the picrew
  commercial notes in `docs/GROWTH_IDEAS.md` §50 — building it from *my own* art is the cleanest
  path and lets me set the usage scope myself.
