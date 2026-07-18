"""
FocusPrompter - A Slack bot for daily task management and focus.

Usage:
    DM the bot with:
    - "add [task]" - Add a new task
    - "list" or "tasks" - Show pending tasks
    - "done [id]" - Mark task as complete
    - "delete [id]" - Remove a task
    - "snooze [id] until tomorrow" - Snooze a task
    - "focus" - Start morning planning
    - "review" - Weekly review
    - "help" - Show commands
"""
import os
import re
import logging
import threading
from pathlib import Path
from functools import wraps
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import pytz

import db
import articles

# Load environment from the .env next to this file, and let it WIN over any
# stale/empty vars lingering in the shell (override=True). Without this, a
# leftover DB_HOST="" in the terminal makes db.py silently fall back to SQLite.
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Slack app (Socket Mode for easy local dev)
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# User config
MY_USER_ID = os.environ.get("MY_USER_ID")
MORNING_TIME = os.environ.get("MORNING_TIME", "11:30")
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Karachi")

# Which database did we connect to? db.py picks Postgres when DB_HOST is set,
# otherwise it silently falls back to a local SQLite file. Surfacing this at
# startup prevents the "extension shows stale tasks" confusion.
DB_BACKEND = (
    "Supabase (Postgres)" if os.environ.get("DB_HOST")
    else "local SQLite — FALLBACK, NOT your Supabase data!"
)

# Module-level scheduler (set in setup_scheduler)
scheduler = None

# Debug: log config on import
print(f"[CONFIG] MORNING_TIME={MORNING_TIME}, TIMEZONE={TIMEZONE}, DB={DB_BACKEND}")
if not os.environ.get("DB_HOST"):
    print("[WARN] DB_HOST not set — using local SQLite. Set DB_* in .env to reach your live tasks.")

# ============================================
# HTTP API for Chrome Extension
# ============================================

EXTENSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'focus-extension')

