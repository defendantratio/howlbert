from config import PRESTIGE_TIERS


def get_tier_info(tier: int) -> dict:
    for info in PRESTIGE_TIERS:
        if info["tier"] == tier:
            return info
    return PRESTIGE_TIERS[0]


def calculate_tier(account) -> int:
    achieved = 0
    for info in PRESTIGE_TIERS:
        if (
            account["legacy_score"] >= info["legacy_req"]
            and account["total_quests"] >= info["quests_req"]
            and account["total_hunts"] >= info["hunts_req"]
            and account["total_retirements"] >= info["retirements_req"]
        ):
            achieved = info["tier"]
    return achieved


def bone_bonus_pct(tier: int) -> int:
    return get_tier_info(tier)["bone_bonus_pct"]


def apply_bone_bonus(amount: int, tier: int) -> int:
    if amount <= 0:
        return 0
    bonus = bone_bonus_pct(tier)
    return max(0, int(amount * (100 + bonus) / 100))


def legacy_from_retirement(standing: int, bones: int, quests_done: int) -> int:
    return standing * 15 + bones // 3 + quests_done * 25


def legacy_from_quest(reward_bones: int, standing_reward: int) -> int:
    return standing_reward * 5 + reward_bones // 2


def format_retirement_breakdown(standing: int, bones: int, quests_done: int) -> str:
    """Preview legacy from retiring the active wolf."""
    standing_pts = standing * 15
    bone_pts = bones // 3
    quest_pts = quests_done * 25
    total = legacy_from_retirement(standing, bones, quests_done)
    return (
        f"standing **{standing}** × 15 = **{standing_pts}**\n"
        f"bones **{bones}** ÷ 3 = **{bone_pts}**\n"
        f"quests **{quests_done}** × 25 = **{quest_pts}**\n"
        f"→ **{total}** legacy if you retire now"
    )


def next_tier_requirements(current_tier: int) -> dict | None:
    for info in PRESTIGE_TIERS:
        if info["tier"] == current_tier + 1:
            return info
    return None


def format_requirement_progress(current: int, required: int) -> str:
    """player-facing progress line with a check when met."""
    mark = "✓" if current >= required else "·"
    return f"{mark} {current} / {required}"


def unlocked_tier_lines(current_tier: int) -> list[str]:
    """summarize bone bonuses from tiers already reached."""
    lines: list[str] = []
    for info in PRESTIGE_TIERS:
        tier = info["tier"]
        if tier <= 0 or tier > current_tier:
            continue
        bonus = info["bone_bonus_pct"]
        lines.append(f"**tier {tier} {info['name']}**; +{bonus}% bones")
    return lines
