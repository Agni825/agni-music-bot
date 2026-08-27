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
from pytgcalls.types import GroupCallConfig

import yt_dlp


# =========================================================
# GLOBAL CLIENTS
# =========================================================

assistant = None
voice = None


# =========================================================
# RENDER HEALTH SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(
            b"Agni Music Bot is running!"
        )

    def log_message(self, format, *args):
        pass


def run_server():

    port = int(
        os.environ.get("PORT", "10000")
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(
        f"🌐 Health server running on port {port}",
        flush=True
    )

    server.serve_forever()


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "📩 /start received",
        flush=True
    )

    await update.message.reply_text(
        "👋 Hello!\n\n"
        "🎵 Agni Music Bot is online!\n"
        "🤖 Telethon assistant is connected.\n\n"
        "Commands:\n"
        "/ping\n"
        "/join\n"
        "/play <YouTube URL>\n"
        "/leave"
    )


# =========================================================
# /PING
# =========================================================

async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "📩 /ping received",
        flush=True
    )

    await update.message.reply_text(
        "🏓 Pong!\n\n"
        "✅ Agni Music Bot is online!"
    )


# =========================================================
# /JOIN
# =========================================================

async def join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    print(
        f"🎤 /join received | CHAT ID: {chat_id}",
        flush=True
    )

    if voice is None:

        await update.message.reply_text(
            "❌ PyTgCalls is not ready."
        )

        return

    try:

        await update.message.reply_text(
            "🎤 Joining Voice Chat..."
        )

        config = GroupCallConfig(
            auto_start=False
        )

        await voice.play(
            chat_id,
            None,
            config=config
        )

        print(
            f"✅ VC JOINED SUCCESSFULLY | CHAT ID: {chat_id}",
            flush=True
        )

        await update.message.reply_text(
            "✅ Assistant joined the Voice Chat! 🎧"
        )

    except Exception as e:

        print(
            f"❌ JOIN ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        await update.message.reply_text(
            f"❌ VC join failed.\n\n"
            f"{type(e).__name__}: {e}"
        )


# =========================================================
# YOUTUBE AUDIO EXTRACTION
# =========================================================

def extract_youtube_audio(url):

    print(
        f"🔎 YouTube extraction started: {url}",
        flush=True
    )

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(
            url,
            download=False
        )

        if not info:

            raise RuntimeError(
                "YouTube information could not be extracted."
            )

        stream_url = info.get("url")

        title = info.get(
            "title",
            "Unknown song"
        )

        if not stream_url:

            raise RuntimeError(
                "No audio stream was found."
            )

        print(
            f"✅ YouTube extracted: {title}",
            flush=True
        )

        return title, stream_url


# =========================================================
# /PLAY
# =========================================================

