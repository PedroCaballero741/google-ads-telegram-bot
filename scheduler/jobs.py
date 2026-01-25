from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import date
import logging
import asyncio

from config import settings
from services import GoogleAdsService, ReportService, AlertService

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler = None
_bot_app = None


def get_scheduler() -> AsyncIOScheduler:
    """Get the scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=settings.tz)
    return _scheduler


async def sync_google_ads_data():
    """Job: Sync latest data from Google Ads API."""
    logger.info("Running scheduled Google Ads sync...")
    try:
        google_ads_service = GoogleAdsService()
        count = google_ads_service.sync_today()
        logger.info(f"Synced {count} records from Google Ads")
    except Exception as e:
        logger.error(f"Google Ads sync failed: {e}")


async def send_daily_report():
    """Job: Send daily summary report to Telegram."""
    global _bot_app
    if not _bot_app:
        logger.error("Bot application not initialized")
        return

    logger.info("Sending daily report...")
    try:
        report_service = ReportService()
        report = report_service.format_daily_summary_for_telegram()

        # Send to configured chat
        await _bot_app.bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=report,
            parse_mode="Markdown"
        )
        logger.info("Daily report sent successfully")
    except Exception as e:
        logger.error(f"Failed to send daily report: {e}")


async def check_alert_thresholds():
    """Job: Check if any alert thresholds have been exceeded."""
    global _bot_app
    if not _bot_app:
        logger.error("Bot application not initialized")
        return

    logger.info("Checking alert thresholds...")
    try:
        alert_service = AlertService()
        triggered_alerts = alert_service.check_alerts(date.today())

        for alert_info in triggered_alerts:
            message = alert_service.format_alert_message(alert_info)

            # Send alert to the configured chat
            await _bot_app.bot.send_message(
                chat_id=alert_info["chat_id"],
                text=message,
                parse_mode="Markdown"
            )

            # Mark alert as sent
            alert_service.mark_alert_sent(alert_info["history_id"])
            logger.info(f"Alert sent: {alert_info['alert_name']}")

        if triggered_alerts:
            logger.info(f"Sent {len(triggered_alerts)} alerts")
    except Exception as e:
        logger.error(f"Alert check failed: {e}")


def setup_scheduler(bot_app) -> AsyncIOScheduler:
    """
    Set up and configure the scheduler with all jobs.

    Args:
        bot_app: The Telegram bot application instance

    Returns:
        Configured AsyncIOScheduler instance
    """
    global _bot_app
    _bot_app = bot_app

    scheduler = get_scheduler()

    # Sync Google Ads data every hour
    scheduler.add_job(
        sync_google_ads_data,
        trigger=IntervalTrigger(hours=1),
        id="sync_google_ads",
        name="Sync Google Ads Data",
        replace_existing=True,
    )

    # Send daily report at 9 AM
    scheduler.add_job(
        send_daily_report,
        trigger=CronTrigger(hour=9, minute=0),
        id="daily_report",
        name="Send Daily Report",
        replace_existing=True,
    )

    # Check alert thresholds every 15 minutes
    scheduler.add_job(
        check_alert_thresholds,
        trigger=IntervalTrigger(minutes=15),
        id="check_alerts",
        name="Check Alert Thresholds",
        replace_existing=True,
    )

    logger.info("Scheduler configured with jobs:")
    logger.info("  - Google Ads sync: every hour")
    logger.info("  - Daily report: 9:00 AM")
    logger.info("  - Alert check: every 15 minutes")

    return scheduler


async def run_initial_sync():
    """Run an initial data sync on startup."""
    logger.info("Running initial data sync...")
    try:
        google_ads_service = GoogleAdsService()
        count = google_ads_service.sync_last_n_days(7)
        logger.info(f"Initial sync complete: {count} records")
    except Exception as e:
        logger.error(f"Initial sync failed: {e}")
