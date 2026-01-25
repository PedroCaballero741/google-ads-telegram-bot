# Google Ads Cost Telegram Bot

A Python service that fetches Google Ads cost data, stores it in PostgreSQL, and communicates via Telegram with daily reports, threshold alerts, and interactive queries.

## Features

- **Cost Tracking**: Automatically sync Google Ads spend data
- **Telegram Bot**: Interactive commands for cost reports
- **Alerts**: Get notified when spend exceeds thresholds
- **Scheduled Reports**: Daily summary reports sent automatically
- **Multiple Views**: Today, yesterday, weekly, monthly reports

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Google Ads API │────▶│   PostgreSQL │◀────│  Telegram Bot   │
│  (Cost Reports) │     │   Database   │     │  (Notifications │
└─────────────────┘     └──────────────┘     │   & Commands)   │
                              ▲              └─────────────────┘
                              │
                        ┌─────┴─────┐
                        │ Scheduler │
                        │(APScheduler)│
                        └───────────┘
```

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Google Ads API credentials
- Telegram Bot Token

### 2. Clone and Setup

```bash
cd google-ads-telegram-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 3. Configure

Edit `.env` with your credentials:

```env
# Google Ads
GOOGLE_ADS_DEVELOPER_TOKEN=your_token
GOOGLE_ADS_CLIENT_ID=your_client_id
GOOGLE_ADS_CLIENT_SECRET=your_client_secret
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
GOOGLE_ADS_CUSTOMER_ID=1234567890

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/google_ads
```

### 4. Start Database

```bash
docker-compose up -d postgres
```

### 5. Run the Bot

```bash
python main.py
```

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message & setup |
| `/today` | Today's total spend |
| `/yesterday` | Yesterday's spend summary |
| `/week` | Last 7 days report |
| `/month` | Current month summary |
| `/campaign <name>` | Search campaign by name |
| `/setalert <amount>` | Set daily spend alert |
| `/alerts` | View active alerts |
| `/deletealert <id>` | Delete an alert |
| `/sync` | Manually sync data |
| `/status` | Check bot status |
| `/help` | List all commands |

## Scheduled Jobs

- **Hourly**: Sync latest cost data from Google Ads
- **Daily 9 AM**: Send daily cost report to Telegram
- **Every 15 min**: Check alert thresholds

## Getting Google Ads API Credentials

1. Create a Google Cloud Project
2. Enable Google Ads API
3. Create OAuth 2.0 credentials
4. Apply for a Google Ads Developer Token
5. Generate a refresh token using the OAuth flow

See: https://developers.google.com/google-ads/api/docs/get-started/introduction

## Getting Telegram Bot Token

1. Talk to [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the token provided

To get your Chat ID:
1. Start a chat with your bot
2. Send a message
3. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Find your chat ID in the response

## Database Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "Description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Docker Deployment

```bash
# Build and run everything
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

## Project Structure

```
google-ads-telegram-bot/
├── config/
│   ├── settings.py          # Configuration management
│   └── google-ads.yaml      # Google Ads credentials
├── database/
│   ├── models.py            # SQLAlchemy models
│   ├── connection.py        # DB connection
│   └── migrations/          # Alembic migrations
├── services/
│   ├── google_ads.py        # Google Ads API client
│   ├── reports.py           # Report generation
│   └── alerts.py            # Alert management
├── bot/
│   ├── handlers.py          # Telegram command handlers
│   └── keyboards.py         # Inline keyboards
├── scheduler/
│   └── jobs.py              # Scheduled tasks
├── docker-compose.yml
└── main.py                  # Entry point
```

## License

MIT