api = Flask(__name__, static_folder=EXTENSION_DIR, static_url_path='/app/static')
CORS(api, resources={
    r"/api/*": {
        "origins": ["chrome-extension://*", "http://localhost:*", "https://*.railway.app"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type"]
    }
})


@api.route("/app")
def serve_web_app_redirect():
    """Redirect /app to /app/ so relative asset paths resolve correctly."""
    return redirect("/app/")


@api.route("/app/")
def serve_web_app():
    """Serve the FocusPrompter web app (mobile-friendly extension UI)."""
    return send_from_directory(EXTENSION_DIR, 'newtab.html')


@api.route("/app/<path:filename>")
def serve_web_app_files(filename):
    """Serve extension assets (JS, CSS, icons)."""
    return send_from_directory(EXTENSION_DIR, filename)

API_TOKEN = os.environ.get("API_TOKEN")
API_PORT = int(os.environ.get("API_PORT", os.environ.get("PORT", 8080)))


def require_auth(f):
    """Decorator to require API token authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token or token != API_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@api.route("/api/health", methods=["GET"])
def api_health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@api.route("/api/tasks", methods=["GET"])
@require_auth
def api_get_tasks():
    """Get all pending tasks."""
    tasks = db.get_pending_tasks()
    return jsonify({"tasks": tasks})


@api.route("/api/tasks", methods=["POST"])
@require_auth
def api_add_task():
    """Add a new task and notify via Slack."""
    data = request.json or {}
    text = data.get("text", "").strip()
    area = data.get("area", "work")

    if not text:
        return jsonify({"error": "Task text required"}), 400

    if area not in ["work", "side_project"]:
        area = "work"

    task_id = db.add_task(text, area)

    # Send Slack notification with quick-complete button
    if MY_USER_ID:
        try:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":heavy_plus_sign: *Added:* _{text}_"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": f"Done #{task_id}"},
                            "action_id": "quick_complete",
                            "value": str(task_id),
                            "style": "primary"
                        }
                    ]
                }
            ]
            send_dm(MY_USER_ID, f"Added: {text} (done {task_id} to complete)", blocks=blocks)
        except Exception as e:
            logger.error(f"Failed to send add notification: {e}")

    return jsonify({
        "id": task_id,
        "text": text,
        "area": area,
        "status": "pending",
        "carryover_count": 0
    }), 201


@api.route("/api/tasks/<int:task_id>/complete", methods=["POST"])
@require_auth
def api_complete_task(task_id):
    """Mark a task as completed and notify via Slack."""
    # Get task details before completing
    task = db.get_task(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    task_text = task["text"]

    if db.complete_task(task_id):
        # Send Slack notification with streak info
        if MY_USER_ID:
            try:
                msg = build_done_message(task_text)
                send_dm(MY_USER_ID, msg)
            except Exception as e:
                logger.error(f"Failed to send completion notification: {e}")

        return jsonify({"success": True, "text": task_text})
    return jsonify({"error": "Failed to complete task"}), 500


@api.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@require_auth
def api_delete_task(task_id):
    """Delete a task."""
    if db.delete_task(task_id):
        return jsonify({"success": True})
    return jsonify({"error": "Task not found"}), 404


@api.route("/api/article", methods=["GET"])
@require_auth
def api_get_article():
    """Get today's recommended article."""
    title, url, description = articles.get_daily_article()
    return jsonify({
        "title": title,
        "url": url,
        "description": description
    })


@api.route("/api/article/refresh", methods=["POST"])
@require_auth
def api_refresh_article():
    """Get a random article, excluding recently seen ones."""
    data = request.get_json(silent=True) or {}
    exclude_titles = data.get("exclude", [])
    title, url, description = articles.get_random_article_excluding(exclude_titles)
    return jsonify({
        "title": title,
        "url": url,
        "description": description
    })


@api.route("/api/stats", methods=["GET"])
@require_auth
def api_get_stats():
    """Get task stats including completed today count."""
    return jsonify({
        "pending": len(db.get_pending_tasks()),
        "completed_today": db.get_completed_today_count()
    })


def run_api():
    """Run the Flask API server in a separate thread."""
    api.run(host="0.0.0.0", port=API_PORT, threaded=True, use_reloader=False)


# ============================================
# Helper Functions
# ============================================

def format_task_list(tasks: list, show_ids: bool = True) -> str:
    """Format tasks for display."""
    if not tasks:
        return "_No pending tasks._"

    lines = []
    for t in tasks:
        check = ":white_check_mark:" if t["status"] == "completed" else ":white_square:"
        carryover = f" (day {t['carryover_count'] + 1})" if t["carryover_count"] > 0 else ""
        area_tag = f"[{t['area']}]" if t["area"] != "work" else ""

        if show_ids:
            lines.append(f"{check} *{t['id']}*. {t['text']}{carryover} {area_tag}")
        else:
            lines.append(f"{check} {t['text']}{carryover} {area_tag}")

    return "\n".join(lines)


def send_dm(user_id: str, text: str, blocks: list = None):
    """Send a direct message to a user."""
    try:
        response = app.client.conversations_open(users=[user_id])
        channel_id = response["channel"]["id"]
        app.client.chat_postMessage(
            channel=channel_id,
            text=text,
            blocks=blocks
        )
    except Exception as e:
        logger.error(f"Failed to send DM: {e}")


def build_done_message(task_text: str) -> str:
    """Build a completion message with remaining count and streak info."""
    remaining = len(db.get_pending_tasks())
    msg = f":white_check_mark: Done: *{task_text}*. {remaining} task{'s' if remaining != 1 else ''} left."

    completed_today = db.get_completed_today_count()
    if completed_today == 3:
        msg += "\n:fire: 3 done today — on a roll."
    elif completed_today == 5:
        msg += "\n:star2: 5 done today — incredible focus."
    elif completed_today >= 7:
        msg += f"\n:trophy: {completed_today} done today — unstoppable."

    streak = db.get_completion_streak()
    if streak >= 3:
        msg += f"\n:calendar: {streak}-day streak."

    return msg


# ============================================
# Morning Planning Flow
# ============================================

def morning_planning_message() -> tuple:
    """Generate the morning planning message with per-task actions."""
    tasks = db.get_pending_tasks()
    stuck = db.get_stuck_tasks(min_carryover=3)

    # Increment carryover for all pending tasks (new day)
    for t in tasks:
        db.increment_carryover(t["id"])

    # Build blocks
    blocks = []

    # Header
    header_text = ":sunrise: *Good morning! Let's plan your day.*"
    if tasks:
        spillover_count = sum(1 for t in tasks if t['carryover_count'] > 0)
        if spillover_count:
            header_text += f"\n_{len(tasks)} pending, {spillover_count} carried over._"
        else:
            header_text += f"\n_{len(tasks)} pending task{'s' if len(tasks) != 1 else ''}._"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": header_text}})
    blocks.append({"type": "divider"})

    # Per-task blocks with actions (limit to 10 to stay under Slack's 50-block limit)
    display_tasks = tasks[:10]
    for t in display_tasks:
        days = t['carryover_count'] + 1
        carryover = f"  ·  day {days}" if t['carryover_count'] > 0 else ""
        warning = " :warning:" if days >= 3 else ""
        area_tag = f"  ·  _{t['area']}_" if t['area'] != "work" else ""

        task_text = f"*{t['text']}*{carryover}{area_tag}{warning}"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": task_text},
            "accessory": {
                "type": "overflow",
                "action_id": f"task_overflow_{t['id']}",
                "options": [
                    {
                        "text": {"type": "plain_text", "text": ":white_check_mark: Done"},
                        "value": f"done_{t['id']}"
                    },
                    {
                        "text": {"type": "plain_text", "text": ":zzz: Snooze until tomorrow"},
                        "value": f"snooze_{t['id']}"
                    },
                    {
                        "text": {"type": "plain_text", "text": ":wastebasket: Delete"},
                        "value": f"delete_{t['id']}"
                    }
                ]
            }
        })

    if len(tasks) > 10:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"_...and {len(tasks) - 10} more. Type `list` to see all._"}
        })

    blocks.append({"type": "divider"})

    # Daily article
    title, url, description = articles.get_daily_article()
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": f":book: *Daily Read:* <{url}|{title}>\n_{description}_"}
    })

    # Win criteria prompt
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*What would make today a win?*\n_Reply with `win: [your focus]` or `add [task]`._"}
    })

    # Fallback text for notifications
    fallback = f"Good morning! You have {len(tasks)} pending tasks."

    return fallback, blocks


