# Book One: The Blinking

Staff reference for the in-bot plot system (`world_state.plot_phase`). **Game canon overrides outline text**; phases supply mechanical pressure and den-news prompts, not a fixed script.

## Commands

| Command | Who | Purpose |
|---------|-----|---------|
| `/world action:plot` | Everyone | Current phase, beat text, active mechanics |
| `/setplotphase phase:N` | Admin | Set phase `0` (off) through `12` |
| `/plotadvance` | Admin | Bump phase by 1 |

Advance phases when RP earns them; not on a fixed day counter.

## Phases (mechanical summary)

| Phase | Title | Sunrise effects |
|-------|-------|-----------------|
| 1 | Bitten Moon | All wolves −1 mood |
| 2 | White Omen | Thistlehide scout survey +1 standing; quest `blink_border_patrol` |
| 3 | Peak Bleeds | Mountain travel DC +2; Greyspire hunt +10% |
| 4 | Warm Below | Silverrush −2 hydration; fishing debuff; fish rot accelerates |
| 5 | Belly Silence | Mistmoor rot-lung pressure; quest hooks |
| 6 | Border Paranoia | Cat trust −3; sniff border fights +25%; rogue crime branch |
| 7 | Iron Debt | Forest travel DC +2; cat pact forge DC +2; steal caught −2 extra standing |
| 8 | Mill Tooth | Explore investigate → fossil tooth reward; `blink_mill_scout` |
| 9 | Memory Bites | Howl −3 mood if pack unity < 5 |
| 10 | Blame Spiral | All Great Pack unity −1; cat trust −2 |
| 11 | Ash Naming | Howl +1 unity; creek drink +5 hydration; `blink_ash_naming` |
| 12 | Pact Remembered | Cat trust +5; warm-river debuffs end |

## Quest board keys

- `blink_border_patrol`; patrol
- `blink_river_crisis`; fishing ×2
- `blink_wind_witness`; sniff (phase 6+)
- `blink_mill_scout`; explore
- `blink_ash_naming`; howl ×3
- `blink_rogue_ledger`; crime ×2 (rogues)

## Splinter (rogue lane)

Exiled Greyspire; not the main antagonist. Mechanics:

- `/bones action:crime` without target during phase 6+: extra bones or border catch (−standing)
- `/field action:sniff`: limp rogue scent flavor
- `/explore investigate` during phase 8+: mill tooth (all wolves)
- Redemption/death remain RP + combat/standing

## Universal participation (all wolves)

While **plot_phase > 0**, every wolf can take part in Book One:

| Mechanic | Who | When |
|----------|-----|------|
| **Plot witness** | Everyone | First plot-tagged action each sunrise: **+1 mood** + flavor (`/field action:sniff`, `/howl`, `/drink`, scout survey, `/explore`, `/medic action:treat`) |
| **Sniff quests** | Everyone | `/field action:sniff` progresses **blink_healer_listen** (phases 1 to 5) and **blink_wind_witness** (phase 6+) |
| **Healer quests** | Medics & apprentices | `/medic action:treat` or `action:observe` during phases **5 to 11** → **blink_healer_touch** (+1 standing or +1 mood once/day for non-canon healers) |
| **Rollover pressure** | Everyone | Mood, hydration, disease, cat trust, unity; see phase table |
| **Activity modifiers** | Pack-tinted | Fishing debuff, travel DC, mill tooth, rogue crime, howl costs; see phase table |

Canon wolves (**Firepaw**, **Soot**, **Splinter**) keep **extra** rewards on top of the universal layer (see below).

## Firepaw (healer apprentice lane)

Thistlehide **Medic Apprentice** under Sypha. **Requires wolf name Firepaw + thistlehide affiliation.**

