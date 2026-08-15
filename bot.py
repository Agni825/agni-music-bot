import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)


# =========================
# RENDER HEALTH SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Agni Music Bot is running!")

    def log_message(self, format, *args):
        pass


def run_server():
    port = int(os.environ.get("PORT", "10000"))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(f"Health server running on port {port}")
    server.serve_forever()


# =========================
# TELEGRAM COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Hello!\n\n"
        "🎵 Welcome to Agni Music Bot!\n\n"
        "🤖 Bot is working successfully!\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/about - About the bot\n"
        "/ping - Check bot status"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📚 Help\n\n"
        "/start - Start the bot\n"
        "/help - Show commands\n"
        "/about - About Agni Music Bot\n"
        "/ping - Check if bot is online"
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🎧 Agni Music Bot\n\n"
        "🤖 Currently running in Basic Mode.\n"
        "🎵 Music features will be added later!"
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🏓 Pong!\n\n"
        "✅ Bot is online and working!"
    )


# =========================
# MAIN
# =========================

def main():

    token = os.environ.get("BOT_TOKEN")

    if not token:
        print("❌ BOT_TOKEN is missing!")
        return

    # Start Render health server
    Thread(
        target=run_server,
        daemon=True
    ).start()

    # Telegram bot
    app = (
        ApplicationBuilder()
        .token(token)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("about", about)
    )

    app.add_handler(
        CommandHandler("ping", ping)
    )

    print("✅ Agni Music Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()