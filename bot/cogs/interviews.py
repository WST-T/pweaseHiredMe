"""
Interview commands cog.
Handles all user-facing commands for managing interviews.
"""

import re
import discord
from discord.ext import commands
from bot.db.models import InterviewManager
from bot.utils.formatters import format_interview_list
from bot.utils.validators import validate_date, validate_time


class InterviewCog(commands.Cog):
    """Commands for managing interviews"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def schedule(
        self,
        ctx: commands.Context,
        date_and_time: str,
        interview_type: str,
        *,
        description: str = commands.parameter(description="Interview details"),
    ):
        """Schedule a new interview

        Usage: !schedule 2024-03-01 14:30 Technical "System Design"
        """
        # Match pattern for date and optional time
        date_time_pattern = r"^(\d{4}-\d{2}-\d{2})(?:\s+(\d{1,2}:\d{2}))?$"
        match = re.match(date_time_pattern, date_and_time)

        if not match:
            await ctx.send(
                "❌ Invalid format! Please use `YYYY-MM-DD` or `YYYY-MM-DD HH:MM`"
            )
            return

        date_str = match.group(1)
        time_str = match.group(2) or "No time specified"  # Default if no time

        # Validate date
        interview_date = validate_date(date_str)
        if not interview_date:
            await ctx.send("❌ Invalid date format! Please use YYYY-MM-DD")
            return

        # Validate time if specified
        if time_str != "No time specified":
            if not validate_time(time_str):
                await ctx.send(
                    "❌ Invalid time format! Please use HH:MM (24-hour format)"
                )
                return

        # Add the interview to the database
        InterviewManager.add_interview(
            ctx.author.id,
            ctx.author.name,
            interview_date,
            time_str,
            interview_type,
            description,
        )

        # Confirm with user
        time_message = f" at {time_str}" if time_str != "No time specified" else ""
        await ctx.send(f"✅ Interview scheduled for {interview_date}{time_message}!")

    @commands.command()
    async def my_interviews(self, ctx):
        """List all your upcoming interviews"""
        interviews = InterviewManager.get_user_interviews(ctx.author.id)

        if not interviews:
            await ctx.send("You have no scheduled interviews! 🎉")
            return

        # Format the interviews into a nice message
        message = format_interview_list(
            interviews, "Your Scheduled Interviews", include_username=False
        )
        await ctx.send(message)

    @commands.command()
    async def update_interview(
        self, ctx: commands.Context, interview_id: int, *, updates: str
    ):
        """Update an interview's details

        Usage: !update_interview 3 date=2024-03-01 time=15:30 type=Technical desc="System Design"
        """
        valid_keys = {
            "date": "interview_date",
            "time": "interview_time",
            "type": "interview_type",
            "desc": "description",
        }

        update_dict = {}

        # Parse the updates from the command
        # First, try to extract quoted values like desc="My description with spaces"
        quoted_parts = re.findall(r'(\w+)=("(?:[^"\\]|\\.)*")', updates)
        for key, value in quoted_parts:
            key = key.lower()
            if key in valid_keys:
                # Remove quotes from the value
                update_dict[valid_keys[key]] = value[1:-1]  # Strip the quotes

        # Next, handle non-quoted simple values like date=2024-03-01
        for part in updates.split():
            if "=" in part and not any(
                part.startswith(f"{k}=") for k, _ in quoted_parts
            ):
                key, value = part.split("=", 1)
                key = key.lower()
                if key in valid_keys and valid_keys[key] not in update_dict:
                    update_dict[valid_keys[key]] = value

        if not update_dict:
            await ctx.send("❌ Valid keys: date=YYYY-MM-DD, time=HH:MM, type=, desc=")
            return

        # Validate date and time if provided
        if "interview_date" in update_dict:
            new_date = validate_date(update_dict["interview_date"])
            if not new_date:
                await ctx.send("❌ Invalid date format! Use YYYY-MM-DD")
                return
            update_dict["interview_date"] = new_date.isoformat()

        if "interview_time" in update_dict:
            if not validate_time(update_dict["interview_time"]):
                await ctx.send("❌ Invalid time format! Use HH:MM (24-hour format)")
                return

        # Get current interview to check additional validation rules
        current = InterviewManager.get_interview(interview_id)
        if not current or current["user_id"] != ctx.author.id:
            await ctx.send("❌ Interview not found or you don't have permission!")
            return

        # Check if we need to fix the interview_type if it looks like a time
        is_type_time_format = re.match(r"^\d{1,2}:\d{2}$", current["interview_type"])
        if (
            "interview_time" in update_dict
            and is_type_time_format
            and "interview_type" not in update_dict
        ):
            # If updating time and interview_type looks like a time, reset interview_type to default
            update_dict["interview_type"] = "Interview"  # Default value

        # Update the interview in the database
        if InterviewManager.update_interview(interview_id, ctx.author.id, update_dict):
            await ctx.send("✅ Interview updated successfully!")
        else:
            await ctx.send("❌ No changes made!")

    @commands.command()
    async def delete_interview(self, ctx: commands.Context, interview_id: int):
        """Delete one of your interviews

        Usage: !delete_interview 5
        """
        if InterviewManager.delete_interview(interview_id, ctx.author.id):
            await ctx.send("✅ Interview deleted successfully!")
        else:
            await ctx.send("❌ Interview not found or you don't have permission!")

    @commands.command()
    async def total(self, ctx):
        """Show your all-time interview count"""
        count = InterviewManager.get_user_total_count(ctx.author.id)
        await ctx.send(f"🎉 You've scheduled {count} interviews in total!")

    @commands.command()
    async def help(self, ctx):
        """Show help about available commands"""
        embed = discord.Embed(
            title="pweaseHiredMe 🍩",
            description="Here's everything I can do!",
            color=0xFFB6C1,
        )

        # User Commands section
        embed.add_field(
            name="📝 User Commands",
            value=(
                "`!schedule <date> [time] <type> <description>` - Schedule interview\n"
                '  Example: `!schedule 2024-03-01 14:30 Technical "System Design"`\n'
                "`!my_interviews` - List your upcoming interviews\n"
                "`!total` - Show your all-time interview count\n"
                "`!update_interview <ID> <key=value>` - Modify interview\n"
                "  Valid keys: date=, time=, type=, desc=\n"
                "`!delete_interview <ID>` - Remove interview"
            ),
            inline=False,
        )

        # Admin Commands
        if ctx.author.guild_permissions.administrator:
            embed.add_field(
                name="👑 Admin Commands",
                value="`!all_interviews` - View all scheduled interviews",
                inline=False,
            )

        # Automatic Features
        embed.add_field(
            name="⏰ Automatic Features",
            value=(
                "• Daily reminders at 8AM Paris time\n"
                "• Weekly rankings every Sunday\n"
                "• Auto-cleanup of old interviews"
            ),
            inline=False,
        )

        # Tips
        embed.add_field(
            name="💡 Pro Tips",
            value=(
                "• Date format: `YYYY-MM-DD`\n"
                "• Time format: `HH:MM` (24-hour)\n"
                "• Use quotes for multi-word descriptions\n"
                "• Find IDs with `!my_interviews`\n"
                "• Times are in Paris/CET timezone"
            ),
            inline=False,
        )

        embed.set_footer(text="Made with 💖 by WST-T '文森特'")

        await ctx.send(embed=embed)
