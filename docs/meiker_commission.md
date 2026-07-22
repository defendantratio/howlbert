# make a wolf character maker: self build guide (ibispaint plus meiker)

this is my build guide for drawing a **make a wolf** character maker for **howlbert**, a dark wolf
roleplay project, **by hand** and assembling it on **meiker.io** (a site that turns a layered PSD
into a clickable dress up or character creator). i could not find an artist i liked who would take on
a project this large, so i am drawing it myself; this doc is the plan and the checklist.

the design is a **hybrid, not fully modular**: a player **picks a whole-wolf base** (each one a
complete drawing i make), then **recolours it and stacks separable overlays** (markings, scars,
accessories) to get close to their in-character wolf. the base carries the pose, build, life stage,
eyes, brows, and mouth; the world's identity traits are covered either by an overlay (scars,
markings), a recolour (coat, eyes), or a base variant (missing limbs, life stage, blindness). built
**full body** so those traits show (a headshot could not). the structure section spells out exactly
what is baked into the base and what stays separable.

**which app: i'm using ibispaint** (i also have procreate). ibispaint wins it for me on the drawing
side, which is where most of the work is: the **specific brushes**, the **vector lineart** for clean,
re-editable outlines, the **shape tool**, and the **symmetry ruler** for a dead symmetric frontal
base. procreate used to have one real edge, exporting a grouped PSD directly, but **ibispaint now
exports a layered PSD too** (share, PSD (Preserved Layers)) and has layer folders, so that edge is
gone and there is no real assembly penalty to choosing ibispaint. procreate stays noted only as an
alternative.

the pipeline (ibispaint):

1. draw each piece over the shared master base, using clipping masks for the three shading layers,
   then **merge each finished option to one flat layer** (see the caveat below).
2. organise the option layers into **layer folders**, one folder per meiker slot, named with the
   meiker tag (for example a folder `[fixed] eyes`).
3. export a layered PSD directly: **share, PSD (Preserved Layers)**. one PSD per category file.
4. in **photopea** (free, runs in a browser), **combine the per category PSDs into one, confirm the
   tags, add the watermark**, and save.
5. upload that PSD to **meiker**.

**ibispaint now has layer folders and PSD export** (share, PSD (Preserved Layers)), so it produces a
grouped PSD directly, the same as procreate; photopea is only needed to **combine** the several per
category files and do the final tagging and watermark. **caveat:** ibispaint's PSD export warns that
**blend modes may not transfer reliably and folder clipping is dropped**, which is exactly why each
option is **merged to a single flat layer before export**, so the shading and clipping are already
baked into pixels and nothing depends on a blend mode surviving. anything that still looks wrong after
export can fall back to a **transparent PNG** for that one piece, dropped into the PSD in photopea.

## about howlbert (the tone i'm aiming for)

howlbert is a wolf roleplay game that runs as a bot inside a community chat server: each player
creates and plays their own wolf, and lives out its whole life through the game, hunting,
surviving, forming bonds, raising pups, and eventually dying.

the setting is a **harsh, grim, low fantasy wilderness**. the wolves are **sentient**: they have
language, names, packs, culture, and religion, so they are humanlike in mind, even though they are
drawn as **fully realistic animals**. keep the body pure wolf (no bright or unnatural colours, no
wings, no anthro features, no upright posture, no armour), but their faces and bearing can carry
real personality, intelligence, and emotion. think naturalistic wildlife painting, but with a
bleak, gothic edge. survival is brutal.

