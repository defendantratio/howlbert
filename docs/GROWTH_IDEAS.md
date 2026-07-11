# howlbert growth ideas (beyond the social media plan)

`docs/SOCIAL_MEDIA.md` already covers the core channels: twitter/x, bluesky, tumblr, instagram, tiktok, reddit, disboard/discadia/discord.me/discords.com, top.gg, proboards rp forums, deviantart, itch.io, a carrd/strawpage link hub, and a neocities lore site. the kickstarter itself is covered in `docs/KICKSTARTER.md`.

this doc is the next layer: channels and tactics that plan does not mention. same rules apply — lead with the world, not the ask; be a genuine participant before you promote; keep it cheap or free, this is a solo project.

---

## 1. finish the referral loop you already started

`invite_referrals` (database.py) and `engine/patron.py` already track invite attribution and grant the inviter and invitee a reward the first time it's used, capped monthly. the tracking and reward plumbing is done — what's missing is the *visible, social* half that turns it into a growth engine instead of a quiet backend bonus:

- **a leaderboard.** a command (or a line in `/pack` or the sunrise news) showing "who brought the most wolves home this season," refreshed monthly. this is the part that does double duty: retention content (a reason to check in) and acquisition content (a screenshot-able flex people post themselves). right now the reward is invisible to everyone but the person who got it.
- **raise the ceiling for top referrers.** the current system is capped per-month per the `invite_reward_month`/`invite_reward_count` columns; consider a separate, uncapped cosmetic-only milestone track (a title at 5 successful invites, another at 25, etc.) so a player who brings in a whole friend group has something to show for it beyond the same flat reward as inviting one person.
- **why this still matters:** disboard/top.gg listings (already in the social plan) catch cold, high-intent searchers, but they don't compound. a referral loop compounds — every new player is also a potential new recruiter — and you've already built the hard (backend) half of it; the cheap remaining work is making it visible.

---

## 2. run an in-character wolf account, separate from the howlbert brand account

the plan's social accounts all speak *as the developer* ("howlbert is a discord wolf rp bot..."). a second, smaller account that speaks *as a wolf* is a different hook entirely and taps the roleplay-hungry crowd harder than a dev account ever will.

- pick one canon book one wolf (the plan already has ~60 with real mechanical roles) and run a small tumblr or bluesky side-blog "as" them: in-character diary entries, in-voice reactions to weather or a rollover event, in-character warnings about river rot.
- this is a known-effective tactic in the warriors/wolf-rp and alternate-reality-game space — people follow characters, not software, and it gives your existing lore a second life outside the main feed.
- low effort: it can literally be 1 post a week, cross-posted from real events that happened to canon wolves in the bot's own plot system (book one already generates scene prompts on the sunrise news — that is free in-character content waiting to be repurposed).
- crucially, do not link the discord in every post; let a handful of posts be pure character work, so it reads as a persona, not a marketing puppet.

---

## 3. push affiliate swaps into joint events, not just banner trades

you're already doing `#affiliates`-style swaps, so the next increment is turning a static banner trade into something that actually moves players between servers instead of just sitting in a channel nobody re-reads:

- **joint mini-events.** a one-off "border dispute" or "trade caravan" crossover rp beat between howlbert and a partner server's world, promoted on both sides at the same time. this cross-pollinates playerbases in a way a banner swap alone does not, because it gives partner-server members an actual reason to click through *today*, not just a passive link sitting in a channel.
- **rotate the banner placement.** if the swap has been sitting static, ask partners to re-pin or re-post it periodically (most affiliate channels decay fast as new swaps get added below the fold); a stale affiliate listing converts near zero regardless of how good the initial swap was.

---

## 4. amino is dead — toyhouse and aminoka are the closer modern fits

amino itself shut down; do not build a channel plan around it. two things fill parts of the gap it left, worth checking instead:

- **toyhouse** (toyhou.se) is very much alive and is where a lot of the oc-trading, worldbuilding, and character-roleplay crowd that used to split time with amino actually lives now — it has active wolf-character threads (character discussion boards run recurring "show me your wolves" style threads) and a "worlds" feature built for exactly this: hosting a shared setting's lore for people to attach their own characters to. creating a howlbert "world" page there, or just posting in the existing wolf-character threads with a link back, is a close-to-zero-cost way to reach oc-focused wolf-rp people directly instead of guessing at where amino refugees went.
- **art fight** (a large annual community art event, typically run mid-year) is huge in exactly this crowd. giving one or two book one canon wolves clean, attackable reference sheets and entering them (or just posting them as "free to attack" art-fight-adjacent content even outside the official event) can pull in fan art and traffic from artists who've never heard of the bot, purely because they wanted to draw a wolf.
- **aminoka** is a newer, actively-maintained clone built specifically for amino refugees; it's small and unproven as of now, so treat it as a "check back in 6 months" watch-item, not a channel to invest in today.