def trigger_morning_planning():
    """Send morning planning DM (called by scheduler)."""
    logger.info(f"=== SCHEDULER TRIGGERED at {datetime.now()} ===")
    if MY_USER_ID:
        logger.info(f"Sending morning planning to {MY_USER_ID}")
        text, blocks = morning_planning_message()
        send_dm(MY_USER_ID, text, blocks)
        logger.info("Morning planning sent successfully")
    else:
        logger.error("MY_USER_ID not set - cannot send morning planning")


# ============================================
# Message Handlers
# ============================================

@app.event("message")
def handle_message(event, say):
    """Handle direct messages to the bot."""
    # Only respond to DMs (not channels)
    if event.get("channel_type") != "im":
        return

    # Ignore bot's own messages
    if event.get("bot_id"):
        return

    text = event.get("text", "").strip().lower()
    original_text = event.get("text", "").strip()

    # --- ADD TASK (single or bulleted list) ---
    if text.startswith("add ") or text.startswith("add\n"):
        task_text = original_text[3:].strip()  # Skip "add", then strip whitespace/newlines
        if task_text:
            # Check if it's a bulleted list (multiple tasks)
            lines = task_text.split('\n')
            bullet_pattern = re.compile(r'^[\-\*\•\●\○\◦\▪\▸\►\◆\→\»]\s*(.+)$|^(\d+[\.\)]\s*)(.+)$')

            tasks_to_add = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                match = bullet_pattern.match(line)
                if match:
                    # Extract task text from bullet or numbered list
                    task = match.group(1) or match.group(3)
                    if task:
                        tasks_to_add.append(task.strip())
                elif len(lines) == 1:
                    # Single task, no bullet
                    tasks_to_add.append(line)

            # If no bullets found but multiple lines, treat each line as a task
            if not tasks_to_add and len(lines) > 1:
                tasks_to_add = [l.strip() for l in lines if l.strip()]

            # Fallback: single task
            if not tasks_to_add:
                tasks_to_add = [task_text]

            # Add all tasks
            added = []
            for task in tasks_to_add:
                area = "work"
                if task.lower().startswith("[side]") or task.lower().startswith("[project]"):
                    area = "side_project"
                    task = task.split("]", 1)[1].strip()
                task_id = db.add_task(task, area)
                added.append(f"#{task_id} {task}")

            if len(added) == 1:
                say(f":white_check_mark: Added: *{tasks_to_add[0]}* (#{task_id})")
            else:
                response = f":white_check_mark: Added {len(added)} tasks:\n"
                for item in added:
                    response += f"  • {item}\n"
                say(response)
        else:
            say("Usage: `add [task description]`\nOptional: `add [side] task` for side projects\n\nYou can also add multiple tasks with a bulleted list:\n```\nadd\n- Task one\n- Task two\n- Task three\n```")

    # --- LIST TASKS ---
    elif text in ["list", "tasks", "show", "ls"]:
        tasks = db.get_pending_tasks()
        snoozed = db.get_snoozed_tasks()
        msg = f"*Your Tasks:*\n{format_task_list(tasks)}"
        if snoozed:
            msg += f"\n\n:zzz: _{len(snoozed)} snoozed_ (type `snoozed` to see)"
        say(msg)

    # --- COMPLETE TASK ---
    elif text.startswith("done ") or text.startswith("complete "):
        try:
            parts = text.split()
            task_id = int(parts[1].replace("#", ""))
            task = db.get_task(task_id)
            if not task:
                say(f"Couldn't find task #{task_id}")
                return
            if db.complete_task(task_id):
                say(build_done_message(task["text"]))
            else:
                say(f"Couldn't complete task #{task_id}")
        except (IndexError, ValueError):
            say("Usage: `done [task_id]` (e.g., `done 3`)")

    # --- DELETE TASK ---
    elif text.startswith("delete ") or text.startswith("remove "):
        try:
            parts = text.split()
            task_id = int(parts[1].replace("#", ""))
            if db.delete_task(task_id):
                say(f":wastebasket: Deleted task #{task_id}")
            else:
                say(f"Couldn't find task #{task_id}")
        except (IndexError, ValueError):
            say("Usage: `delete [task_id]` (e.g., `delete 3`)")

    # --- MORNING FOCUS ---
    elif text in ["focus", "morning", "plan", "start"]:
        text_msg, blocks = morning_planning_message()
        say(text=text_msg, blocks=blocks)

    # --- SNOOZE TASK ---
    elif text.startswith("snooze "):
        match = re.match(r'snooze\s+#?(\d+)\s+(?:until\s+)?(.+)', text)
        if match:
            task_id = int(match.group(1))
            duration_text = match.group(2).strip()
            today = date.today()

            if duration_text == "tomorrow":
                until = today + timedelta(days=1)
            elif duration_text in ["monday", "mon"]:
                days_ahead = (7 - today.weekday()) % 7 or 7
                until = today + timedelta(days=days_ahead)
            elif duration_text in ["next week"]:
                days_ahead = (7 - today.weekday()) % 7 or 7
                until = today + timedelta(days=days_ahead)
            elif "day" in duration_text:
                day_match = re.match(r'(\d+)\s*days?', duration_text)
                if day_match:
                    until = today + timedelta(days=int(day_match.group(1)))
                else:
                    say("Usage: `snooze [id] until tomorrow` or `snooze [id] 3 days`")
                    return
            else:
                say("Usage: `snooze [id] until tomorrow` or `snooze [id] 3 days`")
                return

            task = db.get_task(task_id)
            if not task:
                say(f"Couldn't find task #{task_id}")
                return

            if db.snooze_task(task_id, until):
                say(f":zzz: Snoozed *{task['text']}* until {until.strftime('%A, %b %d')}.")
            else:
                say(f"Couldn't snooze task #{task_id}")
        else:
            say("Usage: `snooze [id] until tomorrow` or `snooze [id] 3 days`")

    # --- SNOOZED LIST ---
    elif text in ["snoozed", "sleeping"]:
        snoozed = db.get_snoozed_tasks()
        if not snoozed:
            say("_No snoozed tasks._")
        else:
            msg = ":zzz: *Snoozed tasks:*\n"
            for t in snoozed:
                until = t.get("snoozed_until", "")
                msg += f"  - *{t['id']}*. {t['text']} — back {until}\n"
            say(msg)

    # --- WEEKLY REVIEW ---
    elif text in ["review", "weekly", "weekly review"]:
        say(weekly_review_message())

    # --- SET WIN CRITERIA ---
    elif text.startswith("win:") or text.startswith("today:"):
        win_text = original_text.split(":", 1)[1].strip()
        if win_text:
            tasks = db.get_pending_tasks()
            focus_items = [t["text"] for t in tasks[:3]]  # Top 3
            db.save_daily_plan(focus_items, win_text)
            say(f":star: Got it! Today's win: *{win_text}*\n\nNow go make it happen!")
        else:
            say("Usage: `win: [what would make today a win]`")

    # --- DEMO (sample morning message) ---
    elif text == "demo":
        # Create sample data for demo
        demo_text = ":sunrise: *Good morning! Let's plan your day.*\n\n"
        demo_text += ":repeat: *Spillovers from previous days:*\n"
        demo_text += "  - Finish API documentation (day 2)\n"
        demo_text += "  - Review pull request #42 (day 3) :warning:\n\n"
        demo_text += ":clipboard: *Added yesterday (not yet started):*\n"
        demo_text += "  - Set up monitoring alerts\n"
        demo_text += "  - Call with design team\n\n"
        demo_text += "_You have 4 pending items. 2 carried over - consider prioritizing these today._\n\n"
        demo_text += ":rotating_light: *Stuck for 3+ days (what's blocking these?):*\n"
        demo_text += "  - Review pull request #42 (day 3)\n\n"
        title, url, description = articles.get_daily_article()
        demo_text += articles.format_article_block(title, url, description)
        demo_text += "\n\n"
        demo_text += "*What would make today a win?*\n"
        demo_text += "_Reply with your focus for today, or type `add [task]` to add items._"
        say(demo_text)

    # --- ARTICLE / READ ---
    elif text in ["read", "article", "reading"]:
        title, url, description = articles.get_daily_article()
        say(articles.format_article_block(title, url, description))

    # --- TEST SCHEDULER (debug) ---
    elif text == "testmorning":
        trigger_morning_planning()
        say(":gear: Manually triggered morning planning.")

    # --- HELP ---
    elif text in ["help", "?", "commands"]:
        help_text = """
:wave: *FocusPrompter Commands*

*Tasks:*
- `add [task]` - Add a task (or `add [side] task` for side projects)
- `list` - Show pending tasks
- `done [id]` - Complete a task
- `delete [id]` - Remove a task
- `snooze [id] until tomorrow` - Snooze (also: `3 days`, `monday`)
- `snoozed` - See snoozed tasks

*Planning:*
- `focus` - Start morning planning
- `win: [text]` - Set today's win criteria
- `read` - Today's article
- `review` - Weekly review

*I'll DM you at {time} on weekday mornings.*
        """.format(time=MORNING_TIME)
        say(help_text)

    # --- UNKNOWN: offer to add as task ---
    else:
        if len(original_text) > 2 and not original_text.startswith("/"):
            say(
                text=f"Add *{original_text}* as a task?",
                blocks=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"Add *{original_text}* as a task?"}
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Yes, add it"},
                                "action_id": "confirm_add_task",
                                "value": original_text,
                                "style": "primary"
                            }
                        ]
                    }
                ]
            )


