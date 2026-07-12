# twine teaser — "first sunrise" (draft)

a short, free, branching interactive-fiction teaser (`docs/GROWTH_IDEAS.md` §21). goal: a
stranger plays a 3–5 minute wolf story, feels one real howlbert mechanic bite (injury →
medic-or-not → death saves → permadeath), and ends on a single door: **join the discord and
build a wolf of your own.** no signup, no download, plays in a browser.

## how to use this

1. get **[twine](https://twinery.org/)** (free; browser or desktop app). story format:
   **harlowe** (default) is fine.
2. either build it passage-by-passage from the outline below, **or** paste the twee source
   (the fenced block at the bottom) into a text file and use twine's **Import → From File**
   (save the block as `first-sunrise.twee` first). twee is twine's plain-text format —
   `:: PassageName` starts a passage, `[[choice text->TargetPassage]]` is a link.
3. replace every `DISCORD_INVITE_URL` with your real invite, and `STRAW_PAGE_URL` with
   `https://howlbert.straw.page`.
4. **Build → Publish to File** gives one self-contained `.html`. host it free on
   **itch.io** (as a browser game — great for discovery), **neocities** (alongside your other
   site pages), or drop it on the straw.page. link it from the discord and every art post.

## design intent

- **one mechanic, felt not explained.** the whole arc exists to make the *treat-yourself vs
  find-the-medic* choice and the *death saves* land emotionally, because that's the beat that
  makes howlbert's permadeath feel real. everything else is atmosphere.
- **every ending routes to the same door** (the `Hook` passage). win, lose, or limp home —
  the story always closes on "that was one sunrise; the wolf you'd actually build waits inside."
- **honest tone.** the dark/bone voice of the brand: cold, spare, a little merciless. don't
  over-explain the rules; let the consequence teach them. keep the death path *possible* — a
  teaser where nothing bad can happen doesn't sell a permadeath game.
- **short.** ~12 passages, most branches 2–3 clicks deep. if it takes more than ~5 minutes
  you've lost the top-of-funnel reader.

## optional styling (harlowe)

paste into the story **Stylesheet** for the bone-on-dark look:

```css
tw-story { background: #14110f; color: #d8cfc2; font-family: Georgia, "Times New Roman", serif; line-height: 1.6; }
tw-link, .enchantment-link { color: #c9a86a; border-bottom: 1px solid #6b5836; }
tw-link:hover { color: #e9d3a0; }
```

---

## story outline (passages & branches)

- **Start** → slip out alone, or wait for the dawn patrol
  - **AloneHunt** → take the sure hare, or gamble on the sick elk
    - **Hare** → a full-enough belly, then a rival's scent → **Border**
    - **Elk** → you land it but a hoof breaks your leg → bind it yourself, or find the medic
      - **SelfTreat** → the wound festers → **Fever**
        - **Fever** → the infection climbs → **DeathSave**
          - **DeathSave** → **Survive** or **Death**
      - **FindMedic** → set, packed, you'll limp but live → **Hook**
  - **PackHunt** → the big prey falls with the pack; warmth, standing, a den → **Hook**
- **Border** → back down, or hold the line (bluff) → **Hook**
- **Survive / Death / (all leaves)** → **Hook** → the door out

---

## twee source (import-ready draft)

```twee
:: Start
The frost hasn't lifted. Your mother's scent is already thinning out of the den —
three sunrises gone now, taken by the river rot before the medics could gather
enough lungwort to matter.

You are hungry. The pack does not feed a wolf who will not hunt.

[[Slip out alone, before the others wake.->AloneHunt]]
[[Wait for the dawn patrol and hunt with the pack.->PackHunt]]

:: AloneHunt
Fog to your hocks. Alone, the whole forest is yours and none of it is safe.
Two scents cross the wind: a hare in the bracken, close and certain — and,
further off, an elk that moves wrong. Sick. Slow. Too much meat for one wolf,
if the one wolf lives to eat it.

[[Take the hare. Small, but sure.->Hare]]
[[Go for the elk. Land it and you eat for days.->Elk]]

:: Hare
You eat. The hunger loosens its grip — for now. A lone belly is never full for
long, and the cold is only getting deeper.

Then the wind shifts, and it carries another wolf. Not pack. A rogue's scent,
laid deliberately across the border you were about to cross.

[[Back away. It isn't worth your throat.->Border]]
[[Hold your ground and answer the scent.->Border]]

:: Elk
The elk is dying already; it just doesn't know the order of things. You do.
You take it at the hamstring — and its hoof takes you back, once, hard, against
the foreleg. Bone gives with a sound you feel more than hear.

The elk goes down. So, nearly, do you. You've made your first real kill, and
you're bleeding into the snow, and there is no one here.

[[Pack the wound with cobweb and moss yourself, and push on.->SelfTreat]]
[[Leave the meat. Limp home and find the medic.->FindMedic]]

:: SelfTreat
Cobweb slows the bleed. Moss hides it. It is not the same as mending it.
You drag what meat you can and tell yourself the heat in the leg is just the
work. By the second sunrise it is not just the work.

[[->Fever]]

:: Fever
The wound has gone tight and shining and hot. The fever walks up your spine one
vertebra at a time. This is where a great many wolves' stories quietly end —
not in a fight, in a leg they should have shown to a healer.

[[Lie down in the cold and let your body decide.->DeathSave]]

:: DeathSave
Three breaths. Three rolls of the dying.

(This part is real. In the world past this story, death is permanent, and *death
saves* are the thin thread a life hangs from when the healers are too far.)

You pass the first breath. You pass the second. The third comes slow, and
colder than the others.

[[...->Survive]]
[[...->Death]]

:: Survive
— and holds. Barely. You wake to a medic's breath fogging over your muzzle,
her paw already splinting the leg she found you dying on. You lived.

Most don't. You should know that going in.

[[->Hook]]

:: Death
— and doesn't come. The cold finishes what the elk started. By morning the den
news carries a single line: your name, your cause, and the one thing you did
that a wolf would remember you for.

That's how it ends here. Every wolf. Eventually. The only question the game ever
asks is *what you did with the sunrises in between.*

[[->Hook]]

:: FindMedic
You leave good meat to the crows and limp three miles on three legs to reach
her. The medic doesn't scold you. She sets the bone, packs it with comfrey,
binds it tight. "You'll limp a moon," she says. "You'll limp."

Knowing when to carry your own wound and when to lay it in front of someone
else is, in the end, the difference between a scar and a grave.

[[->Hook]]

:: PackHunt
You wait. The patrol takes you in without ceremony, and together the big prey
falls the way it never falls for one wolf alone. You eat well. Your standing
rises. And for the first sunrise since your mother, the cold at your flank is
someone else's warmth, not just absence.

A pack is that: a full belly, a treasury, a border worth defending, a war worth
surviving. It is also the thing you can lose.

[[->Hook]]

:: Border
Whichever way you turned, the border holds its breath and lets you go — this
time. A lone wolf's whole life is this: small choices at the edge of things,
each one deciding whether there's a next sunrise.

[[->Hook]]

:: Hook
That was one wolf. One sunrise. One choice out of ten thousand.

The wolf you'd actually build — its bloodline, its bonds, its diseases and
rivals and the pack it dies defending — waits in the wild past this page.

[[Enter the wild → join the pack.|DISCORD_INVITE_URL]]
[[See the world first.|STRAW_PAGE_URL]]
```
```

**before publishing:** swap `DISCORD_INVITE_URL` and `STRAW_PAGE_URL` for the real links, and
run it once yourself end-to-end so every branch actually reaches `Hook`.
