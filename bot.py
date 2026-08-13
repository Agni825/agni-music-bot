import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from youtubesearchpython import VideosSearch

# --- Render Web Service Keep-Alive Port ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Agni Music Bot Status: Active")

def run_port_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_port_server, daemon=True).start()
# ------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 *Welcome to Agni Music!*\n\n"
        "✨ Play songs non-stop using the commands below:\n"
        "👉 `/play <song name>` (e.g. `/play Kesariya`)\n"
        "👉 `/autoplay` (Toggle continuous mode)",
        parse_mode="Markdown"
    )

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("❌ Kripya gane ka naam likhein!\nExample: `/play Kesariya`", parse_mode="Markdown")
        return

    msg = await update.message.reply_text(f"🔍 Searching YouTube for *{query}*...", parse_mode="Markdown")
    
    try:
        results = VideosSearch(query, limit=1).result()
        if results['result']:
            song = results['result'][0]
            title = song['title']
            link = song['link']
            duration = song['duration']
            
            await msg.edit_text(
                f"▶️ **Now Playing:** {title}\n"
                f"⏱️ **Duration:** {duration}\n"
                f"🔗 **Link:** [Click to Listen]({link})\n\n"
                f"🎶 *Spotify Continuous Mode Active!*",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            await msg.edit_text("❌ Song nahi mila, kripya sahi naam likhein.")
    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {e}")

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("Error: BOT_TOKEN not found!")
        return

    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    
    print("Agni Music Bot is running successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()

