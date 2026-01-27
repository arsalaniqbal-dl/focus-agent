# Deploy Focus Agent to Railway (12 hrs/day)

Run the bot only during waking hours to maximize Railway's free tier.

**Result:** 500 free hours = ~41 days of 12-hour daily usage

---

## Step 1: Push to GitHub

```bash
cd /Users/arsalaniqbal/Projects/OperatingSystem/focus-agent

# Initialize git repo
git init
git add .
git commit -m "Initial commit: Focus Agent"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/focus-agent.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy to Railway

1. Go to https://railway.app and sign in with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `focus-agent` repo
4. Railway will auto-detect the Procfile

### Add Environment Variables

In Railway dashboard → your service → **Variables** tab:

```
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-token
MY_USER_ID=U095158463F
MORNING_TIME=11:00
TIMEZONE=Asia/Karachi
```

### Get Railway Service ID

1. In Railway dashboard, click your service
2. Look at the URL: `https://railway.app/project/XXX/service/YYY`
3. The `YYY` part is your **Service ID**

---

## Step 3: Set Up Scheduled Start/Stop

This uses GitHub Actions (free) to start/stop Railway on a schedule.

### Get Railway API Token

1. Go to https://railway.app/account/tokens
2. Click **Create Token**
3. Name it "GitHub Actions"
4. Copy the token

### Add GitHub Secrets

In your GitHub repo → **Settings** → **Secrets and variables** → **Actions**:

| Secret Name | Value |
|-------------|-------|
| `RAILWAY_TOKEN` | Your Railway API token |
| `RAILWAY_SERVICE_ID` | Service ID from step 2 |

### Schedule (default)

The workflow runs:
- **Start:** 9:00 AM PKT (4:00 UTC) daily
- **Stop:** 9:00 PM PKT (16:00 UTC) daily

To change times, edit `.github/workflows/schedule-bot.yml`:
```yaml
schedule:
  - cron: '0 4 * * *'   # Start time (UTC)
  - cron: '0 16 * * *'  # Stop time (UTC)
```

Use https://crontab.guru to help with cron syntax.

---

## Step 4: Manual Control

You can also start/stop manually:

1. Go to GitHub repo → **Actions** → **Schedule Bot**
2. Click **Run workflow**
3. Select `start` or `stop`

---

## Verify It's Working

1. Check Railway dashboard - service should show "Running" during scheduled hours
2. DM the bot in Slack
3. Check GitHub Actions tab for scheduled run history

---

## Cost Breakdown

| Usage | Hours/Month | Free Tier (500 hrs) |
|-------|-------------|---------------------|
| 24/7 | 720 hrs | ~20 days |
| 12 hrs/day | 360 hrs | ~41 days |
| 8 hrs/day | 240 hrs | ~62 days |

After free tier: ~$5/month for always-on, or continue with scheduled runs.

---

## Troubleshooting

**Bot not responding:**
- Check Railway logs: Dashboard → Service → **Deployments** → **View Logs**
- Verify environment variables are set correctly

**Scheduled start/stop not working:**
- Check GitHub Actions runs for errors
- Verify secrets are set correctly
- Make sure the Railway token hasn't expired

**Morning message not arriving:**
- Bot must be running at `MORNING_TIME`
- Adjust schedule so bot starts before your morning time