# ============================================
# Button Actions
# ============================================

@app.action("show_all_tasks")
def handle_show_all(ack, body, client):
    """Handle 'Show All Tasks' button."""
    ack()
    tasks = db.get_pending_tasks()
    user_id = body["user"]["id"]

    work_tasks = [t for t in tasks if t["area"] == "work"]
    side_tasks = [t for t in tasks if t["area"] == "side_project"]

    msg = "*All Pending Tasks:*\n\n"
    if work_tasks:
        msg += "*Work:*\n" + format_task_list(work_tasks) + "\n\n"
    if side_tasks:
        msg += "*Side Projects:*\n" + format_task_list(side_tasks) + "\n"
    if not work_tasks and not side_tasks:
        msg += "_No tasks yet. Add some with `add [task]`_"

    send_dm(user_id, msg)


@app.action("ready_to_work")
def handle_ready(ack, body, client):
    """Handle 'Ready to Work' button."""
    ack()
    user_id = body["user"]["id"]
    send_dm(
        user_id,
        ":muscle: *Let's go!* Focus on what matters.\n\nType `list` anytime to see your tasks."
    )


@app.shortcut("add_as_task")
def handle_add_as_task(ack, shortcut, client):
    """Handle 'Add as Task' message shortcut from any message's context menu."""
    ack()
    message_text = shortcut.get("message", {}).get("text", "").strip()
    user_id = shortcut["user"]["id"]

    if not message_text:
        client.chat_postEphemeral(
            channel=shortcut["channel"]["id"],
            user=user_id,
            text="Couldn't read that message."
        )
        return

    # Truncate if too long
    task_text = message_text[:200]
    task_id = db.add_task(task_text)
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f":white_check_mark: Added: *{task_text}*"}
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": f"Done #{task_id}"},
                    "action_id": "quick_complete",
                    "value": str(task_id),
                    "style": "primary"
                }
            ]
        }
    ]
    send_dm(user_id, f"Added: {task_text} (done {task_id} to complete)", blocks=blocks)


