# Book One: The Blinking

Staff reference for the in-bot plot system (`world_state.plot_phase`). **Game canon overrides outline text**; phases supply mechanical pressure and den-news prompts, not a fixed script.

## Commands

| Command | Who | Purpose |
|---------|-----|---------|
| `/world action:plot` | Everyone | Current phase, beat text, active mechanics |
| `/setplotphase phase:N` | Admin | Set phase `0` (off) through `12` |
| `/plotadvance` | Admin | Bump phase by 1 |

Advance phases when RP earns them — not on a fixed day counter.

## Phases (mechanical summary)

| Phase | Title | Sunrise effects |
|-------|-------|-----------------|
| 1 | Bitten Moon | All wolves −1 mood |
| 2 | White Omen | Thistlehide scout survey +1 standing; quest `blink_border_patrol` |
| 3 | Peak Bleeds | Mountain travel DC +2; Greyspire hunt +10% |
| 4 | Warm Below | Silverrush −2 thirst; fishing debuff; fish rot accelerates |
| 5 | Belly Silence | Mistmoor rot-lung pressure; quest hooks |
| 6 | Border Paranoia | Cat trust −3; sniff border fights +25%; rogue crime branch |
| 7 | Iron Debt | Forest travel DC +2; cat pact forge DC +2; steal caught −2 extra standing |
| 8 | Mill Tooth | Explore investigate → fossil tooth reward; `blink_mill_scout` |
| 9 | Memory Bites | Howl −3 mood if pack unity < 5 |
| 10 | Blame Spiral | All Great Pack unity −1; cat trust −2 |
| 11 | Ash Naming | Howl +1 unity; creek drink +5 thirst; `blink_ash_naming` |
| 12 | Pact Remembered | Cat trust +5; warm-river debuffs end |

## Quest board keys

- `blink_border_patrol` — patrol
- `blink_river_crisis` — fishing ×2
- `blink_wind_witness` — sniff (phase 6+)
- `blink_mill_scout` — explore
- `blink_ash_naming` — howl ×3
- `blink_rogue_ledger` — crime ×2 (rogues)

## Splinter (rogue lane)

Exiled Greyspire; not the main antagonist. Mechanics:

- `/bones action:crime` without target during phase 6+: extra bones or border catch (−standing)
- `/field action:sniff`: limp rogue scent flavor
- `/explore investigate` during phase 8+: mill tooth (all wolves)
- Redemption/death remain RP + combat/standing

## Firepaw (healer apprentice lane)

Thistlehide **Medic Apprentice** under Sypha. **Requires wolf name Firepaw + thistlehide affiliation.**

| Phase | Mechanic |
|-------|----------|
| **1–5** | `/sniff`: **+2 mood**, **sniff bonus** (hunt/track +15%), quest **blink_healer_listen** progress |
| **6–10** | First `/sniff` each sunrise: **+1 standing**, **+1 mood** (once/day plot reward) |
| **5–11** | `/medic action:treat`: **+2 HP** on heal outcomes; quest **blink_healer_touch** progress |
| **5–11** | First `/medic action:treat` each sunrise: **+1 standing** (packmate) or **+2 mood** (self) |
| **5–11** | **Firepaw** may **`/medic action:treat patient:`** (apprentice border-triage) |
| **5+** | `/medic action:observe`: **+2 mood**, **−2 medicine strain**, treat quest progress |

Quest skill rewards: **blink_healer_listen** → medicine +1 · **blink_healer_touch** → medicine +1

## Living world (use alongside phases)

Cat pacts, `/sniff` border fights, season stash failures, territory wars, diseases, restricted herbs, sacred visits, collab hunt/patrol, raccoon, predators, Whispering Wild — all continue during Book One.

## Canon anchors (affiliations)

- **Thistlehide:** Finnpelt, Mossgaze, Kanami, River'Shroud, Pale'Step, Skye, Thyme, Firepaw, Eltanin
- **Silverrush:** Saltmuzzle, Rift, Rivenmaw, Ripple, Aromis
- **Mistmoor:** Murkvein, Mirewort, Gasp
- **Greyspire:** Grim, Talus; **Splinter** exiled rogue

## Ending Book One

Set `/setplotphase phase:0` when staff close the arc, or leave at phase 12 with resolution mechanics active.
