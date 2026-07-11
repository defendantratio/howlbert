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

### ready to post: smallstreamercommunity collab ad

post this in smallstreamercommunity's freeform collab ad channel, filled into their required template. it leads with the hook (a wolf that can really die), keeps expectations loose since this is a discord bot rather than a stream native game, and is explicit about the darker themes and the 18+ server up front so nobody signs up for a surprise.

> **platform:** discord (howlbert is a free discord bot, playable and showable on whatever platform you stream: twitch, youtube, kick, tiktok live, all fine)
>
> **game(s):** howlbert, a permadeath wolf roleplay bot. real injuries and disease, no cooldowns (energy is the only throttle), a wolf you can genuinely lose for good.
>
> **timezone:** flexible, async friendly. i'm one solo dev, not a live co host, so this isn't a "stream together" collab, think "try it live on your own schedule" rather than a scheduled two person stream.
>
> **general information about the collab:** i'm looking for streamers to try howlbert live, chat driven, for 20 to 30 minutes, register a wolf, hunt, forage, maybe watch chat pick which risky choice to make. it's slow burn and stat driven, closer to a cozy survival sim than a shooter, so it plays well with chat participation (let chat vote on actions, name the wolf, etc). i'll be in your discord or chat during the stream if you want live support, and i'll clip and credit the vod afterward (with your permission) for howlbert's own socials. happy to set your wolf, or a wolf named after your channel, up with a small "streamer's wolf" cosmetic title as a thank you, and credit you as a founding tester in the server.
>
> **age range of collab partners:** the howlbert discord server is 18+ only, so i'm looking for streamers whose audience skews adult, or who are comfortable filtering for that.
>
> **is your content family friendly?:** no. it's fantasy wolf ecology content (hunting, injury, illness, and permadeath are core mechanics), with animal death and some genuinely dark themes (terminal illness, mercy killing). no gore and no sexual content, but the tone is closer to a nature documentary than a cozy game, and it's paired with an 18+ discord.
>
> **is your content for those 18+ only?:** yes. the discord server howlbert lives in is 18+ only.
>
> **what i want out of the collab:** a genuine 20+ minute live try through in front of your chat, a mention or link to the discord if you had fun, and (only with your ok) permission to clip a moment or two for howlbert's own social accounts with full credit to you.
>
> **what i don't want from the collab:** no exclusivity, no pressure to make it a recurring series unless you want to, no need to oversell it to your chat. if it's not for you or your audience, no hard feelings and thanks for the look.

adjust the tone slightly per-server (some collab channels want it terser), but keep the "what I don't want" line — a no-pressure ask reads as trustworthy in these communities and gets more replies than a pitch that sounds like it needs a yes.

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

## priority read

if only doing a few of these: **finishing the referral loop (1)** and **discord discovery (5)** are the highest-leverage because they are free, compounding, and aimed at people already inside or already searching — closer to section 16/21b's "highest-intent funnel" framing in the social media plan than a cold audience play, and (1) in particular is mostly done already. **the in-character wolf account (2)**, **toyhouse/art fight (4)**, and **micro-influencer gifting (8)** are the best next tier: cheap, on-brand, and reach warmer, more specific audiences than a generic post. **the conservation tie-in (9)** is the one genuinely different acquisition angle in this whole list — it reaches people none of your other channels touch. the rest are good opportunistic adds once the core runway from `docs/SOCIAL_MEDIA.md` is already running.

## COLLABORATION TEMPLATE
-
Consider using this template when looking for collaboration opportunities! This can help you get on the same page as potential collab partners faster:
-

Platform:
Game(s):
Timezone:
General information about the collab:

Age range of collab partners:
Is your content Family-Friendly?: Yes/No
Is your content for those 18+ Only?: Yes/No

What I want out of the collab:
What I don't want from the collab:

