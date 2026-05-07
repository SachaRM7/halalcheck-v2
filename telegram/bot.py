#!/usr/bin/env python3
from __future__ import annotations

import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    web_app_url = os.getenv("HALALCHECK_WEBAPP_URL", "http://localhost:8000/web/index.html")
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Open HalalCheck", web_app=WebAppInfo(url=web_app_url))]]
    )
    if update.message:
        await update.message.reply_text(
            "Assalamu alaikum! Open HalalCheck to scan products, search halal restaurants, and manage alerts.",
            reply_markup=keyboard,
        )



def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is required")
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