**how realistic, exactly: realistic structure, painterly rendering.** the **anatomy and proportion**
should be a real wolf (the not a cat, not a dog notes below), but the **rendering is stylised
painterly naturalism, not photorealism.** aim for a painted wildlife look, not a photo. a character
maker actively wants this: photoreal texture baked into a coat fights the recolourable `[dynamic]`
swatch, and dozens of separately drawn, swappable parts cannot be kept matching at photoreal
fidelity. so the real target is **stylised realism, held consistent across every part**, so any
combination of coat, eyes, scars, and accessories still looks like one artist drew one wolf.
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
* **canvas: portrait, draw at 1200 by 1600 px** (procreate or ibispaint), bigger than the final so
  detail survives the downscale, on a **transparent background** (new canvas, no background fill).
  every piece is drawn on this one canvas size so the pieces line up perfectly when stacked. note
  both apps cap layers **by canvas size and device RAM** (a bigger canvas gets fewer layers), which
  is the main reason to split the maker across several files by category, below. meiker's own rule
  ([instructions](https://meiker.io/instructions)): final PSD height **800 to 1200 px**, **width no
  greater than height** (square or portrait only), so the PSD is downscaled to about **900 by 1200**
  during photopea assembly.
* export sizes: **9:16, 540 by 960 px** (phone wallpaper or story, the natural fit for a full body)
  and **1:1, 600 by 600 px** (square avatar). one meiker game is **one** canvas ratio, so the
  portrait is the source of truth and the 1:1 is a center or head crop (or a second build for a
  true full body square). note 600 by 600 is below meiker's 800 minimum, so the square is always a
  downscale of the 800 or larger source.
* **non negotiable watermark:** a small **howlbert** brand mark must be a fixed, always visible
  layer that cannot be toggled off (in meiker: a visible layer not in any folder), placed clear of
  both the 9:16 and the 1:1 head crop safe areas. every shared wolf carries the brand.

## rendering: three shading layers

every element is painted with **three layers of shading** over its flat base colour, never a flat
cel fill, so the finished maker reads as a painted wildlife piece rather than a sticker set. both
apps do this with **clipping masks** so the shading never spills past the shape: draw the flat, then
add layers above it set to clip to it (**procreate:** tap the layer, "clipping mask"; **ibispaint:**
the layer's "clipping" toggle), so each shading pass is masked to the flat automatically. the three
passes, bottom to top, over the flat local colour:

1. **form shadow:** a **multiply** clipping layer, the soft shade where each form turns away from
   the light. paint it in the **shadow** stop of that item's hex ramp.
2. **core or occlusion shadow:** a second **multiply** clipping layer, deeper and tighter, in the
   crevices where parts overlap and no light reaches, under the jaw and ruff, inside the legs, behind
   the tail, in the ear hollows. use the shadow stop deepened roughly 15 percent, low opacity so it
   only bites in the deepest folds.
3. **highlight and rim:** an **add (glow)** or **screen** clipping layer for the top planes and the
   fur edges catching light, plus a thin backlit rim against the night and dusk backdrops. paint it
   in the **highlight** stop.

so the **shadow · base · highlight** ramp given for every item below maps straight onto these
layers: base is the flat, shadow drives the two multiply passes (deepened for the core), and
highlight drives the add or screen pass. keep **one consistent light direction across every layer
and every stacked option** (upper left is a good default) so a wolf built from many pieces still
reads as one lit subject. use a soft fur brush and **smudge** the transitions; muted and painterly,
not hard bands. once a piece is fully shaded, **merge its flat plus its three clip layers into one
flat layer** before export; this bakes the shading and clipping into pixels, which matters because
ibispaint's PSD export does not carry blend modes or folder clipping reliably. **the one exception is
the recolourable coat:** keep its flat and shading as separate layers so meiker can recolour it (see
the files section).

## the structure: whole-wolf bases plus four separable things

this maker is **not** fully modular. i draw the **whole wolf** for each base, because that is how the
art keeps its style and stays in register (i draw one base, then **duplicate the file and edit the
copy** to make the next base, so every base shares the same drawing). the eyes, brows, mouth, pose,
build, life stage, tail, and body condition are all **drawn into the base** (the eyes and brows live
in the lineart layer, so they cannot be peeled off). only four things are kept **separate and
stackable**, because they already sit on their own layers: **colour, markings, scars, accessories.**

so meiker composites five kinds of thing:

1. **background** `[fixed]`, pick one (section a).
2. **base wolf** `[fixed]`, pick one: a complete drawing (lineart plus shading) carrying a specific
   pose, build, life stage, tail, eyes, brows, mouth, and condition. variety in any of those **baked**
   traits means drawing another base, not adding an overlay (sections b, c, d, e, and the base notes).
3. **colour** `[dynamic]`: the coat, and ideally the iris and marking regions as separate swatches, so
   one base recolours to any pelt and eye colour (section b3, c). keep colour regions split if
   independent recolour is wanted.
4. **overlays** `[mixed]`, stack several, drawn on a duplicate of the base then isolated to their own
   transparent layer so they work on any base: **markings** (section b4), **scars** (section f),
   **accessories** (section g).
5. **watermark:** a visible layer in no folder, on top, always shown.

**what is baked vs separable, at a glance:**

* **baked into the base** (drawn whole; variety = another base): pose, build, life stage, tail, body
  condition, pregnancy, missing limbs, spine, **eyes** (shape and state, including blindness),
  **brows**, mouth.
* **separable overlay or recolour** (drawn once, works on any base): **colour, markings, scars,
  accessories.**

**the identity trait this costs, and the fix:** blindness (a milky or clouded eye) matters for
matching an in-game wolf, and it is baked into the lineart. handle it as a **base variant**: duplicate
a base, paint the eye milky, and add the clawed scar over it. brow expression is mood, not identity,
so it can stay fixed per base.

**how to read the sections below**

* items tagged **(priority)** are the common ones, or the trait that makes a wolf recognisably that
  wolf. build these first; the rest can be a later update.
* the eyes, brows, and mouth sections (c, d, e) are now **things to draw into the base**, or to draw
  as base variants for the key states; they are not separate meiker slots.
* **hex** is given as a **shadow · base · highlight** ramp (core shade, then local colour, then rim or
  backlit edge). starting swatches; nudge for taste. for the recolourable regions (coat, iris,
  markings) the ramp becomes a `[dynamic]` swatch (name a layer `#c8871f` and meiker reads it as that
  swatch).

**forward-only note:** for a *future* base, drawing the eyes and brows on their own lineart sublayer
(separate from the body outline) would let them become overlays too. not worth redoing the current
one; blindness as a base variant covers the case that matters.

**the only things a seated full body still cannot show:** a true limp or gait (a sitting wolf can show
a tucked or stiff leg but not a limp in motion), and a standing side profile (landscape, will not fit
the canvas). absolute size does not read in a solo portrait, so small or large build must read as
proportion (chunkier or leaner body, bigger or smaller paws and head), not literal scale. everything
else (missing legs, missing tail, twisted leg, pregnancy, body scars, crooked spine) shows fine
seated, as a base variant.

---

## drawing it

the practical method, matched to the whole-wolf-base structure above.

**draw the first whole wolf: the master.** the adult, medium, four legged seated default, fully drawn
and shaded, on the standard canvas. inside this file, keep the **colour, markings, scars, and
accessories each on their own layer** from the start (that separation is what makes them isolable
later); the lineart carries eyes, brows, mouth, and the body.

**make every other base by editing a duplicate of the master file.** duplicate the file, then edit the
copy into the next base variant (a missing foreleg, an elder, a blind eye, a heavier build). because
each base starts as a copy, it is **automatically in register and in the same style** with every other
base; this is the whole reason to work from a duplicate rather than a fresh canvas. each finished base
is one `[fixed]` option.

**isolate the four separable things onto transparent layers.** colour, markings, scars, and
accessories are drawn on the base (in place, in style) and then lifted out so they overlay on **any**
base:

* **colour:** keep it as `[dynamic]` recolour region(s). split into **coat, iris, and marking**
  regions if independent recolour is wanted, so eye and coat colour move separately. the **coat region
  is fur only**; the **nose and other leather** (lip line, eye rims, claws, inner ear) stay on their
  own dark region outside the recolour, or the coat colour drags them along (section b3).
* **markings, scars, accessories:** draw each on a duplicate of a base for correct placement, then
  **hide or erase everything except that one element** so the exported layer is a transparent overlay
  of just the scar (or marking, or raven). merge each to one flat layer, name it clearly (`scar_face`,
  `mark_saddle`, `acc_ravenshoulder`), and put it in its `[mixed]` folder.

**work in several files.** the app caps layers per canvas, so keep the bases in their own files (one
per base, since each is a full drawing) and the overlays grouped by kind (one markings file, one scars
file, one accessories file), every overlay file drawn over a base reference so it registers. name each
file's folders with the meiker tag while drawing, so the export is already sorted.

**export a grouped PSD.** ibispaint: hide the reference and guides, then **share, PSD (Preserved
Layers)**; the folders and merged layers carry through. one PSD per file; combine them in photopea.

**tools that matter:**

* **clipping mask:** masks shading and markings to the shape beneath; the whole three shading layer
  method depends on it.
* **alpha lock:** locks a layer's transparency so a recolour stays inside the existing pixels; good
  for restaining a marking or a coat without redrawing the edge.
* **blend modes:** multiply for the two shadow passes, add (glow) or screen for highlights, overlay
  for subtle colour temperature.
* **fur brushes and smudge:** soft fur and airbrush brushes for coat edges and the ruff; smudge to
  break hard shading bands into painterly fur.
* **selection plus transform:** reuse a drawn shape (an ear, a paw) as the start of a variant instead
  of redrawing from nothing.

if a single merged piece ever comes out wrong from PSD export (a stray blend mode), fall back to a
**transparent PNG** of just that one piece and drop it into the PSD in photopea; never a cropped
export, cropping breaks alignment.

## drawing and studying wolves

craft notes for keeping the art reading as a real wolf, not a cat, a dog, or a fluffy mascot. the
whole grim tone dies if the anatomy goes cartoon, so this is worth study time before the master base.

**study real wolves, from reference, before stylising.** the reference section below has free photo
sources; pull a folder of grey wolves (front on and seated especially) and a wolf skull, and draw
studies first. the maker only works if the master base is right, so the study pays for itself.

**wolf, not a cat (the slip that keeps happening here).** a canine face drifts feline when the muzzle
is too short, the eyes too big and forward, and the skull too round. the fixes, roughly in order of
impact:

* **lengthen the muzzle.** cats have a short, pushed in face; a wolf's snout is long and squared,
  pushed well forward of the eyes. this single change fixes most cat like drawings on its own.
* **bigger, broader nose.** a cat's nose is a small triangle; a wolf's is a large, wide, blocky
  leather. draw it noticeably bigger than instinct says.
* **smaller, side set, round pupil eyes.** cat eyes are large, forward facing, and slit pupilled in
  daylight; wolf eyes are smaller, set further onto the sides of a longer skull, almond shaped, and
  **round pupilled**. slit pupils or big forward eyes read cat instantly.
* **a long wedge skull, not a round dome.** cats have a short, round cranium; a wolf skull is a long
  wedge from ears to nose. lengthen the whole head, not just the snout.
* **ears wider, lower, and rounder.** cat ears are tall and perched close together on top of the
  head; wolf ears are rounder tipped and set further apart and lower.
* **the seat.** a seated cat is compact and vertical with a neatly wrapped tail; a seated wolf is
  bigger and pitches its weight forward through a deep chest and heavy front legs. draw the wolf
  taking up more room and leaning slightly forward, not tucked upright.

**what makes a wolf read as a wolf, not a dog:**

* **long legs, big paws.** wolves are leggy and their paws are oversized (snowshoes); a short legged,
  small pawed canid reads as a dog immediately.
* **deep but narrow chest.** the ribcage is keel deep yet **narrow from the front**, so a front facing
  wolf's chest is tall and slim, not a broad barrel; the front legs sit close together.
* **blocky, long muzzle with a shallow stop.** the brow to muzzle transition is gentle, not the steep
  forehead of many dogs; the muzzle is long and squared, not short.
* **small, rounded, well furred ears** set fairly low and wide, small relative to the head; big pointy
  ears read husky or shepherd.
* **straight, low carried tail.** a wolf's tail hangs straight or low, or streams level in motion; a
  tail **curled up over the back is a spitz or husky tell** and instantly breaks the illusion. tail
  carriage still shifts with mood (tucked in fear, raised in threat), just never a curled ring.
* **a cape or ruff, and a colour saddle.** the longer guard hair over the shoulders and the darker
  saddle over the back are classic wolf; agouti banded fur, not flat colour.
* **eyes.** amber, yellow, and brown are the norm, set with a slight slant; **keep them naturalistic**,
  no big round anime eyes, no bright unnatural colours (blue is rare, and pink only for the albino).

**anatomy that the traits depend on:**

* **digitigrade legs:** wolves walk on their toes, so the joint halfway up the back leg is the **hock
  (ankle), not a backward knee**; getting this wrong makes every seated and missing limb variant look
  broken. study the hindleg fold of a seated dog or wolf.
* **the seat, front on:** in a front facing seat the haunches splay to the sides, the front legs drop
  straight and close, the paws turn slightly out, and the tail curls around the paws. foreshorten the
  muzzle. this exact pose is worth several studies, since every base variant is built on it.
* **fur flow, in clumps not hairs.** map how the coat flows: radiating from the muzzle, sweeping back
  over the skull, fanning from the neck into the ruff, and lying down the legs. draw fur in **clumps
  and breaks in the silhouette**, never as stroked individual hairs; the silhouette should read as
  wolf even as a flat shape.

**expression, for the mouth, brow, ear, and mood options:**

* wolves emote with the **whole body and face**: ears (forward alert, pinned back fear or aggression),
  eyes (wide, narrowed), lips (drawn back and vertically wrinkled for a real snarl, showing the long
  canines), and raised hackles over the shoulders. study wolf body language photos for the snarl, the
  submissive squint, and the play bow so the sign and mouth options read true.
* **elder wolves** grey at the muzzle first, then the brows; eyes sink, the coat thins and loses
  gloss, the frame gets bonier. study old dogs and wolves for the base variant.

**common mistakes to avoid:** the husky face (mask plus blue eyes plus curled tail), an over fluffy
cartoon tail, a short dog muzzle, a broad barrel chest, tiny paws, oversized eyes, and flat single
colour coats. when unsure, go back to the photo reference; a real wolf is stranger and leaner than
memory suggests.

## ibispaint tips (using the tools i picked it for)

**symmetry ruler, for the frontal base.** the maker's wolf is seated and front facing, so a
**vertical line symmetry ruler** (tools, ruler, symmetry, vertical, snapped to the canvas centre)
draws both sides at once: skull, ruff, chest, both front legs, both eyes, all guaranteed even. draw
the master base and every **symmetric** thing with it on: agouti banding, saddle, countershadow,
matched eye colour, brow, a centred mask. then **turn symmetry off** for everything a hard life makes
uneven: a single face or body scar, one torn ear, one blind or clouded eye, heterochromia, a twisted
leg, an off centre marking. a clean symmetric base plus deliberately broken symmetry for damage is
exactly the "clean wolf is the exception" look this world wants.

**vector lineart, for crisp re-editable edges.** put lineart on its **own layer above the flats**,
drawn with ibispaint's vector or curve line tools plus a high **stabilizer** setting, so outlines
stay smooth and a curve can be nudged later without repainting colour. keep it to the places that
actually need a hard edge: eye rims, teeth, claws, the base silhouette, accessory shapes; let the fur
edges stay **lineless** and defined by shading instead, which reads more like painted wildlife than a
sticker. use **force fade** for tapered stroke ends.

**shape tool, for anything that must be geometric or paired.** perfect **circles for irises and
pupils** (draw one eye, then mirror it with symmetry so both match exactly), straight guide lines,
the safe area boxes, the watermark, and accessory geometry (collar bands, bone and tooth charms,
beads). it kills the wobble that freehand circles give an eye.

**brushes.** **dip pen (hard)** for lineart; the **fur, pampas grass, cloud, and fluffy** brushes for
coat edges, the ruff, and winter coat; **airbrush** for the soft form shadow pass; **smudge and blur**
to melt shading bands into fur; a **chalk or textured** brush for scar tissue, ash war paint, and dry
grizzled flecking. save a **custom fur brush preset** for the coat edge once it feels right, so every
pelt shares the same fur language.

**a locked guides layer, at the top, low opacity.** the centre line, a thirds grid, and the two safe
areas (the 9:16 and the 1:1 head crop) on one locked layer kept visible while drawing and
**hidden before every export**. reuse the same guides layer in every file so all pieces register.

**save the hex ramps as a custom palette.** drop the shadow, base, and highlight of the coats, eyes,
and scars into an ibispaint palette so each stop is one tap; it keeps colour consistent across the
dozens of pieces and files.

**colour tidily with clipping and alpha lock.** flats on their own layer; shading as **clipping**
layers above (never spilling past the shape); **alpha lock** a finished flat to restain it without
touching the edge. this is what lets one marking or coat recolour cleanly for the `[dynamic]` swatch.

**colouring the flats: bucket the flat, hand paint the rest.** the flat base colour wants to be **one
even, gap free fill**, which is exactly what the **bucket** is for, and it has to stay a single solid
colour so the `[dynamic]` coat recolours correctly (texture and shading live on the layers above, not
in the flat). then **alpha lock** that flat and it restains in one tap. everything on top, the three
shading layers, fur edges, markings, scars, is **hand painted**: the bucket cannot do form shadow, and
it cannot give the ragged fur silhouette that reads as wolf instead of sticker. the one snag is that a
bucket needs a closed shape and the fur edges are lineless, so a raw fill leaks: in ibispaint, set the
bucket's **reference to the lineart or silhouette layer** and nudge **expansion** up a touch to fill
under the anti aliased edge with no white halo, or block the silhouette as a closed shape first,
bucket the inside, then hand paint the fur edges out over it.

## general art tips

medium and subject aside, the habits that keep a modular maker sane. some are obvious; obvious still
gets skipped.

* **use lots of layers, never one.** separate the sketch, lineart, flat, each shading pass (clip),
  markings, and details, and name them. this is not neatness for its own sake: the recolourable flats
  and the stackable options only exist because each thing is on its own layer.
* **keep the layered source file.** the exported PSD is the delivery, not the working file; keep the
  editable ibispaint file for every category. **duplicate a layer before merging or flattening** so an
  editable version always survives.
* **a temporary neutral backdrop while drawing.** the final export is transparent, but drawing over
  nothing makes values and edges hard to judge; keep a **mid grey fill layer at the bottom** to read
  against, and hide it before export.
* **values before colour.** the form has to read in light and shadow before hue matters; block or
  squint check the values so the wolf is solid, not flat. keep the palette **muted and limited** per
  the world, no bright saturation.
* **vary edge hardness.** hard edges on eye rims, teeth, and claws; soft, broken edges on fur and
  form shadow. edge control is one of the biggest realism levers and costs nothing.
* **flip the canvas horizontally now and then.** ibispaint can mirror the view; a face that looked
  fine flips obviously wrong once its errors show. essential for the frontal base.
* **zoom out and check the silhouette.** the wolf must read as a wolf as a flat shape; if the
  silhouette is unclear zoomed out, rendering will not rescue it.
* **test stack early in meiker.** once the base and a handful of options exist, throw them in and
  switch between them. catching alignment drift or style drift after ten pieces is cheap; after a
  hundred it is a redraw.
* **hold one stylisation across every part.** a photoreal eye beside a flat cel body looks broken;
  pick a rendering level (the stylised realism in the tone section) and keep it identical across
  coats, eyes, scars, and accessories, so any combination still looks like one wolf.

## assembling the psd in photopea

photopea ([photopea.com](https://www.photopea.com/)) is a free, browser based editor that opens and
**saves real layered PSD**, which is what meiker needs. since ibispaint now exports a grouped PSD
directly, photopea's job is mainly to **combine the several per category PSDs into one, confirm the
meiker tags, and add the watermark**. (if the whole maker ever fit in one ibispaint file, its folders
could be tagged in ibispaint and the PSD uploaded straight to meiker, skipping photopea, but a full
maker will not fit.)

1. **new document at the final size:** 900 by 1200 px (portrait), transparent background.
2. **open each per category PSD and drag its folders into this document.** they were all made on the
   same 1200 by 1600 canvas, so they align; scale the whole combined set down to the 900 by 1200
   document together, never piece by piece. the folders arrive already sorted, so most of the
   structure is done. (if any single piece came out wrong from PSD export, drop in a **transparent
   PNG** of just that piece instead.)
3. **one folder per slot** in the layer structure above (background, body base, coat colour, markings,
   eyes, and so on). the ibispaint folders usually already cover this; just make sure each slot ends
   up as exactly one folder. in photopea a folder is a group (right click, group into new group).
4. **confirm each folder's meiker tag** in its name: `[fixed]` (pick one), `[mixed]` (stack several),
   `[optional]` (a single toggle overlay), `[dynamic]` or `[color-picker]` (recolourable). if the tags
   were already named in ibispaint, this is just a check. for the coat and other recolour ramps, name
   the swatch layers with the hex (for example a layer named `#c8871f`) so meiker reads it as a swatch.
5. **the watermark:** a small howlbert brand mark as a **visible layer that sits in no folder**, on
   top, so meiker cannot toggle it off. place it clear of both the 9:16 and the 1:1 head crop safe
   areas.
6. **save as PSD** (file, save as PSD), then upload that PSD to meiker per its instructions.

work in passes: assemble and upload the priority items as a first playable version, then add more
options into the same PSD later (meiker lets me update a game after launch).

## the files (what goes in each)

the whole maker is a handful of ibispaint files, not one. each is drawn on the standard 1200 by 1600
canvas so everything registers.

**the fixed set (always these):**

* **master base** — the clean default wolf, and the file every other base is duplicated from. it
  holds: the **guides** layer (top, hidden on export), the **lineart** (eyes, brows, mouth, body), the
  **coat flat** on its own solid layer, the **iris flat** as its own small region, and the **three
  shading layers**. no markings, scars, or accessories, those are overlays. so the base is a fully
  coloured, plainly rendered wolf, **not just an outline, and not just lineart plus shading**, the
  coat flat is what meiker recolours.
* **markings** — a locked flattened base as the bottom reference, then each marking drawn on it and
  **isolated to its own layer**; `[mixed]` folder.
* **scars** — same base reference, each scar / notched ear / lick patch / ritual glyph isolated;
  `[mixed]` folder.
* **accessories** — same base reference, each item (flower crown, feather, collar, raven, insects)
  isolated; `[mixed]` folder. split into two files (worn items / companions and insects) only if it
  hits the layer cap.
* **background** — each backdrop on its own layer; no base reference needed (it sits behind);
  `[fixed]` folder.

**plus one file per base variant**, each a duplicate of the master, edited: blindness first, then
missing foreleg or hindleg, twisted leg, crooked spine, small or large build, life stages, pregnancy,
gaunt. start with one or two.

**not files:**

* **coat and eye colour** are not drawn per pelt. the coat flat is recoloured by meiker through
  **hex-named `[dynamic]` swatch layers** set up at assembly; drawing a wolf per colour is the mistake
  to avoid.
* **watermark** is a single layer added in photopea.

**reused in every file:** the guides layer and a flattened, locked base reference, pasted in so the
isolated elements land in register.

**count:** the fixed set is **5 files** (master base, markings, scars, accessories, background); add
one per base variant. a realistic v1 is about **6** (the 5 plus a blind base).

**the one technical note on the coat:** the recolourable coat keeps its **flat and its shading as
separate layers** (shading on multiply above the flat), so meiker recolours the flat to any pelt while
the shading rides on top and still reads. this is the one place not to merge flat and shading; the
isolated overlays (markings, scars, accessories) do get merged to one flat layer each. **check that
the coat's multiply shading survives the PSD export** (test one recolour in meiker); if ibispaint
drops the blend mode, use a **low opacity dark shadow layer in normal mode** instead, which exports
reliably and still recolours cleanly underneath.

## step by step (blank canvas to first upload)

the goal of the first pass is a **small playable slice**: one whole-wolf base, a few coat recolours, a
couple of markings, a scar or two, and an accessory, assembled and live on meiker. everything else is
added later. concrete order:

1. **new ibispaint canvas:** 1200 by 1600 px, **transparent background** (no fill).
2. **guides layer.** with the shape tool, draw a centre vertical line, a light thirds grid, and mark
   the 9:16 (540 by 960 proportion) and 1:1 (600 by 600) safe crop boxes. lock it, drop to low
   opacity, keep it top. this layer gets reused in every file.
3. **rough the master base.** new layer, low opacity, **symmetry ruler on (vertical)**: sketch the
   adult, medium, four legged **seated, front facing** wolf. proportions matter most here; every base
   and overlay keys off this drawing.
4. **lineart.** new layer above the sketch: clean the outline, **eyes, eye rims, brows, mouth, and
   teeth** (all of these live in this lineart layer), with the vector or curve tool and high
   stabilizer, symmetry on. leave fur edges lineless.
5. **flat the coat, on its own colour layer.** block the coat in the **base** stop of a chosen ramp
   (wolf grey to start). keep it a single solid colour on its own layer so it can be the `[dynamic]`
   recolour; keep the iris its own small colour region too.
6. **three shading layers** over the flat, each a **clipping** layer (see rendering): multiply form
   shadow, deeper multiply core, add or screen highlight, one light direction. smudge the transitions.
7. **save this as the master base file.** keep colour, markings, scars, and accessories on their own
   layers inside it. flatten a copy of the whole wolf to a low opacity, locked **reference** layer
   (used at the bottom of the overlay files so they register). this file is base number one, a
   `[fixed]` option.
8. **a second base, by editing a duplicate.** duplicate the file and edit the copy into a variant, a
   good first one is the **blind base**: paint one eye milky on the colour layer and add the clawed
   scar over it. it starts in perfect register and style because it is a copy. that is base number two.
9. **the overlay files.** one file each for markings, scars, accessories, every file built over the
   locked base reference. draw each element in place, then **hide or erase everything except that
   element** so it is a transparent overlay, merge it flat, name it (`mark_saddle`, `scar_face`,
   `acc_raven`), and drop it in its `[mixed]` folder. for the coat, set up two or three pelts as the
   `[dynamic]` recolour.
10. **export each file as a PSD:** hide the guides and reference, then **share, PSD (Preserved
    Layers)**. one PSD per file, folders intact.
11. **combine in photopea** (see that section): new 900 by 1200 transparent doc, drag in the base
    folders (`[fixed]`), the coat (`[dynamic]`), and the overlay folders (`[mixed] markings`,
    `[mixed] scars`, `[mixed] accessories`), scale the set together to align, confirm the tags, name
    the coat and iris swatch layers with their hex, and add the **watermark** on top in no folder. save
    as PSD.
12. **upload to meiker** per its instructions, click through: pick a base, recolour it, add a marking,
    a scar, an accessory. check registration and tags. fix any drift in the source file, re-export,
    re-assemble.
13. **expand** per the build order: overlay breadth first (cheap), then more base variants (the big
    lift), then more backgrounds.

## a. background (`[fixed]`, pick one)

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

## b. the base wolf (drawn whole; `[fixed]`, variety = another base)

the whole seated wolf and everything painted into it. **all of this is baked into the base drawing**,
so each combination below is a separate `[fixed]` base, made by editing a duplicate of the master. the
two exceptions that stay separable: **coat colour** (b3) is the `[dynamic]` recolour, and **markings**
(b4) are a `[mixed]` overlay drawn on the base then isolated. everything else here (build, life stage,
condition, tail, legs and posture) is a base variant.

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

**the coat `[dynamic]` region is fur only.** the non-fur "leather" features must sit on **separate
regions outside the coat recolour**, or recolouring the coat drags them along (a green coat would give
a green nose). keep these dark and separate, the same way the iris is its own region:

* **nose leather:** near black on every wolf regardless of coat (`#141210` shadow · `#26221f` base ·
  `#3a352f` highlight). optional swatch for the rare cases: albino pink `#c78a8c`, dilute or snow-nose
  liver `#7a5a52`.
* **lip line, eye rims, claws, inner ear:** same near-black leather, kept out of the coat region.

so the recolourable coat covers the pelt; nose and leather stay dark across every recolour.

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

### b4. markings (`[mixed]` overlay, isolated from the base)

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

### b5. body condition and pregnancy (base variants)

* [ ] body condition: gaunt or starved (ribs, sharp hips), for hungry or wasting wolves
* [ ] body condition: heavy or well fed (fuller barrel)
* [ ] lean or normal is the default base, no overlay
* [ ] pregnant belly overlay (priority): rounded barrel, heavier teats, for expecting dams

### b6. tail (drawn into the base)

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

## c. eyes (drawn into the base; key states as base variants)

the **eye shape and state are baked into the lineart**, so they belong to the base, not a swappable
slot. **eye colour still varies** if the iris is kept as its own `[dynamic]` recolour region (do
that). the colours below are the intended range for that swatch; the **states** (milky/blind,
clouded, heterochromia, failing sight) are **base variants** to draw when a wolf needs them, blindness
first since it is a real in-game trait.

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

## d. eyebrows (drawn into the base)

the brow is in the lineart, so it belongs to the base; brow expression is mood, not identity, so it
can stay fixed per base rather than becoming its own variant. the brow markings below are the
exception, drawn as `[mixed]` markings (section b4, f), not baked.

* [ ] neutral brow (priority)
* [ ] raised or worried (inner brow up)
* [ ] furrowed or angry (inner brow down)
* [ ] relaxed or soft
* [ ] brow markings ("eyebrow" points or dots above the eyes): light or dark marking (see section b4)

---

## e. mouth (drawn into the base)

the mouth is in the lineart, so it belongs to the base; draw the default (closed) on the master, and
draw a snarl or other expression only as a base variant if a wolf needs it.

* [ ] closed or neutral (priority)
* [ ] slight open or relaxed pant
* [ ] snarl (priority): lips curled, teeth bared, also shows dental traits
* [ ] happy, tongue out
* [ ] tongue lolling, heavy pant (hot or exhausted)
* [ ] grimace or sick (drooping)
* [ ] crooked or missing teeth (visible in open or snarl mouths)

---

## f. scars and marks (`[mixed]` overlay, stack several)

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

## g. accessories (`[mixed]` overlay, stack several)

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

1. **one master base**, the adult, medium, four legged seated default, fully drawn and shaded, with
   colour, markings, scars, and accessories each already on their own layer.
2. **v1 the low-effort slice:** make the coat a `[dynamic]` recolour (a few pelts), and draw a handful
   of `[mixed]` overlays (markings, scars, one or two accessories), plus one background. assemble and
   upload. this is a real, playable maker: pick the base, recolour, add markings, scars, accessories.
3. **overlay breadth (cheap, high value):** more markings, more scars, more accessories. each is drawn
   once and works on every base, so this is where variety is cheapest; do it before more bases.
4. **base variants (expensive, do as needed):** the whole-wolf redraws, each made by editing a
   duplicate of the master, in rough priority: **blindness** (the identity trait baked into the
   lineart), then missing foreleg or hindleg, twisted leg, crooked spine, small or large build, life
   stages, pregnancy and body condition. these are the big lift; add the ones players actually want.
5. **more backgrounds** last.

## reference (free stock, safe to use)

free, commercially usable photo sources for wolf anatomy, coats, poses, and expressions, in case
they help. the first three are CC0 (public domain, no attribution needed, safe even for a monetized
project); the last two are mixed, so check the licence shown on each individual file before using it
as more than loose study:

* pexels, wolves: https://www.pexels.com/search/wolf/ (CC0)
* unsplash, wolves: https://unsplash.com/s/photos/wolf (free licence, CC0 like)
* pixabay, wolves: https://pixabay.com/images/search/wolf/ (CC0)
* wikimedia commons, canis lupus: https://commons.wikimedia.org/wiki/Category:Canis_lupus (public domain and CC, per file)
* flickr, filtered to commercial use: https://www.flickr.com/search/?text=wolf&license=9%2C10 (CC0 and public domain only)

for the grim traits that ordinary stock will not cover (scars, milky blind eyes, missing limbs, old
injuries, gaunt winter condition), wolvden's own art (https://www.wolvden.com/) and the wolf photos
on wikimedia's wildlife rehabilitation and injured animal categories are the closest real reference;
otherwise these carry across from dogs and other canids.

**referencing, shapes, and tracing (and the youtube speedpaint).** using these for **construction is
always fine and encouraged**: blocking the big shapes, checking proportion, laying gesture under the
drawing. that is study, not copying, and it is exactly what fixes the cat like face. **tracing** is a
narrower thing: the CC0 sources (pexels, unsplash, pixabay) and public domain wikimedia or flickr
files legally allow derivative art including tracing, but the **share alike and non commercial files
do not fit a monetized project**, so any tracing must come only from the CC0 and public domain ones.
because the process is going on youtube as a speedpaint, three cautions: a **line for line trace draws
copyright complaints and art community backlash even when it is legal**; it sits awkwardly beside this
server's own **no tracing rule**; and for a maker a traced photo is one animal in one pose and light
that will not match or recolour across the other options anyway. so the useful move is to **reference
hard for shapes and construction, draw the final art by hand, and credit the reference photos in the
video description**; keep any tracing to a loose structural underlay from a CC0 or public domain image
that is then fully redrawn and stylised, not a finished traced line.

## working solo: scope and constraints

* this is a large project for one person, so pace it. the base variants (missing limbs, builds, life
  stages) are the expensive part, each a full seated redraw rather than an overlay. do not draw them
  all up front; ship the priority items as a first playable maker and add the rest into the same PSD
  over time (meiker lets me update a game after launch).
* the master base is the whole foundation. get it fully drawn, shaded, and registered before drawing
  anything that stacks on it; every misalignment there multiplies across every option that follows.
* both apps cap layers per canvas, which is why the work splits into several files by category (see
  the workflow section); procreate's cap is higher, so it needs fewer splits. do not fight the limit
  by cramming one giant canvas.
* usage: the outputs are mine to use for howlbert (the shop, the crowdfunder, promo) because i drew
  them, and players generating and sharing their builds is the whole point. meiker takes no license
  to the art. the only outside rights to mind are the free stock references above; use the CC0
  sources freely and check the licence on the mixed ones before leaning on them.
