# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Telegram bot that monitors Google Ads campaign costs, stores data in PostgreSQL, and sends automated alerts/reports. Runs as a 24/7 background service (not a web app).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py

# Run with Docker (includes PostgreSQL)
docker-compose up -d

# Run only PostgreSQL for local development
docker-compose up -d postgres

# Database migrations (Alembic)
alembic upgrade head
```

## Architecture

```
main.py                    # Entry point: init DB → setup bot → start scheduler → polling
├── config/settings.py     # Pydantic settings from environment variables
├── database/
│   ├── connection.py      # SQLAlchemy engine, session factory, context manager
│   └── models.py          # 3 tables: AdCost, AlertThreshold, AlertHistory
├── services/
│   ├── google_ads.py      # Fetches data via GAQL, syncs to database
│   ├── reports.py         # Formats cost reports for Telegram display
│   └── alerts.py          # Manages thresholds, checks triggers, formats notifications
├── bot/
│   ├── handlers.py        # Command handlers with @authorized_only decorator
│   └── keyboards.py       # Reply and inline keyboard layouts
└── scheduler/jobs.py      # 3 APScheduler jobs: hourly sync, daily report, 15-min alerts
```

## Key Patterns

**Authorization**: Commands protected by `@authorized_only` and `@authorized_callback_only` decorators. User IDs from `AUTHORIZED_USERS` env var (falls back to `TELEGRAM_CHAT_ID`).

**Database sessions**: Use the context manager pattern:
```python
from database.connection import get_session

with get_session() as session:
    # Auto-commits on success, rolls back on exception
```

**Service methods return dicts**: AlertService methods return dictionaries instead of ORM objects to avoid SQLAlchemy DetachedInstanceError after session closes.

**Cost storage**: Google Ads costs stored in micros (1,000,000 = $1.00). Use `cost_micros / 1_000_000` for display.

## Database Schema

- **ad_costs**: Daily campaign spend data. Unique on (date, campaign_id).
- **alert_thresholds**: User-configured spend alerts (DAILY_SPEND or CAMPAIGN_SPEND types).
- **alert_history**: Prevents duplicate alerts. Unique on (threshold_id, triggered_date).

## Scheduled Jobs

| Job | Interval | Function |
|-----|----------|----------|
| sync_google_ads_data | 1 hour | Fetches today's data from Google Ads |
| send_daily_report | 9:00 AM | Sends yesterday's summary to chat |
| check_alert_thresholds | 15 min | Checks all alerts, sends notifications |

On startup: `run_initial_sync()` syncs the last 7 days.

## Environment Variables

Required: `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `DATABASE_URL`

Optional: `AUTHORIZED_USERS` (comma-separated), `DEFAULT_ALERT_THRESHOLD`, `TIMEZONE`, `LOG_LEVEL`
