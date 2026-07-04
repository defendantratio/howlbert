# Cat Clans (Warrior Cats)

Staff reference for wolf; cat diplomacy in the **Warrior Cats lake territory** setting.

## The four Clans

| Clan | Territory | Forgeable |
|------|-----------|-----------|
| **ThunderClan** | Oak forest, Sunningrocks | Yes |
| **ShadowClan** | Pine marsh, shadowed pines | Yes |
| **WindClan** | Open moors, rabbit runs | Yes |
| **RiverClan** | River, gorge, reed beds | Yes |

**SkyClan** is not forgeable. Legacy DB pacts stored as `SkyClan` still resolve; new aliases map to ThunderClan.

## Player commands

| Command | Who | Effect |
|---------|-----|--------|
| `/pack pact action:view` | Pack member | List treaties |
| `action:forge` | Alpha, Diplomat | Negotiate truce / alliance / hunting rights |
| `action:renew` | Alpha, Diplomat | Extend active treaty |
| `action:break` | Alpha, Diplomat | Shatter treaty (−unity) |
| `action:gift` | Alpha, Diplomat | Treasury tribute → trust |
| `action:receive` | Any member | Clan goods at scent-line (trust ≥ 35, once/sunrise) |
| `action:trade` | Any member | Barter duplicate hoard → clan goods + trust |
| `/field action:sniff` | Anyone | May trigger border cat fight (reduced by active pacts) |
| `/wilderness action:travel territory:twolegplace` | Anyone | Thunderpath / Twoleg hazards |

## Trust & violations

- **High trust (70+)**: Fewer border fights; extra receive loot; rare **StarClan** omen on receive (+mood).
- **Low trust (<35)**: Allied patrols may attack; defeating them risks **pact violation**.
- **Violation**: Killing an allied **warrior** or **deputy** patrol → trust crash, unity −4, standing −3; treaty may break.

Rogues, loners, kittypets, and **rival-Clan** patrols do not count as violations.

## Seasonal Gathering

On **season change** at sunrise rollover, the four Clans meet at **Fourtrees** (flavor in rollover embed).

Dens with **active cat treaties** get:

- **+2 pack unity**
- **+1 standing** per member
- **+3 mood** per member

## Loot & medicine cats

Clan receive/barter pulls from Clan tables with a bias toward **medicine-cat herbs** (cobweb, yarrow, marigold-style names, etc.). Display uses Warrior Cats medicine naming where mapped in `engine/cat_clan_goods.py`.

## Border NPCs

Named patrol cats (original OC names, WC-style) appear on `/field action:sniff` border fights for `clan_warrior` and `clan_deputy` templates. See `CLAN_CAT_NAMES` in `engine/cat_clans.py`.

## StarClan omens

- `/wilderness action:omen`: nat 1 / 20 = disadvantage / advantage next sunrise; rare vision = +mood only.
- High-trust `action:receive`: ~18% chance of StarClan flavor + mood.

## Config (`config.py`)

| Constant | Default | Notes |
|----------|---------|-------|
| `CAT_PACT_MAX_ACTIVE` | 2 | Per den |
| `CAT_PACT_RECEIVE_MIN_TRUST` | 35 | Receive goods |
| `CAT_GATHERING_UNITY` | 2 | Per season, if pact active |
| `CAT_GATHERING_STANDING` | 1 | Per member |
| `CAT_GATHERING_MOOD` | 3 | Per member |
| `CAT_PACT_STARCLAN_RECEIVE_CHANCE` | 0.18 | High-trust receive |
| `SNIFF_CAT_ENCOUNTER_CHANCE` | 0.12 | Base border fight odds |

## Key files

- `engine/cat_clans.py`; Clan list, territory, patrol names, scent flavor
- `engine/cat_pacts.py`; Treaty logic
- `engine/cat_clan_goods.py`; Loot tables
- `engine/cat_gathering.py`; Season rollover Gathering
- `engine/starclan_omens.py`; Omen text
- `engine/border_combat.py`; `/field action:sniff` cat fights
- `engine/travel_hazards.py`; Twolegplace travel

## Tests

```bash
python tests/test_cat_pacts.py
python tests/test_cat_clan_goods.py
python tests/test_cat_wc_features.py
```