| Phase | Mechanic |
|-------|----------|
| **1 to 5** | `/field action:sniff`: **+2 mood**, **sniff bonus** (hunt/track +15%), quest **blink_healer_listen** progress *(+ universal witness)* |
| **6 to 10** | First `/field action:sniff` each sunrise: **+1 standing**, **+1 mood** (once/day plot reward) |
| **5 to 11** | `/medic action:treat`: **+2 HP** on heal outcomes; quest **blink_healer_touch** progress |
| **5 to 11** | First `/medic action:treat` each sunrise: **+1 standing** (packmate) or **+2 mood** (self) |
| **5 to 11** | **Firepaw** may **`/medic action:treat patient:`** (apprentice border-triage) |
| **5+** | `/medic action:observe`: **+2 mood**, **−2 medicine strain**, treat quest progress |

Quest skill rewards: **blink_healer_listen** → medicine +1 · **blink_healer_touch** → medicine +1

## Soot (Mistmoor healer lane)

Mistmoor **Medic** under Mirewort. **Requires wolf name Soot + mistmoor affiliation.**

| Phase | Mechanic |
|-------|----------|
| **5 to 11** | `/field action:sniff`: **+2 mood**, **sniff bonus** (+15% hunt/track), quest **blink_healer_listen** progress |
| **6 to 10** | First `/field action:sniff` each sunrise: **+1 standing** (second sight; once/day plot reward) |
| **5 to 11** | `/medic action:treat`: **+2 HP** on heal outcomes (**+1** more on **rot-lung** patients) |
| **5 to 11** | First `/medic action:treat` each sunrise: **+1 standing** (packmate) or **+2 mood** (self) |
| **5 to 11** | `/medic action:observe`: **+2 mood**, **−2 medicine strain**, treat quest progress |

Shares healer quests with Firepaw: **blink_healer_listen**, **blink_healer_touch**.

## Thistlehide leadership (canon)

**River'Shroud** holds the Alpha seat after **Finnpelt** yielded following the Rite of Broken Canine. **Finnpelt** now patrols as **hunter**. Pack alpha mechanics (`/pack`, broken canine rite, alpha role events) follow each wolf's `wolf_role` in the database.

### River'Shroud (alpha lane)

Thistlehide **Alpha**. Requires wolf name **RiverShroud** + `wolf_role:alpha` + thistlehide affiliation.

| Phase | Mechanic |
|-------|----------|
| **2 to 5** | `/field action:sniff`: **+1 mood**, **sniff bonus** (+15% hunt/track) |
| **6 to 10** | Every sniff: **+1 mood**, **sniff bonus**; first sniff each sunrise: **+2 standing** |
| **6 to 10** | `/pack patrol` / scout **survey**: **+1 standing** (on top of phase-2 Thistlehide patrol bonus) |
| **9** | `/howl`: **waives Memory Bites** mood penalty when pack unity < 5 |
| **9 to 11** | `/howl`: **+1 pack unity** (stacks with phase **11** Ash Naming unity) |

### Finnpelt (hunter lane)

Thistlehide **hunter** (former Alpha). Requires wolf name **Finnpelt** + `wolf_role:hunter` + thistlehide affiliation.

| Phase | Mechanic |
|-------|----------|
| **6 to 10** | `/field action:sniff`: **+2 mood**, **sniff bonus**; first sniff each sunrise: **+1 standing** |
| **6 to 10** | `/pack patrol` / scout **survey**: **+1 standing** |

## Living world (use alongside phases)

Cat pacts, `/field action:sniff` border fights, season stash failures, territory wars, diseases, restricted herbs, sacred visits, collab hunt/patrol, raccoon, predators, Whispering Wild; all continue during Book One.

## Canon anchors (affiliations)

- **Thistlehide:** River'Shroud (Alpha), Finnpelt, Mossgaze, Kanami, Pale'Step, Skye, Thyme, Firepaw, Eltanin
- **Silverrush:** Saltmuzzle, Rift, Rivenmaw, Ripple, Aromis
- **Mistmoor:** Murkvein, Mirewort, Gasp, Soot
- **Greyspire:** Grim, Talus; **Splinter** exiled rogue

## Ending Book One

Set `/setplotphase phase:0` when staff close the arc, or leave at phase 12 with resolution mechanics active.
