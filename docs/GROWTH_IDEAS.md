# howlbert growth ideas (beyond the social media plan)

`docs/SOCIAL_MEDIA.md` already covers the core channels: twitter/x, bluesky, tumblr, instagram, tiktok, reddit, disboard/discadia/discord.me/discords.com, top.gg, proboards rp forums, deviantart, itch.io, a carrd/strawpage link hub, and a neocities lore site. the kickstarter itself is covered in `docs/KICKSTARTER.md`.

this doc is the next layer: channels and tactics that plan does not mention. same rules apply — lead with the world, not the ask; be a genuine participant before i promote; keep it cheap or free, this is a solo project.

**where i actually stand, applied throughout:** i'm shy about performing on mic, and drawing animals specifically isn't my strength yet — but i'd rather use this whole project as a reason to actually get better at both than route around them permanently. that means long-form, narrated video and animal art are back on the table, just slower and more forgiving than a polished-from-day-one bar: rough early narration and early drawings are allowed to be rough, and "watch me get better at this" is itself a legitimate content angle (see the new learn-in-public section below), not something to hide until it's good. text, community, and backend work are still the fastest wins and still make up most of this doc, but video/art aren't a no anymore, they're a slower yes.

---

## 1. finish the referral loop i already started

`invite_referrals` (database.py) and `engine/patron.py` already track invite attribution and grant the inviter and invitee a reward the first time it's used, capped monthly. the tracking and reward plumbing is done — what's missing is the *visible, social* half that turns it into a growth engine instead of a quiet backend bonus:

- **a leaderboard.** a command (or a line in `/pack` or the sunrise news) showing "who brought the most wolves home this season," refreshed monthly. this is the part that does double duty: retention content (a reason to check in) and acquisition content (a screenshot-able flex people post themselves). right now the reward is invisible to everyone but the person who got it.
- **raise the ceiling for top referrers.** the current system is capped per-month per the `invite_reward_month`/`invite_reward_count` columns; consider a separate, uncapped cosmetic-only milestone track (a title at 5 successful invites, another at 25, etc.) so a player who brings in a whole friend group has something to show for it beyond the same flat reward as inviting one person.
- **why this still matters:** disboard/top.gg listings (already in the social plan) catch cold, high-intent searchers, but they don't compound. a referral loop compounds — every new player is also a potential new recruiter — and i've already built the hard (backend) half of it; the cheap remaining work is making it visible.

---

## 2. run an in-character wolf account, separate from the howlbert brand account

the plan's social accounts all speak *as the developer* ("howlbert is a discord wolf rp bot..."). a second, smaller account that speaks *as a wolf* is a different hook entirely and taps the roleplay-hungry crowd harder than a dev account ever will.

- pick one canon book one wolf (the plan already has ~60 with real mechanical roles) and run a small tumblr or bluesky side-blog "as" them: in-character diary entries, in-voice reactions to weather or a rollover event, in-character warnings about river rot.
- this is a known-effective tactic in the warriors/wolf-rp and alternate-reality-game space — people follow characters, not software, and it gives my existing lore a second life outside the main feed.
- low effort: it can literally be 1 post a week, cross-posted from real events that happened to canon wolves in the bot's own plot system (book one already generates scene prompts on the sunrise news — that is free in-character content waiting to be repurposed).
- crucially, do not link the discord in every post; let a handful of posts be pure character work, so it reads as a persona, not a marketing puppet.

---

## 3. push affiliate swaps into joint events, not just banner trades

i'm already doing `#affiliates`-style swaps, so the next increment is turning a static banner trade into something that actually moves players between servers instead of just sitting in a channel nobody re-reads:

- **joint mini-events.** a one-off "border dispute" or "trade caravan" crossover rp beat between howlbert and a partner server's world, promoted on both sides at the same time. this cross-pollinates playerbases in a way a banner swap alone does not, because it gives partner-server members an actual reason to click through *today*, not just a passive link sitting in a channel.
- **rotate the banner placement.** if the swap has been sitting static, ask partners to re-pin or re-post it periodically (most affiliate channels decay fast as new swaps get added below the fold); a stale affiliate listing converts near zero regardless of how good the initial swap was.

---

## 4. amino is dead — toyhouse and aminoka are the closer modern fits

amino itself shut down; do not build a channel plan around it. two things fill parts of the gap it left, worth checking instead:

- **toyhouse** (toyhou.se) is very much alive and is where a lot of the oc-trading, worldbuilding, and character-roleplay crowd that used to split time with amino actually lives now — it has active wolf-character threads (character discussion boards run recurring "show me your wolves" style threads) and a "worlds" feature built for exactly this: hosting a shared setting's lore for people to attach their own characters to. creating a howlbert "world" page there, or just posting in the existing wolf-character threads with a link back, is a close-to-zero-cost way to reach oc-focused wolf-rp people directly instead of guessing at where amino refugees went.
- **art fight** (a large annual community art event, typically run mid-year) is huge in exactly this crowd. giving one or two book one canon wolves clean, attackable reference sheets and entering them (or just posting them as "free to attack" art-fight-adjacent content even outside the official event) can pull in fan art and traffic from artists who've never heard of the bot, purely because they wanted to draw a wolf. **the catch is real:** this only works with a genuinely clean, appealing reference sheet, and a rough one can actively hurt (art fight attackers pick targets partly on how fun/clear the ref is to draw), so it's a *later* milestone, not a day-one task — a good goal to aim my own animal-art practice (see the learn-in-public section below) toward, or a cheap commission in the meantime if i want to enter sooner. either way, it's a nice-to-have, not a load-bearing idea on this list.
- **aminoka** is a newer, actively-maintained clone built specifically for amino refugees; it's small and unproven as of now, so treat it as a "check back in 6 months" watch-item, not a channel to invest in today.

---

## 5. discord's own server discovery

everything in the plan is *third-party* discovery (disboard, top.gg). discord itself has a first-party **discovery** listing for servers that meet its criteria (member count, activity, community rules enabled, etc.). once the server clears the threshold, applying is free and puts me in front of people browsing inside the discord app itself with clear intent to find a community — a different, often higher-quality funnel than an external directory. check the current requirements when the server is a few hundred members and apply as soon as i qualify.

---

## 6. small streamers and vtubers, not big ones

i don't need a large streamer; i need a handful of small ones (hundreds to low thousands of viewers) who already play cozy/sim or ttrpg-adjacent games. most small streamers and vtubers accept unsolicited "hey, want to try this" dms far more readily than large ones, and their chat is a genuinely engaged, discovery-hungry audience.

**where to actually find them, concretely:**
- **discord discovery communities built for this exact purpose:** `SmallStreamerCommunity` (~20k members, sorts creators by audience size and has promo channels) and `StreamSquad` (explicitly framed around helping smaller streamers grow) are both active discord servers where i can post howlbert directly to an audience of streamers looking for things to play, rather than cold-dming strangers one at a time.
- **cozy/sim-adjacent streamers, not just "wolf" streamers.** the niche most likely to bite is cozy/survival-sim streamers (stardew valley, raft, subnautica, small farming/life-sim titles), since that audience already likes slow, stat-driven, "manage a life" gameplay loops — howlbert's hunger/injury/disease loop is a natural fit even though it's a discord bot, not a steam game. small-streamer-focused creators like **MadMorph** (indie/cozy/story-driven game specialist with a decade of content) are the kind of profile to target, not top-tier variety streamers.
- **vtubers specifically:** search vtuber discovery discords (`VTuber Academy`, ~8.4k members) rather than trying to identify individual wolf-themed vtubers one by one — there are a handful of wolf-persona vtubers out there (e.g. **Lumi**, a wolf-girl vtuber), but they're small, scattered, and not reliably reachable; a discovery community gets me in front of many candidates at once instead of pinning hopes on one.
- **skip the paid key-distribution platforms** (keymailer, woovit, lurkit) — they exist to distribute steam keys to reviewers and charge indie devs a monthly fee; they are not built for a free discord bot with nothing to "key," so they're the wrong tool here despite showing up in every "how do I reach streamers" search.