---

## 5. discord's own server discovery

everything in the plan is *third-party* discovery (disboard, top.gg). discord itself has a first-party **discovery** listing for servers that meet its criteria (member count, activity, community rules enabled, etc.). once the server clears the threshold, applying is free and puts you in front of people browsing inside the discord app itself with clear intent to find a community — a different, often higher-quality funnel than an external directory. check the current requirements when the server is a few hundred members and apply as soon as you qualify.

---

## 6. small streamers and vtubers, not big ones

you do not need a large streamer; you need a handful of small ones (hundreds to low thousands of viewers) who already play cozy/sim or ttrpg-adjacent games. most small streamers and vtubers accept unsolicited "hey, want to try this" dms far more readily than large ones, and their chat is a genuinely engaged, discovery-hungry audience.

**where to actually find them, concretely:**
- **discord discovery communities built for this exact purpose:** `SmallStreamerCommunity` (~20k members, sorts creators by audience size and has promo channels) and `StreamSquad` (explicitly framed around helping smaller streamers grow) are both active discord servers where you can post howlbert directly to an audience of streamers looking for things to play, rather than cold-dming strangers one at a time.
- **cozy/sim-adjacent streamers, not just "wolf" streamers.** the niche most likely to bite is cozy/survival-sim streamers (stardew valley, raft, subnautica, small farming/life-sim titles), since that audience already likes slow, stat-driven, "manage a life" gameplay loops — howlbert's hunger/injury/disease loop is a natural fit even though it's a discord bot, not a steam game. small-streamer-focused creators like **MadMorph** (indie/cozy/story-driven game specialist with a decade of content) are the kind of profile to target, not top-tier variety streamers.
- **vtubers specifically:** search vtuber discovery discords (`VTuber Academy`, ~8.4k members) rather than trying to identify individual wolf-themed vtubers one by one — there are a handful of wolf-persona vtubers out there (e.g. **Lumi**, a wolf-girl vtuber), but they're small, scattered, and not reliably reachable; a discovery community gets you in front of many candidates at once instead of pinning hopes on one.
- **skip the paid key-distribution platforms** (keymailer, woovit, lurkit) — they exist to distribute steam keys to reviewers and charge indie devs a monthly fee; they are not built for a free discord bot with nothing to "key," so they're the wrong tool here despite showing up in every "how do I reach streamers" search.