@app.action(re.compile(r"task_overflow_\d+"))
def handle_task_overflow(ack, body, client):
    """Handle overflow menu actions (done/snooze/delete) on task items."""
    ack()
    user_id = body["user"]["id"]
    selected = body["actions"][0]["selected_option"]["value"]

    # Parse action and task_id from value like "done_5", "snooze_5", "delete_5"
    action, task_id_str = selected.split("_", 1)
    task_id = int(task_id_str)

    task = db.get_task(task_id)
    if not task:
        send_dm(user_id, f"Task #{task_id} not found.")
        return

    if action == "done":
        if db.complete_task(task_id):
            send_dm(user_id, build_done_message(task["text"]))
        else:
            send_dm(user_id, f"Couldn't complete task #{task_id}")

    elif action == "snooze":
        tomorrow = date.today() + timedelta(days=1)
        if db.snooze_task(task_id, tomorrow):
            send_dm(user_id, f":zzz: Snoozed *{task['text']}* until {tomorrow.strftime('%A, %b %d')}.")
        else:
            send_dm(user_id, f"Couldn't snooze task #{task_id}")

    elif action == "delete":
        if db.delete_task(task_id):
            send_dm(user_id, f":wastebasket: Deleted *{task['text']}*")
        else:
            send_dm(user_id, f"Couldn't delete task #{task_id}")


