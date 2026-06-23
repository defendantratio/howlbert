"""Medic sacred-site visits every half-moon."""

from __future__ import annotations

import random
import sqlite3

from engine.role_features import is_full_medic

HALF_MOON_DAYS = 3
SACRED_STANDING_PENALTY = -2

# Words heard at the sacred place (Maw faith; pack-flavored where noted)
SACRED_ANCESTOR_LINES = (
    "Tend the wounded before you tend your pride.",
    "Poison in a warrior's bag is rot in the den's throat.",
    "The green tongue is trusted because it listens.",
    "What you heal returns to the Maw through the living.",
    "Names spoken at the stone are not forgotten.",
    "Half-moon to half-moon; the eye watches whether you walked.",
    "Grief in the den is illness too; do not turn from it.",
    "Apprentice paws learn by watching; teach them at the sick-bed.",
    "The chewing grows quieter when the healer keeps faith.",
    "Turn forbidden leaves to the den store; hoarding is cowardice.",
    "Cough in the nursery is a warning, not a nuisance.",
    "Your oath is to the sick, not to the Alpha's comfort.",
)

SACRED_ANCESTOR_BY_PACK: dict[str, tuple[str, ...]] = {
    "greyspire": (
        "Teeth break; the healer's paws must not.",
        "Strength without mercy is only hunger wearing a wolf's face.",
    ),
    "mistmoor": (
        "The Belly-Rip hears what you withhold from the sick.",
        "Fog lies; your hands on a fever do not.",
    ),
    "thistlehide": (
        "Fur hides wounds poorly when the healer stays away.",
        "Groom the spirit when the body will not mend.",
    ),
    "silverrush": (
        "Tears on the wind carry grief the den will need you to mend.",
        "Listen before you poultice; grief speaks in silence.",
    ),
}


def pick_sacred_ancestor_word(user) -> str:
    """One cryptic line from the ancestors for this visit."""
    gp = user["great_pack"] if user and "great_pack" in user.keys() else None
    pack_lines = SACRED_ANCESTOR_BY_PACK.get(gp or "", ())
    if pack_lines and random.random() < 0.45:
        return random.choice(pack_lines)
    return random.choice(SACRED_ANCESTOR_LINES)


def _days_since_visit(user, day: int) -> int:
    last = int(user["last_sacred_day"] if "last_sacred_day" in user.keys() else 0)
    if last <= 0:
        return day
    return max(0, day - last)


def sacred_visit_due(user, day: int) -> bool:
    """True if a visit is needed before the next rollover standing penalty."""
    if not is_full_medic(user):
        return False
    last = int(user["last_sacred_day"] if "last_sacred_day" in user.keys() else 0)
    if last >= day:
        return False
    if not last and day < HALF_MOON_DAYS:
        return False
    return _days_since_visit(user, day) >= HALF_MOON_DAYS - 1


def format_sacred_visit_reminder(user, day: int) -> str | None:
    """Player-facing status for cooldowns, profile, and /vitals action:condition."""
    if not is_full_medic(user):
        return None
    last = int(user["last_sacred_day"] if "last_sacred_day" in user.keys() else 0)
    if last >= day:
        return (
            "**Sacred visit:** done this sunrise. "
            "Next due within **{days}** sunrises.".format(days=HALF_MOON_DAYS)
        )
    if not last and day < HALF_MOON_DAYS:
        grace = HALF_MOON_DAYS - day
        return (
            f"**Sacred visit:** **{grace}** sunrise(s) of grace as a new Medic; "
            f"then every **{HALF_MOON_DAYS}** sunrises use `/vitals action:sacred` "
            f"or lose **{SACRED_STANDING_PENALTY}** standing."
        )
    elapsed = _days_since_visit(user, day)
    if elapsed >= HALF_MOON_DAYS:
        return (
            "**Sacred visit:** **overdue**; rollover costs "
            f"**{SACRED_STANDING_PENALTY}** standing. Use `/vitals action:sacred` now."
        )
    left = HALF_MOON_DAYS - elapsed
    if left <= 1:
        return (
            "**Sacred visit:** **due this sunrise**; use `/vitals action:sacred` "
            f"or lose **{SACRED_STANDING_PENALTY}** standing on rollover."
        )
    return (
        f"**Sacred visit:** due in **{left}** sunrise(s); `/vitals action:sacred` "
        f"every half-moon or **{SACRED_STANDING_PENALTY}** standing."
    )


def apply_sacred_visit_reminders(conn: sqlite3.Connection, day: int) -> list[dict]:
    """Medics who missed a half-moon sacred visit lose standing."""
    rows = conn.execute(
        """
        SELECT id, wolf_name, last_sacred_day, pack_id
        FROM users
        WHERE wolf_role = 'medic' AND condition NOT IN ('dead', 'dying')
        """
    ).fetchall()
    notes: list[dict] = []
    for row in rows:
        if not is_full_medic(row):
            continue
        last = int(row["last_sacred_day"] if "last_sacred_day" in row.keys() else 0)
        if last and day - last < HALF_MOON_DAYS:
            continue
        if not last and day < HALF_MOON_DAYS:
            continue
        if not row["pack_id"]:
            notes.append(
                {
                    "wolf_name": row["wolf_name"],
                    "text": (
                        "missed the sacred place: no den standing to lose, "
                        "but the ancestors are displeased."
                    ),
                }
            )
            continue
        import database as db

        kick = db.adjust_wolf_standing_by_id(row["id"], SACRED_STANDING_PENALTY, triggered_day=day)
        extra = ""
        if kick == "kicked":
            extra = " Cast out of the pack."
        elif kick == "broken_rite":
            extra = " Rite of the Broken Canine triggered."
        notes.append(
            {
                "wolf_name": row["wolf_name"],
                "text": (
                    f"missed the sacred place ({SACRED_STANDING_PENALTY} standing): "
                    f"visit with `/vitals action:sacred` before the next half-moon.{extra}"
                ),
            }
        )
    return notes


def record_sacred_visit(user, *, day: int) -> tuple[bool, str]:
    if not is_full_medic(user):
        return False, "Only full **Medics** must keep the half-moon sacred visits."
    import database as db

    db.update_user_by_id(user["id"], last_sacred_day=day)
    ancestor = pick_sacred_ancestor_word(user)
    return True, (
        f"**{user['wolf_name']}** walks the spirit path: ancestors heard at the sacred place.\n\n"
        f"_The ancestors say:_ \"{ancestor}\"\n\n"
        f"Next visit due within **{HALF_MOON_DAYS}** sunrises."
    )
