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
# JAMENDO MUSIC SEARCH
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
        f"🔎 Jamendo par "
        f"'{query}' search kar raha hoon..."
    )

    try:

        # -------------------------
        # GET JAMENDO CLIENT ID
        # -------------------------

        client_id = os.environ[
            "JAMENDO_CLIENT_ID"
        ]

        # -------------------------
        # JAMENDO SEARCH
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

        with urllib.request.urlopen(
            search_url,
            timeout=20
        ) as response:

            data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        results = data.get(
            "results",
            []
        )

        # -------------------------
        # NO RESULT
        # -------------------------

        if not results:

            await update.message.reply_text(
                "❌ Jamendo par koi track nahi mila."
            )

            return

        track = results[0]

        track_name = track.get(
            "name",
            "Unknown Track"
        )

        artist = track.get(
            "artist_name",
            "Unknown Artist"
        )

        track_id = track.get(
            "id"
        )

        if not track_id:

            raise RuntimeError(
                "Jamendo track ID missing."
            )

        await update.message.reply_text(
            f"🎵 Found:\n"
            f"**{track_name}**\n"
            f"👤 {artist}\n\n"
            f"🎧 Stream prepare ho raha hai..."
        )

        # -------------------------
        # GET STREAM URL
        # -------------------------

        stream_params = urllib.parse.urlencode({
            "client_id": client_id,
            "format": "json",
            "id": track_id,
            "action": "stream"
        })

        stream_url = (
            "https://api.jamendo.com/v3.0/"
            "tracks/file/?"
            + stream_params
        )

        print(
            "🔵 JAMENDO STREAM REQUEST"
        )

        with urllib.request.urlopen(
            stream_url,
            timeout=20
        ) as response:

            stream_data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        stream_results = stream_data.get(
            "results",
            []
        )

        if not stream_results:

            raise RuntimeError(
                "Jamendo stream unavailable."
            )

        audio_url = stream_results[0].get(
            "audio"
        )

        if not audio_url:

            raise RuntimeError(
                "Jamendo audio URL missing."
            )

        print(
            "✅ JAMENDO AUDIO URL FOUND"
        )

        # -------------------------
        # PLAY IN VOICE CHAT
        # -------------------------

        await update.message.reply_text(
            "🎙️ Audio ready!\n"
            "▶️ Voice Chat me play kar raha hoon..."
        )

        stream = MediaStream(
            audio_url,
            video_flags=MediaStream.Flags.IGNORE
        )

        await voice.play