"""
Entry point for pweaseHiredMe Discord bot.
Just import and run the bot - super simple! ^_^
"""

import asyncio
from bot.db import init_db
from bot.core import run

# Initialize the database
init_db()

if __name__ == "__main__":
    # Run the bot using asyncio
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Bot was stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"Error: {e}")
