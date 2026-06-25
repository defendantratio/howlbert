# Ko-fi Shop; Howlbert

Paste these into Ko-fi Shop listings. **Product titles should include the keywords shown** so the webhook can match them (or add each item's `direct_link_code` to `KOFI_SHOP_CATALOG` in `config.py` after creation).

**On every order:** buyer must be in Discord, have used `/register`, and put their **Discord user ID** in the order message (see `/patron`).

---

## Tier 1; Digital & bones

### Bone Pouch; $5

**One-time in-game thank-you for Howlbert (Discord wolf RP bot).**

- **75 bones** on your wolf (15 per $1)
- Delivered automatically if your Discord user ID is in the order message
- Personal reward; never taken from pack treasury
- Requires `/register` in our Discord server

Put your **Discord user ID** in the order notes. You'll get bones instantly or a `/redeem` code via DM.

---

### Bone Cache; $10

**Larger one-time bone thank-you.**

- **150 bones** on your wolf
- Same rules as Bone Pouch; Discord ID required, `/register` first
- Great for a bigger thank-you without a monthly membership

---

### Gift a Bone Pouch; $5

**Buy a bone pouch for another player.**

- You receive a **one-time redeem code** via Discord DM
- Any registered player can use `/redeem CODE` for **75 bones**
- Perfect for birthdays, packmates, or welcoming a new wolf

Put **your** Discord user ID in the message so we know where to send the gift code.

---

### Supporter Badge (Digital); $5

**Name on the den wall; no in-game stats.**

- Your name (Discord or wolf name) on the **supporters list** in Discord + README
- Thank-you post in our announcements channel (opt out anytime)
- Delivered within **7 days** via Discord DM

Not a substitute for memberships; pure recognition.

---

### Den Wallpaper Pack; $8

**Digital download; wolf & landscape art for your desktop or phone.**

- ZIP of den-themed wallpapers (personal use only)
- Ko-fi digital delivery + confirmation DM
- Delivered within **3 days**

No in-game bones included.

---

## Tier 2; RP extras

### Revive; $35

**Listing title (use exactly):** `Revive`

**Paste into Ko-fi description:**

```
When your wolf falls in Mistmoor, not every story has to end.

Revive is a one-time in-game item for Howlbert, our Discord wolf RP bot. Purchase grants a Revive token to your inventory; use it when your active wolf is dead to pull them back from the mist.

What you get
• Same wolf; same name, attributes, skills, standing, bones, pack, and inventory
• Returned at 1 HP with hunger and thirst restored
• If they died of old age (120 moons), they return at 60 moons

How to use
1. Join our Discord server and /register your wolf first
2. Put your Discord user ID in this order message (see /patron in-server for help)
3. After purchase, check /inventory for Revive
4. When your wolf dies: `/bones action:use item:revive`

Not sold for bones at the in-game trading post. Personal reward only; never taken from pack treasury. One Revive item per purchase.

Questions? Open a ticket in Discord or DM staff.
```

**Webhook keywords:** revive, second chance, bring back

**Ko-fi image:** illustrated linework + soft color (see `docs/shop-assets/revive.png`). Pale mist, wolf rising from snow, cool moon; breath returning.

Put your **Discord user ID** in the order notes.

---

### Reincarnation; $28

**Listing title (use exactly):** `Reincarnation`

**Paste into Ko-fi description:**

```
The soul remembers. The body changes.

Reincarnation is a one-time in-game item for Howlbert, our Discord wolf RP bot. For wolves who died but whose story isn't finished; return in a new body with a new name, while keeping the build you earned.

What you keep
• Attributes, skills, standing, bones, Great Pack, and inventory items
• Your account, legacy, and wolf slot on your profile

What's new
• A new wolf name you choose at use
• 12 moons of age (juvenile); a second life in the pack
• Role synced to your new age

What resets
• Prey hoard and toys cleared (fresh start for `/prey` and `/playpen action:toys`)
• Full HP, healthy condition, no injuries or disease

How to use
1. Join our Discord server and /register first
2. Put your Discord user ID in this order message (see /patron in-server)
3. After purchase, check /inventory for Reincarnation
4. When your wolf dies: `/bones action:use item:reincarnation new_name:YourNewName`

Not the same as Reincarnation ($28); Revive brings back the same wolf unchanged. Reincarnation is for a new identity with the same soul and stats.

Not sold for bones. Personal reward only. One item per purchase.

Questions? Open a ticket in Discord or DM staff.
```

**Webhook keywords:** reincarnation, new life, new body

**Ko-fi image:** illustrated linework + soft color (see `docs/shop-assets/reincarnation.png`). Ghost wolf + younger wolf through mist/stones; same soul, new body.

Put your **Discord user ID** in the order notes.

---

### Den Landmark Name; $20

**Name a place in the world's lore.**

- A creek bend, rock outcrop, trail fork, or similar landmark named after your wolf or chosen name
- Added to the server lore doc / map notes
- Delivered within **14 days**; we'll confirm the name with you first

---

### Quest Hook Commission; $30

**A personal story hook for your wolf.**

- Short custom quest premise (hunt, patrol, explore, or social)
- Run with you and staff in RP; not a guaranteed auto-complete bot quest
- Delivered within **14 days** via Discord DM to plan session

---

### First Hunt Story Snippet; $10

**Short prose piece about your wolf's first kill or first journey.**

- ~200-400 words, digital (Discord post or PDF)
- You provide wolf details and any tone preferences
- Delivered within **7 days**

---

## Tier 3; Premium

### Wolf Portrait (Digital Commission); $40

**Custom digital art of your wolf.**

- One character, simple background
- Style and reference discussed via DM after purchase
- Delivered within **21 days** (or agreed timeline)
- Personal use; ask about server RP posting rights

**Commission; not instant.** We'll contact you within 3 days to start.

---

### Custom Item Name (Cosmetic); $35

**Name a cosmetic in-game item** (toy bundle, trinket, etc.)

- Cosmetic flavor only; **no stat boosts or combat advantage**
- Subject to balance and theme approval
- Delivered within **14 days**

---

### Legend Gift Card (1 Month); $25

**Gift Legend-tier thank-yous to any registered player.**

- Redeem code for **225 bones**, **Legend** recognition, **+3 `/bones action:daily`** for **35 days**, +10 mood / +2 standing on redeem
- You receive the code via DM; keep it or give it away
- Recipient uses `/redeem CODE`

Put your Discord user ID in the order message.

---

## Shop link codes (configured in bot)

| # | Product | Ko-fi link |
|---|---------|------------|
| 1 | Bone Pouch | https://ko-fi.com/s/f5d07feec4 |
| 2 | Bone Cache | https://ko-fi.com/s/86a62f713a |
| 3 | Gift a Bone Pouch | https://ko-fi.com/s/79c40a6fa6 |
| 4 | Supporter Badge | https://ko-fi.com/s/4bd6954008 |
| 5 | Den Wallpaper Pack | https://ko-fi.com/s/c862f55df1 |
| 6 | Den Landmark Name | https://ko-fi.com/s/5cb52af6e0 |
| 7 | Quest Hook Commission | https://ko-fi.com/s/f565f7daee |
| 8 | First Hunt Story Snippet | https://ko-fi.com/s/bba5807b42 |
| 9 | Wolf Portrait | https://ko-fi.com/s/1acef91903 |
| 10 | Custom Item Name | https://ko-fi.com/s/7293d845b2 |
| 11 | Legend Gift Card | https://ko-fi.com/s/ff775b47c9 |
| 12 | Revive ($35) | https://ko-fi.com/s/75109e65b8 |
| 13 | Reincarnation ($28) | https://ko-fi.com/s/931aa27911 |

## Admin

- `/patronadmin orders`; pending manual fulfillments
- `/patronadmin fulfill`; mark delivered
- `/patronadmin code`; manual fallback codes
