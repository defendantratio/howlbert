"""RP scene prompts: a curated static library plus player-suggested / admin-added entries."""

from __future__ import annotations

import random

import database as db
from config import GREAT_PACKS, LONER_KEY, ROGUE_KEY

MOOD_TAGS = (
    "playful",
    "tense",
    "somber",
    "romantic",
    "eerie",
    "hopeful",
    "mischievous",
    "reflective",
)

MAX_PROMPT_LEN = 280

# General prompts; usable by any wolf in any pack.
GENERAL_PROMPTS: tuple[dict, ...] = (
    {"text": "A storm is rolling in fast. Where does your wolf take shelter, and who do they find there?", "mood": "tense"},
    {"text": "Your wolf finds a strange twoleg object half-buried near the border. Do they investigate or avoid it?", "mood": "eerie"},
    {"text": "Two packmates haven't spoken since a falling-out moons ago. Something forces them into the same place tonight.", "mood": "tense"},
    {"text": "A pup asks your wolf to tell them about the stars. What story do they tell?", "mood": "reflective"},
    {"text": "Your wolf catches their reflection in still water and doesn't recognize themself for a moment. Why?", "mood": "reflective"},
    {"text": "A rival pack member is caught alone on your territory, unarmed and lost. What does your wolf do?", "mood": "tense"},
    {"text": "It's the first warm day after a long winter. Your wolf drags a packmate out to enjoy it, whether they want to or not.", "mood": "playful"},
    {"text": "Your wolf finds an old scent trail that shouldn't still be there — it belongs to someone long gone.", "mood": "eerie"},
    {"text": "A game of chase turns into something more serious when someone gets a little too competitive.", "mood": "mischievous"},
    {"text": "Your wolf is asked to keep a secret that could hurt someone they love if it came out. Do they keep it?", "mood": "tense"},
    {"text": "A young wolf challenges your wolf to a wrestling match in front of the whole den. Pride is on the line.", "mood": "playful"},
    {"text": "Your wolf wakes from a dream they can't quite remember, but it's left them unsettled all day.", "mood": "eerie"},
    {"text": "Someone your wolf trusts asks them for a favor that crosses a line. How do they respond?", "mood": "tense"},
    {"text": "Two wolves who've never met share a kill out of necessity during a hard hunt. An odd friendship begins.", "mood": "hopeful"},
    {"text": "Your wolf finds a flower blooming somewhere it shouldn't be able to grow.", "mood": "reflective"},
    {"text": "A teasing comment lands wrong, and now your wolf has to decide whether to let it go or push back.", "mood": "mischievous"},
    {"text": "Your wolf is left in charge of pups for the day while the adults are away. Chaos, predictably, ensues.", "mood": "playful"},
    {"text": "An old wound aches worse than usual tonight. Your wolf can't sleep, and someone notices.", "mood": "somber"},
    {"text": "A courting gift goes hilariously wrong. What was it supposed to be, and what happened instead?", "mood": "romantic"},
    {"text": "Your wolf overhears something they weren't meant to hear. Now what?", "mood": "tense"},
    {"text": "The pack gathers to howl at the full moon. Someone's voice breaks partway through — why?", "mood": "somber"},
    {"text": "Your wolf finds someone else's claw marks on a tree at the edge of their territory, fresh and deliberate.", "mood": "eerie"},
    {"text": "A packmate returns from a long patrol with news that changes everything for the evening.", "mood": "tense"},
    {"text": "Your wolf tries (and fails) to teach a pup how to hunt. The pup has other ideas.", "mood": "playful"},
    {"text": "Someone your wolf cares for is grieving, and they don't know how to help.", "mood": "somber"},
    {"text": "A long-buried rivalry resurfaces over something as small as a contested kill.", "mood": "tense"},
    {"text": "Your wolf finds themself drawn to a stranger's scent on the wind, and can't explain why.", "mood": "romantic"},
    {"text": "The den is quiet tonight — too quiet. Your wolf goes looking for why.", "mood": "eerie"},
    {"text": "A favor owed finally gets called in, at the worst possible time.", "mood": "tense"},
    {"text": "Your wolf shares a meal with someone they shouldn't trust, and finds themself trusting them anyway.", "mood": "hopeful"},
)