@app.action("confirm_add_task")
def handle_confirm_add(ack, body, client):
    """Handle 'Yes, add it' button for unrecognized messages."""
    ack()
    user_id = body["user"]["id"]
    task_text = body["actions"][0]["value"]

    task_id = db.add_task(task_text)

    # Update original message to show it was added
    try:
        client.chat_update(
            channel=body["channel"]["id"],
            ts=body["message"]["ts"],
            text=f":white_check_mark: Added: *{task_text}* (#{task_id})",
            blocks=[]
        )
    except Exception as e:
        logger.error(f"Failed to update message: {e}")
        send_dm(user_id, f":white_check_mark: Added: *{task_text}* (#{task_id})")


@app.action("quick_complete")
def handle_quick_complete(ack, body, client):
    """Handle quick-complete button from extension-added tasks."""
    ack()
    user_id = body["user"]["id"]
    task_id = int(body["actions"][0]["value"])

    task = db.get_task(task_id)
    if not task or task["status"] != "pending":
        send_dm(user_id, f"Task #{task_id} already completed or not found.")
        return

    task_text = task["text"]
    if db.complete_task(task_id):
        msg = build_done_message(task_text)
        send_dm(user_id, msg)

        # Update the original message to show completed
        try:
            client.chat_update(
                channel=body["channel"]["id"],
                ts=body["message"]["ts"],
                text=f":white_check_mark: ~{task_text}~ — done",
                blocks=[]
            )
        except Exception as e:
            logger.error(f"Failed to update message: {e}")
    else:
        send_dm(user_id, f"Couldn't complete task #{task_id}")


