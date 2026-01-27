# FocusPrompter

A personal Slack bot for daily task management and focus. Start every day with intention.

![FocusPrompter](https://img.shields.io/badge/Slack-Bot-4A154B?logo=slack) ![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-MIT-green)

## What It Does

FocusPrompter is a personal productivity companion that lives in your Slack DMs. It helps you:

- **Plan your morning** with a daily ritual that shows pending tasks and yesterday's spillovers
- **Track carryover** so you know what's been sitting too long (3+ day warnings)
- **Refocus mid-day** when you've lost your way
- **Daily reading** with curated tech & philosophy articles (10-15 min reads)

This isn't a team tool. It's your personal assistant.

## Quick Demo

```
You: add Review API documentation
Bot: ✅ Added: Review API documentation (#1)

You: add
    - Call design team
    - Fix login bug
    - Update README
Bot: ✅ Added 3 tasks:
     • #2 Call design team
     • #3 Fix login bug
     • #4 Update README

You: list
Bot: Your Tasks:
     ☐ 1. Review API documentation
     ☐ 2. Call design team
     ☐ 3. Fix login bug
     ☐ 4. Update README

You: done 3
Bot: 🎉 Marked #3 as done!

You: focus
Bot: ☀️ Good morning! Let's plan your day.

     🔁 Spillovers from previous days:
       - Review API documentation (day 2)

     📋 Added yesterday (not yet started):
       - Call design team
       - Update README

     📖 Daily Read (10-15 min):
     Speed Matters - James Somers
     Why being fast changes what you're capable of doing.

     What would make today a win?
```

## Commands

| Command | Description |
|---------|-------------|
| `add [task]` | Add a new task |
| `add [side] task` | Add to side projects category |
| `list` | Show all pending tasks |
| `done [id]` | Mark task complete |
| `delete [id]` | Remove a task |
| `focus` | Start morning planning |
| `refocus` | Get back on track mid-day |
| `win: [text]` | Set today's success criteria |
| `read` | Get today's article recommendation |
| `help` | Show all commands |

You can also add multiple tasks at once with a bulleted list:
```
add
- First task
- Second task
- Third task
```

## Setup

### Prerequisites

- Python 3.9+
- A Slack workspace where you can install apps

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/focus-agent.git
cd focus-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. Name it "FocusPrompter", select your workspace

**Enable Socket Mode:**
- Sidebar → **Socket Mode** → Enable
- Create an App-Level Token (name: "socket")
- Copy the token (starts with `xapp-`)

**Add Bot Permissions:**
- Sidebar → **OAuth & Permissions** → **Bot Token Scopes**
- Add: `chat:write`, `im:history`, `im:read`, `im:write`, `users:read`

**Enable Events:**
- Sidebar → **Event Subscriptions** → Enable
- Subscribe to bot event: `message.im`

**Install:**
- Sidebar → **Install App** → Install to Workspace
- Copy the Bot Token (starts with `xoxb-`)

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
MY_USER_ID=U0123456789
MORNING_TIME=08:00
TIMEZONE=America/Los_Angeles
```

Find your User ID: Slack → Profile → ⋯ → Copy member ID

### 4. Run

```bash
python bot.py
```

DM the bot in Slack and type `help` to get started.

## Deployment

See [DEPLOY.md](DEPLOY.md) for instructions on deploying to Railway with scheduled start/stop (optimized for free tier).

## Daily Reading

FocusPrompter includes 30 curated articles that rotate daily:

- *You and Your Research* — Richard Hamming
- *Speed Matters* — James Somers
- *Solitude and Leadership* — William Deresiewicz
- *The Bus Ticket Theory of Genius* — Paul Graham
- *Becoming a Magician* — Autotranslucence
- *Meditations on Moloch* — Scott Alexander
- And 24 more...

Type `read` anytime to see today's recommendation.

## Project Structure

```
focus-agent/
├── bot.py           # Main Slack bot logic
├── db.py            # SQLite storage layer
├── articles.py      # Curated reading list
├── focus.db         # Your data (created on first run)
├── requirements.txt # Python dependencies
├── Procfile         # For Railway deployment
├── .env.example     # Environment template
├── index.html       # Landing page
├── SETUP.md         # Detailed setup guide
└── DEPLOY.md        # Railway deployment guide
```

## Known Limitations

**Data persistence:** Currently uses SQLite stored locally. On platforms with ephemeral filesystems (Railway, Heroku), data resets on each deployment. For production use, consider migrating to PostgreSQL or adding a persistent volume.

## License

MIT

---

Built for personal use. Deploy your own, customize it, own your data.
