"""Den news summaries for admin rollover embeds."""



from __future__ import annotations



import database as db

from config import DAILY_REWARD

from engine.aging import check_age_milestones, stage_for_age, stage_label

from engine.family import GESTATION_DAYS





def treasury_warning_line(pack, member_count: int) -> str | None:

    treasury = int(pack["treasury"]) if pack["treasury"] is not None else 0

    need = max(DAILY_REWARD * max(1, member_count), DAILY_REWARD * 3)

    if treasury < need:

        return (

            f"**{pack['name']}** treasury **{treasury}** 🦴; low for daily stipends "

            f"(~**{need}** 🦴 needed)."

        )

    return None





def collect_births_ready(day_number: int) -> list[str]:

    lines: list[str] = []

    with db.get_db() as conn:

        rows = conn.execute("SELECT * FROM users WHERE is_pregnant = 1").fetchall()

    for row in rows:

        elapsed = max(0, day_number - row["pregnancy_start_day"])

        if elapsed < GESTATION_DAYS:

            continue

        mate = db.get_mate_wolf(row)

        mate_name = mate["wolf_name"] if mate else "unknown"

        lines.append(f"**{row['wolf_name']}**; ready for `/birth` (mate: **{mate_name}**)")

    return lines





def collect_mate_pregnancy_alerts(day_number: int) -> list[str]:

    lines: list[str] = []

    with db.get_db() as conn:

        rows = conn.execute("SELECT * FROM users WHERE is_pregnant = 1").fetchall()

    for row in rows:

        elapsed = max(0, day_number - row["pregnancy_start_day"])

        remaining = GESTATION_DAYS - elapsed

        if remaining > 7 or remaining < 0:

            continue

        mate = db.get_mate_wolf(row)

        if not mate:

            continue

        if remaining == 0:

            lines.append(f"**{mate['wolf_name']}**; mate **{row['wolf_name']}** can `/birth` now")

        else:

            lines.append(

                f"**{mate['wolf_name']}**; mate **{row['wolf_name']}** births in **{remaining}** day(s)"

            )

    return lines





def collect_treasury_warnings() -> list[str]:

    lines: list[str] = []

    with db.get_db() as conn:

        packs = conn.execute("SELECT * FROM packs").fetchall()

        for pack in packs:

            member_count = conn.execute(

                "SELECT COUNT(*) AS c FROM users WHERE pack_id = ?",

                (pack["id"],),

            ).fetchone()["c"]

            warn = treasury_warning_line(pack, member_count)

            if warn:

                lines.append(warn)

    return lines





def format_age_milestone_line(

    wolf_name: str, old_age: int, new_age: int, old_role: str, new_role: str

) -> str:

    old_stage = stage_label(stage_for_age(old_age))

    new_stage = stage_label(stage_for_age(new_age))

    notes = check_age_milestones(old_age, new_age, old_role)

    base = f"**{wolf_name}**; {old_age} → **{new_age}** moons ({old_stage} → {new_stage})"

    if new_role != old_role:

        base += f" · role **{new_role}**"

    if notes:

        snippet = notes[0].replace("**", "")[:90]

        base += f" · _{snippet}_"

    return base





def birthday_lines(age_milestones: list[dict]) -> list[str]:
    """Celebrate wolves who cross a full year (multiple of 12 moons) this rollover."""
    out: list[str] = []
    for m in age_milestones:
        old_age = int(m["old_age"])
        new_age = int(m["new_age"])
        years = [y for y in range(old_age + 1, new_age + 1) if y % 12 == 0]
        if not years:
            continue
        year = years[-1] // 12
        out.append(
            f"🎂 **{m['wolf_name']}** turns **{year} year{'s' if year != 1 else ''}** old!"
        )
    return out


def collect_den_news(day_number: int, age_milestones: list[dict]) -> dict[str, list[str]]:

    from engine.pack_events import collect_pack_event_lines



    return {

        "birthdays": birthday_lines(age_milestones),

        "age_ups": [

            format_age_milestone_line(

                m["wolf_name"],

                m["old_age"],

                m["new_age"],

                m["old_role"],

                m["new_role"],

            )

            for m in age_milestones

        ],

        "births_ready": collect_births_ready(day_number),

        "pregnancy_alerts": collect_mate_pregnancy_alerts(day_number),

        "treasury_warnings": collect_treasury_warnings(),

        "pack_events": collect_pack_event_lines(day_number),

    }

