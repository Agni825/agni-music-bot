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
from pytgcalls import filters
from pytgcalls.types import Update as PyTgCallsUpdate


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

# Each chat has its own queue
queues = {}

# Current song in each chat
current_tracks = {}

# Prevent multiple auto-next operations
playing_next = set()


# =========================
# QUEUE HELPERS
# =========================

def get_queue(chat_id):

    if chat_id not in queues:
        queues[chat_id] = []

    return queues[chat_id]


def add_to_queue(chat_id, track):

    queue = get_queue(chat_id)

    queue.append(track)


def remove_next_from_queue(chat_id):

    queue = get_queue(chat_id)

    if not queue:
        return None

    return queue.pop(0)


# =========================
# SEARCH JAMENDO
# =========================

async def search_jamendo(query):

    client_id = os.environ[
        "JAMENDO_CLIENT_ID"
    ]

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

    # urllib is blocking, so run it in a thread
    def request():

        with urllib.request.urlopen(
            search_url,
            timeout=20
        ) as response:

            return json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    data = await asyncio.to_thread(
        request
    )

    results = data.get(
        "results",
        []
    )

    if not results:
        return None

    track = results[0]

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

    if not audio_url:
        return None

    return {
        "name": track_name,
        "artist": artist,
        "audio": audio_url,
    }


# =========================
# PLAY TRACK
# =========================

async def play_track(chat_id, track):

    global current_tracks

    audio_url = track.get(
        "audio"
    )

    if not audio_url:
        raise RuntimeError(
            "Audio URL nahi mila."
        )

    stream = MediaStream(
        audio_url,
        video_flags=MediaStream.Flags.IGNORE
    )

    await voice.play(
        chat_id,
        stream
    )

    current_tracks[chat_id] = track

    print(
        f"▶️ PLAYING | "
        f"{track['name']} - "
        f"{track['artist']}"
    )


# =========================
# AUTO NEXT
# =========================

async def play_next(chat_id):

    if chat_id in playing_next:
        return

    playing_next.add(chat_id)

    try:

        next_track = remove_next_from_queue(
            chat_id
        )

        if next_track is None:

            current_tracks.pop(
                chat_id,
                None
            )

            print(
                f"⏹️ QUEUE EMPTY | "
                f"CHAT ID: {chat_id}"
            )

            return

        await play_track(
            chat_id,
            next_track
        )

        print(
            f"⏭️ AUTO NEXT | "
            f"{next_track['name']}"
        )

    except Exception as e:

        print(
            f"❌ AUTO NEXT ERROR: "
            f"{type(e).__name__}: {e}"
        )

    finally:

        playing_next.discard(
            chat_id
        )


# =========================
# PYTGCALLS STREAM END
# ====================== 

# =========================
# STREAM END HANDLER
# =========================

async def stream_end_handler(client, update):

    try:
        chat_id = update.chat_id

        print(
            f"🔔 STREAM ENDED | CHAT ID: {chat_id}"
        )

        await play_next(chat_id)

    except Exception as e:

        print(
            f"❌ STREAM END ERROR: "
            f"{type(e).__name__}: {e}"
        )

    try:

        chat_id = update.chat_id

        print(
            f"🔔 STREAM ENDED | "
            f"CHAT ID: {chat_id}"
        )

        await play_next(
            chat_id
        )

    except Exception as e:

        print(
            f"❌ STREAM END ERROR: "
            f"{type(e).__name__}: {e}"
        )


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

        await voice.play(
            chat_id
        )

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
# =========================

async def play(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

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
        f"🔎 '{query}' search kar raha hoon..."
    )

    try:

        track = await search_jamendo(
            query
        )

        if not track:

            await update.message.reply_text(
                "❌ Koi matching track nahi mila."
            )

            return

        print(
            f"✅ TRACK FOUND: "
            f"{track['name']} - "
            f"{track['artist']}"
        )

        # =====================
        # CHECK CURRENT SONG
        # =====================

        if chat_id in current_tracks:

            add_to_queue(
                chat_id,
                track
            )

            position = len(
                get_queue(chat_id)
            )

            await update.message.reply_text(
                f"➕ **Added to Queue**\n\n"
                f"🎶 {track['name']}\n"
                f"👤 {track['artist']}\n\n"
                f"📋 Queue position: {position}"
            )

            print(
                f"➕ QUEUED | "
                f"{track['name']} | "
                f"POSITION: {position}"
            )

            return

        # =====================
        # NOTHING PLAYING
        # =====================

        await play_track(
            chat_id,
            track
        )

        await update.message.reply_text(
            f"▶️ **Now Playing** 🎵\n\n"
            f"🎶 {track['name']}\n"
            f"👤 {track['artist']}"
        )

    except Exception as e:

        print(
            f"❌ PLAY ERROR: "
            f"{type(e).__name__}: {e}"
        )

        await update.message.reply_text(
            "❌ Playback failed.\n\n"
            f"{type(e).__name__}: {e}"
        )