pitch: "permadeath wolf rp discord bot, free, 20 minutes to try." offer a light incentive: a "streamer's wolf" cosmetic title or founding-player credit for anyone who joins from the stream. this doubles as content: clip the vod for a tiktok/reel (type c, "community moment," already in the plan's video framework) — someone else generating your best raw footage for free.

---

## 7. youtube shorts, distinct from a full youtube channel

the plan explicitly rules out youtube ("overkill until the community is a few hundred"), and that is correct for long-form video, tutorials, and devlogs. shorts is a different surface: it does not require a channel identity or editing investment beyond what you are already producing for tiktok/reels. re-upload the exact same 15-to-30-second clips (type a/b/c/d/e from section 7 of the social plan) to shorts. it is a second discovery algorithm for zero extra production cost, so there is no real reason to skip it once tiktok/reels content exists.

---

## 8. micro-influencer gifting instead of cash sponsorship

you cannot afford paid sponsorships, but you can afford to *gift*. this is one of the most direct-to-audience channels available and worth prioritizing.

**where to find candidates, concretely:** artists in this space report their commissions come overwhelmingly from twitter and discord, so that's where to look, not a generic "influencer marketplace." specific, low-cost-of-entry hubs:
- **discord commission servers.** dedicated servers like the "wolf pack" furry/lgbtq+ community server (centered on commissions, art, vtuber/vrchat avatars) and general furry-art commission servers on disboard/discadia (search the `commissions` and `furry-art` tags) surface active wolf/animal artists directly, often mid-conversation about their own work — a natural place to make a genuine offer rather than a cold dm.
- **toyhouse** (see section 4) doubles as an artist-discovery surface: the same wolf-character threads and worlds feature that reach oc-focused rp players also surface the artists drawing for that crowd.

**the offer:** a free founding-player cosmetic, a named npc/landmark in the world, or a featured commission repost (with full credit) in exchange for one honest post to their audience. this is cheaper than cash, on-brand (art-for-art), and reaches an audience — commission clients and wolf-art followers — that overlaps with your target players but isn't covered by any channel already in the plan.

---

## 9. a conservation tie-in

howlbert is fiction, but it is wolf fiction with real ecological texture (disease, injury, hunger, territory pressure). donating a small, fixed slice of ko-fi income to a real wolf conservation organization gives you a values-aligned hook that reaches an audience none of your other channels touch: wildlife and conservation accounts, who will share a "fiction that funds real wolves" story on principle even if they never touch discord. it costs only a fixed percentage, so it scales with revenue instead of being a fixed expense.

**organizations worth reaching out to, concretely** (most run small-donor-friendly "symbolic adoption" programs, which is the natural mechanic to mirror in-bot — see below):
- **wolf conservation center** (nywolf.org) — new york-based, runs tiered symbolic adoptions from $25, active on social media, and has a track record of engaging with community/creative partnerships.
- **wolf haven international** (wolfhaven.org) — washington-based sanctuary, runs its own symbolic adoption program and is already an "environmental partner" of 1% for the planet, meaning they're set up to work with outside partners donating a revenue slice, not just one-off donors.
- **endangered wolf center** (endangeredwolfcenter.org) — st. louis-based, conservation-and-education focused (a good fit for a "here's what's real" companion angle to the game's fiction), also runs symbolic adoption packages.
- these three are meaningfully more reachable for a small solo project than a huge name like yellowstone forever; start with a low, no-pressure pitch (a fixed 1 to 5% of ko-fi income, framed as "a fiction project that funds real wolf conservation") to one of them rather than a broad cold-email blast.

**the in-bot mirror, to make the tie-in feel real instead of just a footer line:** a `/ko-fi` or `/about` note naming the specific partner org and running total donated, and optionally a cosmetic in-bot "sponsor a real wolf" flourish (a title, or a line in a player's profile) tied to donor tiers — the same symbolic-adoption structure these orgs already use for their own donors, just echoed in-game.

---

## 10. seo-targeted pages on the link hub / lore site

the plan's neocities lore site (section 15) is framed purely as a world bible. the same site is also free, evergreen search real estate if a couple of its pages are deliberately written to answer things people actually google: "wolf roleplay discord," "discord bot with permadeath," "realistic wolf rp bot." one faq-style page answering those phrases in plain language, linked from the homepage, costs almost nothing to add once the site exists and keeps working indefinitely, unlike a social post.

---

## 11. small ttrpg / indie-dev podcast guesting

solo-dev and indie-ttrpg podcasts are numerous, small, and frequently short on guests, which means they say yes to cold pitches more often than you'd expect. a 15-to-20-minute guest slot talking about the disease/injury/permadeath systems reaches a small but very on-target ttrpg-adjacent audience in one sitting, and the clip becomes reusable content (a pull-quote for tumblr, a short video for tiktok).

**specific shows worth a cold pitch:**
- **the solo roleplayers podcast** — interviews content creators in the solo-rp hobby; howlbert's persistent-wolf-you-can-lose framing fits their audience even though it isn't a solo game, since the emotional hook (a character that really matters, that you can really lose) is the same pitch.
- **ye indie'd!** — short, biweekly interviews specifically with indie tabletop rpg creators about their work and design; a near-perfect fit for a "here's the disease/injury system and why i built it this way" conversation.
- **the ansible uplink** — a guest reads/reviews an indie module each episode with the host; less of a direct fit (module-review format, not general dev interviews) but worth a pitch if the format can flex to a devlog-style episode.
- submission processes for all three are informal (direct email/dm, no application portal), which matches "cold pitches work here" — reach out with a short, specific pitch (one brutal mechanic, one sentence on why you built it) rather than a generic press-kit blast.

low volume, but close to zero cost beyond your time, so it is worth a handful of cold pitches once the bot has enough of a story to tell.

---

## 12. dedicated warriors/wolf-rp forums (named, not generic "proboards")

the social plan says "proboards-hosted wolf rp forums" generically. one concrete, still-active example worth targeting by name: **wcrpforums.com**, a warrior-cats-and-adjacent roleplay forum community that runs its own "advertise your rp" and "reviewing communities" style boards where members actively compare and recommend rp spaces to each other. this is a small, high-intent audience — people there are already forum-literate, already rp-committed, and already in the habit of trying new rp communities other members vouch for. post in the correct advertise-your-community board, follow their format exactly, and consider asking an active member for an honest "reviewing communities" style mention once the discord has enough going on to hold up under scrutiny.

---

## 13. get listed on fan-curated "rp discord masterlists"

separate from official directories (disboard, top.gg), the wolf-rp and warriors-rp community maintains its own informal, community-curated lists — pinned google docs, tumblr masterposts, or forum threads titled things like "warrior cats / wolf rp discord servers masterlist" — that circulate hand-to-hand and get reblogged/bumped periodically. these aren't run by any single authority, so there's no formal submission process; the move is to find the currently-circulating ones (search tumblr and the forums in sections 12/17 of the social plan for "masterlist") and ask the maintainer to add howlbert, the same low-key way you'd ask to join an affiliates channel. low effort, and these lists get bookmarked and revisited by exactly the audience you want, unlike a one-time social post.

---

## 14. record your own rp as an "actual play" — your ~24 members are the cast

the biggest owned-content lever you already have the raw material for. actual-play (recorded ttrpg/rp sessions) is one of the most reliable discovery engines in this hobby, and unlike a podcast *about* the game it needs no audience to start — the content **is** the community playing. you have ~24 people and a bot that generates plot beats: that's a cast and a script generator.

- **record it free with craig** ([craig.chat](https://craig.chat/)) — a multi-track discord voice recorder on 340k+ servers, built for exactly this crowd; `/join` to start, `/stop` to end, and it returns a separate clean track *per speaker* (edit one mic without touching the others). run a scheduled voice-channel rp "gathering" (tie it to the in-world moon-howl / fourtrees events the bot already has), record it, lightly cut it in [audacity](https://www.audacityteam.org/) (free).
- **one recording, two publishes:** a "howlbert actual play" video on youtube (evergreen search + feeds the shorts pipeline in section 7) *and* the audio pushed to a podcast host (section 15). one session = a video + a podcast episode + 3–4 clips.
- **why it fits 24 members:** it converts activity you already run into a marketing asset with no new cast to recruit, and it deepens retention (people schedule around a recurring recorded event — section 18) while producing the discovery content at the same time.

---

## 15. an in-world audio series ("field dispatches") — the podcast, done for small scale

you asked about a podcast. a *talk-about-the-game* podcast at 24 members has no audience yet — don't build that. build the version that works at any scale: a short (2–4 min) **in-character narrated audio series** — a wolf's field diary, a warning about river rot, a border report after a rollover — evergreen, searchable, and repurposed straight from the bot's sunrise-news scene prompts (free scripts, the same well section 2 draws from).

- **host it free on [spotify for podcasters](https://podcasters.spotify.com/)** (the former anchor): free hosting that distributes to spotify and exports an rss feed for apple podcasts etc. record in audacity, one voice, minimal edit.
- this is a *different surface* from the in-character text blog (section 2) and the podcast-*guesting* play (section 11): owned audio you control, it seeds podcast-search discovery, and each episode is also a video (waveform + ref art) for youtube/tiktok. keep it in-world so it reads as a persona, not an ad. one episode a fortnight is plenty.

---

## 16. start an email newsletter now — the one audience an algorithm can't throttle

every channel in the plan is rented land (a platform decides your reach). a newsletter is the one **owned, portable** audience: you keep the list, no feed gates it, it compounds. start it at 24 subscribers — that's fine; it's an asset that only grows.

- **[buttondown](https://buttondown.com/)** — free up to 100 subscribers with no feature crippling, clean markdown, you fully own the list (the minimalist, writer-first choice). or **[substack](https://substack.com/)** if you'll trade simplicity for built-in discovery — its recommendation network can surface you to other newsletters' readers, a real if small growth vector. ko-fi also has built-in email broadcasts if you'd rather keep it all in one place.
- content is nearly free: a monthly "dispatch from the wild" = one balance/lore devlog note + one in-world snippet + a "wolf of the month" from your canon roster. link the join form from the strawpage hub and pin it in the server.
- **why it matters at your size:** these 24 are your highest-intent people; capturing even a fraction as subscribers means you can reach them for the kickstarter launch (`docs/KICKSTARTER.md`) *directly* instead of hoping a discord ping or a tweet lands. section 21b of the social plan already flags email as the highest-converting funnel — this is how you start building that list *today*.

---

## 17. a community-editable fan wiki (miraheze), not just the dev-owned lore site

section 10 turns the dev-owned neocities site into seo real estate. a *community-editable* wiki is a different animal and does two jobs a static site can't: it's a collaborative project that gives your 24 members something to build together (retention), and community wikis rank well for exactly the "wolf rp lore / [creature] rp" searches you want.

- **use [miraheze](https://miraheze.org/)** — free, nonprofit, **no ads**, gdpr-clean, community-owned — over [fandom](https://www.fandom.com/), which is ad-cluttered and widely advised against for new wikis in 2026. request a wiki, seed it with your book-one canon roster and world/disease/herb pages (content you already have), then let trusted members add their own wolves and write-ups.
- caveat: miraheze needs a little mediawiki know-how to set up nicely — treat it as a "when a few members want to co-build lore" project, not a day-one task. it's the closest thing to the **"own forum"** you asked about that makes sense at this scale: a standalone web forum would just split a 24-person community, and discord's built-in **forum channels** (section 18) already cover in-server threaded rp/lore for free.

---

## 18. the honest part: at 24 members, retention and co-creation beat acquisition

blunt truth from the research on sub-50 servers: pouring acquisition into a leaky bucket wastes it — a small server with a high active-member ratio beats a bigger dead one, and your fastest growth is turning the 24 into people who **stay and recruit**. this is absent from the whole doc and it's the highest-leverage thing on this list.

- **onboarding:** enable discord's **welcome screen** + **onboarding** (server settings → onboarding) so a new joiner instantly knows what the server is in one sentence and has a clear first action (`/register`, pick a pack). first impressions decide whether a join becomes a member.
- **one reliable weekly ritual beats four random ones:** a fixed weekly in-world event (a fourtrees gathering, a moon-howl night) people schedule around — pair it with the section-14 recording so the ritual doubles as content.
- **question-of-the-day / low-pressure prompts:** a recurring in-character prompt ("what would your wolf do at the border tonight?") keeps the channel warm; empty channels kill small servers.
- **the 48-hour lurker dm:** when someone joins and doesn't post, a friendly manual dm two days later ("saw you joined — anything you're looking for?") recovers a surprising share of silent joiners. trivial at this scale.
- **you visibly *playing*, not just moderating** — small servers live or die on the founder being a genuine participant.
- **co-creation = free evangelism:** let members name an npc, vote on a plot branch, or get a landmark named for their wolf (the bot already has npc/landmark hooks). people don't leave — or shut up about — a world they helped build. it's the cheapest word-of-mouth engine you have.

---

## 19. run one time-boxed "server event" as a launch moment

a small server needs *reasons to invite a friend today*, not just a standing open door. a one-off, **dated**, in-world event — "the great migration," a "founding season," a limited plot arc with a commemorative cosmetic for anyone who takes part — creates urgency, gives members a concrete "come do this with me this weekend" pitch, and is inherently postable (a countdown, a recap, screenshots) across every channel in the social plan.

- announce a date, offer a **participation-only cosmetic** (a founding-season title/badge — you already have the cosmetic/title system), and let current members bring one friend into the event specifically; hang a light referral hook off it (section 1).
- recap it as content afterward (a section-14 recording, a newsletter dispatch, a shorts clip). distinct from the *cross-server* joint events in section 3 — this one is your own house throwing the party.

---

## 20. reserve your namespace while it's free

cheap housekeeping, not a channel — claim your name everywhere before a squatter does, so future searches resolve to you.
- **create the subreddit [r/howlbert](https://www.reddit.com/)** even if you don't use it yet: an owned space that ranks in search and is ready when you're bigger (the social plan only covers posting to *existing* subreddits). free to reserve; sit on it.
- grab the matching handle on any in-plan platform you haven't claimed, plus a **[guilded](https://www.guilded.gg/)** mirror of the discord as a hedge/landing page. minutes of work, avoids a future headache.

---

## priority read

**start with the 24-member reality (18).** at your size, acquisition into a low-retention server leaks out as fast as it comes in — onboarding, one reliable weekly ritual, the 48-hour lurker dm, and co-creation are the cheapest, highest-leverage moves here, and every acquisition play converts better once they're in place. then **start the email list (16)** — the one audience no algorithm can throttle, and what you'll actually launch the kickstarter to. then **record your rp as actual play (14)** — it turns the weekly activity you already run into discovery content with no new cast to find.

from the original list, **finishing the referral loop (1)** and **discord discovery (5)** remain the strongest acquisition plays (free, compounding, high-intent), and **the in-character wolf account (2)**, **toyhouse/art fight (4)**, **micro-influencer gifting (8)**, and **the conservation tie-in (9)** are the best warm-audience next tier. the in-world audio series (15), fan wiki (17), one-off server event (19), and namespace housekeeping (20) are strong opportunistic adds. layer the rest on once the retention loop and your owned assets (list, audio, wiki) are running.

