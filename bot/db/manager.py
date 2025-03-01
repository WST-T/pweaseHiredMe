import sqlite3
import os
from pathlib import Path

# Database file path - use a constant for easier configuration
DB_FILE = "interviews.db"


def get_db():
    """Create a database connection and return it with row factory enabled"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_db():
    """Initialize the database, creating tables if they don't exist"""
    # Make sure the database file exists
    if not os.path.exists(DB_FILE):
        Path(DB_FILE).touch()

    with get_db() as conn:
        # Check if the table already exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='interviews'"
        )
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            # Create interviews table
            conn.execute(
                """CREATE TABLE interviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER, 
                    user_name TEXT, 
                    interview_date DATE, 
                    interview_time TEXT,
                    interview_type TEXT, 
                    description TEXT, 
                    created_at TIMESTAMP
                )"""
            )
            print(f"✅ Created new interviews table in {DB_FILE}")
        else:
            # Check if interview_time column exists
            cursor = conn.execute("PRAGMA table_info(interviews)")
            columns = [info[1] for info in cursor.fetchall()]

            # Add interview_time column if it doesn't exist
            if "interview_time" not in columns:
                conn.execute("ALTER TABLE interviews ADD COLUMN interview_time TEXT")
                print("✅ Added interview_time column to existing table")
