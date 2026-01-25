from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import logging

from services import ReportService, AlertService, GoogleAdsService
from database.models import ThresholdType
from config import settings
from .keyboards import get_main_keyboard, get_quick_actions_keyboard, get_alerts_keyboard

logger = logging.getLogger(__name__)

# Initialize services
report_service = ReportService()
alert_service = AlertService()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    welcome_message = (
        f"👋 Hello {user.first_name}!\n\n"
        f"I'm your Google Ads Cost Tracker bot. I'll help you:\n"
        f"• Monitor daily ad spend\n"
        f"• Get cost reports on demand\n"
        f"• Alert you when thresholds are exceeded\n\n"
        f"Use the keyboard below or type /help to see all commands."
    )
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = (
        "📚 *Available Commands*\n\n"
        "*Reports:*\n"
        "/today - Today's spend summary\n"
        "/yesterday - Yesterday's spend summary\n"
        "/week - Last 7 days report\n"
        "/month - Current month summary\n"
        "/campaign <name> - Search campaign by name\n\n"
        "*Alerts:*\n"
        "/setalert <amount> - Set daily spend alert\n"
        "/alerts - View active alerts\n"
        "/deletealert <id> - Delete an alert\n\n"
        "*Admin:*\n"
        "/sync - Manually sync data from Google Ads\n"
        "/status - Check bot status"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /today command."""
    await update.message.reply_chat_action("typing")
    report = report_service.format_today_report()
    await update.message.reply_text(report, parse_mode="Markdown")


async def yesterday_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /yesterday command."""
    await update.message.reply_chat_action("typing")
    report = report_service.format_yesterday_report()
    await update.message.reply_text(report, parse_mode="Markdown")


async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /week command."""
    await update.message.reply_chat_action("typing")
    report = report_service.format_week_report()
    await update.message.reply_text(report, parse_mode="Markdown")


async def month_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /month command."""
    await update.message.reply_chat_action("typing")
    report = report_service.format_month_report()
    await update.message.reply_text(report, parse_mode="Markdown")


async def campaign_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /campaign <name> command."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a campaign name.\n"
            "Usage: /campaign <name>\n"
            "Example: /campaign Brand"
        )
        return

    campaign_name = " ".join(context.args)
    await update.message.reply_chat_action("typing")
    report = report_service.format_campaign_report(campaign_name)
    await update.message.reply_text(report, parse_mode="Markdown")


async def setalert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /setalert <amount> command."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a threshold amount.\n"
            "Usage: /setalert <amount>\n"
            "Example: /setalert 500"
        )
        return

    try:
        amount = float(context.args[0].replace("$", "").replace(",", ""))
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        await update.message.reply_text("Please provide a valid positive number.")
        return

    chat_id = str(update.effective_chat.id)
    alert = alert_service.create_alert(
        name=f"Daily Spend Alert ${amount:,.2f}",
        threshold_value=amount,
        telegram_chat_id=chat_id,
        threshold_type=ThresholdType.DAILY_SPEND,
    )

    await update.message.reply_text(
        f"✅ Alert created!\n\n"
        f"You'll be notified when daily spend exceeds ${amount:,.2f}",
        parse_mode="Markdown"
    )


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /alerts command."""
    chat_id = str(update.effective_chat.id)
    message = alert_service.format_alerts_list(chat_id)
    await update.message.reply_text(message, parse_mode="Markdown")


async def deletealert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /deletealert <id> command."""
    if not context.args:
        await update.message.reply_text(
            "Please provide an alert ID.\n"
            "Usage: /deletealert <id>\n"
            "Use /alerts to see alert IDs."
        )
        return

    try:
        alert_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a valid alert ID (number).")
        return

    if alert_service.delete_alert(alert_id):
        await update.message.reply_text(f"✅ Alert {alert_id} deleted.")
    else:
        await update.message.reply_text(f"❌ Alert {alert_id} not found.")


async def sync_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sync command - manually trigger data sync."""
    await update.message.reply_text("🔄 Syncing data from Google Ads...")
    await update.message.reply_chat_action("typing")

    try:
        google_ads_service = GoogleAdsService()
        count = google_ads_service.sync_last_n_days(7)
        await update.message.reply_text(f"✅ Sync complete! Updated {count} records.")
    except Exception as e:
        logger.error(f"Sync error: {e}")
        await update.message.reply_text(f"❌ Sync failed: {str(e)}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    chat_id = str(update.effective_chat.id)
    alerts = alert_service.get_active_alerts(chat_id)

    status_text = (
        "🤖 *Bot Status*\n\n"
        f"✅ Bot is running\n"
        f"📊 Active alerts: {len(alerts)}\n"
        f"💬 Chat ID: `{chat_id}`"
    )
    await update.message.reply_text(status_text, parse_mode="Markdown")


async def handle_keyboard_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle reply keyboard button presses."""
    text = update.message.text

    if text == "📊 Today":
        await today_command(update, context)
    elif text == "📈 Yesterday":
        await yesterday_command(update, context)
    elif text == "📅 Week":
        await week_command(update, context)
    elif text == "📆 Month":
        await month_command(update, context)
    elif text == "⚠️ Alerts":
        await alerts_command(update, context)
    elif text == "❓ Help":
        await help_command(update, context)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard callbacks."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "report_today":
        report = report_service.format_today_report()
        await query.edit_message_text(report, parse_mode="Markdown")
    elif data == "report_yesterday":
        report = report_service.format_yesterday_report()
        await query.edit_message_text(report, parse_mode="Markdown")
    elif data == "report_week":
        report = report_service.format_week_report()
        await query.edit_message_text(report, parse_mode="Markdown")
    elif data == "report_month":
        report = report_service.format_month_report()
        await query.edit_message_text(report, parse_mode="Markdown")
    elif data == "alerts_view":
        chat_id = str(update.effective_chat.id)
        message = alert_service.format_alerts_list(chat_id)
        await query.edit_message_text(message, parse_mode="Markdown")
    elif data == "cancel":
        await query.edit_message_text("Action cancelled.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Error: {context.error}", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred. Please try again later."
        )


def setup_handlers(application: Application) -> None:
    """Set up all bot handlers."""
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("yesterday", yesterday_command))
    application.add_handler(CommandHandler("week", week_command))
    application.add_handler(CommandHandler("month", month_command))
    application.add_handler(CommandHandler("campaign", campaign_command))
    application.add_handler(CommandHandler("setalert", setalert_command))
    application.add_handler(CommandHandler("alerts", alerts_command))
    application.add_handler(CommandHandler("deletealert", deletealert_command))
    application.add_handler(CommandHandler("sync", sync_command))
    application.add_handler(CommandHandler("status", status_command))

    # Callback query handler for inline keyboards
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Message handler for reply keyboard buttons
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^(📊|📈|📅|📆|⚠️|❓)"),
        handle_keyboard_buttons
    ))

    # Error handler
    application.add_error_handler(error_handler)

    logger.info("Bot handlers configured")
