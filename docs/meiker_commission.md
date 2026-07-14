# make a wolf character maker: full body art commission brief

this is the art brief for a **make a wolf** character maker for **howlbert**, a dark wolf roleplay
project. it will be built on **meiker.io** (a site that turns a layered PSD into a clickable dress
up or character creator). the goal: a player can build a wolf that matches their in character wolf,
so the world's traits (missing limbs, tail, scars, pregnancy, blindness) all need matching art.
built **full body** so those show (a headshot could not).

## about howlbert (the tone to aim for)

howlbert is a wolf roleplay game that runs as a bot inside a community chat server: each player
creates and plays their own wolf, and lives out its whole life through the game, hunting,
surviving, forming bonds, raising pups, and eventually dying.

the setting is a **harsh, grim, low fantasy wilderness**. the wolves are **sentient**: they have
language, names, packs, culture, and religion, so they are humanlike in mind, even though they are
drawn as **fully realistic animals**. keep the body pure wolf (no bright or unnatural colours, no
wings, no anthro features, no upright posture, no armour), but their faces and bearing can carry
real personality, intelligence, and emotion. think naturalistic wildlife painting, but with a
bleak, gothic edge. survival is brutal.
death is **permanent**, and it shows on the survivors: wolves carry lasting **scars, old injuries,
deformities, disease, and inherited conditions** (blindness, missing limbs, twisted spines), they
**age** visibly, they **breed** and grow gaunt through hard winters. that grit is the whole point
of the art; a clean, unmarked wolf is the exception, not the rule.

wolves belong to one of **four packs**, each tied to a landscape: **greyspire** (mountain, harsh
and scarred), **mistmoor** (swamp, strange and spiritual), **thistlehide** (forest, memory keeping
and herb wise), and **silverrush** (river, fluid and grieving). some wolves are packless **loners
or rogues**. many of them follow **"the maw,"** a grim death cult that treats the world's decay,
carrion, and omens as sacred; ravens, bones, rot, and ritual marks all carry weight in the world.

for the maker, that means two things: the art should **feel weathered and real** (muted palette,
painterly, a little mournful, never cute), and it needs to depict the **full range of a hard life**,
the missing legs, milky blind eyes, battle scars, and swollen bellies alongside the flower crowns
and ravens, so a player can rebuild the exact wolf they have lived and lost in the game.

## format

* **full body, seated or curled pose, front facing or 3⁄4.** a sitting or curled wolf is taller
  than wide, which is the only way to fit a whole wolf on meiker (see the width rule below). a
  classic standing side profile is landscape and **will not fit**, so pose the wolf upright.
