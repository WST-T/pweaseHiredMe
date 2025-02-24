import discord
from discord.ext import commands, tasks
from datetime import datetime, time
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
                 (user_id INTEGER, 
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
                "INSERT INTO interviews VALUES (?, ?, ?, ?, ?, ?)",
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


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_interviews.start()
    weekly_ranking.start()


@tasks.loop(time=time(hour=8))
async def check_interviews():
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


@tasks.loop(time=time(hour=20))
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
async def my_interviews(ctx):
    with get_db() as conn:  # Use context manager
        cursor = conn.execute(
            "SELECT * FROM interviews WHERE user_id = ?", (ctx.author.id,)
        )
        interviews = cursor.fetchall()

    if not interviews:
        await ctx.send("You have no scheduled interviews! 🎉")
        return

    message = ["**Your Scheduled Interviews 📅**"]
    for interview in interviews:
        # Access columns by name instead of index (safer)
        date = interview["interview_date"]
        int_type = interview["interview_type"]
        desc = interview["description"]
        message.append(f"• {date}: {int_type} - {desc}")

    await ctx.send("\n".join(message))


# Replace with your bot token
bot.run(BOT_TOKEN)
