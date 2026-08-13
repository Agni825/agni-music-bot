import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Render Port Binding Code ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Agni Music Bot is running!")

def run_port_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Background mein port server start karein
Thread(target=run_port_server, daemon=True).start()
# --------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 Welcome to Agni Music!\n\n"
        "✨ Your mood, your music.\n\n"
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

