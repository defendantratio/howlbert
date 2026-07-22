# ko-fi shop; howlbert

paste these into ko-fi shop listings. **product titles should include the keywords shown** so the webhook can match them (or add each item's `direct_link_code` to `KOFI_SHOP_CATALOG` in `config.py` after creation).

**on every order:** buyer must be in discord, have used `/register`, and put their **discord user id** in the order message (see `/patron`).

**server age:** the discord server is 18+ only; note this on the ko-fi page since every item here requires joining it to redeem.

---

## tier 1; digital and bones

### bone pouch; $5

**one-time in-game thank-you for howlbert (discord wolf rp bot).**

- **75 bones** on your wolf (15 per $1)
- delivered automatically if your discord user id is in the order message
- personal reward; never taken from pack treasury
- requires `/register` in our discord server

put your **discord user id** in the order notes. you'll get bones instantly or a `/redeem` code via dm.

---

### bone cache; $10

**larger one-time bone thank-you.**

- **150 bones** on your wolf
- same rules as bone pouch; discord id required, `/register` first
- great for a bigger thank-you without a monthly membership

---

### gift a bone pouch; $5

**buy a bone pouch for another player.**

- you receive a **one-time redeem code** via discord dm
- any registered player can use `/redeem CODE` for **75 bones**
- perfect for birthdays, packmates, or welcoming a new wolf

put **your** discord user id in the message so we know where to send the gift code.

---

### supporter badge (digital); $5

**name on the den wall; no in-game stats.**

- your name (discord or wolf name) on the **supporters list** in discord + readme
- thank-you post in our announcements channel (opt out anytime)
- delivered within **7 days** via discord dm

not a substitute for memberships; pure recognition.

---

### den wallpaper pack; $8

**digital download; wolf and landscape art for your desktop or phone.**

- zip of den-themed wallpapers (personal use only)
- ko-fi digital delivery + confirmation dm
- delivered within **3 days**

no in-game bones included.

---

## tier 2; rp extras

### herb satchel; $8

**listing title (use exactly):** `herb satchel`

**paste into ko-fi description:**

```
the green tongue, without the walk to find it.

herb satchel is a one-time in-game item for howlbert, our discord wolf rp bot. purchase grants your choice of herb (pick one from the compendium, `/herbs action:guide`), added to your inventory as raw stock, same as if you'd foraged it yourself.

what you get
✦ 2 to 4 units of one herb of your choice, in its raw/dried form
✦ still needs preparing and using the normal way: `/herbs action:prepare`, `/medic action:treat`
✦ does not skip the medicine check, the right-herb-for-the-ailment matching, or any of the normal treatment mechanics

what this is not
✦ not a cure, not a heal, not a shortcut around any check or roll
✦ does not touch injuries, disease, or hp directly; it's stock, not a spell
✦ restricted/poison herbs are not available through this listing

how to use
1. join our discord server and /register your wolf first
2. put your discord user id **and** which herb you want (exact name from `/herbs action:guide`) in this order message
3. after purchase, check `/bones action:inventory` for your herb

not sold for bones at the in-game trading post. personal reward only; never taken from pack treasury.

questions? open a ticket in discord or dm staff.
```

**webhook keywords:** herb satchel, herb bundle, choose herb

**ko-fi image:** illustrated linework + soft color (see `docs/shop-assets/herb-satchel.png`). a bundle of dried herbs tied with cord, den-store style.

put your **discord user id and chosen herb** in the order notes.

---

### den landmark name; $20

**name a place in the world's lore.**

- a creek bend, rock outcrop, trail fork, or similar landmark named after your wolf or chosen name
- added to the server lore doc / map notes
- delivered within **14 days**; we'll confirm the name with you first

---

### quest hook commission; $30

**a personal story hook for your wolf.**

- short custom quest premise (hunt, patrol, explore, or social)
- run with you and staff in rp; not a guaranteed auto-complete bot quest
- delivered within **14 days** via discord dm to plan session

---

### first hunt story snippet; $10

**short prose piece about your wolf's first kill or first journey.**

- ~200 to 400 words, digital (discord post or pdf)
- you provide wolf details and any tone preferences
- delivered within **7 days**

---

## tier 3; premium

### wolf portrait (digital commission); $40

**custom digital art of your wolf.**

- one character, simple background
- style and reference discussed via dm after purchase
- delivered within **21 days** (or agreed timeline)
- personal use; ask about server rp posting rights

**commission; not instant.** we'll contact you within 3 days to start.

---

### custom item name (cosmetic); $35

**name a cosmetic in-game item** (toy bundle, trinket, etc.)

- cosmetic flavor only; **no stat boosts or combat advantage**
- subject to balance and theme approval
- delivered within **14 days**

---

### legend gift card (1 month); $25

**gift legend-tier thank-yous to any registered player.**

- redeem code for **225 bones**, **legend** recognition, **+3 `/bones action:daily`** for **35 days**, +10 mood / +2 standing on redeem
- you receive the code via dm; keep it or give it away
- recipient uses `/redeem CODE`

put your discord user id in the order message.

---

## shop link codes (configured in bot)

| # | product | ko-fi link |
|---|---------|------------|
| 1 | bone pouch | https://ko-fi.com/s/f5d07feec4 |
| 2 | bone cache | https://ko-fi.com/s/86a62f713a |
| 3 | gift a bone pouch | https://ko-fi.com/s/79c40a6fa6 |
| 4 | supporter badge | https://ko-fi.com/s/4bd6954008 |
| 5 | den wallpaper pack | https://ko-fi.com/s/c862f55df1 |
| 6 | den landmark name | https://ko-fi.com/s/5cb52af6e0 |
| 7 | quest hook commission | https://ko-fi.com/s/f565f7daee |
| 8 | first hunt story snippet | https://ko-fi.com/s/bba5807b42 |
| 9 | wolf portrait | https://ko-fi.com/s/1acef91903 |
| 10 | custom item name | https://ko-fi.com/s/7293d845b2 |
| 11 | legend gift card | https://ko-fi.com/s/ff775b47c9 |
| 12 | herb satchel ($8) | https://ko-fi.com/s/350f8969d2 |

## admin

- `/patronadmin orders`; pending manual fulfillments
- `/patronadmin fulfill`; mark delivered
- `/patronadmin code`; manual fallback codes
