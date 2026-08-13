import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 Welcome to Agni Music!\n\n"
        "✨ Your mood, your music.\n"
        "🎶 Automatic music & playlists coming soon!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 Agni Music Commands\n\n"
        "/start - Start the bot\n"
        "/help - Show help"
    )

def main():
    token = os.environ["BOT_TOKEN"]

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    print("Agni Music Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
