"""
Google Ads Cost Telegram Bot

Main entry point that initializes and runs:
- PostgreSQL database connection
- Telegram bot
- APScheduler for periodic tasks
"""

import asyncio
import logging
import signal
import sys
from telegram import BotCommand
from telegram.ext import Application

from config import settings
from database import init_db, close_db
from bot import setup_handlers
from scheduler import setup_scheduler, get_scheduler
from scheduler.jobs import run_initial_sync

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

# Reduce noise from external libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Initialize services after the bot starts."""
    logger.info("Initializing database...")
    init_db()

    # Set up bot commands menu (appears when user types "/")
    commands = [
        BotCommand("start", "Start the bot and show main menu"),
        BotCommand("help", "Show all available commands"),
        BotCommand("today", "Today's spend summary"),
        BotCommand("yesterday", "Yesterday's spend summary"),
        BotCommand("week", "Last 7 days report"),
        BotCommand("month", "Current month summary"),
        BotCommand("campaign", "Search campaign by name"),
        BotCommand("setalert", "Set daily spend alert"),
        BotCommand("alerts", "View active alerts"),
        BotCommand("deletealert", "Delete an alert by ID"),
        BotCommand("sync", "Manually sync Google Ads data"),
        BotCommand("status", "Check bot and scheduler status"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands menu configured")

    logger.info("Setting up scheduler...")
    scheduler = setup_scheduler(application)
    scheduler.start()

    # Run initial sync in background (don't block startup)
    asyncio.create_task(run_initial_sync())

    logger.info("Bot initialization complete!")


async def shutdown(application: Application) -> None:
    """Cleanup on shutdown."""
    logger.info("Shutting down...")

    # Stop scheduler
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    # Close database connections
    close_db()
    logger.info("Database connections closed")


def main():
    """Main entry point."""
    logger.info("=" * 50)
    logger.info("Google Ads Cost Telegram Bot Starting...")
    logger.info("=" * 50)

    # Create the Telegram bot application
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(shutdown)
        .build()
    )

    # Set up command and message handlers
    setup_handlers(application)

    # Run the bot
    logger.info(f"Starting bot in timezone: {settings.timezone}")
    logger.info(f"Default chat ID: {settings.telegram_chat_id}")
    logger.info("Bot is now running. Press Ctrl+C to stop.")

    application.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
