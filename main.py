import discord
from discord.ext import commands, tasks
from datetime import datetime, time, timedelta
from dotenv import load_dotenv
import sqlite3
import os
import pytz
import re

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
paris_tz = pytz.timezone("Europe/Paris")
bot.help_command = None
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN not found in .env file")
channel_id_str = os.getenv("CHANNEL_ID")
if channel_id_str is None:
    raise ValueError("CHANNEL_ID not found in .env file")
CHANNEL_ID = int(channel_id_str)


def get_db():
    conn = sqlite3.connect("interviews.db")
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


# Create table if not exists - now with interview_time column
with get_db() as conn:
    # Check if interview_time column exists
    cursor = conn.execute("PRAGMA table_info(interviews)")
    columns = [info[1] for info in cursor.fetchall()]

    # Create table if it doesn't exist
    if "interviews" not in [
        table[0]
        for table in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    ]:
        conn.execute(
            """CREATE TABLE interviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER, 
                  user_name TEXT, 
                  interview_date DATE, 
                  interview_time TEXT,
                  interview_type TEXT, 
                  description TEXT, 
                  created_at TIMESTAMP)"""
        )
    # Add interview_time column if it doesn't exist
    elif "interview_time" not in columns:
        conn.execute("ALTER TABLE interviews ADD COLUMN interview_time TEXT")