# Pack-flavored prompts, drawing on each Great Pack's terrain/path/motto.
PACK_PROMPTS: dict[str, tuple[dict, ...]] = {
    "greyspire": (
        {"text": "A rockslide blocks the High Pass. Someone has to be the one to clear it, alone, in the cold.", "mood": "tense"},
        {"text": "A Greyspire elder tells a pup that 'strength is truth, blood is law' — and the pup asks what that really means.", "mood": "reflective"},
        {"text": "Two wolves spar at Stoneguard Watch to settle who leads the next patrol. No hard feelings — mostly.", "mood": "playful"},
    ),
    "mistmoor": (
        {"text": "The swamp fog rolls in thick tonight, and something is moving just out of sight.", "mood": "eerie"},
        {"text": "A Mistmoor wolf brings back something the Maw is said to favor. Is it an offering, or a warning?", "mood": "eerie"},
        {"text": "Mud season has made every den entrance a mess. Someone's tracking it in on purpose to annoy a packmate.", "mood": "mischievous"},
    ),
    "thistlehide": (
        {"text": "Your wolf asks the ancestor-tree a question they're afraid of the answer to.", "mood": "reflective"},
        {"text": "Fallen leaves cover an old grave marker in the forest. Someone stops to clear it.", "mood": "somber"},
        {"text": "A Thistlehide pup gets lost chasing a squirrel too far from the den. Someone has to find them before dark.", "mood": "tense"},
    ),
    "silverrush": (
        {"text": "The river runs high after rain, and a packmate dares another to cross it anyway.", "mood": "playful"},
        {"text": "Someone leaves a stone at the weeping stones, but won't say who it's for.", "mood": "somber"},
        {"text": "A Silverrush wolf teaches an outsider to read the current. It's harder than it looks.", "mood": "hopeful"},
    ),
}

LONER_PROMPTS: tuple[dict, ...] = (
    {"text": "A loner crosses paths with a pack patrol on neutral ground. Neither side wants trouble — yet.", "mood": "tense"},
    {"text": "Your wolf has gone without company for so long that a simple kind word from a stranger catches them off guard.", "mood": "reflective"},
    {"text": "A loner is offered a place in a den for the night. Do they take the risk?", "mood": "hopeful"},
)

ROGUE_PROMPTS: tuple[dict, ...] = (
    {"text": "Your wolf is caught stealing from a pack's cache. There's no good way to explain this.", "mood": "tense"},
    {"text": "An old grudge against a Great Pack finally comes to a head.", "mood": "tense"},
    {"text": "A rogue offers information to a pack — for a price they know the pack won't like.", "mood": "mischievous"},
)

# Book One: The Blinking — phase-tagged prompts that lean on the plot's news beats.
# Phase numbers match engine.plot_blinking.PHASES.
BLINKING_PROMPTS: dict[int, tuple[str, ...]] = {
    1: (
        "The bruised moon hangs wrong overhead. Your wolf can't stop looking up at it.",
        "Someone in the den swears the missing edge of the moon is shaped like a bite.",
    ),
    2: (
        "Star-speech rides the wind tonight. Your wolf catches a few words they can't shake.",
        "A border patrol stops mid-stride, listening to something none of them can name.",
    ),
    3: (
        "Rust-red streaks the high spur of the mountain. Your wolf goes to see for themself.",
        "An elder refuses to say what they think is bleeding from the peak.",
    ),
    4: (
        "Dead fish line the riverbank, belly-up in water that's far too warm. Your wolf can't drink from it.",
        "Something about the warm river makes the wolves who rely on it uneasy in a way they can't explain.",
    ),
    5: (
        "The usual chewing sound from the Drown-Sick vigil hasn't come tonight. The silence is louder than it should be.",
        "A Mistmoor wolf keeps a sacred vigil alone, waiting for a sound that may never return.",
    ),
    6: (
        "Cat musk laced with wolf scent at the border has everyone pointing fingers. Your wolf has their own suspicions.",
        "A patrol grows tense as every shadow starts to look like Greyspire.",
    ),
    7: (
        "Logging scars cut deep near the old paper mill, and something about the place draws your wolf closer than they'd like.",
        "An outlaw's scent threads through the forest, fresh enough to follow if your wolf dares.",
    ),
    8: (
        "Something ancient seems to sleep beneath the mill's rotted timbers. Your wolf swears they can taste iron on the air.",
        "A find at the mill could be worth bones and standing both — if it's safe to take.",
    ),
    9: (
        "A howl carries the names of the forgotten dead, and your wolf flinches at one name in particular.",
        "The pack's unity feels thin tonight; even the howl costs more than it used to.",
    ),
    10: (
        "Bones go missing from the treasury, and every den is ready to blame another.",
        "A cat truce cracks at the seams. Your wolf is caught in the middle of it.",
    ),
    11: (
        "Wolves gather at the river bend to name what was buried. Your wolf has something to say, if they can find the words.",
        "The naming howl rises over the water. Your wolf isn't sure they're ready to let go.",
    ),
    12: (
        "The river runs cool again, and cat clans meet packs at the border stones for a fragile truce.",
        "Book One closes tonight. Your wolf takes one last look at what The Blinking cost them.",
    ),
}

