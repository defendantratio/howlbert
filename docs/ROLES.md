# self-serve roles

the full role menu, built by reconciling the current roles against the channel plan in `docs/CHANNELS.md`. this is a build sheet for the Carl-bot reaction-role menus in **#role-selection**.

**legend:** *keep* = already exists, unchanged · *rename* = exists, relabel · *drop* = remove · **new** = create · *staff* = assigned by staff/bot, not self-serve.

each self-serve category becomes one Carl-bot reaction message. keep the whole menu tight; past ~6 ping toggles people stop setting them, so the ping section has a consolidation option at the end.

---

## 1. identity

| role set | status | notes |
|---|---|---|
| **Pronouns** (She/Her, She/They, They/Them, He/They, He/Him, Any, Ask) | keep | as-is |

## 2. availability & status

| role | status | maps to | what it's for |
|---|---|---|---|
| **DMs Open / Ask to DM / DMs Closed** | keep | server-wide | DM comfort |
| **Ping Friendly / Ping if Important / Do not Ping** | keep | server-wide | ping tolerance |
| **Hiatus / Away** | **new** | #hiatus-notice, #leaving-notice | marks a member as not around, so RP partners know not to wait on a reply. the "not here right now" state your availability set is missing |

## 3. pack

| role | status | maps to | what it's for |
|---|---|---|---|
| **Greyspire · Mistmoor · Thistlehide · Silverrush** | **new** | #in-game-roleplay-chat, plot, pack pings | shows a member's pack on their profile and lets staff/bot ping one pack for a pack-specific plot beat without pinging the server. highest-value addition |

pack roles should match the wolf's registered pack; if you play wolves in more than one pack, this is a "primary" flair, or staff-managed to avoid conflict-of-interest signalling.

## 4. RP status (optional)

| role | status | maps to | what it's for |
|---|---|---|---|
| **Open for Plots** | **new** | #relation-search | "come pitch me a storyline." lets people find writing partners at a glance |
| **Open for Ships** | **new, optional** | #relationship-rules, #relation-search | signals openness to romantic RP. keep it opt-in and clearly separate from Open for Plots, since not everyone wants romance pitched at them |

## 5. creator status (optional; art wing)

| role | status | maps to | what it's for |
|---|---|---|---|
| **Commissions Open** | **new** | #commissions | an artist self-marks available for paid work. the marketplace channel needs a way to show who's taking commissions |
| **Open for Art Trades** | **new, optional** | #art-trade | same idea, for free trades |

these are status flairs, not pings. add them only once the art wing channels are live and have volume; until then they're clutter.

## 6. ping preferences (opt-in pings)

the core reason to have roles at all: give every ping channel an opt-in audience so nothing has to `@everyone`. **`@everyone` stays reserved** for genuine all-server must-reads (safety/security PSAs, ownership news, a big plot launch) — see `docs/SOCIAL_MEDIA.md` on announcement tiers.

| role | status | maps to | fires when |
|---|---|---|---|
| **Looking for RP** | **new** | #rp-finder | someone wants to start a scene. the highest-frequency ping; must not be `@everyone` |
| **Plot & Events** | **rename** (was *Session Announcements*) | #plot-updates, #event-request | a plot beat advances or an event is called. renamed because "session" implies scheduled play; you run 24/7 async |
| **Competitions** | **new** | #competitions | a contest opens or a deadline nears |
| **Raffles** | **new** | #raffles | a giveaway starts. separate from Competitions: a giveaway is "click to win," not "make something and be judged" |
| **Game Nights** | **new** | announcements/#suggestions | a game night is scheduled (Minecraft, WCUE, WolfQuest). you already run these; they had no role and got `@everyone`'d |
| **Seasonal Events** | **new** | #artfight-2026 and future | Art Fight, holiday events, one-offs |
| **Devlog** | **new** | #neocities, bot-update posts | a howlbert update drops. your longest, most frequent posts, and self-described optional; perfect for opt-in |
| **Partner Ads** | **new** | #server-directory / partner channels | a new partner ad goes up. the `PARTNERSHIP_RULES.md` ping role |
| **QOTD** | keep | #qotd | question of the day |
| **Polls** | keep | server-wide polls | a poll opens |
| **Chat Revival** | keep | #general-chat | someone's reviving a quiet chat |
| **Adoption Alerts** | **new, optional** | #adopts | a pup is put up for adoption. add only if adoption volume justifies it |
| ~~**Announcements**~~ | **drop** | — | redundant: must-reads use `@everyone` anyway, so an opt-in version just double-pings the people who have it |

### consolidation option

that's ~12 ping toggles, which is a lot. if the menu feels heavy, merge without losing coverage:

- **"Events & Contests"** = Competitions + Raffles + Game Nights + Seasonal Events (one role for "something's happening"). you wanted Competitions and Raffles separate; keep them split only if you expect contests often enough that art-only members would want just that one.
- **"Server Games"** = QOTD + Polls + Chat Revival (one role for light engagement).

merging those two clusters takes the ping menu from ~12 down to ~7, which is the sweet spot. keep **Looking for RP, Plot & Events, Devlog, and Partner Ads** standalone regardless — they do distinct, higher-stakes jobs.

---

## 7. staff-assigned (not in the self-serve menu)

these exist as roles but are granted by staff or the bot, never picked from the menu:

| role | granted by | what it is |
|---|---|---|
| **Verified** | staff | the 18+ age gate (redacted ID or roblox screenshot). the most important role in the server; gates access. confirm this exists under whatever bot you verify with |
| **Partner Rep** | staff | one contact per partner server (`PARTNERSHIP_RULES.md`); mirrors the rep role they give you |
| **Staff / Mod** | staff | the team |
| **Pelt-Painter · Star-Speaker · Scene-Shaper** | staff | contest winners, per category, rotating (`COMPETITIONS.md`) |
| **the Maw-Marked** | staff | quarterly grand-contest winner |
| **the Offered** | staff | contest participants |
| **referral titles** (Den-Builder, Den-Keeper, Pack-Raiser, Pack Founder) | bot | auto-granted by howlbert on referral milestones; not discord-role-managed unless you mirror them |

**note:** prestige tiers (The Named ... The Sunderer) and maw favor live *inside howlbert*, not as discord roles. don't duplicate them as discord roles; they're already tracked and shown on `/profile`.

---

## summary of changes from the current menu

- **drop:** Announcements (ping)
- **rename:** Session Announcements → Plot & Events
- **add (high value):** the four Pack roles, Looking for RP, Hiatus/Away, Competitions, Raffles, Game Nights, Devlog, Partner Ads
- **add (optional / when volume justifies):** Seasonal Events, Open for Plots, Open for Ships, Commissions Open, Open for Art Trades, Adoption Alerts
- **keep:** Pronouns, the Availability sets, QOTD, Polls, Chat Revival
