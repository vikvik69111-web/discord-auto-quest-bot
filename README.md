# Discord Auto Quest Bot

A production-ready Discord bot using `discord.py` with automatic quest generation, quest tracking, reward claiming, and leaderboard support backed by SQLite.

## Features

- Quest management system:
  - Automatic quest generation and assignment
  - Quest tracking and progress monitoring
  - Quest completion verification
  - Reward claiming and points tracking
- Slash commands:
  - `/quest start` - start a new quest
  - `/quest view` - view your active quest
  - `/quest complete` - submit progress and complete quest
  - `/quest reward` - claim reward for a completed quest
  - `/quest leaderboard` - view top users
- Auto features:
  - Daily quest generation for known users
  - Automatic reward distribution (configurable)
  - Automatic leaderboard cache refresh
- Configuration:
  - Environment variable driven setup
  - Configurable quest types, difficulties, and reward values

## Project Structure

- `/home/runner/work/discord-auto-quest-bot/discord-auto-quest-bot/bot.py` - Main bot entrypoint
- `/home/runner/work/discord-auto-quest-bot/discord-auto-quest-bot/config.py` - Configuration management
- `/home/runner/work/discord-auto-quest-bot/discord-auto-quest-bot/cogs/quest.py` - Quest commands and automation loop
- `/home/runner/work/discord-auto-quest-bot/discord-auto-quest-bot/database/db.py` - SQLite schema and data access
- `/home/runner/work/discord-auto-quest-bot/discord-auto-quest-bot/utils/quest_generator.py` - Quest generation helpers
- `/home/runner/work/discord-auto-quest-bot/discord-auto-quest-bot/requirements.txt` - Python dependencies
- `/home/runner/work/discord-auto-quest-bot/discord-auto-quest-bot/.env.example` - Environment template

## Setup

1. Create virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and set values:
   ```bash
   cp .env.example .env
   ```

3. Run bot:
   ```bash
   python /home/runner/work/discord-auto-quest-bot/discord-auto-quest-bot/bot.py
   ```

## Testing

Run focused tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```
