# Deploy FocusPrompter (serverless morning DM)

FocusPrompter no longer needs an always-on host. The weekday-morning digest is
sent by a **GitHub Actions cron job** (`.github/workflows/morning-dm.yml`) that
connects to your existing Supabase database and posts to Slack. It's free on a
public repo and there's no server to run or pay for.

**Tradeoff:** without an always-on process there is no Socket Mode listener, so
interactive Slack commands (`add`, `list`, `done`, buttons) and the Chrome
extension / `/app` web UI are no longer served. The morning message is a one-way
digest. Your task history and article rotation are unaffected — see below.

---

## What still works vs. what stops

| Feature | Status |
|---------|--------|
| Weekday morning DM (pending tasks + carryover + daily article) | ✅ via GitHub Actions |
| Task history in Supabase | ✅ untouched (Action reads the same DB) |
| Daily article rotation | ✅ deterministic by day-of-year — sequence continues unchanged |
| Interactive DM commands (`add`/`list`/`done`/`snooze`) | ❌ needs Socket Mode (always-on) |
| Message buttons / overflow menus | ❌ needs a running listener |
| Chrome extension + `/app` web UI | ❌ needs the Flask server |

To manage tasks you can run `python bot.py` locally on demand (it still speaks to
Supabase if the `DB_*` vars are set), or edit rows directly in Supabase.

---

## Setup: GitHub Secrets

The Action needs the same credentials the bot used on Railway. In the repo →
**Settings → Secrets and variables → Actions → New repository secret**, add:

| Secret | Where to get it |
|--------|-----------------|
| `SLACK_BOT_TOKEN` | Slack app OAuth token (`xoxb-…`) |
| `MY_USER_ID` | Your Slack member ID (`U…`) |
| `DB_HOST` | Supabase → Project → Connect → Session Pooler host |
| `DB_PORT` | Supabase pooler port (e.g. `5432` or `6543`) |
| `DB_NAME` | `postgres` |
| `DB_USER` | Supabase pooler user |
| `DB_PASSWORD` | Supabase database password |

> Copy the `DB_*` values from your **Railway service variables** (or the Supabase
> dashboard) so the Action reads the **same** database — this is what keeps your
> full task history. If `DB_HOST` is missing, `send_morning.py` fails loudly
> instead of silently sending an empty digest.

---

## Schedule

`morning-dm.yml` runs `cron: '30 6 * * 1-5'` — 06:30 UTC = **11:30 Asia/Karachi**,
Mon–Fri. Pakistan has no DST, so this is stable year-round. To change the time,
edit the cron (UTC) in that file. GitHub cron is best-effort and can be delayed a
few minutes under load.

## Test it now

Repo → **Actions → Morning DM → Run workflow**. You should get the DM within a
few seconds. Check the run logs if not.

## Keepalive

GitHub disables scheduled workflows after 60 days of repo inactivity.
`keepalive.yml` pushes a trivial empty commit on the 1st of each month so the
morning cron stays enabled. No action needed on your part.

---

## Decommission Railway

Once the Action posts successfully:

1. Railway dashboard → your project → **Settings → Delete Service/Project**.
2. Cancel/downgrade the Railway plan if you were on a paid one.
3. Your data is safe — it lives in Supabase, not on Railway.

The old `RAILWAY_TOKEN` / `RAILWAY_SERVICE_ID` GitHub secrets can be deleted too.
