import logging

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from app.config import get_settings
from app.telegram.handlers import (
    cmd_help,
    cmd_insight,
    cmd_month,
    cmd_start,
    cmd_summary,
    cmd_today,
    cmd_week,
    handle_text,
)

logger = logging.getLogger(__name__)


def start_bot() -> None:
    settings = get_settings()

    application = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(None)
        .build()
    )

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("today", cmd_today))
    application.add_handler(CommandHandler("week", cmd_week))
    application.add_handler(CommandHandler("month", cmd_month))
    application.add_handler(CommandHandler("summary", cmd_summary))
    application.add_handler(CommandHandler("insight", cmd_insight))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    logger.info("PunyaMarcelBot is starting...")
    application.run_polling()