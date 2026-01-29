"""
FocusPrompter - A Slack bot for daily task management and focus.

Usage:
    DM the bot with:
    - "add [task]" - Add a new task
    - "list" or "tasks" - Show pending tasks
    - "done [id]" - Mark task as complete
    - "delete [id]" - Remove a task
    - "focus" - Start morning planning
    - "refocus" - Get back on track mid-day
    - "help" - Show commands
"""
import os
import logging
import threading
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, request, jsonify
from flask_cors import CORS
import pytz

import db
import articles

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Slack app (Socket Mode for easy local dev)
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# User config
MY_USER_ID = os.environ.get("MY_USER_ID")
MORNING_TIME = os.environ.get("MORNING_TIME", "11:30")
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Karachi")

# Debug: log config on import
print(f"[CONFIG] MORNING_TIME={MORNING_TIME}, TIMEZONE={TIMEZONE}")

# ============================================
# HTTP API for Chrome Extension
# ============================================

api = Flask(__name__)
CORS(api, resources={
    r"/api/*": {
        "origins": ["chrome-extension://*", "http://localhost:*"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type"]
    }
})

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
    """Add a new task."""
    data = request.json or {}
    text = data.get("text", "").strip()
    area = data.get("area", "work")

    if not text:
        return jsonify({"error": "Task text required"}), 400

    if area not in ["work", "side_project"]:
        area = "work"

    task_id = db.add_task(text, area)
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
    """Mark a task as completed."""
    if db.complete_task(task_id):
        return jsonify({"success": True})
    return jsonify({"error": "Task not found"}), 404


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


@api.route("/api/stats", methods=["GET"])
@require_auth
def api_get_stats():
    """Get task stats including completed today count."""
    conn = db.get_connection()
    cursor = conn.cursor()

    # Get pending count
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
    pending = cursor.fetchone()[0]

    # Get completed today count
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE status = 'completed' AND DATE(completed_at) = ?",
        (today,)
    )
    completed_today = cursor.fetchone()[0]

    conn.close()
    return jsonify({
        "pending": pending,
        "completed_today": completed_today
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


# ============================================
# Morning Planning Flow
# ============================================

def morning_planning_message() -> tuple:
    """Generate the morning planning message."""
    tasks = db.get_pending_tasks()
    stuck = db.get_stuck_tasks(min_carryover=3)

    # Increment carryover for all pending tasks (new day)
    for t in tasks:
        db.increment_carryover(t["id"])

    text = ":sunrise: *Good morning! Let's plan your day.*\n\n"

    if tasks:
        # Separate fresh tasks (day 1) from spillovers
        fresh_tasks = [t for t in tasks if t['carryover_count'] == 0]
        spillover_tasks = [t for t in tasks if t['carryover_count'] > 0]

        if spillover_tasks:
            text += ":repeat: *Spillovers from previous days:*\n"
            for t in spillover_tasks:
                days = t['carryover_count'] + 1
                warning = " :warning:" if days >= 3 else ""
                text += f"  - {t['text']} _(day {days})_{warning}\n"
            text += "\n"

        if fresh_tasks:
            text += ":clipboard: *Added yesterday (not yet started):*\n"
            text += format_task_list(fresh_tasks)
            text += "\n\n"

        # Summary to prompt action
        total = len(tasks)
        if spillover_tasks:
            text += f"_You have {total} pending item{'s' if total > 1 else ''}. "
            text += f"{len(spillover_tasks)} carried over - consider prioritizing these today._\n\n"

    if stuck:
        text += ":rotating_light: *Stuck for 3+ days (what's blocking these?):*\n"
        for t in stuck:
            text += f"  - {t['text']} (day {t['carryover_count'] + 1})\n"
        text += "\n"

    # Daily article recommendation
    title, url, description = articles.get_daily_article()
    text += articles.format_article_block(title, url, description)
    text += "\n\n"

    text += "*What would make today a win?*\n"
    text += "_Reply with your focus for today, or type `add [task]` to add items._"

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text}
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Show All Tasks"},
                    "action_id": "show_all_tasks"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "I'm Ready to Work"},
                    "action_id": "ready_to_work",
                    "style": "primary"
                }
            ]
        }
    ]

    return text, blocks


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
    if text.startswith("add "):
        task_text = original_text[4:].strip()
        if task_text:
            # Check if it's a bulleted list (multiple tasks)
            import re
            lines = task_text.split('\n')
            bullet_pattern = re.compile(r'^[\-\*\•]\s*(.+)$|^(\d+[\.\)]\s*)(.+)$')

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
        say(f"*Your Tasks:*\n{format_task_list(tasks)}")

    # --- COMPLETE TASK ---
    elif text.startswith("done ") or text.startswith("complete "):
        try:
            parts = text.split()
            task_id = int(parts[1].replace("#", ""))
            if db.complete_task(task_id):
                say(f":tada: Marked #{task_id} as done!")
            else:
                say(f"Couldn't find task #{task_id}")
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

    # --- REFOCUS ---
    elif text in ["refocus", "stuck", "help me focus"]:
        plan = db.get_today_plan()
        tasks = db.get_pending_tasks()

        if not tasks:
            say(":thinking_face: You have no pending tasks. Add some with `add [task]`")
            return

        # Find the smallest/easiest next step
        msg = ":dart: *Let's refocus.*\n\n"

        if plan and plan.get("win_criteria"):
            msg += f"This morning you said a win would be: _{plan['win_criteria']}_\n\n"

        msg += "*Your pending tasks:*\n"
        msg += format_task_list(tasks[:5])  # Show top 5

        if len(tasks) > 5:
            msg += f"\n_...and {len(tasks) - 5} more_\n"

        msg += "\n:point_right: *Pick ONE. What's the smallest next step you can take right now?*"

        say(msg)

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

