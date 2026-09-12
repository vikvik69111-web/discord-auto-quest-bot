from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedQuest:
    title: str
    description: str
    difficulty: str
    quest_type: str
    target: int
    reward_points: int


DIFFICULTY_MULTIPLIER: dict[str, tuple[int, int, float]] = {
    "easy": (3, 8, 1.0),
    "medium": (8, 15, 1.6),
    "hard": (15, 30, 2.4),
}


def generate_quest(
    difficulty_levels: tuple[str, ...],
    quest_types: tuple[str, ...],
    base_reward: int,
) -> GeneratedQuest:
    difficulty = random.choice(difficulty_levels)
    quest_type = random.choice(quest_types)
    target_min, target_max, reward_mul = DIFFICULTY_MULTIPLIER.get(
        difficulty, (3, 8, 1.0)
    )
    target = random.randint(target_min, target_max)
    reward = max(int(base_reward * reward_mul), 1)

    title = f"{difficulty.title()} {quest_type.title()} Quest"
    description = (
        f"Complete {target} {quest_type} actions to finish this {difficulty} quest."
    )
    return GeneratedQuest(
        title=title,
        description=description,
        difficulty=difficulty,
        quest_type=quest_type,
        target=target,
        reward_points=reward,
    )
