import os
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from telethon import TelegramClient
from telethon.sessions import StringSession

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream


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

    print(f"🌐 Health server running on port {port}")

    server.serve_forever()


# =========================
# GLOBALS
# =========================

assistant = None
voice = None


# =========================
# /START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Hello!\n\n"
        "🎵 Agni Music Bot is online!\n"
        "🎧 Voice Chat system is ready."
    )


# =========================
# /PING
# =========================

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🏓 Pong!\n\n"
        "✅ Agni Music Bot is online!"
    )


# =========================
# /JOIN
# =========================

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "🎙️ Joining Voice Chat..."
    )

    try:

        await voice.play(chat_id)

        await update.message.reply_text(
            "✅ Assistant joined the Voice Chat! 🎧\n\n"
            "🎵 Agni Music is ready."
        )

        print(
            f"✅ VC JOINED SUCCESSFULLY | CHAT ID: {chat_id}"
        )

    except Exception as e:

        print(
            f"❌ VC JOIN ERROR: {type(e).__name__}: {e}"
        )

        await update.message.reply_text(
            f"❌ VC join failed.\n\n"
            f"{type(e).__name__}: {e}"
        )


# =========================
# /PLAY
# =========================

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    if not context.args:

        await update.message.reply_text(
            "🎵 Please give a direct audio URL.\n\n"
            "Example:\n"
            "/play https://example.com/song.mp3"
        )

        return

    url = context.args[0].strip()

    # -------------------------
    # Block YouTube for now
    # -------------------------

    youtube_domains = (
        "youtube.com",
        "youtu.be",
        "music.youtube.com"
    )

    if any(domain in url.lower() for domain in youtube_domains):

        await update.message.reply_text(
            "❌ YouTube playback फिलहाल disabled है.\n\n"
            "🎧 अभी direct audio stream URL इस्तेमाल करें."
        )

        return

    # -------------------------
    # Basic URL check
    # -------------------------

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):

        await update.message.reply_text(
            "❌ यह valid audio URL नहीं लग रहा.\n\n"
            "Example:\n"
            "/play https://example.com/song.mp3"
        )

        return

    await update.message.reply_text(
        "🎵 Audio stream मिल गया...\n"
        "🎧 Voice Chat में play करने की कोशिश कर रहा हूँ..."
    )

    try:

        stream = MediaStream(
            url,
            video_flags=MediaStream.Flags.IGNORE
        )

        await voice.play(
            chat_id,
            stream
        )

        await update.message.reply_text(
            "▶️ Playback started! 🎵🎧"
        )

        print(
            f"▶️ PLAYBACK STARTED | CHAT ID: {chat_id}"
        )

        print(
            f"🔊 SOURCE: {url}"
        )

    except Exception as e:

        print(
            f"❌ PLAYBACK ERROR: "
            f"{type(e).__name__}: {e}"
        )

        await update.message.reply_text(
            "❌ Playback failed.\n\n"
            f"{type(e).__name__}: {e}"
        )


# =========================
# TELETHON + PYTGCALLS
# =========================

async def start_assistant():

    global assistant
    global voice

    print(
        "🔵 TELETHON: reading environment variables..."
    )

    api_id = int(os.environ["API_ID"])
    api_hash = os.environ["API_HASH"]
    session_string = os.environ["SESSION_STRING"]

    print(
        "🔵 TELETHON: creating client..."
    )

    assistant = TelegramClient(
        StringSession(session_string),
        api_id,
        api_hash
    )

    print(
        "🔵 TELETHON: connecting..."
    )

    await assistant.connect()

    if not await assistant.is_user_authorized():

        print(
            "❌ TELETHON: session is not authorized!"
        )

        await assistant.disconnect()

        raise RuntimeError(
            "Telethon SESSION_STRING is invalid or expired."
        )

    me = await assistant.get_me()

    username = (
        f"@{me.username}"
        if me.username
        else "@None"
    )

    print(
        f"✅ ASSISTANT CONNECTED: "
        f"{me.first_name} ({username})"
    )

    # -------------------------
    # PYTGCALLS
    # -------------------------

    print(
        "🔵 PYTGCALLS: creating client..."
    )

    voice = PyTgCalls(assistant)

    print(
        "🔵 PYTGCALLS: starting..."
    )

    await voice.start()

    print(
        "✅ PYTGCALLS CONNECTED!"
    )

    return assistant, voice


# =========================
# MAIN
# =========================

def main():

    print(
        "🚀 AGNI MUSIC BOT STARTING..."
    )

    bot_token = os.environ.get("BOT_TOKEN")

    if not bot_token:
        print("❌ BOT_TOKEN is missing!")
        return

    if not os.environ.get("API_ID"):
        print("❌ API_ID is missing!")
        return

    if not os.environ.get("API_HASH"):
        print("❌ API_HASH is missing!")
        return

    if not os.environ.get("SESSION_STRING"):
        print("❌ SESSION_STRING is missing!")
        return

    # -------------------------
    # HEALTH SERVER
    # -------------------------

    Thread(
        target=run_server,
        daemon=True
    ).start()

    # -------------------------
    # ASYNCIO
    # -------------------------

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    # -------------------------
    # ASSISTANT
    # -------------------------

    try:

        loop.run_until_complete(
            start_assistant()
        )

    except Exception as e:

        print(
            f"❌ ASSISTANT ERROR: "
            f"{type(e).__name__}: {e}"
        )

        return

    # -------------------------
    # TELEGRAM BOT
    # -------------------------

    print(
        "🔵 Creating Telegram bot..."
    )

    app = (
        ApplicationBuilder()
        .token(bot_token)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("ping", ping)
    )

    app.add_handler(
        CommandHandler("join", join)
    )

    app.add_handler(
        CommandHandler("play", play)
    )

    print(
        "✅ AGNI MUSIC BOT + "
        "TELETHON ASSISTANT + PYTGCALLS READY!"
    )

    # -------------------------
    # START BOT
    # -------------------------

    try:

        loop.run_until_complete(
            app.initialize()
        )

        loop.run_until_complete(
            app.start()
        )

        loop.run_until_complete(
            app.updater.start_polling()
        )

        print(
            "🎵 AGNI MUSIC BOT IS FULLY RUNNING!"
        )

        loop.run_forever()

    except Exception as e:

        print(
            f"❌ TELEGRAM BOT ERROR: "
            f"{type(e).__name__}: {e}"
        )

    finally:

        print(
            "🔵 Shutting down..."
        )

        try:

            loop.run_until_complete(
                app.updater.stop()
            )

        except Exception:
            pass

        try:

            loop.run_until_complete(
                app.stop()
            )

        except Exception:
            pass

        try:

            loop.run_until_complete(
                app.shutdown()
            )

        except Exception:
            pass

        try:

            if assistant:
                loop.run_until_complete(
                    assistant.disconnect()
                )

        except Exception:
            pass

        print(
            "🛑 AGNI MUSIC BOT STOPPED."
        )


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()