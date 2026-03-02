# Project Notes - Google Ads Telegram Bot

## Setup Checklist

### 1. Google Ads API Setup
- [ ] Create Google Cloud Project
- [ ] Enable Google Ads API
- [ ] Create OAuth 2.0 Client credentials
- [ ] Get Developer Token (apply if needed)
- [ ] Generate refresh token

### 2. Telegram Bot Setup
- [ ] Create bot via @BotFather
- [ ] Get bot token
- [ ] Get your chat ID

### 3. Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Fill in all credentials

### 4. Database
- [ ] Start PostgreSQL: `docker-compose up -d postgres`
- [ ] Run migrations: `alembic upgrade head`

### 5. Run Application
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Start bot: `python main.py`

## Key Files

| File | Purpose |
|------|---------|
| `config/settings.py` | All configuration from environment variables |
| `database/models.py` | SQLAlchemy ORM models |
| `services/google_ads.py` | Google Ads API integration |
| `services/reports.py` | Report generation logic |
| `services/alerts.py` | Alert threshold management |
| `bot/handlers.py` | Telegram command handlers |
| `scheduler/jobs.py` | APScheduler job definitions |
| `main.py` | Application entry point |

## Database Tables

- `ad_costs` - Stores daily campaign cost data
- `alert_thresholds` - User-configured spend alerts
- `alert_history` - Track triggered alerts (prevents spam)

## Scheduled Jobs

| Job | Frequency | Description |
|-----|-----------|-------------|
| `sync_google_ads` | Every hour | Fetch latest cost data |
| `daily_report` | 9:00 AM daily | Send summary to Telegram |
| `check_alerts` | Every 15 min | Check threshold violations |

## API Rate Limits

Google Ads API:
- Basic access: 10,000 operations/day
- Standard access: 15,000 operations/day

## Troubleshooting

### Bot not responding
1. Check `TELEGRAM_BOT_TOKEN` is correct
2. Ensure bot is running (`python main.py`)
3. Check logs for errors

### No data syncing
1. Verify Google Ads credentials
2. Check `GOOGLE_ADS_CUSTOMER_ID` format (no dashes)
3. Test with `/sync` command

### Alerts not triggering
1. Verify data exists for today (`/today`)
2. Check alert is active (`/alerts`)
3. Ensure threshold is below current spend
