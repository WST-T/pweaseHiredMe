from datetime import datetime, timedelta
import pytz
from .manager import get_db


class InterviewManager:
    """Handles all operations related to interview data"""

    @staticmethod
    def add_interview(
        user_id, user_name, interview_date, interview_time, interview_type, description
    ):
        """Add a new interview to the database"""
        with get_db() as conn:
            conn.execute(
                """INSERT INTO interviews 
                (user_id, user_name, interview_date, interview_time, interview_type, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    user_name,
                    interview_date.isoformat(),  # Store dates as ISO strings
                    interview_time,
                    interview_type,
                    description,
                    datetime.now().isoformat(),
                ),
            )
            return True

    @staticmethod
    def get_user_interviews(user_id, include_past=False):
        """Get all interviews for a specific user"""
        today = datetime.now(pytz.timezone("Europe/Paris")).date().isoformat()

        query = "SELECT * FROM interviews WHERE user_id = ?"
        params = [user_id]

        if not include_past:
            query += " AND interview_date >= ?"
            params.append(today)

        query += " ORDER BY interview_date, interview_time"

        with get_db() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    @staticmethod
    def get_today_interviews():
        """Get all interviews scheduled for today"""
        today = datetime.now(pytz.timezone("Europe/Paris")).date().isoformat()

        with get_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM interviews WHERE interview_date = ? ORDER BY interview_time",
                (today,),
            )
            return cursor.fetchall()

    @staticmethod
    def get_all_future_interviews():
        """Get all future interviews for all users"""
        today = datetime.now(pytz.timezone("Europe/Paris")).date().isoformat()

        with get_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM interviews WHERE interview_date >= ? ORDER BY interview_date, interview_time",
                (today,),
            )
            return cursor.fetchall()

    @staticmethod
    def get_all_interviews_count():
        """Get count of interviews by user"""
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT user_name, COUNT(*) as count FROM interviews GROUP BY user_id ORDER BY count DESC"
            )
            return cursor.fetchall()

    @staticmethod
    def get_user_total_count(user_id):
        """Get total count of interviews for a specific user"""
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM interviews WHERE user_id = ?", (user_id,)
            )
            return cursor.fetchone()[0]

    @staticmethod
    def update_interview(interview_id, user_id, updates):
        """Update an existing interview"""
        # Build SQL for updates
        sql_updates = []
        params = []

        for key, value in updates.items():
            sql_updates.append(f"{key} = ?")
            params.append(value)

        # Add WHERE clause parameters
        params.extend([interview_id, user_id])

        with get_db() as conn:
            cursor = conn.execute(
                f"UPDATE interviews SET {', '.join(sql_updates)} WHERE id = ? AND user_id = ?",
                params,
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete_interview(interview_id, user_id):
        """Delete an interview by ID (only if it belongs to the user)"""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM interviews WHERE id = ? AND user_id = ?",
                (interview_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete_old_interviews():
        """Delete interviews from before today"""
        yesterday = datetime.now(pytz.timezone("Europe/Paris")).date() - timedelta(
            days=1
        )

        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM interviews WHERE interview_date < ?",
                (yesterday.isoformat(),),
            )
            return cursor.rowcount  # Number of deleted interviews

    @staticmethod
    def get_interview(interview_id):
        """Get a single interview by ID"""
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM interviews WHERE id = ?", (interview_id,)
            )
            return cursor.fetchone()
