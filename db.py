"""
Database access layer for the 75-Day Vibe Habit Tracker.
Uses raw sqlite3 for zero-config persistence.
"""

import os
import sqlite3
from datetime import date, timedelta
from typing import List, Dict, Any, Set

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "habits.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initializes tables and populates default seed data if database is empty."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                emoji TEXT NOT NULL,
                frequency TEXT NOT NULL CHECK(frequency IN ('daily', 'weekdays')),
                archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0, 1)),
                created_at TEXT NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS completions (
                habit_id INTEGER NOT NULL,
                completed_date TEXT NOT NULL,
                PRIMARY KEY (habit_id, completed_date),
                FOREIGN KEY (habit_id) REFERENCES habits (id) ON DELETE CASCADE
            );
        """)

        # Check if habits table is empty to insert default seed data
        cursor.execute("SELECT COUNT(*) FROM habits;")
        count = cursor.fetchone()[0]

        if count == 0:
            today = date.today()
            # Seed initial habits
            seeds = [
                ("Drink 3L Water", "💧", "daily"),
                ("Morning Walk / Run", "🏃‍♂️", "weekdays"),
                ("Read 20 Pages", "📖", "daily"),
                ("10 Min Meditation", "🧘", "daily"),
            ]

            created_date = (today - timedelta(days=6)).isoformat()

            for name, emoji, freq in seeds:
                cursor.execute(
                    "INSERT INTO habits (name, emoji, frequency, archived, created_at) VALUES (?, ?, ?, 0, ?);",
                    (name, emoji, freq, created_date)
                )
                habit_id = cursor.lastrowid

                # Add past completion history for past 4 days
                for i in range(1, 5):
                    past_d = today - timedelta(days=i)
                    if freq == 'weekdays' and past_d.weekday() >= 5:
                        continue
                    cursor.execute(
                        "INSERT OR IGNORE INTO completions (habit_id, completed_date) VALUES (?, ?);",
                        (habit_id, past_d.isoformat())
                    )

        conn.commit()


def get_habits(include_archived: bool = False) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if include_archived:
            cursor.execute("SELECT * FROM habits ORDER BY id ASC;")
        else:
            cursor.execute("SELECT * FROM habits WHERE archived = 0 ORDER BY id ASC;")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def add_habit(name: str, emoji: str, frequency: str) -> int:
    today_str = date.today().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO habits (name, emoji, frequency, archived, created_at) VALUES (?, ?, ?, 0, ?);",
            (name.strip(), emoji.strip(), frequency, today_str)
        )
        conn.commit()
        return cursor.lastrowid


def update_habit(habit_id: int, name: str, emoji: str, frequency: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE habits SET name = ?, emoji = ?, frequency = ? WHERE id = ?;",
            (name.strip(), emoji.strip(), frequency, habit_id)
        )
        conn.commit()


def archive_habit(habit_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE habits SET archived = 1 WHERE id = ?;", (habit_id,))
        conn.commit()


def unarchive_habit(habit_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE habits SET archived = 0 WHERE id = ?;", (habit_id,))
        conn.commit()


def toggle_completion(habit_id: int, date_str: str) -> bool:
    """Toggles completion for a given habit and date. Returns True if completed, False if removed."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM completions WHERE habit_id = ? AND completed_date = ?;",
            (habit_id, date_str)
        )
        exists = cursor.fetchone()
        if exists:
            cursor.execute(
                "DELETE FROM completions WHERE habit_id = ? AND completed_date = ?;",
                (habit_id, date_str)
            )
            completed = False
        else:
            cursor.execute(
                "INSERT INTO completions (habit_id, completed_date) VALUES (?, ?);",
                (habit_id, date_str)
            )
            completed = True
        conn.commit()
        return completed


def get_all_completions_by_habit() -> Dict[int, List[str]]:
    """Returns a dict mapping habit_id to a list of completed_date strings."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT habit_id, completed_date FROM completions ORDER BY completed_date ASC;")
        rows = cursor.fetchall()
        result: Dict[int, List[str]] = {}
        for row in rows:
            h_id = row["habit_id"]
            d_str = row["completed_date"]
            if h_id not in result:
                result[h_id] = []
            result[h_id].append(d_str)
        return result


def get_completions_for_date(date_str: str) -> Set[int]:
    """Returns a set of habit_ids completed on a specific date."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT habit_id FROM completions WHERE completed_date = ?;", (date_str,))
        rows = cursor.fetchall()
        return {row["habit_id"] for row in rows}


def get_challenge_start_date() -> date:
    """Gets the earliest habit creation date or earliest completion date to compute Challenge Day count."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(created_at) FROM habits;")
        row = cursor.fetchone()
        min_created = row[0] if row and row[0] else None

        cursor.execute("SELECT MIN(completed_date) FROM completions;")
        row = cursor.fetchone()
        min_completed = row[0] if row and row[0] else None

        dates = [d for d in [min_created, min_completed] if d]
        if dates:
            return date.fromisoformat(min(dates))
        return date.today()
