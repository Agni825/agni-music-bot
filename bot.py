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

    print(
        f"🌐 Health server running on port {port}",
        flush=True
    )

    server.serve_forever()


# =========================
# TELEGRAM BOT COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Hello!\n\n"
        "🎵 Agni Music Bot is online!\n"
        "🤖 Telethon assistant system is connected."
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🏓 Pong!\n\n"
        "✅ Bot is online!"
    )


# =========================
# TELETHON ASSISTANT
# =========================

async def start_assistant():

    print(
        "🔵 TELETHON: reading environment variables...",
        flush=True
    )

    api_id = int(os.environ["API_ID"])
    api_hash = os.environ["API_HASH"]
    session_string = os.environ["SESSION_STRING"]

    print(
        "🔵 TELETHON: creating client...",
        flush=True
    )

    assistant = TelegramClient(
        StringSession(session_string),
        api_id,
        api_hash
    )

    print(
        "🔵 TELETHON: connecting...",
        flush=True
    )

    await assistant.connect()

    if not await assistant.is_user_authorized():

        print(
            "❌ TELETHON: session is not authorized!",
            flush=True
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

    voice = PyTgCalls(assistant)

    print(
        "🔵 PYTGCALLS: starting...",
        flush=True
    )

    await voice.start()

    print(
        "✅ PYTGCALLS CONNECTED!",
        flush=True
    )

    return assistant, voice


# =========================
# MAIN
# =========================

def main():

    # IMPORTANT DIAGNOSTIC LINE
    print(
        "🔥 AGNI TEST: bot.py STARTED!",
        flush=True
    )

    bot_token = os.environ.get("BOT_TOKEN")

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
    # TELETHON ASSISTANT
    # =========================

    try:

        assistant, voice = loop.run_until_complete(
            start_assistant()
        )

    except Exception as e:

        print(
            f"❌ ASSISTANT ERROR: {e}",
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
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("ping", ping)
    )

    print(
        "✅ AGNI MUSIC BOT + "
        "TELETHON ASSISTANT + PYTGCALLS READY!",
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
            f"❌ TELEGRAM BOT ERROR: {e}",
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