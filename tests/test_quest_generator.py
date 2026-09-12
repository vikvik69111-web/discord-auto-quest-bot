import unittest

from utils.quest_generator import generate_quest


class QuestGeneratorTests(unittest.TestCase):
    def test_generate_quest_returns_valid_fields(self) -> None:
        quest = generate_quest(
            difficulty_levels=("easy", "medium", "hard"),
            quest_types=("messages", "reactions"),
            base_reward=100,
        )
        self.assertIn(quest.difficulty, {"easy", "medium", "hard"})
        self.assertIn(quest.quest_type, {"messages", "reactions"})
        self.assertGreaterEqual(quest.target, 1)
        self.assertGreaterEqual(quest.reward_points, 1)
        self.assertTrue(quest.title)
        self.assertTrue(quest.description)


if __name__ == "__main__":
    unittest.main()
