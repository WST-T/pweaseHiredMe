from datetime import datetime


def validate_date(date_str):
    """Validate a date string is in YYYY-MM-DD format

    Args:
        date_str: String date to validate

    Returns:
        datetime.date object if valid, None if invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def validate_time(time_str):
    """Validate a time string is in HH:MM format

    Args:
        time_str: String time to validate

    Returns:
        True if valid, False if invalid
    """
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def is_valid_interview_id(interview_id):
    """Check if an interview ID is a valid integer

    Args:
        interview_id: ID to validate

    Returns:
        True if valid, False if invalid
    """
    try:
        int(interview_id)
        return True
    except (ValueError, TypeError):
        return False
