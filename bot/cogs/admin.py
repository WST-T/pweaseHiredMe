"""
Admin commands cog.
Handles administrative commands that require special permissions.
"""

import discord
from discord.ext import commands
from bot.db.models import InterviewManager
from bot.utils.formatters import format_interview_list


class AdminCog(commands.Cog):
    """Administrative commands requiring special permissions"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def all_interviews(self, ctx):
        """List all scheduled interviews (Admin only)

        This command requires administrator permissions.
        """
        interviews = InterviewManager.get_all_future_interviews()

        if not interviews:
            await ctx.send("No interviews scheduled yet! 📭")
            return

        # Format the interviews into a nice message
        message = format_interview_list(
            interviews, "All Scheduled Interviews", include_username=True
        )
        await ctx.send(message)

    # You could add more admin commands here
    # For example, manual task triggering or configuration commands

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, *, message: str):
        """Send an announcement to the bot's configured channel

        Usage: !announce Hello everyone! This is an important message.
        """
        channel = self.bot.get_channel(int(self.bot.CHANNEL_ID))
        if not channel:
            await ctx.send("⚠️ Could not find the configured announcement channel!")
            return

        # Create a nice embed for the announcement
        embed = discord.Embed(
            title="📢 Announcement", description=message, color=0x7289DA
        )
        embed.set_footer(text=f"From: {ctx.author.name}")

        await channel.send(embed=embed)
        await ctx.send("✅ Announcement sent!")

    # Error handler for admin commands
    @all_interviews.error
    @announce.error
    async def admin_error(self, ctx, error):
        """Handle errors in admin commands"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "❌ Sorry, you need administrator permissions to use this command!"
            )
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")
