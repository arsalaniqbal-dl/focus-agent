# FocusPrompter

Personal Slack bot + Chrome extension for daily task management and focus.

## Project Overview

**What:** A Slack bot (Socket Mode) that DMs you each morning with a planning ritual — pending tasks, carryover warnings, curated article. Also has a Chrome extension new-tab page and a Flask REST API for the extension to talk to the bot.

**Stack:** Python 3.9+, slack-bolt, Flask, APScheduler, SQLite, Chrome Extension (vanilla JS/HTML/CSS)

**Status:** Working MVP. Deployed to Railway with scheduled start/stop via GitHub Actions.

## Architecture

```
focus-agent/
├── bot.py              # Main entry point — Slack bot + Flask API server + scheduler
├── db.py               # SQLite storage layer (tasks, daily_plans tables)
├── articles.py         # Curated reading list (30 articles, rotates by day-of-year)
├── create_profile.py   # Bot profile image generator (PIL)
├── focus-extension/    # Chrome extension (new tab page)
│   ├── manifest.json   # Extension manifest v3
│   ├── newtab.html     # New tab override page
│   ├── settings.html   # Extension settings page
│   ├── css/            # Styles
│   ├── js/             # Extension JS (API calls, UI)
│   └── icons/          # Extension icons
├── index.html          # Landing page
├── .github/workflows/  # Railway start/stop scheduler
├── requirements.txt    # Python deps
├── Procfile            # Railway: `worker: python bot.py`
├── .env.example        # Env var template
├── SETUP.md            # Slack app setup guide
└── DEPLOY.md           # Railway deployment guide
```

## How It Works

1. **bot.py** starts three things concurrently:
   - Slack Socket Mode handler (listens for DMs)
   - Flask API server on `API_PORT` (for Chrome extension)
   - APScheduler cron job (morning planning DM at `MORNING_TIME`)

2. **db.py** uses SQLite with two tables:
   - `tasks` — id, text, area (work/side_project), status, carryover_count, timestamps
   - `daily_plans` — date, focus_items, win_criteria

3. **Chrome extension** calls the Flask API with Bearer token auth to add/complete/list tasks

## Slack Commands

| Command | Handler |
|---------|---------|
| `add [task]` | Parses single or bulleted list, supports `[side]` prefix |
| `list` / `tasks` | Shows pending with carryover day count |
| `done [id]` | Marks complete |
| `delete [id]` | Removes task |
| `focus` / `morning` | Triggers morning planning message |
| `refocus` / `stuck` | Shows top 5 tasks + pick-one prompt |
| `win: [text]` | Sets daily win criteria |
| `read` / `article` | Today's curated article |
| `demo` | Sample morning message |
| `testmorning` | Debug: manually triggers scheduler |

## API Endpoints (Flask)

All `/api/*` routes require `Authorization: Bearer <API_TOKEN>` header.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check (no auth) |
| `/api/tasks` | GET | List pending tasks |
| `/api/tasks` | POST | Add task `{text, area}` |
| `/api/tasks/<id>/complete` | POST | Complete task |
| `/api/tasks/<id>` | DELETE | Delete task |
| `/api/article` | GET | Today's article |
| `/api/stats` | GET | Pending count + completed today |

## Environment Variables

```
SLACK_BOT_TOKEN=xoxb-...     # Bot OAuth token
SLACK_APP_TOKEN=xapp-...     # Socket Mode app-level token
MY_USER_ID=U...              # Your Slack user ID
MORNING_TIME=11:30           # 24hr format
TIMEZONE=Asia/Karachi        # pytz timezone
API_TOKEN=...                # Bearer token for Chrome extension API
API_PORT=8080                # Flask port (defaults to PORT or 8080)
```

## Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in .env values

# Run locally
python bot.py
```

## Key Design Decisions

- **Socket Mode** over webhook: simpler local dev, no ngrok needed
- **SQLite** for simplicity: single-user personal tool, not a team product
- **Flask in thread**: runs alongside Slack bot in same process for simplicity
- **Carryover tracking**: tasks auto-increment carryover_count each morning, warns at 3+ days
- **Article rotation**: deterministic by day-of-year (not random) so you get the same one all day

## Known Limitations

- SQLite on Railway's ephemeral filesystem means data resets on deploy. Needs PostgreSQL or persistent volume for production.
- No tests yet.
- Chrome extension uses hardcoded API URL from settings — no auto-discovery.
- Python 3.9 (from runtime.txt) — could upgrade.

## Working With This Codebase

- **Never commit `.env` or `focus.db`** — both are in .gitignore
- The `venv/` directory is local only — don't modify it
- When adding new Slack commands, add them to the `handle_message` function in bot.py following the existing `elif` pattern
- When adding new API endpoints, follow the existing Flask route pattern with `@require_auth` decorator
- Keep it simple — this is a personal tool, not enterprise software
