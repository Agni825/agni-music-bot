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


# =========================
# GLOBAL CLIENTS
# =========================

assistant = None
voice = None


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
        f"🌐 Health server running on port {port}",
        flush=True
    )

    server.serve_forever()


# =========================
# TELEGRAM BOT COMMANDS
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Hello!\n\n"
        "🎵 Agni Music Bot is online!\n"
        "🤖 Telethon assistant system is connected."
    )


async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🏓 Pong!\n\n"
        "✅ Bot is online!"
    )


# =========================
# ACTUAL VC JOIN
# =========================

async def join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    print(
        f"🎤 JOIN COMMAND RECEIVED | CHAT ID: {chat_id}",
        flush=True
    )

    if voice is None:

        await update.message.reply_text(
            "❌ PyTgCalls is not ready."
        )

        print(
            "❌ JOIN ERROR: voice client is None",
            flush=True
        )

        return

    await update.message.reply_text(
        "🎤 Joining the active VC..."
    )

    try:

        # Do NOT create a new voice chat.
        # Join the already-active VC.
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
            "✅ Assistant joined the Voice Chat! 🎤\n\n"
            "🎵 Agni Music is ready."
        )

    except Exception as e:

        print(
            f"❌ VC JOIN ERROR: {type(e).__name__}: {e}",
            flush=True
        )

        await update.message.reply_text(
            "❌ VC join failed.\n\n"
            f"Error: {type(e).__name__}: {e}"
        )


# =========================
# LEAVE VC
# =========================

async def leave(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    print(
        f"🚪 LEAVE COMMAND RECEIVED | CHAT ID: {chat_id}",
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
            f"❌ VC LEAVE ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        await update.message.reply_text(
            "❌ Leave failed.\n\n"
            f"Error: {type(e).__name__}: {e}"
        )


# =========================
# TELETHON ASSISTANT
# =========================

async def start_assistant():

    print(
        "🔵 TELETHON: reading environment variables...",
        flush=True
    )

    api_id = int(
        os.environ["API_ID"]
    )

    api_hash = os.environ["API_HASH"]

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

    # =========================
    # PYTGCALLS
    # =========================

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


# =========================
# MAIN
# =========================

def main():

    global assistant
    global voice

    print(
        "🔥 AGNI TEST: bot.py STARTED!",
        flush=True
    )

    # =========================
    # ENVIRONMENT VARIABLES
    # =========================

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

    asyncio.set_event_loop(loop)

    # =========================
    # TELETHON + PYTGCALLS
    # =========================

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

    # =========================
    # TELEGRAM BOT
    # =========================

    print(
        "🔵 Creating Telegram bot...",
        flush=True
    )

    app = (
        ApplicationBuilder()
        .token(bot_token)
        .build()
    )

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
            "leave",
            leave
        )
    )

    print(
        "✅ AGNI MUSIC BOT + "
        "TELETHON ASSISTANT + "
        "PYTGCALLS READY!",
        flush=True
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


# =========================
# RUN
# =========================

if __name__ == "__main__":

    main()