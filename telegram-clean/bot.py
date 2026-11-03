#!/usr/bin/env python3
"""MADHOUSE Telegram Clean — fresh-bot front door, nothing else.

One job: open the Dashboard with one tap.

* /start and /dashboard send ONE message with ONE button:
  "Open Dashboard" -> the WebApp URL (the telegram-clean/ site).
* The bot's menu button is set to the same WebApp, so the user can
  also tap the menu button in the Telegram client.
* /help sends the same button, plus three plain lines.
* Any other text gets the same button. No "unknown command" dead end,
  no registration conversation, no number / colour / name / chrono flow,
  no pocket flow, no command list to hunt through.

No engine call is made by this bot. The Dashboard itself works without
an engine, and says so plainly. Live Dots / Pocket / trades are added
later as a clearly labelled live section, never as a simulation.

Configuration — environment only, never in code, never in chat:
  TELEGRAM_BOT_TOKEN  from @BotFather, for the FRESH bot only.
                      Created by the user on his phone. Never pasted
                      in chat, never committed, never reset by this code.
  WEBAPP_URL          public https URL of the telegram-clean/ site.
                      Default is the GitHub Pages URL for this repo.
  WEBHOOK_URL         optional. If set, the bot runs as a webhook at
                      WEBHOOK_URL + "/tg-webhook". If unset, it polls.
                      Polling is the simple first-load test.
  WEBHOOK_SECRET      optional secret token Telegram must present
                      on webhook calls. Set it if WEBHOOK_URL is set.
"""
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, Update, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("madhouse-clean")

WEBAPP_URL = os.environ.get(
    "WEBAPP_URL", "https://zorbstoken.github.io/madhouse/telegram-clean/"
).rstrip("/") + "/"

DASHBOARD_TEXT = (
    "Welcome to the MADHOUSE.\n\n"
    "The door is open. You are welcome.\n\n"
    "Tap below. The Dashboard opens inside Telegram — "
    "no commands to learn, no forms, no phone number, "
    "no biometrics, no government registration."
)


def dashboard_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🌀 Open Dashboard", web_app=WebAppInfo(url=WEBAPP_URL))]]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(DASHBOARD_TEXT, reply_markup=dashboard_keyboard())


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Tap Open Dashboard. Bottom menu: Dashboard, Compass, Control, "
        "Site Map, Games, Map. Town Hall and Help are one tap from the Dashboard.\n\n"
        "No live Dots yet in this clean front-end — the Dashboard says so plainly.",
        reply_markup=dashboard_keyboard(),
    )


async def any_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Never a dead end, never command hunting: any text gets the Dashboard.
    await update.message.reply_text(DASHBOARD_TEXT, reply_markup=dashboard_keyboard())


async def post_init(app) -> None:
    # One-tap entry, in the client itself: the menu button opens the WebApp.
    await app.bot.set_chat_menu_button(menu_button=MenuButtonWebApp(
        text="Open Dashboard", web_app=WebAppInfo(url=WEBAPP_URL)))
    await app.bot.set_my_commands([
        ("start", "Open the Dashboard"),
        ("dashboard", "Open the Dashboard"),
        ("help", "Help, in plain words"),
    ])
    log.info("madhouse-clean: menu button and commands set for %s", WEBAPP_URL)


def build_application():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token or "__PASTE__" in token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set. Set it in the environment only.")
    return (
        ApplicationBuilder()
        .token(token)
        .post_init(post_init)
        .build()
    )


def main() -> None:
    app = build_application()
    # /dashboard is the same handler as /start by design; keep the
    # command list to three, and keep the behaviour identical.
    app.add_handler(CommandHandler(["start", "dashboard"], start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_text))
    webhook_url = os.environ.get("WEBHOOK_URL", "").rstrip("/")
    if webhook_url:
        secret = os.environ.get("WEBHOOK_SECRET", "") or None
        log.info("madhouse-clean: webhook mode at %s/tg-webhook", webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", "8080")),
            url_path="tg-webhook",
            webhook_url=webhook_url + "/tg-webhook",
            secret_token=secret,
        )
    else:
        log.info("madhouse-clean: polling mode (first-load test)")
        app.run_polling()


if __name__ == "__main__":
    main()