# ============================================
# Weekly Review
# ============================================

def weekly_review_message() -> str:
    """Generate the weekly review message."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())

    completed = db.get_completed_in_range(monday, today)
    pending = db.get_pending_tasks()
    most_stuck = db.get_most_stuck_tasks(limit=5)

    text = f":calendar: *Weekly Review — Week of {monday.strftime('%b %d')}*\n\n"

    if completed:
        text += f":white_check_mark: *Completed this week: {len(completed)}*\n"
        for t in completed:
            text += f"  - {t['text']}\n"
        text += "\n"
    else:
        text += "_No tasks completed this week._\n\n"

    text += f":clipboard: *Still pending: {len(pending)}*\n"
    if pending:
        for t in pending[:5]:
            carryover = f" (day {t['carryover_count'] + 1})" if t['carryover_count'] > 0 else ""
            text += f"  - {t['text']}{carryover}\n"
        if len(pending) > 5:
            text += f"  _...and {len(pending) - 5} more_\n"
    text += "\n"

    if most_stuck:
        text += ":warning: *Most carried-over (consider dropping or breaking down):*\n"
        for t in most_stuck:
            text += f"  - {t['text']} — *{t['carryover_count'] + 1} days*\n"
        text += "\n"

    total_touched = len(completed) + len(pending)
    if total_touched > 0:
        rate = len(completed) / total_touched * 100
        text += f":bar_chart: *Completion rate: {rate:.0f}%* ({len(completed)} done / {total_touched} total)\n\n"

    text += "_Clean up: delete what you won't do, snooze what can wait, start Monday fresh._"
    return text


# ============================================
# Scheduler Setup
# ============================================

def setup_scheduler():
    """Set up the morning planning and weekly review schedulers."""
    global scheduler
    tz = pytz.timezone(TIMEZONE)
    scheduler = BackgroundScheduler(timezone=tz)

    # Morning planning — weekdays only (Mon–Fri)
    hour, minute = MORNING_TIME.split(":")
    scheduler.add_job(
        trigger_morning_planning,
        CronTrigger(day_of_week='mon-fri', hour=int(hour), minute=int(minute), timezone=tz),
        id="morning_planning",
        replace_existing=True,
        misfire_grace_time=300
    )

    scheduler.start()

    job = scheduler.get_job("morning_planning")
    if job and job.next_run_time:
        logger.info(f"Scheduler started. Morning planning at {MORNING_TIME} {TIMEZONE} (weekdays only)")
        logger.info(f"Next scheduled run: {job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    return scheduler


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    # Verify config
    if not os.environ.get("SLACK_BOT_TOKEN"):
        print("Error: SLACK_BOT_TOKEN not set. Copy .env.example to .env and fill in values.")
        exit(1)

    if not os.environ.get("SLACK_APP_TOKEN"):
        print("Error: SLACK_APP_TOKEN not set. Enable Socket Mode in your Slack app.")
        exit(1)

    if not MY_USER_ID:
        print("Warning: MY_USER_ID not set. Scheduled morning messages won't work.")

    # Start HTTP API server in background thread (for Chrome extension)
    if API_TOKEN:
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        logger.info(f"API server started on port {API_PORT}")
    else:
        logger.warning("API_TOKEN not set - HTTP API disabled")

    # Start scheduler
    scheduler = setup_scheduler()

    # Start bot
    print(f"""
    ================================
    FocusPrompter is running!
    ================================
    Morning planning: {MORNING_TIME} {TIMEZONE}
    User ID: {MY_USER_ID or 'Not set'}
    Database: {DB_BACKEND}
    API: {'Enabled on port ' + str(API_PORT) if API_TOKEN else 'Disabled (set API_TOKEN)'}

    DM the bot in Slack to get started.
    Type 'help' for commands.
    ================================
    """)

    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()
