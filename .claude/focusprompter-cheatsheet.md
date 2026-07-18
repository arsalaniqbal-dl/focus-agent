# 📌 FocusPrompter — Ops Cheat-Sheet

**Architecture (serverless, no Railway):**
- **Morning DM** runs in the cloud via **GitHub Actions** (`send_morning.py` → `.github/workflows/morning-dm.yml`), Mon–Fri 11:30 Asia/Karachi. Fires regardless of whether any local machine is on.
- **Data** lives in **Supabase Postgres** (`DB_*` env vars). Local SQLite (`focus.db`) is only a dev fallback when `DB_HOST` is unset.
- **Interactive Slack commands + Chrome extension** only work while `bot.py` runs locally. It's auto-started on this Mac via a **launchd** agent (`com.focusprompter.bot`), so it's normally already running.

**Key commands:**
| Need | Command |
|---|---|
| Is the background bot alive? | `launchctl list \| grep focusprompter` |
| Bot logs / errors | `tail -f logs/bot.out.log` · `tail -f logs/bot.err.log` |
| Stop the background bot | `launchctl unload -w ~/Library/LaunchAgents/com.focusprompter.bot.plist` |
| Start it again | `launchctl load -w ~/Library/LaunchAgents/com.focusprompter.bot.plist` |
| Run the bot by hand | `./venv/bin/python bot.py` |
| Fire the morning DM now | `gh workflow run morning-dm.yml` |
| Check live task count in Supabase | `./venv/bin/python -c "from dotenv import load_dotenv; load_dotenv(); import db; print(len(db.get_pending_tasks()))"` |

**Gotchas:**
- No bare `python` on this Mac — use `./venv/bin/python` (or `python3`).
- `bot.py`/`send_morning.py` must `load_dotenv()` **before** `import db` (db picks its backend at import time). Startup banner prints `Database: Supabase (Postgres)` when correct.
- The launchd bot runs with `DISABLE_SCHEDULER=1` so it does **not** send a duplicate morning DM (GitHub Actions owns that).
- Extension settings → API URL `http://localhost:8080`, token = `API_TOKEN` from `.env`.

See `DEPLOY.md` for full deployment details and how to restore full interactivity on a free always-on host.
