import discord
from discord.ext import commands, tasks
from datetime import datetime, time, timedelta
from discord.ext.commands import Context
from dotenv import load_dotenv
import sqlite3
import os
import pytz

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
paris_tz = pytz.timezone("Europe/Paris")
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


# Create table if not exists
with get_db() as conn:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS interviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER, 
                  user_name TEXT, 
                  interview_date DATE, 
                  interview_type TEXT, 
                  description TEXT, 
                  created_at TIMESTAMP)"""
    )


class InterviewManager:
    @staticmethod
    def add_interview(user_id, user_name, interview_date, interview_type, description):
        with get_db() as conn:
            conn.execute(
                """INSERT INTO interviews 
            (user_id, user_name, interview_date, interview_type, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    user_name,
                    interview_date,
                    interview_type,
                    description,
                    datetime.now(),
                ),
            )

    @staticmethod
    def get_today_interviews():
        today = datetime.now(paris_tz).date()
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
                "DELETE FROM interviews WHERE interview_date < ?", (yesterday,)
            )


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_interviews.start()
    weekly_ranking.start()


@tasks.loop(time=time(hour=8, tzinfo=paris_tz))
async def check_interviews():
    InterviewManager.delete_old_interviews()
    channel = bot.get_channel(CHANNEL_ID)  # Replace with your channel ID
    today_interviews = InterviewManager.get_today_interviews()

    if not today_interviews:
        await channel.send("No interviews scheduled for today! 🎉")
        return

    message = ["**Today's Interviews 🚨**"]
    for interview in today_interviews:
        user_name = interview[1]
        int_type = interview[3]
        desc = interview[4]
        message.append(f"• {user_name}: {int_type} - {desc}")

    await channel.send("\n".join(message))


@tasks.loop(time=time(hour=20, tzinfo=paris_tz))
async def weekly_ranking():
    if datetime.now(paris_tz).weekday() != 6:  # Only run on Sunday
        return

    channel = bot.get_channel(CHANNEL_ID)  # Replace with your channel ID
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
    date: str,
    interview_type: str,
    *,  # Force description to be keyword-only
    description: str = commands.parameter(description="Interview details"),
):
    try:
        interview_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        await ctx.send("Invalid date format! Please use YYYY-MM-DD")
        return

    InterviewManager.add_interview(
        ctx.author.id, ctx.author.name, interview_date, interview_type, description
    )

    await ctx.send(f"✅ Interview scheduled for {interview_date}!")


@bot.command()
@commands.has_permissions(administrator=True)
async def all_interviews(ctx):
    """Show all scheduled interviews (Admin only)"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM interviews ORDER BY interview_date")
        interviews = cursor.fetchall()

    if not interviews:
        await ctx.send("No interviews scheduled yet! 📭")
        return

    message = ["**All Scheduled Interviews** 📋"]
    for interview in interviews:
        message.append(
            f"`ID {interview['id']}` {interview['user_name']}: "
            f"{interview['interview_date']} - {interview['interview_type']}\n"
            f"*{interview['description']}*"
        )

    await ctx.send("\n".join(message))


@bot.command()
async def update_interview(ctx: commands.Context, interview_id: int, *, updates: str):
    """Update your interview details using key=value pairs"""
    valid_keys = ["date", "type", "desc"]
    update_dict = {}

    # Parse key=value pairs
    for part in updates.split():
        if "=" in part:
            key, value = part.split("=", 1)
            key = key.lower()
            if key in valid_keys:
                update_dict[key] = value

    if not update_dict:
        await ctx.send("❌ Valid keys: date=, type=, desc=")
        return

    # Build updates
    sql_updates = []
    params = []

    if "date" in update_dict:
        try:
            new_date = datetime.strptime(update_dict["date"], "%Y-%m-%d").date()
            sql_updates.append("interview_date = ?")
            params.append(new_date)
        except ValueError:
            await ctx.send("❌ Invalid date format! Use YYYY-MM-DD")
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
        await ctx.send("❌ Interview not found or no changes made!")


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
async def my_interviews(ctx):
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM interviews WHERE user_id = ?", (ctx.author.id,)
        )
        interviews = cursor.fetchall()

    if not interviews:
        await ctx.send("You have no scheduled interviews! 🎉")
        return

    message = ["**Your Scheduled Interviews 📅**"]
    for interview in interviews:
        message.append(
            f"`ID {interview['id']}` {interview['interview_date']}: "
            f"{interview['interview_type']} - {interview['description']}"
        )

    await ctx.send("\n".join(message))


# Replace with your bot token
bot.run(BOT_TOKEN)
