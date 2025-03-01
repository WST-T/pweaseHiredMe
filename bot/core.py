"""
Core bot setup and configuration.
This is where all the important bot initialization happens!
"""

import os
import discord
from discord.ext import commands
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN not found in .env file")

channel_id_str = os.getenv("CHANNEL_ID")
if channel_id_str is None:
    raise ValueError("CHANNEL_ID not found in .env file")
CHANNEL_ID = int(channel_id_str)

# Set up timezone
paris_tz = pytz.timezone("Europe/Paris")

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.help_command = None  # We'll use our custom help command

# Export important variables for use in other modules
__all__ = ["bot", "paris_tz", "CHANNEL_ID", "BOT_TOKEN"]


async def setup_bot():
    """Load all cogs and perform any other setup needed"""
    # Import here to avoid circular imports
    from bot.cogs import interviews, admin, tasks

    # Register all cogs (need to await these since they're coroutines)
    await bot.add_cog(interviews.InterviewCog(bot))
    await bot.add_cog(admin.AdminCog(bot))
    await bot.add_cog(tasks.TasksCog(bot))

    @bot.event
    async def on_ready():
        """Called when the bot is ready to start receiving events"""
        print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
        print(f"🌍 Using CHANNEL_ID: {CHANNEL_ID}")
        print("✨ Bot is ready to receive commands!")


async def run():
    """Start the bot with the token from environment"""
    await setup_bot()
    await bot.start(BOT_TOKEN)  # Using bot.start instead of bot.run
