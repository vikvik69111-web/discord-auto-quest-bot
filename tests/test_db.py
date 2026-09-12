import tempfile
import unittest
from pathlib import Path

from database.db import QuestDatabase


class QuestDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_quests.db")
        self.db = QuestDatabase(self.db_path)
        self.user_id = 12345

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_fetch_active_quest(self) -> None:
        self.db.create_quest(
            user_id=self.user_id,
            title="Test Quest",
            description="Do something",
            difficulty="easy",
            quest_type="messages",
            target=5,
            reward_points=100,
        )
        quest = self.db.get_active_quest(self.user_id)
        self.assertIsNotNone(quest)
        assert quest is not None
        self.assertEqual(quest.status, "active")
        self.assertEqual(quest.target, 5)

    def test_complete_and_claim_reward(self) -> None:
        self.db.create_quest(
            user_id=self.user_id,
            title="Test Quest",
            description="Do something",
            difficulty="easy",
            quest_type="messages",
            target=3,
            reward_points=120,
        )
        updated = self.db.complete_active_quest(self.user_id, progress=3)
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated.status, "completed")
        reward = self.db.claim_reward(self.user_id)
        self.assertEqual(reward, 120)
        second_reward = self.db.claim_reward(self.user_id)
        self.assertEqual(second_reward, 0)

    def test_leaderboard_cache(self) -> None:
        for i in range(1, 4):
            user = self.user_id + i
            self.db.create_quest(
                user_id=user,
                title="Quest",
                description="Do work",
                difficulty="easy",
                quest_type="messages",
                target=1,
                reward_points=i * 10,
            )
            self.db.complete_active_quest(user, progress=1)
            self.db.claim_reward(user)
        self.db.update_leaderboard_cache()
        leaderboard = self.db.get_leaderboard(limit=3)
        self.assertEqual(len(leaderboard), 3)
        self.assertGreaterEqual(leaderboard[0]["points"], leaderboard[1]["points"])


if __name__ == "__main__":
    unittest.main()
