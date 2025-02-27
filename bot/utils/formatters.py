"""
Message formatting utilities.
Functions to format messages in a consistent way.
"""

import re
from datetime import datetime
import pytz


def format_interview_list(interviews, title, include_username=True):
    """Format a list of interviews into a nicely structured message

    Args:
        interviews: List of interview objects (from database)
        title: Title for the message
        include_username: Whether to include the username in the output

    Returns:
        Formatted string with all interviews grouped by date
    """
    today = datetime.now(pytz.timezone("Europe/Paris")).date()
    date_groups = {}

    for interview_row in interviews:
        # Convert sqlite3.Row to dictionary if needed
        interview = (
            dict(interview_row) if hasattr(interview_row, "keys") else interview_row
        )

        # Convert string to date object if needed
        if isinstance(interview["interview_date"], str):
            int_date = datetime.strptime(interview["interview_date"], "%Y-%m-%d").date()
        else:
            int_date = interview["interview_date"]

        # Calculate days difference for grouping
        days_diff = (int_date - today).days

        # Create a group based on the date
        if days_diff == 0:
            group = "**Today** 🚨"
        elif days_diff == 1:
            group = "**Tomorrow** ⏳"
        else:
            days_text = (
                f"in {days_diff} days" if days_diff > 0 else f"{-days_diff} days ago"
            )
            group = f"**{int_date.strftime('%A, %b %d')}** ({days_text}) 📅"

        # Add the interview to the appropriate group
        if group not in date_groups:
            date_groups[group] = []
        date_groups[group].append(interview)

    # Build the message
    message = [f"**{title}**"]

    # Sort groups by date (Today first, then Tomorrow, then future dates)
    sorted_groups = sorted(
        date_groups.items(),
        key=lambda x: (
            -100 if "Today" in x[0] else (-50 if "Tomorrow" in x[0] else days_diff)
        ),
    )

    # Add each group to the message
    for group_name, group_interviews in sorted_groups:
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

            # Build the interview description line
            interview_desc = f"`ID {interview['id']}`"

            # Add username if requested (for admin commands)
            if include_username:
                interview_desc += f" **{interview['user_name']}**"

            # Add time and type information
            interview_desc += (
                f"{time_info} {interview_type}: {interview['description']}"
            )

            message.append(interview_desc)

    return "\n".join(message)
