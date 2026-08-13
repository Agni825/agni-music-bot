import os
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yt_dlp

# --- Render Port Binding (Keep-Alive) ---
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
# ----------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 *Welcome to Agni Music!*\n\n"
        "Song search karne ke liye command use karein:\n"
        "👉 `/play <song name>` (e.g. `/play Kesariya`)",
        parse_mode="Markdown"
    )

def search_yt(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info and len(info['entries']) > 0:
            return info['entries'][0]
        return None

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("❌ Kripya gane ka naam likhein!\nExample: `/play Kesariya`", parse_mode="Markdown")
        return

    msg = await update.message.reply_text(f"🔍 Searching YouTube for *{query}*...", parse_mode="Markdown")
    
    try:
        # Run synchronous yt-dlp in executor to avoid blocking
        loop = asyncio.get_event_loop()
        song = await loop.run_in_executor(None, search_yt, query)
        
        if song:
            title = song.get('title', 'Unknown')
            link = song.get('webpage_url', '')
            duration = song.get('duration', 0)
            
            # Format duration in MM:SS
            mins = duration // 60
            secs = duration % 60
            dur_str = f"{mins}:{secs:02d}"
            
            await msg.edit_text(
                f"▶️ **Song Found!**\n\n"
                f"📌 **Title:** {title}\n"
                f"⏱️ **Duration:** {dur_str}\n"
                f"🔗 **Link:** [Click Here to Listen]({link})\n\n"
                f"🎶 *Agni Music Bot Active!*",
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
        else:
            await msg.edit_text("❌ Song nahi mila, name check karke try karein!")
    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {e}")

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("BOT_TOKEN missing!")
        return

    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    
    print("Agni Music Bot is running!")
    app.run_polling()

if __name__ == "__main__":
    main()
