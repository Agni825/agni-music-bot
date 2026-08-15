import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello!\n\n"
        "🎵 Welcome to Agni Music Bot!\n"
        "🤖 Basic bot is working successfully!\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/about - About this bot"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Help\n\n"
        "/start - Start the bot\n"
        "/help - Show commands\n"
        "/about - About Agni Bot"
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 Agni Music Bot\n\n"
        "Currently running in Basic Mode.\n"
        "Music features will be added later! 🚀"
    )


def main():
    token = os.environ.get("BOT_TOKEN")

    if not token:
        print("❌ BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))

    print("✅ Agni Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()