PACK_LABEL_CHOICES = tuple(GREAT_PACKS.keys()) + (LONER_KEY, ROGUE_KEY)


def _static_pool(pack: str | None, mood: str | None) -> list[dict]:
    pool: list[dict] = []
    if pack is None:
        pool.extend(GENERAL_PROMPTS)
        for entries in PACK_PROMPTS.values():
            pool.extend(entries)
        pool.extend(LONER_PROMPTS)
        pool.extend(ROGUE_PROMPTS)
    elif pack == LONER_KEY:
        pool.extend(LONER_PROMPTS)
    elif pack == ROGUE_KEY:
        pool.extend(ROGUE_PROMPTS)
    elif pack in PACK_PROMPTS:
        pool.extend(GENERAL_PROMPTS)
        pool.extend(PACK_PROMPTS[pack])
    else:
        pool.extend(GENERAL_PROMPTS)
    if mood:
        pool = [p for p in pool if p.get("mood") == mood]
    return pool


def _db_pool(guild_id: int, pack: str | None, mood: str | None) -> list[dict]:
    rows = db.list_rp_prompts(guild_id, status="approved", pack=pack, mood=mood)
    return [{"text": r["text"], "mood": r["mood"] if "mood" in r.keys() else None} for r in rows]


def random_prompt(
    guild_id: int,
    *,
    pack: str | None = None,
    mood: str | None = None,
    plot_phase: int | None = None,
) -> dict | None:
    if plot_phase is not None:
        choices = BLINKING_PROMPTS.get(plot_phase, ())
        if not choices:
            return None
        return {"text": random.choice(choices), "mood": None, "source": "plot_blinking"}
    pool = _static_pool(pack, mood) + _db_pool(guild_id, pack, mood)
    if not pool:
        return None
    return random.choice(pool)


def submit_prompt(
    guild_id: int,
    discord_id: int,
    text: str,
    *,
    pack: str | None = None,
    mood: str | None = None,
    day: int | None = None,
) -> tuple[bool, str]:
    cleaned = text.strip()
    if not cleaned:
        return False, "write a prompt before suggesting it."
    if len(cleaned) > MAX_PROMPT_LEN:
        return False, f"keep prompts under **{MAX_PROMPT_LEN}** characters."
    db.add_rp_prompt(
        guild_id,
        cleaned,
        pack=pack,
        mood=mood,
        submitted_by=discord_id,
        status="pending",
        created_day=day,
    )
    return True, "suggestion sent for admin review. thank you!"


def add_prompt_direct(
    guild_id: int,
    admin_id: int,
    text: str,
    *,
    pack: str | None = None,
    mood: str | None = None,
    plot_phase: int | None = None,
    day: int | None = None,
) -> tuple[bool, str]:
    cleaned = text.strip()
    if not cleaned:
        return False, "write a prompt to add."
    if len(cleaned) > MAX_PROMPT_LEN:
        return False, f"keep prompts under **{MAX_PROMPT_LEN}** characters."
    prompt_id = db.add_rp_prompt(
        guild_id,
        cleaned,
        pack=pack,
        mood=mood,
        plot_phase=plot_phase,
        submitted_by=admin_id,
        status="approved",
        created_day=day,
    )
    return True, f"prompt `#{prompt_id}` added and live for `/rpprompt action:get`."


def approve_prompt(prompt_id: int, reviewer_id: int) -> tuple[bool, str]:
    row = db.get_rp_prompt(prompt_id)
    if not row:
        return False, f"no prompt `#{prompt_id}`."
    if row["status"] != "pending":
        return False, f"prompt `#{prompt_id}` is already **{row['status']}**."
    db.set_rp_prompt_status(prompt_id, "approved", reviewed_by=reviewer_id)
    return True, f"prompt `#{prompt_id}` approved and live."


def reject_prompt(prompt_id: int, reviewer_id: int) -> tuple[bool, str]:
    row = db.get_rp_prompt(prompt_id)
    if not row:
        return False, f"no prompt `#{prompt_id}`."
    if row["status"] != "pending":
        return False, f"prompt `#{prompt_id}` is already **{row['status']}**."
    db.set_rp_prompt_status(prompt_id, "rejected", reviewed_by=reviewer_id)
    return True, f"prompt `#{prompt_id}` rejected."


def list_pending(guild_id: int, limit: int = 10) -> list:
    return db.list_rp_prompts(guild_id, status="pending")[:limit]
