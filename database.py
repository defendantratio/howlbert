import random
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import (
    DB_PATH,
    DEFAULT_SHOP_ITEMS,
    DEFAULT_TERRITORIES,
    GREAT_PACKS,
    LONER_KEY,
    MOONS_PER_ROLLOVER,
    ROGUE_KEY,
    SEASONS,
    STATIC_QUESTS,
    ROLE_QUESTS,
    WAR_DURATION_DAYS,
    WEATHER_TYPES,
    NEUTRAL_CLAIM_SCORE,
)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_val(row, key: str, default=None):
    """Read a column from sqlite3.Row (no .get()) or a mapping."""
    if not row:
        return default
    if hasattr(row, "keys"):
        if key in row.keys():
            val = row[key]
            return default if val is None else val
        return default
    if hasattr(row, "get"):
        return row.get(key, default)
    return default


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS packs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                alpha_id INTEGER,
                treasury INTEGER NOT NULL DEFAULT 0,
                tax_rate INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                discord_id INTEGER PRIMARY KEY,
                wolf_name TEXT NOT NULL,
                pack_id INTEGER,
                rank TEXT NOT NULL DEFAULT 'subordinate',
                strength INTEGER NOT NULL DEFAULT 10,
                speed INTEGER NOT NULL DEFAULT 10,
                stamina INTEGER NOT NULL DEFAULT 10,
                scent INTEGER NOT NULL DEFAULT 10,
                standing INTEGER NOT NULL DEFAULT 0,
                bones INTEGER NOT NULL DEFAULT 0,
                condition TEXT NOT NULL DEFAULT 'healthy',
                last_hunt_day INTEGER NOT NULL DEFAULT 0,
                last_daily_day INTEGER NOT NULL DEFAULT 0,
                last_hunt TEXT,
                last_daily TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (pack_id) REFERENCES packs(id)
            );

            CREATE TABLE IF NOT EXISTS world_state (
                guild_id INTEGER PRIMARY KEY,
                day_number INTEGER NOT NULL DEFAULT 1,
                season TEXT NOT NULL DEFAULT 'spring',
                weather TEXT NOT NULL DEFAULT 'clear',
                time_of_day TEXT NOT NULL DEFAULT 'dawn',
                last_rollover TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                price INTEGER NOT NULL,
                sell_price INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS inventory (
                discord_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (discord_id, item_id),
                FOREIGN KEY (item_id) REFERENCES items(id)
            );

            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                objective_type TEXT NOT NULL,
                objective_count INTEGER NOT NULL DEFAULT 1,
                reward_bones INTEGER NOT NULL DEFAULT 0,
                standing_reward INTEGER NOT NULL DEFAULT 0,
                quest_type TEXT NOT NULL DEFAULT 'static',
                difficulty TEXT NOT NULL DEFAULT 'easy'
            );

            CREATE TABLE IF NOT EXISTS user_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                quest_id INTEGER NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                assigned_day INTEGER NOT NULL DEFAULT 0,
                accepted_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (quest_id) REFERENCES quests(id)
            );

            CREATE TABLE IF NOT EXISTS territories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                name TEXT NOT NULL,
                owner_pack_id INTEGER,
                daily_bonus INTEGER NOT NULL DEFAULT 5,
                UNIQUE (guild_id, key),
                FOREIGN KEY (owner_pack_id) REFERENCES packs(id)
            );

            CREATE TABLE IF NOT EXISTS wars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                territory_id INTEGER NOT NULL,
                attacker_pack_id INTEGER NOT NULL,
                defender_pack_id INTEGER,
                start_day INTEGER NOT NULL,
                end_day INTEGER NOT NULL,
                attacker_score INTEGER NOT NULL DEFAULT 0,
                defender_score INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (territory_id) REFERENCES territories(id),
                FOREIGN KEY (attacker_pack_id) REFERENCES packs(id)
            );

            CREATE TABLE IF NOT EXISTS account_progress (
                discord_id INTEGER PRIMARY KEY,
                legacy_score INTEGER NOT NULL DEFAULT 0,
                prestige_tier INTEGER NOT NULL DEFAULT 0,
                total_quests INTEGER NOT NULL DEFAULT 0,
                total_hunts INTEGER NOT NULL DEFAULT 0,
                total_retirements INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS retired_wolves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                wolf_name TEXT NOT NULL,
                great_pack TEXT,
                legacy_contribution INTEGER NOT NULL,
                retired_at TEXT NOT NULL
            );
            """
        )
        _migrate(conn)
        _seed_shop_items(conn)
        _retire_shop_items(conn)
        _seed_herb_items(conn)
        _seed_prey_items(conn)
        _seed_amusement_items(conn)
        _seed_quests(conn)
    _run_journal_backfill_once()
    _run_canonical_bonds_once()
    _run_canonical_mates_once()
    _run_pronoun_backfill_once()
    _run_herb_stacks_to_inventory_once()


def _run_canonical_bonds_once() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        row = conn.execute(
            "SELECT value FROM app_meta WHERE key = 'canonical_bonds_v2'"
        ).fetchone()
        if row:
            return
    from engine.canonical_bonds import backfill_all_canonical_bonds

    added = backfill_all_canonical_bonds(refresh_notes=True)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO app_meta (key, value) VALUES ('canonical_bonds_v2', ?)",
            (str(added),),
        )


def _run_canonical_mates_once() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        row = conn.execute(
            "SELECT value FROM app_meta WHERE key = 'canonical_mates_v1'"
        ).fetchone()
        if row:
            return
    from engine.canonical_bonds import backfill_canonical_mates

    linked = backfill_canonical_mates()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO app_meta (key, value) VALUES ('canonical_mates_v1', ?)",
            (str(linked),),
        )


def _run_pronoun_backfill_once() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        row = conn.execute(
            "SELECT value FROM app_meta WHERE key = 'pronoun_backfill_v3'"
        ).fetchone()
        if row:
            return
        users = conn.execute(
            "SELECT id, wolf_name, birth_sex, pronouns FROM users"
        ).fetchall()
    from engine.pronouns import canonical_pronouns_for_name, resolve_wolf_pronouns

    updated = 0
    for user in users:
        canon = canonical_pronouns_for_name(user["wolf_name"])
        if canon:
            resolved = canon
        else:
            resolved = resolve_wolf_pronouns(
                user["wolf_name"],
                birth_sex=user["birth_sex"],
                explicit=user["pronouns"],
            )
        if not resolved:
            continue
        current = (user["pronouns"] or "").strip() if user["pronouns"] else ""
        if current == resolved:
            continue
        if not canon and current:
            continue
        with get_db() as conn:
            conn.execute("UPDATE users SET pronouns = ? WHERE id = ?", (resolved, user["id"]))
        updated += 1
    with get_db() as conn:
        conn.execute(
            "INSERT INTO app_meta (key, value) VALUES ('pronoun_backfill_v3', ?)",
            (str(updated),),
        )


def _run_herb_stacks_to_inventory_once() -> None:
    """Move personal forage herb stacks into inventory; herb bag removed."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        row = conn.execute(
            "SELECT value FROM app_meta WHERE key = 'herb_stacks_to_inventory_v1'"
        ).fetchone()
        if row:
            return
        stacks = conn.execute("SELECT * FROM herb_stacks").fetchall()
    if not stacks:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO app_meta (key, value) VALUES ('herb_stacks_to_inventory_v1', '0')"
            )
        return
    from herbs import herb_inventory_key

    moved = 0
    for stack in stacks:
        user = get_user_by_id(int(stack["wolf_id"]))
        if not user:
            continue
        item_key = herb_inventory_key(stack["herb_key"])
        item = get_item_by_key(item_key)
        if not item:
            continue
        grant_item(user["discord_id"], item["id"], quantity=1)
        moved += 1
    with get_db() as conn:
        conn.execute("DELETE FROM herb_stacks")
        conn.execute(
            "INSERT INTO app_meta (key, value) VALUES ('herb_stacks_to_inventory_v1', ?)",
            (str(moved),),
        )


def _run_journal_backfill_once() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        row = conn.execute(
            "SELECT value FROM app_meta WHERE key = 'wolf_journal_backfill_v1'"
        ).fetchone()
        if row:
            return
    from engine.journal_backfill import backfill_all_wolf_journals

    inserted = backfill_all_wolf_journals()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO app_meta (key, value) VALUES ('wolf_journal_backfill_v1', ?)",
            (str(inserted),),
        )


def _migrate(conn: sqlite3.Connection) -> None:
    user_cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "prey_points" in user_cols and "bones" not in user_cols:
        conn.execute("ALTER TABLE users RENAME COLUMN prey_points TO bones")
        user_cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "last_hunt_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_hunt_day INTEGER NOT NULL DEFAULT 0")
    if "last_daily_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_daily_day INTEGER NOT NULL DEFAULT 0")
    if "last_scavenge_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_scavenge_day INTEGER NOT NULL DEFAULT 0")
    if "last_track_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_track_day INTEGER NOT NULL DEFAULT 0")
    if "last_fishing_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_fishing_day INTEGER NOT NULL DEFAULT 0")
    if "great_pack" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN great_pack TEXT")
    if "deposit_progress" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN deposit_progress INTEGER NOT NULL DEFAULT 0")
    if "last_patrol_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_patrol_day INTEGER NOT NULL DEFAULT 0")
    if "last_scout_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_scout_day INTEGER NOT NULL DEFAULT 0")
    if "wolf_role" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN wolf_role TEXT NOT NULL DEFAULT 'hunter'")
    if "attr_str" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN attr_str INTEGER NOT NULL DEFAULT 6")
        conn.execute("ALTER TABLE users ADD COLUMN attr_dex INTEGER NOT NULL DEFAULT 5")
        conn.execute("ALTER TABLE users ADD COLUMN attr_con INTEGER NOT NULL DEFAULT 4")
        conn.execute("ALTER TABLE users ADD COLUMN attr_int INTEGER NOT NULL DEFAULT 1")
        conn.execute("ALTER TABLE users ADD COLUMN attr_cha INTEGER NOT NULL DEFAULT 1")
        conn.execute("ALTER TABLE users ADD COLUMN attr_wis INTEGER NOT NULL DEFAULT 1")
        conn.execute("ALTER TABLE users ADD COLUMN skill_proficiencies TEXT NOT NULL DEFAULT '[]'")
        conn.execute("ALTER TABLE users ADD COLUMN hp INTEGER NOT NULL DEFAULT 11")
        conn.execute("ALTER TABLE users ADD COLUMN max_hp INTEGER NOT NULL DEFAULT 11")
        conn.execute("ALTER TABLE users ADD COLUMN exhaustion INTEGER NOT NULL DEFAULT 0")
        _backfill_rpg_stats(conn)
    if "active_injuries" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN active_injuries TEXT NOT NULL DEFAULT '[]'")
    if "disease" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN disease TEXT")
    if "last_forage_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_forage_day INTEGER NOT NULL DEFAULT 0")
    if "last_verge_forage_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_verge_forage_day INTEGER NOT NULL DEFAULT 0")
    if "last_rest_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_rest_day INTEGER NOT NULL DEFAULT 0")
    if "herb_heals_today" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN herb_heals_today INTEGER NOT NULL DEFAULT 0")
    if "herb_treats_today" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN herb_treats_today INTEGER NOT NULL DEFAULT 0")
    if "gender" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN gender TEXT")
    if "birth_sex" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN birth_sex TEXT")
        if "gender" in user_cols:
            conn.execute("UPDATE users SET birth_sex = gender WHERE gender IS NOT NULL")
    if "sexuality" not in user_cols:
        conn.execute(
            "ALTER TABLE users ADD COLUMN sexuality TEXT NOT NULL DEFAULT 'bisexual'"
        )
    if "is_pregnant" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_pregnant INTEGER NOT NULL DEFAULT 0")
    if "pregnancy_start_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN pregnancy_start_day INTEGER NOT NULL DEFAULT 0")
    if "mate_discord_id" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN mate_discord_id INTEGER")
    if "death_save_round" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN death_save_round INTEGER NOT NULL DEFAULT 0")
    if "death_save_fails" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN death_save_fails INTEGER NOT NULL DEFAULT 0")
    if "death_save_successes" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN death_save_successes INTEGER NOT NULL DEFAULT 0")
    if "cause_of_death" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN cause_of_death TEXT")
    if "death_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN death_day INTEGER")
    if "receptive_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN receptive_day INTEGER NOT NULL DEFAULT 0")
    if "bonus_role_feature" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN bonus_role_feature TEXT")
    if "character_traits" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN character_traits TEXT")
    if "maw_belief" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN maw_belief TEXT")
    if "character_lore" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN character_lore TEXT")
    if "avatar_url" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
    if "pronouns" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN pronouns TEXT")
    if "ref_image_url" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN ref_image_url TEXT")
    if "bio" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN bio TEXT")
    if "birthday" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN birthday TEXT")
    if "proxy_prefix" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN proxy_prefix TEXT")
    if "proxy_suffix" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN proxy_suffix TEXT")
    if "bonded_mate_id" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN bonded_mate_id INTEGER")
    if "last_adopt_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_adopt_day INTEGER NOT NULL DEFAULT 0")
    if "last_den_charm_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_den_charm_day INTEGER NOT NULL DEFAULT 0")
    if "last_hunt_yield" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_hunt_yield INTEGER NOT NULL DEFAULT 0")
    if "last_prey_pile_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_prey_pile_day INTEGER NOT NULL DEFAULT 0")
    if "last_prey_label" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_prey_label TEXT")
    if "last_role_event_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_role_event_day INTEGER NOT NULL DEFAULT 0")
    if "last_prophecy_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_prophecy_day INTEGER NOT NULL DEFAULT 0")
    if "last_role_reroll_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_role_reroll_day INTEGER NOT NULL DEFAULT 0")
    if "commanding_howl_buff" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN commanding_howl_buff INTEGER NOT NULL DEFAULT 0")
    if "last_blood_oath_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN last_blood_oath_day INTEGER NOT NULL DEFAULT 0")
    if "scout_hidden_day" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN scout_hidden_day INTEGER NOT NULL DEFAULT 0")

    quest_cols = {row[1] for row in conn.execute("PRAGMA table_info(quests)")}
    if "required_role" not in quest_cols:
        conn.execute("ALTER TABLE quests ADD COLUMN required_role TEXT")
    if "required_pack" not in quest_cols:
        conn.execute("ALTER TABLE quests ADD COLUMN required_pack TEXT")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prey_piles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER,
            hunter_wolf_id INTEGER NOT NULL,
            hunter_name TEXT NOT NULL,
            prey_label TEXT NOT NULL,
            prey_bones INTEGER NOT NULL DEFAULT 0,
            day_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prey_pile_responses (
            pile_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            choice TEXT NOT NULL,
            responded_at TEXT NOT NULL,
            PRIMARY KEY (pile_id, wolf_id),
            FOREIGN KEY (pile_id) REFERENCES prey_piles(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prey_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            prey_key TEXT NOT NULL,
            uses_left INTEGER NOT NULL,
            bone_value INTEGER NOT NULL,
            acquired_day INTEGER NOT NULL,
            is_rotting INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS herb_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            herb_key TEXT NOT NULL,
            form TEXT NOT NULL DEFAULT 'fresh',
            acquired_day INTEGER NOT NULL,
            potency INTEGER NOT NULL DEFAULT 100,
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS herb_seeds (
            wolf_id INTEGER NOT NULL,
            herb_key TEXT NOT NULL,
            qty INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (wolf_id, herb_key),
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS herb_gardens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            herb_key TEXT NOT NULL,
            planted_day INTEGER NOT NULL,
            season_planted TEXT NOT NULL DEFAULT 'spring',
            last_tended_day INTEGER NOT NULL DEFAULT 0,
            last_eval_day INTEGER NOT NULL DEFAULT 0,
            health INTEGER NOT NULL DEFAULT 100,
            dead INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wolf_death_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            discord_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            guild_id INTEGER,
            cause TEXT NOT NULL,
            day INTEGER,
            logged_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS collab_hunts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER,
            leader_wolf_id INTEGER NOT NULL,
            pack_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            result_text TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS collab_hunt_members (
            hunt_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            discord_id INTEGER NOT NULL,
            joined_at TEXT NOT NULL DEFAULT (datetime('now')),
            hunt_role TEXT NOT NULL DEFAULT 'flank',
            rp_said INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (hunt_id, wolf_id),
            FOREIGN KEY (hunt_id) REFERENCES collab_hunts(id)
        )
        """
    )
    collab_cols = {row[1] for row in conn.execute("PRAGMA table_info(collab_hunts)")}
    if collab_cols and "result_text" not in collab_cols:
        conn.execute("ALTER TABLE collab_hunts ADD COLUMN result_text TEXT")
    member_cols = {row[1] for row in conn.execute("PRAGMA table_info(collab_hunt_members)")}
    if member_cols and "hunt_role" not in member_cols:
        conn.execute("ALTER TABLE collab_hunt_members ADD COLUMN hunt_role TEXT NOT NULL DEFAULT 'flank'")
    if member_cols and "rp_said" not in member_cols:
        conn.execute("ALTER TABLE collab_hunt_members ADD COLUMN rp_said INTEGER NOT NULL DEFAULT 0")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS collab_patrols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER,
            leader_wolf_id INTEGER NOT NULL,
            pack_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            result_text TEXT,
            patrol_kind TEXT NOT NULL DEFAULT 'survey',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS collab_patrol_members (
            patrol_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            discord_id INTEGER NOT NULL,
            joined_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (patrol_id, wolf_id),
            FOREIGN KEY (patrol_id) REFERENCES collab_patrols(id)
        )
        """
    )
    patrol_cols = {row[1] for row in conn.execute("PRAGMA table_info(collab_patrols)")}
    if patrol_cols and "result_text" not in patrol_cols:
        conn.execute("ALTER TABLE collab_patrols ADD COLUMN result_text TEXT")
    if patrol_cols and "patrol_kind" not in patrol_cols:
        conn.execute(
            "ALTER TABLE collab_patrols ADD COLUMN patrol_kind TEXT NOT NULL DEFAULT 'survey'"
        )

    pack_cols = {row[1] for row in conn.execute("PRAGMA table_info(packs)")}
    if "pack_unity" not in pack_cols:
        conn.execute("ALTER TABLE packs ADD COLUMN pack_unity INTEGER NOT NULL DEFAULT 5")
    if "tax_rate" not in pack_cols:
        conn.execute("ALTER TABLE packs ADD COLUMN tax_rate INTEGER NOT NULL DEFAULT 0")
    if "key" not in pack_cols:
        conn.execute("ALTER TABLE packs ADD COLUMN key TEXT")
    if "last_feedall_day" not in pack_cols:
        conn.execute(
            "ALTER TABLE packs ADD COLUMN last_feedall_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_drinkall_day" not in pack_cols:
        conn.execute(
            "ALTER TABLE packs ADD COLUMN last_drinkall_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_pack_event_day" not in pack_cols:
        conn.execute(
            "ALTER TABLE packs ADD COLUMN last_pack_event_day INTEGER NOT NULL DEFAULT 0"
        )
    if "season_stash_deposits" not in pack_cols:
        conn.execute(
            "ALTER TABLE packs ADD COLUMN season_stash_deposits INTEGER NOT NULL DEFAULT 0"
        )
    if "season_stash_goal_met" not in pack_cols:
        conn.execute(
            "ALTER TABLE packs ADD COLUMN season_stash_goal_met INTEGER NOT NULL DEFAULT 0"
        )
    if "season_goal_epoch" not in pack_cols:
        conn.execute(
            "ALTER TABLE packs ADD COLUMN season_goal_epoch INTEGER NOT NULL DEFAULT 0"
        )

    user_cols_needs = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "hunger_exhaustion_skip" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN hunger_exhaustion_skip INTEGER NOT NULL DEFAULT 0"
        )
    if "march_exhaustion_skip" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN march_exhaustion_skip INTEGER NOT NULL DEFAULT 0"
        )
    if "jaw_meal_shield" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN jaw_meal_shield INTEGER NOT NULL DEFAULT 0"
        )
    if "smoke_debuff" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN smoke_debuff INTEGER NOT NULL DEFAULT 0"
        )
    if "last_forager_gift_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_forager_gift_day INTEGER NOT NULL DEFAULT 0"
        )
    if "quarantined" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN quarantined INTEGER NOT NULL DEFAULT 0"
        )
    if "genetic_conditions" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN genetic_conditions TEXT NOT NULL DEFAULT '[]'"
        )
    if "disease_save_buff" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN disease_save_buff INTEGER NOT NULL DEFAULT 0"
        )
    if "cough_suppressed" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN cough_suppressed INTEGER NOT NULL DEFAULT 0"
        )
    if "milk_fever_due_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN milk_fever_due_day INTEGER NOT NULL DEFAULT 0"
        )
    if "disease_save_buff_days" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN disease_save_buff_days INTEGER NOT NULL DEFAULT 0"
        )
    if "herb_buffs" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN herb_buffs TEXT NOT NULL DEFAULT '{}'"
        )
    if "distressed" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN distressed INTEGER NOT NULL DEFAULT 0"
        )
    if "extra_pup_milk" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN extra_pup_milk INTEGER NOT NULL DEFAULT 0"
        )
    if "last_nurse_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_nurse_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_milk_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_milk_day INTEGER NOT NULL DEFAULT 0"
        )
    if "long_term_injuries" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN long_term_injuries TEXT NOT NULL DEFAULT '[]'"
        )
    if "frightened_fire" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN frightened_fire INTEGER NOT NULL DEFAULT 0"
        )
    if "last_fire_reroll_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_fire_reroll_day INTEGER NOT NULL DEFAULT 0"
        )
    if "omen_buff" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN omen_buff TEXT NOT NULL DEFAULT ''"
        )
    if "last_sacred_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_sacred_day INTEGER NOT NULL DEFAULT 0"
        )
    if "food_cache_meals" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN food_cache_meals INTEGER NOT NULL DEFAULT 0"
        )
    if "last_surgery_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_surgery_day INTEGER NOT NULL DEFAULT 0"
        )
    if "bone_rest_until" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN bone_rest_until INTEGER NOT NULL DEFAULT 0"
        )
    if "last_observe_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_observe_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_shadow_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_shadow_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_train_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_train_day INTEGER NOT NULL DEFAULT 0"
        )
    if "trained_attr_total" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN trained_attr_total INTEGER NOT NULL DEFAULT 0"
        )
    if "last_medic_rounds_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_medic_rounds_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_healer_tribute_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_healer_tribute_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_swim_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_swim_day INTEGER NOT NULL DEFAULT 0"
        )
    if "naming_ceremony_day" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN naming_ceremony_day INTEGER NOT NULL DEFAULT 0"
        )
    if "skill_ranks" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN skill_ranks TEXT NOT NULL DEFAULT '{}'"
        )
    if "trait_failure_days" not in user_cols_needs:
        conn.execute(
            "ALTER TABLE users ADD COLUMN trait_failure_days TEXT NOT NULL DEFAULT '{}'"
        )
    if "size_class" not in user_cols_needs:
        conn.execute("ALTER TABLE users ADD COLUMN size_class TEXT NOT NULL DEFAULT ''")
    conn.execute("UPDATE users SET disease = 'redscratch' WHERE disease = 'den_fever'")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS account_progress (
            discord_id INTEGER PRIMARY KEY,
            legacy_score INTEGER NOT NULL DEFAULT 0,
            prestige_tier INTEGER NOT NULL DEFAULT 0,
            total_quests INTEGER NOT NULL DEFAULT 0,
            total_hunts INTEGER NOT NULL DEFAULT 0,
            total_retirements INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    acct_cols_early = {row[1] for row in conn.execute("PRAGMA table_info(account_progress)")}
    if acct_cols_early and "xp" not in acct_cols_early:
        conn.execute("ALTER TABLE account_progress ADD COLUMN xp INTEGER NOT NULL DEFAULT 0")

    _migrate_multi_wolf(conn)

    _seed_great_packs(conn)
    _reconcile_great_pack_alphas(conn)
    _migrate_user_pack_affiliation(conn)
    _backfill_starting_herbs(conn)
    _strip_canonical_lore_genetics(conn)

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retired_wolves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            great_pack TEXT,
            legacy_contribution INTEGER NOT NULL,
            retired_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS combat_encounters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'recruiting',
            round INTEGER NOT NULL DEFAULT 0,
            turn_order TEXT NOT NULL DEFAULT '[]',
            current_turn INTEGER NOT NULL DEFAULT 0,
            created_by INTEGER,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS combat_fighters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encounter_id INTEGER NOT NULL,
            discord_id INTEGER,
            npc_name TEXT,
            initiative INTEGER NOT NULL DEFAULT 0,
            hp INTEGER NOT NULL,
            max_hp INTEGER NOT NULL,
            FOREIGN KEY (encounter_id) REFERENCES combat_encounters(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_relations (
            guild_id INTEGER NOT NULL,
            pack_a_id INTEGER NOT NULL,
            pack_b_id INTEGER NOT NULL,
            standing INTEGER NOT NULL DEFAULT 5,
            PRIMARY KEY (guild_id, pack_a_id, pack_b_id),
            FOREIGN KEY (pack_a_id) REFERENCES packs(id),
            FOREIGN KEY (pack_b_id) REFERENCES packs(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_raid_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            victim_pack_id INTEGER NOT NULL,
            suspect_pack_id INTEGER NOT NULL,
            stolen_amount INTEGER NOT NULL DEFAULT 0,
            recovered_amount INTEGER NOT NULL DEFAULT 0,
            raid_day INTEGER NOT NULL,
            expires_day INTEGER NOT NULL,
            caught INTEGER NOT NULL DEFAULT 0,
            last_audit_day INTEGER NOT NULL DEFAULT 0,
            accused_pack_id INTEGER,
            accuse_day INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pack_raid_alerts_victim
        ON pack_raid_alerts (guild_id, victim_pack_id, expires_day)
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bond_relation_cooldowns (
            guild_id INTEGER NOT NULL,
            pack_a_id INTEGER NOT NULL,
            pack_b_id INTEGER NOT NULL,
            last_penalty_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, pack_a_id, pack_b_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cross_pack_scandals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            wolf_a_id INTEGER NOT NULL,
            wolf_b_id INTEGER NOT NULL,
            pack_a_id INTEGER NOT NULL,
            pack_b_id INTEGER NOT NULL,
            caught_day INTEGER NOT NULL,
            UNIQUE (guild_id, wolf_a_id, wolf_b_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scent_marks (
            guild_id INTEGER NOT NULL,
            territory_key TEXT NOT NULL,
            pack_key TEXT NOT NULL,
            marker_wolf_id INTEGER NOT NULL,
            marked_day INTEGER NOT NULL,
            PRIMARY KEY (guild_id, territory_key, pack_key),
            FOREIGN KEY (marker_wolf_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_diplomacy_log (
            guild_id INTEGER NOT NULL,
            pack_a_id INTEGER NOT NULL,
            pack_b_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            action_day INTEGER NOT NULL,
            PRIMARY KEY (guild_id, pack_a_id, pack_b_id, action, action_day),
            FOREIGN KEY (pack_a_id) REFERENCES packs(id),
            FOREIGN KEY (pack_b_id) REFERENCES packs(id)
        )
        """
    )
    acct_cols = {row[1] for row in conn.execute("PRAGMA table_info(account_progress)")}
    if acct_cols and "xp" not in acct_cols:
        conn.execute("ALTER TABLE account_progress ADD COLUMN xp INTEGER NOT NULL DEFAULT 0")

    user_cols_late = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "last_work_day" not in user_cols_late:
        conn.execute("ALTER TABLE users ADD COLUMN last_work_day INTEGER NOT NULL DEFAULT 0")
    if "last_crime_day" not in user_cols_late:
        conn.execute("ALTER TABLE users ADD COLUMN last_crime_day INTEGER NOT NULL DEFAULT 0")
    if "last_duplicate_trade_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_duplicate_trade_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_cat_receive_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_cat_receive_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_wolf_receive_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_wolf_receive_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_cat_food_trade_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_cat_food_trade_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_firepaw_reward_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_firepaw_reward_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_soot_reward_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_soot_reward_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_rivershroud_reward_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_rivershroud_reward_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_finnpelt_reward_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_finnpelt_reward_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_plot_witness_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_plot_witness_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_plot_healer_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_plot_healer_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_rest_omen_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_rest_omen_day INTEGER NOT NULL DEFAULT 0"
        )
    if "age_months" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN age_months INTEGER NOT NULL DEFAULT 24"
        )
        conn.execute(
            """
            UPDATE users SET age_months = CASE wolf_role
                WHEN 'pup' THEN 3
                WHEN 'juvenile' THEN 12
                ELSE 24
            END
            """
        )
    if "last_ageup_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_ageup_day INTEGER NOT NULL DEFAULT 0"
        )
    if "birth_lunar_phase" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN birth_lunar_phase TEXT NOT NULL DEFAULT ''"
        )
    if "last_lunar_aged_lunation" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_lunar_aged_lunation INTEGER NOT NULL DEFAULT -1"
        )

    user_cols_lunar = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if user_cols_lunar and "birth_lunar_phase" in user_cols_lunar:
        from config import ROLLOVER_TIMEZONE
        from engine.lunar import assign_birth_lunar_phase, rollover_now

        empty = conn.execute(
            "SELECT id, created_at FROM users WHERE birth_lunar_phase = '' OR birth_lunar_phase IS NULL"
        ).fetchall()
        for row in empty:
            if row["created_at"]:
                try:
                    born_at = datetime.fromisoformat(row["created_at"])
                except ValueError:
                    born_at = rollover_now(ROLLOVER_TIMEZONE)
            else:
                born_at = rollover_now(ROLLOVER_TIMEZONE)
            phase = assign_birth_lunar_phase(born_at)
            conn.execute(
                "UPDATE users SET birth_lunar_phase = ? WHERE id = ?",
                (phase, row["id"]),
            )

    cf_cols_late = {row[1] for row in conn.execute("PRAGMA table_info(combat_fighters)")}
    if cf_cols_late and "npc_template" not in cf_cols_late:
        conn.execute("ALTER TABLE combat_fighters ADD COLUMN npc_template TEXT")
    if cf_cols_late and "combat_flags" not in cf_cols_late:
        conn.execute(
            "ALTER TABLE combat_fighters ADD COLUMN combat_flags TEXT NOT NULL DEFAULT '{}'"
        )

    user_cols_inj = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if user_cols_inj and "injury_since" not in user_cols_inj:
        conn.execute(
            "ALTER TABLE users ADD COLUMN injury_since TEXT NOT NULL DEFAULT '{}'"
        )

    enc_cols_late = {row[1] for row in conn.execute("PRAGMA table_info(combat_encounters)")}
    if enc_cols_late and "is_hunt_prey" not in enc_cols_late:
        conn.execute(
            "ALTER TABLE combat_encounters ADD COLUMN is_hunt_prey INTEGER NOT NULL DEFAULT 0"
        )
    if enc_cols_late and "hunter_discord_id" not in enc_cols_late:
        conn.execute("ALTER TABLE combat_encounters ADD COLUMN hunter_discord_id INTEGER")
    if enc_cols_late and "hunter_wolf_id" not in enc_cols_late:
        conn.execute("ALTER TABLE combat_encounters ADD COLUMN hunter_wolf_id INTEGER")
    if enc_cols_late and "hunt_prey_rewarded" not in enc_cols_late:
        conn.execute(
            "ALTER TABLE combat_encounters ADD COLUMN hunt_prey_rewarded INTEGER NOT NULL DEFAULT 0"
        )
    if enc_cols_late and "ambush_activity" not in enc_cols_late:
        conn.execute(
            "ALTER TABLE combat_encounters ADD COLUMN ambush_activity TEXT NOT NULL DEFAULT ''"
        )
    if enc_cols_late and "ambush_finalized" not in enc_cols_late:
        conn.execute(
            "ALTER TABLE combat_encounters ADD COLUMN ambush_finalized INTEGER NOT NULL DEFAULT 0"
        )
    if enc_cols_late and "is_border_fight" not in enc_cols_late:
        conn.execute(
            "ALTER TABLE combat_encounters ADD COLUMN is_border_fight INTEGER NOT NULL DEFAULT 0"
        )
    if enc_cols_late and "border_fight_rewarded" not in enc_cols_late:
        conn.execute(
            "ALTER TABLE combat_encounters ADD COLUMN border_fight_rewarded INTEGER NOT NULL DEFAULT 0"
        )
    if enc_cols_late and "border_cat_clan" not in enc_cols_late:
        conn.execute(
            "ALTER TABLE combat_encounters ADD COLUMN border_cat_clan TEXT NOT NULL DEFAULT ''"
        )
    if enc_cols_late and "border_pact_violation" not in enc_cols_late:
        conn.execute(
            "ALTER TABLE combat_encounters ADD COLUMN border_pact_violation INTEGER NOT NULL DEFAULT 0"
        )
    if enc_cols_late and "collab_hunt_id" not in enc_cols_late:
        conn.execute("ALTER TABLE combat_encounters ADD COLUMN collab_hunt_id INTEGER")
    if enc_cols_late and "collab_patrol_id" not in enc_cols_late:
        conn.execute("ALTER TABLE combat_encounters ADD COLUMN collab_patrol_id INTEGER")

    pack_cols_late = {row[1] for row in conn.execute("PRAGMA table_info(packs)")}
    if pack_cols_late and "last_cat_pact_gift_day" not in pack_cols_late:
        conn.execute(
            "ALTER TABLE packs ADD COLUMN last_cat_pact_gift_day INTEGER NOT NULL DEFAULT 0"
        )
    if pack_cols_late and "last_garden_tend_day" not in pack_cols_late:
        conn.execute(
            "ALTER TABLE packs ADD COLUMN last_garden_tend_day INTEGER NOT NULL DEFAULT 0"
        )

    garden_cols = {row[1] for row in conn.execute("PRAGMA table_info(herb_gardens)")}
    if garden_cols and "pack_id" not in garden_cols:
        conn.execute("ALTER TABLE herb_gardens ADD COLUMN pack_id INTEGER")
        conn.execute(
            """
            UPDATE herb_gardens
            SET pack_id = (
                SELECT pack_id FROM users WHERE users.id = herb_gardens.wolf_id
            )
            WHERE pack_id IS NULL
            """
        )
        conn.execute(
            """
            UPDATE herb_gardens
            SET last_tended_day = planted_day - 1
            WHERE last_tended_day = planted_day AND dead = 0
            """
        )

    world_cols = {row[1] for row in conn.execute("PRAGMA table_info(world_state)")}
    if world_cols and "plot_phase" not in world_cols:
        conn.execute(
            "ALTER TABLE world_state ADD COLUMN plot_phase INTEGER NOT NULL DEFAULT 0"
        )
    if world_cols and "last_den_news_dm_day" not in world_cols:
        conn.execute(
            "ALTER TABLE world_state ADD COLUMN last_den_news_dm_day INTEGER NOT NULL DEFAULT 0"
        )
    if world_cols and "season_override" not in world_cols:
        conn.execute(
            "ALTER TABLE world_state ADD COLUMN season_override TEXT"
        )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS combat_target_picks (
            discord_id INTEGER NOT NULL,
            encounter_id INTEGER NOT NULL,
            target_fighter_id INTEGER NOT NULL,
            PRIMARY KEY (discord_id, encounter_id),
            FOREIGN KEY (encounter_id) REFERENCES combat_encounters(id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_discord_id INTEGER NOT NULL,
            to_discord_id INTEGER NOT NULL,
            from_item_id INTEGER,
            from_item_qty INTEGER NOT NULL DEFAULT 0,
            from_bones INTEGER NOT NULL DEFAULT 0,
            to_item_id INTEGER,
            to_item_qty INTEGER NOT NULL DEFAULT 0,
            to_bones INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            message_id INTEGER
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_howls (
            pack_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            howl_day INTEGER NOT NULL,
            discord_id INTEGER NOT NULL,
            PRIMARY KEY (pack_id, guild_id, howl_day, discord_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            pack_id INTEGER NOT NULL,
            signaler_id INTEGER NOT NULL,
            signal_key TEXT NOT NULL,
            target_id INTEGER,
            day INTEGER NOT NULL,
            responders TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rp_scenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            thread_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            topic TEXT,
            owner_discord_id INTEGER NOT NULL,
            day INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rp_scene_members (
            scene_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            discord_id INTEGER NOT NULL,
            joined_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (scene_id, wolf_id)
        )
        """
    )

    user_cols_late = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "last_sign_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_sign_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_sign_read_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_sign_read_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_howl_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_howl_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_sniff_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_sniff_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_mark_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_mark_day INTEGER NOT NULL DEFAULT 0"
        )
    if "sniff_bonus_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN sniff_bonus_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_explore_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_explore_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_play_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_play_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_socialize_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_socialize_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_raccoon_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_raccoon_day INTEGER NOT NULL DEFAULT 0"
        )
    if "raccoon_sells_today" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN raccoon_sells_today INTEGER NOT NULL DEFAULT 0"
        )
    if "mood" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN mood INTEGER NOT NULL DEFAULT 75"
        )
    if "last_rescout_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_rescout_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_playall_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_playall_day INTEGER NOT NULL DEFAULT 0"
        )
    if "rescout_uses_today" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN rescout_uses_today INTEGER NOT NULL DEFAULT 0"
        )
    if "last_survey_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_survey_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_trail_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_trail_day INTEGER NOT NULL DEFAULT 0"
        )
    if "hunger" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN hunger INTEGER NOT NULL DEFAULT 80"
        )
    if "thirst" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN thirst INTEGER NOT NULL DEFAULT 80"
        )
    if "remnants" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN remnants INTEGER NOT NULL DEFAULT 0"
        )
    if "last_groom_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_groom_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_drink_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_drink_day INTEGER NOT NULL DEFAULT 0"
        )
    if "drinks_today" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN drinks_today INTEGER NOT NULL DEFAULT 0"
        )
    if "last_drink_at" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_drink_at TEXT NOT NULL DEFAULT ''"
        )
    if "last_wild_encounter_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_wild_encounter_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_wild_encounter_at" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_wild_encounter_at TEXT NOT NULL DEFAULT ''"
        )
    if "hunt_uses_today" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN hunt_uses_today INTEGER NOT NULL DEFAULT 0"
        )
    if "last_hunt_uses_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_hunt_uses_day INTEGER NOT NULL DEFAULT 0"
        )
    if "raccoon_buys_today" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN raccoon_buys_today INTEGER NOT NULL DEFAULT 0"
        )
    if "last_raccoon_offer_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_raccoon_offer_day INTEGER NOT NULL DEFAULT 0"
        )
    if "bio_parent_1_id" not in user_cols_late:
        conn.execute("ALTER TABLE users ADD COLUMN bio_parent_1_id INTEGER")
    if "bio_parent_2_id" not in user_cols_late:
        conn.execute("ALTER TABLE users ADD COLUMN bio_parent_2_id INTEGER")
    if "adopt_parent_1_id" not in user_cols_late:
        conn.execute("ALTER TABLE users ADD COLUMN adopt_parent_1_id INTEGER")
    if "adopt_parent_2_id" not in user_cols_late:
        conn.execute("ALTER TABLE users ADD COLUMN adopt_parent_2_id INTEGER")
    if "is_born_pup" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN is_born_pup INTEGER NOT NULL DEFAULT 0"
        )
    if "has_blooding" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN has_blooding INTEGER NOT NULL DEFAULT 0"
        )
    if "last_court_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_court_day INTEGER NOT NULL DEFAULT 0"
        )
    if "ic_location" not in user_cols_late:
        conn.execute("ALTER TABLE users ADD COLUMN ic_location TEXT")
    if "dormant" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN dormant INTEGER NOT NULL DEFAULT 0"
        )
    if "last_weep_day" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_weep_day INTEGER NOT NULL DEFAULT 0"
        )
    if "last_freeze_at" not in user_cols_late:
        conn.execute(
            "ALTER TABLE users ADD COLUMN last_freeze_at TEXT NOT NULL DEFAULT ''"
        )

    scene_cols = {row[1] for row in conn.execute("PRAGMA table_info(rp_scenes)")}
    if "roster_message_id" not in scene_cols:
        conn.execute("ALTER TABLE rp_scenes ADD COLUMN roster_message_id INTEGER")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wolf_journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            event_key TEXT NOT NULL,
            summary TEXT NOT NULL,
            day INTEGER,
            guild_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_wolf_journal_wolf
        ON wolf_journal_entries (wolf_id, id DESC)
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS server_npcs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            avatar_url TEXT,
            bio TEXT,
            proxy_prefix TEXT,
            proxy_suffix TEXT,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(guild_id, name)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_adoptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER,
            message_id INTEGER,
            adopter_1_wolf_id INTEGER NOT NULL,
            adopter_2_wolf_id INTEGER NOT NULL,
            youth_wolf_id INTEGER NOT NULL,
            youth_owner_discord_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS court_history (
            courter_wolf_id INTEGER NOT NULL,
            target_wolf_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            PRIMARY KEY (courter_wolf_id, target_wolf_id, day_number)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wolf_bonds (
            wolf_a_id INTEGER NOT NULL,
            wolf_b_id INTEGER NOT NULL,
            bond_type TEXT NOT NULL,
            strength INTEGER NOT NULL DEFAULT 40,
            note TEXT NOT NULL DEFAULT '',
            created_day INTEGER NOT NULL DEFAULT 0,
            updated_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (wolf_a_id, wolf_b_id, bond_type),
            CHECK (wolf_a_id < wolf_b_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sign_partner_streaks (
            wolf_a_id INTEGER NOT NULL,
            wolf_b_id INTEGER NOT NULL,
            last_at TEXT NOT NULL,
            streak INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (wolf_a_id, wolf_b_id),
            CHECK (wolf_a_id < wolf_b_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS npc_sign_streaks (
            npc_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            last_at TEXT NOT NULL,
            streak INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (npc_id, wolf_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wolf_families (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL COLLATE NOCASE UNIQUE,
            founder_wolf_id INTEGER NOT NULL,
            created_day INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wolf_family_members (
            family_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            joined_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (family_id, wolf_id),
            FOREIGN KEY (family_id) REFERENCES wolf_families(id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_cat_pacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            pack_id INTEGER NOT NULL,
            clan_name TEXT NOT NULL COLLATE NOCASE,
            pact_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            trust INTEGER NOT NULL DEFAULT 50,
            tribute_paid INTEGER NOT NULL DEFAULT 0,
            terms_note TEXT NOT NULL DEFAULT '',
            forged_day INTEGER NOT NULL DEFAULT 0,
            expires_day INTEGER NOT NULL DEFAULT 0,
            forged_by_discord_id INTEGER NOT NULL DEFAULT 0,
            broken_day INTEGER,
            break_reason TEXT NOT NULL DEFAULT '',
            UNIQUE(pack_id, clan_name)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_cat_pact_offers (
            pack_id INTEGER NOT NULL,
            clan_name TEXT NOT NULL COLLATE NOCASE,
            last_fail_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (pack_id, clan_name)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_wolf_treaties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            pack_id INTEGER NOT NULL,
            other_pack_id INTEGER NOT NULL,
            pact_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            terms_note TEXT NOT NULL DEFAULT '',
            forged_day INTEGER NOT NULL DEFAULT 0,
            expires_day INTEGER NOT NULL DEFAULT 0,
            forged_by_discord_id INTEGER NOT NULL DEFAULT 0,
            broken_day INTEGER,
            break_reason TEXT NOT NULL DEFAULT '',
            UNIQUE(pack_id, other_pack_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_wolf_pact_offers (
            pack_id INTEGER NOT NULL,
            other_pack_id INTEGER NOT NULL,
            last_fail_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (pack_id, other_pack_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_mates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER,
            message_id INTEGER,
            initiator_wolf_id INTEGER NOT NULL,
            partner_wolf_id INTEGER NOT NULL,
            partner_discord_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_role_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            discord_id INTEGER NOT NULL,
            wolf_id INTEGER NOT NULL,
            wolf_name TEXT NOT NULL,
            role_feature TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            resolved_by_discord_id INTEGER
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_stillborn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            mother_wolf_id INTEGER NOT NULL,
            pup_name TEXT NOT NULL,
            genetic_conditions TEXT NOT NULL DEFAULT '[]',
            stats_json TEXT NOT NULL,
            father_wolf_id INTEGER,
            pack_id INTEGER,
            great_pack TEXT,
            birth_sex TEXT NOT NULL,
            born_day INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.execute("DROP TABLE IF EXISTS pups")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_prey_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            prey_key TEXT NOT NULL,
            uses_left INTEGER NOT NULL,
            bone_value INTEGER NOT NULL,
            acquired_day INTEGER NOT NULL,
            is_rotting INTEGER NOT NULL DEFAULT 0,
            deposited_by INTEGER,
            FOREIGN KEY (pack_id) REFERENCES packs(id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_herb_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            herb_key TEXT NOT NULL,
            form TEXT NOT NULL DEFAULT 'dried',
            potency INTEGER NOT NULL DEFAULT 100,
            quantity INTEGER NOT NULL DEFAULT 1,
            acquired_day INTEGER NOT NULL,
            deposited_by INTEGER,
            FOREIGN KEY (pack_id) REFERENCES packs(id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wolf_rivalries (
            wolf_id INTEGER NOT NULL,
            rival_key TEXT NOT NULL,
            grudge INTEGER NOT NULL DEFAULT 0,
            encounters INTEGER NOT NULL DEFAULT 0,
            last_encounter_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (wolf_id, rival_key)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rp_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            pack TEXT,
            mood TEXT,
            plot_phase INTEGER,
            status TEXT NOT NULL DEFAULT 'pending',
            submitted_by INTEGER,
            reviewed_by INTEGER,
            created_day INTEGER
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pack_amusement_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            uses_left INTEGER NOT NULL,
            deposited_by INTEGER,
            FOREIGN KEY (pack_id) REFERENCES packs(id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS amusement_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wolf_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            uses_left INTEGER NOT NULL,
            FOREIGN KEY (wolf_id) REFERENCES users(id)
        )
        """
    )

    acct_cols_late = {row[1] for row in conn.execute("PRAGMA table_info(account_progress)")}
    if acct_cols_late and "used_secondary_switch" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN used_secondary_switch INTEGER NOT NULL DEFAULT 0"
        )
    if acct_cols_late and "boost_first_claimed" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN boost_first_claimed INTEGER NOT NULL DEFAULT 0"
        )
    if acct_cols_late and "boost_second_claimed" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN boost_second_claimed INTEGER NOT NULL DEFAULT 0"
        )
    if acct_cols_late and "invite_reward_month" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN invite_reward_month TEXT NOT NULL DEFAULT ''"
        )
    if acct_cols_late and "invite_reward_count" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN invite_reward_count INTEGER NOT NULL DEFAULT 0"
        )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS invite_referrals (
            guild_id INTEGER NOT NULL,
            invitee_discord_id INTEGER NOT NULL,
            inviter_discord_id INTEGER NOT NULL,
            join_day INTEGER NOT NULL,
            registered_day INTEGER,
            rollovers_after_register INTEGER NOT NULL DEFAULT 0,
            welcome_granted INTEGER NOT NULL DEFAULT 0,
            referrer_granted INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, invitee_discord_id)
        )
        """
    )

    if acct_cols_late and "donor_tier" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN donor_tier TEXT NOT NULL DEFAULT ''"
        )
    if acct_cols_late and "donor_total_cents" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN donor_total_cents INTEGER NOT NULL DEFAULT 0"
        )
    if acct_cols_late and "donor_supporter_until" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN donor_supporter_until TEXT NOT NULL DEFAULT ''"
        )
    if acct_cols_late and "donor_bones_month" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN donor_bones_month TEXT NOT NULL DEFAULT ''"
        )
    if acct_cols_late and "donor_bones_month_amount" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN donor_bones_month_amount INTEGER NOT NULL DEFAULT 0"
        )
    if acct_cols_late and "kickstarter_backer" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN kickstarter_backer INTEGER NOT NULL DEFAULT 0"
        )
    if acct_cols_late and "kofi_membership_tier" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN kofi_membership_tier TEXT NOT NULL DEFAULT ''"
        )
    if acct_cols_late and "kofi_membership_until" not in acct_cols_late:
        conn.execute(
            "ALTER TABLE account_progress ADD COLUMN kofi_membership_until TEXT NOT NULL DEFAULT ''"
        )
    if acct_cols_late and "possess_wolf_id" not in acct_cols_late:
        conn.execute("ALTER TABLE account_progress ADD COLUMN possess_wolf_id INTEGER")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS donation_codes (
            code TEXT PRIMARY KEY,
            bones INTEGER NOT NULL DEFAULT 0,
            donor_tier TEXT NOT NULL DEFAULT '',
            mood_bonus INTEGER NOT NULL DEFAULT 0,
            standing_bonus INTEGER NOT NULL DEFAULT 0,
            daily_bonus_days INTEGER NOT NULL DEFAULT 0,
            max_uses INTEGER NOT NULL DEFAULT 1,
            uses_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            note TEXT NOT NULL DEFAULT ''
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_xp_claims (
            discord_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            last_claim_day INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (discord_id, guild_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS donation_redemptions (
            code TEXT NOT NULL,
            discord_id INTEGER NOT NULL,
            redeemed_at TEXT NOT NULL,
            PRIMARY KEY (code, discord_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS kofi_transactions (
            transaction_id TEXT PRIMARY KEY,
            discord_id INTEGER NOT NULL,
            amount_cents INTEGER NOT NULL,
            bones_granted INTEGER NOT NULL,
            processed_at TEXT NOT NULL,
            event_type TEXT NOT NULL DEFAULT 'donation',
            tier_name TEXT NOT NULL DEFAULT '',
            is_subscription INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    kofi_cols = {row[1] for row in conn.execute("PRAGMA table_info(kofi_transactions)")}
    if kofi_cols and "event_type" not in kofi_cols:
        conn.execute(
            "ALTER TABLE kofi_transactions ADD COLUMN event_type TEXT NOT NULL DEFAULT 'donation'"
        )
    if kofi_cols and "tier_name" not in kofi_cols:
        conn.execute(
            "ALTER TABLE kofi_transactions ADD COLUMN tier_name TEXT NOT NULL DEFAULT ''"
        )
    if kofi_cols and "is_subscription" not in kofi_cols:
        conn.execute(
            "ALTER TABLE kofi_transactions ADD COLUMN is_subscription INTEGER NOT NULL DEFAULT 0"
        )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS kofi_email_links (
            email TEXT PRIMARY KEY,
            discord_id INTEGER NOT NULL,
            linked_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS kofi_shop_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL,
            discord_id INTEGER,
            email TEXT NOT NULL DEFAULT '',
            product_key TEXT NOT NULL,
            product_label TEXT NOT NULL,
            amount_cents INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            fulfilled_at TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS broken_canine_rites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id INTEGER NOT NULL,
            incumbent_wolf_id INTEGER NOT NULL,
            winner_wolf_id INTEGER NOT NULL,
            log_json TEXT NOT NULL,
            outcome TEXT NOT NULL,
            triggered_day INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )

    from config import PUP_MAX_MOONS

    conn.execute(
        """
        UPDATE users
        SET sexuality = 'too_young'
        WHERE age_months < ? AND sexuality != 'too_young'
        """,
        (PUP_MAX_MOONS,),
    )

    from engine.character import reconcile_hp

    for row in conn.execute(
        "SELECT id, attr_str, attr_con, hp, max_hp FROM users"
    ).fetchall():
        new_hp, new_max = reconcile_hp(
            row["hp"],
            row["max_hp"],
            row["attr_str"],
            row["attr_con"],
        )
        conn.execute(
            "UPDATE users SET max_hp = ?, hp = ? WHERE id = ?",
            (new_max, new_hp, row["id"]),
        )

    _migrate_wolf_name_uniqueness(conn)
    _migrate_merge_suffix_duplicate_wolves(conn)
    _migrate_pending_stillborn_name_uniqueness(conn)
    _migrate_skill_ranks_to_traits(conn)
    _migrate_stick_item_key(conn)
    _ensure_combat_fighters_wolf_id(conn)


def _migrate_skill_ranks_to_traits(conn: sqlite3.Connection) -> None:
    """Legacy skill_ranks column → earned character_traits bonuses."""
    from engine.character import parse_skill_ranks
    from engine.character_traits import adjust_skill_trait_experience

    rows = conn.execute(
        "SELECT id, skill_ranks FROM users WHERE skill_ranks IS NOT NULL AND skill_ranks != '{}'"
    ).fetchall()
    for row in rows:
        ranks = parse_skill_ranks(row["skill_ranks"])
        if not ranks:
            continue
        wolf_id = int(row["id"])
        for skill_key, rank in ranks.items():
            for _ in range(max(0, int(rank))):
                adjust_skill_trait_experience(wolf_id, skill_key, 1)
        conn.execute("UPDATE users SET skill_ranks = '{}' WHERE id = ?", (wolf_id,))


def _migrate_stick_item_key(conn: sqlite3.Connection) -> None:
    """Rename inventory item herb_stick → stick (compendium key stays stick)."""
    old = conn.execute("SELECT id FROM items WHERE key = 'herb_stick'").fetchone()
    if not old:
        return
    clash = conn.execute("SELECT id FROM items WHERE key = 'stick'").fetchone()
    if clash:
        old_id, new_id = old["id"], clash["id"]
        for row in conn.execute(
            "SELECT wolf_id, quantity FROM inventory WHERE item_id = ?", (old_id,)
        ).fetchall():
            existing = conn.execute(
                "SELECT quantity FROM inventory WHERE wolf_id = ? AND item_id = ?",
                (row["wolf_id"], new_id),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE inventory SET quantity = quantity + ? WHERE wolf_id = ? AND item_id = ?",
                    (row["quantity"], row["wolf_id"], new_id),
                )
            else:
                conn.execute(
                    "INSERT INTO inventory (wolf_id, item_id, quantity) VALUES (?, ?, ?)",
                    (row["wolf_id"], new_id, row["quantity"]),
                )
        conn.execute("DELETE FROM inventory WHERE item_id = ?", (old_id,))
        conn.execute("DELETE FROM items WHERE id = ?", (old_id,))
    else:
        conn.execute("UPDATE items SET key = 'stick' WHERE key = 'herb_stick'")


_SUFFIX_WOLF_NAME_RE = re.compile(r"^(.*) \((\d+)\)$")


def _wolf_name_taken_conn(
    conn: sqlite3.Connection,
    name: str,
    *,
    exclude_wolf_id: int | None = None,
) -> bool:
    cleaned = name.strip()
    sql = "SELECT 1 FROM users WHERE wolf_name = ? COLLATE NOCASE"
    params: list = [cleaned]
    if exclude_wolf_id is not None:
        sql += " AND id != ?"
        params.append(exclude_wolf_id)
    sql += " LIMIT 1"
    return conn.execute(sql, params).fetchone() is not None


def _pending_pup_name_taken_conn(
    conn: sqlite3.Connection,
    name: str,
    *,
    exclude_pending_id: int | None = None,
) -> bool:
    cleaned = name.strip()
    sql = "SELECT 1 FROM pending_stillborn WHERE pup_name = ? COLLATE NOCASE"
    params: list = [cleaned]
    if exclude_pending_id is not None:
        sql += " AND id != ?"
        params.append(exclude_pending_id)
    sql += " LIMIT 1"
    return conn.execute(sql, params).fetchone() is not None


def _disambiguated_wolf_name(base: str, counter: int) -> str:
    suffix = f" ({counter})"
    max_len = 32
    if len(base) + len(suffix) <= max_len:
        return base + suffix
    trimmed = base[: max_len - len(suffix)].rstrip()
    if not trimmed:
        trimmed = base[:1]
    return trimmed + suffix


def _migrate_wolf_name_uniqueness(conn: sqlite3.Connection) -> None:
    dup_groups = conn.execute(
        """
        SELECT LOWER(wolf_name) AS name_key, GROUP_CONCAT(id ORDER BY id) AS ids
        FROM users
        GROUP BY name_key
        HAVING COUNT(*) > 1
        """
    ).fetchall()
    for group in dup_groups:
        ids = [int(x) for x in group["ids"].split(",")]
        base = conn.execute(
            "SELECT wolf_name FROM users WHERE id = ?", (ids[0],)
        ).fetchone()["wolf_name"]
        counter = 2
        for wid in ids[1:]:
            while True:
                candidate = _disambiguated_wolf_name(base, counter)
                if not _wolf_name_taken_conn(conn, candidate):
                    break
                counter += 1
            conn.execute(
                "UPDATE users SET wolf_name = ? WHERE id = ?",
                (candidate, wid),
            )
            counter += 1
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_wolf_name_ci "
        "ON users(wolf_name COLLATE NOCASE)"
    )


def _merge_wolf_score(row: sqlite3.Row) -> int:
    score = 0
    if row["condition"] != "dead":
        score += 1000
    if row["character_lore"]:
        score += 500
    if row["character_traits"]:
        score += 400
    score += int(row["bones"] or 0)
    score += int(row["standing"] or 0)
    return score


def _canonical_wolf_name_from_pair(*names: str) -> str:
    for name in names:
        cleaned = name.strip()
        if not _SUFFIX_WOLF_NAME_RE.match(cleaned):
            return cleaned
    match = _SUFFIX_WOLF_NAME_RE.match(names[0].strip())
    return match.group(1).strip() if match else names[0].strip()


def _iter_wolf_fk_columns(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    tables = [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    for table in tables:
        if table == "users":
            continue
        for col in conn.execute(f"PRAGMA table_info({table})"):
            cname = col[1]
            if cname == "wolf_id" or cname.endswith("_wolf_id"):
                refs.append((table, cname))
    return refs


def _repoint_wolf_fk_conn(
    conn: sqlite3.Connection, donor_id: int, keeper_id: int
) -> None:
    for table, col in _iter_wolf_fk_columns(conn):
        try:
            conn.execute(
                f"UPDATE {table} SET {col} = ? WHERE {col} = ?",
                (keeper_id, donor_id),
            )
        except sqlite3.IntegrityError:
            conn.execute(f"DELETE FROM {table} WHERE {col} = ?", (donor_id,))
        except sqlite3.OperationalError:
            continue

    for col in (
        "bonded_mate_id",
        "mate_wolf_id",
        "bio_parent_1_id",
        "bio_parent_2_id",
        "adopt_parent_1_id",
        "adopt_parent_2_id",
    ):
        conn.execute(
            f"UPDATE users SET {col} = ? WHERE {col} = ?",
            (keeper_id, donor_id),
        )
    conn.execute(
        "UPDATE account_progress SET active_wolf_id = ? WHERE active_wolf_id = ?",
        (keeper_id, donor_id),
    )


def _merge_wolf_profiles_conn(
    conn: sqlite3.Connection, keeper_id: int, donor_id: int
) -> None:
    if keeper_id == donor_id:
        return
    keeper = conn.execute("SELECT * FROM users WHERE id = ?", (keeper_id,)).fetchone()
    donor = conn.execute("SELECT * FROM users WHERE id = ?", (donor_id,)).fetchone()
    if not keeper or not donor:
        return
    if keeper["discord_id"] != donor["discord_id"]:
        raise ValueError("Wolves must belong to the same account to merge.")

    canonical_name = _canonical_wolf_name_from_pair(
        keeper["wolf_name"], donor["wolf_name"]
    )

    for row in conn.execute(
        "SELECT item_id, quantity FROM inventory WHERE wolf_id = ?", (donor_id,)
    ):
        _grant_item_conn(conn, keeper_id, row["item_id"], int(row["quantity"]))
    conn.execute("DELETE FROM inventory WHERE wolf_id = ?", (donor_id,))

    for field in ("bones", "standing", "remnants"):
        donor_val = int(donor[field] or 0)
        if donor_val:
            conn.execute(
                f"UPDATE users SET {field} = COALESCE({field}, 0) + ? WHERE id = ?",
                (donor_val, keeper_id),
            )

    _repoint_wolf_fk_conn(conn, donor_id, keeper_id)
    conn.execute("DELETE FROM user_quests WHERE wolf_id = ?", (donor_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (donor_id,))

    if keeper["wolf_name"] != canonical_name and not _wolf_name_taken_conn(
        conn, canonical_name, exclude_wolf_id=keeper_id
    ):
        conn.execute(
            "UPDATE users SET wolf_name = ? WHERE id = ?",
            (canonical_name, keeper_id),
        )


def merge_wolf_profiles(keeper_wolf_id: int, donor_wolf_id: int) -> None:
    with get_db() as conn:
        _merge_wolf_profiles_conn(conn, keeper_wolf_id, donor_wolf_id)


def _migrate_merge_suffix_duplicate_wolves(conn: sqlite3.Connection) -> None:
    wolves = conn.execute("SELECT id, discord_id, wolf_name FROM users").fetchall()
    by_discord: dict[int, dict[str, sqlite3.Row]] = {}
    for wolf in wolves:
        by_discord.setdefault(wolf["discord_id"], {})[wolf["wolf_name"].lower()] = wolf

    merged_ids: set[int] = set()
    for discord_id, name_map in by_discord.items():
        for wolf in list(name_map.values()):
            if wolf["id"] in merged_ids:
                continue
            match = _SUFFIX_WOLF_NAME_RE.match(wolf["wolf_name"])
            if not match:
                continue
            base_wolf = name_map.get(match.group(1).lower())
            if not base_wolf or base_wolf["id"] in merged_ids:
                continue
            row_a = conn.execute(
                "SELECT * FROM users WHERE id = ?", (base_wolf["id"],)
            ).fetchone()
            row_b = conn.execute("SELECT * FROM users WHERE id = ?", (wolf["id"],)).fetchone()
            if not row_a or not row_b:
                continue
            if _merge_wolf_score(row_a) >= _merge_wolf_score(row_b):
                keeper_id, donor_id = row_a["id"], row_b["id"]
            else:
                keeper_id, donor_id = row_b["id"], row_a["id"]
            _merge_wolf_profiles_conn(conn, keeper_id, donor_id)
            merged_ids.add(donor_id)


def _migrate_pending_stillborn_name_uniqueness(conn: sqlite3.Connection) -> None:
    dup_groups = conn.execute(
        """
        SELECT LOWER(pup_name) AS name_key, GROUP_CONCAT(id ORDER BY id) AS ids
        FROM pending_stillborn
        GROUP BY name_key
        HAVING COUNT(*) > 1
        """
    ).fetchall()
    for group in dup_groups:
        ids = [int(x) for x in group["ids"].split(",")]
        base = conn.execute(
            "SELECT pup_name FROM pending_stillborn WHERE id = ?", (ids[0],)
        ).fetchone()["pup_name"]
        counter = 2
        for row_id in ids[1:]:
            while True:
                candidate = _disambiguated_wolf_name(base, counter)
                if not _pending_pup_name_taken_conn(conn, candidate):
                    break
                counter += 1
            conn.execute(
                "UPDATE pending_stillborn SET pup_name = ? WHERE id = ?",
                (candidate, row_id),
            )
            counter += 1
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_pending_stillborn_pup_name_ci "
        "ON pending_stillborn(pup_name COLLATE NOCASE)"
    )


def wolf_name_taken(name: str, *, exclude_wolf_id: int | None = None) -> bool:
    with get_db() as conn:
        return _wolf_name_taken_conn(conn, name, exclude_wolf_id=exclude_wolf_id)


def pending_pup_name_taken(
    name: str, *, exclude_pending_id: int | None = None
) -> bool:
    with get_db() as conn:
        return _pending_pup_name_taken_conn(
            conn, name, exclude_pending_id=exclude_pending_id
        )


def get_pending_stillborn_global(pup_name: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pending_stillborn
            WHERE pup_name = ? COLLATE NOCASE
            LIMIT 1
            """,
            (pup_name.strip(),),
        ).fetchone()


def validate_wolf_name_available(
    name: str,
    *,
    exclude_wolf_id: int | None = None,
    label: str = "Wolf names",
) -> tuple[str | None, str | None]:
    from utils.names import validate_display_name

    cleaned, err = validate_display_name(name, label=label)
    if err:
        return None, err
    with get_db() as conn:
        if _wolf_name_taken_conn(conn, cleaned, exclude_wolf_id=exclude_wolf_id):
            return None, (
                f"The name **{cleaned}** is already taken by another wolf. "
                "Choose a different name."
            )
        if _pending_pup_name_taken_conn(conn, cleaned):
            return None, (
                f"The name **{cleaned}** is already reserved by a dying pup "
                "awaiting neonatal care. Choose a different name."
            )
    return cleaned, None


def _resolve_wolf_id_conn(conn: sqlite3.Connection, discord_id: int) -> int | None:
    account = conn.execute(
        "SELECT active_wolf_id, possess_wolf_id FROM account_progress WHERE discord_id = ?",
        (discord_id,),
    ).fetchone()
    if account and account["possess_wolf_id"]:
        possessed = conn.execute(
            "SELECT id FROM users WHERE id = ?",
            (account["possess_wolf_id"],),
        ).fetchone()
        if possessed:
            return int(possessed["id"])
        conn.execute(
            "UPDATE account_progress SET possess_wolf_id = NULL WHERE discord_id = ?",
            (discord_id,),
        )
    if account and account["active_wolf_id"]:
        active = conn.execute(
            "SELECT id FROM users WHERE id = ? AND discord_id = ?",
            (account["active_wolf_id"], discord_id),
        ).fetchone()
        if active:
            return int(active["id"])
        conn.execute(
            "UPDATE account_progress SET active_wolf_id = NULL WHERE discord_id = ?",
            (discord_id,),
        )
    row = conn.execute(
        "SELECT id FROM users WHERE discord_id = ? ORDER BY id ASC LIMIT 1",
        (discord_id,),
    ).fetchone()
    return row["id"] if row else None


def _rebuild_users_with_id_pk(conn: sqlite3.Connection) -> None:
    cols = conn.execute("PRAGMA table_info(users)").fetchall()
    col_names = [c[1] for c in cols]
    parts = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
    for c in cols:
        name, ctype, notnull, default, pk = c[1], c[2], c[3], c[4], c[5]
        if pk:
            continue
        defn = f"{name} {ctype}"
        if notnull:
            defn += " NOT NULL"
        if default is not None:
            default_str = str(default)
            if default_str.startswith("'") and default_str.endswith("'"):
                defn += f" DEFAULT {default_str}"
            elif ctype.upper().startswith("TEXT"):
                defn += f" DEFAULT '{default_str}'"
            else:
                defn += f" DEFAULT {default_str}"
        parts.append(defn)
    # Former primary key (discord_id) becomes a normal indexed owner column.
    pk_cols = [c[1] for c in cols if c[5]]
    for pk_name in pk_cols:
        pk_col = next(c for c in cols if c[1] == pk_name)
        _, ctype, notnull, default, _pk = pk_col[1], pk_col[2], pk_col[3], pk_col[4], pk_col[5]
        defn = f"{pk_name} {ctype} NOT NULL"
        if default is not None:
            default_str = str(default)
            if default_str.startswith("'") and default_str.endswith("'"):
                defn += f" DEFAULT {default_str}"
            elif ctype.upper().startswith("TEXT"):
                defn += f" DEFAULT '{default_str}'"
            else:
                defn += f" DEFAULT {default_str}"
        parts.append(defn)
    conn.execute("DROP TABLE IF EXISTS users_new")
    conn.execute(f"CREATE TABLE users_new ({', '.join(parts)})")
    names_sql = ", ".join(col_names)
    conn.execute(f"INSERT INTO users_new ({names_sql}) SELECT {names_sql} FROM users")
    conn.execute("DROP TABLE users")
    conn.execute("ALTER TABLE users_new RENAME TO users")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_discord_id ON users(discord_id)")


def _migrate_inventory_to_wolf_id(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE inventory ADD COLUMN wolf_id INTEGER")
    for row in conn.execute("SELECT DISTINCT discord_id FROM inventory"):
        wid = _resolve_wolf_id_conn(conn, row["discord_id"])
        if wid:
            conn.execute(
                "UPDATE inventory SET wolf_id = ? WHERE discord_id = ?",
                (wid, row["discord_id"]),
            )
    conn.execute(
        """
        CREATE TABLE inventory_new (
            wolf_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (wolf_id, item_id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
        """
    )
    conn.execute(
        """
        INSERT INTO inventory_new (wolf_id, item_id, quantity)
        SELECT wolf_id, item_id, quantity FROM inventory WHERE wolf_id IS NOT NULL
        """
    )
    conn.execute("DROP TABLE inventory")
    conn.execute("ALTER TABLE inventory_new RENAME TO inventory")


def _migrate_user_quests_to_wolf_id(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE user_quests ADD COLUMN wolf_id INTEGER")
    for row in conn.execute("SELECT DISTINCT discord_id FROM user_quests"):
        wid = _resolve_wolf_id_conn(conn, row["discord_id"])
        if wid:
            conn.execute(
                "UPDATE user_quests SET wolf_id = ? WHERE discord_id = ?",
                (wid, row["discord_id"]),
            )


def _migrate_multi_wolf(conn: sqlite3.Connection) -> None:
    user_cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "id" not in user_cols:
        _rebuild_users_with_id_pk(conn)

    account_cols = {row[1] for row in conn.execute("PRAGMA table_info(account_progress)")}
    if account_cols and "autoproxy_wolf_id" not in account_cols:
        conn.execute("ALTER TABLE account_progress ADD COLUMN autoproxy_wolf_id INTEGER")
    if account_cols and "active_wolf_id" not in account_cols:
        conn.execute("ALTER TABLE account_progress ADD COLUMN active_wolf_id INTEGER")
        for row in conn.execute("SELECT DISTINCT discord_id FROM users"):
            wid = conn.execute(
                "SELECT id FROM users WHERE discord_id = ? ORDER BY id ASC LIMIT 1",
                (row["discord_id"],),
            ).fetchone()
            if not wid:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO account_progress (discord_id) VALUES (?)",
                (row["discord_id"],),
            )
            conn.execute(
                "UPDATE account_progress SET active_wolf_id = ? WHERE discord_id = ?",
                (wid["id"], row["discord_id"]),
            )

    inv_cols = {row[1] for row in conn.execute("PRAGMA table_info(inventory)")}
    if inv_cols and "wolf_id" not in inv_cols:
        _migrate_inventory_to_wolf_id(conn)

    uq_cols = {row[1] for row in conn.execute("PRAGMA table_info(user_quests)")}
    if uq_cols and "wolf_id" not in uq_cols:
        _migrate_user_quests_to_wolf_id(conn)

    _ensure_combat_fighters_wolf_id(conn)

    _migrate_bond_ids_to_wolf_ids(conn)


def _ensure_combat_fighters_wolf_id(conn: sqlite3.Connection) -> None:
    cf_cols = {row[1] for row in conn.execute("PRAGMA table_info(combat_fighters)")}
    if not cf_cols or "wolf_id" in cf_cols:
        return
    conn.execute("ALTER TABLE combat_fighters ADD COLUMN wolf_id INTEGER")
    for row in conn.execute(
        "SELECT DISTINCT discord_id FROM combat_fighters WHERE discord_id IS NOT NULL"
    ):
        wid = _resolve_wolf_id_conn(conn, row["discord_id"])
        if wid:
            conn.execute(
                "UPDATE combat_fighters SET wolf_id = ? WHERE discord_id = ?",
                (wid, row["discord_id"]),
            )


def _migrate_bond_ids_to_wolf_ids(conn: sqlite3.Connection) -> None:
    user_cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "mate_wolf_id" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN mate_wolf_id INTEGER")

    for row in conn.execute(
        "SELECT id, bonded_mate_id FROM users WHERE bonded_mate_id IS NOT NULL"
    ):
        bm = row["bonded_mate_id"]
        if conn.execute("SELECT 1 FROM users WHERE id = ?", (bm,)).fetchone():
            continue
        partner = conn.execute(
            "SELECT id FROM users WHERE discord_id = ? ORDER BY id ASC LIMIT 1",
            (bm,),
        ).fetchone()
        if partner:
            conn.execute(
                "UPDATE users SET bonded_mate_id = ? WHERE id = ?",
                (partner["id"], row["id"]),
            )

    for row in conn.execute(
        """
        SELECT id, mate_discord_id FROM users
        WHERE mate_discord_id IS NOT NULL AND (mate_wolf_id IS NULL OR mate_wolf_id = 0)
        """
    ):
        partner = conn.execute(
            "SELECT id FROM users WHERE discord_id = ? ORDER BY id ASC LIMIT 1",
            (row["mate_discord_id"],),
        ).fetchone()
        if partner:
            conn.execute(
                "UPDATE users SET mate_wolf_id = ? WHERE id = ?",
                (partner["id"], row["id"]),
            )


def _seed_great_packs(conn: sqlite3.Connection) -> None:
    """Ensure the four Great Packs exist as shared pack rows."""
    now = utcnow()
    for key, info in GREAT_PACKS.items():
        existing = conn.execute("SELECT id FROM packs WHERE key = ?", (key,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE packs SET name = ? WHERE key = ?",
                (info["name"], key),
            )
        else:
            conn.execute(
                """
                INSERT INTO packs (key, name, alpha_id, treasury, tax_rate, pack_unity, created_at)
                VALUES (?, ?, NULL, 0, 0, 5, ?)
                """,
                (key, info["name"], now),
            )


def _reconcile_great_pack_alphas(conn: sqlite3.Connection) -> None:
    """Point Great Pack alpha_id at a wolf with the Alpha role when the seat is stale."""
    for key in GREAT_PACKS:
        pack = conn.execute("SELECT * FROM packs WHERE key = ?", (key,)).fetchone()
        if not pack:
            continue
        alphas = conn.execute(
            """
            SELECT discord_id FROM users
            WHERE pack_id = ? AND wolf_role = 'alpha'
            ORDER BY standing DESC, id ASC
            """,
            (pack["id"],),
        ).fetchall()
        if not alphas:
            continue
        valid = {int(row["discord_id"]) for row in alphas}
        holder = pack["alpha_id"]
        if holder is None or int(holder) not in valid:
            conn.execute(
                "UPDATE packs SET alpha_id = ? WHERE id = ?",
                (alphas[0]["discord_id"], pack["id"]),
            )


def _migrate_user_pack_affiliation(conn: sqlite3.Connection) -> None:
    """Point users' pack_id at their Great Pack row when great_pack is set."""
    for key in GREAT_PACKS:
        pack = conn.execute("SELECT id FROM packs WHERE key = ?", (key,)).fetchone()
        if not pack:
            continue
        conn.execute(
            "UPDATE users SET pack_id = ? WHERE great_pack = ?",
            (pack["id"], key),
        )


def _backfill_starting_herbs(conn: sqlite3.Connection) -> None:
    """One-time: grant pack starting herbs to wolves who never received them."""
    users = conn.execute(
        "SELECT id, great_pack FROM users WHERE great_pack IS NOT NULL"
    ).fetchall()
    for user in users:
        gp = user["great_pack"]
        if gp not in GREAT_PACKS:
            continue
        has_herb = conn.execute(
            """
            SELECT 1 FROM inventory i
            JOIN items it ON it.id = i.item_id
            WHERE i.wolf_id = ? AND it.key LIKE 'herb_%'
            LIMIT 1
            """,
            (user["id"],),
        ).fetchone()
        if has_herb:
            continue
        _grant_starting_herbs_conn(conn, user["id"], gp)


def _strip_canonical_lore_genetics(conn: sqlite3.Connection) -> None:
    """Kanami/Murkvein disabilities live in character_traits; remove duplicate genetics."""
    from engine.genetics import encode_genetic_conditions, parse_genetic_conditions

    strip_map = {
        "Kanami": ["blindness", "partial_blindness"],
        "Murkvein": ["missing_tail"],
    }
    for name, remove_keys in strip_map.items():
        rows = conn.execute(
            "SELECT id, discord_id, genetic_conditions FROM users WHERE wolf_name = ? COLLATE NOCASE",
            (name,),
        ).fetchall()
        for row in rows:
            existing = parse_genetic_conditions(row["genetic_conditions"])
            remaining = [k for k in existing if k not in remove_keys]
            if remaining != existing:
                conn.execute(
                    "UPDATE users SET genetic_conditions = ? WHERE id = ?",
                    (encode_genetic_conditions(remaining), row["id"]),
                )


def _grant_starting_herbs_conn(
    conn: sqlite3.Connection, wolf_id: int, great_pack_key: str
) -> int:
    if great_pack_key not in GREAT_PACKS:
        return 0
    granted = 0
    for herb_key in GREAT_PACKS[great_pack_key]["starting_herbs"]:
        from herbs import herb_inventory_key

        item_row = conn.execute(
            "SELECT id FROM items WHERE key = ?", (herb_inventory_key(herb_key),)
        ).fetchone()
        if not item_row:
            continue
        item_id = item_row["id"]
        row = conn.execute(
            "SELECT quantity FROM inventory WHERE wolf_id = ? AND item_id = ?",
            (wolf_id, item_id),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE inventory SET quantity = quantity + 1 WHERE wolf_id = ? AND item_id = ?",
                (wolf_id, item_id),
            )
        else:
            conn.execute(
                "INSERT INTO inventory (wolf_id, item_id, quantity) VALUES (?, ?, 1)",
                (wolf_id, item_id),
            )
        granted += 1
    return granted


def grant_great_pack_starting_herbs(wolf_id: int, great_pack_key: str) -> int:
    with get_db() as conn:
        return _grant_starting_herbs_conn(conn, wolf_id, great_pack_key)


def _seed_shop_items(conn: sqlite3.Connection) -> None:
    for key, name, description, price, sell_price in DEFAULT_SHOP_ITEMS:
        conn.execute(
            """
            INSERT OR IGNORE INTO items (key, name, description, price, sell_price)
            VALUES (?, ?, ?, ?, ?)
            """,
            (key, name, description, price, sell_price),
        )
        conn.execute(
            """
            UPDATE items
            SET name = ?, description = ?, price = ?, sell_price = ?
            WHERE key = ?
            """,
            (name, description, price, sell_price, key),
        )


def _retire_shop_items(conn: sqlite3.Connection) -> None:
    from config import RETIRED_SHOP_ITEM_KEYS

    for key in RETIRED_SHOP_ITEM_KEYS:
        conn.execute(
            "UPDATE items SET price = 0, sell_price = 0 WHERE key = ?",
            (key,),
        )


def _seed_herb_items(conn: sqlite3.Connection) -> None:
    from herbs import HERBS, herb_inventory_key

    for key, meta in HERBS.items():
        item_key = herb_inventory_key(key)
        conn.execute(
            """
            INSERT OR IGNORE INTO items (key, name, description, price, sell_price)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                item_key,
                meta["name"],
                meta["effect"],
                0,
                5,
            ),
        )
        if key == "stick":
            conn.execute(
                """
                UPDATE items SET name = ?, description = ?, sell_price = ?
                WHERE key = 'stick'
                """,
                (meta["name"], meta["effect"], 5),
            )


def _seed_prey_items(conn: sqlite3.Connection) -> None:
    from config import SHOP_PREY_PRICES
    from engine.prey_items import PREY_CATALOG

    for key, meta in PREY_CATALOG.items():
        item_key = f"prey_{key}"
        price, sell = SHOP_PREY_PRICES.get(key, (0, 0))
        is_forage = meta.get("category") == "forage"
        noun = "Hoard food" if is_forage else "Hoard carcass"
        spoil_verb = "overripens" if is_forage else "rots"
        desc = (
            f"{noun}; `/eat` or `/preypile`. "
            f"{spoil_verb.capitalize()} after ~{meta.get('rot_days', 5)} sunrises."
        )
        if price > 0:
            desc += " Buy at the trading post."
        conn.execute(
            """
            INSERT OR IGNORE INTO items (key, name, description, price, sell_price)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_key, meta["name"], desc, price, sell),
        )
        conn.execute(
            """
            UPDATE items
            SET name = ?, description = ?, price = ?, sell_price = ?
            WHERE key = ?
            """,
            (meta["name"], desc, price, sell, item_key),
        )


def _seed_amusement_items(conn: sqlite3.Connection) -> None:
    from config import SHOP_TOY_PRICES
    from engine.amusement_items import AMUSEMENT_CATALOG

    for key, meta in AMUSEMENT_CATALOG.items():
        item_key = f"toy_{key}"
        if key in SHOP_TOY_PRICES:
            price, sell = SHOP_TOY_PRICES[key]
        else:
            price, sell = 0, meta.get("sell_bones", 0)
        desc = meta["description"] + "; `/playpen action:play` to boost mood."
        if price > 0:
            desc += " Buy at the trading post."
        conn.execute(
            """
            INSERT OR IGNORE INTO items (key, name, description, price, sell_price)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_key, meta["name"], desc, price, sell),
        )
        if price > 0:
            conn.execute(
                """
                UPDATE items
                SET name = ?, description = ?, price = ?, sell_price = ?
                WHERE key = ?
                """,
                (meta["name"], desc, price, sell, item_key),
            )


def _seed_quests(conn: sqlite3.Connection) -> None:
    _purge_retired_quests(conn)
    from config import ACHIEVEMENT_QUESTS

    for row in ACHIEVEMENT_QUESTS:
        key, title, desc, obj, count, reward, standing, qtype, diff = row
        conn.execute(
            """
            INSERT OR IGNORE INTO quests
            (key, title, description, objective_type, objective_count,
             reward_bones, standing_reward, quest_type, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (key, title, desc, obj, count, reward, standing, qtype, diff),
        )
    for row in STATIC_QUESTS:
        key, title, desc, obj, count, reward, standing, qtype, diff = row
        conn.execute(
            """
            INSERT OR IGNORE INTO quests
            (key, title, description, objective_type, objective_count,
             reward_bones, standing_reward, quest_type, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (key, title, desc, obj, count, reward, standing, qtype, diff),
        )
    for row in ROLE_QUESTS:
        key, title, desc, obj, count, reward, standing, qtype, diff, role, pack = row
        conn.execute(
            """
            INSERT OR IGNORE INTO quests
            (key, title, description, objective_type, objective_count,
             reward_bones, standing_reward, quest_type, difficulty,
             required_role, required_pack)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (key, title, desc, obj, count, reward, standing, qtype, diff, role, pack),
        )
        conn.execute(
            """
            UPDATE quests
            SET title = ?, description = ?, objective_type = ?, objective_count = ?,
                reward_bones = ?, standing_reward = ?, difficulty = ?,
                required_role = ?, required_pack = ?
            WHERE key = ?
            """,
            (title, desc, obj, count, reward, standing, diff, role, pack, key),
        )


def ensure_achievement_quests(discord_id: int, wolf_id: int) -> None:
    """Auto-enroll a wolf in every lifetime achievement; idempotent.

    Achievements aren't accepted from a board — every wolf tracks all of
    them automatically from registration onward. Also called lazily from
    `increment_quest_progress` so wolves registered before this system
    existed get backfilled the first time any of their progress fires.
    """
    from config import ACHIEVEMENT_QUESTS

    with get_db() as conn:
        have = conn.execute(
            """
            SELECT COUNT(*) AS n FROM user_quests uq
            JOIN quests q ON q.id = uq.quest_id
            WHERE uq.wolf_id = ? AND q.quest_type = 'achievement'
            """,
            (wolf_id,),
        ).fetchone()["n"]
        if have >= len(ACHIEVEMENT_QUESTS):
            return
        achievement_ids = conn.execute(
            "SELECT id FROM quests WHERE quest_type = 'achievement'"
        ).fetchall()
        existing_ids = {
            row["quest_id"]
            for row in conn.execute(
                "SELECT quest_id FROM user_quests WHERE wolf_id = ?", (wolf_id,)
            ).fetchall()
        }
        for row in achievement_ids:
            if row["id"] in existing_ids:
                continue
            conn.execute(
                """
                INSERT INTO user_quests
                (discord_id, quest_id, wolf_id, progress, status, assigned_day, accepted_at)
                VALUES (?, ?, ?, 0, 'active', 0, ?)
                """,
                (discord_id, row["id"], wolf_id, utcnow()),
            )


RETIRED_QUEST_KEYS = ("den_crafter",)


def _purge_retired_quests(conn: sqlite3.Connection) -> None:
    """Remove quests dropped from config (and any player assignments)."""
    for key in RETIRED_QUEST_KEYS:
        for row in conn.execute(
            "SELECT id FROM quests WHERE key = ? COLLATE NOCASE", (key,)
        ).fetchall():
            conn.execute("DELETE FROM user_quests WHERE quest_id = ?", (row["id"],))
            conn.execute("DELETE FROM quests WHERE id = ?", (row["id"],))


def ensure_territories(guild_id: int) -> None:
    with get_db() as conn:
        for key, name, bonus in DEFAULT_TERRITORIES:
            conn.execute(
                """
                INSERT OR IGNORE INTO territories (guild_id, key, name, daily_bonus)
                VALUES (?, ?, ?, ?)
                """,
                (guild_id, key, name, bonus),
            )


# --- Users ---


def _resolve_wolf_id(discord_id: int) -> int | None:
    with get_db() as conn:
        return _resolve_wolf_id_conn(conn, discord_id)


def get_user_by_id(wolf_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (wolf_id,)).fetchone()


def get_wolf_by_name(wolf_name: str) -> sqlite3.Row | None:
    cleaned = (wolf_name or "").strip()
    if not cleaned:
        return None
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM users
            WHERE LOWER(wolf_name) = LOWER(?)
            ORDER BY id ASC
            LIMIT 1
            """,
            (cleaned,),
        ).fetchone()


def get_user(discord_id: int) -> sqlite3.Row | None:
    wolf_id = _resolve_wolf_id(discord_id)
    if not wolf_id:
        return None
    return get_user_by_id(wolf_id)


def count_user_wolves(discord_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE discord_id = ?",
            (discord_id,),
        ).fetchone()
        return row["c"] if row else 0


def count_slot_wolves(discord_id: int) -> int:
    """Wolves that count toward MAX_WOLVES_PER_PLAYER (excludes born pups)."""
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM users
            WHERE discord_id = ? AND is_born_pup = 0
            """,
            (discord_id,),
        ).fetchone()
        return row["c"] if row else 0


def count_born_pups(discord_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM users
            WHERE discord_id = ? AND is_born_pup = 1
            """,
            (discord_id,),
        ).fetchone()
        return row["c"] if row else 0


def list_user_wolves(discord_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE discord_id = ? ORDER BY id ASC",
            (discord_id,),
        ).fetchall()


def find_user_wolf(discord_id: int, wolf_name: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM users
            WHERE discord_id = ? AND wolf_name = ? COLLATE NOCASE
            """,
            (discord_id, wolf_name.strip()),
        ).fetchone()


def explain_wolf_not_found(discord_id: int, wolf_name: str, *, player_label: str) -> str:
    """Actionable hint when find_user_wolf misses (lore-only name, global taken, etc.)."""
    name = wolf_name.strip()
    wolves = list_user_wolves(discord_id)
    lines = [f"**{player_label}** has no wolf named **{name}**."]

    if wolves:
        listed = ", ".join(f"**{row['wolf_name']}**" for row in wolves)
        lines.append(f"Their wolves: {listed}.")
        lines.append("Use `/wolfadmin list` to inspect, or omit **wolf_name** to target their active wolf.")
    else:
        lines.append("They have **no registered wolves** on Howlbert yet.")

    with get_db() as conn:
        global_row = conn.execute(
            """
            SELECT id, discord_id, wolf_name FROM users
            WHERE wolf_name = ? COLLATE NOCASE
            LIMIT 1
            """,
            (name,),
        ).fetchone()

    if global_row and int(global_row["discord_id"]) != int(discord_id):
        lines.append(
            f"**{global_row['wolf_name']}** already exists under another Discord account "
            f"(wolf id `{global_row['id']}`). "
            f"Use `/wolfadmin transfer` from that owner, or choose a different name."
        )
    else:
        from engine.character_lore_data import CHARACTER_LORE_BY_NAME

        if any(key.lower() == name.lower() for key in CHARACTER_LORE_BY_NAME):
            lines.append(
                f"Canonical lore is on file for **{name}**; the profile still needs to be created. "
                f"Use `/wolfadmin assign player:@… name:{name}` or have them `/register`."
            )
        elif not wolves:
            lines.append("Create one with `/wolfadmin assign` or have the player `/register`.")

    return "\n".join(lines)


def reassign_wolf_owner(
    wolf_id: int,
    new_discord_id: int,
    *,
    set_active: bool = True,
) -> str:
    """
    Move a wolf profile to another Discord account.
    Returns: ok | not_found | same_owner
    """
    with get_db() as conn:
        wolf = conn.execute("SELECT * FROM users WHERE id = ?", (wolf_id,)).fetchone()
        if not wolf:
            return "not_found"
        old_discord_id = wolf["discord_id"]
        if old_discord_id == new_discord_id:
            return "same_owner"

        conn.execute(
            "UPDATE users SET discord_id = ?, dormant = 0 WHERE id = ?",
            (new_discord_id, wolf_id),
        )
        conn.execute(
            "UPDATE user_quests SET discord_id = ? WHERE wolf_id = ?",
            (new_discord_id, wolf_id),
        )
        conn.execute(
            "UPDATE combat_fighters SET discord_id = ? WHERE wolf_id = ?",
            (new_discord_id, wolf_id),
        )

        pack_id = wolf["pack_id"]
        if pack_id:
            pack = conn.execute("SELECT * FROM packs WHERE id = ?", (pack_id,)).fetchone()
            if pack and pack["alpha_id"] == old_discord_id:
                conn.execute(
                    "UPDATE packs SET alpha_id = ? WHERE id = ?",
                    (new_discord_id, pack_id),
                )

        conn.execute(
            "INSERT OR IGNORE INTO account_progress (discord_id) VALUES (?)",
            (new_discord_id,),
        )

        if set_active:
            conn.execute(
                "UPDATE account_progress SET active_wolf_id = ? WHERE discord_id = ?",
                (wolf_id, new_discord_id),
            )

        account = conn.execute(
            "SELECT active_wolf_id FROM account_progress WHERE discord_id = ?",
            (old_discord_id,),
        ).fetchone()
        if account and account["active_wolf_id"] == wolf_id:
            remaining = conn.execute(
                "SELECT id FROM users WHERE discord_id = ? ORDER BY id ASC LIMIT 1",
                (old_discord_id,),
            ).fetchone()
            conn.execute(
                "UPDATE account_progress SET active_wolf_id = ? WHERE discord_id = ?",
                (remaining["id"] if remaining else None, old_discord_id),
            )

        old_auto = conn.execute(
            "SELECT autoproxy_wolf_id FROM account_progress WHERE discord_id = ?",
            (old_discord_id,),
        ).fetchone()
        if old_auto and old_auto["autoproxy_wolf_id"] == wolf_id:
            conn.execute(
                "UPDATE account_progress SET autoproxy_wolf_id = NULL WHERE discord_id = ?",
                (old_discord_id,),
            )
            conn.execute(
                "UPDATE account_progress SET autoproxy_wolf_id = ? WHERE discord_id = ?",
                (wolf_id, new_discord_id),
            )

    return "ok"


def set_active_wolf(discord_id: int, wolf_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE id = ? AND discord_id = ?",
            (wolf_id, discord_id),
        ).fetchone()
        if not row:
            return False
        user = conn.execute("SELECT * FROM users WHERE id = ?", (wolf_id,)).fetchone()
        conn.execute(
            "INSERT OR IGNORE INTO account_progress (discord_id) VALUES (?)",
            (discord_id,),
        )
        conn.execute(
            "UPDATE account_progress SET active_wolf_id = ? WHERE discord_id = ?",
            (wolf_id, discord_id),
        )
        first = conn.execute(
            "SELECT id FROM users WHERE discord_id = ? ORDER BY id ASC LIMIT 1",
            (discord_id,),
        ).fetchone()
        if first and first["id"] != wolf_id:
            conn.execute(
                "UPDATE account_progress SET used_secondary_switch = 1 WHERE discord_id = ?",
                (discord_id,),
            )
        if user and user["pack_id"]:
            pack = conn.execute(
                "SELECT * FROM packs WHERE id = ?", (user["pack_id"],)
            ).fetchone()
            if pack and pack["key"] in GREAT_PACKS:
                if user["wolf_role"] == "alpha":
                    conn.execute(
                        "UPDATE packs SET alpha_id = ? WHERE id = ?",
                        (discord_id, pack["id"]),
                    )
                elif pack["alpha_id"] == discord_id:
                    _promote_pack_alpha(conn, pack["id"])
        return True


def has_used_secondary_switch(discord_id: int) -> bool:
    account = get_account(discord_id)
    return bool(account and account["used_secondary_switch"])


def get_active_wolf_id(discord_id: int) -> int | None:
    return _resolve_wolf_id(discord_id)


# --- Wolf identity (avatar / bio / pronouns) and message proxying ---

_IDENTITY_FIELDS = frozenset(
    {"avatar_url", "pronouns", "ref_image_url", "bio", "birthday"}
)


def set_wolf_identity(wolf_id: int, **fields) -> None:
    """Update a wolf's RP identity fields (avatar, bio, pronouns, ref image, birthday)."""
    clean = {k: v for k, v in fields.items() if k in _IDENTITY_FIELDS}
    if not clean or not wolf_id:
        return
    update_user_by_id(wolf_id, **clean)


def set_wolf_proxy(wolf_id: int, prefix: str | None, suffix: str | None) -> None:
    update_user_by_id(
        wolf_id,
        proxy_prefix=(prefix or None),
        proxy_suffix=(suffix or None),
    )


def clear_wolf_proxy(wolf_id: int) -> None:
    update_user_by_id(wolf_id, proxy_prefix=None, proxy_suffix=None)


def get_proxy_wolves(discord_id: int) -> list[sqlite3.Row]:
    """Wolves on this account that have a proxy tag configured."""
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM users
            WHERE discord_id = ?
              AND (proxy_prefix IS NOT NULL OR proxy_suffix IS NOT NULL)
            ORDER BY id ASC
            """,
            (discord_id,),
        ).fetchall()


def get_autoproxy_wolf_id(discord_id: int) -> int | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT autoproxy_wolf_id FROM account_progress WHERE discord_id = ?",
            (discord_id,),
        ).fetchone()
    if not row or not row["autoproxy_wolf_id"]:
        return None
    return int(row["autoproxy_wolf_id"])


def set_autoproxy_wolf(discord_id: int, wolf_id: int | None) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO account_progress (discord_id) VALUES (?)",
            (discord_id,),
        )
        conn.execute(
            "UPDATE account_progress SET autoproxy_wolf_id = ? WHERE discord_id = ?",
            (wolf_id, discord_id),
        )


def create_scene(
    guild_id: int, thread_id: int, name: str, topic: str | None, owner_discord_id: int, day: int
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO rp_scenes (guild_id, thread_id, name, topic, owner_discord_id, day)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (guild_id, thread_id, name, topic, owner_discord_id, day),
        )
        return int(cur.lastrowid)


def get_scene_by_thread(thread_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM rp_scenes WHERE thread_id = ? ORDER BY id DESC LIMIT 1",
            (thread_id,),
        ).fetchone()


def join_scene(scene_id: int, wolf_id: int, wolf_name: str, discord_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO rp_scene_members (scene_id, wolf_id, wolf_name, discord_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(scene_id, wolf_id) DO UPDATE SET wolf_name = excluded.wolf_name
            """,
            (scene_id, wolf_id, wolf_name, discord_id),
        )


def leave_scene(scene_id: int, wolf_id: int) -> bool:
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM rp_scene_members WHERE scene_id = ? AND wolf_id = ?",
            (scene_id, wolf_id),
        )
        return cur.rowcount > 0


def get_scene_members(scene_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM rp_scene_members WHERE scene_id = ? ORDER BY joined_at ASC",
            (scene_id,),
        ).fetchall()


def close_scene(scene_id: int) -> None:
    with get_db() as conn:
        conn.execute("UPDATE rp_scenes SET status = 'closed' WHERE id = ?", (scene_id,))


def set_scene_roster_message_id(scene_id: int, message_id: int | None) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE rp_scenes SET roster_message_id = ? WHERE id = ?",
            (message_id, scene_id),
        )


def set_ic_location(discord_id: int, wolf_id: int, location: str | None) -> None:
    update_user(discord_id, wolf_id=wolf_id, ic_location=location)


JOURNAL_SUMMARY_MAX = 4000


def _clip_journal_summary(summary: str) -> str:
    summary = (summary or "").strip()
    if len(summary) <= JOURNAL_SUMMARY_MAX:
        return summary
    return summary[: JOURNAL_SUMMARY_MAX - 1].rstrip() + "…"


def add_wolf_journal_entry(
    wolf_id: int,
    event_key: str,
    summary: str,
    *,
    day: int | None = None,
    guild_id: int | None = None,
    conn: sqlite3.Connection | None = None,
) -> None:
    summary = _clip_journal_summary(summary)
    if not summary:
        return

    def _insert(c: sqlite3.Connection) -> None:
        c.execute(
            """
            INSERT INTO wolf_journal_entries (wolf_id, event_key, summary, day, guild_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (wolf_id, event_key, summary, day, guild_id),
        )

    if conn is not None:
        _insert(conn)
    else:
        with get_db() as c:
            _insert(c)


def get_wolf_journal_event_keys(wolf_id: int) -> set[str]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT event_key FROM wolf_journal_entries WHERE wolf_id = ?",
            (wolf_id,),
        ).fetchall()
        return {str(r["event_key"]) for r in rows}


def add_wolf_journal_entry_if_new(
    wolf_id: int,
    event_key: str,
    summary: str,
    *,
    day: int | None = None,
    guild_id: int | None = None,
) -> bool:
    """Insert when this wolf does not already have the event_key. Returns True if inserted."""
    summary = _clip_journal_summary(summary)
    if not summary:
        return False
    with get_db() as conn:
        exists = conn.execute(
            """
            SELECT 1 FROM wolf_journal_entries
            WHERE wolf_id = ? AND event_key = ?
            LIMIT 1
            """,
            (wolf_id, event_key),
        ).fetchone()
        if exists:
            return False
        conn.execute(
            """
            INSERT INTO wolf_journal_entries (wolf_id, event_key, summary, day, guild_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (wolf_id, event_key, summary, day, guild_id),
        )
        return True


def upsert_wolf_journal_entry(
    wolf_id: int,
    event_key: str,
    summary: str,
    *,
    day: int | None = None,
    guild_id: int | None = None,
) -> None:
    """Insert or replace summary for a stable event_key (e.g. lore backfill refresh)."""
    summary = _clip_journal_summary(summary)
    if not summary:
        return
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT id FROM wolf_journal_entries
            WHERE wolf_id = ? AND event_key = ?
            LIMIT 1
            """,
            (wolf_id, event_key),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE wolf_journal_entries
                SET summary = ?, day = COALESCE(?, day), guild_id = COALESCE(?, guild_id)
                WHERE id = ?
                """,
                (summary, day, guild_id, row["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO wolf_journal_entries (wolf_id, event_key, summary, day, guild_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (wolf_id, event_key, summary, day, guild_id),
            )


def list_wolf_journal(
    wolf_id: int, *, limit: int = 200, chronological: bool = False
) -> list[sqlite3.Row]:
    limit = max(1, min(limit, 200))
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM wolf_journal_entries
            WHERE wolf_id = ?
            """,
            (wolf_id,),
        ).fetchall()
    if chronological:
        rows = sorted(rows, key=_journal_sort_key)
    else:
        rows = sorted(rows, key=_journal_sort_key, reverse=True)
    return rows[:limit]


def _journal_sort_key(row: sqlite3.Row) -> tuple:
    """In-game days first (oldest→newest), then pre-game den records at the end."""
    key = str(row["event_key"])
    day = row["day"]
    row_id = int(row["id"])

    if key.startswith("lore:") or key in ("born", "adopted"):
        sub = {"lore:backstory": 0, "lore:family": 1, "born": 2, "adopted": 3}.get(key, 9)
        return (2, 0, sub, row_id)

    game_day = int(day) if day is not None else 0
    if key == "registered":
        game_day = 0

    sub = {
        "registered": 0,
        "pack_joined": 1,
        "pack_left": 2,
        "bonded": 3,
        "blooded": 4,
        "rite_blooding": 5,
        "rite_naming": 6,
        "rite_mourning": 7,
    }.get(key, 10)
    if key.startswith("bond:"):
        sub = 20
    elif key.startswith("court:"):
        sub = 21
    elif key.startswith("family:"):
        sub = 22
    elif key == "died" or key.startswith("died"):
        sub = 99

    return (1, game_day, sub, row_id)


def format_journal_preview(wolf_id: int, *, limit: int = 5) -> str | None:
    rows = list_wolf_journal(wolf_id, limit=200, chronological=True)
    if not rows:
        return None
    preview = rows[-limit:]
    lines: list[str] = []
    for row in preview:
        day = row["day"]
        prefix = f"Day {day} · " if day is not None else ""
        lines.append(f"✦ {prefix}{row['summary']}")
    return "\n".join(lines)


def list_guild_active_wolves(discord_ids: list[int]) -> list[sqlite3.Row]:
    if not discord_ids:
        return []
    placeholders = ",".join("?" * len(discord_ids))
    with get_db() as conn:
        return conn.execute(
            f"""
            SELECT u.*
            FROM users u
            INNER JOIN account_progress ap
                ON ap.discord_id = u.discord_id AND ap.active_wolf_id = u.id
            WHERE u.discord_id IN ({placeholders})
              AND u.condition != 'dead'
            ORDER BY COALESCE(u.great_pack, 'zzz'), u.wolf_name COLLATE NOCASE
            """,
            discord_ids,
        ).fetchall()


def create_server_npc(
    guild_id: int,
    name: str,
    *,
    avatar_url: str | None = None,
    bio: str | None = None,
    prefix: str | None = None,
    suffix: str | None = None,
    created_by: int,
) -> int | None:
    name = name.strip()[:80]
    if not name:
        return None
    with get_db() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO server_npcs
                (guild_id, name, avatar_url, bio, proxy_prefix, proxy_suffix, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (guild_id, name, avatar_url, bio, prefix, suffix, created_by),
            )
            return int(cur.lastrowid)
        except sqlite3.IntegrityError:
            return None


def get_server_npc(guild_id: int, name: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM server_npcs
            WHERE guild_id = ? AND LOWER(name) = LOWER(?)
            """,
            (guild_id, name.strip()),
        ).fetchone()


def list_server_npcs(guild_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM server_npcs
            WHERE guild_id = ?
            ORDER BY name COLLATE NOCASE
            """,
            (guild_id,),
        ).fetchall()


def delete_server_npc(guild_id: int, name: str) -> bool:
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM server_npcs WHERE guild_id = ? AND LOWER(name) = LOWER(?)",
            (guild_id, name.strip()),
        )
        return cur.rowcount > 0


def match_proxy(discord_id: int, content: str) -> tuple[sqlite3.Row, str] | None:
    """Return (wolf, inner_text) if content matches a wolf's proxy tag, else None.

    Longest matching prefix+suffix wins so overlapping tags resolve predictably.
    """
    if not content:
        return None
    best: tuple[sqlite3.Row, str] | None = None
    best_len = -1
    for wolf in get_proxy_wolves(discord_id):
        prefix = wolf["proxy_prefix"] or ""
        suffix = wolf["proxy_suffix"] or ""
        if not prefix and not suffix:
            continue
        if prefix and not content.startswith(prefix):
            continue
        if suffix and not content.endswith(suffix):
            continue
        inner = content[len(prefix): len(content) - len(suffix) if suffix else None]
        # Require some inner text unless this is a bare/sticker proxy.
        score = len(prefix) + len(suffix)
        if score > best_len:
            best = (wolf, inner.strip())
            best_len = score
    return best


def get_possess_wolf_id(admin_discord_id: int) -> int | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT possess_wolf_id FROM account_progress WHERE discord_id = ?",
            (admin_discord_id,),
        ).fetchone()
    if not row or not row["possess_wolf_id"]:
        return None
    return int(row["possess_wolf_id"])


def get_possess_session(admin_discord_id: int) -> dict | None:
    """Return {wolf_id, wolf_name, owner_discord_id} when an admin is steering another wolf."""
    wolf_id = get_possess_wolf_id(admin_discord_id)
    if not wolf_id:
        return None
    wolf = get_user_by_id(wolf_id)
    if not wolf:
        clear_admin_possess(admin_discord_id)
        return None
    return {
        "wolf_id": wolf_id,
        "wolf_name": wolf["wolf_name"],
        "owner_discord_id": int(wolf["discord_id"]),
    }


def set_admin_possess(admin_discord_id: int, wolf_id: int) -> tuple[bool, str]:
    wolf = get_user_by_id(wolf_id)
    if not wolf:
        return False, "That wolf no longer exists."
    if int(wolf["discord_id"]) == admin_discord_id:
        return False, "That's your own wolf; use `/switchwolf` instead."
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO account_progress (discord_id) VALUES (?)",
            (admin_discord_id,),
        )
        conn.execute(
            "UPDATE account_progress SET possess_wolf_id = ? WHERE discord_id = ?",
            (wolf_id, admin_discord_id),
        )
    return True, f"Now steering **{wolf['wolf_name']}** (owner <@{wolf['discord_id']}>)."


def clear_admin_possess(admin_discord_id: int) -> tuple[bool, str]:
    session = get_possess_session(admin_discord_id)
    with get_db() as conn:
        conn.execute(
            "UPDATE account_progress SET possess_wolf_id = NULL WHERE discord_id = ?",
            (admin_discord_id,),
        )
    if not session:
        return False, "You are not possessing a wolf."
    return True, f"Released **{session['wolf_name']}**; back to your own wolves."


def resolve_possessed_wolf(
    admin_discord_id: int,
    player: int,
    wolf_name: str | None,
) -> tuple[sqlite3.Row | None, str | None]:
    """Pick a wolf row for /wolfadmin possess."""
    if wolf_name:
        wolf = find_user_wolf(player, wolf_name)
        if not wolf:
            return None, explain_wolf_not_found(player, wolf_name, player_label=f"<@{player}>")
        return wolf, None
    wolf = get_user(player)
    if not wolf:
        return None, f"<@{player}> has no active wolf."
    return wolf, None


def _backfill_rpg_stats(conn: sqlite3.Connection) -> None:
    """Map legacy strength/speed/stamina/scent to Basil attributes where customized."""
    from engine.character import compute_max_hp

    rows = conn.execute(
        "SELECT discord_id, strength, speed, stamina, scent FROM users"
    ).fetchall()
    for row in rows:
        if (
            row["strength"] == 10
            and row["speed"] == 10
            and row["stamina"] == 10
            and row["scent"] == 10
        ):
            continue
        attr_str = max(1, min(10, 5 + (row["strength"] - 10) // 2))
        attr_dex = max(1, min(10, 5 + (row["speed"] - 10) // 2))
        attr_con = max(1, min(10, 5 + (row["stamina"] - 10) // 2))
        attr_wis = max(1, min(10, 5 + (row["scent"] - 10) // 2))
        max_hp = compute_max_hp(attr_str, attr_con)
        conn.execute(
            """
            UPDATE users
            SET attr_str = ?, attr_dex = ?, attr_con = ?, attr_wis = ?,
                hp = ?, max_hp = ?
            WHERE discord_id = ?
            """,
            (attr_str, attr_dex, attr_con, attr_wis, max_hp, max_hp, row["discord_id"]),
        )


def register_user(
    discord_id: int,
    wolf_name: str,
    affiliation: str,
    wolf_role: str = "hunter",
    stats: dict | None = None,
    birth_sex: str | None = None,
    sexuality: str | None = None,
    *,
    age_months: int | None = None,
    set_active: bool = True,
    genetic_conditions: str | None = None,
    maw_belief: str | None = None,
) -> int:
    import json

    from engine.aging import proficiencies_for_role, resolve_register_age, sync_role_to_age
    from rpg_rules import ROLE_PROFICIENCIES
    from engine.character import compute_max_hp, default_stats_for_role

    from engine.maw_belief import resolve_register_maw_belief

    cleaned_name, name_err = validate_wolf_name_available(wolf_name)
    if name_err:
        raise ValueError(name_err)
    wolf_name = cleaned_name

    requested_role = wolf_role if wolf_role in ROLE_PROFICIENCIES else "hunter"
    months = resolve_register_age(requested_role, age_months)
    role = sync_role_to_age(months, requested_role)
    spread = stats or default_stats_for_role(role)
    max_hp = compute_max_hp(spread["attr_str"], spread["attr_con"])
    proficiencies = proficiencies_for_role(role)
    from engine.attraction import resolve_register_sexuality

    orient = resolve_register_sexuality(months, sexuality)
    pack_id, great_pack = _affiliation_fields(affiliation)
    genetics_json = genetic_conditions if genetic_conditions else "[]"
    belief = resolve_register_maw_belief(maw_belief, affiliation=affiliation)
    from config import ROLLOVER_TIMEZONE
    from engine.lunar import assign_birth_lunar_phase, rollover_now

    born_at = rollover_now(ROLLOVER_TIMEZONE)
    birth_lunar_phase = assign_birth_lunar_phase(born_at)
    now = utcnow()
    with get_db() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO users (
                    discord_id, wolf_name, pack_id, rank, great_pack, wolf_role,
                    birth_sex, sexuality, age_months, genetic_conditions, maw_belief,
                    attr_str, attr_dex, attr_con, attr_int, attr_cha, attr_wis,
                    skill_proficiencies, hp, max_hp,
                    birth_lunar_phase, last_lunar_aged_lunation,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    discord_id,
                    wolf_name.strip(),
                    pack_id,
                    "member",
                    great_pack,
                    role,
                    birth_sex,
                    orient,
                    months,
                    genetics_json,
                    belief,
                    spread["attr_str"],
                    spread["attr_dex"],
                    spread["attr_con"],
                    spread["attr_int"],
                    spread["attr_cha"],
                    spread["attr_wis"],
                    proficiencies,
                    max_hp,
                    max_hp,
                    birth_lunar_phase,
                    -1,
                    now,
                ),
            )
        except sqlite3.IntegrityError:
            raise ValueError(
                f"The name **{wolf_name}** is already taken by another wolf. "
                "Choose a different name."
            ) from None
        wolf_id = cursor.lastrowid
        conn.execute(
            "INSERT OR IGNORE INTO account_progress (discord_id) VALUES (?)",
            (discord_id,),
        )
        if set_active:
            conn.execute(
                "UPDATE account_progress SET active_wolf_id = ? WHERE discord_id = ?",
                (wolf_id, discord_id),
            )
        else:
            account = conn.execute(
                "SELECT active_wolf_id FROM account_progress WHERE discord_id = ?",
                (discord_id,),
            ).fetchone()
            if not account or not account["active_wolf_id"]:
                conn.execute(
                    "UPDATE account_progress SET active_wolf_id = ? WHERE discord_id = ?",
                    (wolf_id, discord_id),
                )
        if pack_id:
            _claim_pack_alpha_if_eligible(conn, pack_id, discord_id, role)
    if great_pack and great_pack in GREAT_PACKS:
        grant_great_pack_starting_herbs(wolf_id, great_pack)
    _apply_canonical_character_lore(discord_id, wolf_id, wolf_name.strip())
    _apply_canonical_character_traits(discord_id, wolf_id, wolf_name.strip())
    _apply_canonical_character_defaults(discord_id, wolf_id, wolf_name.strip())
    from engine.wolf_journal import log_registered

    log_registered(wolf_id, wolf_name.strip(), great_pack or affiliation)
    ensure_achievement_quests(discord_id, wolf_id)
    from engine.canonical_bonds import apply_canonical_bonds_for_wolf

    apply_canonical_bonds_for_wolf(wolf_id, refresh_notes=True)
    _apply_canonical_pronouns(discord_id, wolf_id, wolf_name.strip(), birth_sex=birth_sex)
    return wolf_id


def _apply_canonical_pronouns(discord_id: int, wolf_id: int, wolf_name: str, *, birth_sex: str | None = None) -> None:
    from engine.pronouns import resolve_wolf_pronouns

    pronouns = resolve_wolf_pronouns(wolf_name, birth_sex=birth_sex)
    if pronouns:
        set_wolf_identity(wolf_id, pronouns=pronouns)


def _apply_canonical_character_lore(discord_id: int, wolf_id: int, wolf_name: str) -> None:
    from engine.character_lore_data import CHARACTER_LORE_BY_NAME

    for key, lore_json in CHARACTER_LORE_BY_NAME.items():
        if key.lower() == wolf_name.lower():
            update_user(discord_id, wolf_id=wolf_id, character_lore=lore_json)
            break


def _apply_canonical_character_traits(discord_id: int, wolf_id: int, wolf_name: str) -> None:
    from engine.character_traits import canonical_traits_for_name, encode_character_traits

    traits = canonical_traits_for_name(wolf_name)
    if traits:
        update_user(discord_id, wolf_id=wolf_id, character_traits=encode_character_traits(traits))


def _apply_canonical_character_defaults(discord_id: int, wolf_id: int, wolf_name: str) -> None:
    import json

    from engine.aging import proficiencies_for_role
    from engine.character_traits import canonical_register_defaults_for_name

    defaults = canonical_register_defaults_for_name(wolf_name)
    if not defaults:
        return
    fields: dict = {}
    if "wolf_role" in defaults:
        role = defaults["wolf_role"]
        fields["wolf_role"] = role
        fields["skill_proficiencies"] = json.dumps(proficiencies_for_role(role))
    if "maw_belief" in defaults:
        fields["maw_belief"] = defaults["maw_belief"]
    if "size_class" in defaults:
        fields["size_class"] = defaults["size_class"]
    if fields:
        update_user(discord_id, wolf_id=wolf_id, **fields)


def backfill_canonical_character_sheet(
    user,
    *,
    force_lore: bool = False,
    force_traits: bool = False,
    force_defaults: bool = False,
    dry_run: bool = False,
) -> list[str]:
    """
    Apply canonical lore/traits/register defaults for a named character wolf.
    By default only fills empty lore/traits and unset default fields.
    Returns human-readable change lines (empty when nothing to do).
    """
    from engine.character_lore_data import CHARACTER_LORE_BY_NAME
    from engine.character_traits import (
        canonical_register_defaults_for_name,
        canonical_traits_for_name,
        encode_character_traits,
    )
    from engine.aging import proficiencies_for_role

    import json

    def _field(key: str, default=None):
        if hasattr(user, "keys") and key in user.keys():
            return user[key]
        if isinstance(user, dict):
            return user.get(key, default)
        return default

    wolf_name = (_field("wolf_name") or "").strip()
    wolf_id = int(_field("id") or 0)
    discord_id = int(_field("discord_id") or 0)
    if not wolf_name or not wolf_id or not discord_id:
        return []

    canonical_key = None
    for key in CHARACTER_LORE_BY_NAME:
        if key.lower() == wolf_name.lower():
            canonical_key = key
            break
    if not canonical_key:
        return []

    changes: list[str] = []
    updates: dict = {}

    lore_raw = _field("character_lore")
    if force_lore or not lore_raw:
        updates["character_lore"] = CHARACTER_LORE_BY_NAME[canonical_key]
        changes.append("lore")

    traits = canonical_traits_for_name(wolf_name)
    traits_raw = _field("character_traits")
    if traits and (force_traits or not traits_raw):
        updates["character_traits"] = encode_character_traits(traits)
        changes.append("traits")

    defaults = canonical_register_defaults_for_name(wolf_name) or {}
    if "wolf_role" in defaults:
        role = defaults["wolf_role"]
        current_role = _field("wolf_role") or "hunter"
        if force_defaults or current_role == "hunter":
            if current_role != role or force_defaults:
                updates["wolf_role"] = role
                updates["skill_proficiencies"] = json.dumps(proficiencies_for_role(role))
                if current_role != role:
                    changes.append(f"role -> {role}")

    if "maw_belief" in defaults:
        belief = defaults["maw_belief"]
        current_belief = _field("maw_belief")
        if force_defaults or not current_belief:
            if current_belief != belief or force_defaults:
                updates["maw_belief"] = belief
                if current_belief != belief:
                    changes.append(f"maw_belief -> {belief}")

    if "size_class" in defaults:
        size = defaults["size_class"]
        current_size = (_field("size_class") or "").strip()
        if force_defaults or not current_size:
            if current_size != size or force_defaults:
                updates["size_class"] = size
                if current_size != size:
                    changes.append(f"size_class -> {size}")

    if updates and not dry_run:
        update_user(discord_id, wolf_id=wolf_id, **updates)
    elif not updates:
        return []
    return changes


def update_user(discord_id: int, wolf_id: int | None = None, **fields) -> None:
    if not fields:
        return
    wid = wolf_id or _resolve_wolf_id(discord_id)
    if not wid:
        return
    columns = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [wid]
    with get_db() as conn:
        conn.execute(f"UPDATE users SET {columns} WHERE id = ?", values)


def update_user_by_id(wolf_id: int, **fields) -> None:
    if not fields or not wolf_id:
        return
    columns = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [wolf_id]
    with get_db() as conn:
        conn.execute(f"UPDATE users SET {columns} WHERE id = ?", values)


def set_quarantined(discord_id: int, quarantined: bool, *, wolf_id: int | None = None) -> None:
    update_user(discord_id, wolf_id=wolf_id, quarantined=1 if quarantined else 0)


def set_wolf_dormant(wolf_id: int, dormant: bool) -> None:
    """
    Dormant wolves (admin-held NPCs nobody is actively playing) are exempt
    from the mood/hunger/thirst decay applied on /rollover; see
    _decay_vitals_on_rollover. Cleared automatically when a wolf is
    transferred to a new owner via reassign_wolf_owner.
    """
    update_user_by_id(wolf_id, dormant=1 if dormant else 0)


def list_pack_quarantined(pack_id: int) -> list:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM users
            WHERE pack_id = ? AND quarantined = 1
              AND condition NOT IN ('dead', 'dying')
            ORDER BY wolf_name COLLATE NOCASE
            """,
            (pack_id,),
        ).fetchall()


def add_bones(discord_id: int, amount: int, *, wolf_id: int | None = None) -> None:
    wid = wolf_id or _resolve_wolf_id(discord_id)
    if not wid:
        return
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET bones = bones + ? WHERE id = ?",
            (amount, wid),
        )


def deduct_bones(discord_id: int, amount: int) -> bool:
    if amount <= 0:
        return True
    wid = _resolve_wolf_id(discord_id)
    if not wid:
        return False
    with get_db() as conn:
        user = conn.execute(
            "SELECT bones FROM users WHERE id = ?", (wid,)
        ).fetchone()
        if not user or user["bones"] < amount:
            return False
        conn.execute(
            "UPDATE users SET bones = bones - ? WHERE id = ?",
            (amount, wid),
        )
        return True


def transfer_bones(from_id: int, to_id: int, amount: int) -> bool:
    if amount <= 0:
        return False
    from_wid = _resolve_wolf_id(from_id)
    to_wid = _resolve_wolf_id(to_id)
    if not from_wid or not to_wid:
        return False
    with get_db() as conn:
        sender = conn.execute(
            "SELECT bones FROM users WHERE id = ?", (from_wid,)
        ).fetchone()
        if not sender or sender["bones"] < amount:
            return False
        conn.execute(
            "UPDATE users SET bones = bones - ? WHERE id = ?",
            (amount, from_wid),
        )
        conn.execute(
            "UPDATE users SET bones = bones + ? WHERE id = ?",
            (amount, to_wid),
        )
        return True


def get_leaderboard(limit: int = 10) -> list[sqlite3.Row]:
    from engine.test_accounts import is_test_leaderboard_user

    with get_db() as conn:
        rows = conn.execute(
            "SELECT discord_id, wolf_name, bones FROM users ORDER BY bones DESC",
        ).fetchall()
    clean = [r for r in rows if not is_test_leaderboard_user(r["discord_id"], r["wolf_name"])]
    return clean[:limit]


def get_hall_of_fame(limit: int = 10) -> list[sqlite3.Row]:
    from engine.test_accounts import is_test_hall_account, is_test_wolf_name

    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT discord_id, legacy_score, prestige_tier, total_retirements
            FROM account_progress
            ORDER BY legacy_score DESC
            """,
        ).fetchall()
    clean: list[sqlite3.Row] = []
    for row in rows:
        if is_test_hall_account(row["discord_id"]):
            continue
        user = get_user(row["discord_id"])
        if user and is_test_wolf_name(user["wolf_name"]):
            continue
        clean.append(row)
    return clean[:limit]


def purge_test_accounts() -> list[str]:
    """
    Remove unit-test wolves and their account_progress rows from the live database.
    Returns wolf names removed.
    """
    from engine.test_accounts import is_test_discord_id, is_test_wolf_name

    removed: list[str] = []
    with get_db() as conn:
        rows = conn.execute("SELECT id, discord_id, wolf_name FROM users").fetchall()
        purge_ids: set[int] = set()
        for row in rows:
            if is_test_discord_id(row["discord_id"]) or is_test_wolf_name(row["wolf_name"]):
                purge_ids.add(int(row["discord_id"]))
                removed.append(row["wolf_name"])

        for discord_id in purge_ids:
            wolves = conn.execute(
                "SELECT id FROM users WHERE discord_id = ?", (discord_id,)
            ).fetchall()
            for wolf in wolves:
                wid = wolf["id"]
                conn.execute("DELETE FROM inventory WHERE wolf_id = ?", (wid,))
                conn.execute(
                    "DELETE FROM user_quests WHERE wolf_id = ? OR (wolf_id IS NULL AND discord_id = ?)",
                    (wid, discord_id),
                )
                conn.execute("DELETE FROM users WHERE id = ?", (wid,))
            conn.execute("DELETE FROM account_progress WHERE discord_id = ?", (discord_id,))
            conn.execute("DELETE FROM retired_wolves WHERE discord_id = ?", (discord_id,))
            conn.execute("DELETE FROM chat_xp_claims WHERE discord_id = ?", (discord_id,))

    return sorted(set(removed))


def rename_wolf(
    discord_id: int,
    wolf_name: str,
    *,
    wolf_id: int | None = None,
) -> str | None:
    wid = wolf_id or _resolve_wolf_id(discord_id)
    if not wid:
        return "not_registered"
    cleaned, err = validate_wolf_name_available(wolf_name, exclude_wolf_id=wid)
    if err:
        return f"name:{err}"
    update_user(discord_id, wolf_id=wid, wolf_name=cleaned)
    return None


def set_great_pack(discord_id: int, great_pack: str) -> None:
    """Legacy alias; use assign_pack_affiliation."""
    assign_pack_affiliation(discord_id, great_pack)


def _affiliation_fields(affiliation: str) -> tuple[int | None, str | None]:
    """Return (pack_id, great_pack key) for register."""
    if affiliation == LONER_KEY:
        return None, None
    if affiliation == ROGUE_KEY:
        return None, ROGUE_KEY
    if affiliation not in GREAT_PACKS:
        return None, None
    pack = get_pack_by_key(affiliation)
    if not pack:
        return None, None
    return pack["id"], affiliation


def _claim_pack_alpha_if_eligible(
    conn: sqlite3.Connection,
    pack_id: int,
    discord_id: int,
    wolf_role: str,
) -> None:
    """Set packs.alpha_id when the wolf's role is Alpha and the seat is vacant."""
    if wolf_role != "alpha":
        return
    conn.execute(
        "UPDATE packs SET alpha_id = ? WHERE id = ? AND alpha_id IS NULL",
        (discord_id, pack_id),
    )


def _promote_pack_alpha(conn: sqlite3.Connection, pack_id: int, exclude_id: int | None = None) -> None:
    base = "SELECT id, discord_id FROM users WHERE pack_id = ?"
    if exclude_id:
        base += " AND discord_id != ?"
    alpha_query = base + " AND wolf_role = 'alpha' ORDER BY standing DESC, created_at ASC LIMIT 1"
    fallback_query = base + " ORDER BY standing DESC, created_at ASC LIMIT 1"
    params = (pack_id, exclude_id) if exclude_id else (pack_id,)
    successor = conn.execute(alpha_query, params).fetchone()
    if not successor:
        successor = conn.execute(fallback_query, params).fetchone()
    if successor:
        conn.execute(
            "UPDATE packs SET alpha_id = ? WHERE id = ?",
            (successor["discord_id"], pack_id),
        )
    else:
        conn.execute("UPDATE packs SET alpha_id = NULL WHERE id = ?", (pack_id,))


def assign_pack_affiliation(discord_id: int, affiliation: str) -> str | None:
    """
    Join a Great Pack, switch packs, or go loner.
    Returns error message or None on success.
    """
    if affiliation not in GREAT_PACKS and affiliation not in (LONER_KEY, ROGUE_KEY):
        return "Unknown pack affiliation."

    user = get_user(discord_id)
    if not user:
        return "Not registered."

    wolf_id = user["id"]
    old_great_pack = user["great_pack"] if "great_pack" in user.keys() else None
    old_pack_id = user["pack_id"]
    with get_db() as conn:
        if old_pack_id:
            old_pack = conn.execute(
                "SELECT * FROM packs WHERE id = ?", (old_pack_id,)
            ).fetchone()
            if old_pack and old_pack["alpha_id"] == discord_id:
                _promote_pack_alpha(conn, old_pack_id, exclude_id=discord_id)

        if affiliation in (LONER_KEY, ROGUE_KEY):
            conn.execute(
                """
                UPDATE users
                SET great_pack = ?, pack_id = NULL
                WHERE id = ?
                """,
                (None if affiliation == LONER_KEY else ROGUE_KEY, wolf_id),
            )
            new_key = None if affiliation == LONER_KEY else ROGUE_KEY
            from engine.wolf_journal import log_pack_change

            log_pack_change(wolf_id, user["wolf_name"], old_great_pack, new_key)
            return None

        pack = conn.execute(
            "SELECT * FROM packs WHERE key = ?", (affiliation,)
        ).fetchone()
        if not pack:
            return "That Great Pack is not set up yet. Restart the bot."

        wolf_role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
        conn.execute(
            """
            UPDATE users
            SET great_pack = ?, pack_id = ?
            WHERE id = ?
            """,
            (affiliation, pack["id"], wolf_id),
        )
        _claim_pack_alpha_if_eligible(conn, pack["id"], discord_id, wolf_role)
    if not old_great_pack and affiliation in GREAT_PACKS:
        grant_great_pack_starting_herbs(wolf_id, affiliation)
    from engine.wolf_journal import log_pack_change

    log_pack_change(wolf_id, user["wolf_name"], old_great_pack, affiliation)
    return None


def get_user_affiliation(user) -> str:
    gp = user["great_pack"] if "great_pack" in user.keys() else None
    if gp == ROGUE_KEY:
        return ROGUE_KEY
    if gp and gp in GREAT_PACKS:
        return gp
    return LONER_KEY


def count_pack_members(pack_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE pack_id = ?", (pack_id,)
        ).fetchone()
        return row["c"] if row else 0


def delete_wolf_profile(discord_id: int) -> str:
    """
    Remove the active wolf profile. Keeps account_progress (prestige/legacy).
    Returns: ok | not_registered | alpha_transfer
    """
    user = get_user(discord_id)
    if not user:
        return "not_registered"

    wolf_id = user["id"]
    with get_db() as conn:
        pack_id = user["pack_id"]
        if pack_id:
            pack = conn.execute("SELECT * FROM packs WHERE id = ?", (pack_id,)).fetchone()
            members = conn.execute(
                "SELECT COUNT(*) AS c FROM users WHERE pack_id = ?", (pack_id,)
            ).fetchone()["c"]
            is_great_pack = pack and "key" in pack.keys() and pack["key"] in GREAT_PACKS
            if pack and pack["alpha_id"] == discord_id and members > 1 and not is_great_pack:
                return "alpha_transfer"
            if pack and pack["alpha_id"] == discord_id and members > 1 and is_great_pack:
                _promote_pack_alpha(conn, pack_id, exclude_id=discord_id)
            if members <= 1 and pack and not is_great_pack:
                conn.execute(
                    "DELETE FROM wars WHERE attacker_pack_id = ? OR defender_pack_id = ?",
                    (pack_id, pack_id),
                )
                conn.execute(
                    "UPDATE territories SET owner_pack_id = NULL WHERE owner_pack_id = ?",
                    (pack_id,),
                )
                conn.execute("DELETE FROM packs WHERE id = ?", (pack_id,))
            elif pack and pack["alpha_id"] == discord_id and not is_great_pack:
                conn.execute(
                    "UPDATE packs SET alpha_id = NULL WHERE id = ?",
                    (pack_id,),
                )

        conn.execute("DELETE FROM inventory WHERE wolf_id = ?", (wolf_id,))
        conn.execute(
            "DELETE FROM user_quests WHERE wolf_id = ? OR (wolf_id IS NULL AND discord_id = ?)",
            (wolf_id, discord_id),
        )
        partner_wolf_id = user["bonded_mate_id"] if "bonded_mate_id" in user.keys() else None
        conn.execute("UPDATE users SET bonded_mate_id = NULL WHERE bonded_mate_id = ?", (wolf_id,))
        if partner_wolf_id:
            conn.execute(
                "UPDATE users SET bonded_mate_id = NULL WHERE id = ?",
                (partner_wolf_id,),
            )
        conn.execute("DELETE FROM users WHERE id = ?", (wolf_id,))

        remaining = conn.execute(
            "SELECT id FROM users WHERE discord_id = ? ORDER BY id ASC LIMIT 1",
            (discord_id,),
        ).fetchone()
        if remaining:
            conn.execute(
                "UPDATE account_progress SET active_wolf_id = ? WHERE discord_id = ?",
                (remaining["id"], discord_id),
            )
        else:
            conn.execute(
                "UPDATE account_progress SET active_wolf_id = NULL WHERE discord_id = ?",
                (discord_id,),
            )

    return "ok"


# --- Account / prestige ---


def get_account(discord_id: int) -> sqlite3.Row:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM account_progress WHERE discord_id = ?", (discord_id,)
        ).fetchone()
        if row:
            return row
        conn.execute(
            "INSERT INTO account_progress (discord_id) VALUES (?)",
            (discord_id,),
        )
        return conn.execute(
            "SELECT * FROM account_progress WHERE discord_id = ?", (discord_id,)
        ).fetchone()


def is_kickstarter_backer(discord_id: int) -> bool:
    account = get_account(discord_id)
    return bool(int(account["kickstarter_backer"])) if "kickstarter_backer" in account.keys() else False


def grant_kickstarter_backer(discord_id: int) -> bool:
    """Mark account as Kickstarter backer. Returns True if newly granted."""
    get_account(discord_id)
    with get_db() as conn:
        row = conn.execute(
            "SELECT kickstarter_backer FROM account_progress WHERE discord_id = ?",
            (discord_id,),
        ).fetchone()
        if row and int(row["kickstarter_backer"]):
            return False
        conn.execute(
            "UPDATE account_progress SET kickstarter_backer = 1 WHERE discord_id = ?",
            (discord_id,),
        )
    return True


def revoke_kickstarter_backer(discord_id: int) -> bool:
    get_account(discord_id)
    with get_db() as conn:
        row = conn.execute(
            "SELECT kickstarter_backer FROM account_progress WHERE discord_id = ?",
            (discord_id,),
        ).fetchone()
        if not row or not int(row["kickstarter_backer"]):
            return False
        conn.execute(
            "UPDATE account_progress SET kickstarter_backer = 0 WHERE discord_id = ?",
            (discord_id,),
        )
    return True


def _recalculate_prestige(conn: sqlite3.Connection, discord_id: int) -> None:
    from engine.prestige import calculate_tier

    account = conn.execute(
        "SELECT * FROM account_progress WHERE discord_id = ?", (discord_id,)
    ).fetchone()
    if not account:
        return
    new_tier = calculate_tier(account)
    conn.execute(
        "UPDATE account_progress SET prestige_tier = ? WHERE discord_id = ?",
        (new_tier, discord_id),
    )


def add_legacy(discord_id: int, amount: int) -> None:
    if amount <= 0:
        return
    with get_db() as conn:
        get_account(discord_id)
        conn.execute(
            "UPDATE account_progress SET legacy_score = legacy_score + ? WHERE discord_id = ?",
            (amount, discord_id),
        )
        _recalculate_prestige(conn, discord_id)


def record_quest_complete(discord_id: int, reward_bones: int, standing_reward: int) -> None:
    from engine.prestige import legacy_from_quest

    legacy = legacy_from_quest(reward_bones, standing_reward)
    with get_db() as conn:
        get_account(discord_id)
        conn.execute(
            """
            UPDATE account_progress
            SET total_quests = total_quests + 1,
                legacy_score = legacy_score + ?
            WHERE discord_id = ?
            """,
            (legacy, discord_id),
        )
        _recalculate_prestige(conn, discord_id)


def record_hunt(discord_id: int) -> None:
    with get_db() as conn:
        get_account(discord_id)
        conn.execute(
            "UPDATE account_progress SET total_hunts = total_hunts + 1 WHERE discord_id = ?",
            (discord_id,),
        )
        _recalculate_prestige(conn, discord_id)


def get_completed_quest_count(discord_id: int) -> int:
    wolf_id = _resolve_wolf_id(discord_id)
    if not wolf_id:
        return 0
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM user_quests
            WHERE wolf_id = ? AND status = 'completed'
            """,
            (wolf_id,),
        ).fetchone()
        return row["c"] if row else 0


def retire_wolf(discord_id: int) -> tuple[int, int] | None:
    """Returns (legacy_gained, new_prestige_tier) or None if not registered."""
    from engine.prestige import legacy_from_retirement, calculate_tier

    user = get_user(discord_id)
    if not user:
        return None

    quests_done = get_completed_quest_count(discord_id)
    legacy_gain = legacy_from_retirement(user["standing"], user["bones"], quests_done)
    now = utcnow()

    with get_db() as conn:
        get_account(discord_id)
        conn.execute(
            """
            INSERT INTO retired_wolves (discord_id, wolf_name, great_pack, legacy_contribution, retired_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (discord_id, user["wolf_name"], user["great_pack"], legacy_gain, now),
        )
        conn.execute(
            """
            UPDATE account_progress
            SET legacy_score = legacy_score + ?,
                total_retirements = total_retirements + 1
            WHERE discord_id = ?
            """,
            (legacy_gain, discord_id),
        )
        _recalculate_prestige(conn, discord_id)
        account = conn.execute(
            "SELECT prestige_tier FROM account_progress WHERE discord_id = ?",
            (discord_id,),
        ).fetchone()

    return legacy_gain, account["prestige_tier"]


def get_retired_wolves(discord_id: int, limit: int = 10) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT wolf_name, great_pack, legacy_contribution, retired_at
            FROM retired_wolves
            WHERE discord_id = ?
            ORDER BY retired_at DESC
            LIMIT ?
            """,
            (discord_id, limit),
        ).fetchall()


# --- Packs ---


def get_pack(pack_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM packs WHERE id = ?", (pack_id,)).fetchone()


def get_pack_by_key(key: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM packs WHERE key = ?", (key,)).fetchone()


def get_pack_by_name(name: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM packs WHERE name = ? COLLATE NOCASE", (name.strip(),)
        ).fetchone()


def create_pack(name: str, alpha_id: int) -> int:
    now = utcnow()
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO packs (name, alpha_id, created_at) VALUES (?, ?, ?)",
            (name.strip(), alpha_id, now),
        )
        return cursor.lastrowid


def rename_pack(pack_id: int, name: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE packs SET name = ? WHERE id = ?",
            (name.strip(), pack_id),
        )


def set_pack_tax_rate(pack_id: int, rate: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE packs SET tax_rate = ? WHERE id = ?",
            (rate, pack_id),
        )


def add_pack_treasury(pack_id: int, amount: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE packs SET treasury = treasury + ? WHERE id = ?",
            (amount, pack_id),
        )


def deduct_pack_treasury(pack_id: int, amount: int) -> bool:
    if amount <= 0:
        return False
    with get_db() as conn:
        pack = conn.execute(
            "SELECT treasury FROM packs WHERE id = ?", (pack_id,)
        ).fetchone()
        if not pack or int(pack["treasury"]) < amount:
            return False
        conn.execute(
            "UPDATE packs SET treasury = treasury - ? WHERE id = ?",
            (amount, pack_id),
        )
        return True


def claim_daily_stipend(discord_id: int, pack_id: int, amount: int) -> bool:
    """Pay daily stipend from pack treasury to the active wolf (atomic)."""
    if amount <= 0:
        return False
    wid = _resolve_wolf_id(discord_id)
    if not wid:
        return False
    with get_db() as conn:
        user = conn.execute(
            "SELECT pack_id FROM users WHERE id = ?", (wid,)
        ).fetchone()
        if not user or user["pack_id"] != pack_id:
            return False
        pack = conn.execute(
            "SELECT treasury FROM packs WHERE id = ?", (pack_id,)
        ).fetchone()
        if not pack or pack["treasury"] < amount:
            return False
        conn.execute(
            "UPDATE packs SET treasury = treasury - ? WHERE id = ?",
            (amount, pack_id),
        )
        conn.execute(
            "UPDATE users SET bones = bones + ? WHERE id = ?",
            (amount, wid),
        )
        return True


def raid_pack_treasury(discord_id: int, victim_pack_id: int, amount: int) -> int:
    """Steal up to amount from a rival pack treasury into the active wolf's bones."""
    if amount <= 0:
        return 0
    wid = _resolve_wolf_id(discord_id)
    if not wid:
        return 0
    with get_db() as conn:
        pack = conn.execute(
            "SELECT treasury FROM packs WHERE id = ?", (victim_pack_id,)
        ).fetchone()
        if not pack or pack["treasury"] <= 0:
            return 0
        take = min(amount, int(pack["treasury"]))
        conn.execute(
            "UPDATE packs SET treasury = treasury - ? WHERE id = ?",
            (take, victim_pack_id),
        )
        conn.execute(
            "UPDATE users SET bones = bones + ? WHERE id = ?",
            (take, wid),
        )
        return take


def transfer_to_pack_treasury(discord_id: int, pack_id: int, amount: int) -> bool:
    if amount <= 0:
        return False
    wid = _resolve_wolf_id(discord_id)
    if not wid:
        return False
    ready_keys: list[str] = []
    with get_db() as conn:
        user = conn.execute(
            "SELECT bones, pack_id FROM users WHERE id = ?", (wid,)
        ).fetchone()
        if not user or user["pack_id"] != pack_id or user["bones"] < amount:
            return False
        conn.execute(
            "UPDATE users SET bones = bones - ? WHERE id = ?",
            (amount, wid),
        )
        conn.execute(
            "UPDATE packs SET treasury = treasury + ? WHERE id = ?",
            (amount, pack_id),
        )
        ready_keys = _increment_deposit_quest_progress_conn(conn, wid, amount)
    _auto_complete_ready_quests(discord_id, ready_keys)
    return True


def transfer_from_pack_treasury(discord_id: int, pack_id: int, amount: int) -> bool:
    if amount <= 0:
        return False
    wid = _resolve_wolf_id(discord_id)
    if not wid:
        return False
    with get_db() as conn:
        user = conn.execute(
            "SELECT pack_id FROM users WHERE id = ?", (wid,)
        ).fetchone()
        pack = conn.execute(
            "SELECT treasury FROM packs WHERE id = ?", (pack_id,)
        ).fetchone()
        if not user or not pack or user["pack_id"] != pack_id or pack["treasury"] < amount:
            return False
        conn.execute(
            "UPDATE packs SET treasury = treasury - ? WHERE id = ?",
            (amount, pack_id),
        )
        conn.execute(
            "UPDATE users SET bones = bones + ? WHERE id = ?",
            (amount, wid),
        )
        return True


# --- World ---


def get_world(guild_id: int) -> sqlite3.Row:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM world_state WHERE guild_id = ?", (guild_id,)
        ).fetchone()
        if row:
            return row
        now = utcnow()
        conn.execute(
            """
            INSERT INTO world_state (guild_id, day_number, season, weather, time_of_day, last_rollover)
            VALUES (?, 1, 'spring', 'clear', 'dawn', ?)
            """,
            (guild_id, now),
        )
        return conn.execute(
            "SELECT * FROM world_state WHERE guild_id = ?", (guild_id,)
        ).fetchone()


def get_plot_phase(guild_id: int) -> int:
    world = get_world(guild_id)
    if "plot_phase" not in world.keys():
        return 0
    return int(world["plot_phase"])


def set_plot_phase(guild_id: int, phase: int) -> sqlite3.Row:
    from engine.plot_blinking import PLOT_MAX_PHASE

    get_world(guild_id)
    phase = max(0, min(PLOT_MAX_PHASE, int(phase)))
    with get_db() as conn:
        conn.execute(
            "UPDATE world_state SET plot_phase = ? WHERE guild_id = ?",
            (phase, guild_id),
        )
    return get_world(guild_id)


def advance_plot_phase(guild_id: int) -> tuple[int, sqlite3.Row]:
    current = get_plot_phase(guild_id)
    new_phase = min(current + 1, 12)
    world = set_plot_phase(guild_id, new_phase)
    return new_phase, world


def den_news_dm_sent_for_day(guild_id: int, day: int) -> bool:
    """True if sunrise den-news DMs already went out for this in-game day."""
    world = get_world(guild_id)
    if "last_den_news_dm_day" not in world.keys():
        return False
    return int(world["last_den_news_dm_day"]) >= int(day)


def mark_den_news_dm_sent(guild_id: int, day: int) -> None:
    with get_db() as conn:
        conn.execute(
            """
            UPDATE world_state SET last_den_news_dm_day = ?
            WHERE guild_id = ? AND last_den_news_dm_day < ?
            """,
            (int(day), guild_id, int(day)),
        )


def save_world(
    guild_id: int,
    *,
    day_number: int,
    season: str,
    weather: str,
    time_of_day: str,
) -> sqlite3.Row:
    now = utcnow()
    with get_db() as conn:
        conn.execute(
            """
            UPDATE world_state
            SET day_number = ?, season = ?, weather = ?, time_of_day = ?, last_rollover = ?
            WHERE guild_id = ?
            """,
            (day_number, season, weather, time_of_day, now, guild_id),
        )
        return conn.execute(
            "SELECT * FROM world_state WHERE guild_id = ?", (guild_id,)
        ).fetchone()


def real_world_season(dt: datetime) -> str:
    """Northern Hemisphere meteorological season for a real-world date.

    Mar-May spring, Jun-Aug summer, Sep-Nov autumn, Dec-Feb winter. Used at
    rollover so the den's season tracks the real calendar unless a server
    admin has pinned it with `/world action:setseason`.
    """
    month = dt.month
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


def set_season_override(guild_id: int, season: str | None) -> None:
    """Pin the den's season (admin); pass None to return to real-calendar sync."""
    with get_db() as conn:
        conn.execute(
            "UPDATE world_state SET season_override = ? WHERE guild_id = ?",
            (season, guild_id),
        )


def _random_weather() -> str:
    return random.choice(WEATHER_TYPES)


def _age_wolves_on_rollover(months: int, rollover_at: datetime | None = None) -> tuple[list[dict], int]:
    from config import LUNAR_BIRTH_AGING, MAX_WOLF_AGE_MOONS, ROLLOVER_TIMEZONE
    from engine.lunar import current_lunation_number, rollover_now, wolf_should_age_this_rollover
    from engine.aging import check_age_milestones, proficiencies_for_role, role_after_milestones

    milestones: list[dict] = []
    wolves_aged = 0
    if months <= 0:
        return milestones, wolves_aged
    if rollover_at is None:
        rollover_at = rollover_now(ROLLOVER_TIMEZONE)
    lunation = current_lunation_number(rollover_at)
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM users").fetchall()
        for user in rows:
            if not wolf_should_age_this_rollover(
                user, rollover_at, lunar_birth_aging=LUNAR_BIRTH_AGING
            ):
                continue
            old_age = user["age_months"] if "age_months" in user.keys() else 24
            new_age = min(MAX_WOLF_AGE_MOONS, old_age + months)
            if new_age == old_age:
                continue
            role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
            new_role = role_after_milestones(new_age, role)
            if new_role != role:
                profs = proficiencies_for_role(new_role)
                conn.execute(
                    """
                    UPDATE users
                    SET age_months = ?, wolf_role = ?, skill_proficiencies = ?,
                        last_lunar_aged_lunation = ?
                    WHERE id = ?
                    """,
                    (new_age, new_role, profs, lunation, user["id"]),
                )
            else:
                conn.execute(
                    """
                    UPDATE users
                    SET age_months = ?, last_lunar_aged_lunation = ?
                    WHERE id = ?
                    """,
                    (new_age, lunation, user["id"]),
                )
            wolves_aged += 1
            if check_age_milestones(old_age, new_age, role) or new_age != old_age:
                milestones.append(
                    {
                        "wolf_name": user["wolf_name"],
                        "old_age": old_age,
                        "new_age": new_age,
                        "old_role": role,
                        "new_role": new_role,
                    }
                )
    return milestones, wolves_aged


def set_wolf_age_moons(wolf_id: int, new_age: int) -> dict | None:
    """
    Set a wolf's age in moons. Returns dict with old_age, new_age, old_role, new_role, notes.
    """
    from config import MAX_WOLF_AGE_MOONS
    from engine.aging import check_age_milestones, proficiencies_for_role, sync_role_to_age
    from engine.attraction import PUP_SEXUALITY, is_pup_age

    new_age = max(0, min(MAX_WOLF_AGE_MOONS, int(new_age)))
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (wolf_id,)).fetchone()
        if not user:
            return None
        old_age = user["age_months"] if "age_months" in user.keys() else 24
        role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
        new_role = sync_role_to_age(new_age, role)
        notes = check_age_milestones(old_age, new_age, role)
        profs = proficiencies_for_role(new_role)
        if is_pup_age(new_age):
            conn.execute(
                """
                UPDATE users
                SET age_months = ?, wolf_role = ?, skill_proficiencies = ?, sexuality = ?
                WHERE id = ?
                """,
                (new_age, new_role, profs, PUP_SEXUALITY, wolf_id),
            )
        else:
            conn.execute(
                """
                UPDATE users SET age_months = ?, wolf_role = ?, skill_proficiencies = ?
                WHERE id = ?
                """,
                (new_age, new_role, profs, wolf_id),
            )
    return {
        "old_age": old_age,
        "new_age": new_age,
        "old_role": role,
        "new_role": new_role,
        "notes": notes,
    }


def _decay_vitals_on_rollover() -> None:
    """Mood, hunger, and thirst slip each sunrise; dormant wolves are exempt."""
    from config import (
        HUNGER_ROLLOVER_DECAY,
        HUNGER_SICK_EXTRA_DECAY,
        MOOD_ROLLOVER_DECAY,
        THIRST_ROLLOVER_DECAY,
        THIRST_SICK_EXTRA_DECAY,
    )

    with get_db() as conn:
        conn.execute(
            """
            UPDATE users
            SET mood = MAX(0, mood - ?),
                hunger = MAX(0, hunger - ?),
                thirst = MAX(0, thirst - ?),
                raccoon_sells_today = 0,
                raccoon_buys_today = 0,
                drinks_today = 0
            WHERE dormant = 0 AND (disease IS NULL OR disease = '')
            """,
            (MOOD_ROLLOVER_DECAY, HUNGER_ROLLOVER_DECAY, THIRST_ROLLOVER_DECAY),
        )
        conn.execute(
            """
            UPDATE users
            SET mood = MAX(0, mood - ?),
                hunger = MAX(0, hunger - ?),
                thirst = MAX(0, thirst - ?),
                raccoon_sells_today = 0,
                raccoon_buys_today = 0,
                drinks_today = 0
            WHERE dormant = 0 AND disease IS NOT NULL AND disease != ''
            """,
            (
                MOOD_ROLLOVER_DECAY * 2,
                HUNGER_ROLLOVER_DECAY + HUNGER_SICK_EXTRA_DECAY,
                THIRST_ROLLOVER_DECAY + THIRST_SICK_EXTRA_DECAY,
            ),
        )


def _decay_mood_on_rollover() -> None:
    """Legacy alias; vitals decay includes mood."""
    _decay_vitals_on_rollover()


def _long_rest_all_wolves_on_rollover(day_number: int) -> None:
    """Living wolves sleep through the rollover; same as a long rest."""
    from engine.conditions import apply_long_rest_benefits

    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM users
            WHERE condition NOT IN ('dead', 'dying')
            """
        ).fetchall()
        for user in rows:
            rest = apply_long_rest_benefits(user)
            from engine.herb_buffs import tick_buffs_for_rollover

            tick_fields = tick_buffs_for_rollover(user, day_number)
            conn.execute(
                """
                UPDATE users
                SET hp = ?, exhaustion = ?, mood = ?,
                    herb_heals_today = 0, herb_treats_today = 0,
                    last_rest_day = ?,
                    jaw_meal_shield = 0, smoke_debuff = 0, cough_suppressed = 0,
                    hunger_exhaustion_skip = 0, march_exhaustion_skip = 0,
                    disease_save_buff = ?, disease_save_buff_days = ?, herb_buffs = ?
                WHERE id = ?
                """,
                (
                    rest["hp"],
                    rest["exhaustion"],
                    rest["mood"],
                    day_number,
                    tick_fields.get(
                        "disease_save_buff",
                        int(user["disease_save_buff"]) if "disease_save_buff" in user.keys() else 0,
                    ),
                    tick_fields.get(
                        "disease_save_buff_days",
                        int(user["disease_save_buff_days"]) if "disease_save_buff_days" in user.keys() else 0,
                    ),
                    tick_fields.get("herb_buffs", user["herb_buffs"] if "herb_buffs" in user.keys() else "{}"),
                    user["id"],
                ),
            )


_global_wolf_rollover_keys: set[str] = set()


def _rollover_global_key(rollover_at: datetime, new_day: int, tz_name: str) -> str:
    """One global wolf tick per in-game day per calendar sunrise (multi-guild dedup)."""
    local_date = rollover_at.astimezone(ZoneInfo(tz_name)).date().isoformat()
    return f"{local_date}:{new_day}"


def perform_rollover(guild_id: int, rollover_at: datetime | None = None) -> tuple[sqlite3.Row, dict]:
    from config import LUNAR_BIRTH_AGING, ROLLOVER_TIMEZONE
    from engine.lunar import BIRTH_LUNAR_LABELS, active_lunar_phase, lunar_phase_label, rollover_now

    if rollover_at is None:
        rollover_at = rollover_now(ROLLOVER_TIMEZONE)
    state = get_world(guild_id)
    old_season = state["season"]
    new_day = state["day_number"] + 1
    override = state["season_override"] if "season_override" in state.keys() else None
    new_season = override if override in SEASONS else real_world_season(rollover_at)
    new_weather = _random_weather()
    global_key = _rollover_global_key(rollover_at, new_day, ROLLOVER_TIMEZONE)
    run_global = global_key not in _global_wolf_rollover_keys
    if run_global:
        _global_wolf_rollover_keys.add(global_key)
    _pay_territory_bonuses(guild_id)
    condition_notes: list = []
    age_milestones: list = []
    wolves_aged: list = []
    needs_crisis: dict = {"deaths": [], "collapses": []}
    vitals_exhaustion: list = []
    mood_exhaustion: list = []
    if run_global:
        condition_notes = _progress_conditions(guild_id)
        with get_db() as conn:
            from engine.disease_spread import apply_disease_spread_on_rollover

            spread_notes = apply_disease_spread_on_rollover(conn)
        condition_notes.extend(spread_notes)
        _long_rest_all_wolves_on_rollover(new_day)
        from engine.character_traits import decay_skill_strain_on_rollover

        decay_skill_strain_on_rollover()
        with get_db() as conn:
            from engine.nursing import apply_unfed_pup_penalty_on_rollover

            unfed_notes = apply_unfed_pup_penalty_on_rollover(conn, state["day_number"])
        if unfed_notes:
            condition_notes.extend(unfed_notes)
        with get_db() as conn:
            from engine.restricted_herbs import apply_restricted_hoard_audit_on_rollover

            hoard_audit = apply_restricted_hoard_audit_on_rollover(conn)
        if hoard_audit:
            condition_notes.extend(
                {
                    "wolf_name": row["wolf_name"],
                    "discord_id": row.get("discord_id"),
                    "line": row["note"],
                }
                for row in hoard_audit
            )
        _decay_vitals_on_rollover()
        with get_db() as conn:
            from engine.nursing import apply_reproduction_vitals_drain_on_rollover

            repro_notes = apply_reproduction_vitals_drain_on_rollover(conn)
        if repro_notes:
            condition_notes.extend(repro_notes)
        with get_db() as conn:
            from engine.pack_food import auto_feed_wolves_on_rollover

            auto_feed_wolves_on_rollover(conn, new_day, new_season)
        with get_db() as conn:
            from engine.disease_contract import apply_mental_illness_rollover

            mental_notes = apply_mental_illness_rollover(conn, new_day)
        if mental_notes:
            needs_crisis["mental_notes"] = mental_notes
        from engine.exhaustion_effects import (
            apply_exhaustion_death_on_rollover,
            apply_mood_exhaustion_on_rollover,
            clamp_hp_for_exhaustion_on_rollover,
        )
        from engine.vitals import apply_needs_crisis_on_rollover, apply_needs_exhaustion_on_rollover

        with get_db() as conn:
            vitals_exhaustion = apply_needs_exhaustion_on_rollover(conn)
            mood_exhaustion = apply_mood_exhaustion_on_rollover(conn)
            clamp_hp_for_exhaustion_on_rollover(conn)
            exhaustion_deaths = apply_exhaustion_death_on_rollover(
                conn, guild_id=guild_id, day=new_day
            )
            needs_crisis = apply_needs_crisis_on_rollover(
                conn, guild_id=guild_id, day=new_day
            )
        needs_crisis["vitals_exhaustion"] = vitals_exhaustion + mood_exhaustion
        if exhaustion_deaths:
            needs_crisis["deaths"].extend(exhaustion_deaths)
        age_milestones, wolves_aged = _age_wolves_on_rollover(MOONS_PER_ROLLOVER, rollover_at)
        from engine.aging import apply_old_age_deaths_on_rollover

        with get_db() as conn:
            old_age_deaths = apply_old_age_deaths_on_rollover(
                conn, guild_id=guild_id, day=new_day
            )
        needs_crisis["old_age_deaths"] = old_age_deaths
        needs_crisis["deaths"].extend(old_age_deaths)
        grief_notes: list[dict] = []
        for entry in needs_crisis.get("deaths", []):
            grief = entry.pop("mate_grief", None) if isinstance(entry, dict) else None
            if grief:
                grief_notes.append(grief)
        if grief_notes:
            needs_crisis["grief_notes"] = grief_notes
        with get_db() as conn:
            from engine.season_rollover import apply_season_rollover_effects

            season_lines, cache_notes = apply_season_rollover_effects(
                conn, guild_id, new_season
            )
        if season_lines:
            needs_crisis.setdefault("season_notes", []).extend(season_lines)
        if cache_notes:
            needs_crisis.setdefault("food_cache", []).extend(cache_notes)
    expel_wolves_below_standing_threshold(guild_id)
    close_prey_piles_for_guild(guild_id)
    close_collab_hunts_for_guild(guild_id)
    close_collab_patrols_for_guild(guild_id)
    prey_rot_notes = rot_prey_stacks(guild_id, new_day)
    pack_prey_rot_notes = rot_pack_prey_stacks(guild_id, new_day)
    prey_spoilage = prey_rot_notes + pack_prey_rot_notes
    if prey_spoilage:
        needs_crisis["prey_spoilage"] = prey_spoilage
    rot_herb_stacks(guild_id, new_day)
    from engine.patron import process_invite_rollovers

    process_invite_rollovers(guild_id, new_day)
    from engine.rollover_news import collect_den_news

    needs_crisis["den_news"] = collect_den_news(new_day, age_milestones)
    from engine.den_rhythm import apply_bond_relation_pressure, apply_den_rhythm_unity
    from engine.pack_raid_ecology import collect_raid_den_news

    expire_pack_raid_alerts_before(guild_id, new_day)
    rhythm_notes = apply_den_rhythm_unity(guild_id, new_day - 1)
    bond_notes = apply_bond_relation_pressure(guild_id, new_day)
    raid_news = collect_raid_den_news(guild_id, new_day - 1)
    if rhythm_notes or bond_notes or raid_news:
        pack_events = needs_crisis.setdefault("den_news", {}).setdefault("pack_events", [])
        pack_events.extend(rhythm_notes + bond_notes + raid_news)
    needs_crisis["condition_notes"] = condition_notes
    from engine.forager_perk import apply_forager_daily_herbs_on_rollover

    with get_db() as conn:
        needs_crisis["forager_herbs"] = apply_forager_daily_herbs_on_rollover(conn, new_day, guild_id=guild_id)
    expire_pending_stillborn_before_day(new_day)
    expired_pacts = expire_cat_pacts_for_day(guild_id, new_day)
    expired_wolf_treaties = expire_wolf_treaties_for_day(guild_id, new_day)
    with get_db() as conn:
        from engine.sacred_visits import apply_sacred_visit_reminders

        sacred_notes = apply_sacred_visit_reminders(conn, new_day)
    plot_phase = get_plot_phase(guild_id)
    if sacred_notes:
        if plot_phase == 5:
            needs_crisis.setdefault("sacred_notes", []).extend(sacred_notes + sacred_notes)
        else:
            needs_crisis.setdefault("sacred_notes", []).extend(sacred_notes)
    if plot_phase > 0:
        from engine.plot_blinking import apply_plot_rollover_effects, plot_den_news_line

        with get_db() as conn:
            plot_notes = apply_plot_rollover_effects(conn, guild_id, new_day, plot_phase)
        if plot_notes:
            needs_crisis.setdefault("plot_notes", []).extend(plot_notes)
        plot_news = plot_den_news_line(plot_phase, new_day)
        if plot_news:
            needs_crisis.setdefault("den_news", {}).setdefault("pack_events", []).append(
                plot_news
            )
    from engine.healer_refusal import healer_refusal_reminder, rot_lung_outbreak_news

    rot_lines: list[str] = []
    healer_lines: list[str] = []
    with get_db() as conn:
        pack_rows = conn.execute(
            "SELECT DISTINCT pack_id FROM users WHERE pack_id IS NOT NULL"
        ).fetchall()
        for row in pack_rows:
            pid = row["pack_id"]
            outbreak = rot_lung_outbreak_news(pid)
            if outbreak:
                pack = get_pack(pid)
                label = pack["name"] if pack else "Pack"
                rot_lines.append(f"**{label}**: {outbreak}")
            for medic in get_pack_den_wolves(pid):
                from engine.role_features import is_full_medic

                if is_full_medic(medic):
                    rem = healer_refusal_reminder(medic, pack_id=pid)
                    if rem:
                        healer_lines.append(f"**{medic['wolf_name']}**: dying packmate needs care.")
    if rot_lines:
        needs_crisis.setdefault("season_notes", []).extend(rot_lines)
    if healer_lines:
        needs_crisis.setdefault("den_news", {}).setdefault("pack_events", []).extend(
            healer_lines[:6]
        )
    if expired_pacts:
        needs_crisis.setdefault("expired_cat_pacts", expired_pacts)
    if expired_wolf_treaties:
        needs_crisis.setdefault("expired_wolf_treaties", expired_wolf_treaties)
    if old_season != new_season:
        from engine.cat_gathering import apply_gathering_on_season_change

        with get_db() as conn:
            gathering_notes = apply_gathering_on_season_change(
                conn, guild_id, new_season, new_day
            )
        if gathering_notes:
            needs_crisis.setdefault("season_notes", []).extend(gathering_notes)
    sky = active_lunar_phase(rollover_at)
    needs_crisis["lunar_phase_label"] = (
        BIRTH_LUNAR_LABELS[sky] if sky else lunar_phase_label(rollover_at)
    )
    needs_crisis["wolves_aged"] = wolves_aged
    needs_crisis["lunar_birth_aging"] = LUNAR_BIRTH_AGING
    world = save_world(
        guild_id,
        day_number=new_day,
        season=new_season,
        weather=new_weather,
        time_of_day="dawn",
    )
    return world, needs_crisis


def _progress_conditions(guild_id: int) -> list[dict]:
    """Daily disease and injury progression for all wolves. Returns rollover notes."""
    from engine.conditions import progress_disease, progress_injuries, progress_mental_overlay
    from engine.exhaustion_effects import consume_march_exhaustion_skip
    from engine.herb_buffs import get_buffs

    notes: list[dict] = []
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE disease IS NOT NULL AND disease != ''"
        ).fetchall()
        for user in rows:
            outcome = progress_disease(user)
            if outcome.get("changed"):
                new_hp = user["hp"]
                exhaustion = user["exhaustion"]
                disease = outcome["new_stage"]
                if outcome.get("cleared"):
                    disease = None
                    conn.execute("UPDATE users SET quarantined = 0 WHERE id = ?", (user["id"],))
                if outcome.get("hp_loss"):
                    new_hp = max(0, user["hp"] - outcome["hp_loss"])
                if outcome.get("exhaustion_gain"):
                    gain = outcome["exhaustion_gain"]
                    gain, _ = consume_march_exhaustion_skip(conn, user, gain)
                    from engine.exhaustion_effects import consume_pain_exhaustion_skip

                    gain, _ = consume_pain_exhaustion_skip(conn, user, gain)
                    if gain:
                        exhaustion = min(6, user["exhaustion"] + gain)
                if outcome.get("hunger_loss"):
                    conn.execute(
                        "UPDATE users SET hunger = MAX(0, hunger - ?) WHERE id = ?",
                        (outcome["hunger_loss"], user["id"]),
                    )
                if outcome.get("thirst_loss"):
                    conn.execute(
                        "UPDATE users SET thirst = MAX(0, thirst - ?) WHERE id = ?",
                        (outcome["thirst_loss"], user["id"]),
                    )
                if outcome.get("mood_loss"):
                    conn.execute(
                        "UPDATE users SET mood = MAX(0, mood - ?) WHERE id = ?",
                        (outcome["mood_loss"], user["id"]),
                    )
                if outcome.get("consume_disease_buff"):
                    from engine.herb_buffs import consume_disease_save_after_roll

                    buff_updates = consume_disease_save_after_roll(user)
                    if buff_updates:
                        conn.execute(
                            "UPDATE users SET disease_save_buff = ? WHERE id = ?",
                            (buff_updates.get("disease_save_buff", 0), user["id"]),
                        )
                cond = user["condition"] if "condition" in user.keys() else "healthy"
                collapsed = new_hp <= 0 and cond not in ("dead", "dying")
                if collapsed:
                    conn.execute(
                        """
                        UPDATE users SET disease = ?, hp = 0, exhaustion = ?,
                            condition = 'dying', death_save_round = 1,
                            death_save_fails = 0, death_save_successes = 0,
                            herb_heals_today = 0
                        WHERE id = ?
                        """,
                        (disease, exhaustion, user["id"]),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE users SET disease = ?, hp = ?, exhaustion = ?,
                            herb_heals_today = 0
                        WHERE id = ?
                        """,
                        (disease, new_hp, exhaustion, user["id"]),
                    )
                for line in outcome.get("messages", []):
                    notes.append(
                        {
                            "wolf_name": user["wolf_name"],
                            "discord_id": user["discord_id"],
                            "line": line,
                        }
                    )
                if collapsed:
                    notes.append(
                        {
                            "wolf_name": user["wolf_name"],
                            "discord_id": user["discord_id"],
                            "line": "collapsed to **0 HP**; use **`/medic action:deathsaves`**.",
                        }
                    )
                user = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()

            if user and get_buffs(user).get("mental_disease"):
                overlay = progress_mental_overlay(user)
                if overlay.get("changed"):
                    if overlay.get("mood_loss"):
                        conn.execute(
                            "UPDATE users SET mood = MAX(0, mood - ?) WHERE id = ?",
                            (overlay["mood_loss"], user["id"]),
                        )
                    buff_fields = overlay.get("buff_fields") or {}
                    if buff_fields.get("herb_buffs") is not None:
                        conn.execute(
                            "UPDATE users SET herb_buffs = ? WHERE id = ?",
                            (buff_fields["herb_buffs"], user["id"]),
                        )
                    for line in overlay.get("messages", []):
                        notes.append(
                            {
                                "wolf_name": user["wolf_name"],
                                "discord_id": user["discord_id"],
                                "line": line,
                            }
                        )

        inj_rows = conn.execute(
            """
            SELECT * FROM users
            WHERE active_injuries IS NOT NULL
              AND active_injuries != ''
              AND active_injuries != '[]'
            """
        ).fetchall()
        for user in inj_rows:
            world_day = int(
                conn.execute(
                    "SELECT day_number FROM world_state WHERE guild_id = ?",
                    (guild_id,),
                ).fetchone()["day_number"]
            )
            outcome = progress_injuries(user, day=world_day)
            if not outcome.get("changed"):
                continue
            new_hp = user["hp"]
            exhaustion = user["exhaustion"]
            if outcome.get("hp_loss"):
                new_hp = max(0, user["hp"] - outcome["hp_loss"])
            if outcome.get("exhaustion_gain"):
                gain = outcome["exhaustion_gain"]
                gain, _ = consume_march_exhaustion_skip(conn, user, gain)
                from engine.exhaustion_effects import consume_pain_exhaustion_skip

                gain, _ = consume_pain_exhaustion_skip(conn, user, gain)
                if gain:
                    exhaustion = min(6, user["exhaustion"] + gain)
            cond = user["condition"] if "condition" in user.keys() else "healthy"
            collapsed = new_hp <= 0 and cond not in ("dead", "dying")
            if collapsed:
                conn.execute(
                    """
                    UPDATE users SET hp = 0, exhaustion = ?,
                        condition = 'dying', death_save_round = 1,
                        death_save_fails = 0, death_save_successes = 0
                    WHERE id = ?
                    """,
                    (exhaustion, user["id"]),
                )
            else:
                conn.execute(
                    "UPDATE users SET hp = ?, exhaustion = ? WHERE id = ?",
                    (new_hp, exhaustion, user["id"]),
                )
            for line in outcome.get("messages", []):
                notes.append(
                    {
                        "wolf_name": user["wolf_name"],
                        "discord_id": user["discord_id"],
                        "line": line,
                    }
                )
            if collapsed:
                notes.append(
                    {
                        "wolf_name": user["wolf_name"],
                        "discord_id": user["discord_id"],
                        "line": "collapsed to **0 HP**; use **`/medic action:deathsaves`**.",
                    }
                )
    from engine.chronic_conditions import apply_elder_chronic_on_rollover
    from engine.disease_contract import apply_pending_milk_fever_on_rollover

    world = get_world(guild_id)
    with get_db() as conn:
        for entry in apply_pending_milk_fever_on_rollover(conn, world["day_number"]):
            notes.append(
                {
                    "wolf_name": entry["wolf_name"],
                    "discord_id": entry["discord_id"],
                    "line": entry["line"],
                }
            )
        for entry in apply_elder_chronic_on_rollover(conn):
            notes.append(
                {
                    "wolf_name": entry["wolf_name"],
                    "discord_id": entry["discord_id"],
                    "line": entry["message"],
                }
            )
    return notes


def _pay_territory_bonuses(guild_id: int) -> None:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT owner_pack_id, SUM(daily_bonus) AS bonus
            FROM territories
            WHERE guild_id = ? AND owner_pack_id IS NOT NULL
            GROUP BY owner_pack_id
            """,
            (guild_id,),
        ).fetchall()
        for row in rows:
            conn.execute(
                "UPDATE packs SET treasury = treasury + ? WHERE id = ?",
                (row["bonus"], row["owner_pack_id"]),
            )


# --- Shop & inventory ---


def get_all_items() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute("SELECT * FROM items ORDER BY price ASC").fetchall()


def get_shop_items() -> list[sqlite3.Row]:
    """Items sold at the trading post (excludes foraged herbs at price 0)."""
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM items WHERE price > 0 ORDER BY price ASC, name ASC"
        ).fetchall()


def get_item_by_key(key: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM items WHERE key = ? COLLATE NOCASE", (key.strip(),)
        ).fetchone()


def get_item_by_id(item_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()


def _inventory_qty_conn(conn: sqlite3.Connection, wolf_id: int, item_id: int) -> int:
    row = conn.execute(
        "SELECT quantity FROM inventory WHERE wolf_id = ? AND item_id = ?",
        (wolf_id, item_id),
    ).fetchone()
    return int(row["quantity"]) if row else 0


def _grant_item_conn(
    conn: sqlite3.Connection, wolf_id: int, item_id: int, quantity: int
) -> None:
    if quantity <= 0:
        return
    row = conn.execute(
        "SELECT quantity FROM inventory WHERE wolf_id = ? AND item_id = ?",
        (wolf_id, item_id),
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE inventory SET quantity = quantity + ? WHERE wolf_id = ? AND item_id = ?",
            (quantity, wolf_id, item_id),
        )
    else:
        conn.execute(
            "INSERT INTO inventory (wolf_id, item_id, quantity) VALUES (?, ?, ?)",
            (wolf_id, item_id, quantity),
        )


def _consume_item_conn(
    conn: sqlite3.Connection, wolf_id: int, item_id: int, quantity: int
) -> bool:
    if quantity <= 0:
        return True
    row = conn.execute(
        "SELECT quantity FROM inventory WHERE wolf_id = ? AND item_id = ?",
        (wolf_id, item_id),
    ).fetchone()
    if not row or row["quantity"] < quantity:
        return False
    if row["quantity"] == quantity:
        conn.execute(
            "DELETE FROM inventory WHERE wolf_id = ? AND item_id = ?",
            (wolf_id, item_id),
        )
    else:
        conn.execute(
            "UPDATE inventory SET quantity = quantity - ? WHERE wolf_id = ? AND item_id = ?",
            (quantity, wolf_id, item_id),
        )
    return True


def _transfer_bones_conn(
    conn: sqlite3.Connection, from_wid: int, to_wid: int, amount: int
) -> bool:
    if amount <= 0:
        return True
    sender = conn.execute(
        "SELECT bones FROM users WHERE id = ?", (from_wid,)
    ).fetchone()
    if not sender or sender["bones"] < amount:
        return False
    conn.execute(
        "UPDATE users SET bones = bones - ? WHERE id = ?",
        (amount, from_wid),
    )
    conn.execute(
        "UPDATE users SET bones = bones + ? WHERE id = ?",
        (amount, to_wid),
    )
    return True


def transfer_bones_by_wolf_id(from_wolf_id: int, to_wolf_id: int, amount: int) -> bool:
    if amount <= 0 or from_wolf_id == to_wolf_id:
        return False
    with get_db() as conn:
        return _transfer_bones_conn(conn, from_wolf_id, to_wolf_id, amount)


def transfer_item_by_wolf_id(
    from_wolf_id: int, to_wolf_id: int, item_id: int, quantity: int
) -> bool:
    if quantity <= 0 or from_wolf_id == to_wolf_id:
        return False
    with get_db() as conn:
        return _move_item_conn(conn, from_wolf_id, to_wolf_id, item_id, quantity)


def _move_item_conn(
    conn: sqlite3.Connection,
    from_wid: int,
    to_wid: int,
    item_id: int,
    quantity: int,
) -> bool:
    if quantity <= 0:
        return True
    if not _consume_item_conn(conn, from_wid, item_id, quantity):
        return False
    _grant_item_conn(conn, to_wid, item_id, quantity)
    return True


def transfer_item(
    from_discord_id: int, to_discord_id: int, item_id: int, quantity: int
) -> bool:
    if quantity <= 0:
        return False
    with get_db() as conn:
        from_wid = _resolve_wolf_id_conn(conn, from_discord_id)
        to_wid = _resolve_wolf_id_conn(conn, to_discord_id)
        if not from_wid or not to_wid or from_wid == to_wid:
            return False
        return _move_item_conn(conn, from_wid, to_wid, item_id, quantity)


TRADE_EXPIRE_SECONDS = 600


def cancel_pending_trades_for_user(discord_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            """
            UPDATE pending_trades
            SET status = 'cancelled'
            WHERE status = 'pending'
              AND (from_discord_id = ? OR to_discord_id = ?)
            """,
            (discord_id, discord_id),
        )


def create_pending_trade(
    from_discord_id: int,
    to_discord_id: int,
    *,
    from_item_id: int | None = None,
    from_item_qty: int = 0,
    from_bones: int = 0,
    to_item_id: int | None = None,
    to_item_qty: int = 0,
    to_bones: int = 0,
    message_id: int | None = None,
) -> int | None:
    cancel_pending_trades_for_user(from_discord_id)
    cancel_pending_trades_for_user(to_discord_id)
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pending_trades (
                from_discord_id, to_discord_id,
                from_item_id, from_item_qty, from_bones,
                to_item_id, to_item_qty, to_bones,
                status, created_at, message_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (
                from_discord_id,
                to_discord_id,
                from_item_id,
                from_item_qty,
                from_bones,
                to_item_id,
                to_item_qty,
                to_bones,
                utcnow(),
                message_id,
            ),
        )
        return cursor.lastrowid


def get_pending_trade(trade_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM pending_trades WHERE id = ?", (trade_id,)
        ).fetchone()


def set_pending_trade_message_id(trade_id: int, message_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE pending_trades SET message_id = ? WHERE id = ?",
            (message_id, trade_id),
        )


def decline_pending_trade(trade_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT status FROM pending_trades WHERE id = ?", (trade_id,)
        ).fetchone()
        if not row or row["status"] != "pending":
            return False
        conn.execute(
            "UPDATE pending_trades SET status = 'declined' WHERE id = ?",
            (trade_id,),
        )
        return True


def complete_pending_trade(trade_id: int) -> str:
    with get_db() as conn:
        trade = conn.execute(
            "SELECT * FROM pending_trades WHERE id = ?", (trade_id,)
        ).fetchone()
        if not trade:
            return "not_found"
        if trade["status"] != "pending":
            return "not_pending"

        created = datetime.fromisoformat(trade["created_at"])
        age = (datetime.now(timezone.utc) - created).total_seconds()
        if age > TRADE_EXPIRE_SECONDS:
            conn.execute(
                "UPDATE pending_trades SET status = 'expired' WHERE id = ?",
                (trade_id,),
            )
            return "expired"

        from_wid = _resolve_wolf_id_conn(conn, trade["from_discord_id"])
        to_wid = _resolve_wolf_id_conn(conn, trade["to_discord_id"])
        if not from_wid or not to_wid:
            return "not_registered"

        from_bones = int(trade["from_bones"])
        to_bones = int(trade["to_bones"])
        from_item_id = trade["from_item_id"]
        from_item_qty = int(trade["from_item_qty"])
        to_item_id = trade["to_item_id"]
        to_item_qty = int(trade["to_item_qty"])

        if from_bones > 0:
            row = conn.execute(
                "SELECT bones FROM users WHERE id = ?", (from_wid,)
            ).fetchone()
            if not row or row["bones"] < from_bones:
                return "insufficient_from"

        if from_item_id and from_item_qty > 0:
            if _inventory_qty_conn(conn, from_wid, from_item_id) < from_item_qty:
                return "insufficient_from"

        if to_bones > 0:
            row = conn.execute(
                "SELECT bones FROM users WHERE id = ?", (to_wid,)
            ).fetchone()
            if not row or row["bones"] < to_bones:
                return "insufficient_to"

        if to_item_id and to_item_qty > 0:
            if _inventory_qty_conn(conn, to_wid, to_item_id) < to_item_qty:
                return "insufficient_to"

        if from_bones > 0 and not _transfer_bones_conn(conn, from_wid, to_wid, from_bones):
            return "insufficient_from"
        if to_bones > 0 and not _transfer_bones_conn(conn, to_wid, from_wid, to_bones):
            return "insufficient_to"
        if from_item_id and from_item_qty > 0:
            if not _move_item_conn(conn, from_wid, to_wid, from_item_id, from_item_qty):
                return "insufficient_from"
        if to_item_id and to_item_qty > 0:
            if not _move_item_conn(conn, to_wid, from_wid, to_item_id, to_item_qty):
                return "insufficient_to"

        conn.execute(
            "UPDATE pending_trades SET status = 'completed' WHERE id = ?",
            (trade_id,),
        )
        return "ok"


def get_inventory(discord_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return []
        return conn.execute(
            """
            SELECT i.key, i.name, i.description, i.price, i.sell_price, inv.quantity
            FROM inventory inv
            JOIN items i ON i.id = inv.item_id
            WHERE inv.wolf_id = ? AND inv.quantity > 0
            ORDER BY i.name ASC
            """,
            (wolf_id,),
        ).fetchall()


def get_inventory_quantity(discord_id: int, item_id: int) -> int:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return 0
        return _inventory_qty_conn(conn, wolf_id, item_id)


def get_inventory_quantity_for_wolf(wolf_id: int, item_id: int) -> int:
    with get_db() as conn:
        return _inventory_qty_conn(conn, wolf_id, item_id)


def consume_item_for_wolf(wolf_id: int, item_id: int, quantity: int = 1) -> bool:
    with get_db() as conn:
        return _consume_item_conn(conn, wolf_id, item_id, quantity)


def buy_item(discord_id: int, item_id: int, price: int) -> bool:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return False
        user = conn.execute(
            "SELECT bones FROM users WHERE id = ?", (wolf_id,)
        ).fetchone()
        if not user or user["bones"] < price:
            return False
        conn.execute(
            "UPDATE users SET bones = bones - ? WHERE id = ?",
            (price, wolf_id),
        )
        existing = conn.execute(
            "SELECT quantity FROM inventory WHERE wolf_id = ? AND item_id = ?",
            (wolf_id, item_id),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE inventory SET quantity = quantity + 1 WHERE wolf_id = ? AND item_id = ?",
                (wolf_id, item_id),
            )
        else:
            conn.execute(
                "INSERT INTO inventory (wolf_id, item_id, quantity) VALUES (?, ?, 1)",
                (wolf_id, item_id),
            )
        return True


def sell_item(discord_id: int, item_id: int, sell_price: int) -> bool:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return False
        row = conn.execute(
            "SELECT quantity FROM inventory WHERE wolf_id = ? AND item_id = ?",
            (wolf_id, item_id),
        ).fetchone()
        if not row or row["quantity"] < 1:
            return False
        if row["quantity"] == 1:
            conn.execute(
                "DELETE FROM inventory WHERE wolf_id = ? AND item_id = ?",
                (wolf_id, item_id),
            )
        else:
            conn.execute(
                "UPDATE inventory SET quantity = quantity - 1 WHERE wolf_id = ? AND item_id = ?",
                (wolf_id, item_id),
            )
        conn.execute(
            "UPDATE users SET bones = bones + ? WHERE id = ?",
            (sell_price, wolf_id),
        )
        return True


# --- Quests ---


def get_quest_by_key(key: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM quests WHERE key = ? COLLATE NOCASE", (key.strip(),)
        ).fetchone()


def list_board_quests() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM quests
            WHERE quest_type IN ('static', 'unique', 'seasonal')
            ORDER BY difficulty, title
            """
        ).fetchall()


def create_quest(
    key: str,
    title: str,
    description: str,
    objective_type: str,
    objective_count: int,
    reward_bones: int,
    *,
    standing_reward: int = 0,
    quest_type: str = "static",
    difficulty: str = "easy",
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO quests
            (key, title, description, objective_type, objective_count,
             reward_bones, standing_reward, quest_type, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                key.strip().lower(),
                title.strip(),
                description.strip(),
                objective_type,
                objective_count,
                reward_bones,
                standing_reward,
                quest_type,
                difficulty,
            ),
        )
        return cursor.lastrowid


def delete_quest_by_key(key: str) -> bool:
    with get_db() as conn:
        quest = conn.execute(
            "SELECT id FROM quests WHERE key = ? COLLATE NOCASE", (key.strip(),)
        ).fetchone()
        if not quest:
            return False
        active = conn.execute(
            "SELECT 1 FROM user_quests WHERE quest_id = ? AND status = 'active'",
            (quest["id"],),
        ).fetchone()
        if active:
            return False
        conn.execute("DELETE FROM quests WHERE id = ?", (quest["id"],))
        conn.execute("DELETE FROM user_quests WHERE quest_id = ?", (quest["id"],))
        return True


def get_available_quests(discord_id: int, *, guild_id: int | None = None) -> list[sqlite3.Row]:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return []
        rows = conn.execute(
            """
            SELECT q.*
            FROM quests q
            WHERE q.quest_type IN ('static', 'unique', 'seasonal')
            AND q.required_role IS NULL
            AND NOT EXISTS (
                SELECT 1 FROM user_quests uq
                WHERE uq.quest_id = q.id AND uq.wolf_id = ?
                AND uq.status IN ('active', 'completed')
            )
            ORDER BY q.difficulty, q.title
            """,
            (wolf_id,),
        ).fetchall()
        if guild_id is not None:
            from engine.plot_quests import plot_quest_available

            rows = [q for q in rows if plot_quest_available(q["key"], guild_id)]
        return rows


def get_role_quests(discord_id: int) -> list[sqlite3.Row]:
    from engine.apprentice_roles import parent_role

    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return []
        user = conn.execute(
            "SELECT wolf_role, great_pack FROM users WHERE id = ?", (wolf_id,)
        ).fetchone()
        if not user:
            return []
        role = user["wolf_role"] or "hunter"
        pack = user["great_pack"]
        parent = parent_role(role)
        role_filter = (role,) if not parent else (role, parent)
        placeholders = ",".join("?" * len(role_filter))
        rows = conn.execute(
            f"""
            SELECT q.*
            FROM quests q
            WHERE q.required_role IN ({placeholders})
            AND NOT EXISTS (
                SELECT 1 FROM user_quests uq
                WHERE uq.quest_id = q.id AND uq.wolf_id = ?
                AND uq.status IN ('active', 'completed')
            )
            ORDER BY q.difficulty, q.title
            """,
            (*role_filter, wolf_id),
        ).fetchall()
        return [
            q
            for q in rows
            if not q["required_pack"] or q["required_pack"] == pack
        ]


def get_user_active_quests(discord_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return []
        return conn.execute(
            """
            SELECT uq.*, q.key AS quest_key, q.title, q.description,
                   q.objective_type, q.objective_count, q.reward_bones,
                   q.standing_reward, q.difficulty, q.quest_type
            FROM user_quests uq
            JOIN quests q ON q.id = uq.quest_id
            WHERE uq.wolf_id = ? AND uq.status = 'active'
            ORDER BY uq.accepted_at
            """,
            (wolf_id,),
        ).fetchall()


def get_user_questlog(discord_id: int, limit: int = 15) -> list[sqlite3.Row]:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return []
        return conn.execute(
            """
            SELECT uq.completed_at, q.key AS quest_key, q.title, q.reward_bones, q.difficulty
            FROM user_quests uq
            JOIN quests q ON q.id = uq.quest_id
            WHERE uq.wolf_id = ? AND uq.status = 'completed'
            ORDER BY uq.completed_at DESC
            LIMIT ?
            """,
            (wolf_id, limit),
        ).fetchall()


def has_completed_unique(discord_id: int, quest_id: int) -> bool:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return False
        row = conn.execute(
            """
            SELECT 1 FROM user_quests uq
            JOIN quests q ON q.id = uq.quest_id
            WHERE uq.wolf_id = ? AND uq.quest_id = ? AND uq.status = 'completed'
            """,
            (wolf_id, quest_id),
        ).fetchone()
        return row is not None


def _credit_daily_objectives_conn(
    conn: sqlite3.Connection, wolf_id: int, day: int, *, guild_id: int | None = None
) -> None:
    """If the wolf already did a daily activity this rollover, credit matching quests."""
    user = conn.execute("SELECT * FROM users WHERE id = ?", (wolf_id,)).fetchone()
    if not user or day <= 0:
        return
    if guild_id is not None:
        from engine.plot_quests import plot_quest_available
    done_today = {
        "forage": int(user["last_forage_day"]) >= day
        or int(user["last_verge_forage_day"] if "last_verge_forage_day" in user.keys() else 0)
        >= day,
        "hunt": int(user["last_hunt_day"]) >= day,
        "scavenge": int(user["last_scavenge_day"]) >= day,
        "track": int(user["last_track_day"]) >= day,
        "fishing": int(user["last_fishing_day"]) >= day,
        "sniff": int(user["last_sniff_day"] if "last_sniff_day" in user.keys() else 0) >= day,
        "patrol": int(user["last_patrol_day"] if "last_patrol_day" in user.keys() else 0) >= day,
        "explore": int(user["last_explore_day"] if "last_explore_day" in user.keys() else 0) >= day,
        "howl": int(user["last_howl_day"] if "last_howl_day" in user.keys() else 0) >= day,
        "crime": int(user["last_crime_day"] if "last_crime_day" in user.keys() else 0) >= day,
        "survey": int(user["last_survey_day"] if "last_survey_day" in user.keys() else 0) >= day,
    }
    for objective_type, completed in done_today.items():
        if not completed:
            continue
        rows = conn.execute(
            """
            SELECT uq.id, uq.progress, q.objective_count, q.key AS quest_key
            FROM user_quests uq
            JOIN quests q ON q.id = uq.quest_id
            WHERE uq.wolf_id = ? AND uq.status = 'active' AND q.objective_type = ?
            """,
            (wolf_id, objective_type),
        ).fetchall()
        for row in rows:
            if guild_id is not None and not plot_quest_available(row["quest_key"], guild_id):
                continue
            new_progress = min(int(row["progress"]) + 1, int(row["objective_count"]))
            conn.execute(
                "UPDATE user_quests SET progress = ? WHERE id = ?",
                (new_progress, row["id"]),
            )


def accept_quest(
    discord_id: int, quest_id: int, assigned_day: int = 0, *, guild_id: int | None = None
) -> bool:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return False
        active = conn.execute(
            """
            SELECT 1 FROM user_quests
            WHERE wolf_id = ? AND quest_id = ? AND status = 'active'
            """,
            (wolf_id, quest_id),
        ).fetchone()
        if active:
            return False
        conn.execute(
            """
            INSERT INTO user_quests (discord_id, wolf_id, quest_id, assigned_day, accepted_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (discord_id, wolf_id, quest_id, assigned_day, utcnow()),
        )
        if assigned_day > 0:
            _credit_daily_objectives_conn(conn, wolf_id, assigned_day, guild_id=guild_id)
        return True


def abandon_quest(discord_id: int, quest_key: str) -> bool:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return False
        quest = conn.execute(
            "SELECT id FROM quests WHERE key = ? COLLATE NOCASE", (quest_key.strip(),)
        ).fetchone()
        if not quest:
            return False
        cursor = conn.execute(
            """
            UPDATE user_quests SET status = 'abandoned'
            WHERE wolf_id = ? AND quest_id = ? AND status = 'active'
            """,
            (wolf_id, quest["id"]),
        )
        return cursor.rowcount > 0


def _auto_complete_ready_quests(discord_id: int, ready_keys: list[str]) -> list[sqlite3.Row]:
    """
    Call complete_quest for each key that just hit its objective count.
    Always called *after* the caller's own `with get_db()` block has closed,
    since complete_quest opens its own connection (nesting them deadlocks
    mid-transaction; see the herb-grant rollover bug this mirrors the fix for).
    """
    results = []
    for key in ready_keys:
        result = complete_quest(discord_id, key)
        if result:
            results.append(result)
    return results


def increment_quest_progress(
    discord_id: int,
    objective_type: str,
    amount: int = 1,
    *,
    wolf_id: int | None = None,
    guild_id: int | None = None,
) -> list[sqlite3.Row]:
    """Bump progress on matching active quests; auto-completes (and grants
    rewards for) any that just hit their objective count. Returns the
    completed quest result rows, if any."""
    wid_lookup = wolf_id or _resolve_wolf_id(discord_id)
    if wid_lookup:
        # One-time backfill for wolves registered before the achievement
        # system existed; called outside the block below to avoid nesting
        # get_db() connections (ensure_achievement_quests opens its own).
        ensure_achievement_quests(discord_id, wid_lookup)
    ready_keys: list[str] = []
    with get_db() as conn:
        wid = wolf_id or _resolve_wolf_id_conn(conn, discord_id)
        if not wid:
            return []
        rows = conn.execute(
            """
            SELECT uq.id, uq.progress, q.objective_count, q.key AS quest_key
            FROM user_quests uq
            JOIN quests q ON q.id = uq.quest_id
            WHERE uq.wolf_id = ? AND uq.status = 'active' AND q.objective_type = ?
            """,
            (wid, objective_type),
        ).fetchall()
        if guild_id is not None:
            from engine.plot_quests import plot_quest_available
        for row in rows:
            if guild_id is not None and not plot_quest_available(row["quest_key"], guild_id):
                continue
            new_progress = min(row["progress"] + amount, row["objective_count"])
            conn.execute(
                "UPDATE user_quests SET progress = ? WHERE id = ?",
                (new_progress, row["id"]),
            )
            if new_progress >= row["objective_count"]:
                ready_keys.append(row["quest_key"])
    return _auto_complete_ready_quests(discord_id, ready_keys)


def increment_quest_progress_by_keys(
    discord_id: int,
    quest_keys: tuple[str, ...] | list[str],
    amount: int = 1,
    *,
    wolf_id: int | None = None,
    guild_id: int | None = None,
) -> list[sqlite3.Row]:
    """Same as increment_quest_progress, but for an explicit set of quest keys."""
    if not quest_keys:
        return []
    ready_keys: list[str] = []
    with get_db() as conn:
        wid = wolf_id or _resolve_wolf_id_conn(conn, discord_id)
        if not wid:
            return []
        placeholders = ",".join("?" * len(quest_keys))
        rows = conn.execute(
            f"""
            SELECT uq.id, uq.progress, q.objective_count, q.key AS quest_key
            FROM user_quests uq
            JOIN quests q ON q.id = uq.quest_id
            WHERE uq.wolf_id = ? AND uq.status = 'active' AND q.key IN ({placeholders})
            """,
            (wid, *quest_keys),
        ).fetchall()
        if guild_id is not None:
            from engine.plot_quests import plot_quest_available
        for row in rows:
            if guild_id is not None and not plot_quest_available(row["quest_key"], guild_id):
                continue
            new_progress = min(row["progress"] + amount, row["objective_count"])
            conn.execute(
                "UPDATE user_quests SET progress = ? WHERE id = ?",
                (new_progress, row["id"]),
            )
            if new_progress >= row["objective_count"]:
                ready_keys.append(row["quest_key"])
    return _auto_complete_ready_quests(discord_id, ready_keys)


def _increment_deposit_quest_progress_conn(
    conn: sqlite3.Connection, wolf_id: int, amount: int
) -> list[str]:
    user = conn.execute(
        "SELECT deposit_progress FROM users WHERE id = ?", (wolf_id,)
    ).fetchone()
    if not user:
        return []
    total = user["deposit_progress"] + amount
    conn.execute(
        "UPDATE users SET deposit_progress = ? WHERE id = ?",
        (total, wolf_id),
    )
    rows = conn.execute(
        """
        SELECT uq.id, q.objective_count, q.key AS quest_key
        FROM user_quests uq
        JOIN quests q ON q.id = uq.quest_id
        WHERE uq.wolf_id = ? AND uq.status = 'active' AND q.objective_type = 'deposit'
        """,
        (wolf_id,),
    ).fetchall()
    ready_keys: list[str] = []
    for row in rows:
        progress = min(total, row["objective_count"])
        conn.execute(
            "UPDATE user_quests SET progress = ? WHERE id = ?",
            (progress, row["id"]),
        )
        if progress >= row["objective_count"]:
            ready_keys.append(row["quest_key"])
    return ready_keys


def increment_deposit_quest_progress(discord_id: int, amount: int) -> list[sqlite3.Row]:
    """Same auto-completion behavior as increment_quest_progress, for deposit quests."""
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return []
        ready_keys = _increment_deposit_quest_progress_conn(conn, wolf_id, amount)
    return _auto_complete_ready_quests(discord_id, ready_keys)


def get_active_quest_by_key(discord_id: int, quest_key: str) -> sqlite3.Row | None:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return None
        return conn.execute(
            """
            SELECT uq.*, q.key AS quest_key, q.title, q.objective_type, q.objective_count
            FROM user_quests uq
            JOIN quests q ON q.id = uq.quest_id
            WHERE uq.wolf_id = ? AND q.key = ? COLLATE NOCASE AND uq.status = 'active'
            """,
            (wolf_id, quest_key.strip()),
        ).fetchone()


def complete_quest(discord_id: int, quest_key: str | None = None) -> sqlite3.Row | None:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return None
        if quest_key:
            quest = conn.execute(
                "SELECT * FROM quests WHERE key = ? COLLATE NOCASE", (quest_key.strip(),)
            ).fetchone()
            if not quest:
                return None
            uq = conn.execute(
                """
                SELECT uq.*, q.key AS quest_key, q.title, q.reward_bones, q.standing_reward,
                       q.objective_count, q.objective_type, q.difficulty, q.quest_type
                FROM user_quests uq
                JOIN quests q ON q.id = uq.quest_id
                WHERE uq.wolf_id = ? AND uq.quest_id = ? AND uq.status = 'active'
                """,
                (wolf_id, quest["id"]),
            ).fetchone()
        else:
            uq = conn.execute(
                """
                SELECT uq.*, q.key AS quest_key, q.title, q.reward_bones, q.standing_reward,
                       q.objective_count, q.objective_type, q.difficulty, q.quest_type
                FROM user_quests uq
                JOIN quests q ON q.id = uq.quest_id
                WHERE uq.wolf_id = ? AND uq.status = 'active' AND uq.progress >= q.objective_count
                ORDER BY uq.accepted_at
                LIMIT 1
                """,
                (wolf_id,),
            ).fetchone()
        if not uq or uq["progress"] < uq["objective_count"]:
            return None
        conn.execute(
            """
            UPDATE user_quests SET status = 'completed', completed_at = ? WHERE id = ?
            """,
            (utcnow(), uq["id"]),
        )
        conn.execute(
            "UPDATE users SET bones = bones + ? WHERE id = ?",
            (uq["reward_bones"], wolf_id),
        )

    if uq["standing_reward"]:
        adjust_wolf_standing(discord_id, uq["standing_reward"])

    if "quest_type" in uq.keys() and uq["quest_type"] == "achievement":
        wolf = get_user_by_id(wolf_id)
        if wolf:
            from engine.wolf_journal import log_achievement

            log_achievement(wolf_id, wolf["wolf_name"], uq["title"])

    record_quest_complete(discord_id, uq["reward_bones"], uq["standing_reward"])
    user = get_user(discord_id)
    if user and user["pack_id"]:
        adjust_pack_unity(user["pack_id"], 1)

    from config import QUEST_SKILL_REWARDS
    from engine.quest_rewards import quest_xp_reward

    diff = uq["difficulty"] if "difficulty" in uq.keys() else None
    xp_gain = quest_xp_reward(uq["quest_key"], difficulty=diff)
    add_xp(discord_id, xp_gain)
    skill_reward = QUEST_SKILL_REWARDS.get(uq["quest_key"])
    if skill_reward:
        skill_key, rank_gain = skill_reward
        add_skill_rank(int(uq["wolf_id"]), skill_key, rank_gain, grant_proficiency=True)
    return uq


def ensure_daily_quests(discord_id: int, day: int) -> list[sqlite3.Row]:
    from config import DAILY_QUEST_TEMPLATES
    import random as rnd

    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return []
        existing = conn.execute(
            """
            SELECT uq.*, q.key AS quest_key, q.title, q.description,
                   q.objective_type, q.objective_count, q.reward_bones,
                   q.standing_reward, q.difficulty, q.quest_type
            FROM user_quests uq
            JOIN quests q ON q.id = uq.quest_id
            WHERE uq.wolf_id = ? AND q.quest_type = 'daily'
            AND uq.assigned_day = ? AND uq.status IN ('active', 'completed')
            """,
            (wolf_id, day),
        ).fetchall()
        if existing:
            return list(existing)

        for difficulty in ("easy", "medium", "hard"):
            pool = DAILY_QUEST_TEMPLATES[difficulty]
            key, title, desc, obj, count, reward = rnd.choice(pool)
            quest_key = f"{key}_{day}_{wolf_id}"
            conn.execute(
                """
                INSERT OR IGNORE INTO quests
                (key, title, description, objective_type, objective_count,
                 reward_bones, quest_type, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, 'daily', ?)
                """,
                (quest_key, title, desc, obj, count, reward, difficulty),
            )
            quest = conn.execute(
                "SELECT id FROM quests WHERE key = ?", (quest_key,)
            ).fetchone()
            conn.execute(
                """
                INSERT INTO user_quests (discord_id, wolf_id, quest_id, assigned_day, accepted_at, status)
                VALUES (?, ?, ?, ?, ?, 'active')
                """,
                (discord_id, wolf_id, quest["id"], day, utcnow()),
            )

        return conn.execute(
            """
            SELECT uq.*, q.key AS quest_key, q.title, q.description,
                   q.objective_type, q.objective_count, q.reward_bones,
                   q.standing_reward, q.difficulty, q.quest_type
            FROM user_quests uq
            JOIN quests q ON q.id = uq.quest_id
            WHERE uq.wolf_id = ? AND q.quest_type = 'daily' AND uq.assigned_day = ?
            """,
            (wolf_id, day),
        ).fetchall()


# --- Warfare ---


def get_territories(guild_id: int) -> list[sqlite3.Row]:
    ensure_territories(guild_id)
    with get_db() as conn:
        return conn.execute(
            """
            SELECT t.*, p.name AS owner_name
            FROM territories t
            LEFT JOIN packs p ON p.id = t.owner_pack_id
            WHERE t.guild_id = ?
            ORDER BY t.name
            """,
            (guild_id,),
        ).fetchall()


def get_territory_by_key(guild_id: int, key: str) -> sqlite3.Row | None:
    ensure_territories(guild_id)
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM territories WHERE guild_id = ? AND key = ? COLLATE NOCASE",
            (guild_id, key.strip()),
        ).fetchone()


def get_active_war_for_pack(guild_id: int, pack_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT w.*, t.name AS territory_name, t.key AS territory_key
            FROM wars w
            JOIN territories t ON t.id = w.territory_id
            WHERE w.guild_id = ? AND w.status = 'active'
            AND (w.attacker_pack_id = ? OR w.defender_pack_id = ?)
            LIMIT 1
            """,
            (guild_id, pack_id, pack_id),
        ).fetchone()


def get_active_war_between_packs(
    guild_id: int, pack_a: int, pack_b: int
) -> sqlite3.Row | None:
    """Active territory war contested by both Great Packs, if any."""
    if not pack_a or not pack_b or int(pack_a) == int(pack_b):
        return None
    war = get_active_war_for_pack(guild_id, int(pack_a))
    if not war or not war["defender_pack_id"]:
        return None
    pair = {int(war["attacker_pack_id"]), int(war["defender_pack_id"])}
    if pair == {int(pack_a), int(pack_b)}:
        return war
    return None


def start_war(
    guild_id: int,
    territory_id: int,
    attacker_pack_id: int,
    defender_pack_id: int | None,
    start_day: int,
) -> int:
    end_day = start_day + WAR_DURATION_DAYS
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO wars
            (guild_id, territory_id, attacker_pack_id, defender_pack_id,
             start_day, end_day, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
            """,
            (guild_id, territory_id, attacker_pack_id, defender_pack_id, start_day, end_day),
        )
        war_id = cursor.lastrowid
    if defender_pack_id:
        adjust_pack_relation(guild_id, attacker_pack_id, defender_pack_id, -2)
    adjust_pack_unity(attacker_pack_id, -1)
    return war_id


def add_war_score(war_id: int, pack_id: int, points: int) -> None:
    with get_db() as conn:
        war = conn.execute("SELECT * FROM wars WHERE id = ?", (war_id,)).fetchone()
        if not war or war["status"] != "active":
            return
        if pack_id == war["attacker_pack_id"]:
            conn.execute(
                "UPDATE wars SET attacker_score = attacker_score + ? WHERE id = ?",
                (points, war_id),
            )
        elif war["defender_pack_id"] and pack_id == war["defender_pack_id"]:
            conn.execute(
                "UPDATE wars SET defender_score = defender_score + ? WHERE id = ?",
                (points, war_id),
            )


def _adjudicate_war(conn: sqlite3.Connection, war: sqlite3.Row) -> str:
    """Score a war and update territory, unity, and status. Returns final status."""
    guild_id = war["guild_id"]
    attacker_wins = False
    defender_wins = False
    if war["defender_pack_id"] is None:
        attacker_wins = war["attacker_score"] >= NEUTRAL_CLAIM_SCORE
    elif war["attacker_score"] > war["defender_score"]:
        attacker_wins = True
    elif war["defender_score"] > war["attacker_score"]:
        defender_wins = True

    if attacker_wins:
        conn.execute(
            "UPDATE territories SET owner_pack_id = ? WHERE id = ?",
            (war["attacker_pack_id"], war["territory_id"]),
        )
        adjust_pack_unity(war["attacker_pack_id"], 1)
        if war["defender_pack_id"]:
            adjust_pack_unity(war["defender_pack_id"], -1)
            adjust_pack_relation(
                guild_id, war["attacker_pack_id"], war["defender_pack_id"], -1
            )
    elif defender_wins and war["defender_pack_id"]:
        adjust_pack_unity(war["defender_pack_id"], 1)
        adjust_pack_unity(war["attacker_pack_id"], -1)
        adjust_pack_relation(
            guild_id, war["attacker_pack_id"], war["defender_pack_id"], -2
        )

    status = (
        "won_attacker"
        if attacker_wins
        else "won_defender"
        if defender_wins
        else "stalemate"
    )
    conn.execute(
        "UPDATE wars SET status = ? WHERE id = ?",
        (status, war["id"]),
    )
    return status


def resolve_war(war_id: int) -> str | None:
    """Manually resolve an active war by current score. Returns final status or None."""
    with get_db() as conn:
        war = conn.execute(
            "SELECT * FROM wars WHERE id = ? AND status = 'active'",
            (war_id,),
        ).fetchone()
        if not war:
            return None
        world = conn.execute(
            "SELECT day_number FROM world_state WHERE guild_id = ?",
            (war["guild_id"],),
        ).fetchone()
        if (
            world
            and "end_day" in war.keys()
            and int(world["day_number"]) < int(war["end_day"])
        ):
            return None
        return _adjudicate_war(conn, war)


def territory_has_active_war(guild_id: int, territory_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM wars
            WHERE guild_id = ? AND territory_id = ? AND status = 'active'
            """,
            (guild_id, territory_id),
        ).fetchone()
        return row is not None


# --- Stats, conditions, herbs ---


def set_user_stats(discord_id: int, stats: dict) -> None:
    from engine.character import reconcile_hp

    wid = _resolve_wolf_id(discord_id)
    if not wid:
        return
    with get_db() as conn:
        user = conn.execute(
            "SELECT hp, max_hp FROM users WHERE id = ?", (wid,)
        ).fetchone()
        if not user:
            return
        new_hp, max_hp = reconcile_hp(
            user["hp"],
            user["max_hp"],
            stats["attr_str"],
            stats["attr_con"],
        )
        conn.execute(
            """
            UPDATE users
            SET attr_str = ?, attr_dex = ?, attr_con = ?,
                attr_int = ?, attr_cha = ?, attr_wis = ?,
                max_hp = ?, hp = ?
            WHERE id = ?
            """,
            (
                stats["attr_str"],
                stats["attr_dex"],
                stats["attr_con"],
                stats["attr_int"],
                stats["attr_cha"],
                stats["attr_wis"],
                max_hp,
                new_hp,
                wid,
            ),
        )


def grant_item(discord_id: int, item_id: int, quantity: int = 1, *, conn: sqlite3.Connection | None = None) -> None:
    def _apply(c: sqlite3.Connection) -> None:
        wolf_id = _resolve_wolf_id_conn(c, discord_id)
        if not wolf_id:
            return
        row = c.execute(
            "SELECT quantity FROM inventory WHERE wolf_id = ? AND item_id = ?",
            (wolf_id, item_id),
        ).fetchone()
        if row:
            c.execute(
                "UPDATE inventory SET quantity = quantity + ? WHERE wolf_id = ? AND item_id = ?",
                (quantity, wolf_id, item_id),
            )
        else:
            c.execute(
                "INSERT INTO inventory (wolf_id, item_id, quantity) VALUES (?, ?, ?)",
                (wolf_id, item_id, quantity),
            )

    if conn is not None:
        _apply(conn)
        return
    with get_db() as c:
        _apply(c)


def consume_item(discord_id: int, item_id: int, quantity: int = 1) -> bool:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if not wolf_id:
            return False
        row = conn.execute(
            "SELECT quantity FROM inventory WHERE wolf_id = ? AND item_id = ?",
            (wolf_id, item_id),
        ).fetchone()
        if not row or row["quantity"] < quantity:
            return False
        if row["quantity"] == quantity:
            conn.execute(
                "DELETE FROM inventory WHERE wolf_id = ? AND item_id = ?",
                (wolf_id, item_id),
            )
        else:
            conn.execute(
                "UPDATE inventory SET quantity = quantity - ? WHERE wolf_id = ? AND item_id = ?",
                (quantity, wolf_id, item_id),
            )
        return True


def set_user_conditions(
    discord_id: int,
    *,
    wolf_id: int | None = None,
    hp: int | None = None,
    exhaustion: int | None = None,
    disease: str | None = None,
    active_injuries: str | None = None,
    condition: str | None = None,
    clear_disease: bool = False,
    herb_heals_today: int | None = None,
    last_rest_day: int | None = None,
    death_cause: str | None = None,
) -> None:
    wid = wolf_id or _resolve_wolf_id(discord_id)
    if not wid:
        return
    with get_db() as conn:
        if clear_disease:
            conn.execute(
                "UPDATE users SET disease = NULL, quarantined = 0 WHERE id = ?",
                (wid,),
            )
        if condition == "dead":
            mark_wolf_dead(wid, death_cause or "unknown", conn=conn)
            return
        fields = {}
        if hp is not None:
            fields["hp"] = hp
        if exhaustion is not None:
            fields["exhaustion"] = exhaustion
        if disease is not None:
            fields["disease"] = disease
        if active_injuries is not None:
            fields["active_injuries"] = active_injuries
        if condition is not None:
            fields["condition"] = condition
        if herb_heals_today is not None:
            fields["herb_heals_today"] = herb_heals_today
        if last_rest_day is not None:
            fields["last_rest_day"] = last_rest_day
        if fields:
            columns = ", ".join(f"{k} = ?" for k in fields)
            conn.execute(
                f"UPDATE users SET {columns} WHERE id = ?",
                list(fields.values()) + [wid],
            )


def adjust_pack_unity(pack_id: int, delta: int) -> str:
    """Adjust unity (−5 to 10). Returns 'dissolved' if the pack fractured."""
    from config import PACK_UNITY_DISSOLVE_THRESHOLD, PACK_UNITY_MAX, PACK_UNITY_MIN

    with get_db() as conn:
        conn.execute(
            """
            UPDATE packs
            SET pack_unity = MIN(?, MAX(?, pack_unity + ?))
            WHERE id = ?
            """,
            (PACK_UNITY_MAX, PACK_UNITY_MIN, delta, pack_id),
        )
        row = conn.execute(
            "SELECT pack_unity FROM packs WHERE id = ?", (pack_id,)
        ).fetchone()
        if not row:
            return ""
        unity = int(row["pack_unity"])
        if unity <= PACK_UNITY_DISSOLVE_THRESHOLD:
            _dissolve_pack_conn(conn, pack_id)
            return "dissolved"
    return ""


def _dissolve_pack_conn(conn: sqlite3.Connection, pack_id: int) -> int:
    """Fracture a Great Pack; all members become loners. Returns wolves cast out."""
    pack = conn.execute("SELECT * FROM packs WHERE id = ?", (pack_id,)).fetchone()
    if not pack:
        return 0

    members = conn.execute(
        "SELECT id, discord_id FROM users WHERE pack_id = ?", (pack_id,)
    ).fetchall()
    for member in members:
        _expel_wolf_from_pack_conn(conn, member["id"], reset_standing=False)

    conn.execute(
        "DELETE FROM wars WHERE attacker_pack_id = ? OR defender_pack_id = ?",
        (pack_id, pack_id),
    )
    conn.execute(
        "UPDATE territories SET owner_pack_id = NULL WHERE owner_pack_id = ?",
        (pack_id,),
    )
    conn.execute(
        """
        UPDATE packs
        SET pack_unity = 5, alpha_id = NULL
        WHERE id = ?
        """,
        (pack_id,),
    )
    return len(members)


def _expel_wolf_from_pack_conn(
    conn: sqlite3.Connection, wolf_id: int, *, reset_standing: bool = True
) -> None:
    user = conn.execute("SELECT * FROM users WHERE id = ?", (wolf_id,)).fetchone()
    if not user or not user["pack_id"]:
        return

    pack_id = user["pack_id"]
    pack = conn.execute("SELECT * FROM packs WHERE id = ?", (pack_id,)).fetchone()
    if pack and pack["alpha_id"] == user["discord_id"]:
        _promote_pack_alpha(conn, pack_id, exclude_id=user["discord_id"])

    if reset_standing:
        conn.execute(
            """
            UPDATE users
            SET great_pack = NULL, pack_id = NULL, standing = 0
            WHERE id = ?
            """,
            (wolf_id,),
        )
    else:
        conn.execute(
            """
            UPDATE users
            SET great_pack = NULL, pack_id = NULL
            WHERE id = ?
            """,
            (wolf_id,),
        )


def adjust_wolf_standing_by_id(wolf_id: int, delta: int, *, triggered_day: int = 0) -> str:
    """
    Adjust standing for a specific wolf row.
    Returns '', 'kicked', or 'broken_rite' (Alpha leadership challenge).
    """
    from config import WOLF_STANDING_KICK_THRESHOLD, WOLF_STANDING_MIN
    from engine.broken_canine import maybe_trigger_broken_canine_rite

    user = get_user_by_id(wolf_id)
    if not user:
        return ""

    old_standing = int(user["standing"])
    new_standing = max(WOLF_STANDING_MIN, old_standing + delta)
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET standing = ? WHERE id = ?",
            (new_standing, wolf_id),
        )
        user = conn.execute("SELECT * FROM users WHERE id = ?", (wolf_id,)).fetchone()
        if new_standing <= WOLF_STANDING_KICK_THRESHOLD and user["pack_id"]:
            rite = maybe_trigger_broken_canine_rite(
                conn,
                user,
                old_standing=old_standing,
                new_standing=new_standing,
                triggered_day=triggered_day,
            )
            if rite:
                return "broken_rite"
            pack = get_pack(user["pack_id"]) if user["pack_id"] else None
            pack_name = pack["name"] if pack else "the pack"
            from engine.wolf_journal import log_cast_out

            log_cast_out(
                wolf_id,
                user["wolf_name"],
                pack_name,
                day=triggered_day or None,
            )
            _expel_wolf_from_pack_conn(conn, wolf_id, reset_standing=True)
            return "kicked"
    return ""


def adjust_wolf_standing(discord_id: int, delta: int) -> str:
    """
    Adjust personal pack standing for the active wolf (−10 to unbounded high).
    Returns '' or 'kicked' if cast out at/below kick threshold.
    """
    user = get_user(discord_id)
    if not user:
        return ""
    return adjust_wolf_standing_by_id(user["id"], delta)


def expel_wolves_below_standing_threshold(guild_id: int | None = None) -> int:
    """Rollover sweep; cast out wolves at/below kick threshold (Alphas trigger the Broken Canine rite)."""
    from config import WOLF_STANDING_KICK_THRESHOLD
    from engine.pack_leadership import is_pack_alpha

    day = 0
    if guild_id:
        world = get_world(guild_id)
        if world:
            day = int(world["day_number"])

    expelled = 0
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM users
            WHERE pack_id IS NOT NULL AND standing <= ?
            """,
            (WOLF_STANDING_KICK_THRESHOLD,),
        ).fetchall()
        for user in rows:
            pack = conn.execute(
                "SELECT * FROM packs WHERE id = ?", (user["pack_id"],)
            ).fetchone()
            if pack and is_pack_alpha(user, pack):
                done = conn.execute(
                    """
                    SELECT 1 FROM broken_canine_rites
                    WHERE pack_id = ? AND incumbent_wolf_id = ? AND triggered_day = ?
                    LIMIT 1
                    """,
                    (user["pack_id"], user["id"], day),
                ).fetchone()
                if not done:
                    from engine.broken_canine import run_broken_canine_rite

                    run_broken_canine_rite(
                        conn,
                        pack_id=int(user["pack_id"]),
                        incumbent_wolf_id=int(user["id"]),
                        triggered_day=day,
                    )
                continue
            _expel_wolf_from_pack_conn(conn, user["id"], reset_standing=True)
            expelled += 1
    return expelled


def get_latest_broken_canine_rite(pack_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM broken_canine_rites
            WHERE pack_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (pack_id,),
        ).fetchone()


def get_pack_unity(pack_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT pack_unity FROM packs WHERE id = ?", (pack_id,)
        ).fetchone()
        return int(row["pack_unity"]) if row else 5


def record_pack_howl(pack_id: int, guild_id: int, howl_day: int, discord_id: int) -> int:
    """Log a sunrise howl; return how many distinct wolves howled for this pack today."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO pack_howls (pack_id, guild_id, howl_day, discord_id)
            VALUES (?, ?, ?, ?)
            """,
            (pack_id, guild_id, howl_day, discord_id),
        )
        row = conn.execute(
            """
            SELECT COUNT(*) AS n FROM pack_howls
            WHERE pack_id = ? AND guild_id = ? AND howl_day = ?
            """,
            (pack_id, guild_id, howl_day),
        ).fetchone()
        return int(row["n"]) if row else 1


def get_pack_howl_discord_ids(pack_id: int, guild_id: int, howl_day: int) -> list[int]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT discord_id FROM pack_howls
            WHERE pack_id = ? AND guild_id = ? AND howl_day = ?
            """,
            (pack_id, guild_id, howl_day),
        ).fetchall()
    return [int(r["discord_id"]) for r in rows]


def record_pack_signal(
    guild_id: int,
    pack_id: int,
    signaler_id: int,
    signal_key: str,
    day: int,
    target_id: int | None = None,
) -> int:
    """Log a body-language signal in the den; return the new signal id."""
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO pack_signals
                (guild_id, pack_id, signaler_id, signal_key, target_id, day)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (guild_id, pack_id, signaler_id, signal_key, target_id, day),
        )
        return int(cur.lastrowid)


def get_readable_pack_signal(
    guild_id: int, pack_id: int, day: int, reader_wolf_id: int
) -> sqlite3.Row | None:
    """Most recent signal in this den today that `reader` did not post or already answer."""
    reader = str(int(reader_wolf_id))
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM pack_signals
            WHERE guild_id = ? AND pack_id = ? AND day = ? AND signaler_id != ?
            ORDER BY id DESC
            """,
            (guild_id, pack_id, day, reader_wolf_id),
        ).fetchall()
    for row in rows:
        responders = {r for r in str(row["responders"]).split(",") if r}
        if reader not in responders:
            return row
    return None


def mark_signal_responded(signal_id: int, reader_wolf_id: int) -> None:
    reader = str(int(reader_wolf_id))
    with get_db() as conn:
        row = conn.execute(
            "SELECT responders FROM pack_signals WHERE id = ?", (signal_id,)
        ).fetchone()
        if not row:
            return
        responders = [r for r in str(row["responders"]).split(",") if r]
        if reader in responders:
            return
        responders.append(reader)
        conn.execute(
            "UPDATE pack_signals SET responders = ? WHERE id = ?",
            (",".join(responders), signal_id),
        )


def _normalize_pack_pair(pack_a: int, pack_b: int) -> tuple[int, int]:
    return (pack_a, pack_b) if pack_a < pack_b else (pack_b, pack_a)


def get_pack_relation(guild_id: int, pack_a: int, pack_b: int) -> int:
    if pack_a == pack_b:
        return 10
    a, b = _normalize_pack_pair(pack_a, pack_b)
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT standing FROM pack_relations
            WHERE guild_id = ? AND pack_a_id = ? AND pack_b_id = ?
            """,
            (guild_id, a, b),
        ).fetchone()
        return row["standing"] if row else 5


def adjust_pack_relation(guild_id: int, pack_a: int, pack_b: int, delta: int) -> int:
    if pack_a == pack_b:
        return 10
    a, b = _normalize_pack_pair(pack_a, pack_b)
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT standing FROM pack_relations
            WHERE guild_id = ? AND pack_a_id = ? AND pack_b_id = ?
            """,
            (guild_id, a, b),
        ).fetchone()
        standing = row["standing"] if row else 5
        standing = min(10, max(0, standing + delta))
        conn.execute(
            """
            INSERT INTO pack_relations (guild_id, pack_a_id, pack_b_id, standing)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, pack_a_id, pack_b_id)
            DO UPDATE SET standing = excluded.standing
            """,
            (guild_id, a, b, standing),
        )
    if standing <= 0:
        from engine.pack_relations import maybe_declare_relation_war

        world = get_world(guild_id)
        day = int(world["day_number"]) if world else 0
        maybe_declare_relation_war(guild_id, a, b, day)
    return standing


def list_pack_relations(guild_id: int, pack_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT pr.standing,
                   CASE WHEN pr.pack_a_id = ? THEN pr.pack_b_id ELSE pr.pack_a_id END AS other_pack_id,
                   p.name AS other_pack_name
            FROM pack_relations pr
            JOIN packs p ON p.id = CASE WHEN pr.pack_a_id = ? THEN pr.pack_b_id ELSE pr.pack_a_id END
            WHERE pr.guild_id = ? AND (pr.pack_a_id = ? OR pr.pack_b_id = ?)
            ORDER BY pr.standing ASC
            """,
            (pack_id, pack_id, guild_id, pack_id, pack_id),
        ).fetchall()


def record_pack_raid_alert(
    guild_id: int,
    *,
    victim_pack_id: int,
    suspect_pack_id: int,
    stolen_amount: int,
    raid_day: int,
    expires_day: int,
    caught: bool = False,
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO pack_raid_alerts (
                guild_id, victim_pack_id, suspect_pack_id, stolen_amount,
                raid_day, expires_day, caught
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                victim_pack_id,
                suspect_pack_id,
                stolen_amount,
                raid_day,
                expires_day,
                1 if caught else 0,
            ),
        )
        return int(cur.lastrowid)


def get_active_raid_alert_for_victim(guild_id: int, victim_pack_id: int, day: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pack_raid_alerts
            WHERE guild_id = ? AND victim_pack_id = ? AND expires_day >= ?
            ORDER BY raid_day DESC, id DESC
            LIMIT 1
            """,
            (guild_id, victim_pack_id, day),
        ).fetchone()


def raid_watch_active(guild_id: int, pack_a: int, pack_b: int, day: int) -> bool:
    if pack_a == pack_b:
        return False
    a, b = _normalize_pack_pair(pack_a, pack_b)
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM pack_raid_alerts
            WHERE guild_id = ? AND expires_day >= ?
              AND ((victim_pack_id = ? AND suspect_pack_id = ?)
                OR (victim_pack_id = ? AND suspect_pack_id = ?))
            LIMIT 1
            """,
            (guild_id, day, a, b, b, a),
        ).fetchone()
        return row is not None


def recover_raid_alert_bones(alert_id: int, amount: int, victim_pack_id: int) -> int:
    if amount <= 0:
        return 0
    with get_db() as conn:
        alert = conn.execute(
            "SELECT * FROM pack_raid_alerts WHERE id = ?", (alert_id,)
        ).fetchone()
        if not alert or int(alert["victim_pack_id"]) != victim_pack_id:
            return 0
        remaining = int(alert["stolen_amount"]) - int(alert["recovered_amount"])
        take = min(amount, max(0, remaining))
        if take <= 0:
            return 0
        conn.execute(
            """
            UPDATE pack_raid_alerts
            SET recovered_amount = recovered_amount + ?
            WHERE id = ?
            """,
            (take, alert_id),
        )
        conn.execute(
            "UPDATE packs SET treasury = treasury + ? WHERE id = ?",
            (take, victim_pack_id),
        )
        return take


def clawback_raid_from_pack_treasury(
    suspect_pack_id: int, amount: int, victim_pack_id: int, alert_id: int
) -> int:
    if amount <= 0:
        return 0
    with get_db() as conn:
        pack = conn.execute(
            "SELECT treasury FROM packs WHERE id = ?", (suspect_pack_id,)
        ).fetchone()
        if not pack:
            return 0
        take = min(amount, int(pack["treasury"]))
        if take <= 0:
            return 0
        conn.execute(
            "UPDATE packs SET treasury = treasury - ? WHERE id = ?",
            (take, suspect_pack_id),
        )
        conn.execute(
            "UPDATE packs SET treasury = treasury + ? WHERE id = ?",
            (take, victim_pack_id),
        )
        conn.execute(
            """
            UPDATE pack_raid_alerts
            SET recovered_amount = recovered_amount + ?
            WHERE id = ?
            """,
            (take, alert_id),
        )
        return take


def set_raid_alert_audit_day(alert_id: int, day: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE pack_raid_alerts SET last_audit_day = ? WHERE id = ?",
            (day, alert_id),
        )


def set_raid_alert_accused(alert_id: int, accused_pack_id: int, day: int) -> None:
    with get_db() as conn:
        conn.execute(
            """
            UPDATE pack_raid_alerts
            SET accused_pack_id = ?, accuse_day = ?
            WHERE id = ?
            """,
            (accused_pack_id, day, alert_id),
        )


def expire_pack_raid_alerts_before(guild_id: int, day: int) -> None:
    with get_db() as conn:
        conn.execute(
            "DELETE FROM pack_raid_alerts WHERE guild_id = ? AND expires_day < ?",
            (guild_id, day),
        )


def get_bond_relation_cooldown(guild_id: int, pack_a: int, pack_b: int) -> int:
    a, b = _normalize_pack_pair(pack_a, pack_b)
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT last_penalty_day FROM bond_relation_cooldowns
            WHERE guild_id = ? AND pack_a_id = ? AND pack_b_id = ?
            """,
            (guild_id, a, b),
        ).fetchone()
        return int(row["last_penalty_day"]) if row else 0


def set_bond_relation_cooldown(guild_id: int, pack_a: int, pack_b: int, day: int) -> None:
    a, b = _normalize_pack_pair(pack_a, pack_b)
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO bond_relation_cooldowns (guild_id, pack_a_id, pack_b_id, last_penalty_day)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, pack_a_id, pack_b_id)
            DO UPDATE SET last_penalty_day = excluded.last_penalty_day
            """,
            (guild_id, a, b, day),
        )


def record_cross_pack_scandal(
    guild_id: int,
    wolf_a_id: int,
    wolf_b_id: int,
    *,
    caught_day: int,
) -> None:
    a = get_user_by_id(wolf_a_id)
    b = get_user_by_id(wolf_b_id)
    if not a or not b:
        return
    pack_a = a["pack_id"] if "pack_id" in a.keys() else None
    pack_b = b["pack_id"] if "pack_id" in b.keys() else None
    if not pack_a or not pack_b or pack_a == pack_b:
        return
    low_w, high_w = (wolf_a_id, wolf_b_id) if wolf_a_id < wolf_b_id else (wolf_b_id, wolf_a_id)
    pa, pb = _normalize_pack_pair(pack_a, pack_b)
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO cross_pack_scandals (
                guild_id, wolf_a_id, wolf_b_id, pack_a_id, pack_b_id, caught_day
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, wolf_a_id, wolf_b_id)
            DO UPDATE SET caught_day = excluded.caught_day,
                          pack_a_id = excluded.pack_a_id,
                          pack_b_id = excluded.pack_b_id
            """,
            (guild_id, low_w, high_w, pa, pb, caught_day),
        )


def list_cross_pack_scandals(guild_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM cross_pack_scandals WHERE guild_id = ?",
            (guild_id,),
        ).fetchall()


def clear_cross_pack_scandal(scandal_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM cross_pack_scandals WHERE id = ?", (scandal_id,))


def mark_collab_hunt_rp_said(wolf_id: int, channel_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT m.hunt_id FROM collab_hunt_members m
            JOIN collab_hunts h ON h.id = m.hunt_id
            WHERE m.wolf_id = ? AND h.channel_id = ? AND h.status IN ('open', 'encounter')
            LIMIT 1
            """,
            (wolf_id, channel_id),
        ).fetchone()
        if not row:
            return False
        conn.execute(
            """
            UPDATE collab_hunt_members SET rp_said = 1
            WHERE hunt_id = ? AND wolf_id = ?
            """,
            (row["hunt_id"], wolf_id),
        )
        return True


def collab_hunt_member_rp_said(hunt_id: int, wolf_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT rp_said FROM collab_hunt_members WHERE hunt_id = ? AND wolf_id = ?",
            (hunt_id, wolf_id),
        ).fetchone()
        return bool(row and int(row["rp_said"]))


def upsert_scent_mark(
    guild_id: int,
    territory_key: str,
    pack_key: str,
    marker_wolf_id: int,
    marked_day: int,
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO scent_marks (guild_id, territory_key, pack_key, marker_wolf_id, marked_day)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, territory_key, pack_key)
            DO UPDATE SET marker_wolf_id = excluded.marker_wolf_id,
                          marked_day = excluded.marked_day
            """,
            (guild_id, territory_key.strip().lower(), pack_key, marker_wolf_id, marked_day),
        )


def get_scent_marks_for_pack(guild_id: int, pack_key: str, *, since_day: int = 0) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT sm.*, t.name AS territory_name
            FROM scent_marks sm
            LEFT JOIN territories t ON t.guild_id = sm.guild_id AND t.key = sm.territory_key
            WHERE sm.guild_id = ? AND sm.pack_key = ? AND sm.marked_day >= ?
            ORDER BY sm.marked_day DESC
            """,
            (guild_id, pack_key, since_day),
        ).fetchall()


def pack_diplomacy_done_today(
    guild_id: int,
    pack_a: int,
    pack_b: int,
    action: str,
    day: int,
) -> bool:
    a, b = _normalize_pack_pair(pack_a, pack_b)
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM pack_diplomacy_log
            WHERE guild_id = ? AND pack_a_id = ? AND pack_b_id = ? AND action = ? AND action_day = ?
            """,
            (guild_id, a, b, action, day),
        ).fetchone()
        return row is not None


def record_pack_diplomacy(
    guild_id: int,
    pack_a: int,
    pack_b: int,
    action: str,
    day: int,
) -> None:
    a, b = _normalize_pack_pair(pack_a, pack_b)
    with get_db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO pack_diplomacy_log
            (guild_id, pack_a_id, pack_b_id, action, action_day)
            VALUES (?, ?, ?, ?, ?)
            """,
            (guild_id, a, b, action, day),
        )


# --- Cat clan pacts (pack treaties) ---


def get_cat_pact(pack_id: int, clan_name: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pack_cat_pacts
            WHERE pack_id = ? AND clan_name = ? COLLATE NOCASE
            """,
            (pack_id, clan_name.strip()),
        ).fetchone()


def list_active_cat_pacts(guild_id: int, pack_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pack_cat_pacts
            WHERE guild_id = ? AND pack_id = ? AND status = 'active'
            ORDER BY trust DESC, clan_name ASC
            """,
            (guild_id, pack_id),
        ).fetchall()


def count_active_cat_pacts(pack_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM pack_cat_pacts
            WHERE pack_id = ? AND status = 'active'
            """,
            (pack_id,),
        ).fetchone()
        return int(row["c"]) if row else 0


def upsert_cat_pact(
    guild_id: int,
    pack_id: int,
    clan_name: str,
    *,
    pact_type: str,
    trust: int,
    tribute_paid: int,
    terms_note: str,
    forged_day: int,
    expires_day: int,
    forged_by_discord_id: int,
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO pack_cat_pacts (
                guild_id, pack_id, clan_name, pact_type, status, trust, tribute_paid,
                terms_note, forged_day, expires_day, forged_by_discord_id,
                broken_day, break_reason
            )
            VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, NULL, '')
            ON CONFLICT(pack_id, clan_name) DO UPDATE SET
                guild_id = excluded.guild_id,
                pact_type = excluded.pact_type,
                status = 'active',
                trust = excluded.trust,
                tribute_paid = excluded.tribute_paid,
                terms_note = excluded.terms_note,
                forged_day = excluded.forged_day,
                expires_day = excluded.expires_day,
                forged_by_discord_id = excluded.forged_by_discord_id,
                broken_day = NULL,
                break_reason = ''
            """,
            (
                guild_id,
                pack_id,
                clan_name.strip(),
                pact_type,
                max(0, min(100, int(trust))),
                tribute_paid,
                terms_note,
                forged_day,
                expires_day,
                forged_by_discord_id,
            ),
        )


def renew_cat_pact(pack_id: int, clan_name: str, *, expires_day: int, trust: int, day: int) -> None:
    with get_db() as conn:
        conn.execute(
            """
            UPDATE pack_cat_pacts
            SET expires_day = ?, trust = ?, forged_day = ?
            WHERE pack_id = ? AND clan_name = ? COLLATE NOCASE AND status = 'active'
            """,
            (expires_day, max(0, min(100, int(trust))), day, pack_id, clan_name.strip()),
        )


def break_cat_pact(pack_id: int, clan_name: str, *, day: int, reason: str) -> None:
    with get_db() as conn:
        conn.execute(
            """
            UPDATE pack_cat_pacts
            SET status = 'broken', broken_day = ?, break_reason = ?, trust = 0
            WHERE pack_id = ? AND clan_name = ? COLLATE NOCASE AND status = 'active'
            """,
            (day, (reason or "")[:200], pack_id, clan_name.strip()),
        )


def adjust_cat_pact_trust(pack_id: int, clan_name: str, delta: int) -> int:
    pact = get_cat_pact(pack_id, clan_name)
    if not pact or pact["status"] != "active":
        return 0
    new_trust = max(0, min(100, int(pact["trust"]) + delta))
    with get_db() as conn:
        conn.execute(
            """
            UPDATE pack_cat_pacts SET trust = ?
            WHERE pack_id = ? AND clan_name = ? COLLATE NOCASE
            """,
            (new_trust, pack_id, clan_name.strip()),
        )
    return new_trust


def expire_cat_pacts_for_day(guild_id: int, day: int) -> list[str]:
    """Mark expired pacts; return clan names for den news."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT clan_name, pack_id FROM pack_cat_pacts
            WHERE guild_id = ? AND status = 'active' AND expires_day < ?
            """,
            (guild_id, day),
        ).fetchall()
        if not rows:
            return []
        conn.execute(
            """
            UPDATE pack_cat_pacts
            SET status = 'expired', break_reason = 'Treaty term ended.'
            WHERE guild_id = ? AND status = 'active' AND expires_day < ?
            """,
            (guild_id, day),
        )
    return [row["clan_name"] for row in rows]


def get_pack_cat_pact_fail_day(pack_id: int, clan_name: str) -> int | None:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT last_fail_day FROM pack_cat_pact_offers
            WHERE pack_id = ? AND clan_name = ? COLLATE NOCASE
            """,
            (pack_id, clan_name.strip()),
        ).fetchone()
        return int(row["last_fail_day"]) if row else None


def set_pack_cat_pact_fail_day(pack_id: int, clan_name: str, day: int) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO pack_cat_pact_offers (pack_id, clan_name, last_fail_day)
            VALUES (?, ?, ?)
            ON CONFLICT(pack_id, clan_name) DO UPDATE SET last_fail_day = excluded.last_fail_day
            """,
            (pack_id, clan_name.strip(), day),
        )


def cat_pact_gift_used_today(pack_id: int, day: int) -> bool:
    pack = get_pack(pack_id)
    if not pack:
        return True
    return int(pack["last_cat_pact_gift_day"]) >= day


def mark_cat_pact_gift_day(pack_id: int, day: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE packs SET last_cat_pact_gift_day = ? WHERE id = ?",
            (day, pack_id),
        )


def get_wolf_treaty(pack_id: int, other_pack_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pack_wolf_treaties
            WHERE pack_id = ? AND other_pack_id = ?
            """,
            (pack_id, other_pack_id),
        ).fetchone()


def list_active_wolf_treaties(guild_id: int, pack_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT wt.*, p.name AS other_pack_name, p.key AS other_pack_key
            FROM pack_wolf_treaties wt
            JOIN packs p ON p.id = wt.other_pack_id
            WHERE wt.guild_id = ? AND wt.pack_id = ? AND wt.status = 'active'
            ORDER BY wt.expires_day ASC
            """,
            (guild_id, pack_id),
        ).fetchall()


def count_active_wolf_treaties(pack_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM pack_wolf_treaties
            WHERE pack_id = ? AND status = 'active'
            """,
            (pack_id,),
        ).fetchone()
        return int(row["c"]) if row else 0


def upsert_wolf_treaty(
    guild_id: int,
    pack_id: int,
    other_pack_id: int,
    *,
    pact_type: str,
    terms_note: str,
    forged_day: int,
    expires_day: int,
    forged_by_discord_id: int,
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO pack_wolf_treaties (
                guild_id, pack_id, other_pack_id, pact_type, status, terms_note,
                forged_day, expires_day, forged_by_discord_id, broken_day, break_reason
            ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, NULL, '')
            ON CONFLICT(pack_id, other_pack_id) DO UPDATE SET
                pact_type = excluded.pact_type,
                status = 'active',
                terms_note = excluded.terms_note,
                forged_day = excluded.forged_day,
                expires_day = excluded.expires_day,
                forged_by_discord_id = excluded.forged_by_discord_id,
                broken_day = NULL,
                break_reason = ''
            """,
            (
                guild_id,
                pack_id,
                other_pack_id,
                pact_type,
                terms_note or "",
                forged_day,
                expires_day,
                forged_by_discord_id,
            ),
        )


def renew_wolf_treaty(
    pack_id: int, other_pack_id: int, *, expires_day: int, day: int
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            UPDATE pack_wolf_treaties
            SET expires_day = ?, forged_day = ?
            WHERE pack_id = ? AND other_pack_id = ? AND status = 'active'
            """,
            (expires_day, day, pack_id, other_pack_id),
        )


def break_wolf_treaty(
    pack_id: int, other_pack_id: int, *, day: int, reason: str
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            UPDATE pack_wolf_treaties
            SET status = 'broken', broken_day = ?, break_reason = ?
            WHERE pack_id = ? AND other_pack_id = ?
            """,
            (day, reason or "Treaty withdrawn.", pack_id, other_pack_id),
        )


def expire_wolf_treaties_for_day(guild_id: int, day: int) -> list[str]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT wt.other_pack_id, p.name AS other_pack_name
            FROM pack_wolf_treaties wt
            JOIN packs p ON p.id = wt.other_pack_id
            WHERE wt.guild_id = ? AND wt.status = 'active' AND wt.expires_day < ?
            """,
            (guild_id, day),
        ).fetchall()
        if not rows:
            return []
        conn.execute(
            """
            UPDATE pack_wolf_treaties
            SET status = 'expired', break_reason = 'Treaty term ended.'
            WHERE guild_id = ? AND status = 'active' AND expires_day < ?
            """,
            (guild_id, day),
        )
    return [row["other_pack_name"] for row in rows]


def get_wolf_pact_fail_day(pack_id: int, other_pack_id: int) -> int | None:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT last_fail_day FROM pack_wolf_pact_offers
            WHERE pack_id = ? AND other_pack_id = ?
            """,
            (pack_id, other_pack_id),
        ).fetchone()
        return int(row["last_fail_day"]) if row else None


def set_wolf_pact_fail_day(pack_id: int, other_pack_id: int, day: int) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO pack_wolf_pact_offers (pack_id, other_pack_id, last_fail_day)
            VALUES (?, ?, ?)
            ON CONFLICT(pack_id, other_pack_id) DO UPDATE SET last_fail_day = excluded.last_fail_day
            """,
            (pack_id, other_pack_id, day),
        )


def reconcile_encounter_if_broken(encounter_id: int) -> bool:
    """
    End or repair encounters stuck with no fighters, no living combatants,
    or a turn order pointing at missing fighters. Returns True if ended.
    """
    import json

    enc = get_encounter(encounter_id)
    if not enc or enc["status"] not in ("recruiting", "active"):
        return False

    fighters = get_combat_fighters(encounter_id)
    if not fighters:
        if enc["status"] == "recruiting":
            return False
        end_encounter(encounter_id)
        return True

    if enc["status"] == "recruiting":
        return False

    if len(fighters) < 2:
        end_encounter(encounter_id)
        return True

    living = [f for f in fighters if int(f["hp"]) > 0]
    if not living:
        end_encounter(encounter_id)
        return True

    order = json.loads(enc["turn_order"] or "[]")
    valid = {f["id"] for f in fighters}
    pruned = [fid for fid in order if fid in valid]
    if pruned == order and order:
        return False

    if not pruned:
        rebuild_encounter_initiative(encounter_id)
        return False

    old_turn = int(enc["current_turn"])
    current_fid = order[old_turn] if order and 0 <= old_turn < len(order) else None
    if current_fid in pruned:
        new_turn = pruned.index(current_fid)
    else:
        new_turn = min(old_turn, len(pruned) - 1)

    with get_db() as conn:
        conn.execute(
            """
            UPDATE combat_encounters
            SET turn_order = ?, current_turn = ?
            WHERE id = ?
            """,
            (json.dumps(pruned), new_turn, encounter_id),
        )
    return False


def insert_fighter_into_active_encounter(
    encounter_id: int,
    fighter_id: int,
    initiative: int,
) -> None:
    """Slot a new fighter into an active fight without re-rolling everyone."""
    import json

    set_fighter_initiative(fighter_id, initiative)
    with get_db() as conn:
        enc = conn.execute(
            "SELECT * FROM combat_encounters WHERE id = ?", (encounter_id,)
        ).fetchone()
        if not enc or enc["status"] != "active":
            return

        order = json.loads(enc["turn_order"] or "[]")
        if fighter_id in order:
            return

        old_turn = int(enc["current_turn"])
        current_fid = order[old_turn] if order and 0 <= old_turn < len(order) else None

        order.append(fighter_id)
        rows = conn.execute(
            "SELECT id, initiative FROM combat_fighters WHERE encounter_id = ?",
            (encounter_id,),
        ).fetchall()
        inits = {row["id"]: int(row["initiative"] or 0) for row in rows}
        order.sort(key=lambda fid: (-inits.get(fid, 0), fid))

        if current_fid is not None and current_fid in order:
            new_turn = order.index(current_fid)
        else:
            new_turn = min(old_turn, len(order) - 1) if order else 0

        conn.execute(
            """
            UPDATE combat_encounters
            SET turn_order = ?, current_turn = ?
            WHERE id = ?
            """,
            (json.dumps(order), new_turn, encounter_id),
        )


def list_active_encounters(channel_id: int) -> list:
    """All recruiting/active fights in a channel (reconciles broken ones)."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id FROM combat_encounters
            WHERE channel_id = ? AND status IN ('recruiting', 'active')
            ORDER BY id DESC
            """,
            (channel_id,),
        ).fetchall()
    alive: list = []
    for row in rows:
        if reconcile_encounter_if_broken(row["id"]):
            continue
        enc = get_encounter(row["id"])
        if enc and enc["status"] in ("recruiting", "active"):
            alive.append(enc)
    return alive


def player_encounters_in_channel(channel_id: int, discord_id: int) -> list:
    return [
        enc
        for enc in list_active_encounters(channel_id)
        if player_in_encounter(enc["id"], discord_id)
    ]


def format_encounter_choices(encounters: list, *, limit: int = 8) -> str:
    if not encounters:
        return ""
    parts = []
    for enc in encounters[:limit]:
        n = len(get_combat_fighters(enc["id"]))
        parts.append(f"**#{enc['id']}** ({enc['status']}, {n} fighters)")
    return ", ".join(parts)


def resolve_combat_encounter(
    channel_id: int,
    discord_id: int | None = None,
    encounter_id: int | None = None,
    *,
    require_membership: bool = False,
    joinable_only: bool = False,
    require_recruiting: bool = False,
) -> tuple[sqlite3.Row | None, str | None]:
    """Pick the fight a command should target. Returns (encounter, error_message)."""

    def _fresh(enc_id: int) -> sqlite3.Row | None:
        reconcile_encounter_if_broken(enc_id)
        enc = get_encounter(enc_id)
        if enc and enc["status"] in ("recruiting", "active"):
            return enc
        return None

    if encounter_id is not None:
        enc = get_encounter(encounter_id)
        if not enc or enc["channel_id"] != channel_id:
            return None, f"No open fight **#{encounter_id}** in this channel."
        enc = _fresh(encounter_id)
        if not enc:
            return None, f"Fight **#{encounter_id}** is not open."
        if require_membership and discord_id and not player_in_encounter(enc["id"], discord_id):
            return None, f"You're not in fight **#{encounter_id}**."
        if joinable_only and discord_id and player_in_encounter(enc["id"], discord_id):
            return None, "You're already in that fight."
        if require_recruiting and enc["status"] != "recruiting":
            return None, f"Fight **#{encounter_id}** has already begun; `/combat join` still works mid-fight."
        return enc, None

    active = list_active_encounters(channel_id)
    if not active:
        return None, "No open fights here. `/combat start` opens a new one."

    if joinable_only and discord_id:
        candidates = [e for e in active if not player_in_encounter(e["id"], discord_id)]
        if require_recruiting:
            candidates = [e for e in candidates if e["status"] == "recruiting"]
        if not candidates:
            return None, "No fights here you can join."
        if len(candidates) == 1:
            return candidates[0], None
        return None, (
            "Several fights are open: "
            f"{format_encounter_choices(candidates)}. "
            "Use `encounter:` on `/combat join`."
        )

    if require_membership and discord_id:
        mine = [e for e in active if player_in_encounter(e["id"], discord_id)]
        if require_recruiting:
            mine = [e for e in mine if e["status"] == "recruiting"]
        if len(mine) == 1:
            return mine[0], None
        if len(mine) > 1:
            return None, (
                "You're in multiple fights: "
                f"{format_encounter_choices(mine)}. "
                "Pass `encounter:` on this command."
            )
        return None, "You're not in a fight here."

    if len(active) == 1:
        return active[0], None
    return None, (
        "Several fights are open: "
        f"{format_encounter_choices(active)}. "
        "Use `/combat list` or pass `encounter:`."
    )


def get_active_encounter(channel_id: int) -> sqlite3.Row | None:
    """Most recent open fight in a channel (legacy helper)."""
    active = list_active_encounters(channel_id)
    return active[0] if active else None


def get_encounter(encounter_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM combat_encounters WHERE id = ?",
            (encounter_id,),
        ).fetchone()


def create_encounter(guild_id: int, channel_id: int, created_by: int) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO combat_encounters
            (guild_id, channel_id, status, created_by, created_at)
            VALUES (?, ?, 'recruiting', ?, ?)
            """,
            (guild_id, channel_id, created_by, utcnow()),
        )
        return cursor.lastrowid


def setup_hunt_prey_encounter(
    guild_id: int,
    channel_id: int,
    hunter_discord_id: int,
    hunter_wolf_id: int,
    *,
    hunter_hp: int,
    hunter_max_hp: int,
    prey_hp: int,
    prey_name: str,
) -> int:
    """Create an active hunt fight vs large prey (deer/elk)."""
    import json
    import random

    from engine.bestiary import stats_for_fighter
    from engine.character import attr_modifier
    from engine.combat import roll_initiative

    enc_id = create_encounter(guild_id, channel_id, hunter_discord_id)
    with get_db() as conn:
        conn.execute(
            """
            UPDATE combat_encounters
            SET is_hunt_prey = 1, hunter_discord_id = ?, hunter_wolf_id = ?
            WHERE id = ?
            """,
            (hunter_discord_id, hunter_wolf_id, enc_id),
        )

    hunter_fighter_id = add_combat_fighter(
        enc_id,
        discord_id=hunter_discord_id,
        wolf_id=hunter_wolf_id,
        hp=hunter_hp,
        max_hp=hunter_max_hp,
    )
    prey_fighter_id = add_combat_fighter(
        enc_id,
        npc_name=prey_name,
        npc_template="large_prey",
        hp=prey_hp,
        max_hp=prey_hp,
    )

    rolls: list[tuple[int, int]] = []
    for fighter_id, is_hunter in ((hunter_fighter_id, True), (prey_fighter_id, False)):
        if is_hunter:
            user = get_user(hunter_discord_id)
            die, mod, total = roll_initiative(user)
        else:
            prey_row = get_combat_fighter(enc_id, prey_fighter_id)
            stats = stats_for_fighter(prey_row)
            die = random.randint(1, 20)
            mod = attr_modifier(stats["attr_dex"])
            total = die + mod
        set_fighter_initiative(fighter_id, total)
        rolls.append((fighter_id, total))

    order = [fid for fid, _ in sorted(rolls, key=lambda x: -x[1])]
    start_combat_encounter(enc_id, order)
    return enc_id


def setup_border_cat_encounter(
    guild_id: int,
    channel_id: int,
    hunter_discord_id: int,
    hunter_wolf_id: int,
    *,
    hunter_hp: int,
    hunter_max_hp: int,
    cat_hp: int,
    cat_name: str,
    cat_template: str,
    border_cat_clan: str = "",
    border_pact_violation: bool = False,
) -> int:
    """Create an active border fight vs a clan cat."""
    import random

    from engine.bestiary import stats_for_fighter
    from engine.character import attr_modifier
    from engine.combat import roll_initiative

    enc_id = create_encounter(guild_id, channel_id, hunter_discord_id)
    with get_db() as conn:
        conn.execute(
            """
            UPDATE combat_encounters
            SET is_border_fight = 1, hunter_discord_id = ?, hunter_wolf_id = ?,
                border_cat_clan = ?, border_pact_violation = ?
            WHERE id = ?
            """,
            (
                hunter_discord_id,
                hunter_wolf_id,
                (border_cat_clan or "")[:32],
                1 if border_pact_violation else 0,
                enc_id,
            ),
        )

    hunter_fighter_id = add_combat_fighter(
        enc_id,
        discord_id=hunter_discord_id,
        wolf_id=hunter_wolf_id,
        hp=hunter_hp,
        max_hp=hunter_max_hp,
    )
    cat_fighter_id = add_combat_fighter(
        enc_id,
        npc_name=cat_name,
        npc_template=cat_template,
        hp=cat_hp,
        max_hp=cat_hp,
    )

    rolls: list[tuple[int, int]] = []
    for fighter_id, is_hunter in ((hunter_fighter_id, True), (cat_fighter_id, False)):
        if is_hunter:
            user = get_user(hunter_discord_id)
            die, mod, total = roll_initiative(user)
        else:
            cat_row = get_combat_fighter(enc_id, cat_fighter_id)
            stats = stats_for_fighter(cat_row)
            die = random.randint(1, 20)
            mod = attr_modifier(stats["attr_dex"])
            total = die + mod
        set_fighter_initiative(fighter_id, total)
        rolls.append((fighter_id, total))

    order = [fid for fid, _ in sorted(rolls, key=lambda x: -x[1])]
    start_combat_encounter(enc_id, order)
    return enc_id


def setup_npc_ambush_encounter(
    guild_id: int,
    channel_id: int,
    hunter_discord_id: int,
    hunter_wolf_id: int,
    *,
    hunter_hp: int,
    hunter_max_hp: int,
    npc_template: str,
    npc_hp: int,
    npc_base_name: str,
    ambush_activity: str = "",
) -> int:
    """Create an active ambush fight vs a random or scripted NPC."""
    import random

    from engine.bestiary import stats_for_fighter
    from engine.character import attr_modifier
    from engine.combat import roll_initiative
    from engine.combat_display import assign_npc_display_name

    enc_id = create_encounter(guild_id, channel_id, hunter_discord_id)
    with get_db() as conn:
        conn.execute(
            """
            UPDATE combat_encounters
            SET hunter_discord_id = ?, hunter_wolf_id = ?, ambush_activity = ?
            WHERE id = ?
            """,
            (hunter_discord_id, hunter_wolf_id, ambush_activity or "", enc_id),
        )
    hunter_fighter_id = add_combat_fighter(
        enc_id,
        discord_id=hunter_discord_id,
        wolf_id=hunter_wolf_id,
        hp=hunter_hp,
        max_hp=hunter_max_hp,
    )
    display_name = assign_npc_display_name(enc_id, npc_template, npc_base_name)
    npc_fighter_id = add_combat_fighter(
        enc_id,
        npc_name=display_name,
        npc_template=npc_template,
        hp=npc_hp,
        max_hp=npc_hp,
    )

    rolls: list[tuple[int, int]] = []
    for fighter_id, is_hunter in ((hunter_fighter_id, True), (npc_fighter_id, False)):
        if is_hunter:
            user = get_user(hunter_discord_id)
            die, mod, total = roll_initiative(user)
        else:
            npc_row = get_combat_fighter(enc_id, npc_fighter_id)
            stats = stats_for_fighter(npc_row)
            die = random.randint(1, 20)
            mod = attr_modifier(stats["attr_dex"])
            total = die + mod
        set_fighter_initiative(fighter_id, total)
        rolls.append((fighter_id, total))

    order = [fid for fid, _ in sorted(rolls, key=lambda x: -x[1])]
    start_combat_encounter(enc_id, order)
    return enc_id


def mark_border_fight_rewarded(encounter_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE combat_encounters SET border_fight_rewarded = 1 WHERE id = ?",
            (encounter_id,),
        )


def mark_hunt_prey_rewarded(encounter_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE combat_encounters SET hunt_prey_rewarded = 1 WHERE id = ?",
            (encounter_id,),
        )


def set_combat_target(discord_id: int, encounter_id: int, target_fighter_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO combat_target_picks (discord_id, encounter_id, target_fighter_id)
            VALUES (?, ?, ?)
            ON CONFLICT(discord_id, encounter_id) DO UPDATE SET target_fighter_id = excluded.target_fighter_id
            """,
            (discord_id, encounter_id, target_fighter_id),
        )


def get_combat_target(discord_id: int, encounter_id: int) -> int | None:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT target_fighter_id FROM combat_target_picks
            WHERE discord_id = ? AND encounter_id = ?
            """,
            (discord_id, encounter_id),
        ).fetchone()
        return int(row["target_fighter_id"]) if row else None


def clear_combat_target(discord_id: int, encounter_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "DELETE FROM combat_target_picks WHERE discord_id = ? AND encounter_id = ?",
            (discord_id, encounter_id),
        )


def update_fighter_npc_name(fighter_id: int, npc_name: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE combat_fighters SET npc_name = ? WHERE id = ?",
            (npc_name[:100], fighter_id),
        )


def add_combat_fighter(
    encounter_id: int,
    *,
    discord_id: int | None = None,
    wolf_id: int | None = None,
    npc_name: str | None = None,
    npc_template: str | None = None,
    hp: int,
    max_hp: int,
) -> int:
    with get_db() as conn:
        if discord_id and not wolf_id:
            wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        cursor = conn.execute(
            """
            INSERT INTO combat_fighters
            (encounter_id, discord_id, wolf_id, npc_name, npc_template, hp, max_hp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (encounter_id, discord_id, wolf_id, npc_name, npc_template, hp, max_hp),
        )
        return cursor.lastrowid


def get_combat_fighters(encounter_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM combat_fighters WHERE encounter_id = ? ORDER BY initiative DESC, id ASC",
            (encounter_id,),
        ).fetchall()


def get_combat_fighter(encounter_id: int, fighter_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM combat_fighters WHERE encounter_id = ? AND id = ?",
            (encounter_id, fighter_id),
        ).fetchone()


def get_fighter_by_discord(encounter_id: int, discord_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        wolf_id = _resolve_wolf_id_conn(conn, discord_id)
        if wolf_id:
            row = conn.execute(
                """
                SELECT * FROM combat_fighters
                WHERE encounter_id = ? AND (wolf_id = ? OR discord_id = ?)
                """,
                (encounter_id, wolf_id, discord_id),
            ).fetchone()
            if row:
                return row
        return conn.execute(
            "SELECT * FROM combat_fighters WHERE encounter_id = ? AND discord_id = ?",
            (encounter_id, discord_id),
        ).fetchone()


def resolve_player_fighter(encounter_id: int, discord_id: int) -> sqlite3.Row | None:
    """Player fighter in this encounter; if several wolves, the one whose turn it is."""
    fighters = [
        f
        for f in get_combat_fighters(encounter_id)
        if f["discord_id"] == discord_id and not f["npc_name"]
    ]
    if not fighters:
        return get_fighter_by_discord(encounter_id, discord_id)
    if len(fighters) == 1:
        return fighters[0]
    from engine.combat_display import current_fighter_for_enc

    current = current_fighter_for_enc(encounter_id)
    if current and not current["npc_name"]:
        for fighter in fighters:
            if fighter["id"] == current["id"]:
                return fighter
    return None


def player_in_encounter(encounter_id: int, discord_id: int) -> bool:
    return any(
        f
        for f in get_combat_fighters(encounter_id)
        if f["discord_id"] == discord_id and not f["npc_name"]
    )


def rebuild_encounter_initiative(encounter_id: int) -> None:
    """Re-roll initiative for every fighter and restart turn order."""
    import json

    from engine.bestiary import stats_for_fighter
    from engine.character import attr_modifier
    from engine.combat import roll_initiative

    fighters = get_combat_fighters(encounter_id)
    rolls: list[tuple[int, int]] = []
    for fighter in fighters:
        if fighter["npc_name"]:
            stats = stats_for_fighter(fighter)
            die = random.randint(1, 20)
            mod = attr_modifier(stats["attr_dex"])
            total = die + mod
        else:
            user = (
                get_user_by_id(fighter["wolf_id"])
                if fighter["wolf_id"]
                else get_user(fighter["discord_id"])
            )
            if not user:
                total = random.randint(1, 20)
            else:
                _, _, total = roll_initiative(user)
        set_fighter_initiative(fighter["id"], total)
        rolls.append((fighter["id"], total))
    order = [fid for fid, _ in sorted(rolls, key=lambda x: -x[1])]
    start_combat_encounter(encounter_id, order)


def _sync_fighter_hp_to_user(conn: sqlite3.Connection, fighter, hp: int) -> None:
    hp = max(0, hp)
    wolf_id = fighter["wolf_id"] if "wolf_id" in fighter.keys() else None
    if wolf_id:
        conn.execute("UPDATE users SET hp = ? WHERE id = ?", (hp, wolf_id))
        return
    if fighter["discord_id"]:
        wid = _resolve_wolf_id_conn(conn, fighter["discord_id"])
        if wid:
            conn.execute("UPDATE users SET hp = ? WHERE id = ?", (hp, wid))


def update_fighter_hp(fighter_id: int, hp: int) -> None:
    with get_db() as conn:
        conn.execute("UPDATE combat_fighters SET hp = ? WHERE id = ?", (hp, fighter_id))


def update_fighter_combat_flags(fighter_id: int, **flags) -> None:
    """Merge combat flags (bools or pinned_by fighter id). False/None removes a key."""
    import json

    with get_db() as conn:
        row = conn.execute(
            "SELECT combat_flags FROM combat_fighters WHERE id = ?", (fighter_id,)
        ).fetchone()
        if not row:
            return
        raw = row["combat_flags"] if "combat_flags" in row.keys() else "{}"
        try:
            data = json.loads(raw or "{}")
            if not isinstance(data, dict):
                data = {}
        except json.JSONDecodeError:
            data = {}
        for key, value in flags.items():
            if value is False or value is None:
                data.pop(key, None)
            else:
                data[key] = value
        conn.execute(
            "UPDATE combat_fighters SET combat_flags = ? WHERE id = ?",
            (json.dumps(data), fighter_id),
        )


def record_injury_since(wolf_id: int, injury_key: str, day: int) -> None:
    """Stamp when an injury was acquired (for heal_days display; no auto-clear)."""
    import json

    with get_db() as conn:
        row = conn.execute(
            "SELECT injury_since FROM users WHERE id = ?", (wolf_id,)
        ).fetchone()
        if not row:
            return
        raw = row["injury_since"] if "injury_since" in row.keys() else "{}"
        try:
            since = json.loads(raw or "{}")
            if not isinstance(since, dict):
                since = {}
        except json.JSONDecodeError:
            since = {}
        if injury_key not in since:
            since[injury_key] = day
            conn.execute(
                "UPDATE users SET injury_since = ? WHERE id = ?",
                (json.dumps(since), wolf_id),
            )


def clear_injury_since(wolf_id: int, injury_key: str) -> None:
    import json

    with get_db() as conn:
        row = conn.execute(
            "SELECT injury_since FROM users WHERE id = ?", (wolf_id,)
        ).fetchone()
        if not row:
            return
        raw = row["injury_since"] if "injury_since" in row.keys() else "{}"
        try:
            since = json.loads(raw or "{}")
            if not isinstance(since, dict):
                return
        except json.JSONDecodeError:
            return
        if injury_key not in since:
            return
        del since[injury_key]
        conn.execute(
            "UPDATE users SET injury_since = ? WHERE id = ?",
            (json.dumps(since), wolf_id),
        )


def set_fighter_initiative(fighter_id: int, initiative: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE combat_fighters SET initiative = ? WHERE id = ?",
            (initiative, fighter_id),
        )


def start_combat_encounter(encounter_id: int, turn_order: list[int]) -> None:
    import json

    with get_db() as conn:
        conn.execute(
            """
            UPDATE combat_encounters
            SET status = 'active', round = 1, turn_order = ?, current_turn = 0
            WHERE id = ?
            """,
            (json.dumps(turn_order), encounter_id),
        )


def advance_combat_turn(encounter_id: int) -> None:
    import json

    with get_db() as conn:
        enc = conn.execute(
            "SELECT * FROM combat_encounters WHERE id = ?", (encounter_id,)
        ).fetchone()
        if not enc:
            return
        order = json.loads(enc["turn_order"] or "[]")
        if not order:
            return
        hp_map = {
            row["id"]: row["hp"]
            for row in conn.execute(
                "SELECT id, hp FROM combat_fighters WHERE encounter_id = ?",
                (encounter_id,),
            )
        }
        next_turn = enc["current_turn"]
        new_round = enc["round"]
        for _ in range(len(order)):
            next_turn = (next_turn + 1) % len(order)
            if next_turn == 0:
                new_round += 1
            if hp_map.get(order[next_turn], 0) > 0:
                break
        conn.execute(
            """
            UPDATE combat_encounters
            SET current_turn = ?, round = ?
            WHERE id = ?
            """,
            (next_turn, new_round, encounter_id),
        )


def yield_fighter(encounter_id: int, fighter_id: int) -> str:
    """
    Remove a fighter from combat (surrender). Syncs HP to profile for players.
    Returns: not_found | ended | ok
    """
    import json

    with get_db() as conn:
        enc = conn.execute(
            "SELECT * FROM combat_encounters WHERE id = ?", (encounter_id,)
        ).fetchone()
        if not enc:
            return "not_found"

        fighter = conn.execute(
            "SELECT * FROM combat_fighters WHERE encounter_id = ? AND id = ?",
            (encounter_id, fighter_id),
        ).fetchone()
        if not fighter:
            return "not_found"

        from engine.combat_status import release_pin_states

        release_pin_states(fighter_id, encounter_id)

        if fighter["discord_id"] or (fighter["wolf_id"] if "wolf_id" in fighter.keys() else None):
            _sync_fighter_hp_to_user(conn, fighter, fighter["hp"])

        old_order = json.loads(enc["turn_order"] or "[]")
        yield_idx = old_order.index(fighter_id) if fighter_id in old_order else None
        was_current = (
            enc["status"] == "active"
            and yield_idx is not None
            and yield_idx == enc["current_turn"]
        )
        old_turn = enc["current_turn"]

        conn.execute(
            "DELETE FROM combat_fighters WHERE id = ?",
            (fighter_id,),
        )

        remaining = conn.execute(
            """
            SELECT id FROM combat_fighters
            WHERE encounter_id = ?
            ORDER BY initiative DESC, id ASC
            """,
            (encounter_id,),
        ).fetchall()

        if len(remaining) < 2:
            for row in conn.execute(
                """
                SELECT discord_id, wolf_id, hp FROM combat_fighters
                WHERE encounter_id = ? AND (discord_id IS NOT NULL OR wolf_id IS NOT NULL)
                """,
                (encounter_id,),
            ):
                _sync_fighter_hp_to_user(conn, row, row["hp"])
            from engine.ambush_activity import finalize_ambush_activity

            finalize_ambush_activity(encounter_id)
            conn.execute(
                "UPDATE combat_encounters SET status = 'ended' WHERE id = ?",
                (encounter_id,),
            )
            conn.execute(
                "DELETE FROM combat_target_picks WHERE encounter_id = ?",
                (encounter_id,),
            )
            return "ended"

        remaining_ids = [row["id"] for row in remaining]
        # Preserve the established turn order minus the yielded fighter; append
        # any fighters not yet placed (e.g. mid-join) in initiative order.
        new_order = [fid for fid in old_order if fid in remaining_ids and fid != fighter_id]
        for fid in remaining_ids:
            if fid not in new_order:
                new_order.append(fid)

        if enc["status"] != "active":
            conn.execute(
                "UPDATE combat_encounters SET turn_order = ? WHERE id = ?",
                (json.dumps(new_order), encounter_id),
            )
            return "ok"

        if was_current:
            new_turn = old_turn % len(new_order)
        elif yield_idx is not None and yield_idx < old_turn:
            new_turn = max(0, old_turn - 1)
        else:
            new_turn = min(old_turn, len(new_order) - 1)

        conn.execute(
            """
            UPDATE combat_encounters
            SET turn_order = ?, current_turn = ?
            WHERE id = ?
            """,
            (json.dumps(new_order), new_turn, encounter_id),
        )
        return "ok"


def end_encounter(encounter_id: int) -> None:
    from engine.ambush_activity import finalize_ambush_activity

    finalize_ambush_activity(encounter_id)
    with get_db() as conn:
        fighters = conn.execute(
            """
            SELECT discord_id, wolf_id, hp FROM combat_fighters
            WHERE encounter_id = ? AND (discord_id IS NOT NULL OR wolf_id IS NOT NULL)
            """,
            (encounter_id,),
        ).fetchall()
        for f in fighters:
            _sync_fighter_hp_to_user(conn, f, f["hp"])
        conn.execute(
            "UPDATE combat_encounters SET status = 'ended' WHERE id = ?",
            (encounter_id,),
        )
        conn.execute(
            "DELETE FROM combat_target_picks WHERE encounter_id = ?",
            (encounter_id,),
        )


def sync_fighter_hp_to_user(discord_id: int, hp: int) -> None:
    wid = _resolve_wolf_id(discord_id)
    if not wid:
        return
    hp = max(0, hp)
    with get_db() as conn:
        conn.execute("UPDATE users SET hp = ? WHERE id = ?", (hp, wid))
        if hp <= 0:
            conn.execute(
                """
                UPDATE users
                SET condition = 'dying', death_save_round = 1,
                    death_save_fails = 0, death_save_successes = 0
                WHERE id = ? AND hp <= 0
                """,
                (wid,),
            )


# --- XP ---


def add_xp(discord_id: int, amount: int) -> int:
    if amount <= 0:
        return get_account(discord_id)["xp"]
    get_account(discord_id)
    with get_db() as conn:
        conn.execute(
            "UPDATE account_progress SET xp = xp + ? WHERE discord_id = ?",
            (amount, discord_id),
        )
        row = conn.execute(
            "SELECT xp FROM account_progress WHERE discord_id = ?", (discord_id,)
        ).fetchone()
        return row["xp"]


def try_grant_chat_xp(discord_id: int, guild_id: int, day: int) -> bool:
    """Grant +1 XP once per game day for being active in server chat."""
    if day <= 0 or not _resolve_wolf_id(discord_id):
        return False
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT last_claim_day FROM chat_xp_claims
            WHERE discord_id = ? AND guild_id = ?
            """,
            (discord_id, guild_id),
        ).fetchone()
        if row and row["last_claim_day"] >= day:
            return False
        if row:
            conn.execute(
                """
                UPDATE chat_xp_claims SET last_claim_day = ?
                WHERE discord_id = ? AND guild_id = ?
                """,
                (day, discord_id, guild_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO chat_xp_claims (discord_id, guild_id, last_claim_day)
                VALUES (?, ?, ?)
                """,
                (discord_id, guild_id, day),
            )
    add_xp(discord_id, 1)
    return True


def add_skill_rank(
    wolf_id: int,
    skill_key: str,
    amount: int = 1,
    *,
    grant_proficiency: bool = False,
) -> int:
    """Grant earned trait experience on a skill (quest rewards). Returns new earned bonus total."""
    from engine.character_traits import adjust_skill_trait_experience, get_earned_trait_bonus_for_wolf

    skill_key = skill_key.strip().lower()
    amount = max(0, int(amount))
    for _ in range(amount):
        ok, _msg = adjust_skill_trait_experience(wolf_id, skill_key, 1)
        if not ok:
            break
    if grant_proficiency:
        import json

        from engine.character import parse_proficiencies

        with get_db() as conn:
            row = conn.execute(
                "SELECT skill_proficiencies FROM users WHERE id = ?", (wolf_id,)
            ).fetchone()
            if row:
                profs = list(parse_proficiencies(row["skill_proficiencies"]))
                if skill_key not in profs:
                    profs.append(skill_key)
                    conn.execute(
                        "UPDATE users SET skill_proficiencies = ? WHERE id = ?",
                        (json.dumps(profs), wolf_id),
                    )
    return get_earned_trait_bonus_for_wolf(wolf_id, skill_key)


def get_skill_rank_for_wolf(wolf_id: int, skill_key: str) -> int:
    from engine.character_traits import get_earned_trait_bonus_for_wolf

    return get_earned_trait_bonus_for_wolf(wolf_id, skill_key)


def spend_xp(discord_id: int, cost: int) -> bool:
    get_account(discord_id)
    with get_db() as conn:
        row = conn.execute(
            "SELECT xp FROM account_progress WHERE discord_id = ?", (discord_id,)
        ).fetchone()
        if not row or row["xp"] < cost:
            return False
        conn.execute(
            "UPDATE account_progress SET xp = xp - ? WHERE discord_id = ?",
            (cost, discord_id),
        )
        return True


def set_birth_sex(discord_id: int, birth_sex: str) -> None:
    if birth_sex not in ("female", "male", "intersex", "nonbinary"):
        birth_sex = "female"
    update_user(discord_id, birth_sex=birth_sex)


def set_size_class(discord_id: int, size_class: str, *, wolf_id: int | None = None) -> tuple[bool, str | None]:
    from engine.combat_size import VALID_SIZE_CLASSES

    key = (size_class or "").strip().lower()
    if key in ("auto", "default", "reset", ""):
        value = ""
    elif key in VALID_SIZE_CLASSES:
        value = key
    else:
        return False, "Use **small**, **medium**, **large**, or **auto**."
    wid = wolf_id or _resolve_wolf_id(discord_id)
    if not wid:
        return False, "No wolf profile found."
    update_user(discord_id, wolf_id=wid, size_class=value)
    return True, None


def set_maw_belief(discord_id: int, belief: str, *, wolf_id: int | None = None) -> tuple[bool, str | None]:
    from engine.maw_belief import VALID_MAW_BELIEFS

    if belief not in VALID_MAW_BELIEFS:
        return False, "Unknown Maw belief."
    wid = wolf_id or _resolve_wolf_id(discord_id)
    if not wid:
        return False, "No wolf profile found."
    update_user(discord_id, wolf_id=wid, maw_belief=belief)
    return True, None


def set_character_lore(discord_id: int, lore_json: str, *, wolf_id: int | None = None) -> tuple[bool, str | None]:
    from engine.character_lore import parse_character_lore

    if not parse_character_lore(lore_json):
        return False, "Lore must include at least one non-empty field."
    wid = wolf_id or _resolve_wolf_id(discord_id)
    if not wid:
        return False, "No wolf profile found."
    update_user(discord_id, wolf_id=wid, character_lore=lore_json)
    return True, None


def set_sexuality(discord_id: int, sexuality: str) -> tuple[bool, str | None]:
    from engine.attraction import validate_set_sexuality

    user = get_user(discord_id)
    if not user:
        return False, "No wolf profile found."
    stored, err = validate_set_sexuality(user, sexuality)
    if err:
        return False, err
    update_user(discord_id, sexuality=stored)
    return True, None


def set_gender(discord_id: int, gender: str) -> None:
    """Legacy alias; updates birth_sex."""
    set_birth_sex(discord_id, gender)


def enter_dying_state(discord_id: int) -> None:
    set_user_conditions(
        discord_id,
        hp=0,
        condition="dying",
    )
    update_user(
        discord_id,
        death_save_round=1,
        death_save_fails=0,
        death_save_successes=0,
    )


def apply_death_save_result(discord_id: int, success: bool, nat20: bool = False) -> str:
    """Returns: stabilized | died | continue"""
    user = get_user(discord_id)
    if not user:
        return "none"
    if nat20:
        stabilize_patient(discord_id)
        from engine.wolf_journal import log_stabilized

        log_stabilized(user["id"], user["wolf_name"])
        return "stabilized"

    if not success:
        mark_wolf_dead(user["id"], "failed death saves")
        return "died"

    round_num = user["death_save_round"] or 1
    if round_num >= 3:
        stabilize_patient(discord_id)
        from engine.wolf_journal import log_stabilized

        log_stabilized(user["id"], user["wolf_name"])
        return "stabilized"

    update_user(discord_id, death_save_round=round_num + 1, death_save_successes=round_num)
    return "continue"


def revive_wolf(discord_id: int) -> str | None:
    """Revive a dead active wolf. Returns error code or None on success."""
    user = get_user(discord_id)
    if not user:
        return "not_registered"
    if user["condition"] != "dead":
        return "not_dead"

    from config import MAX_WOLF_AGE_MOONS, NEEDS_SURVIVAL_RESTORE, REVIVE_MOOD_FLOOR, REVIVE_OLD_AGE_RESET

    old_age = int(user["age_months"]) if "age_months" in user.keys() else 24
    new_age = REVIVE_OLD_AGE_RESET if old_age >= MAX_WOLF_AGE_MOONS else old_age

    with get_db() as conn:
        conn.execute(
            """
            UPDATE users
            SET condition = 'healthy',
                hp = 1,
                death_save_round = 0,
                death_save_fails = 0,
                death_save_successes = 0,
                cause_of_death = NULL,
                death_day = NULL,
                hunger = ?,
                thirst = ?,
                mood = MAX(?, mood),
                age_months = ?
            WHERE id = ?
            """,
            (
                NEEDS_SURVIVAL_RESTORE,
                NEEDS_SURVIVAL_RESTORE,
                REVIVE_MOOD_FLOOR,
                new_age,
                user["id"],
            ),
        )
    from engine.wolf_journal import log_revived

    log_revived(user["id"], user["wolf_name"])
    return None


def reincarnate_as_new_life(discord_id: int, new_name: str) -> str | None:
    """
    Dead wolf returns in a new body: new name, juvenile age, same build & standing.
    Clears prey/toy hoards. Returns error code or None on success.
    """
    from config import (
        HUNGER_DEFAULT,
        REINCARNATION_MOOD,
        REINCARNATION_START_AGE_MOONS,
        THIRST_DEFAULT,
    )
    from engine.aging import proficiencies_for_role, sync_role_to_age

    user = get_user(discord_id)
    if not user:
        return "not_registered"
    if user["condition"] != "dead":
        return "not_dead"

    cleaned, name_err = validate_wolf_name_available(
        new_name, exclude_wolf_id=user["id"], label="Wolf names"
    )
    if name_err:
        if "already taken" in name_err:
            return "name_taken"
        return f"name:{name_err}"
    if cleaned.lower() == user["wolf_name"].lower():
        return "same_name"

    old_role = user["wolf_role"] if "wolf_role" in user.keys() else "hunter"
    if old_role == "elder":
        old_role = "hunter"
    new_role = sync_role_to_age(REINCARNATION_START_AGE_MOONS, old_role)
    profs = proficiencies_for_role(new_role)
    max_hp = int(user["max_hp"])
    wolf_id = user["id"]

    with get_db() as conn:
        conn.execute("DELETE FROM prey_stacks WHERE wolf_id = ?", (wolf_id,))
        conn.execute("DELETE FROM herb_stacks WHERE wolf_id = ?", (wolf_id,))
        conn.execute("DELETE FROM amusement_stacks WHERE wolf_id = ?", (wolf_id,))
        conn.execute(
            """
            UPDATE users
            SET wolf_name = ?,
                age_months = ?,
                wolf_role = ?,
                skill_proficiencies = ?,
                condition = 'healthy',
                hp = ?,
                death_save_round = 0,
                death_save_fails = 0,
                death_save_successes = 0,
                cause_of_death = NULL,
                death_day = NULL,
                hunger = ?,
                thirst = ?,
                mood = ?,
                disease = NULL,
                active_injuries = '[]',
                exhaustion = 0
            WHERE id = ?
            """,
            (
                cleaned,
                REINCARNATION_START_AGE_MOONS,
                new_role,
                profs,
                max_hp,
                HUNGER_DEFAULT,
                THIRST_DEFAULT,
                REINCARNATION_MOOD,
                wolf_id,
            ),
        )
    from engine.wolf_journal import log_reincarnated

    log_reincarnated(wolf_id, user["wolf_name"], cleaned)
    return None


def stabilize_patient(discord_id: int) -> None:
    from config import NEEDS_SURVIVAL_RESTORE

    wid = _resolve_wolf_id(discord_id)
    if not wid:
        return
    with get_db() as conn:
        conn.execute(
            """
            UPDATE users
            SET hp = 1, condition = 'healthy',
                death_save_round = 0, death_save_fails = 0, death_save_successes = 0,
                hunger = CASE WHEN hunger <= 0 THEN ? ELSE hunger END,
                thirst = CASE WHEN thirst <= 0 THEN ? ELSE thirst END
            WHERE id = ?
            """,
            (NEEDS_SURVIVAL_RESTORE, NEEDS_SURVIVAL_RESTORE, wid),
        )


def get_bonded_mate(user) -> sqlite3.Row | None:
    if "bonded_mate_id" not in user.keys() or not user["bonded_mate_id"]:
        return None
    return get_user_by_id(user["bonded_mate_id"])


def get_mate_wolf(user) -> sqlite3.Row | None:
    if "mate_wolf_id" in user.keys() and user["mate_wolf_id"]:
        return get_user_by_id(user["mate_wolf_id"])
    if user["mate_discord_id"]:
        return get_user(user["mate_discord_id"])
    return None


def set_pregnancy(female_wolf_id: int, male_wolf_id: int, start_day: int) -> None:
    female = get_user_by_id(female_wolf_id)
    male = get_user_by_id(male_wolf_id)
    if not female or not male:
        return
    update_user(
        female["discord_id"],
        wolf_id=female_wolf_id,
        is_pregnant=1,
        pregnancy_start_day=start_day,
        mate_discord_id=male["discord_id"],
        mate_wolf_id=male_wolf_id,
    )
    set_bonded_mates(female_wolf_id, male_wolf_id)


def set_bonded_mates(wolf_a_id: int, wolf_b_id: int) -> None:
    wolf_a = get_user_by_id(wolf_a_id)
    wolf_b = get_user_by_id(wolf_b_id)
    if not wolf_a or not wolf_b:
        return
    update_user(wolf_a["discord_id"], wolf_id=wolf_a_id, bonded_mate_id=wolf_b_id)
    update_user(wolf_b["discord_id"], wolf_id=wolf_b_id, bonded_mate_id=wolf_a_id)
    from engine.wolf_journal import log_bonded

    log_bonded(wolf_a_id, wolf_b_id)


def clear_bonded_mates(wolf_id: int) -> None:
    user = get_user_by_id(wolf_id)
    if not user:
        return
    partner_id = user["bonded_mate_id"] if "bonded_mate_id" in user.keys() else None
    update_user(user["discord_id"], wolf_id=wolf_id, bonded_mate_id=None)
    if partner_id:
        partner = get_user_by_id(partner_id)
        if partner and partner["bonded_mate_id"] == wolf_id:
            update_user(partner["discord_id"], wolf_id=partner_id, bonded_mate_id=None)


def _death_context_conn(
    conn: sqlite3.Connection,
    wolf_id: int,
    *,
    day: int | None,
    guild_id: int | None,
) -> tuple[sqlite3.Row | None, int | None, int | None]:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (wolf_id,)).fetchone()
    if not row:
        return None, day, guild_id
    gid = guild_id
    if day is None and gid:
        world = conn.execute(
            "SELECT day_number FROM world_state WHERE guild_id = ?", (int(gid),)
        ).fetchone()
        if world:
            day = int(world["day_number"])
    return row, day, int(gid) if gid else None


def mark_wolf_dead(
    wolf_id: int,
    cause: str,
    *,
    conn: sqlite3.Connection | None = None,
    day: int | None = None,
    guild_id: int | None = None,
    grief: bool = True,
) -> dict | None:
    """Mark a wolf dead, record cause, append death log, optionally trigger mate grief."""
    cause = (cause or "unknown").strip() or "unknown"

    def _apply(c: sqlite3.Connection) -> dict | None:
        row, resolved_day, resolved_guild = _death_context_conn(
            c, wolf_id, day=day, guild_id=guild_id
        )
        if not row:
            return None
        c.execute(
            """
            UPDATE users
            SET condition = 'dead', hp = 0,
                cause_of_death = ?, death_day = ?
            WHERE id = ?
            """,
            (cause, resolved_day, wolf_id),
        )
        c.execute(
            """
            INSERT INTO wolf_death_log
            (wolf_id, discord_id, wolf_name, guild_id, cause, day)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                wolf_id,
                int(row["discord_id"]),
                row["wolf_name"],
                resolved_guild,
                cause,
                resolved_day,
            ),
        )
        if grief:
            result = handle_mate_grief_on_wolf_death(c, wolf_id)
        else:
            result = None
        from engine.wolf_journal import log_died

        unnamed_pup = (
            row["wolf_role"] == "pup"
            and int(row["naming_ceremony_day"] or 0) == 0
            if "naming_ceremony_day" in row.keys()
            else False
        )
        log_died(
            wolf_id,
            row["wolf_name"],
            cause,
            guild_id=resolved_guild,
            day=resolved_day,
            conn=c,
            unnamed_pup=unnamed_pup,
        )
        return result

    if conn is not None:
        return _apply(conn)
    with get_db() as c:
        return _apply(c)


def list_death_log(
    *,
    guild_id: int | None = None,
    discord_id: int | None = None,
    wolf_id: int | None = None,
    limit: int = 25,
) -> list[sqlite3.Row]:
    clauses: list[str] = []
    params: list = []
    if guild_id is not None:
        clauses.append("guild_id = ?")
        params.append(guild_id)
    if discord_id is not None:
        clauses.append("discord_id = ?")
        params.append(discord_id)
    if wolf_id is not None:
        clauses.append("wolf_id = ?")
        params.append(wolf_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(max(1, min(limit, 100)))
    with get_db() as conn:
        return conn.execute(
            f"""
            SELECT * FROM wolf_death_log
            {where}
            ORDER BY id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()


def list_current_dead_wolves(
    *,
    guild_id: int | None = None,
    discord_id: int | None = None,
) -> list[sqlite3.Row]:
    clauses = ["u.condition = 'dead'"]
    params: list = []
    if discord_id is not None:
        clauses.append("u.discord_id = ?")
        params.append(discord_id)
    if guild_id is not None:
        clauses.append(
            "u.id IN (SELECT wolf_id FROM wolf_death_log WHERE guild_id = ?)"
        )
        params.append(guild_id)
    where = " AND ".join(clauses)
    with get_db() as conn:
        return conn.execute(
            f"""
            SELECT u.id, u.discord_id, u.wolf_name, u.cause_of_death, u.death_day
            FROM users u
            WHERE {where}
            ORDER BY u.death_day DESC, u.wolf_name
            """,
            params,
        ).fetchall()


def handle_mate_grief_on_wolf_death(conn: sqlite3.Connection, dead_wolf_id: int) -> dict | None:
    """Clear mate bond and roll grief for the surviving partner."""
    dead = conn.execute("SELECT * FROM users WHERE id = ?", (dead_wolf_id,)).fetchone()
    if not dead:
        return None
    partner_id = dead["bonded_mate_id"] if "bonded_mate_id" in dead.keys() else None
    if not partner_id:
        return None
    partner = conn.execute("SELECT * FROM users WHERE id = ?", (partner_id,)).fetchone()
    conn.execute(
        "UPDATE users SET bonded_mate_id = NULL WHERE id IN (?, ?)",
        (dead_wolf_id, partner_id),
    )
    if not partner or partner["condition"] in ("dead", "dying"):
        return None
    from engine.disease_contract import try_grief_on_bond_loss

    note = try_grief_on_bond_loss(partner, bond_type="mate", conn=conn)
    if not note:
        return None
    return {
        "wolf_name": partner["wolf_name"],
        "discord_id": partner["discord_id"],
        "line": note,
    }


def clear_pregnancy(wolf_id: int) -> None:
    user = get_user_by_id(wolf_id)
    if not user:
        return
    update_user(
        user["discord_id"],
        wolf_id=wolf_id,
        is_pregnant=0,
        pregnancy_start_day=0,
        mate_discord_id=None,
        mate_wolf_id=None,
    )


def record_pup(
    mother_id: int,
    father_id: int | None,
    pup_name: str,
    born_day: int,
    stats_json: str,
    *,
    is_adopted: bool = False,
) -> int:
    """Deprecated; pups table removed; births use register_born_wolf."""
    raise NotImplementedError("Legacy pups ledger removed; use register_born_wolf.")


def get_pups_for_wolf(discord_id: int, limit: int = 10) -> list[sqlite3.Row]:
    """Deprecated; use get_lineage_children_for_discord."""
    return []


def add_pending_stillborn(
    *,
    discord_id: int,
    mother_wolf_id: int,
    pup_name: str,
    genetic_conditions: str,
    stats_json: str,
    father_wolf_id: int | None,
    pack_id: int | None,
    great_pack: str | None,
    birth_sex: str,
    born_day: int,
) -> int:
    cleaned_name, name_err = validate_wolf_name_available(pup_name, label="Pup names")
    if name_err:
        raise ValueError(name_err)
    pup_name = cleaned_name
    now = utcnow()
    with get_db() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO pending_stillborn (
                    discord_id, mother_wolf_id, pup_name, genetic_conditions, stats_json,
                    father_wolf_id, pack_id, great_pack, birth_sex, born_day, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    discord_id,
                    mother_wolf_id,
                    pup_name,
                    genetic_conditions,
                    stats_json,
                    father_wolf_id,
                    pack_id,
                    great_pack,
                    birth_sex,
                    born_day,
                    now,
                ),
            )
        except sqlite3.IntegrityError:
            raise ValueError(
                f"The name **{pup_name}** is already reserved by a dying pup "
                "awaiting neonatal care. Choose a different name."
            ) from None
        return cursor.lastrowid


def get_pending_stillborn(discord_id: int, pup_name: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pending_stillborn
            WHERE discord_id = ? AND LOWER(pup_name) = LOWER(?)
            LIMIT 1
            """,
            (discord_id, pup_name.strip()),
        ).fetchone()


def delete_pending_stillborn(row_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM pending_stillborn WHERE id = ?", (row_id,))


def expire_pending_stillborn_before_day(day_number: int) -> int:
    """Remove dying pups whose save window closed at sunrise."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM pending_stillborn WHERE born_day < ?",
            (day_number,),
        )
        return cursor.rowcount


def register_born_wolf(
    *,
    discord_id: int,
    wolf_name: str,
    mother_wolf_id: int,
    father_wolf_id: int | None,
    stats: dict,
    pack_id: int | None,
    great_pack: str | None,
    age_months: int = 3,
    birth_sex: str | None = None,
    genetic_conditions: str | None = None,
) -> int:
    import json

    from engine.aging import proficiencies_for_role, sync_role_to_age
    from engine.character import compute_max_hp
    from engine.role_restrictions import PUP_ROLE

    from engine.attraction import PUP_SEXUALITY

    cleaned_name, name_err = validate_wolf_name_available(wolf_name)
    if name_err:
        raise ValueError(name_err)
    wolf_name = cleaned_name

    months = max(0, int(age_months))
    role = sync_role_to_age(months, PUP_ROLE)
    proficiencies = proficiencies_for_role(role)
    max_hp = compute_max_hp(stats["attr_str"], stats["attr_con"])
    sex = birth_sex if birth_sex in ("female", "male", "intersex", "nonbinary") else "female"
    genetics_json = genetic_conditions if genetic_conditions else "[]"
    from config import ROLLOVER_TIMEZONE
    from engine.lunar import assign_birth_lunar_phase, rollover_now

    born_at = rollover_now(ROLLOVER_TIMEZONE)
    birth_lunar_phase = assign_birth_lunar_phase(born_at)
    now = utcnow()
    with get_db() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO users (
                    discord_id, wolf_name, pack_id, rank, great_pack, wolf_role,
                    birth_sex, sexuality, age_months, genetic_conditions,
                    attr_str, attr_dex, attr_con, attr_int, attr_cha, attr_wis,
                    skill_proficiencies, hp, max_hp,
                    bio_parent_1_id, bio_parent_2_id, is_born_pup,
                    birth_lunar_phase, last_lunar_aged_lunation,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    discord_id,
                    wolf_name.strip(),
                    pack_id,
                    "member",
                    great_pack,
                    role,
                    sex,
                    PUP_SEXUALITY,
                    months,
                    genetics_json,
                    stats["attr_str"],
                    stats["attr_dex"],
                    stats["attr_con"],
                    stats["attr_int"],
                    stats["attr_cha"],
                    stats["attr_wis"],
                    proficiencies,
                    max_hp,
                    max_hp,
                    mother_wolf_id,
                    father_wolf_id,
                    1,
                    birth_lunar_phase,
                    -1,
                    now,
                ),
            )
        except sqlite3.IntegrityError:
            raise ValueError(
                f"The name **{wolf_name}** is already taken by another wolf. "
                "Choose a different name."
            ) from None
        wolf_id = cursor.lastrowid
        conn.execute(
            "INSERT OR IGNORE INTO account_progress (discord_id) VALUES (?)",
            (discord_id,),
        )
        account = conn.execute(
            "SELECT active_wolf_id FROM account_progress WHERE discord_id = ?",
            (discord_id,),
        ).fetchone()
        if not account or not account["active_wolf_id"]:
            conn.execute(
                "UPDATE account_progress SET active_wolf_id = ? WHERE discord_id = ?",
                (wolf_id, discord_id),
            )
        if pack_id:
            _claim_pack_alpha_if_eligible(conn, pack_id, discord_id, role)
    if great_pack and great_pack in GREAT_PACKS:
        grant_great_pack_starting_herbs(wolf_id, great_pack)
    mother = get_user_by_id(mother_wolf_id)
    father = get_user_by_id(father_wolf_id) if father_wolf_id else None
    from engine.wolf_journal import log_born

    log_born(
        wolf_id,
        wolf_name.strip(),
        mother_name=mother["wolf_name"] if mother else None,
        father_name=father["wolf_name"] if father else None,
    )
    return wolf_id


def set_adoptive_parents(youth_wolf_id: int, parent1_id: int, parent2_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            """
            UPDATE users
            SET adopt_parent_1_id = ?, adopt_parent_2_id = ?
            WHERE id = ?
            """,
            (parent1_id, parent2_id, youth_wolf_id),
        )


def get_adopted_youth_for_parent(parent_wolf_id: int) -> list[sqlite3.Row]:
    from config import JUVENILE_MAX_MOONS

    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM users
            WHERE (adopt_parent_1_id = ? OR adopt_parent_2_id = ?)
              AND age_months < ?
            ORDER BY age_months ASC, id ASC
            """,
            (parent_wolf_id, parent_wolf_id, JUVENILE_MAX_MOONS),
        ).fetchall()


def get_pack_den_wolves(pack_id: int) -> list[sqlite3.Row]:
    """Pack members plus young wolves adopted into any member's den."""
    members = get_pack_members(pack_id)
    seen = {m["id"] for m in members}
    den = list(members)
    for member in members:
        for youth in get_adopted_youth_for_parent(member["id"]):
            if youth["id"] not in seen:
                seen.add(youth["id"])
                den.append(youth)
    return den


def wolf_display_name(wolf_id: int | None) -> str | None:
    if not wolf_id:
        return None
    row = get_user_by_id(wolf_id)
    return row["wolf_name"] if row else None


def format_lineage_for_profile(user) -> str | None:
    parts: list[str] = []
    bio1 = wolf_display_name(user["bio_parent_1_id"] if "bio_parent_1_id" in user.keys() else None)
    bio2 = wolf_display_name(user["bio_parent_2_id"] if "bio_parent_2_id" in user.keys() else None)
    if bio1 or bio2:
        names = " & ".join(n for n in (bio1, bio2) if n)
        parts.append(f"**Biological:** {names}")
    adopt1 = wolf_display_name(
        user["adopt_parent_1_id"] if "adopt_parent_1_id" in user.keys() else None
    )
    adopt2 = wolf_display_name(
        user["adopt_parent_2_id"] if "adopt_parent_2_id" in user.keys() else None
    )
    if adopt1 or adopt2:
        names = " & ".join(n for n in (adopt1, adopt2) if n)
        parts.append(f"**Adoptive:** {names}")
    offspring = get_lineage_children_for_wolf(user["id"], limit=6)
    if offspring:
        names = ", ".join(f"**{c['wolf_name']}**" for c in offspring[:5])
        if len(offspring) > 5:
            names += f" (+{len(offspring) - 5} more)"
        parts.append(f"**Offspring:** {names}")
    if "has_blooding" in user.keys() and user["has_blooding"]:
        parts.append("**Blooded**")
    return "\n".join(parts) if parts else None


def get_lineage_children_for_wolf(wolf_id: int, limit: int = 10) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM users
            WHERE bio_parent_1_id = ? OR bio_parent_2_id = ?
               OR adopt_parent_1_id = ? OR adopt_parent_2_id = ?
            ORDER BY age_months ASC, id ASC
            LIMIT ?
            """,
            (wolf_id, wolf_id, wolf_id, wolf_id, limit),
        ).fetchall()


def get_nursing_pups_for_mother(mother_wolf_id: int) -> list[sqlite3.Row]:
    """Biological pups still on mother's milk (under weaning age)."""
    from config import PUP_MAX_MOONS

    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM users
            WHERE bio_parent_1_id = ?
              AND age_months < ?
              AND condition NOT IN ('dead', 'dying')
            ORDER BY wolf_name COLLATE NOCASE
            """,
            (mother_wolf_id, PUP_MAX_MOONS),
        ).fetchall()


def get_pack_pups_needing_feed(pack_id: int) -> list[sqlite3.Row]:
    from config import PUP_MAX_MOONS

    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM users
            WHERE pack_id = ?
              AND age_months < ?
              AND condition NOT IN ('dead', 'dying')
            ORDER BY wolf_name COLLATE NOCASE
            """,
            (pack_id, PUP_MAX_MOONS),
        ).fetchall()


def get_lineage_children_for_discord(discord_id: int) -> list[sqlite3.Row]:
    wolves = list_user_wolves(discord_id)
    wolf_ids = [wolf["id"] for wolf in wolves]
    if not wolf_ids:
        return []
    placeholders = ",".join("?" * len(wolf_ids))
    params = wolf_ids * 4
    with get_db() as conn:
        return conn.execute(
            f"""
            SELECT * FROM users
            WHERE bio_parent_1_id IN ({placeholders})
               OR bio_parent_2_id IN ({placeholders})
               OR adopt_parent_1_id IN ({placeholders})
               OR adopt_parent_2_id IN ({placeholders})
            ORDER BY age_months ASC, id ASC
            """,
            params,
        ).fetchall()


# --- Wolf bonds & found families ---


def _bond_pair(wolf_a_id: int, wolf_b_id: int) -> tuple[int, int]:
    if wolf_a_id == wolf_b_id:
        raise ValueError("same_wolf")
    return (wolf_a_id, wolf_b_id) if wolf_a_id < wolf_b_id else (wolf_b_id, wolf_a_id)


def get_bonds_for_wolf(wolf_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM wolf_bonds
            WHERE wolf_a_id = ? OR wolf_b_id = ?
            ORDER BY bond_type ASC, strength DESC
            """,
            (wolf_id, wolf_id),
        ).fetchall()


def bump_sign_partner_streak(wolf_a_id: int, wolf_b_id: int, *, window_minutes: int) -> int:
    """
    Track repeat /sign interactions between a pair (either direction counts
    the same pair). Returns the streak count *after* this call: 1 if this is
    a fresh interaction (no prior one within window_minutes), else prior+1.
    Used to apply diminishing returns so two wolves can't sign-spam infinite
    free mood.
    """
    from engine.time_cooldowns import minutes_since_iso

    low, high = _bond_pair(wolf_a_id, wolf_b_id)
    now = utcnow()
    with get_db() as conn:
        row = conn.execute(
            "SELECT last_at, streak FROM sign_partner_streaks WHERE wolf_a_id = ? AND wolf_b_id = ?",
            (low, high),
        ).fetchone()
        elapsed = minutes_since_iso(row["last_at"]) if row else None
        if row and elapsed is not None and elapsed <= window_minutes:
            streak = int(row["streak"]) + 1
        else:
            streak = 1
        conn.execute(
            """
            INSERT INTO sign_partner_streaks (wolf_a_id, wolf_b_id, last_at, streak)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(wolf_a_id, wolf_b_id)
            DO UPDATE SET last_at = excluded.last_at, streak = excluded.streak
            """,
            (low, high, now, streak),
        )
    return streak


def bump_npc_sign_streak(npc_id: int, wolf_id: int, *, window_minutes: int) -> int:
    """Same idea as bump_sign_partner_streak, for `/npc sign` (not admin-gated,
    so a player could otherwise spam any NPC at their own wolf for free mood)."""
    from engine.time_cooldowns import minutes_since_iso

    now = utcnow()
    with get_db() as conn:
        row = conn.execute(
            "SELECT last_at, streak FROM npc_sign_streaks WHERE npc_id = ? AND wolf_id = ?",
            (npc_id, wolf_id),
        ).fetchone()
        elapsed = minutes_since_iso(row["last_at"]) if row else None
        if row and elapsed is not None and elapsed <= window_minutes:
            streak = int(row["streak"]) + 1
        else:
            streak = 1
        conn.execute(
            """
            INSERT INTO npc_sign_streaks (npc_id, wolf_id, last_at, streak)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(npc_id, wolf_id)
            DO UPDATE SET last_at = excluded.last_at, streak = excluded.streak
            """,
            (npc_id, wolf_id, now, streak),
        )
    return streak


def get_bond(wolf_a_id: int, wolf_b_id: int, bond_type: str) -> sqlite3.Row | None:
    if bond_type not in ("friendship", "rivalry", "kin", "mentor"):
        return None
    low, high = _bond_pair(wolf_a_id, wolf_b_id)
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM wolf_bonds
            WHERE wolf_a_id = ? AND wolf_b_id = ? AND bond_type = ?
            """,
            (low, high, bond_type),
        ).fetchone()


def set_bond(
    wolf_a_id: int,
    wolf_b_id: int,
    bond_type: str,
    *,
    strength: int = 40,
    note: str = "",
    day: int = 0,
) -> sqlite3.Row | None:
    if bond_type not in ("friendship", "rivalry", "kin", "mentor"):
        return None
    low, high = _bond_pair(wolf_a_id, wolf_b_id)
    strength = max(0, min(100, int(strength)))
    note = (note or "").strip()[:120]
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO wolf_bonds (wolf_a_id, wolf_b_id, bond_type, strength, note, created_day, updated_day)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(wolf_a_id, wolf_b_id, bond_type) DO UPDATE SET
                strength = excluded.strength,
                note = CASE WHEN excluded.note != '' THEN excluded.note ELSE wolf_bonds.note END,
                updated_day = excluded.updated_day
            """,
            (low, high, bond_type, strength, note, day, day),
        )
    return get_bond(low, high, bond_type)


def adjust_bond_strength(
    wolf_a_id: int,
    wolf_b_id: int,
    bond_type: str,
    delta: int,
    *,
    day: int = 0,
) -> sqlite3.Row | None:
    if bond_type not in ("friendship", "rivalry", "kin", "mentor"):
        return None
    if wolf_a_id == wolf_b_id:
        return None
    low, high = _bond_pair(wolf_a_id, wolf_b_id)
    existing = get_bond(low, high, bond_type)
    if existing:
        new_strength = max(0, min(100, int(existing["strength"]) + delta))
        if new_strength <= 0 and bond_type != "rivalry":
            clear_bond(low, high, bond_type)
            return None
        if new_strength <= 0:
            clear_bond(low, high, bond_type)
            return None
        with get_db() as conn:
            conn.execute(
                """
                UPDATE wolf_bonds SET strength = ?, updated_day = ?
                WHERE wolf_a_id = ? AND wolf_b_id = ? AND bond_type = ?
                """,
                (new_strength, day, low, high, bond_type),
            )
        return get_bond(low, high, bond_type)
    if delta <= 0:
        return None
    return set_bond(low, high, bond_type, strength=min(100, 40 + delta), day=day)


def clear_bond(wolf_a_id: int, wolf_b_id: int, bond_type: str) -> bool:
    if bond_type not in ("friendship", "rivalry", "kin", "mentor"):
        return False
    low, high = _bond_pair(wolf_a_id, wolf_b_id)
    with get_db() as conn:
        cur = conn.execute(
            """
            DELETE FROM wolf_bonds
            WHERE wolf_a_id = ? AND wolf_b_id = ? AND bond_type = ?
            """,
            (low, high, bond_type),
        )
        return cur.rowcount > 0


def count_bonds_for_wolf(wolf_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM wolf_bonds
            WHERE wolf_a_id = ? OR wolf_b_id = ?
            """,
            (wolf_id, wolf_id),
        ).fetchone()
        return int(row["c"]) if row else 0


def get_wolf_family(wolf_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT f.* FROM wolf_families f
            JOIN wolf_family_members m ON m.family_id = f.id
            WHERE m.wolf_id = ?
            """,
            (wolf_id,),
        ).fetchone()


def get_family_by_name(name: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM wolf_families WHERE name = ? COLLATE NOCASE",
            (name.strip(),),
        ).fetchone()


def get_family_members(family_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT u.wolf_name, u.id AS wolf_id, m.role
            FROM wolf_family_members m
            JOIN users u ON u.id = m.wolf_id
            WHERE m.family_id = ?
            ORDER BY
                CASE m.role
                    WHEN 'founder' THEN 0
                    WHEN 'parent' THEN 1
                    WHEN 'sibling' THEN 2
                    WHEN 'cub' THEN 3
                    ELSE 4
                END,
                u.wolf_name ASC
            """,
            (family_id,),
        ).fetchall()


def create_wolf_family(wolf_id: int, name: str, *, day: int = 0) -> tuple[sqlite3.Row | None, str | None]:
    name = name.strip()
    if len(name) < 2 or len(name) > 32:
        return None, "Family name must be 2-32 characters."
    if get_wolf_family(wolf_id):
        return None, "Leave your current found family first (`/bonds action:Family leave:true`)."
    if get_family_by_name(name):
        return None, "That family name is taken; ask to be invited or pick another name."
    now = utcnow()
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO wolf_families (name, founder_wolf_id, created_day, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (name, wolf_id, day, now),
        )
        family_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO wolf_family_members (family_id, wolf_id, role, joined_day)
            VALUES (?, ?, 'founder', ?)
            """,
            (family_id, wolf_id, day),
        )
    return get_family_by_name(name), None


def join_wolf_family(wolf_id: int, name: str, *, role: str = "member", day: int = 0) -> tuple[sqlite3.Row | None, str | None]:
    if get_wolf_family(wolf_id):
        return None, "You're already in a found family."
    family = get_family_by_name(name)
    if not family:
        return None, f"No found family named **{name.strip()}**; create it with `/bonds action:Family`."
    role = role if role in ("parent", "sibling", "cub", "member") else "member"
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO wolf_family_members (family_id, wolf_id, role, joined_day)
            VALUES (?, ?, ?, ?)
            """,
            (family["id"], wolf_id, role, day),
        )
    return get_wolf_family(wolf_id), None


def leave_wolf_family(wolf_id: int) -> tuple[bool, str | None]:
    family = get_wolf_family(wolf_id)
    if not family:
        return False, "You're not in a found family."
    with get_db() as conn:
        member = conn.execute(
            "SELECT role FROM wolf_family_members WHERE family_id = ? AND wolf_id = ?",
            (family["id"], wolf_id),
        ).fetchone()
        conn.execute(
            "DELETE FROM wolf_family_members WHERE family_id = ? AND wolf_id = ?",
            (family["id"], wolf_id),
        )
        remaining = conn.execute(
            "SELECT COUNT(*) AS c FROM wolf_family_members WHERE family_id = ?",
            (family["id"],),
        ).fetchone()
        if remaining and remaining["c"] == 0:
            conn.execute("DELETE FROM wolf_families WHERE id = ?", (family["id"],))
        elif member and member["role"] == "founder":
            next_f = conn.execute(
                """
                SELECT wolf_id FROM wolf_family_members
                WHERE family_id = ?
                ORDER BY joined_day ASC, wolf_id ASC
                LIMIT 1
                """,
                (family["id"],),
            ).fetchone()
            if next_f:
                conn.execute(
                    "UPDATE wolf_family_members SET role = 'founder' WHERE family_id = ? AND wolf_id = ?",
                    (family["id"], next_f["wolf_id"]),
                )
                conn.execute(
                    "UPDATE wolf_families SET founder_wolf_id = ? WHERE id = ?",
                    (next_f["wolf_id"], family["id"]),
                )
    return True, None


def create_pending_adoption(
    *,
    guild_id: int,
    channel_id: int,
    adopter_1_wolf_id: int,
    adopter_2_wolf_id: int,
    youth_wolf_id: int,
    youth_owner_discord_id: int,
    day_number: int,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pending_adoptions (
                guild_id, channel_id, adopter_1_wolf_id, adopter_2_wolf_id,
                youth_wolf_id, youth_owner_discord_id, day_number, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                channel_id,
                adopter_1_wolf_id,
                adopter_2_wolf_id,
                youth_wolf_id,
                youth_owner_discord_id,
                day_number,
                utcnow(),
            ),
        )
        return cursor.lastrowid


def set_pending_adoption_message(pending_id: int, message_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE pending_adoptions SET message_id = ? WHERE id = ?",
            (message_id, pending_id),
        )


def get_pending_adoption(pending_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM pending_adoptions WHERE id = ?",
            (pending_id,),
        ).fetchone()


def set_pending_adoption_status(pending_id: int, status: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE pending_adoptions SET status = ? WHERE id = ?",
            (status, pending_id),
        )


def get_pending_adoption_for_owner(discord_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pending_adoptions
            WHERE youth_owner_discord_id = ? AND status = 'pending'
            ORDER BY id DESC LIMIT 1
            """,
            (discord_id,),
        ).fetchone()


def get_pending_adoption_for_adopter_pair(wolf_id_a: int, wolf_id_b: int) -> sqlite3.Row | None:
    """Active adoption request from this bonded pair (either adopter slot order)."""
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pending_adoptions
            WHERE status = 'pending'
              AND (
                (adopter_1_wolf_id = ? AND adopter_2_wolf_id = ?)
                OR (adopter_1_wolf_id = ? AND adopter_2_wolf_id = ?)
              )
            ORDER BY id DESC LIMIT 1
            """,
            (wolf_id_a, wolf_id_b, wolf_id_b, wolf_id_a),
        ).fetchone()


def list_pending_adoptions() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM pending_adoptions WHERE status = 'pending' ORDER BY id ASC"
        ).fetchall()


def record_court_attempt(courter_wolf_id: int, target_wolf_id: int, day_number: int) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO court_history (courter_wolf_id, target_wolf_id, day_number)
            VALUES (?, ?, ?)
            """,
            (courter_wolf_id, target_wolf_id, day_number),
        )


def court_blocked_for_pair(courter_wolf_id: int, target_wolf_id: int, day_number: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM court_history
            WHERE courter_wolf_id = ? AND target_wolf_id = ? AND day_number = ?
            """,
            (courter_wolf_id, target_wolf_id, day_number),
        ).fetchone()
        return row is not None


def create_pending_mate(
    *,
    guild_id: int,
    channel_id: int,
    initiator_wolf_id: int,
    partner_wolf_id: int,
    partner_discord_id: int,
    day_number: int,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pending_mates (
                guild_id, channel_id, initiator_wolf_id, partner_wolf_id,
                partner_discord_id, day_number, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                channel_id,
                initiator_wolf_id,
                partner_wolf_id,
                partner_discord_id,
                day_number,
                utcnow(),
            ),
        )
        return cursor.lastrowid


def set_pending_mate_message(pending_id: int, message_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE pending_mates SET message_id = ? WHERE id = ?",
            (message_id, pending_id),
        )


def get_pending_mate(pending_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM pending_mates WHERE id = ?",
            (pending_id,),
        ).fetchone()


def get_pending_mate_for_partner(discord_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pending_mates
            WHERE partner_discord_id = ? AND status = 'pending'
            ORDER BY id DESC LIMIT 1
            """,
            (discord_id,),
        ).fetchone()


def get_pending_mate_for_pair(wolf_a_id: int, wolf_b_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pending_mates
            WHERE status = 'pending'
              AND (
                (initiator_wolf_id = ? AND partner_wolf_id = ?)
                OR (initiator_wolf_id = ? AND partner_wolf_id = ?)
              )
            ORDER BY id DESC LIMIT 1
            """,
            (wolf_a_id, wolf_b_id, wolf_b_id, wolf_a_id),
        ).fetchone()


def set_pending_mate_status(pending_id: int, status: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE pending_mates SET status = ? WHERE id = ?",
            (status, pending_id),
        )


def list_pending_mates() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM pending_mates WHERE status = 'pending' ORDER BY id ASC"
        ).fetchall()


def create_pending_role_feature(
    *,
    guild_id: int,
    discord_id: int,
    wolf_id: int,
    wolf_name: str,
    role_feature: str,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pending_role_features (
                guild_id, discord_id, wolf_id, wolf_name, role_feature, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (guild_id, discord_id, wolf_id, wolf_name, role_feature, utcnow()),
        )
        return cursor.lastrowid


def get_pending_role_feature(pending_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM pending_role_features WHERE id = ?",
            (pending_id,),
        ).fetchone()


def get_open_pending_for_wolf(wolf_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pending_role_features
            WHERE wolf_id = ? AND status = 'pending'
            ORDER BY id DESC LIMIT 1
            """,
            (wolf_id,),
        ).fetchone()


def list_open_pending_role_features(guild_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pending_role_features
            WHERE guild_id = ? AND status = 'pending'
            ORDER BY id ASC
            """,
            (guild_id,),
        ).fetchall()


def set_pending_role_feature_status(
    pending_id: int,
    status: str,
    *,
    resolved_by_discord_id: int | None = None,
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            UPDATE pending_role_features
            SET status = ?, resolved_at = ?, resolved_by_discord_id = ?
            WHERE id = ?
            """,
            (status, utcnow(), resolved_by_discord_id, pending_id),
        )


def get_pregnancy_where_partner(wolf_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE is_pregnant = 1 AND mate_wolf_id = ?",
            (wolf_id,),
        ).fetchone()


def format_pup_lineage_entry(
    child,
    viewer_wolf_ids: set[int],
    *,
    viewer_discord_id: int | None = None,
    day_number: int | None = None,
) -> str:
    from engine.aging import stage_for_age, stage_label
    from engine.nursing import pup_fed_today, pup_needs_milk_today

    stage = stage_label(stage_for_age(child["age_months"]))
    bio = (
        (child["bio_parent_1_id"] in viewer_wolf_ids if child["bio_parent_1_id"] else False)
        or (child["bio_parent_2_id"] in viewer_wolf_ids if child["bio_parent_2_id"] else False)
    )
    adopted = (
        (child["adopt_parent_1_id"] in viewer_wolf_ids if child["adopt_parent_1_id"] else False)
        or (child["adopt_parent_2_id"] in viewer_wolf_ids if child["adopt_parent_2_id"] else False)
    )
    if bio and adopted:
        tag = "biological · in your den"
    elif bio:
        tag = "biological"
    elif adopted:
        tag = "adopted into your den"
    else:
        tag = "young"
    owner = child["discord_id"]
    player_note = ""
    if owner and viewer_discord_id and owner != viewer_discord_id:
        player_note = f" · <@{owner}>"
    parents: list[str] = []
    for pid in (
        child["bio_parent_1_id"] if "bio_parent_1_id" in child.keys() else None,
        child["bio_parent_2_id"] if "bio_parent_2_id" in child.keys() else None,
    ):
        name = wolf_display_name(pid)
        if name:
            parents.append(f"**{name}**")
    if parents:
        tag += f" · parents: {' & '.join(parents)}"
    if day_number is not None:
        if pup_needs_milk_today(child, day_number):
            tag += " · **needs milk**"
        elif pup_fed_today(child, day_number):
            tag += " · fed today"
    return f"**{child['wolf_name']}**; {stage}, {child['age_months']} moons ({tag}){player_note}"


# --- Prey pile ---


def create_prey_pile(
    *,
    guild_id: int,
    channel_id: int,
    hunter_wolf_id: int,
    hunter_name: str,
    prey_label: str,
    prey_bones: int,
    day_number: int,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO prey_piles
            (guild_id, channel_id, hunter_wolf_id, hunter_name, prey_label,
             prey_bones, day_number, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?)
            """,
            (
                guild_id,
                channel_id,
                hunter_wolf_id,
                hunter_name,
                prey_label,
                prey_bones,
                day_number,
                utcnow(),
            ),
        )
        return cursor.lastrowid


def set_prey_pile_message(pile_id: int, message_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE prey_piles SET message_id = ? WHERE id = ?",
            (message_id, pile_id),
        )


def get_prey_pile(pile_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM prey_piles WHERE id = ?", (pile_id,)
        ).fetchone()


def get_open_prey_piles() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM prey_piles WHERE status = 'open' AND message_id IS NOT NULL"
        ).fetchall()


def close_prey_piles_for_guild(guild_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE prey_piles SET status = 'closed' WHERE guild_id = ? AND status = 'open'",
            (guild_id,),
        )


def wolves_available_for_prey_pile(discord_id: int, pile_id: int) -> list[sqlite3.Row]:
    """Wolves on this account that have not yet responded to the pile."""
    wolves = list_user_wolves(discord_id)
    return [w for w in wolves if not get_prey_pile_response(pile_id, w["id"])]


def get_prey_pile_response(pile_id: int, wolf_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM prey_pile_responses WHERE pile_id = ? AND wolf_id = ?",
            (pile_id, wolf_id),
        ).fetchone()


def record_prey_pile_response(
    pile_id: int, wolf_id: int, wolf_name: str, choice: str
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO prey_pile_responses (pile_id, wolf_id, wolf_name, choice, responded_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pile_id, wolf_id, wolf_name, choice, utcnow()),
        )


def get_prey_pile_response_summary(pile_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT choice, COUNT(*) AS count
            FROM prey_pile_responses
            WHERE pile_id = ?
            GROUP BY choice
            ORDER BY count DESC
            """,
            (pile_id,),
        ).fetchall()


def count_prey_pile_responses(pile_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM prey_pile_responses WHERE pile_id = ?",
            (pile_id,),
        ).fetchone()
        return row["c"] if row else 0


# --- Food hoard (Wolvden-style carcasses) ---


def add_prey_stack(
    wolf_id: int,
    prey_key: str,
    *,
    uses_left: int,
    bone_value: int,
    acquired_day: int,
    guild_id: int,
    is_rotting: int = 0,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO prey_stacks
            (wolf_id, guild_id, prey_key, uses_left, bone_value, acquired_day, is_rotting)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (wolf_id, guild_id, prey_key, uses_left, bone_value, acquired_day, is_rotting),
        )
        return cursor.lastrowid


def get_prey_stacks(wolf_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM prey_stacks
            WHERE wolf_id = ? AND uses_left > 0
            ORDER BY is_rotting ASC, acquired_day DESC, id DESC
            """,
            (wolf_id,),
        ).fetchall()


def get_prey_stack(stack_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM prey_stacks WHERE id = ?", (stack_id,)
        ).fetchone()


def get_todays_prey_stacks(wolf_id: int, day: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM prey_stacks
            WHERE wolf_id = ? AND acquired_day >= ? AND uses_left > 0
            ORDER BY is_rotting ASC, bone_value DESC, id DESC
            """,
            (wolf_id, day),
        ).fetchall()


def pick_prey_stack_for_pile(wolf_id: int, day: int) -> sqlite3.Row | None:
    stacks = get_todays_prey_stacks(wolf_id, day)
    if not stacks:
        return None
    fresh = [s for s in stacks if not s["is_rotting"]]
    return fresh[0] if fresh else None


def update_prey_stack_uses(stack_id: int, uses_left: int) -> None:
    with get_db() as conn:
        if uses_left <= 0:
            conn.execute("DELETE FROM prey_stacks WHERE id = ?", (stack_id,))
        else:
            conn.execute(
                "UPDATE prey_stacks SET uses_left = ? WHERE id = ?",
                (uses_left, stack_id),
            )


def remove_prey_stack(stack_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM prey_stacks WHERE id = ?", (stack_id,))


def rot_prey_stacks(guild_id: int, day: int) -> list[dict]:
    """Mark rotting prey, delete spoiled carcasses. Returns rollover notes for owners."""
    from engine.prey_items import PREY_ROTTEN_GRACE_DAYS, is_forage_food, prey_meta, spoilage_terms

    notes: list[dict] = []
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT ps.*, u.wolf_name, u.discord_id
            FROM prey_stacks ps
            JOIN users u ON u.id = ps.wolf_id
            WHERE ps.guild_id = ?
            """,
            (guild_id,),
        ).fetchall()
        for stack in rows:
            age = day - stack["acquired_day"]
            rot_days = prey_meta(stack["prey_key"]).get("rot_days", 5)
            meta = prey_meta(stack["prey_key"])
            terms = spoilage_terms(stack["prey_key"])
            forage = is_forage_food(stack["prey_key"])
            if age >= rot_days + PREY_ROTTEN_GRACE_DAYS:
                conn.execute("DELETE FROM prey_stacks WHERE id = ?", (stack["id"],))
                gone = "rotted to mush and was left for the flies" if forage else "spoiled and was dragged from the hoard"
                notes.append(
                    {
                        "wolf_name": stack["wolf_name"],
                        "discord_id": stack["discord_id"],
                        "line": f"**{meta['name']}** {gone}.",
                    }
                )
            elif age >= rot_days and not stack["is_rotting"]:
                conn.execute(
                    "UPDATE prey_stacks SET is_rotting = 1 WHERE id = ?",
                    (stack["id"],),
                )
                tail = "eat soon" if forage else "eat at risk or `/salvage`"
                notes.append(
                    {
                        "wolf_name": stack["wolf_name"],
                        "discord_id": stack["discord_id"],
                        "line": (
                            f"**{meta['name']}** is **{terms['rotting']}** (`/food` — {tail})."
                        ),
                    }
                )
    return notes


# --- Pack food reserve (shared den stash, slower rot) ---


def get_pack_members(pack_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM users
            WHERE pack_id = ? AND condition != 'dead'
            ORDER BY wolf_name COLLATE NOCASE
            """,
            (pack_id,),
        ).fetchall()


def pick_sniff_encounter_wolf(
    *,
    exclude_wolf_id: int,
    exclude_discord_id: int,
    pack_id: int | None,
    great_pack: str | None,
) -> sqlite3.Row | None:
    """Random alive wolf for a sniff encounter; packmate, then faction, then anyone."""
    with get_db() as conn:
        if pack_id:
            row = conn.execute(
                """
                SELECT * FROM users
                WHERE pack_id = ? AND id != ? AND discord_id != ?
                  AND condition != 'dead'
                ORDER BY RANDOM() LIMIT 1
                """,
                (pack_id, exclude_wolf_id, exclude_discord_id),
            ).fetchone()
            if row:
                return row
        if great_pack:
            row = conn.execute(
                """
                SELECT * FROM users
                WHERE great_pack = ? AND id != ? AND discord_id != ?
                  AND condition != 'dead'
                ORDER BY RANDOM() LIMIT 1
                """,
                (great_pack, exclude_wolf_id, exclude_discord_id),
            ).fetchone()
            if row:
                return row
        return conn.execute(
            """
            SELECT * FROM users
            WHERE id != ? AND discord_id != ? AND condition != 'dead'
            ORDER BY RANDOM() LIMIT 1
            """,
            (exclude_wolf_id, exclude_discord_id),
        ).fetchone()


def add_pack_prey_stack(
    pack_id: int,
    prey_key: str,
    *,
    uses_left: int,
    bone_value: int,
    acquired_day: int,
    guild_id: int,
    deposited_by: int | None = None,
    is_rotting: int = 0,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pack_prey_stacks
            (pack_id, guild_id, prey_key, uses_left, bone_value, acquired_day,
             is_rotting, deposited_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pack_id,
                guild_id,
                prey_key,
                uses_left,
                bone_value,
                acquired_day,
                is_rotting,
                deposited_by,
            ),
        )
        return cursor.lastrowid


def get_pack_prey_stacks(pack_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pack_prey_stacks
            WHERE pack_id = ? AND uses_left > 0
            ORDER BY is_rotting ASC, acquired_day DESC, id DESC
            """,
            (pack_id,),
        ).fetchall()


def get_pack_prey_stack(stack_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM pack_prey_stacks WHERE id = ?", (stack_id,)
        ).fetchone()


def update_pack_prey_stack_uses(stack_id: int, uses_left: int) -> None:
    with get_db() as conn:
        if uses_left <= 0:
            conn.execute("DELETE FROM pack_prey_stacks WHERE id = ?", (stack_id,))
        else:
            conn.execute(
                "UPDATE pack_prey_stacks SET uses_left = ? WHERE id = ?",
                (uses_left, stack_id),
            )


def remove_pack_prey_stack(stack_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM pack_prey_stacks WHERE id = ?", (stack_id,))


def add_pack_herb_stack(
    pack_id: int,
    herb_key: str,
    *,
    form: str,
    potency: int,
    quantity: int,
    acquired_day: int,
    guild_id: int,
    deposited_by: int | None = None,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pack_herb_stacks
            (pack_id, guild_id, herb_key, form, potency, quantity, acquired_day, deposited_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pack_id,
                guild_id,
                herb_key,
                form,
                potency,
                quantity,
                acquired_day,
                deposited_by,
            ),
        )
        return cursor.lastrowid


def get_pack_herb_stacks(pack_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pack_herb_stacks
            WHERE pack_id = ? AND quantity > 0
            ORDER BY acquired_day DESC, id DESC
            """,
            (pack_id,),
        ).fetchall()


def get_pack_herb_stack(stack_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM pack_herb_stacks WHERE id = ?", (stack_id,)
        ).fetchone()


def update_pack_herb_stack(stack_id: int, **fields) -> None:
    allowed = {"quantity", "form", "potency", "acquired_day"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    cols = ", ".join(f"{k} = ?" for k in updates)
    vals = list(updates.values()) + [stack_id]
    with get_db() as conn:
        conn.execute(f"UPDATE pack_herb_stacks SET {cols} WHERE id = ?", vals)


def remove_pack_herb_stack(stack_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM pack_herb_stacks WHERE id = ?", (stack_id,))


def get_wolf_rivalry(wolf_id: int, rival_key: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM wolf_rivalries WHERE wolf_id = ? AND rival_key = ?",
            (wolf_id, rival_key),
        ).fetchone()


def list_wolf_rivalries(wolf_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM wolf_rivalries WHERE wolf_id = ? ORDER BY grudge DESC",
            (wolf_id,),
        ).fetchall()


def adjust_wolf_rivalry_grudge(
    wolf_id: int, rival_key: str, delta: int, *, day: int, grudge_min: int = 0, grudge_max: int = 100
) -> int:
    """Insert or update a wolf's grudge with a rival NPC; returns the new grudge."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT grudge, encounters FROM wolf_rivalries WHERE wolf_id = ? AND rival_key = ?",
            (wolf_id, rival_key),
        ).fetchone()
        if row is None:
            new_grudge = max(grudge_min, min(grudge_max, delta))
            conn.execute(
                """
                INSERT INTO wolf_rivalries (wolf_id, rival_key, grudge, encounters, last_encounter_day)
                VALUES (?, ?, ?, 1, ?)
                """,
                (wolf_id, rival_key, new_grudge, day),
            )
            return new_grudge
        new_grudge = max(grudge_min, min(grudge_max, int(row["grudge"]) + delta))
        conn.execute(
            """
            UPDATE wolf_rivalries
            SET grudge = ?, encounters = encounters + 1, last_encounter_day = ?
            WHERE wolf_id = ? AND rival_key = ?
            """,
            (new_grudge, day, wolf_id, rival_key),
        )
        return new_grudge


def add_rp_prompt(
    guild_id: int,
    text: str,
    *,
    pack: str | None = None,
    mood: str | None = None,
    plot_phase: int | None = None,
    submitted_by: int | None = None,
    status: str = "pending",
    created_day: int | None = None,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO rp_prompts
            (guild_id, text, pack, mood, plot_phase, status, submitted_by, created_day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (guild_id, text, pack, mood, plot_phase, status, submitted_by, created_day),
        )
        return cursor.lastrowid


def get_rp_prompt(prompt_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM rp_prompts WHERE id = ?", (prompt_id,)
        ).fetchone()


def list_rp_prompts(
    guild_id: int,
    *,
    status: str | None = None,
    pack: str | None = None,
    mood: str | None = None,
    plot_phase: int | None = None,
) -> list[sqlite3.Row]:
    clauses = ["guild_id = ?"]
    params: list = [guild_id]
    if status is not None:
        clauses.append("status = ?")
        params.append(status)
    if pack is not None:
        clauses.append("pack = ?")
        params.append(pack)
    if mood is not None:
        clauses.append("mood = ?")
        params.append(mood)
    if plot_phase is not None:
        clauses.append("plot_phase = ?")
        params.append(plot_phase)
    where = " AND ".join(clauses)
    with get_db() as conn:
        return conn.execute(
            f"SELECT * FROM rp_prompts WHERE {where} ORDER BY id DESC",
            params,
        ).fetchall()


def set_rp_prompt_status(prompt_id: int, status: str, reviewed_by: int | None = None) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE rp_prompts SET status = ?, reviewed_by = ? WHERE id = ?",
            (status, reviewed_by, prompt_id),
        )


def delete_rp_prompt(prompt_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM rp_prompts WHERE id = ?", (prompt_id,))


def set_pack_feedall_day(pack_id: int, day: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE packs SET last_feedall_day = ? WHERE id = ?",
            (day, pack_id),
        )


def set_pack_drinkall_day(pack_id: int, day: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE packs SET last_drinkall_day = ? WHERE id = ?",
            (day, pack_id),
        )


def update_pack_season_goal(pack_id: int, **fields) -> None:
    allowed = {"season_stash_deposits", "season_stash_goal_met", "season_goal_epoch"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    clause = ", ".join(f"{k} = ?" for k in updates)
    with get_db() as conn:
        conn.execute(
            f"UPDATE packs SET {clause} WHERE id = ?",
            list(updates.values()) + [pack_id],
        )


def rot_pack_prey_stacks(guild_id: int, day: int) -> list[dict]:
    """Rot pack reserve carcasses; slower than personal hoard. Returns rollover notes."""
    from config import PACK_STASH_ROT_BONUS_DAYS
    from engine.prey_items import PREY_ROTTEN_GRACE_DAYS, prey_meta

    notes: list[dict] = []
    removed = 0
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT ps.*, p.name AS pack_name
            FROM pack_prey_stacks ps
            JOIN packs p ON p.id = ps.pack_id
            WHERE ps.guild_id = ?
            """,
            (guild_id,),
        ).fetchall()
        for stack in rows:
            age = day - stack["acquired_day"]
            meta = prey_meta(stack["prey_key"])
            rot_days = meta.get("rot_days", 5) + PACK_STASH_ROT_BONUS_DAYS
            pack_label = stack["pack_name"] if stack["pack_name"] else "Den"
            if age >= rot_days + PREY_ROTTEN_GRACE_DAYS:
                conn.execute("DELETE FROM pack_prey_stacks WHERE id = ?", (stack["id"],))
                removed += 1
                notes.append(
                    {
                        "wolf_name": pack_label,
                        "discord_id": None,
                        "line": (
                            f"Den reserve **{meta['name']}** spoiled and was cleared from `/pack stash`."
                        ),
                    }
                )
            elif age >= rot_days and not stack["is_rotting"]:
                conn.execute(
                    "UPDATE pack_prey_stacks SET is_rotting = 1 WHERE id = ?",
                    (stack["id"],),
                )
                notes.append(
                    {
                        "wolf_name": pack_label,
                        "discord_id": None,
                        "line": (
                            f"Den reserve **{meta['name']}** is **rotting** "
                            "(`/pack stash` — communal feed at gut-sickness risk)."
                        ),
                    }
                )
    return notes


# --- Amusement toys ---


def add_amusement_stack(wolf_id: int, item_key: str, *, uses_left: int) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO amusement_stacks (wolf_id, item_key, uses_left)
            VALUES (?, ?, ?)
            """,
            (wolf_id, item_key, uses_left),
        )
        return cursor.lastrowid


def get_amusement_stacks(wolf_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM amusement_stacks
            WHERE wolf_id = ? AND uses_left > 0
            ORDER BY id DESC
            """,
            (wolf_id,),
        ).fetchall()


def get_amusement_stack(stack_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM amusement_stacks WHERE id = ?", (stack_id,)
        ).fetchone()


def update_amusement_stack_uses(stack_id: int, uses_left: int) -> None:
    with get_db() as conn:
        if uses_left <= 0:
            conn.execute("DELETE FROM amusement_stacks WHERE id = ?", (stack_id,))
        else:
            conn.execute(
                "UPDATE amusement_stacks SET uses_left = ? WHERE id = ?",
                (uses_left, stack_id),
            )


def remove_amusement_stack(stack_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM amusement_stacks WHERE id = ?", (stack_id,))


def transfer_amusement_stack(stack_id: int, new_wolf_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM amusement_stacks WHERE id = ?", (stack_id,)
        ).fetchone()
        if not row:
            return False
        conn.execute(
            "UPDATE amusement_stacks SET wolf_id = ? WHERE id = ?",
            (new_wolf_id, stack_id),
        )
        return True


def add_pack_amusement_stack(
    pack_id: int,
    item_key: str,
    *,
    uses_left: int,
    guild_id: int,
    deposited_by: int | None = None,
) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pack_amusement_stacks
            (pack_id, guild_id, item_key, uses_left, deposited_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pack_id, guild_id, item_key, uses_left, deposited_by),
        )
        return cursor.lastrowid


def get_pack_amusement_stacks(pack_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM pack_amusement_stacks
            WHERE pack_id = ? AND uses_left > 0
            ORDER BY id DESC
            """,
            (pack_id,),
        ).fetchall()


def get_pack_amusement_stack(stack_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM pack_amusement_stacks WHERE id = ?", (stack_id,)
        ).fetchone()


def update_pack_amusement_stack_uses(stack_id: int, uses_left: int) -> None:
    with get_db() as conn:
        if uses_left <= 0:
            conn.execute("DELETE FROM pack_amusement_stacks WHERE id = ?", (stack_id,))
        else:
            conn.execute(
                "UPDATE pack_amusement_stacks SET uses_left = ? WHERE id = ?",
                (uses_left, stack_id),
            )


def remove_pack_amusement_stack(stack_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM pack_amusement_stacks WHERE id = ?", (stack_id,))


def adjust_mood(wolf_id: int, delta: int) -> int:
    from config import MOOD_MAX, MOOD_MIN

    with get_db() as conn:
        row = conn.execute("SELECT mood FROM users WHERE id = ?", (wolf_id,)).fetchone()
        if not row:
            return 0
        mood = max(MOOD_MIN, min(MOOD_MAX, int(row["mood"]) + delta))
        conn.execute("UPDATE users SET mood = ? WHERE id = ?", (mood, wolf_id))
        return mood


def adjust_hunger(wolf_id: int, delta: int) -> int:
    from config import HUNGER_MAX, HUNGER_MIN

    with get_db() as conn:
        row = conn.execute("SELECT hunger FROM users WHERE id = ?", (wolf_id,)).fetchone()
        if not row:
            return 0
        hunger = max(HUNGER_MIN, min(HUNGER_MAX, int(row["hunger"]) + delta))
        conn.execute("UPDATE users SET hunger = ? WHERE id = ?", (hunger, wolf_id))
        return hunger


def adjust_thirst(wolf_id: int, delta: int) -> int:
    from config import THIRST_MAX, THIRST_MIN

    with get_db() as conn:
        row = conn.execute("SELECT thirst FROM users WHERE id = ?", (wolf_id,)).fetchone()
        if not row:
            return 0
        thirst = max(THIRST_MIN, min(THIRST_MAX, int(row["thirst"]) + delta))
        conn.execute("UPDATE users SET thirst = ? WHERE id = ?", (thirst, wolf_id))
        return thirst


def get_remnants(wolf_id: int) -> int:
    with get_db() as conn:
        row = conn.execute("SELECT remnants FROM users WHERE id = ?", (wolf_id,)).fetchone()
        return int(row["remnants"]) if row else 0


def add_remnants(wolf_id: int, amount: int) -> int:
    if amount <= 0:
        return get_remnants(wolf_id)
    with get_db() as conn:
        row = conn.execute("SELECT remnants FROM users WHERE id = ?", (wolf_id,)).fetchone()
        if not row:
            return 0
        total = int(row["remnants"]) + amount
        conn.execute("UPDATE users SET remnants = ? WHERE id = ?", (total, wolf_id))
        return total


def spend_remnants(wolf_id: int, amount: int) -> bool:
    if amount <= 0:
        return True
    with get_db() as conn:
        row = conn.execute("SELECT remnants FROM users WHERE id = ?", (wolf_id,)).fetchone()
        if not row or int(row["remnants"]) < amount:
            return False
        conn.execute(
            "UPDATE users SET remnants = remnants - ? WHERE id = ?",
            (amount, wolf_id),
        )
        return True


# --- Herb stacks (fresh / dried / prepared) ---


def add_herb_stack(
    wolf_id: int,
    herb_key: str,
    *,
    guild_id: int,
    acquired_day: int,
    form: str = "fresh",
    potency: int = 100,
    conn: sqlite3.Connection | None = None,
) -> int:
    sql = """
            INSERT INTO herb_stacks
            (wolf_id, guild_id, herb_key, form, acquired_day, potency)
            VALUES (?, ?, ?, ?, ?, ?)
            """
    params = (wolf_id, guild_id, herb_key, form, acquired_day, potency)
    if conn is not None:
        cur = conn.execute(sql, params)
        return int(cur.lastrowid)
    with get_db() as inner:
        cur = inner.execute(sql, params)
        return int(cur.lastrowid)


def get_herb_stacks(wolf_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM herb_stacks
            WHERE wolf_id = ?
            ORDER BY acquired_day DESC, id DESC
            """,
            (wolf_id,),
        ).fetchall()


def get_herb_stack(stack_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM herb_stacks WHERE id = ?", (stack_id,)
        ).fetchone()


def update_herb_stack(stack_id: int, **fields) -> None:
    if not fields:
        return
    cols = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [stack_id]
    with get_db() as conn:
        conn.execute(f"UPDATE herb_stacks SET {cols} WHERE id = ?", vals)


def remove_herb_stack(stack_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM herb_stacks WHERE id = ?", (stack_id,))


def transfer_herb_stack(stack_id: int, new_wolf_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM herb_stacks WHERE id = ?", (stack_id,)
        ).fetchone()
        if not row:
            return False
        conn.execute(
            "UPDATE herb_stacks SET wolf_id = ? WHERE id = ?",
            (new_wolf_id, stack_id),
        )
        return True


# --- Herb seeds & gardens (grow-your-own) ---


def get_herb_seeds(wolf_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT herb_key, qty FROM herb_seeds WHERE wolf_id = ? AND qty > 0 ORDER BY herb_key",
            (wolf_id,),
        ).fetchall()


def get_herb_seed_qty(wolf_id: int, herb_key: str) -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT qty FROM herb_seeds WHERE wolf_id = ? AND herb_key = ?",
            (wolf_id, herb_key),
        ).fetchone()
        return int(row["qty"]) if row else 0


def add_herb_seeds(wolf_id: int, herb_key: str, qty: int = 1, *, conn=None) -> None:
    sql = """
        INSERT INTO herb_seeds (wolf_id, herb_key, qty)
        VALUES (?, ?, ?)
        ON CONFLICT(wolf_id, herb_key) DO UPDATE SET qty = qty + excluded.qty
    """
    params = (wolf_id, herb_key, qty)
    if conn is not None:
        conn.execute(sql, params)
        return
    with get_db() as c:
        c.execute(sql, params)


def consume_herb_seed(wolf_id: int, herb_key: str, qty: int = 1) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT qty FROM herb_seeds WHERE wolf_id = ? AND herb_key = ?",
            (wolf_id, herb_key),
        ).fetchone()
        if not row or int(row["qty"]) < qty:
            return False
        conn.execute(
            "UPDATE herb_seeds SET qty = qty - ? WHERE wolf_id = ? AND herb_key = ?",
            (qty, wolf_id, herb_key),
        )
        return True


def add_herb_planting(
    wolf_id: int,
    herb_key: str,
    *,
    pack_id: int,
    guild_id: int,
    day: int,
    season: str,
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO herb_gardens
            (wolf_id, pack_id, guild_id, herb_key, planted_day, season_planted,
             last_tended_day, last_eval_day, health, dead)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 100, 0)
            """,
            (wolf_id, pack_id, guild_id, herb_key, day, season, day - 1, day),
        )
        return int(cur.lastrowid)


def get_herb_plantings(wolf_id: int) -> list[sqlite3.Row]:
    """Legacy: plantings by planter wolf id."""
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM herb_gardens WHERE wolf_id = ? ORDER BY planted_day ASC, id ASC",
            (wolf_id,),
        ).fetchall()


def get_pack_herb_plantings(pack_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM herb_gardens WHERE pack_id = ? ORDER BY planted_day ASC, id ASC",
            (pack_id,),
        ).fetchall()


def pack_garden_tended_today(pack_id: int, day: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT last_garden_tend_day FROM packs WHERE id = ?",
            (pack_id,),
        ).fetchone()
        if not row:
            return False
        return int(row["last_garden_tend_day"]) >= day


def mark_pack_garden_tended(pack_id: int, day: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE packs SET last_garden_tend_day = ? WHERE id = ?",
            (day, pack_id),
        )


def get_herb_planting(planting_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM herb_gardens WHERE id = ?", (planting_id,)
        ).fetchone()


def update_herb_planting(planting_id: int, **fields) -> None:
    if not fields:
        return
    allowed = {"last_tended_day", "last_eval_day", "health", "dead"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return
    cols = ", ".join(f"{k} = ?" for k in sets)
    with get_db() as conn:
        conn.execute(
            f"UPDATE herb_gardens SET {cols} WHERE id = ?",
            (*sets.values(), planting_id),
        )


def remove_herb_planting(planting_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM herb_gardens WHERE id = ?", (planting_id,))


def count_herb_plantings(wolf_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM herb_gardens WHERE wolf_id = ? AND dead = 0",
            (wolf_id,),
        ).fetchone()
        return int(row["n"]) if row else 0


def count_pack_herb_plantings(pack_id: int) -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM herb_gardens WHERE pack_id = ? AND dead = 0",
            (pack_id,),
        ).fetchone()
        return int(row["n"]) if row else 0


def rot_herb_stacks(guild_id: int, day: int) -> int:
    """Remove spoiled fresh/prepared herbs; fade old dried stacks."""
    from config import (
        HERB_DRIED_STORAGE_DAYS,
        HERB_FRESH_DRY_DAYS,
        HERB_PREPARED_FORMS,
        HERB_PREPARED_STORAGE_DAYS,
    )
    from engine.herb_buffs import herb_storage_multiplier

    removed = 0
    with get_db() as conn:
        rows = conn.execute(
            "SELECT hs.*, u.herb_buffs, u.last_rest_day FROM herb_stacks hs "
            "JOIN users u ON u.id = hs.wolf_id "
            "WHERE hs.guild_id = ?",
            (guild_id,),
        ).fetchall()
        for stack in rows:
            age = day - int(stack["acquired_day"])
            form = stack["form"]
            user_row = {
                "herb_buffs": stack["herb_buffs"],
                "last_rest_day": stack["last_rest_day"],
            }
            mult = herb_storage_multiplier(user_row, day)
            fresh_limit = max(1, int(HERB_FRESH_DRY_DAYS * mult))
            dried_limit = max(1, int(HERB_DRIED_STORAGE_DAYS * mult))
            prepared_limit = max(1, int(HERB_PREPARED_STORAGE_DAYS * mult))
            if form == "fresh" and age > fresh_limit:
                conn.execute("DELETE FROM herb_stacks WHERE id = ?", (stack["id"],))
                removed += 1
            elif form in HERB_PREPARED_FORMS and age > prepared_limit:
                conn.execute("DELETE FROM herb_stacks WHERE id = ?", (stack["id"],))
                removed += 1
            elif form == "dried" and age > dried_limit:
                conn.execute("DELETE FROM herb_stacks WHERE id = ?", (stack["id"],))
                removed += 1
            elif form == "dried" and age > dried_limit // 2:
                pot = int(stack["potency"])
                if pot > 50:
                    conn.execute(
                        "UPDATE herb_stacks SET potency = ? WHERE id = ?",
                        (max(50, pot - 15), stack["id"]),
                    )
    return removed


def create_collab_hunt(
    *,
    guild_id: int,
    channel_id: int,
    leader_wolf_id: int,
    pack_id: int,
    day_number: int,
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO collab_hunts (guild_id, channel_id, leader_wolf_id, pack_id, day_number)
            VALUES (?, ?, ?, ?, ?)
            """,
            (guild_id, channel_id, leader_wolf_id, pack_id, day_number),
        )
        return int(cur.lastrowid)


def add_collab_hunt_member(
    hunt_id: int,
    *,
    wolf_id: int,
    wolf_name: str,
    discord_id: int,
    hunt_role: str = "flank",
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO collab_hunt_members (hunt_id, wolf_id, wolf_name, discord_id, hunt_role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (hunt_id, wolf_id, wolf_name, discord_id, hunt_role),
        )


def get_collab_hunt(hunt_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM collab_hunts WHERE id = ?", (hunt_id,)).fetchone()


def get_collab_hunt_members(hunt_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM collab_hunt_members WHERE hunt_id = ? ORDER BY joined_at ASC",
            (hunt_id,),
        ).fetchall()


def set_collab_hunt_message(hunt_id: int, message_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE collab_hunts SET message_id = ? WHERE id = ?",
            (message_id, hunt_id),
        )


def set_collab_hunt_status(hunt_id: int, status: str, *, result_text: str | None = None) -> None:
    with get_db() as conn:
        if result_text is not None:
            conn.execute(
                "UPDATE collab_hunts SET status = ?, result_text = ? WHERE id = ?",
                (status, result_text, hunt_id),
            )
        else:
            conn.execute(
                "UPDATE collab_hunts SET status = ? WHERE id = ?",
                (status, hunt_id),
            )


def get_open_collab_hunts() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM collab_hunts WHERE status = 'open' AND message_id IS NOT NULL"
        ).fetchall()


def close_collab_hunts_for_guild(guild_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE collab_hunts SET status = 'cancelled' WHERE guild_id = ? AND status IN ('open', 'encounter')",
            (guild_id,),
        )


def wolf_in_open_collab_hunt(wolf_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM collab_hunt_members m
            JOIN collab_hunts h ON h.id = m.hunt_id
            WHERE m.wolf_id = ? AND h.status IN ('open', 'encounter')
            LIMIT 1
            """,
            (wolf_id,),
        ).fetchone()
        return row is not None


def get_open_collab_hunt_by_leader(leader_wolf_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM collab_hunts
            WHERE leader_wolf_id = ? AND status IN ('open', 'encounter')
            LIMIT 1
            """,
            (leader_wolf_id,),
        ).fetchone()


def set_encounter_collab_hunt(encounter_id: int, hunt_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE combat_encounters SET collab_hunt_id = ? WHERE id = ?",
            (hunt_id, encounter_id),
        )


def set_encounter_collab_patrol(encounter_id: int, patrol_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE combat_encounters SET collab_patrol_id = ? WHERE id = ?",
            (patrol_id, encounter_id),
        )


def create_collab_patrol(
    *,
    guild_id: int,
    channel_id: int,
    leader_wolf_id: int,
    pack_id: int,
    day_number: int,
    patrol_kind: str = "survey",
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO collab_patrols
                (guild_id, channel_id, leader_wolf_id, pack_id, day_number, patrol_kind)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (guild_id, channel_id, leader_wolf_id, pack_id, day_number, patrol_kind),
        )
        return int(cur.lastrowid)


def add_collab_patrol_member(
    patrol_id: int,
    *,
    wolf_id: int,
    wolf_name: str,
    discord_id: int,
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO collab_patrol_members (patrol_id, wolf_id, wolf_name, discord_id)
            VALUES (?, ?, ?, ?)
            """,
            (patrol_id, wolf_id, wolf_name, discord_id),
        )


def get_collab_patrol(patrol_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM collab_patrols WHERE id = ?", (patrol_id,)).fetchone()


def get_collab_patrol_members(patrol_id: int) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM collab_patrol_members WHERE patrol_id = ? ORDER BY joined_at ASC",
            (patrol_id,),
        ).fetchall()


def set_collab_patrol_message(patrol_id: int, message_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE collab_patrols SET message_id = ? WHERE id = ?",
            (message_id, patrol_id),
        )


def set_collab_patrol_status(patrol_id: int, status: str, *, result_text: str | None = None) -> None:
    with get_db() as conn:
        if result_text is not None:
            conn.execute(
                "UPDATE collab_patrols SET status = ?, result_text = ? WHERE id = ?",
                (status, result_text, patrol_id),
            )
        else:
            conn.execute(
                "UPDATE collab_patrols SET status = ? WHERE id = ?",
                (status, patrol_id),
            )


def get_open_collab_patrols() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM collab_patrols WHERE status = 'open' AND message_id IS NOT NULL"
        ).fetchall()


def close_collab_patrols_for_guild(guild_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE collab_patrols SET status = 'cancelled' WHERE guild_id = ? AND status IN ('open', 'encounter')",
            (guild_id,),
        )


def wolf_in_open_collab_patrol(wolf_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM collab_patrol_members m
            JOIN collab_patrols p ON p.id = m.patrol_id
            WHERE m.wolf_id = ? AND p.status IN ('open', 'encounter')
            LIMIT 1
            """,
            (wolf_id,),
        ).fetchone()
        return row is not None


def get_open_collab_patrol_by_leader(leader_wolf_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            """
            SELECT * FROM collab_patrols
            WHERE leader_wolf_id = ? AND status IN ('open', 'encounter')
            LIMIT 1
            """,
            (leader_wolf_id,),
        ).fetchone()
