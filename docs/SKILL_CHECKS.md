# Basil skill checks

Full catalog lives in `engine/skill_checks.py` (69 scenarios).

## Commands

- `/skills category:… check:…`; roll with modifiers (tracking weather, yarrow on stabilize, etc.)
- `/skills opponent:`; opposed checks roll **both wolves** (dominance, covered trail, trap detect)
- `/skilllist category:…`; reference DCs
- `/rpg action:roll`; freeform rolls for opposed contests or custom scenes

## Herb preparation loop

1. `/field action:forage` or `verge` → **fresh** stack in herb bag
2. `/herbs action:bag`; view stacks (`#ID`)
3. `/herbs action:prepare`; `dry` · `poultice` · `tea` · `ointment` on `stack:ID`
4. `/medic action:treat` with `stack:ID`; respects fresh toxicity, form requirements, potency

Fresh herbs rot after **1 sunrise** without drying. Shop/inventory herbs stay stable.

## Categories

| Category | Examples |
|----------|----------|
| tracking | fresh trail DC 8 → faint DC 25, blood scent, covered trail |
| stealth | silent move, hide, sneak prey (advantage) |
| howling | locate packmate, storm howl |
| social | intimidate, persuade alpha, truce DC 18 |
| spiritual | omen, ancestors DC 20, cleansing ritual |
| survival | river, blizzard shelter, stabilize, set bone |
| herb_prep | chew poultice, mix tea, dry storage, antidote |
| crafting | splint, travois |
| navigation | landmarks, blizzard camp |

## Daily track

`/field action:track trail_age:recent` uses the tracking catalog instead of the old random fail %.