* **canvas: portrait, about 900 by 1200 px source** (draw big, downscale for posting). meiker's
  rule ([instructions](https://meiker.io/instructions)): height **800 to 1200 px**, **width no
  greater than height** (square or portrait only).
* export sizes: **9:16, 540 by 960 px** (phone wallpaper or story, the natural fit for a full body)
  and **1:1, 600 by 600 px** (square avatar). one meiker game is **one** canvas ratio, so the
  portrait is the source of truth and the 1:1 is a center or head crop (or a second build for a
  true full body square). note 600 by 600 is below meiker's 800 minimum, so the square is always a
  downscale of the 800 or larger source.
* **non negotiable watermark:** a small **howlbert** brand mark must be a fixed, always visible
  layer that cannot be toggled off (in meiker: a visible layer not in any folder), placed clear of
  both the 9:16 and the 1:1 head crop safe areas. every shared wolf carries the brand.

## meiker layer structure (back to front)

each is a PSD folder with a meiker tag. **scars** and **accessories** are `[mixed]` (stack many);
most others are `[fixed]` (pick one). silhouette changing traits (missing limbs, tail, build, pose)
are **base variants**, not overlays; that is the extra art cost of going full body. the hex ramps
below drop straight into meiker's `[color-picker]` or `[dynamic]` swatches (name a layer `#c8871f`
and it becomes that swatch).

1. **background** `[fixed]` (section a)
2. **body base** `[fixed]`: whole seated wolf; build or size, sex, life stage, missing limb variants (section b)
3. **coat colour** `[dynamic]` palette on the body (section b3)
4. **body condition** `[optional]`: gaunt or heavy overlay (section b5)
5. **tail** `[fixed]`: includes a no tail option (section b6)
6. **markings** `[mixed]`: face and body (section b4)
7. **eyes** `[fixed]`: colour, state, expression (section c)
8. **eyebrows** `[optional]` (section d)
9. **mouth** `[fixed]`: expression and teeth or jaw (section e)
10. **scars and marks** `[mixed]`: face and body (section f)
11. **pregnancy** `[optional]`: belly overlay (section b5)
12. **accessories** `[mixed]`: worn items, companions, insects (section g)
13. fixed watermark: always visible free layer, on top

**how to read this**

* items tagged **(priority)** are the common ones, or the trait that makes a wolf recognisably
  that wolf. build these first; the rest can be a later update.
* some items are **in world traits** (a condition, deformity, scar, size, or life stage a wolf can
  actually have in the game); drawing them lets a built wolf match a real character. the rest are
  **cosmetic**: coat and eye colour are open ended, so the swatches here are the intended range,
  wolf realistic, not rainbow.
* **hex** is given as a **shadow · base · highlight** ramp (core shade, then local colour, then rim
  or backlit edge). these are starting swatches; nudge for taste. markings are coloured relative to
  the coat underneath (see section b4) so one marking layer works on every pelt.

**the only things a seated full body still cannot show:** a true limp or gait (limping is
movement; a sitting wolf can show a tucked or stiff leg but not a limp in motion), and a standing
side profile (landscape, will not fit the canvas). also note absolute size does not read in a solo
portrait (nothing to compare to), so small or large build must read as proportion (chunkier or
leaner body, bigger or smaller paws and head), not literal scale. everything else (missing legs,
missing tail, twisted leg, pregnancy, body scars, crooked spine) shows fine seated.

---

## a. background (slot 1)

keep backgrounds simple and low contrast so the wolf stays the subject: a 2 to 3 colour wash plus
one silhouette layer. hex is a **far · mid · near** depth ramp (light and back, to dark and front).

general:

* forest, day (priority): far `#8fa06a` · mid `#5c7040` · near `#2f3d22`
* moor or open grassland: far `#c9c58a` · mid `#9a9a5c` · near `#6d6a3a`
* den mouth or cave: far `#6a6258` · mid `#3d372f` · near `#14110f`
* snow or winter: far `#eef2f5` · mid `#cdd6dd` · near `#9fadb7`
* riverbank or water: far `#adc4c2` · mid `#6f9490` · near `#3f5f5c`
* night plus full moon, the brand shot (priority): far `#2a3550` · mid `#161d30` · near `#0a0d16`, moon `#f2ede0`
* dawn or dusk warm light: far `#f2c98a` · mid `#d98a5c` · near `#8a4f4a`
* storm or fog, eerie: far `#b8bcc0` · mid `#8a8f95` · near `#5c6066`
* flat colour or vignette, clean profile: single wash plus darker edge vignette

pack specific (one signature backdrop per canon pack, a pack pride sharing hook; there are four packs):

* greyspire, mountain (priority): far `#b8bcc4` · mid `#7f8590` · near `#4c515c`; jagged grey peaks, thin snow, teeth of stone
* mistmoor, swamp (priority): far `#8f9c6e` · mid `#5c6b47` · near `#33402a`; rotting fen, hanging mist, still black water
* thistlehide, forest (priority): far `#7f8f5a` · mid `#4f6338` · near `#2b3a20`; dense old trees, a pale ancestor tree behind
* silverrush, river (priority): far `#bcd0ce` · mid `#7fa39d` · near `#48706a`; rushing river, wet stones, silver light

lifestyle:

* loner or rogue, the wild edge (priority): far `#c4b48f` · mid `#8a7a58` · near `#4a3f2c`; lone ridge at dusk, no den, one bare tree
* pack den, generic: far `#8a7f6c` · mid `#5c5344` · near `#2f2a22`; warm den mouth, worn earth, bones, belonging

---

## b. body base (slots 2 to 6, 11)

the whole seated wolf and everything painted into it.

### b1. build or size

reads as proportion, not literal scale (see the note above). draw as body base variants.

* [ ] medium build, default (priority)
* [ ] small build (leaner, finer, smaller paws and head; runt or small)
* [ ] large build (chunkier, heavier, bigger paws and head)
* [ ] masculine overlay (priority): broader muzzle plus heavier neck ruff plus thicker build; its
      absence reads as the leaner female or neutral form. that is the whole sex difference.

### b2. life stage

head and body proportion variants:

* [ ] adult, prime, the default (priority)
* [ ] pup (rounded, big paws and ears, soft)
* [ ] juvenile or yearling (leggy, half grown)
* [ ] elder (greyed muzzle, sunken flanks, thinner ruff, stiffer seat)

### b3. base coat colour

the body, head, and ruff colour. each pelt is a 3 stop ramp; shade with the shadow, catch fur
edges with the highlight. keep a warm undertone in the darks; pure neutral greys read plastic. (in
meiker, these become a `[dynamic]` palette so one body recolours to any pelt.)

* black (priority): shadow `#0d0b09` · base `#1a1714` · highlight `#332e28`
* charcoal or dark grey (priority): shadow `#26241f` · base `#3d3a36` · highlight `#5c5851`
* grey, agouti "wolf grey" (priority): shadow `#5f584f` · base `#8a8178` · highlight `#b0a89d`
* silver or pale grey (priority): shadow `#9a9186` · base `#c7c1b8` · highlight `#e6e1d8`
* brown or tawny (priority): shadow `#513c27` · base `#7a5c3e` · highlight `#a07f5b`
* red or rust (priority): shadow `#6f3f24` · base `#a5623a` · highlight `#c78a5c`
* cream or pale gold: shadow `#b39c74` · base `#d9c19a` · highlight `#efe0c1`
* white, off white: shadow `#cfc8bb` · base `#f2ede4` · highlight `#ffffff`
* sable (brown and black banded): shadow `#3a2c1e` · base `#5c4632` · highlight `#856848`
* blue grey (dilute): shadow `#4c4f54` · base `#6f7278` · highlight `#9498a0`

special coat genetics:

* albinism (priority): plus pink eyes; shadow `#e4d9cf` · base `#faf6ef` · highlight `#ffffff`
* melanism, all dark (priority): shadow `#0a0906` · base `#15130f` · highlight `#2b2823`
* [ ] coat colour dilution: a desaturation plus slight lighten overlay (about 35 percent less
      saturation, 8 percent more lightness) over the chosen coat, not new swatches; makes any pelt
      paler and muddier.

### b4. markings (slot 6, `[mixed]`)

stack over the coat, so colour them as a value shift of whatever coat is underneath; one marking
layer then works on every pelt:

* dark marking is the coat multiplied by 0.6 (or blend the coat's shadow stop about 70 percent)
* light marking is the coat plus 25 percent lightness (or blend the coat's highlight)
* true white is a fixed layer: base `#f2ede4`, shadow `#d8d1c4`, highlight `#ffffff` (do not tint it to the coat)

markings:

* agouti banding, wild type (priority): dark plus light shift banded together
* saddle or cape, dark back (priority): dark marking over back and shoulders
* countershadow, pale belly, throat, inner legs (priority): light marking underside
* facial mask, muzzle or eye: dark or light marking
* widow's peak or forehead: dark marking
* dark points, ears, muzzle, paws, tail: dark marking
* piebald or white patches (chest blaze, socks, tail tip, belly): true white layer
* ticking or roaning, flecked: true white or dark flecks, low opacity
* grizzled or grey flecked (also elder ageing): `#c7c1b8` flecks, low opacity
* coat texture (thick winter, sleek summer, patchy mid shed): ragged tufting overlay

### b5. body condition and pregnancy (slots 4 and 11, `[optional]` overlays)

* [ ] body condition: gaunt or starved (ribs, sharp hips), for hungry or wasting wolves
* [ ] body condition: heavy or well fed (fuller barrel)
* [ ] lean or normal is the default base, no overlay
* [ ] pregnant belly overlay (priority): rounded barrel, heavier teats, for expecting dams

### b6. tail (slot 5, `[fixed]`)

seated pose curls the tail around the paws, a good showcase spot.

* [ ] full brush tail, default (priority): carries coat plus tail tip marking
* [ ] missing tail: stub or none
* [ ] tail carriage: relaxed and curled, tucked and fearful, or raised (crosses with mood)

### b7. legs, paws, and posture (base variants)

silhouette changes, so drawn as alternate seated bases, not overlays.

* [ ] four legged seated, default (priority)
* [ ] missing foreleg (seated, one front leg absent)
* [ ] missing hindleg (seated, one hind leg tucked or absent)
* [ ] twisted leg (a malformed, bent limb visible in the seat)
* [ ] stiff or tucked leg: the closest a seated pose gets to a limp or arthritis (a favoured, drawn
      in leg); note a true moving limp cannot be shown seated
* [ ] crooked or hunched spine (a curved seated back)
* [ ] flat skull or short muzzle
* [ ] crooked jaw (overbite or underbite, muzzle silhouette)
* [ ] ear set: neutral, forward, pinned back, or one torn

---

## c. eyes (slot 7)

iris ramp: **shadow** (upper iris or lash shadow), **base** (local colour), **highlight** (glint
adjacent). always add a separate near white specular dot on top.

* amber or gold (priority): shadow `#8f5c12` · base `#c8871f` · highlight `#e6ab45`
* yellow (priority): shadow `#9c7d1f` · base `#d8b23a` · highlight `#f0d572`
* brown (priority): shadow `#48301a` · base `#6b4a2b` · highlight `#8f6a43`
* pale yellow or ice: shadow `#b6a86a` · base `#e6dca0` · highlight `#f6efc8`
* green: shadow `#54622f` · base `#7a8a4e` · highlight `#a0ad74`
* blue: shadow `#3f5668` · base `#5f7d92` · highlight `#8aa3b4`; uncommon, keep muted
* pink or red, albino (priority): shadow `#9c4a4a` · base `#c76b6b` · highlight `#e29797`; pairs with albinism
* milky or blind (priority): shadow `#b0b1ab` · base `#cfd0cb` · highlight `#e8e9e4`; flat, no clear pupil
* clouded or cataract: shadow `#8f938f` · base `#a9adaa` · highlight `#c8ccc8`; hazy film over a normal iris
* [ ] heterochromia: any two of the above, one per eye
* [ ] fading or dull eyes, failing sight: desaturate the iris about 40 percent, catchlight to half
* [ ] eye shape expressions: wide, neutral, narrowed, half closed, squint closed

---

## d. eyebrows (slot 8)

the brow ridge carries a lot of stylized emotion, worth its own slot.

* [ ] neutral brow (priority)
* [ ] raised or worried (inner brow up)
* [ ] furrowed or angry (inner brow down)
* [ ] relaxed or soft
* [ ] brow markings ("eyebrow" points or dots above the eyes): light or dark marking (see section b4)

---

## e. mouth (slot 9)

* [ ] closed or neutral (priority)
* [ ] slight open or relaxed pant
* [ ] snarl (priority): lips curled, teeth bared, also shows dental traits
* [ ] happy, tongue out
* [ ] tongue lolling, heavy pant (hot or exhausted)
* [ ] grimace or sick (drooping)
* [ ] crooked or missing teeth (visible in open or snarl mouths)

---

## f. scars and marks (slot 10, `[mixed]`, stack several)

permanent marks a wolf earns and carries for life. full body, so both face and torso are fair
game. scar tissue palette (deepen the shadow on pale pelts): old or silvered `#b8a99a` · `#d8cabb`
· `#efe6da`; fresh or raw shadow `#a86a5e` · base `#c98a7c` · highlight `#e0a89b`.

* [ ] face scar (muzzle, cheek, or brow variants) (priority): silvered
* [ ] body scarring: scar lines on flank, shoulder, or haunch (priority): silvered
* [ ] scarred hide: heavy multi scar across the torso, battle worn; silvered
* [ ] torn or notched ear
* [ ] blind in one eye clawed scar (over a milky eye): fresh or raw across the eye
* [ ] raw lick patch (a hairless, raw obsessive lick spot on a leg or flank): fresh or raw `#c98a7c`
* [ ] ritual glyph (a carved or painted mark on brow, shoulder, or flank, for the world's death
      cult "the maw"): `#8a2b2b`, faint glow `#c24a4a`

---

## g. accessories (slot 12, `[mixed]`, stack several)

worn items, companions, and accents, the most requested "personalise me" layer. hex is
**shadow · base · highlight** for each item's main material.

* flower crown (priority): see bloom swatches below; spring, autumn, dried, or single stem variants
* flowers behind ear or in ruff: reuse crown blooms
* herb sprig in mouth, for healer wolves: shadow `#3f5a2b` · base `#5f7d38` · highlight `#86a45c`; nettle, marigold, poppy
* leaf caught in fur, green: shadow `#4a5a26` · base `#6d8236` · highlight `#93a85e`
* leaf caught in fur, autumn: shadow `#7a3f1c` · base `#a86428` · highlight `#cf8a42`
* moss or lichen tuft: shadow `#5c6b3a` · base `#7f9155` · highlight `#a7b57e`
* black raven feather in ruff (priority): shadow `#0d0e12` · base `#1c1e26` · highlight `#3a3d49`; pairs with the raven below
* pale or barred feather: shadow `#7d766a` · base `#a89f8f` · highlight `#cfc7b8`
* bone adornment (necklace or worn in fur): shadow `#c8bda3` · base `#e4dbc4` · highlight `#f5efdd`; rib, claw, or tooth; leader flavour
* beaded or twine cord: shadow `#5a4632` · base `#7d6142` · highlight `#9e7f57`; add bead accent colours freely
* simple leather collar: shadow `#3e2c1d` · base `#5e442c` · highlight `#7f6142`
* war paint or ash streaks: `#3a3733` · `#565149` · dry brush; ritual or battle
* blood smear, fresh, on muzzle or paws: shadow `#5e1414` · base `#8a1f1f` · highlight `#b23a3a`; just fed or battle
* bandage or poultice wrap, leg or torso: shadow `#c9c2b2` · base `#e6e0d2` · highlight `#f6f2e8`; wounded wolves
* frost or snow on coat: shadow `#c6ccd2` · base `#e2e7ec` · highlight `#ffffff`; low opacity seasonal
* rain droplets: translucent `#9fb0bb` glints; seasonal

companions (kept realistic; no fox or snake, since those are insults in this world; ravens
genuinely follow wolf packs):

* raven, on shoulder, beside, or overhead (priority): shadow `#0b0c10` · base `#191b22` · highlight `#3d4658` sheen; beak and legs `#0d0d0d`
* crow, smaller: same, no sheen
* magpie: black and white plus `#2f5a7d` wing sheen
* a lone pup at the wolf's side: a wolf, reuse the pup base

insect accents (realistic; insects land on animals; not companions):

* butterfly, on nose, paw, or back: wings warm shadow `#8a5a12` · base `#c8871f` · highlight `#f0d572` (recolourable)
* moth, dusky: shadow `#4a4038` · base `#6e6156` · highlight `#948578`
* beetle, iridescent: shadow `#0c1a12` · base `#183226` · highlight `#3f6b4e` sheen
* dragonfly or firefly accent: body `#3a4a2e` · `#5c7444`; glow dot `#d8e08a`

flower crown blooms (shadow · base · highlight; mix into crowns or behind ear sprigs):

* white daisy: shadow `#d0c9ba` · base `#f2ede2` · highlight `#ffffff`, centre `#e0b437`
* yellow buttercup or marigold: shadow `#b8860f` · base `#e6b325` · highlight `#f7db6e`
* pink wildflower: shadow `#a24f6e` · base `#cf7a99` · highlight `#ecabc0`
* purple heather or thistle: shadow `#553a6b` · base `#7d5a9c` · highlight `#a98cc4`
* red poppy: shadow `#7a1414` · base `#b52424` · highlight `#e05555`, centre `#1a1714`
* blue forget me not: shadow `#3f5f86` · base `#5f84b0` · highlight `#8fb0d4`, eye `#e6c93a`
* dried or autumn, withered: shadow `#6a4a2a` · base `#916b3f` · highlight `#b8905c`
* green foliage or stems: shadow `#3f5a2b` · base `#5f7d38` · highlight `#86a45c`

---

## build order (suggested)

1. one adult, medium, four legged seated base plus the layer registration (get coat, markings,
   eyes, brows, mouth, scars, tail, and accessories all landing correctly on one body first).
2. the in world base variants: missing foreleg or hindleg, twisted leg, crooked spine, small or
   large build, life stages. these are the expensive silhouette redraws and the real
   differentiator: it lets someone build a three legged, pregnant, scarred survivor.
3. cosmetic breadth (more coats, markings, eye colours, expressions): easy wins once the system holds.
4. backgrounds, companions, accessories last.

## notes for quoting

* cost is driven by the number of layers and the silhouette changing base variants (missing limbs,
  builds, life stages each are a full seated redraw). that base variant count is the biggest line
  item in a full body build, so it is the main thing to price.
* the priority items are the minimum viable first version; the rest can ship as a later update
  (meiker lets you add items after launch).
* usage rights: this maker is for howlbert, which is a monetized project (it has a shop and a
  crowdfunder), and players will generate and publicly share their results. so the commission needs
  to include commercial and promotional usage rights for the project, plus the right for players to
  create and share outputs. meiker itself takes no license to the art, so those rights are just
  between us; happy to work them into the agreement.
