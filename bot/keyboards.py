from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Get the main reply keyboard."""
    keyboard = [
        ["📊 Today", "📈 Yesterday"],
        ["📅 Week", "📆 Month"],
        ["⚠️ Alerts", "❓ Help"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_quick_actions_keyboard() -> InlineKeyboardMarkup:
    """Get quick action inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("Today", callback_data="report_today"),
            InlineKeyboardButton("Yesterday", callback_data="report_yesterday"),
        ],
        [
            InlineKeyboardButton("Week", callback_data="report_week"),
            InlineKeyboardButton("Month", callback_data="report_month"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_alerts_keyboard() -> InlineKeyboardMarkup:
    """Get alerts management inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("View Alerts", callback_data="alerts_view"),
            InlineKeyboardButton("Set Alert", callback_data="alerts_set"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Get confirmation keyboard for delete/deactivate actions."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}_{item_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
