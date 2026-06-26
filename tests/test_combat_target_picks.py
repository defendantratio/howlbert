"""Combat target locking and auto-target for lone prey."""

import database as db
from engine.combat_display import pick_combat_target
from engine.hunt_combat import start_large_prey_fight
from utils.combat_views import _attack_target_options


def _setup_hunt(discord_id: int, wolf_name: str) -> tuple:
    db.init_db()
    with db.get_db() as conn:
        conn.execute("DELETE FROM combat_target_picks")
        conn.execute("DELETE FROM combat_fighters")
        conn.execute("DELETE FROM combat_encounters")
        conn.execute("DELETE FROM users WHERE discord_id = ?", (discord_id,))
        conn.execute(
            """
            INSERT INTO users (
                discord_id, wolf_name, pack_id, rank, created_at,
                hp, max_hp, hunger, thirst, exhaustion, condition, wolf_role
            ) VALUES (?, ?, 1, 'hunter', 0, 20, 20, 80, 80, 0, 'healthy', 'hunter')
            """,
            (discord_id, wolf_name),
        )
    user = db.get_user(discord_id)
    enc_id = start_large_prey_fight(user, guild_id=1, channel_id=1)
    fighters = db.get_combat_fighters(enc_id)
    hunter = next(f for f in fighters if not f["npc_name"])
    prey = next(f for f in fighters if f["npc_name"])
    return user, enc_id, hunter, prey


def test_hunt_auto_targets_prey_on_start():
    user, enc_id, hunter, prey = _setup_hunt(880001, "HuntAutoA")
    assert db.get_combat_target(user["discord_id"], enc_id) == prey["id"]


def test_pick_combat_target_rejects_self_lock():
    user, enc_id, hunter, prey = _setup_hunt(880002, "HuntAutoB")
    db.set_combat_target(user["discord_id"], enc_id, hunter["id"])
    picked = pick_combat_target(user["discord_id"], enc_id, hunter["id"])
    assert picked == prey["id"]
    assert picked != hunter["id"]


def test_attack_target_options_exclude_hunter():
    user, enc_id, hunter, prey = _setup_hunt(880003, "AshbarkSim")
    from engine.combat_display import current_fighter_for_enc

    for _ in range(40):
        if current_fighter_for_enc(enc_id) and not current_fighter_for_enc(enc_id)["npc_name"]:
            break
        user, enc_id, hunter, prey = _setup_hunt(880003, "AshbarkSim")
    options = _attack_target_options(enc_id, None)
    values = {int(o.value) for o in options}
    assert hunter["id"] not in values
    assert prey["id"] in values
