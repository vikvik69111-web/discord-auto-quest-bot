from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional at runtime
    def load_dotenv() -> None:
        return None


load_dotenv()


def _parse_csv(value: str, fallback: list[str]) -> list[str]:
    parsed = [item.strip() for item in value.split(",") if item.strip()]
    return parsed or fallback


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    discord_bot_token: str
    database_path: str = "database/quests.db"
    default_reward_points: int = 100
    auto_reward_distribution: bool = False
    quest_difficulty_levels: tuple[str, ...] = ("easy", "medium", "hard")
    quest_types: tuple[str, ...] = ("messages", "reactions", "time")


def get_settings() -> Settings:
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    return Settings(
        discord_bot_token=token,
        database_path=os.getenv("DATABASE_PATH", "database/quests.db"),
        default_reward_points=int(os.getenv("DEFAULT_REWARD_POINTS", "100")),
        auto_reward_distribution=_parse_bool(
            os.getenv("AUTO_REWARD_DISTRIBUTION"), default=False
        ),
        quest_difficulty_levels=tuple(
            _parse_csv(
                os.getenv("QUEST_DIFFICULTY_LEVELS", "easy,medium,hard"),
                ["easy", "medium", "hard"],
            )
        ),
        quest_types=tuple(
            _parse_csv(
                os.getenv("QUEST_TYPES", "messages,reactions,time"),
                ["messages", "reactions", "time"],
            )
        ),
    )
