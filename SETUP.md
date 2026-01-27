# FocusPrompter - Setup Guide

A personal Slack bot for daily task management and focus.

## Quick Start

```bash
cd focus-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Slack credentials
python bot.py
```

## Slack App Setup (Step-by-Step)

### 1. Create a Slack App

1. Go to https://api.slack.com/apps
2. Click **Create New App** > **From scratch**
3. Name: "FocusPrompter" (or whatever you want)
4. Workspace: Select your workspace
5. Click **Create App**

### 2. Enable Socket Mode

Socket Mode lets you run the bot locally without exposing a public URL.

1. In the left sidebar, click **Socket Mode**
2. Toggle **Enable Socket Mode** to ON
3. Give the token a name (e.g., "focus-agent-socket")
4. Copy the **App-Level Token** (starts with `xapp-`)
5. Add it to your `.env` as `SLACK_APP_TOKEN`

### 3. Configure Bot Permissions

1. In the left sidebar, click **OAuth & Permissions**
2. Scroll to **Scopes** > **Bot Token Scopes**
3. Add these scopes:
   - `chat:write` - Send messages
   - `im:history` - Read DM history
   - `im:read` - Read DM metadata
   - `im:write` - Start DMs
   - `users:read` - Look up user info

### 4. Enable Events

1. In the left sidebar, click **Event Subscriptions**
2. Toggle **Enable Events** to ON
3. Expand **Subscribe to bot events**
4. Add: `message.im` (to receive DMs)
5. Click **Save Changes**

### 5. Install the App

1. In the left sidebar, click **Install App**
2. Click **Install to Workspace**
3. Review permissions and click **Allow**
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)
5. Add it to your `.env` as `SLACK_BOT_TOKEN`

### 6. Find Your User ID

1. In Slack, click your profile picture
2. Click **Profile**
3. Click the **...** (more) button
4. Click **Copy member ID**
5. Add it to your `.env` as `MY_USER_ID`

### 7. Configure Schedule

Edit `.env`:
```
MORNING_TIME=08:00
TIMEZONE=America/Los_Angeles
```

Use your local timezone. Find yours at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

## Running the Bot

```bash
# Make sure you're in the venv
source venv/bin/activate

# Run
python bot.py
```

You should see:
```
================================
FocusPrompter is running!
================================
Morning planning: 08:00 America/Los_Angeles
User ID: U0123456789
================================
```

## Testing

1. Open Slack
2. Find "FocusPrompter" in your Apps (or search for it)
3. Send it a DM: `help`
4. Try: `add Test my first task`
5. Try: `list`
6. Try: `focus`

## Commands Reference

| Command | Description |
|---------|-------------|
| `add [task]` | Add a new task |
| `add [side] task` | Add to side projects |
| `list` | Show all pending tasks |
| `done [id]` | Mark task complete |
| `delete [id]` | Remove a task |
| `focus` | Start morning planning |
| `refocus` | Get back on track |
| `win: [text]` | Set today's win criteria |
| `help` | Show all commands |

## For Work Slack Approval

When requesting approval from your IT/admin team, explain:

**What it does:**
- Personal productivity bot for task management
- Only interacts via DMs (not in channels)
- No access to company data or other users

**Permissions needed:**
- `chat:write` - Send you DMs
- `im:history` - Read your DMs to the bot
- `im:read` / `im:write` - Handle DM conversations
- `users:read` - Look up your user ID

**Security:**
- Runs on your machine (or your own server)
- Data stays local (SQLite file)
- Open source code you can review

## Troubleshooting

**Bot doesn't respond:**
- Check the terminal for errors
- Verify `SLACK_BOT_TOKEN` starts with `xoxb-`
- Verify `SLACK_APP_TOKEN` starts with `xapp-`

**Morning message not arriving:**
- Check `MY_USER_ID` is set correctly
- Verify timezone is correct
- Check that your computer was on at the scheduled time

**"not_allowed_token_type" error:**
- You're using the wrong token
- Bot token = `xoxb-...` (for SLACK_BOT_TOKEN)
- App token = `xapp-...` (for SLACK_APP_TOKEN)

## Files

```
focus-agent/
├── bot.py           # Main bot logic
├── db.py            # SQLite storage
├── focus.db         # Your data (created on first run)
├── requirements.txt # Dependencies
├── .env.example     # Template for credentials
├── .env             # Your credentials (don't commit!)
└── SETUP.md         # This file
```
