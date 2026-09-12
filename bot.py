from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

from cogs.quest import setup as setup_quest_cog
from config import get_settings
from database import QuestDatabase


class QuestBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.settings = get_settings()
        self.db = QuestDatabase(self.settings.database_path)

    async def setup_hook(self) -> None:
        await setup_quest_cog(self, self.settings, self.db)
        await self.tree.sync()


async def main() -> None:
    bot = QuestBot()
    if not bot.settings.discord_bot_token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set in environment.")
    async with bot:
        await bot.start(bot.settings.discord_bot_token)


if __name__ == "__main__":
    asyncio.run(main())
