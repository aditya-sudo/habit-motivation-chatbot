"""
Database layer for the habit‑motivation chatbot.

This module wraps a tiny SQLite database so that other parts of the
application don't need to deal with SQL directly. It manages users,
their habits and daily check‑ins. All timestamps are stored in ISO
format (YYYY‑MM‑DD) to make string comparison and date parsing
straightforward.

Functions in this module raise exceptions on failure rather than
printing errors to stdout – callers should handle errors as
appropriate. The module is deliberately thin to make the underlying
storage technology easy to replace later (e.g. TinyDB or a remote DB).
"""

import logging
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

# When the application runs from the project root the database file
# lives alongside the Python modules. Using Path ensures the code
# behaves correctly regardless of the working directory.
DB_PATH = Path(__file__).resolve().parent / "habits.db"


def _get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database.

    The connection uses row factory to return dict‑like objects for ease
    of access. Callers must close the connection when finished or use
    it as a context manager.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db() -> None:
    """Create database tables if they don't already exist.

    This function is idempotent: it can be called multiple times
    without destroying existing data. Tables are created for users,
    habits and progress. Foreign keys enforce referential integrity.
    """
    with _get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()
        # Create users table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            """
        )
        # Create habits table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        # Create progress table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                checkin_date TEXT NOT NULL,
                completed INTEGER NOT NULL,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()
        logging.debug("Database tables ensured.")


def add_user(name: str) -> int:
    """Insert a new user into the database.

    If the user already exists, their existing ID is returned. Names
    must be unique across all users.

    Args:
        name: The human readable name of the user.

    Returns:
        The database ID of the user.
    """
    with _get_connection() as conn:
        cur = conn.cursor()
        # Try to insert; ignore if unique constraint fails
        try:
            cur.execute("INSERT INTO users (name) VALUES (?);", (name,))
            conn.commit()
            logging.info("Created new user %s with id %s", name, cur.lastrowid)
            return cur.lastrowid
        except sqlite3.IntegrityError:
            # Fetch existing user
            cur.execute("SELECT id FROM users WHERE name = ?;", (name,))
            row = cur.fetchone()
            if row:
                logging.info("User %s already exists with id %s", name, row["id"])
                return row["id"]
            raise


def get_user_id(name: str) -> Optional[int]:
    """Return the user ID for a given name or None if not found."""
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE name = ?;", (name,))
        row = cur.fetchone()
        return row["id"] if row else None


def add_habit(user_id: int, habit_name: str) -> int:
    """Add a new habit for the given user.

    A new row is inserted into the habits table with the current date
    recorded as the start_date. The new habit ID is returned.
    """
    start = date.today().isoformat()
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO habits (user_id, name, start_date) VALUES (?, ?, ?);",
            (user_id, habit_name, start),
        )
        conn.commit()
        habit_id = cur.lastrowid
        logging.info("Added habit '%s' for user %s (habit id %s)", habit_name, user_id, habit_id)
        return habit_id


def get_habits(user_id: int) -> List[sqlite3.Row]:
    """Retrieve all habits associated with the given user.

    Returns a list of sqlite3.Row objects with columns: id, user_id,
    name, start_date.
    """
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, start_date FROM habits WHERE user_id = ? ORDER BY id;",
            (user_id,),
        )
        return cur.fetchall()


def log_checkin(habit_id: int, completed: bool, checkin_date: Optional[date] = None) -> None:
    """Record a daily check‑in for a habit.

    Args:
        habit_id: The identifier of the habit being updated.
        completed: True if the user completed the habit today, False
            otherwise.
        checkin_date: Optionally supply a specific date; defaults to today.
    """
    if checkin_date is None:
        checkin_date = date.today()
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO progress (habit_id, checkin_date, completed) VALUES (?, ?, ?);",
            (habit_id, checkin_date.isoformat(), int(bool(completed))),
        )
        conn.commit()
        logging.debug(
            "Logged check‑in for habit %s on %s (completed=%s)", habit_id, checkin_date, completed
        )


def _get_completed_dates(habit_id: int) -> List[date]:
    """Return a list of all dates on which the habit was marked completed.

    This helper isolates SQL and parsing in one place. Dates are
    returned as datetime.date objects in descending order (most recent
    first).
    """
    with _get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT checkin_date FROM progress WHERE habit_id = ? AND completed = 1 ORDER BY checkin_date DESC;",
            (habit_id,),
        )
        rows = cur.fetchall()
        return [datetime.strptime(row["checkin_date"], "%Y-%m-%d").date() for row in rows]


def get_streak(habit_id: int) -> int:
    """Calculate the current streak of consecutive days the habit was completed.

    A streak is the number of days in a row (including today) that the
    habit has been marked completed. For example, if the user
    completed the habit on the last three days but missed the day
    before that, the streak is 3. If the habit wasn't completed today
    the streak resets to 0.
    """
    completed_dates = _get_completed_dates(habit_id)
    if not completed_dates:
        return 0
    streak = 0
    today = date.today()
    for i, record_date in enumerate(completed_dates):
        expected = today - timedelta(days=i)
        if record_date == expected:
            streak += 1
        else:
            break
    return streak


def store_user_data() -> None:
    """Persist any in‑memory changes to disk.

    Using SQLite means writes occur immediately when commit() is called.
    This function exists primarily for API symmetry and logging.
    """
    # SQLite commits happen in each function. Nothing to do here.
    logging.debug("store_user_data called; SQLite auto‑commits on write.")


def load_user_data() -> None:
    """Initialize database on application start.

    This function ensures the database exists and tables are created.
    It's idempotent so calling it repeatedly is safe.
    """
    initialize_db()
    logging.debug("Database initialized and ready.")