class InterviewManager:
    @staticmethod
    def add_interview(
        user_id, user_name, interview_date, interview_time, interview_type, description
    ):
        with get_db() as conn:
            conn.execute(
                """INSERT INTO interviews 
                (user_id, user_name, interview_date, interview_time, interview_type, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    user_name,
                    interview_date.isoformat(),  # Store as ISO string
                    interview_time,
                    interview_type,
                    description,
                    datetime.now().isoformat(),
                ),
            )

    @staticmethod
    def get_today_interviews():
        today = datetime.now(paris_tz).date().isoformat()  # Compare as string
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM interviews WHERE interview_date = ?", (today,)
            )
            return cursor.fetchall()

    @staticmethod
    def get_all_interviews_count():
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT user_name, COUNT(*) FROM interviews GROUP BY user_id"
            )
            return cursor.fetchall()

    @staticmethod
    def delete_old_interviews():
        yesterday = datetime.now(paris_tz).date() - timedelta(days=1)
        with get_db() as conn:
            conn.execute(
                "DELETE FROM interviews WHERE interview_date < ?",
                (yesterday.isoformat(),),
            )


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_interviews.start()
    weekly_ranking.start()


@tasks.loop(time=time(hour=8, tzinfo=paris_tz))
async def check_interviews():
    InterviewManager.delete_old_interviews()
    channel = bot.get_channel(CHANNEL_ID)
    today_interviews = InterviewManager.get_today_interviews()

    if not today_interviews:
        await channel.send("No interviews scheduled for today! 🎉")
        return

    message = ["**Today's Interviews 🚨**"]
    for interview in today_interviews:
        # Using the actual user_name field instead of user_id
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
async def weekly_ranking():
    if datetime.now(paris_tz).weekday() != 6:  # Only run on Sunday
        return

    channel = bot.get_channel(CHANNEL_ID)
    counts = InterviewManager.get_all_interviews_count()

    if not counts:
        await channel.send("No interviews tracked yet! 📭")
        return

    sorted_counts = sorted(counts, key=lambda x: x[1], reverse=True)
    message = ["**Weekly Interview Ranking 🏆**"]
    for idx, (user, count) in enumerate(sorted_counts, 1):
        message.append(f"{idx}. {user}: {count} interviews")

    await channel.send("\n".join(message))


@bot.command()
async def schedule(
    ctx: commands.Context,
    date_and_time: str,
    interview_type: str,
    *,  # Force description to be keyword-only
    description: str = commands.parameter(description="Interview details"),
):
    # Match pattern for date and optional time
    # Format: YYYY-MM-DD or YYYY-MM-DD HH:MM
    date_time_pattern = r"^(\d{4}-\d{2}-\d{2})(?:\s+(\d{1,2}:\d{2}))?$"
    match = re.match(date_time_pattern, date_and_time)

    if not match:
        await ctx.send(
            "❌ Invalid format! Please use `YYYY-MM-DD` or `YYYY-MM-DD HH:MM`"
        )
        return

    date_str = match.group(1)
    time_str = match.group(2) or "No time specified"  # Default if no time

    try:
        interview_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        await ctx.send("❌ Invalid date format! Please use YYYY-MM-DD")
        return

    if time_str != "No time specified":
        try:
            # Validate time format
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            await ctx.send("❌ Invalid time format! Please use HH:MM (24-hour format)")
            return

    InterviewManager.add_interview(
        ctx.author.id,
        ctx.author.name,
        interview_date,
        time_str,
        interview_type,
        description,
    )

    time_message = f" at {time_str}" if time_str != "No time specified" else ""
    await ctx.send(f"✅ Interview scheduled for {interview_date}{time_message}!")


@bot.command()
@commands.has_permissions(administrator=True)
async def all_interviews(ctx):
    today_iso = datetime.now(paris_tz).date().isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM interviews WHERE interview_date >= ? ORDER BY interview_date",
            (today_iso,),
        )
        interviews = cursor.fetchall()

    if not interviews:
        await ctx.send("No interviews scheduled yet! 📭")
        return

    # Convert string dates to date objects and Row objects to dicts
    processed = []
    for interview_row in interviews:
        interview = dict(interview_row)
        interview["interview_date"] = datetime.strptime(
            interview["interview_date"], "%Y-%m-%d"
        ).date()
        processed.append(interview)

    # Group interviews by date
    today = datetime.now(paris_tz).date()
    date_groups = {}

    for interview in processed:
        int_date = interview["interview_date"]
        days_diff = (int_date - today).days

        if days_diff == 0:
            group = "**Today** 🚨"
        elif days_diff == 1:
            group = "**Tomorrow** ⏳"
        else:
            days_text = (
                f"in {days_diff} days" if days_diff > 0 else f"{-days_diff} days ago"
            )
            group = f"**{int_date.strftime('%A, %b %d')}** ({days_text}) 📅"

        date_groups.setdefault(group, []).append(interview)

    # Build message with proper sorting
    message = ["**All Scheduled Interviews**"]
    for group_name, group_interviews in sorted(
        date_groups.items(),
        key=lambda x: (
            today
            if "Today" in x[0]
            else (
                today + timedelta(days=1) if "Tomorrow" in x[0] else int_date
            )  # Use actual date from processed interviews
        ),
    ):
        message.append(f"\n{group_name}")
        for interview in group_interviews:
            time_info = ""
            if interview.get("interview_time"):
                time_info = f" at {interview['interview_time']}"

            message.append(
                f"`ID {interview['id']}` **{interview['user_name']}**{time_info} {interview['interview_type']}: "
                f"{interview['description']}"
            )
    await ctx.send("\n".join(message))


@bot.command()
async def update_interview(ctx: commands.Context, interview_id: int, *, updates: str):
    """Update your interview details using key=value pairs"""
    valid_keys = ["date", "time", "type", "desc"]
    update_dict = {}

    # Parse the updates from the command
    # First, try to extract quoted values like desc="My description with spaces"
    quoted_parts = re.findall(r'(\w+)=("(?:[^"\\]|\\.)*")', updates)
    for key, value in quoted_parts:
        key = key.lower()
        if key in valid_keys:
            # Remove quotes from the value
            update_dict[key] = value[1:-1]  # Strip the quotes

    # Next, handle non-quoted simple values like date=2024-03-01
    for part in updates.split():
        if "=" in part and not any(part.startswith(f"{k}=") for k, _ in quoted_parts):
            key, value = part.split("=", 1)
            key = key.lower()
            if (
                key in valid_keys and key not in update_dict
            ):  # Don't override quoted values
                update_dict[key] = value

    if not update_dict:
        await ctx.send("❌ Valid keys: date=YYYY-MM-DD, time=HH:MM, type=, desc=")
        return

    # First, fetch the current interview to check fields
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM interviews WHERE id = ? AND user_id = ?",
            (interview_id, ctx.author.id),
        )
        current_interview = cursor.fetchone()

    if not current_interview:
        await ctx.send("❌ Interview not found or you don't have permission!")
        return

    # Build updates
    sql_updates = []
    params = []

    # Check if we need to fix the interview_type if it looks like a time
    is_type_time_format = re.match(
        r"^\d{1,2}:\d{2}$", current_interview["interview_type"]
    )
    if "time" in update_dict and is_type_time_format and "type" not in update_dict:
        # If updating time and interview_type looks like a time, reset interview_type to default
        sql_updates.append("interview_type = ?")
        params.append("Interview")  # Default value

    if "date" in update_dict:
        try:
            new_date = datetime.strptime(update_dict["date"], "%Y-%m-%d").date()
            sql_updates.append("interview_date = ?")
            params.append(new_date.isoformat())
        except ValueError:
            await ctx.send("❌ Invalid date format! Use YYYY-MM-DD")
            return

    if "time" in update_dict:
        try:
            # Validate time format
            datetime.strptime(update_dict["time"], "%H:%M")
            sql_updates.append("interview_time = ?")
            params.append(update_dict["time"])
        except ValueError:
            await ctx.send("❌ Invalid time format! Use HH:MM (24-hour format)")
            return

    if "type" in update_dict:
        sql_updates.append("interview_type = ?")
        params.append(update_dict["type"])

    if "desc" in update_dict:
        sql_updates.append("description = ?")
        params.append(update_dict["desc"])

    # Add ID and user_id to params
    params.extend([interview_id, ctx.author.id])

    with get_db() as conn:
        cursor = conn.execute(
            f"UPDATE interviews SET {', '.join(sql_updates)} WHERE id = ? AND user_id = ?",
            params,
        )

    if cursor.rowcount > 0:
        await ctx.send("✅ Interview updated successfully!")
    else:
        await ctx.send("❌ No changes made!")


@bot.command()
async def delete_interview(ctx: commands.Context, interview_id: int):
    """Delete one of your interviews"""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM interviews WHERE id = ? AND user_id = ?",
            (interview_id, ctx.author.id),
        )

    if cursor.rowcount == 0:
        await ctx.send("❌ Interview not found or you don't have permission!")
    else:
        await ctx.send("✅ Interview deleted successfully!")


@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="pweaseHiredMe 🍩",
        description="Here's everything I can do!",
        color=0xFFB6C1,
    )

    # Updated User Commands section with new time format
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


@bot.command()
async def my_interviews(ctx):
    today_iso = datetime.now(paris_tz).date().isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM interviews WHERE user_id = ? AND interview_date >= ? ORDER BY interview_date",
            (ctx.author.id, today_iso),
        )
        interviews = cursor.fetchall()

    if not interviews:
        await ctx.send("You have no scheduled interviews! 🎉")
        return

    today = datetime.now(paris_tz).date()
    date_groups = {}

    for interview_row in interviews:
        # Convert sqlite3.Row to dictionary
        interview = dict(interview_row)

        # Convert string to date object
        int_date = datetime.strptime(interview["interview_date"], "%Y-%m-%d").date()
        days_diff = (int_date - today).days

        if days_diff == 0:
            group = "**Today** 🚨"
        elif days_diff == 1:
            group = "**Tomorrow** ⏳"
        else:
            days_text = (
                f"in {days_diff} days" if days_diff > 0 else f"{-days_diff} days ago"
            )
            group = f"**{int_date.strftime('%A, %b %d')}** ({days_text}) 📅"

        date_groups.setdefault(group, []).append(interview)

    # Build message
    message = ["**Your Scheduled Interviews**"]
    for group_name, group_interviews in date_groups.items():
        message.append(f"\n{group_name}")
        for interview in group_interviews:
            time_info = ""
            interview_type = interview["interview_type"]

            # Check if interview_type looks like a time (HH:MM)
            is_type_time_format = re.match(r"^\d{1,2}:\d{2}$", interview_type)

            # Case 1: We have a proper interview_time
            if (
                interview.get("interview_time")
                and interview["interview_time"] != "No time specified"
            ):
                time_info = f" at {interview['interview_time']}"

                # If interview_type also looks like a time, it's probably incorrect data
                if is_type_time_format:
                    interview_type = "Interview"  # Default type

            # Case 2: No proper interview_time but interview_type looks like a time
            elif is_type_time_format:
                time_info = f" at {interview_type}"
                interview_type = "Interview"  # Default type

            message.append(
                f"`ID {interview['id']}`{time_info} {interview_type}: "
                f"{interview['description']}"
            )

    await ctx.send("\n".join(message))


@bot.command()
async def total(ctx):
    """Show your all-time interview count"""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM interviews WHERE user_id = ?", (ctx.author.id,)
        )
        count = cursor.fetchone()[0]

    await ctx.send(f"🎉 You've scheduled {count} interviews in total!")


# Replace with your bot token
bot.run(BOT_TOKEN)
