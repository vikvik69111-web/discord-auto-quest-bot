from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import Settings
from database import QuestDatabase
from utils import generate_quest


class QuestCog(commands.Cog):
    def __init__(self, bot: commands.Bot, settings: Settings, db: QuestDatabase) -> None:
        self.bot = bot
        self.settings = settings
        self.db = db
        self.quest_group = app_commands.Group(name="quest", description="Quest commands")
        self._register_commands()
        self.daily_automation_loop.start()

    def cog_unload(self) -> None:
        self.daily_automation_loop.cancel()

    def _register_commands(self) -> None:
        self.quest_group.command(name="start", description="Start a new quest")(
            self.quest_start
        )
        self.quest_group.command(name="view", description="View active quest")(
            self.quest_view
        )
        self.quest_group.command(
            name="complete", description="Submit progress and complete quest"
        )(self.quest_complete)
        self.quest_group.command(name="reward", description="Claim quest reward")(
            self.quest_reward
        )
        self.quest_group.command(name="leaderboard", description="View leaderboard")(
            self.quest_leaderboard
        )
        self.bot.tree.add_command(self.quest_group)

    async def quest_start(self, interaction: discord.Interaction) -> None:
        user_id = interaction.user.id
        if self.db.has_active_quest(user_id):
            await interaction.response.send_message(
                "You already have an active quest. Use `/quest view` first.",
                ephemeral=True,
            )
            return
        quest = generate_quest(
            self.settings.quest_difficulty_levels,
            self.settings.quest_types,
            self.settings.default_reward_points,
        )
        self.db.create_quest(
            user_id=user_id,
            title=quest.title,
            description=quest.description,
            difficulty=quest.difficulty,
            quest_type=quest.quest_type,
            target=quest.target,
            reward_points=quest.reward_points,
        )
        await interaction.response.send_message(
            f"Quest started: **{quest.title}**\n{quest.description}\n"
            f"Reward: {quest.reward_points} points",
            ephemeral=True,
        )

    async def quest_view(self, interaction: discord.Interaction) -> None:
        quest = self.db.get_active_quest(interaction.user.id)
        if quest is None:
            await interaction.response.send_message(
                "No active quest found. Use `/quest start`.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"**{quest.title}**\n{quest.description}\n"
            f"Progress: {quest.progress}/{quest.target}\n"
            f"Reward: {quest.reward_points} points",
            ephemeral=True,
        )

    @app_commands.describe(progress="Your completed progress number")
    async def quest_complete(
        self, interaction: discord.Interaction, progress: app_commands.Range[int, 0, 10000]
    ) -> None:
        quest = self.db.complete_active_quest(interaction.user.id, int(progress))
        if quest is None:
            await interaction.response.send_message(
                "No active quest to complete. Start one with `/quest start`.",
                ephemeral=True,
            )
            return
        if quest.status != "completed":
            await interaction.response.send_message(
                f"Quest progress updated: {quest.progress}/{quest.target}. "
                "Complete target to finish the quest.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Quest marked as completed. Use `/quest reward` to claim reward.",
            ephemeral=True,
        )

    async def quest_reward(self, interaction: discord.Interaction) -> None:
        reward = self.db.claim_reward(interaction.user.id)
        if reward <= 0:
            await interaction.response.send_message(
                "No completed quest reward available to claim.", ephemeral=True
            )
            return
        self.db.update_leaderboard_cache()
        await interaction.response.send_message(
            f"Reward claimed: {reward} points added.", ephemeral=True
        )

    async def quest_leaderboard(self, interaction: discord.Interaction) -> None:
        leaderboard = self.db.get_leaderboard(limit=10)
        if not leaderboard:
            await interaction.response.send_message(
                "Leaderboard is empty. Complete quests to rank up.", ephemeral=True
            )
            return
        lines = ["🏆 **Quest Leaderboard**"]
        for row in leaderboard:
            lines.append(
                f"{row['rank']}. <@{row['user_id']}> - {row['points']} points"
            )
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @tasks.loop(minutes=60)
    async def daily_automation_loop(self) -> None:
        today = datetime.now(timezone.utc).date().isoformat()
        last_run = self.db.get_daily_marker("daily_quest_generation_date")
        if last_run != today:
            for user_id in self.db.get_known_users():
                if not self.db.has_active_quest(user_id):
                    quest = generate_quest(
                        self.settings.quest_difficulty_levels,
                        self.settings.quest_types,
                        self.settings.default_reward_points,
                    )
                    self.db.create_quest(
                        user_id=user_id,
                        title=quest.title,
                        description=quest.description,
                        difficulty=quest.difficulty,
                        quest_type=quest.quest_type,
                        target=quest.target,
                        reward_points=quest.reward_points,
                    )
            self.db.set_daily_marker("daily_quest_generation_date", today)

        if self.settings.auto_reward_distribution:
            self.db.auto_claim_all_rewards()
        self.db.update_leaderboard_cache()

    @daily_automation_loop.before_loop
    async def before_daily_loop(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot, settings: Settings, db: QuestDatabase) -> None:
    await bot.add_cog(QuestCog(bot=bot, settings=settings, db=db))
