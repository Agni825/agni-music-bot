import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from youtubesearchpython import VideosSearch, Search

# --- Render Port Binding ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Agni Music Bot is Running!")

def run_port_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_port_server, daemon=True).start()
# ---------------------------

# Global Variables
song_queue = []
last_played_song = None
autoplay_enabled = True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 **Welcome to Agni Music!**\n\n"
        "✨ **Spotify Style Autoplay Active!**\n"
        "Aap bas 1 song play karein, baki songs bot apne aap mood ke hisab se endlessly chalata rahega.\n\n"
        "🔹 `/play <song name>` - Play music\n"
        "🔹 `/autoplay <on/off>` - Turn autoplay On or Off",
        parse_mode="Markdown"
    )

# Related/Similar Song Search karne ka function
def get_recommendation(last_song_title):
    try:
        # Last song ke name se related mix/radio search karna
        search = Search(f"{last_song_title} song recommendation", limit=5)
        results = search.result()['result']
        if results:
            for item in results:
                if 'title' in item and item['title'] != last_song_title:
                    return {
                        "title": item['title'],
                        "link": item['link'],
                        "duration": item.get('duration', 'N/A')
                    }
    except Exception as e:
        print(f"Autoplay Error: {e}")
    return None

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_played_song
    query = " ".join(context.args)
    
    if not query:
        await update.message.reply_text("❌ Kripya gane ka naam likhein!\nExample: `/play Kesariya`", parse_mode="Markdown")
        return

    msg = await update.message.reply_text(f"🔍 Searching *{query}*...", parse_mode="Markdown")
    
    try:
        results = VideosSearch(query, limit=1).result()
        if results['result']:
            song = results['result'][0]
            last_played_song = song['title']
            
            await msg.edit_text(
                f"▶️ **Now Playing:** {song['title']}\n"
                f"⏱️ **Duration:** {song['duration']}\n\n"
                f"📻 *Autoplay Mode ON: Iske khatam hone par related songs apne aap chalenge!*",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text("❌ Song nahi mila!")
    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {e}")

# Autoplay Toggle Command
async def toggle_autoplay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global autoplay_enabled
    if context.args and context.args[0].lower() == "off":
        autoplay_enabled = False
        await update.message.reply_text("🔴 Autoplay turned OFF.")
    else:
        autoplay_enabled = True
        await update.message.reply_text("🟢 Spotify Style Autoplay is ON.")

def main():
    token = os.environ.get("BOT_TOKEN")
    
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("autoplay", toggle_autoplay))
    
    print("Agni Music Bot running with Spotify Autoplay...")
    app.run_polling()

if __name__ == "__main__":
    main()
