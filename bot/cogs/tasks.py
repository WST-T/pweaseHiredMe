"""
Tasks cog.
Handles scheduled tasks like daily reminders and weekly rankings.
"""

from discord.ext import commands, tasks
from datetime import time, datetime
from bot.db.models import InterviewManager
from bot.core import CHANNEL_ID, paris_tz


class TasksCog(commands.Cog):
    """Scheduled tasks and reminders"""

    def __init__(self, bot):
        self.bot = bot

        # We'll start the tasks in cog_load instead
        self.tasks_started = False

    async def cog_load(self):
        """Set up the tasks when the cog is loaded"""
        # Start the scheduled tasks after the bot is ready
        # This avoids the "no running event loop" error
        self.check_interviews.start()
        self.weekly_ranking.start()
        self.tasks_started = True
        print("✅ Scheduled tasks started")

    def cog_unload(self):
        """Clean up when the cog is unloaded"""
        if self.tasks_started:
            self.check_interviews.cancel()
            self.weekly_ranking.cancel()
            print("❌ Scheduled tasks stopped")

    @tasks.loop(time=time(hour=8, tzinfo=paris_tz))
    async def check_interviews(self):
        """Daily task to remind about today's interviews"""
        print(
            f"📅 Running daily interview check at {datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S')}"
        )

        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            print(f"⚠️ Could not find channel with ID {CHANNEL_ID}")
            return

        # Clean up old interviews first
        deleted = InterviewManager.delete_old_interviews()
        if deleted > 0:
            print(f"🧹 Cleaned up {deleted} old interviews")

        # Get today's interviews
        today_interviews = InterviewManager.get_today_interviews()

        if not today_interviews:
            await channel.send("No interviews scheduled for today! 🎉")
            return

        # Format the message
        message = ["**Today's Interviews 🚨**"]
        for interview in today_interviews:
            user_name = interview["user_name"]
            int_type = interview["interview_type"]
            int_time = (
                interview["interview_time"]
                if interview["interview_time"]
                else "No time specified"
            )
            desc = interview["description"]
            message.append(f"• **{user_name}** at **{int_time}**: {int_type} - {desc}")

        await channel.send("\n".join(message))

    @tasks.loop(time=time(hour=20, tzinfo=paris_tz))
    async def weekly_ranking(self):
        """Weekly task to show interview rankings (runs on Sunday)"""
        print(
            f"📊 Weekly ranking check triggered at {datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Get current day of week (0 = Monday, 6 = Sunday)
        current_day = datetime.now(paris_tz).weekday()

        # Only run on Sunday (day 6)
        if current_day != 6:
            print(f"📊 Not Sunday (day: {current_day}), skipping weekly ranking")
            return

        print("📊 It's Sunday! Running weekly ranking...")
        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            print(f"⚠️ Could not find channel with ID {CHANNEL_ID}")
            return

        # Get interview counts for all users
        counts = InterviewManager.get_all_interviews_count()

        if not counts:
            await channel.send("No interviews tracked yet! 📭")
            return

        # Format the message
        message = ["**Weekly Interview Ranking 🏆**"]
        for idx, row in enumerate(counts, 1):
            message.append(f"{idx}. {row['user_name']}: {row['count']} interviews")

        await channel.send("\n".join(message))

    # Wait until the bot is ready before starting tasks
    @check_interviews.before_loop
    @weekly_ranking.before_loop
    async def before_tasks(self):
        """Wait until the bot is ready before starting tasks"""
        await self.bot.wait_until_ready()