async def play(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    print(
        f"🎵 /play received | CHAT ID: {chat_id}",
        flush=True
    )

    # -----------------------------------------------------
    # CHECK ARGUMENT
    # -----------------------------------------------------

    if not context.args:

        await update.message.reply_text(
            "🎵 Please send a YouTube URL.\n\n"
            "Example:\n"
            "/play https://www.youtube.com/watch?v=..."
        )

        print(
            "⚠️ /play received without URL",
            flush=True
        )

        return

    youtube_url = context.args[0]

    print(
        f"🔗 YouTube URL: {youtube_url}",
        flush=True
    )

    # -----------------------------------------------------
    # CHECK VC CLIENT
    # -----------------------------------------------------

    if voice is None:

        await update.message.reply_text(
            "❌ PyTgCalls is not ready."
        )

        print(
            "❌ PLAY ERROR: voice client is None",
            flush=True
        )

        return

    # -----------------------------------------------------
    # MESSAGE
    # -----------------------------------------------------

    try:

        await update.message.reply_text(
            "🔎 YouTube audio खोज रहा हूँ..."
        )

        # -------------------------------------------------
        # EXTRACT AUDIO
        # -------------------------------------------------

        title, stream_url = await asyncio.to_thread(
            extract_youtube_audio,
            youtube_url
        )

        await update.message.reply_text(
            f"🎵 Found:\n{title}\n\n"
            f"▶️ Playing..."
        )

        # -------------------------------------------------
        # PLAY AUDIO
        # -------------------------------------------------

        print(
            f"🎧 Starting playback: {title}",
            flush=True
        )

        config = GroupCallConfig(
            auto_start=False
        )

        await voice.play(
            chat_id,
            stream_url,
            config=config
        )

        print(
            f"✅ PLAYBACK STARTED: {title}",
            flush=True
        )

        await update.message.reply_text(
            "🎧 Now playing! 🔥"
        )

    except Exception as e:

        print(
            f"❌ PLAY ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        await update.message.reply_text(
            "❌ Playback failed.\n\n"
            f"{type(e).__name__}: {e}"
        )


# =========================================================
# /LEAVE
# =========================================================

async def leave(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    print(
        f"🚪 /leave received | CHAT ID: {chat_id}",
        flush=True
    )

    if voice is None:

        await update.message.reply_text(
            "❌ PyTgCalls is not ready."
        )

        return

    try:

        await voice.leave_call(
            chat_id
        )

        print(
            f"✅ LEFT VC | CHAT ID: {chat_id}",
            flush=True
        )

        await update.message.reply_text(
            "🚪 Assistant left the Voice Chat."
        )

    except Exception as e:

        print(
            f"❌ LEAVE ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        await update.message.reply_text(
            f"❌ Leave failed:\n"
            f"{type(e).__name__}: {e}"
        )


# =========================================================
# TELETHON ASSISTANT
# =========================================================

async def start_assistant():

    print(
        "🔵 TELETHON: reading environment variables...",
        flush=True
    )

    api_id = int(
        os.environ["API_ID"]
    )

    api_hash = os.environ[
        "API_HASH"
    ]

    session_string = os.environ[
        "SESSION_STRING"
    ]

    print(
        "🔵 TELETHON: creating client...",
        flush=True
    )

    assistant_client = TelegramClient(
        StringSession(session_string),
        api_id,
        api_hash
    )

    print(
        "🔵 TELETHON: connecting...",
        flush=True
    )

    await assistant_client.connect()

    if not await assistant_client.is_user_authorized():

        print(
            "❌ TELETHON: session is not authorized!",
            flush=True
        )

        await assistant_client.disconnect()

        raise RuntimeError(
            "Telethon SESSION_STRING is invalid or expired."
        )

    me = await assistant_client.get_me()

    username = (
        f"@{me.username}"
        if me.username
        else "@None"
    )

    print(
        f"✅ ASSISTANT CONNECTED: "
        f"{me.first_name} ({username})",
        flush=True
    )

    # -----------------------------------------------------
    # PYTGCALLS
    # -----------------------------------------------------

    print(
        "🔵 PYTGCALLS: creating client...",
        flush=True
    )

    voice_client = PyTgCalls(
        assistant_client
    )

    print(
        "🔵 PYTGCALLS: starting...",
        flush=True
    )

    await voice_client.start()

    print(
        "✅ PYTGCALLS CONNECTED!",
        flush=True
    )

    return (
        assistant_client,
        voice_client
    )


# =========================================================
# MAIN
# =========================================================

def main():

    global assistant
    global voice

    print(
        "🔥 AGNI MUSIC BOT STARTING...",
        flush=True
    )

    # -----------------------------------------------------
    # ENVIRONMENT VARIABLES
    # -----------------------------------------------------

    bot_token = os.environ.get(
        "BOT_TOKEN"
    )

    if not bot_token:

        print(
            "❌ BOT_TOKEN is missing!",
            flush=True
        )

        return

    if not os.environ.get("API_ID"):

        print(
            "❌ API_ID is missing!",
            flush=True
        )

        return

    if not os.environ.get("API_HASH"):

        print(
            "❌ API_HASH is missing!",
            flush=True
        )

        return

    if not os.environ.get("SESSION_STRING"):

        print(
            "❌ SESSION_STRING is missing!",
            flush=True
        )

        return

    # -----------------------------------------------------
    # HEALTH SERVER
    # -----------------------------------------------------

    Thread(
        target=run_server,
        daemon=True
    ).start()

    # -----------------------------------------------------
    # EVENT LOOP
    # -----------------------------------------------------

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    # -----------------------------------------------------
    # TELETHON + PYTGCALLS
    # -----------------------------------------------------

    try:

        assistant, voice = (
            loop.run_until_complete(
                start_assistant()
            )
        )

    except Exception as e:

        print(
            f"❌ ASSISTANT ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        return

    # -----------------------------------------------------
    # TELEGRAM BOT
    # -----------------------------------------------------

    print(
        "🔵 Creating Telegram bot...",
        flush=True
    )

    app = (
        ApplicationBuilder()
        .token(bot_token)
        .build()
    )

    # -----------------------------------------------------
    # COMMAND HANDLERS
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "ping",
            ping
        )
    )

    app.add_handler(
        CommandHandler(
            "join",
            join
        )
    )

    app.add_handler(
        CommandHandler(
            "play",
            play
        )
    )

    app.add_handler(
        CommandHandler(
            "leave",
            leave
        )
    )

    print(
        "✅ ALL COMMAND HANDLERS REGISTERED:",
        flush=True
    )

    print(
        "   /start",
        flush=True
    )

    print(
        "   /ping",
        flush=True
    )

    print(
        "   /join",
        flush=True
    )

    print(
        "   /play",
        flush=True
    )

    print(
        "   /leave",
        flush=True
    )

    # -----------------------------------------------------
    # START POLLING
    # -----------------------------------------------------

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
            "🎵 AGNI MUSIC BOT IS FULLY RUNNING!",
            flush=True
        )

        loop.run_forever()

    except KeyboardInterrupt:

        print(
            "🛑 Bot stopped.",
            flush=True
        )

    except Exception as e:

        print(
            f"❌ TELEGRAM BOT ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True
        )

    finally:

        print(
            "🔵 Shutting down...",
            flush=True
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
            "🛑 AGNI MUSIC BOT STOPPED.",
            flush=True
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()