# =========================
# /SKIP
# =========================

async def skip(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    if chat_id not in current_tracks:

        await update.message.reply_text(
            "❌ Abhi koi song nahi chal raha."
        )

        return

    try:

        queue = get_queue(chat_id)

        # Remove current song from tracking
        current_tracks.pop(
            chat_id,
            None
        )

        # If queue is empty
        if not queue:

            await update.message.reply_text(
                "⏭️ Current song skipped.\n\n"
                "📭 Queue empty hai."
            )

            print(
                f"⏭️ SKIPPED | "
                f"QUEUE EMPTY | "
                f"CHAT ID: {chat_id}"
            )

            return

        # Get next song
        next_track = remove_next_from_queue(
            chat_id
        )

        # Play next song
        await play_track(
            chat_id,
            next_track
        )

        await update.message.reply_text(
            f"⏭️ Skipped!\n\n"
            f"▶️ Now Playing:\n"
            f"🎶 {next_track['name']}\n"
            f"👤 {next_track['artist']}"
        )

    except Exception as e:

        print(
            f"❌ SKIP ERROR: "
            f"{type(e).__name__}: {e}"
        )

        await update.message.reply_text(
            "❌ Skip failed.\n\n"
            f"{type(e).__name__}: {e}"
        )


# =========================
# /QUEUE
# =========================

async def queue_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    queue = get_queue(
        chat_id
    )

    current = current_tracks.get(
        chat_id
    )

    if not current and not queue:

        await update.message.reply_text(
            "📭 Queue empty hai."
        )

        return

    text = "🎵 **Agni Music Queue**\n\n"

    if current:

        text += (
            "▶️ **Now Playing**\n"
            f"🎶 {current['name']}\n"
            f"👤 {current['artist']}\n\n"
        )

    if queue:

        text += "📋 **Up Next:**\n"

        for index, track in enumerate(
            queue,
            start=1
        ):

            text += (
                f"{index}. "
                f"{track['name']} — "
                f"{track['artist']}\n"
            )

    else:

        text += "📭 **Up Next:** Empty"

    await update.message.reply_text(
        text
    )


# =========================
# /CLEAR
# =========================

async def clear_queue(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    queue = get_queue(
        chat_id
    )

    queue.clear()

    await update.message.reply_text(
        "🗑️ Queue clear kar di gayi."
    )

    print(
        f"🗑️ QUEUE CLEARED | "
        f"CHAT ID: {chat_id}"
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

await voice.start()

# STREAM END HANDLER REGISTER
voice.on_update(
    filters.stream_end()
)(
    stream_end_handler
)

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

    # =========================
    # ENVIRONMENT VARIABLES
    # =========================

    bot_token = os.environ.get(
        "BOT_TOKEN"
    )

    if not bot_token:

        print(
            "❌ BOT_TOKEN is missing!"
        )

        return

    if not os.environ.get(
        "API_ID"
    ):

        print(
            "❌ API_ID is missing!"
        )

        return

    if not os.environ.get(
        "API_HASH"
    ):

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

    # =========================
    # HEALTH SERVER
    # =========================

    Thread(
        target=run_server,
        daemon=True
    ).start()

    # =========================
    # ASYNCIO LOOP
    # =========================

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(
        loop
    )

    # =========================
    # START ASSISTANT
    # =========================

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

    # =========================
    # TELEGRAM BOT
    # =========================

    print(
        "🔵 Creating Telegram bot..."
    )

    app = (
        ApplicationBuilder()
        .token(bot_token)
        .build()
    )

    # =========================
    # COMMAND HANDLERS
    # =========================

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
            "skip",
            skip
        )
    )

    app.add_handler(
        CommandHandler(
            "queue",
            queue_command
        )
    )

    app.add_handler(
        CommandHandler(
            "clear",
            clear_queue
        )
    )

    print(
        "✅ AGNI MUSIC BOT + "
        "QUEUE + "
        "SKIP + "
        "AUTO NEXT + "
        "PYTGCALLS + "
        "JAMENDO READY!"
    )

    # =========================
    # START BOT
    # =========================

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