*Adding & Managing Tasks:*
- `add [task]` - Add a new task
- `add [side] task` - Add to side projects
- `list` - Show all pending tasks
- `done [id]` - Mark task complete
- `delete [id]` - Remove a task

*Planning & Focus:*
- `focus` - Start morning planning
- `refocus` - Get back on track
- `win: [text]` - Set today's win criteria
- `read` - Get today's article recommendation

*Tips:*
- I'll DM you each morning at {time}
- Tasks that carry over get tracked
- If something's stuck for 3+ days, I'll ask why
        """.format(time=MORNING_TIME)
        say(help_text)

    # --- UNKNOWN ---
    else:
        # Treat as a task if it looks like one
        if len(original_text) > 3 and not original_text.startswith("/"):
            say(f"Not sure what you mean. Did you want to add a task?\n`add {original_text}`\n\nType `help` for commands.")


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
        ":muscle: *Let's go!* Focus on what matters.\n\nType `refocus` anytime you need to get back on track."
    )


# ============================================
# Scheduler Setup
# ============================================

def setup_scheduler():
    """Set up the morning planning scheduler."""
    tz = pytz.timezone(TIMEZONE)
    scheduler = BackgroundScheduler(timezone=tz)

    hour, minute = MORNING_TIME.split(":")
    scheduler.add_job(
        trigger_morning_planning,
        CronTrigger(hour=int(hour), minute=int(minute), timezone=tz),  # explicit timezone
        id="morning_planning",
        replace_existing=True,
        misfire_grace_time=300  # 5 min grace period if job missed
    )

    scheduler.start()

    # Log next scheduled run
    job = scheduler.get_job("morning_planning")
    if job and job.next_run_time:
        logger.info(f"Scheduler started. Morning planning at {MORNING_TIME} {TIMEZONE}")
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
    API: {'Enabled on port ' + str(API_PORT) if API_TOKEN else 'Disabled (set API_TOKEN)'}

    DM the bot in Slack to get started.
    Type 'help' for commands.
    ================================
    """)

    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()
