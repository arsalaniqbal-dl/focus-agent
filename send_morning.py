"""
Standalone morning digest sender for FocusPrompter.

Runs once per weekday morning via GitHub Actions — no always-on server needed.
Connects to the same Supabase Postgres the bot uses, builds the morning planning
message, advances carryover counts, and posts it to Slack via the Web API.

This is the serverless replacement for the APScheduler job in bot.py. It does NOT
handle interactive commands or buttons (that needs a persistent Socket Mode
connection); the message is a one-way plain-text digest.
"""
import os
import sys
import logging

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import db
import articles

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
MY_USER_ID = os.environ.get("MY_USER_ID")


def build_morning_text() -> str:
    """Build the plain-text morning planning message and advance carryover counts."""
    tasks = db.get_pending_tasks()

    # Advance carryover for all pending tasks (a new day has begun).
    # Display uses the pre-increment value + 1, matching the original bot behavior.
    for t in tasks:
        db.increment_carryover(t["id"])

    lines = [":sunrise: *Good morning! Let's plan your day.*"]

    if tasks:
        spillover = sum(1 for t in tasks if t["carryover_count"] > 0)
        if spillover:
            lines.append(f"_{len(tasks)} pending, {spillover} carried over._")
        else:
            lines.append(f"_{len(tasks)} pending task{'s' if len(tasks) != 1 else ''}._")
        lines.append("")

        for t in tasks[:10]:
            days = t["carryover_count"] + 1
            carryover = f"  ·  day {days}" if t["carryover_count"] > 0 else ""
            warning = " :warning:" if days >= 3 else ""
            area_tag = f"  ·  _{t['area']}_" if t["area"] != "work" else ""
            lines.append(f"• *{t['text']}*{carryover}{area_tag}{warning}")

        if len(tasks) > 10:
            lines.append(f"_...and {len(tasks) - 10} more._")
    else:
        lines.append("_No pending tasks — clean slate._")

    lines.append("")

    title, url, description = articles.get_daily_article()
    lines.append(f":book: *Daily Read:* <{url}|{title}>")
    lines.append(f"_{description}_")

    lines.append("")
    lines.append("_What would make today a win?_")

    return "\n".join(lines)


def main() -> int:
    if not SLACK_BOT_TOKEN:
        logger.error("SLACK_BOT_TOKEN not set — cannot post to Slack.")
        return 1
    if not MY_USER_ID:
        logger.error("MY_USER_ID not set — nowhere to send the digest.")
        return 1

    # Guard: without DB_HOST, db.py silently falls back to an empty local SQLite,
    # which would send a misleading "no pending tasks" digest every day. Fail loud.
    if not os.environ.get("DB_HOST"):
        logger.error(
            "DB_HOST not set — refusing to run against ephemeral SQLite. "
            "Set the Supabase DB_* secrets so the digest reads your real tasks."
        )
        return 1

    text = build_morning_text()

    client = WebClient(token=SLACK_BOT_TOKEN)
    try:
        channel = client.conversations_open(users=[MY_USER_ID])["channel"]["id"]
        client.chat_postMessage(channel=channel, text=text)
    except SlackApiError as e:
        logger.error(f"Slack API error: {e.response['error']}")
        return 1

    logger.info("Morning digest sent successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
