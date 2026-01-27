"""
Simple SQLite storage for tasks and daily plans.
"""
import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "focus.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

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
        "SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at"
    )
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks


def get_tasks_by_area(area: str) -> list:
    """Get pending tasks for a specific area."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tasks WHERE status = 'pending' AND area = ? ORDER BY created_at",
        (area,)
    )
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks


def complete_task(task_id: int) -> bool:
    """Mark a task as completed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET status = 'completed', completed_at = ? WHERE id = ?",
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
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def increment_carryover(task_id: int):
    """Increment the carryover count for a task (called when it rolls to next day)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET carryover_count = carryover_count + 1 WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    conn.close()


def get_stuck_tasks(min_carryover: int = 3) -> list:
    """Get tasks that have been carried over multiple times."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tasks WHERE status = 'pending' AND carryover_count >= ?",
        (min_carryover,)
    )
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks


# --- Daily Plan Operations ---

def save_daily_plan(focus_items: list, win_criteria: str = "") -> int:
    """Save today's plan. Replaces existing plan for today."""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    focus_text = "\n".join(focus_items) if focus_items else ""

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
        "SELECT * FROM daily_plans WHERE plan_date = ?",
        (today,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_yesterday_plan() -> Optional[dict]:
    """Get yesterday's plan to check carryover."""
    conn = get_connection()
    cursor = conn.cursor()
    from datetime import timedelta
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    cursor.execute(
        "SELECT * FROM daily_plans WHERE plan_date = ?",
        (yesterday,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# Initialize on import
init_db()
