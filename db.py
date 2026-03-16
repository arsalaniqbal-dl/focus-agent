"""
PostgreSQL storage for tasks and daily plans (Supabase-hosted).
Falls back to SQLite if DB_HOST is not set (local dev).
"""
import os
from datetime import datetime, date, timedelta
from typing import Optional

DB_HOST = os.environ.get("DB_HOST")

if DB_HOST:
    import psycopg2
    import psycopg2.extras

    def get_connection():
        conn = psycopg2.connect(
            host=DB_HOST,
            port=int(os.environ.get("DB_PORT", 5432)),
            dbname=os.environ.get("DB_NAME", "postgres"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", ""),
        )
        return conn

    def _fetchall(cursor):
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _fetchone(cursor):
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None

    _param = "%s"
else:
    import sqlite3
    from pathlib import Path

    DB_PATH = Path(__file__).parent / "focus.db"

    def get_connection():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _fetchall(cursor):
        return [dict(row) for row in cursor.fetchall()]

    def _fetchone(cursor):
        row = cursor.fetchone()
        return dict(row) if row else None

    _param = "?"


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    if DB_HOST:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                area TEXT DEFAULT 'work',
                created_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP,
                status TEXT DEFAULT 'pending',
                carryover_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_plans (
                id SERIAL PRIMARY KEY,
                plan_date DATE NOT NULL UNIQUE,
                focus_items TEXT,
                win_criteria TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                area TEXT DEFAULT 'work',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT DEFAULT 'pending',
                carryover_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_date DATE NOT NULL UNIQUE,
                focus_items TEXT,
                win_criteria TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    conn.commit()
    conn.close()


# --- Task Operations ---

def add_task(text: str, area: str = "work") -> int:
    """Add a new task. Returns the task ID."""
    conn = get_connection()
    cursor = conn.cursor()
    if DB_HOST:
        cursor.execute(
            "INSERT INTO tasks (text, area) VALUES (%s, %s) RETURNING id",
            (text, area)
        )
        task_id = cursor.fetchone()[0]
    else:
        cursor.execute(
            "INSERT INTO tasks (text, area) VALUES (?, ?)",
            (text, area)
        )
        task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def get_pending_tasks() -> list:
    """Get all pending (incomplete) tasks."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at"
    )
    tasks = _fetchall(cursor)
    conn.close()
    return tasks


def get_tasks_by_area(area: str) -> list:
    """Get pending tasks for a specific area."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM tasks WHERE status = 'pending' AND area = {_param} ORDER BY created_at",
        (area,)
    )
    tasks = _fetchall(cursor)
    conn.close()
    return tasks


def complete_task(task_id: int) -> bool:
    """Mark a task as completed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE tasks SET status = 'completed', completed_at = {_param} WHERE id = {_param}",
        (datetime.now(), task_id)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def delete_task(task_id: int) -> bool:
    """Delete a task entirely."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM tasks WHERE id = {_param}", (task_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def increment_carryover(task_id: int):
    """Increment the carryover count for a task (called when it rolls to next day)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE tasks SET carryover_count = carryover_count + 1 WHERE id = {_param}",
        (task_id,)
    )
    conn.commit()
    conn.close()


def get_stuck_tasks(min_carryover: int = 3) -> list:
    """Get tasks that have been carried over multiple times."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM tasks WHERE status = 'pending' AND carryover_count >= {_param}",
        (min_carryover,)
    )
    tasks = _fetchall(cursor)
    conn.close()
    return tasks


# --- Daily Plan Operations ---

def save_daily_plan(focus_items: list, win_criteria: str = "") -> int:
    """Save today's plan. Replaces existing plan for today."""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    focus_text = "\n".join(focus_items) if focus_items else ""

    if DB_HOST:
        cursor.execute(
            """INSERT INTO daily_plans (plan_date, focus_items, win_criteria)
               VALUES (%s, %s, %s)
               ON CONFLICT(plan_date) DO UPDATE SET
               focus_items = EXCLUDED.focus_items,
               win_criteria = EXCLUDED.win_criteria
               RETURNING id""",
            (today, focus_text, win_criteria)
        )
        plan_id = cursor.fetchone()[0]
    else:
        cursor.execute(
            """INSERT INTO daily_plans (plan_date, focus_items, win_criteria)
               VALUES (?, ?, ?)
               ON CONFLICT(plan_date) DO UPDATE SET
               focus_items = excluded.focus_items,
               win_criteria = excluded.win_criteria""",
            (today, focus_text, win_criteria)
        )
        plan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return plan_id


def get_today_plan() -> Optional[dict]:
    """Get today's plan if it exists."""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute(
        f"SELECT * FROM daily_plans WHERE plan_date = {_param}",
        (today,)
    )
    row = _fetchone(cursor)
    conn.close()
    return row


def get_yesterday_plan() -> Optional[dict]:
    """Get yesterday's plan to check carryover."""
    conn = get_connection()
    cursor = conn.cursor()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    cursor.execute(
        f"SELECT * FROM daily_plans WHERE plan_date = {_param}",
        (yesterday,)
    )
    row = _fetchone(cursor)
    conn.close()
    return row


# Initialize on import
init_db()
