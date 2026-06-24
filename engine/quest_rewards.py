"""Quest XP and skill-rank reward display."""

from __future__ import annotations

from config import QUEST_SKILL_REWARDS, QUEST_XP_REWARDS
from rpg_rules import SKILLS, SKILL_RANK_BONUS
from utils.currency import format_bones


def quest_xp_reward(quest_key: str) -> int:
    return QUEST_XP_REWARDS.get(quest_key, 1)


def quest_skill_reward(quest_key: str) -> tuple[str, int] | None:
    return QUEST_SKILL_REWARDS.get(quest_key)


def format_quest_reward_suffix(quest_key: str) -> str:
    """Extra reward text (XP / skill rank) without bones."""
    parts: list[str] = []
    xp = quest_xp_reward(quest_key)
    if xp:
        parts.append(f"+{xp} XP")
    skill_reward = quest_skill_reward(quest_key)
    if skill_reward:
        skill_key, rank_gain = skill_reward
        label = SKILLS.get(skill_key, ((), skill_key))[1]
        parts.append(f"**{label}** rank +{rank_gain}")
    return " · ".join(parts)


def format_quest_reward_line(quest_key: str, reward_bones: int) -> str:
    """Bones plus XP / skill extras for quest board embeds."""
    line = format_bones(reward_bones)
    extra = format_quest_reward_suffix(quest_key)
    if extra:
        line = f"{line} · {extra}"
    return line
