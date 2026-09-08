import os
import asyncio
import urllib.parse
import urllib.request
import json

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
        f"🌐 Health server running on port {port}"
    )

    server.serve_forever()


# =========================
# GLOBALS
# =========================

assistant = None
voice = None


# =========================
# /START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Hello!\n\n"
        "🎵 Agni Music Bot is online!\n"
        "🎧 Voice Chat system is ready."
    )


# =========================
# /PING
# =========================

async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🏓 Pong!\n\n"
        "✅ Agni Music Bot is online!"
    )


# =========================
# /JOIN
# =========================

async def join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
            f"✅ VC JOINED SUCCESSFULLY | "
            f"CHAT ID: {chat_id}"
        )

    except Exception as e:

        print(
            f"❌ VC JOIN ERROR: "
            f"{type(e).__name__}: {e}"
        )

        await update.message.reply_text(
            "❌ VC join failed.\n\n"
            f"{type(e).__name__}: {e}"
        )


# =========================
# /PLAY
# JAMENDO SEARCH
# =========================

async def play(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    # -------------------------
    # CHECK QUERY
    # -------------------------

    if not context.args:

        await update.message.reply_text(
            "🎵 Song name likhiye.\n\n"
            "Example:\n"
            "/play chill music"
        )

        return

    query = " ".join(
        context.args
    ).strip()

    await update.message.reply_text(
        f"🔎 Jamendo par '{query}' "
        f"search kar raha hoon..."
    )

    try:

        # -------------------------
        # JAMENDO CLIENT ID
        # -------------------------

        client_id = os.environ[
            "JAMENDO_CLIENT_ID"
        ]

        # -------------------------
        # SEARCH JAMENDO
        # -------------------------

        params = urllib.parse.urlencode({
            "client_id": client_id,
            "format": "json",
            "limit": 1,
            "namesearch": query,
            "audioformat": "mp32"
        })

        search_url = (
            "https://api.jamendo.com/v3.0/tracks/"
            "?" + params
        )

        print(
            f"🔎 JAMENDO SEARCH: {query}"
        )

        # -------------------------
        # REQUEST
        # -------------------------

        with urllib.request.urlopen(
            search_url,
            timeout=20
        ) as response:

            data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        # -------------------------
        # RESULTS
        # -------------------------

        results = data.get(
            "results",
            []
        )

        if not results:

            await update.message.reply_text(
                "❌ Jamendo par koi track nahi mila."
            )

            return

        track = results[0]

        # -------------------------
        # TRACK INFORMATION
        # -------------------------

        track_name = track.get(
            "name",
            "Unknown Track"
        )

        artist = track.get(
            "artist_name",
            "Unknown Artist"
        )

        audio_url = track.get(
            "audio"
        )

        # -------------------------
        # CHECK AUDIO URL
        # -------------------------

        if not audio_url:

            raise RuntimeError(
                "Jamendo audio URL nahi mila."
            )

        print(
            f"✅ TRACK FOUND: "
            f"{track_name} - {artist}"
        )

        print(
            "✅ JAMENDO AUDIO URL FOUND"
        )

        await update.message.reply_text(
            f"🎵 **Found!**\n\n"
            f"🎶 {track_name}\n"
            f"👤 {artist}\n\n"
            f"🎧 Voice Chat me play kar raha hoon..."
        )

        # -------------------------
        # CREATE MEDIA STREAM
        # -------------------------

        stream = MediaStream(
            audio_url,
            video_flags=MediaStream.Flags.IGNORE
        )

        # -------------------------
        # PLAY IN VC
        # -------------------------

        await voice.play(
            chat_id,
            stream
        )

        print(
            f"✅ PLAYBACK STARTED | "
            f"{track_name} - {artist}"
        )

        await update.message.reply_text(
            f"▶️ **Now Playing** 🎵\n\n"
            f"🎶 {track_name}\n"
            f"👤 {artist}"
        )

    except Exception as e:

        print(
            f"❌ JAMENDO PLAY ERROR: "
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
            "Telethon SESSION_STRING "
            "is invalid or expired."
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

    voice = PyTgCalls(
        assistant
    )

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

    # -------------------------
    # ENVIRONMENT VARIABLES
    # -------------------------

    bot_token = os.environ.get(
        "BOT_TOKEN"
    )

    if not bot_token:

        print(
            "❌ BOT_TOKEN is missing!"
        )

        return

    if not os.environ.get("API_ID"):

        print(
            "❌ API_ID is missing!"
        )

        return

    if not os.environ.get("API_HASH"):

        print(
            "❌ API_HASH is missing!"
        )

        return

    if not os.environ.get(
        "SESSION_STRING"
    ):

        print(
            "❌ SESSION_STRING is missing!"
        )

        return

    if not os.environ.get(
        "JAMENDO_CLIENT_ID"
    ):

        print(
            "❌ JAMENDO_CLIENT_ID is missing!"
        )

        return

    # -------------------------
    # HEALTH SERVER
    # -------------------------

    Thread(
        target=run_server,
        daemon=True
    ).start()

    # -------------------------
    # ASYNCIO LOOP
    # -------------------------

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    # -------------------------
    # START ASSISTANT
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

    # -------------------------
    # COMMAND HANDLERS
    # -------------------------

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

    print(
        "✅ AGNI MUSIC BOT + "
        "TELETHON ASSISTANT + "
        "PYTGCALLS + "
        "JAMENDO READY!"
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
            "🎵 AGNI MUSIC BOT "
            "IS FULLY RUNNING!"
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