pitch: "permadeath wolf rp discord bot, free, 20 minutes to try." offer a light incentive: a "streamer's wolf" cosmetic title or founding-player credit for anyone who joins from the stream. this doubles as content: clip the vod for a tiktok/reel (type c, "community moment," already in the plan's video framework) — someone else generating my best raw footage for free.

---

## 7. youtube shorts, distinct from a full youtube channel

the plan explicitly rules out youtube ("overkill until the community is a few hundred"), and that is correct for long-form video, tutorials, and devlogs. shorts is a different surface: it does not require a channel identity or editing investment beyond what i'm already producing for tiktok/reels. re-upload the exact same 15-to-30-second clips (type a/b/c/d/e from section 7 of the social plan) to shorts. it is a second discovery algorithm for zero extra production cost, so there is no real reason to skip it once tiktok/reels content exists.

---

## 8. micro-influencer gifting instead of cash sponsorship

i cannot afford paid sponsorships, but i can afford to *gift*. this is one of the most direct-to-audience channels available and worth prioritizing.

**where to find candidates, concretely:** artists in this space report their commissions come overwhelmingly from twitter and discord, so that's where to look, not a generic "influencer marketplace." specific, low-cost-of-entry hubs:
- **discord commission servers.** dedicated servers like the "wolf pack" furry/lgbtq+ community server (centered on commissions, art, vtuber/vrchat avatars) and general furry-art commission servers on disboard/discadia (search the `commissions` and `furry-art` tags) surface active wolf/animal artists directly, often mid-conversation about their own work — a natural place to make a genuine offer rather than a cold dm.
- **toyhouse** (see section 4) doubles as an artist-discovery surface: the same wolf-character threads and worlds feature that reach oc-focused rp players also surface the artists drawing for that crowd.

**the offer:** a free founding-player cosmetic, a named npc/landmark in the world, or a featured commission repost (with full credit) in exchange for one honest post to their audience. this is cheaper than cash, on-brand (art-for-art), and reaches an audience — commission clients and wolf-art followers — that overlaps with my target players but isn't covered by any channel already in the plan.

---

## 9. a conservation tie-in, step by step (wolf haven international)

howlbert is fiction, but it is wolf fiction with real ecological texture (disease, injury, hunger, territory pressure). donating a small, fixed slice of ko-fi income to a real wolf conservation organization gives me a values-aligned hook that reaches an audience none of my other channels touch: wildlife and conservation accounts, who will share a "fiction that funds real wolves" story on principle even if they never touch discord. it costs only a fixed percentage, so it scales with revenue instead of being a fixed expense.

of the three orgs i originally scouted, **wolf haven international** (wolfhaven.org, tenino, washington) is the one worth actually pursuing, based on what's on their own site: they're already a **1% for the planet** environmental partner (a program built specifically for businesses/creators pledging a revenue slice, not just one-off donors), they name a specific development director for partnership and matching-gift conversations, and their symbolic adoption program (currently mid-rename/restructure on their own site, so check `wolfhaven.org/support/symbolic-adoption` for the live tiers before quoting numbers anywhere) is the exact donor-tier structure to mirror in-bot.

**step by step:**

1. **decide the pledge before reaching out, not after.** pick a fixed, small percentage of ko-fi income (1 to 5%) and a cadence (monthly or quarterly) i can actually sustain indefinitely — the pitch is much easier to make, and much easier for them to say yes to, when it's a concrete number instead of "some amount, unspecified."
2. **join 1% for the planet as the pledging business, with wolf haven as the designated recipient.** since wolf haven is already listed as one of their environmental partners, this is the cleanest, most "official" version of the tie-in: it's a real, third-party-verified pledge (not just a self-reported footer claim), and 1% for the planet's own network gives a second, small discovery channel on top of wolf haven's own audience. check `onepercentfortheplanet.org` for current member requirements and fees before committing.
3. **email wolf haven directly once the pledge is decided**, not before: their development team (contactable via `development@wolfhaven.org` or `info@wolfhaven.org`, 360-264-4695) handles partnership and matching-gift conversations. lead with the concrete pledge from step 1, mention the 1% for the planet membership from step 2 if it's in place, and ask what they'd want named/credited as (a specific wolf, a program, or a general conservation credit) — a specific ask gets a faster, clearer answer than "can we partner."
4. **wait for their confirmation on how they'd like to be named before building the in-bot mirror.** this avoids the mistake of shipping a "sponsors wolf haven's northern gray wolf" line and having it be wrong, or needing to be walked back publicly.
5. **build the in-bot mirror once confirmed:** a `/ko-fi` or `/about` note naming wolf haven specifically and a running total donated, and optionally a cosmetic "sponsor a real wolf" flourish (a title, or a profile line) tied to donor tiers, echoing whatever symbolic-adoption tier structure is live on their site at that point.
6. **post the announcement once, not as an ongoing pitch.** a single tumblr/bluesky post ("this fiction project funds real wolf conservation, here's the receipt") reaches the conservation/wildlife audience section 9 was written for; after that, let the running-total line in the bot do the ongoing work instead of repeating the ask.

**why not the other two:** wolf conservation center (nywolf.org) and endangered wolf center (endangeredwolfcenter.org) both still run their own symbolic adoption programs and are perfectly legitimate orgs, but neither has the same explicit, business-facing partnership infrastructure that wolf haven's 1% for the planet membership provides — worth revisiting only if wolf haven doesn't respond or the fit doesn't work out.

---

## 10. seo-targeted pages on the link hub / lore site

the plan's neocities lore site (section 15) is framed purely as a world bible. the same site is also free, evergreen search real estate if a couple of its pages are deliberately written to answer things people actually google: "wolf roleplay discord," "discord bot with permadeath," "realistic wolf rp bot." one faq-style page answering those phrases in plain language, linked from the homepage, costs almost nothing to add once the site exists and keeps working indefinitely, unlike a social post.

---

## 11. small ttrpg / indie-dev podcast guesting

solo-dev and indie-ttrpg podcasts are numerous, small, and frequently short on guests, which means they say yes to cold pitches more often than i'd expect. a 15-to-20-minute guest slot talking about the disease/injury/permadeath systems reaches a small but very on-target ttrpg-adjacent audience in one sitting, and the clip becomes reusable content (a pull-quote for tumblr, a short video for tiktok).

**specific shows worth a cold pitch:**
- **the solo roleplayers podcast** — interviews content creators in the solo-rp hobby; howlbert's persistent-wolf-i-can-lose framing fits their audience even though it isn't a solo game, since the emotional hook (a character that really matters, that i can really lose) is the same pitch.
- **ye indie'd!** — short, biweekly interviews specifically with indie tabletop rpg creators about their work and design; a near-perfect fit for a "here's the disease/injury system and why i built it this way" conversation.
- **the ansible uplink** — a guest reads/reviews an indie module each episode with the host; less of a direct fit (module-review format, not general dev interviews) but worth a pitch if the format can flex to a devlog-style episode.
- submission processes for all three are informal (direct email/dm, no application portal), which matches "cold pitches work here" — reach out with a short, specific pitch (one brutal mechanic, one sentence on why i built it) rather than a generic press-kit blast.

low volume, but close to zero cost beyond my time, so it is worth a handful of cold pitches once the bot has enough of a story to tell.

---

## 12. dedicated warriors/wolf-rp forums (named, not generic "proboards")

the social plan says "proboards-hosted wolf rp forums" generically. one concrete, still-active example worth targeting by name: **wcrpforums.com**, a warrior-cats-and-adjacent roleplay forum community that runs its own "advertise your rp" and "reviewing communities" style boards where members actively compare and recommend rp spaces to each other. this is a small, high-intent audience — people there are already forum-literate, already rp-committed, and already in the habit of trying new rp communities other members vouch for. post in the correct advertise-your-community board, follow their format exactly, and consider asking an active member for an honest "reviewing communities" style mention once the discord has enough going on to hold up under scrutiny.

---

## 13. get listed on fan-curated "rp discord masterlists"

separate from official directories (disboard, top.gg), the wolf-rp and warriors-rp community maintains its own informal, community-curated lists — pinned google docs, tumblr masterposts, or forum threads titled things like "warrior cats / wolf rp discord servers masterlist" — that circulate hand-to-hand and get reblogged/bumped periodically. these aren't run by any single authority, so there's no formal submission process; the move is to find the currently-circulating ones (search tumblr and the forums in sections 12/17 of the social plan for "masterlist") and ask the maintainer to add howlbert, the same low-key way i'd ask to join an affiliates channel. low effort, and these lists get bookmarked and revisited by exactly the audience i want, unlike a one-time social post.

---

## 14. record my own rp as an "actual play" — my ~24 members are the cast

the biggest owned-content lever i already have the raw material for. actual-play (recorded ttrpg/rp sessions) is one of the most reliable discovery engines in this hobby, and unlike a podcast *about* the game it needs no audience to start — the content **is** the community playing. i have ~24 people and a bot that generates plot beats: that's a cast and a script generator.

- **record it free with craig** ([craig.chat](https://craig.chat/)) — a multi-track discord voice recorder on 340k+ servers, built for exactly this crowd; `/join` to start, `/stop` to end, and it returns a separate clean track *per speaker* (edit one mic without touching the others). run a scheduled voice-channel rp "gathering" (tie it to the in-world moon-howl / fourtrees events the bot already has), record it, lightly cut it in [audacity](https://www.audacityteam.org/) (free).
- **one recording, two publishes:** a "howlbert actual play" video on youtube (evergreen search + feeds the shorts pipeline in section 7) *and* the audio pushed to a podcast host (section 15). one session = a video + a podcast episode + 3–4 clips.
- **why it fits 24 members:** it converts activity i already run into a marketing asset with no new cast to recruit, and it deepens retention (people schedule around a recurring recorded event — section 18) while producing the discovery content at the same time.
- **caveat, flagged honestly:** this idea assumes voices on tape, and it only works if enough *other* members are comfortable being recorded and don't mind their voice going on youtube (mine doesn't have to be one of them; i can run craig, sit out of voice, and let willing players carry the session). if nobody in the ~24 is up for that either, this idea doesn't have a workaround, it just doesn't fit right now. don't force it.

---

## 15. an in-world audio series ("field dispatches") — the podcast, done for small scale

i asked about a podcast. a *talk-about-the-game* podcast at 24 members has no audience yet — don't build that. build the version that works at any scale: a short (2–4 min) **in-character narrated audio series** — a wolf's field diary, a warning about river rot, a border report after a rollover — evergreen, searchable, and repurposed straight from the bot's sunrise-news scene prompts (free scripts, the same well section 2 draws from).

- **host it free on [spotify for podcasters](https://podcasters.spotify.com/)** (the former anchor): free hosting that distributes to spotify and exports an rss feed for apple podcasts etc. record in audacity, one voice, minimal edit.
- this is a *different surface* from the in-character text blog (section 2) and the podcast-*guesting* play (section 11): owned audio i control, it seeds podcast-search discovery, and each episode is also a video (waveform + ref art) for youtube/tiktok. keep it in-world so it reads as a persona, not an ad. one episode a fortnight is plenty.
- **the good low-stakes place to start practicing narration.** short, scripted, in-character, and forgiving — nobody expects a wolf's field diary to sound like a polished vo reel, so this is honestly a better first-rep than a dev-voice devlog would be. record it messy, keep the ones that land, and let the voice get more comfortable episode over episode; that improvement arc is itself part of the pitch (see the learn-in-public section below).

---

## 16. start an email newsletter now — the one audience an algorithm can't throttle

every channel in the plan is rented land (a platform decides my reach). a newsletter is the one **owned, portable** audience: i keep the list, no feed gates it, it compounds. start it at 24 subscribers — that's fine; it's an asset that only grows.

- **[buttondown](https://buttondown.com/)** — free up to 100 subscribers with no feature crippling, clean markdown, i fully own the list (the minimalist, writer-first choice). or **[substack](https://substack.com/)** if i'll trade simplicity for built-in discovery — its recommendation network can surface me to other newsletters' readers, a real if small growth vector. ko-fi also has built-in email broadcasts if i'd rather keep it all in one place.
- content is nearly free: a monthly "dispatch from the wild" = one balance/lore devlog note + one in-world snippet + a "wolf of the month" from my canon roster. link the join form from the strawpage hub and pin it in the server.
- **why it matters at my size:** these 24 are my highest-intent people; capturing even a fraction as subscribers means i can reach them for the kickstarter launch (`docs/KICKSTARTER.md`) *directly* instead of hoping a discord ping or a tweet lands. section 21b of the social plan already flags email as the highest-converting funnel — this is how i start building that list *today*.

---

## 17. a community-editable fan wiki (miraheze), not just the dev-owned lore site

section 10 turns the dev-owned neocities site into seo real estate. a *community-editable* wiki is a different animal and does two jobs a static site can't: it's a collaborative project that gives my 24 members something to build together (retention), and community wikis rank well for exactly the "wolf rp lore / [creature] rp" searches i want.

- **use [miraheze](https://miraheze.org/)** — free, nonprofit, **no ads**, gdpr-clean, community-owned — over [fandom](https://www.fandom.com/), which is ad-cluttered and widely advised against for new wikis in 2026. request a wiki, seed it with my book-one canon roster and world/disease/herb pages (content i already have), then let trusted members add their own wolves and write-ups.
- caveat: miraheze needs a little mediawiki know-how to set up nicely — treat it as a "when a few members want to co-build lore" project, not a day-one task. it's the closest thing to my own "own forum" idea that makes sense at this scale: a standalone web forum would just split a 24-person community, and discord's built-in **forum channels** (section 18) already cover in-server threaded rp/lore for free.

---

## 18. the honest part: at 24 members, retention and co-creation beat acquisition

blunt truth from the research on sub-50 servers: pouring acquisition into a leaky bucket wastes it — a small server with a high active-member ratio beats a bigger dead one, and my fastest growth is turning the 24 into people who **stay and recruit**. this is absent from the whole doc and it's the highest-leverage thing on this list.

- **onboarding:** enable discord's **welcome screen** + **onboarding** (server settings → onboarding) so a new joiner instantly knows what the server is in one sentence and has a clear first action (`/register`, pick a pack). first impressions decide whether a join becomes a member.
- **one reliable weekly ritual beats four random ones:** a fixed weekly in-world event (a fourtrees gathering, a moon-howl night) people schedule around — pair it with a recap post afterward (screenshots, a newsletter dispatch) so the ritual doubles as content without needing a recording.
- ~~question-of-the-day / low-pressure prompts~~ **already running** — i've had this going since the server started; keep it up, it's exactly the right move and doesn't need changing.
- **the 48-hour lurker dm:** when someone joins and doesn't post, a friendly manual dm two days later ("saw you joined — anything you're looking for?") recovers a surprising share of silent joiners. trivial at this scale.
- **the "your wolf misses you" re-engagement dm (built, dormant — section 44):** the other half of the lurker dm, for the opposite failure mode — an *existing* player who's gone quiet (no rollover activity in a while) gets a friendly, low-pressure check-in instead of just fading out unnoticed. `/patronadmin quietwolves` finds them; a manual dm still does the actual reaching out. currently turned off given how the earlier rollover-reminder dm was received; ask players first, then flip it on.
- **i visibly *playing*, not just moderating** — small servers live or die on the founder being a genuine participant.
- **co-creation = free evangelism:** let members name an npc, vote on a plot branch, or get a landmark named for their wolf (the bot already has npc/landmark hooks). people don't leave — or shut up about — a world they helped build. it's the cheapest word-of-mouth engine i have.
- **writing and art contests, run periodically (monthly or per-season).** a themed prompt tied to the current in-world season or plot beat ("write your wolf's worst sunrise" / "draw your wolf meeting the maw"), a couple weeks to submit, then a vote or a staff pick. this is co-creation (above) with a deadline and a spotlight attached, and it's a natural, recurring source of content for the wolf-of-the-week/community-highlights pipeline (40, `docs/SOCIAL_MEDIA.md` section 4) without me having to invent a new theme from scratch each time — the season or the current plot phase supplies it.
  - **prize ideas, cheapest first:** an in-bot cosmetic title (e.g. "den storyteller" / "den artist," same pattern as the referral milestone titles in section 1) · a permanent `/credits` and neocities-site listing as the season's winner · the winning piece becomes canon-adjacent — a named npc, a landmark, or a line folded into the world's lore with credit (real, lasting recognition for writers especially, who tend to care more about their words mattering in the world than about a prize object) · a bones prize funded from the pack treasury or my own pocket, since it costs the game nothing real · for art specifically, the winning piece becomes the featured `/herbs action:guide` header, a shop graphic, or a wallpaper-pack entry (section 8) with full credit — real exposure to everyone who uses that feature afterward · only once there's ko-fi income to spare, a small real prize (a bone pouch gift, section 39's cheap tier) for the top pick.
  - **keep it low-stakes and infrequent enough to matter:** at 24 members a monthly contest is plenty; more often than that and "the contest" stops feeling special and starts feeling like homework.

---

## 19. run one time-boxed "server event" as a launch moment

a small server needs *reasons to invite a friend today*, not just a standing open door. a one-off, **dated**, in-world event — "the great migration," a "founding season," a limited plot arc with a commemorative cosmetic for anyone who takes part — creates urgency, gives members a concrete "come do this with me this weekend" pitch, and is inherently postable (a countdown, a recap, screenshots) across every channel in the social plan.

- announce a date, offer a **participation-only cosmetic** (a founding-season title/badge — i already have the cosmetic/title system), and let current members bring one friend into the event specifically; hang a light referral hook off it (section 1).
- recap it as content afterward (a section-14 recording, a newsletter dispatch, a shorts clip). distinct from the *cross-server* joint events in section 3 — this one is my own house throwing the party.
- **free scheduling hook:** the in-game season already syncs to the real calendar automatically (`database.py`'s `real_world_season`), so a leaf-bare/winter push or a newgrowth/spring push lands on a real date four times a year without me having to invent one — piggyback event timing on that instead of picking an arbitrary weekend.

---

## 20. reserve my namespace while it's free

cheap housekeeping, not a channel — claim my name everywhere before a squatter does, so future searches resolve to me.
- **create the subreddit [r/howlbert](https://www.reddit.com/)** even if i don't use it yet: an owned space that ranks in search and is ready when i'm bigger (the social plan only covers posting to *existing* subreddits). free to reserve; sit on it.
- grab the matching handle on any in-plan platform i haven't claimed yet. minutes of work, avoids a future headache.
- (guilded, formerly a candidate for a discord-mirror hedge, shut down and no longer exists — skip it.)

---

## 21. a playable teaser built in twine, no discord join required

a free, text-only interactive-fiction tool ([twinery.org](https://twinery.org/)) lets me build a five-to-ten-minute "choose your path" teaser, hosted as a single static html file, playable directly in a browser tab. no voice, no drawing, no discord account needed to try it. this is a genuinely different funnel from everything else in either doc: instead of asking a stranger to commit to joining a server, i let them *play a taste of the world* first, then the last page is the hook ("this was one choice out of hundreds; the wolf you'd actually build waits at the discord link below").

- **no, this doesn't need graphics.** twine's default output is pure text, styled with plain css (background color, font, a border), and that's a genuinely normal, well-liked look for interactive fiction; a lot of the most-played twine games on itch.io are text-only. an image or two is a nice-to-have later, not a requirement to ship this, and i can lean on the site's existing dark/bone css variables (the same ones namegen.html and the rest of the neocities pages already use) to make it feel on-brand without drawing anything.
- write it once as a short branching scene: a young wolf's first hunt, or its first sunrise after a parent's death, ending on a choice that mirrors a real in-game mechanic — treat the wound directly, or find the medic.
- host it free on itch.io (already in the social plan for the devlog) or embed it directly on the neocities site as its own page.
- link it as the pinned first post on tumblr/bluesky instead of a static text hook; "play five minutes of the world" converts curiosity better than a paragraph does, and it costs me nothing i don't already have (writing, which is the one skill this whole project already proves i have).

---

## 22. get added to existing bluesky starter packs and curated feeds

the social plan mentions starter packs in passing as a bluesky best practice; this is the concrete action version. bluesky's discovery is not algorithmic virality, it's starter packs (curated "follow these N accounts" lists) and custom feeds, both built by community members, not by me.

- search bluesky for existing wolf-rp, warriors, and indie-ttrpg starter packs and feeds (they're usually named plainly, e.g. "warriors rp starter pack") and ask the curator directly to add the howlbert account; this is a normal, expected ask in that community, not an imposition.
- once i have any following, consider building my own small starter pack of *other* wolf-rp/indie accounts i genuinely like; curating one is itself a form of participation (ties into the "engage before you broadcast" rule already in the social plan) and puts my name in front of everyone who later finds that pack.
- zero art, zero voice, pure text/curation work.

---

## 23. cross-post short in-world fiction to ao3

archive of our own (ao3.org) hosts a huge amount of original, non-fandom fiction under "original work," and the wolf-rp/warriors-adjacent reader base already lives partly on ao3 as fic readers. a short (1,000 to 2,000 word) original piece, an in-character vignette using the same lore i'm already writing for tumblr (section 2) or the sunrise-news scene prompts, posted as an original work with howlbert credited and linked in the end notes, reaches people through ao3's own tag/search discovery instead of a social feed algorithm.

- tag generously and accurately (original work, wolves, found family, permadeath, dark, etc.) since ao3 discovery is entirely tag-driven.
- this is pure writing, the exact skill the whole project already leans on; no voice, no drawing, no video editing.
- low volume is fine here, one or two pieces is enough to plant a flag; it's a long-tail, evergreen channel, not a weekly commitment.

---

## 24. answer "looking for rp" posts directly, don't just wait for people to find me

warriors/wolf-rp forums, subreddits, and discord LFRP (looking-for-roleplay) channels regularly have individual roleplayers posting "looking for a wolf rp discord" or "any good wolf/warriors servers?" this is the single warmest possible lead, someone who has already stated the exact thing i'm selling, and it's completely free.

- check wcrpforums.com (section 12) and general rp-partner-search discords/subreddits (r/RoleplayingForReddit already appears in the social plan for a different purpose) periodically for these posts and reply genuinely and specifically, not with a copy-pasted pitch.
- this is a five-minutes-a-week habit, not a channel to build infrastructure around, but it converts at a rate nothing else on this list can match, because the person is already asking.

---

## 25. reddit self-promo megathreads, not standalone posts

section 3 of the social plan is right to warn me off a bare self-promo post in most subreddits, but a lot of the subreddits that ban standalone promo (r/discordapp, r/discordbots, and plenty of game/hobby subs) run a recurring, pinned **self-promo megathread** (weekly or monthly) specifically so people can drop a project without it reading as spam. this is a distinct, lower-risk move from posting my own thread: i check the sub's pinned posts or rules for a "self-promo saturday," "share your project," or similar recurring thread, and drop a short, honest pitch there. it costs a few minutes, doesn't risk a rule-breaking removal, and reaches the same subreddit audience the "read the rules first" caution in the social plan is worried about losing me access to.

---

## 26. real-wolf-biology content as its own top-of-funnel hook

every hook in the social plan is a *game* mechanic (river rot, death saves, injuries). a parallel, cheaper-to-write track: short posts translating real wolf biology into the game's mechanics — "wolf saliva actually has mild antibacterial properties, which is why howlbert lets a wolf lick its own wound for a small, real heal instead of treating it as reckless" is exactly this kind of post, and it's free content that's already sitting in this session's own design decisions. this pulls in a different crowd than "brutal mechanic" hooks do: wildlife/nature-interested followers who like learning a real fact first and discover the game as a bonus, not people already primed for permadeath rp. it's also a natural bridge to the conservation tie-in (9) — the same audience.

---

## 27. guest-write for someone else's blog or newsletter, not just my own devlog

distinct from podcast guesting (11), which is audio: a lot of small indie-game and ttrpg newsletters/blogs take guest posts, the text equivalent of a podcast guest slot. a short "how i designed the disease/injury system" or "what i learned building a discord-native rpg" piece, pitched to a newsletter or blog that already has an audience i don't, reaches readers who'll never see my own devlog because they don't know it exists yet. pure writing, no voice, no drawing, and it's a natural repurpose of the same design-decision material behind the devlog posts i'm already writing.

---

## 28. get howlbert listed on established warriors/wolf-rp fan wikis

distinct from the informal community-curated masterlists (13): large, established fan wikis (the warriors wiki on fandom and similar community-run wolf-rp wikis) often keep a "similar communities," "affiliated rp," or "external links" section, maintained under normal wiki editing rules rather than a maintainer's personal doc. this is a slower, more formal ask than a masterlist ping (i'd want to check each wiki's own rules on external links before editing, and some wikis are stricter than others about it), but it's a free, evergreen, search-indexed placement once it's there, and it reaches people who are already deep enough into the fandom to be browsing its wiki.

---

## 29. an invite-code vanity system, riding the referral tracking that already exists

the referral tracker (`invite_referrals` in database.py, section 1) already knows exactly who invited whom. a small extension: let a player mint a **named** invite link tied to their wolf (e.g. a discord invite with a custom vanity code, or a bot-generated short link that redirects to the real invite while logging the same referral row), so "join through Hemlock's link" is a thing a player can put in their own bio/carrd/toyhouse page instead of a bare discord.gg url. this is a small addition on top of code i've already built (the invite listener in `cogs/patron.py`), not a new system, and it turns every active player's *own* social presence into a trackable acquisition channel instead of just the official accounts.

---

## 30. a `/showcase` or `/brag` command that generates a shareable card

the richest, most specific content in the social plan (a `/vitals` screenshot, a death-save panel, an injury message) already exists inside the bot; right now getting it out requires a manual screenshot and a blur pass on the username. a command that renders a clean, pre-blurred, on-brand image (using the same dark/bone palette as the neocities site) summarizing a wolf's current state, a recent death, or a milestone (title unlocked, first kill, pack founded) — built with something like `Pillow` server-side — turns "screenshot a good moment" from a manual chore into a one-command, always-on-brand asset. this is real engineering work (a render pipeline, a font, the palette as constants), but it directly feeds sections 6 and 7 of the social plan (streamers/vtubers clipping something worth clipping) and the community-highlights content pillar, without needing me to personally screenshot and edit anything.

---

## 31. an rss/json feed of rollover events, for anyone who wants to build on top of it

the bot already generates structured, story-shaped events every sunrise (disease onsets, deaths, plot scene prompts). exposing a lightweight, read-only feed of these (a `/feed.json` or `/feed.xml` endpoint, or even just a webhook the discord bot already posts to that's also mirrored to a public url) costs little beyond code i've mostly already written for the sunrise news, and it opens a channel none of the manual social work can: **other people build things with it**. a fan could pipe it into a bluesky bot that auto-posts "a wolf died of river rot today" style flavor text, or a toyhouse/wiki-adjacent tracker could pull recent births/deaths for a roster page. this is speculative — it only pays off if someone actually builds on it — but the cost of exposing the feed is small compared to what a single motivated fan project could do for visibility.

---

## 32. an api-key-free "public stats" page fed straight from the database

a simple, honest counter page (wolves registered, packs founded, sunrises survived, diseases cured, deaths this season) on the neocities site or the strawpage hub, generated from a small export script run against the bot's own database (a cron job or a manual `python export_stats.py` before each social batch, per section 6 of the social plan). numbers like this are cheap, real social proof — "1,200 sunrises survived, 340 wolves lost to the wild" reads as a living world, not a pitch, and it's the kind of stat that's genuinely postable on its own (a monthly "state of the wild" tumblr/bluesky post, section 6's batching habit) without needing new art, voice, or a fresh idea every time; the data renews itself.

---

## 33. a lightweight discord activity/embedded-app teaser instead of a full game port

discord supports embedded "activities" (apps that run inside a voice channel or the app sidebar, the same surface party games use). a minimal, read-only activity — browse the herb compendium, look up a disease, or play the same twine teaser from section 21 inside an iframe — never leaves discord, which lowers the friction of the pitch even further than a browser link: someone can try a taste of howlbert without leaving the app they're already in, mid-server-browsing. this is a heavier lift than anything else on this list (discord's activity sdk, hosting, review process) and shouldn't be a priority, but it's worth knowing it exists as a ceiling to build toward once the simpler owned-content plays (16, 17, 21) are running.

---

## 34. pillowfort — a smaller, still-funded tumblr alternative

checked and confirmed still running: pillowfort is a nine-year-old, independent, user-funded blogging platform (anti-ai, pro-nsfw, no ad-driven algorithm) that's still actively developed, including recent 2026 feature updates to its image uploader. it's smaller than tumblr, but the crowd that migrated there specifically wanted an algorithm-free, art-and-fandom-friendly space, which overlaps with exactly the audience section 3 of the social plan is chasing. cross-post the same lore/mechanic posts already written for tumblr; it costs nothing beyond an account and a few minutes per post, and a smaller platform means an early post has a real chance of being seen by the people who run it, not buried.

---

## 35. dreamwidth rp communities — a different, older rp culture worth a look

checked and confirmed still active in 2026: dreamwidth (a livejournal-style blogging platform) hosts a genuinely distinct long-form roleplay culture, entirely separate from discord/tumblr rp, with its own conventions: dedicated "rp ads" communities for advertising a game or character, a maintained master list (`dwrpmasterlist`), and multi-year panfandom/original games with daily-active cores of a dozen-plus members. this is a smaller, older, more text-heavy crowd than tumblr's, but it's a crowd that already knows how to commit to a long-running rp and already browses exactly the kind of masterlist section 13 targets elsewhere — worth a look at the current `dwrpmasterlist` and `rpads` communities to see if howlbert (or an in-character presence, section 2) fits their format.

---

## 36. the furry fediverse (mastodon/pixelfed instances) — small, active, no algorithm

checked and confirmed active: a handful of furry-specific mastodon instances (meow.social, confirmed ~9,140 users and active in 2026 though currently invite-only; pawb.fun; owo.town) form a small, decentralized "furry fediverse" that overlaps with wolf/animal-rp audiences without a single company's algorithm deciding reach — posts reach followers chronologically, same as bluesky. this is a genuine niche, not a mass audience, so treat it as a low-effort cross-post from whatever's already written for bluesky (same short-form, chronological-feed logic), not a dedicated content pillar.

---

## 37. sofurry and vgen — two more artist/writer hubs for the same audience section 8 targets

checked and confirmed active: **sofurry** (running since 2002, 400,000+ registered users, active 2026 traffic) combines a gallery, a fiction library, and rp/chat tools under one roof, making it a single place to find both wolf-adjacent writers and artists at once, closer to the toyhouse/deviantart mix already in sections 4 and 8 than to a new standalone channel. **vgen** (a verified-artist commission marketplace, confirmed active with 2026 copyright and an ongoing verification program) is a more curated, higher-trust alternative to searching discord commission tags for the micro-influencer gifting play in section 8 — verified artists there have visible ratings and completed-order history, which makes it easier to vet a genuine offer before reaching out.

---

## 38. learn in public: narration and animal art as their own content, not just skills to unlock other ideas

practicing a skill visibly, in front of an audience, is a real and proven content genre on its own — "watch someone get better at something" reliably outperforms "here's a finished thing" for building a following that actually roots for the creator, because the audience gets invested in the arc, not just the output. this reframes the video/art gaps in this doc: instead of routing around narration and animal art until they're good enough to be invisible, the practice itself is postable, on both tumblr/bluesky (progress sketches, "attempt #12 at a wolf running gait") and long-form youtube (narration that's honestly a little rough early on, the same way a first devlog post admits the bot itself is a work in progress).

- **start a habit, not a project:** a short weekly or biweekly "wolf sketch" and a short narrated clip, posted as practice, not as a polished asset. the bar for postable is "I made this today," not "this is good enough to represent the brand."
- **the field dispatches audio series (15) is the natural home for narration practice** — short, scripted, low-stakes, and it's the same content the growth plan already wants either way, so the practice reps and the actual deliverable are the same thing.
- **tie it to a visible, dated goal** (a clean art fight reference sheet by a certain season, section 4) rather than an open-ended "get better eventually" — a deadline with a public arc leading up to it is itself a mini launch-moment (section 19's logic, applied to a skill instead of an event).
- **the honest framing works in this community's favor:** the wolf-rp/warriors crowd already responds well to "made with care, not polish" (the social plan's own content-warning and authenticity guidance leans this way already) — a visible learning curve reads as sincere effort, not a weakness to hide.

---

## 39. small, one-time paid upgrades worth their cost (everything else in this doc stays free)

the whole plan runs on free channels on purpose, but a handful of small, bounded, one-time or low-recurring costs buy real, disproportionate polish for a few dollars. none of these are required; they're upgrades to layer on once the free basics are running, not a new track to build.

- **a real domain (~$10 to 15/year).** a plain `.com`/`.net` that redirects to the strawpage/carrd link hub reads as more permanent and is easier to say out loud in a podcast pitch (section 11) or read off a sticker than a subdomain. cheapest, highest-value item on this list.
- **a one-time logo/wordmark commission (~$20 to 50 on fiverr or from an indie artist).** a single, consistent mark used everywhere (profile pictures, the neocities favicon, a video end card) reads as far more put-together than a stock wolf photo, and it sidesteps the animal-art gap entirely since it's a small, scoped, paid job rather than an ongoing art need.
- **print materials for irl handouts (~$20 to 30 for a small batch of stickers or cards via stickermule/moo).** a qr code to the discord on a sticker or card is cheap in small runs and gives something physical to hand out at a con, a tabletop meetup, or to kickstarter backers as a stretch-goal add-on (`docs/KICKSTARTER.md`).
- **a bounded, single test-ad spend (~$10 to 20), not an ad program.** one small, tightly-targeted promoted post (a reddit ad in a specific relevant subreddit, or boosting the single best-performing tumblr/bluesky post) is cheap enough to treat as a one-off experiment rather than the "paid ads" program section 18 correctly says to skip for now; the point is learning whether paid reach converts at all before ever spending more.
- **canva pro (~$13/month), once graphics become a weekly habit, not before.** the free tier is enough to start; the paid tier's brand kit (locked fonts/colors/logo across every graphic) only pays for itself once i'm making enough lore graphics and thumbnails on a regular cadence (section 6) that consistency starts to matter more than the monthly cost.
- **an occasional real prize for the top referral leaderboard spot (~$3 to 10, e.g. gifting a month of discord nitro basic).** the referral loop (section 1) is otherwise entirely in-bot cosmetics; a small, occasional real-world prize for whoever tops the leaderboard some months is a cheap, one-time nudge, not a recurring cost.

---

## 40. a "wolf of the week" auto-generated spotlight — built

**status: shipped.** `engine/spotlight.py` scores the last 7 sunrises of `wolf_journal` activity (achievements, pack foundings, raids, quests, deaths, bondings, and more) and picks the single most noteworthy entry; `/patronadmin spotlight` posts it as an embed. does double duty: retention content (section 18, a reason to check the den news) and a ready-made post for tumblr/bluesky (section 6's batching habit), generated from data that already existed instead of something i had to notice and write up by hand each week.

- **how to use it:** run `/patronadmin spotlight` in the den announcements channel once a week (any day works; it looks back 7 sunrises from whenever it's run). if nothing weighted happened that week it says so plainly instead of forcing a weak pick.
- **worth doing later, not now:** fully automating it to post itself on a schedule, once the manual habit proves it's actually worth the weekly attention.

---

## 41. an in-world obituary line on death — built

**status: shipped.** permadeath is honestly absolute again (section 9's rewrite); `engine/obituary.py` leans into that. every death now generates a short in-character line — cause of death plus one real highlight pulled from that wolf's own `wolf_journal` — instead of a bare "died of X." wired into both death paths: the automatic rollover-crisis deaths (starvation, exhaustion, old age) in the den news "losses" field, and the manual `/medic action:deathsaves` failure message. this is exactly the "type c, community moment" post format already in `docs/SOCIAL_MEDIA.md` section 7, except it writes itself instead of needing me to catch a good death and screenshot it in time. pairs naturally with the wolf-of-the-week spotlight (40) as the same underlying content pipeline — a striking obituary is often exactly what the spotlight picks up the following week.

---

## 42. frequent small achievements, not just the big prestige climb — built

**status: built.** prestige (`/prestige`) is a long multi-tier climb; good long-term hook, slow one. `engine/wolf_journal.py`'s original `log_achievement` had exactly one caller (a quest-completion path); founding a pack (`/foundpack`) now also logs a genuine achievement trophy for both founders. added `log_achievement_once` (keys namespaced as `achievement:<type>` so multiple distinct "first x" moments can each land once per wolf, instead of only a wolf's very first achievement of any kind ever counting) and wired two new triggers: a wolf's first successful surgery (`engine/surgery.py`) and a wolf's first disease cured (`cogs/care_handlers.py`'s `cured_disease` outcome). `engine/spotlight.py` was updated so these namespaced keys still score as a normal achievement for wolf-of-the-week picks.

- **worth wiring next, when there's time:** first kill/blooding already has its own journal event (`log_blooded`), so it's covered; surviving a chronic-illness scare (a disease death-save success, not just a cure) is the next-best candidate — same `log_achievement_once` pattern, added at its existing success point.
- these feed the wolf-of-the-week (40) and community-highlights pillar (`docs/SOCIAL_MEDIA.md` section 4) with more raw material than the big prestige tiers alone generate.

---

## 43. "caption this" as a recurring engagement format

post a `/vitals` panel or a combat log with no caption; ask people to guess what happened. `docs/SOCIAL_MEDIA.md`'s own research (section 21a) already found interactive posts significantly outperform static announcements — this is a zero-writing-effort way to hit that regularly, using screenshots the bot already generates rather than needing a new idea each time. pairs well with the wolf-of-the-week and obituary content (40, 41) as the same recurring habit. pure posting habit, no code needed.

---

## 44. finding players who've gone quiet — built, but turned off on purpose

**status: shipped, dormant.** `engine/reengagement.py` reuses the same "last active" pattern `engine/exhaustion_effects.py` already used for the away-wolf exemption, and `/patronadmin quietwolves` (optionally `days:`, default 5) lists registered, living wolves with no tracked activity in that window — the other half of the 48-hour lurker dm in section 18, for players who already joined and played, then faded out, instead of players who never posted at all.

- **why it's off right now:** an earlier rollover-reminder dm feature landed badly with the community, so this is gated behind `QUIETWOLVES_COMMAND_ENABLED` in `config.py` (currently `False`) until there's been a chance to actually ask players how they'd feel about an activity check-in, rather than assuming. flip the flag when ready; nothing else needs to change.
- **how to use it once it's on:** run it occasionally, then send a few genuine, low-pressure manual dms to whoever's on the list ("saw your wolf's been quiet, everything okay?"). it's a list, not an auto-messenger, on purpose — a real check-in reads very differently from a bot-blasted one, and that distinction is probably worth explaining up front if it comes up when asking players.

---

## 45. a real server structure: booster perks + an art/creative wing

most of this doc treats the server as a container for the bot. it's worth treating server *structure itself* as a retention lever — a server that only has rp channels gives people one reason to stay; a server with a real creative community around it gives them several, and most of these cost nothing but channel setup.

**booster perks, documented properly:** the bones/mood/standing rewards for boosting already exist and already auto-fire the moment someone boosts (`cogs/patron.py`'s `on_member_update` listener, `engine/patron.py`'s `grant_first_boost`/`grant_second_boost`) — the gap isn't code, it's visibility. a **#patron** channel spelling out exactly what boosting and other support gets someone (and who's currently boosting/backing) turns an invisible auto-grant into something people actually know to want. this channel can mostly write itself from data the bot already has: `/patron` for personal status, the referral leaderboard (section 1) and kickstarter backer badge for public recognition.

**checked against the real server structure:** the real server already has an **art sharing** channel under OOC SPACE. that channel doesn't get replaced by this wing — it's the general dump, and the wing below is the specialization of it (commissions vs. free trades vs. adopts vs. weekly spotlight are different enough activities that splitting them out is worth it once art sharing has enough volume to justify it). start the wing small — #commissions and #art-of-the-week are the two with the clearest immediate payoff (real marketplace, reuses the spotlight code already built) — and only peel off the rest of the list as art-sharing traffic actually demands it, rather than launching 8 near-empty channels at once.

a dedicated **howlbert category** (separate from OOC SPACE) is worth it specifically because bot commands currently sit inside a general ooc catch-all alongside voice chat and birthdays — pulling bot-adjacent channels (bot commands, and #open-scenes and #screenshot-showcase once those exist) into their own category makes the bot's presence feel intentional instead of tacked-on, and it's a pure discord-admin reorg, no bot code involved. not worth it yet if it's just one channel; worth it once #open-scenes and #screenshot-showcase exist alongside bot commands, since three related channels in a generic ooc category is exactly the kind of clutter categories are for.

**an art/creative wing**, mostly under one **art** category:
- **#commissions** (forum) — writing and art commissions, a real marketplace channel; this is also where the micro-influencer gifting play (section 8) and the sofurry/vgen artist-discovery channels (section 37) point *inward* to once someone's interested, instead of the conversation dead-ending in dms.
- **#headcanons** — quick lore ideas and interpretations; low-effort, high-frequency posting, the kind of channel that stays alive on its own once it has momentum.
- **#free-to-use-images** — a shared stock/asset folder (borders, dividers, textures); small thing, real quality-of-life for anyone building a character sheet or a bio.
- **#art-of-the-week** — same underlying idea as the wolf-of-the-week spotlight (section 40, already built), applied to the art side instead of the journal side; could even be judged the same way the contest picks (section 18) are.
- **#art-trade** and **#requests** — free-exchange boards, distinct from paid commissions; lower barrier to entry, keeps less-established artists engaged too.
- **#adopts** (forum) — character-adoption marketplace; a genuinely standard, well-understood channel type in oc/rp-adjacent communities (the same crowd toyhouse and art fight, sections 4 and 8, already reach).
- **#resources** (forum) — tutorials, palettes, brush packs, reference sheets; a forum type here so tutorials stay individually findable instead of scrolling, same reasoning as #commissions and #adopts above.
- **partnership rules** (a pinned doc or channel topic, not necessarily its own channel) — the actual terms for the affiliate swaps already happening (section 3): what a partner gets, what's expected in return, so it's a repeatable process instead of a one-off conversation each time.
- **#server-directory** — the affiliate/partner server links live here (sections 3, 13), in one place instead of scattered.
- **#server-art** — credited server- and howlbert-specific art (emojis, icons, banners), with a pinned "how to submit" post; this is also where a future logo/wordmark commission (section 39) or a `/showcase`-style asset (section 30) would get shown off.
- **#neocities** — just the link, kept simple; the neocities site (`docs/SOCIAL_MEDIA.md` section 15) deserves a persistent, easy-to-find pointer in-server, not just an occasional social post.
- **#howlbert** — the real server already has a **bot commands** channel under OOC SPACE, which mostly covers this; a rename/repurpose rather than a new channel, unless the goal is separating command-spam from bot-related discussion, in which case keeping both makes sense.

**a few more channels worth adding to the list, on top of what's already planned:**
- **#new-member-intro** — the real server already has an **introductions** channel under BEGIN YOUR JOURNEY, so this is covered; no new channel needed.
- **#screenshot-showcase** — a dedicated dump for dramatic `/vitals` panels, death saves, and combat logs. this is the exact raw material the wolf-of-the-week spotlight and caption-this format (sections 40, 43) already need; right now those moments have nowhere to land and just scroll past in rp channels. genuinely new — nothing in the real channel list covers this.
- **#fic-recs** (distinct from headcanons) — headcanons are quick lore ideas; this is for actual longer written scenes and stories in the world, and it's the natural in-server counterpart to the ao3 crosspost idea (section 23). genuinely new.
- **#open-scenes — built.** the bot now keeps a live, auto-edited index of currently-open `/scene` threads (`engine/open_scenes_index.py`, wired into `/scene start`/`join`/`leave`/`end`); point `OPEN_SCENES_CHANNEL_ID` at a channel and it maintains itself. the real server already has **rp finder** and **session discussion** under ROLEPLAY HUB — worth checking what those are actually used for before adding a third channel; if rp finder is just "post looking for rp" text, the auto-index is a straight upgrade and can replace it, if it's doing something else the two can coexist.
- **#suggestions** — the real server already has a **suggestions** channel under OOC SPACE, so this is covered; no new channel needed.

---

## 52. enter a game jam / themed community jam

jams are time-boxed events with a built-in, discovery-hungry audience already hunting for something new to try. even a discord bot can ride the traffic with a devlog entry, but the honest catch is that most jams expect a downloadable or browser-playable game — so the thing i'd actually *enter* is the **twine teaser (section 21)**, not the bot itself. a jam gives that teaser a reason to exist on a deadline and an audience the day it ships. i browse **[itch.io/jams](https://itch.io/jams)**, pick one whose theme fits (cozy, wholesome, animals, interactive fiction), submit the teaser on my existing itch page, and post the jam link everywhere. free, dated (urgency built in), and it points curious players at a five-minute taste of the world rather than a cold discord invite.

---

## 53. a small ambassador / "pack leader" program

formalize the co-creation in section 18: pick 2–3 of my most active members, give them a cosmetic title + a private channel + first look at features, and ask them (no pressure) to help welcome newcomers and post about events. a tiny, motivated ambassador cohort is the classic small-community growth multiplier — they carry the culture and recruit from their own circles. costs nothing but a role and some trust, and it's the natural next step *once a few standouts emerge* from the retention work (18), not something to force early — at 24 members, appointing "ambassadors" before there's an obvious 2–3 would read as hierarchy for its own sake.

---

## 54. a "which pack are you" quiz, extending the name generator i already built

the lead-magnet mini-tool idea is half-done already: `docs/site/namegen.html` is exactly the pattern — a tiny interactive page that ranks for high-volume searches ("wolf name generator," "wolf rp name") and funnels cold searchers toward the bot. the cheap next increment on the same hub is a **"which great pack are you" sorting quiz**: quiz results are inherently shareable ("i got mistmoor!" screenshots spread themselves), and the result page can CTA straight into "make this wolf real → `/register` in the discord." it reuses the same dark/bone css the name generator and neocities pages already share, so it's writing + light html, no art or voice, and it pulls search-and-share traffic none of my lore pages do.

---

## 55. bot-to-bot cross-promotion, not just server-to-server

the affiliate swaps in section 3 are server-to-server; there's a parallel lane in mutual promotion between complementary discord *bots/projects*. i find another small rp- or cozy-game bot dev (through the top.gg / discadia listings, or indie-bot-dev discords) and we agree to mention each other in our `/help` credits, pinned channels, or newsletters. it reaches an audience that has already proven it installs bots — warmer and more qualified than a cold server crowd — and it's a genuinely mutual, low-ask trade between peers rather than a promotion i'm begging for.

---

## 56. a printable "field guide" zine as a newsletter incentive

a short, pretty PDF — a wolf-world field guide covering the diseases, herbs, and packs — does triple duty: (a) a **lead magnet**, "subscribe to get the field guide," which measurably lifts newsletter signups (section 16); (b) shareable lore content; (c) a proto-artifact if i ever do print/merch (section 39). the text is nearly free — the herb compendium, disease list, and pack traits are all already in-bot content i can lift straight out — and i gate the download behind the newsletter join form. the animal-art caveat is real: it wants at least a little art to look good, so it pairs with the learn-in-public art practice (38) or a small logo/spot commission (39), and it's a "once i have a few pieces i like" task, not a day-one one.

---

## 57. a "make-a-wolf" picrew as a shareable lead magnet

a picrew (picrew.me, a japanese "image maker" platform) is a character-avatar creator that other people use to build their own oc and share it. a **make-a-wolf picrew** — build your own howlbert-style wolf — is an inherently viral lead magnet: players make their own wolf, post it to their own socials, and the image carries a link back, so the discovery is driven by *them*, not me.

- **i can build it myself or commission one.** either way the parts must be *my own art* (or commissioned *with rights*) — same rule as my local artist best-practices notes. building it myself doubles as animal-art practice (section 38), and pairs perfectly with the name generator/quiz (54): "generate a name → design the wolf → make it real in the discord."


---

## 58. canon-character speedpaints as short-form art content (tiktok / instagram / youtube shorts)

the canon roster (~60 wolves with real lore) is a ready-made subject list for speedpaint/timelapse videos, cross-posted to **tiktok, instagram reels, and youtube shorts** — three discovery algorithms off one recording. this is the video/art route made concrete, and it slots straight into learn-in-public (38): early ones are allowed to be rough, "watch me get better at drawing these wolves" *is* the arc, and each finished piece is also a static post (tumblr/bluesky), a candidate art-fight ref (4), and a zine page (56).

- **the honest short-form fit:** the priority read is right that short-form usually punishes a slow, cozy world for lacking a two-second hook — but a *speedpaint* has a built-in one: the satisfying blank-to-finished timelapse is the hook. so speedpaints are the one short-form format actually worth prioritizing for me, even while reels/shorts stay deprioritized for gameplay clips.
- **compliance matters here because these promote a paid product.** before posting any speedpaint i run the local `docs/ARTIST_BEST_PRACTICES.md` checklist — especially: **commercial-cleared music only** (tiktok's commercial music library / instagram's business-licensed audio / the youtube audio library — crediting a copyrighted song is *not* permission, **credit** any base/brushes, and **show the full process** so it never reads as traced.)

---

## priority read

**start with the 24-member reality (18).** at my size, acquisition into a low-retention server leaks out as fast as it comes in — onboarding, one reliable weekly ritual, the 48-hour lurker dm, and co-creation are the cheapest, highest-leverage moves here (the qotd habit is already running and already correct, keep it), and every acquisition play converts better once they're in place. then **start the email list (16)** — the one audience no algorithm can throttle, and what i'll actually launch the kickstarter to.

**next, finish the referral loop (1)** — it's mostly built already, a leaderboard is the cheap remaining piece — and **apply for discord discovery (5)** once i clear the threshold; both are free, compounding, and aimed at people already inside or already searching.

**for warm-audience reach that's pure writing/community work:** the in-character wolf account as a text blog (2), the twine teaser (21), bluesky starter packs (22), the ao3 crossposts (23), answering "looking for rp" posts directly (24), reddit megathreads (25), real-wolf-biology content (26), and guest-writing (27) need no camera, no narration, no drawing, and they're still the fastest wins on this list regardless of how the video/art practice goes. toyhouse (4), micro-influencer gifting (8), the conservation tie-in (9), the fan wiki (17), fan-wiki listings (28), and namespace housekeeping (20) round out this tier.

**long-form, narrated video is a real second track now, not a low-priority experiment — reels/shorts are the part still deprioritized.** short-form lives and dies on a hook in the first two seconds; that's a bad match for a slow, cozy world and a mismatch for practicing narration under pressure. long-form doesn't have that problem: it's forgiving of a rough take, fits the "cozy over attention-grabbing" pacing this world actually has, and is a reasonable place to get narration reps in publicly (see the learn-in-public section below). the audio series (15) is the lowest-stakes place to start those reps. actual-play (14) is still the odd one out — it needs live, unscripted participation from whoever's in the session, which is a different kind of ask than scripted narration, so it still only happens if other willing members carry it.

**the code-driven ideas (29-33) are opportunistic, not urgent.** the invite-code vanity system (29) is the cheapest since it extends code i've already built for the referral loop; the public stats page (32) is nearly as cheap and doubles as recurring social content. the showcase-card command (30), the events feed (31), and the discord activity (33) are real engineering projects, worth doing when there's spare dev time, not something to block the retention/acquisition basics above on.

**the niche platforms (34-37) are cheap cross-posts, not new pillars.** pillowfort (34) and the furry fediverse (36) cost nothing beyond reposting what's already written for tumblr/bluesky; dreamwidth (35) is worth a one-time look at its rp-ad culture to see if it's a fit; sofurry and vgen (37) are just more places to find the same artists section 8 is already after. none of these need new content, just the discipline to also post the existing hooks somewhere small.

**start the learn-in-public habit (38) now, alongside everything else, not after skills are "ready."** it's low-cost, it turns the narration/art gap into content instead of a blocker, and it directly feeds the field dispatches series (15) and a future art fight entry (4) rather than competing with them for time.

**the paid upgrades (39) are purely opportunistic — nice when there's a few dollars spare, never a blocker.** the domain and the logo commission are the two with the best cost-to-polish ratio if only doing one or two; the rest (print materials, a test ad, canva pro, an occasional referral prize) are fine to skip entirely without weakening anything else in this doc.

**the wolf-of-the-week spotlight (40) and the obituary line (41) are built; start actually using them.** `/patronadmin spotlight` weekly is now just a habit to build, not a feature to build — the code side is done. caption-this (43) is the same content pipeline with zero code, pure posting habit. frequent achievements (42) has one real trigger wired (founding a pack); the next few (surgery, disease survival) are small, one-line additions whenever there's a spare few minutes. finding quiet players (44) is built but deliberately left off — ask players how they'd feel about it before flipping `QUIETWOLVES_COMMAND_ENABLED` on.

**the server structure (45) is cheap, one-time setup work — worth doing in one focused pass rather than piecemeal.** the #patron channel and #screenshot-showcase are the two with the most direct payoff (documenting a reward that already silently exists; feeding content into 40/43 that currently has nowhere to go). the rest of the art wing can be seeded thin (one pinned post each) and left to grow on its own; an empty channel is fine, an empty *category* full of dead channels reads worse than not having them.

**the latest additions (52–58) mostly slot into tiers already above.** the **"which pack are you" quiz (54)** is the cheapest and most on-brand — it's a small extension of the name generator i already built, pure writing/html, and it feeds the same search-and-share funnel as the twine teaser (21). **speedpaints (58)** are the one short-form format worth prioritizing despite the reels/shorts caution, because the timelapse *is* the hook — but only under the `ARTIST_BEST_PRACTICES.md` rules (commercial-cleared music, credit, show process), since they promote a paid product. the **make-a-wolf picrew (57)** and the **field-guide zine (56)** are strong fan-spread/lead-magnet plays but both wait on a little art (38/39) and both carry commercial caveats worth minding — the field-guide zine's text is nearly free now, though, since the herb compendium and treatment flows already live in full in `docs/CHANNELS.md`. the **ambassador program (53)** and **bot-to-bot cross-promo (55)** are natural once retention (18) and a few peer-dev relationships exist. the **game jam (52)** is opportunistic — worth it *only* to give the twine teaser a launch moment, not on its own.

