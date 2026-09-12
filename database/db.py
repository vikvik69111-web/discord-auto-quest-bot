from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Quest:
    id: int
    user_id: int
    title: str
    description: str
    difficulty: str
    quest_type: str
    target: int
    progress: int
    status: str
    reward_points: int
    reward_claimed: int
    created_at: str
    completed_at: str | None


class QuestDatabase:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self) -> Iterable[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    points INTEGER NOT NULL DEFAULT 0,
                    total_completed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS quests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    quest_type TEXT NOT NULL,
                    target INTEGER NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'active',
                    reward_points INTEGER NOT NULL,
                    reward_claimed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_state (
                    state_key TEXT PRIMARY KEY,
                    state_value TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leaderboard_cache (
                    user_id INTEGER PRIMARY KEY,
                    points INTEGER NOT NULL,
                    rank INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def ensure_user(self, user_id: int) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, points, total_completed, created_at)
                VALUES (?, 0, 0, ?)
                ON CONFLICT(user_id) DO NOTHING
                """,
                (user_id, utcnow_iso()),
            )

    def has_active_quest(self, user_id: int) -> bool:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM quests WHERE user_id=? AND status='active' LIMIT 1",
                (user_id,),
            ).fetchone()
            return row is not None

    def create_quest(
        self,
        user_id: int,
        title: str,
        description: str,
        difficulty: str,
        quest_type: str,
        target: int,
        reward_points: int,
    ) -> int:
        self.ensure_user(user_id)
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO quests (
                    user_id, title, description, difficulty, quest_type,
                    target, progress, status, reward_points, reward_claimed, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 'active', ?, 0, ?)
                """,
                (
                    user_id,
                    title,
                    description,
                    difficulty,
                    quest_type,
                    target,
                    reward_points,
                    utcnow_iso(),
                ),
            )
            return int(cursor.lastrowid)

    def get_active_quest(self, user_id: int) -> Quest | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM quests
                WHERE user_id=? AND status='active'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            return self._to_quest(row) if row else None

    def get_last_completed_unclaimed(self, user_id: int) -> Quest | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM quests
                WHERE user_id=? AND status='completed' AND reward_claimed=0
                ORDER BY completed_at DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            return self._to_quest(row) if row else None

    def complete_active_quest(self, user_id: int, progress: int) -> Quest | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM quests
                WHERE user_id=? AND status='active'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if row is None:
                return None

            normalized_progress = max(int(progress), 0)
            target = int(row["target"])
            status = "completed" if normalized_progress >= target else "active"
            completed_at = utcnow_iso() if status == "completed" else None
            conn.execute(
                """
                UPDATE quests
                SET progress=?, status=?, completed_at=?
                WHERE id=?
                """,
                (normalized_progress, status, completed_at, row["id"]),
            )
            updated = conn.execute(
                "SELECT * FROM quests WHERE id=?",
                (row["id"],),
            ).fetchone()
            return self._to_quest(updated)

    def claim_reward(self, user_id: int) -> int:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM quests
                WHERE user_id=? AND status='completed' AND reward_claimed=0
                ORDER BY completed_at DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if row is None:
                return 0

            reward_points = int(row["reward_points"])
            conn.execute(
                "UPDATE quests SET reward_claimed=1 WHERE id=?",
                (row["id"],),
            )
            conn.execute(
                """
                UPDATE users
                SET points = points + ?, total_completed = total_completed + 1
                WHERE user_id=?
                """,
                (reward_points, user_id),
            )
            return reward_points

    def auto_claim_all_rewards(self) -> int:
        total_rewards = 0
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT id, user_id, reward_points FROM quests
                WHERE status='completed' AND reward_claimed=0
                """
            ).fetchall()
            for row in rows:
                reward_points = int(row["reward_points"])
                conn.execute(
                    "UPDATE quests SET reward_claimed=1 WHERE id=?",
                    (row["id"],),
                )
                conn.execute(
                    """
                    UPDATE users
                    SET points = points + ?, total_completed = total_completed + 1
                    WHERE user_id=?
                    """,
                    (reward_points, int(row["user_id"])),
                )
                total_rewards += reward_points
        return total_rewards

    def get_known_users(self) -> list[int]:
        with self.connection() as conn:
            rows = conn.execute("SELECT user_id FROM users").fetchall()
            return [int(row["user_id"]) for row in rows]

    def set_daily_marker(self, key: str, value: str) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO daily_state(state_key, state_value)
                VALUES(?, ?)
                ON CONFLICT(state_key) DO UPDATE SET state_value=excluded.state_value
                """,
                (key, value),
            )

    def get_daily_marker(self, key: str) -> str | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT state_value FROM daily_state WHERE state_key=?",
                (key,),
            ).fetchone()
            return str(row["state_value"]) if row else None

    def update_leaderboard_cache(self) -> None:
        now = utcnow_iso()
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT user_id, points
                FROM users
                ORDER BY points DESC, total_completed DESC, user_id ASC
                LIMIT 20
                """
            ).fetchall()
            conn.execute("DELETE FROM leaderboard_cache")
            for index, row in enumerate(rows, start=1):
                conn.execute(
                    """
                    INSERT INTO leaderboard_cache(user_id, points, rank, updated_at)
                    VALUES(?, ?, ?, ?)
                    """,
                    (int(row["user_id"]), int(row["points"]), index, now),
                )

    def get_leaderboard(self, limit: int = 10) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT user_id, points, rank FROM leaderboard_cache
                ORDER BY rank ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            if rows:
                return [dict(row) for row in rows]

            fallback = conn.execute(
                """
                SELECT user_id, points
                FROM users
                ORDER BY points DESC, total_completed DESC, user_id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            ranked = []
            for index, row in enumerate(fallback, start=1):
                ranked.append(
                    {"user_id": int(row["user_id"]), "points": int(row["points"]), "rank": index}
                )
            return ranked

    def _to_quest(self, row: sqlite3.Row) -> Quest:
        return Quest(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            title=str(row["title"]),
            description=str(row["description"]),
            difficulty=str(row["difficulty"]),
            quest_type=str(row["quest_type"]),
            target=int(row["target"]),
            progress=int(row["progress"]),
            status=str(row["status"]),
            reward_points=int(row["reward_points"]),
            reward_claimed=int(row["reward_claimed"]),
            created_at=str(row["created_at"]),
            completed_at=row["completed_at"],
        )
