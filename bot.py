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

from pyrogram import Client
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

    print(f"🌐 HEALTH SERVER STARTED ON PORT {port}")

    server.serve_forever()


# =========================
# BASIC BOT COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Hello!\n\n"
        "🎵 Agni Music Bot is online!\n"
        "🤖 Assistant system is starting."
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🏓 Pong!\n\n"
        "✅ Bot is online!"
    )


# =========================
# ASSISTANT + PYTGCALLS
# =========================

async def start_assistant():

    print("🔵 ASSISTANT: reading environment variables...")

    api_id = int(os.environ["API_ID"])
    api_hash = os.environ["API_HASH"]
    session_string = os.environ["SESSION_STRING"]

    print("🔵 ASSISTANT: environment variables loaded.")

    print("🔵 ASSISTANT: creating Pyrogram client...")

    assistant = Client(
        "agni_assistant",
        api_id=api_id,
        api_hash=api_hash,
        session_string=session_string
    )

    print("🔵 ASSISTANT: starting Pyrogram...")

    try:

        await asyncio.wait_for(
            assistant.start(),
            timeout=30
        )

    except asyncio.TimeoutError:

        print(
            "❌ ASSISTANT ERROR: "
            "assistant.start() timed out after 30 seconds"
        )

        raise

    except Exception as e:

        print(
            f"❌ ASSISTANT ERROR during "
            f"assistant.start(): {e}"
        )

        raise

    print("🟢 ASSISTANT: Pyrogram started!")

    print("🔵 ASSISTANT: checking account...")

    try:

        me = await asyncio.wait_for(
            assistant.get_me(),
            timeout=15
        )

    except Exception as e:

        print(
            f"❌ ASSISTANT ERROR during "
            f"get_me(): {e}"
        )

        raise

    username = (
        f"@{me.username}"
        if me.username
        else "@None"
    )

    print(
        f"✅ ASSISTANT CONNECTED: "
        f"{me.first_name} ({username})"
    )

    # =========================
    # PYTGCALLS
    # =========================

    print("🔵 PYTGCALLS: creating client...")

    try:

        voice = PyTgCalls(assistant)

        print("🔵 PYTGCALLS: starting...")

        await asyncio.wait_for(
            voice.start(),
            timeout=30
        )

        print("✅ PYTGCALLS CONNECTED!")

    except asyncio.TimeoutError:

        print(
            "❌ PYTGCALLS ERROR: "
            "voice.start() timed out after 30 seconds"
        )

        raise

    except Exception as e:

        print(
            f"❌ PYTGCALLS ERROR: {e}"
        )

        raise

    return assistant, voice


# =========================
# MAIN
# =========================

def main():

    print("🚀 AGNI MUSIC BOT STARTING...")

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

    # =========================
    # HEALTH SERVER
    # =========================

    print("🔵 Starting Render health server...")

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
    # START ASSISTANT
    # =========================

    try:

        print("🔵 Starting assistant system...")

        assistant, voice = loop.run_until_complete(
            start_assistant()
        )

    except Exception as e:

        print(
            f"❌ ASSISTANT SYSTEM FAILED: {e}"
        )

        return

    # =========================
    # TELEGRAM BOT
    # =========================

    print("🔵 Creating Telegram bot...")

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

    print(
        "✅ AGNI MUSIC BOT + "
        "ASSISTANT + PYTGCALLS READY!"
    )

    # =========================
    # START TELEGRAM BOT
    # =========================

    try:

        print("🔵 Initializing Telegram bot...")

        loop.run_until_complete(
            app.initialize()
        )

        print("🔵 Starting Telegram bot...")

        loop.run_until_complete(
            app.start()
        )

        print("🔵 Starting polling...")

        loop.run_until_complete(
            app.updater.start_polling()
        )

        print(
            "🎵 AGNI MUSIC BOT IS FULLY RUNNING! 🎵"
        )

        loop.run_forever()

    except KeyboardInterrupt:

        print("🛑 Bot stopped manually.")

    except Exception as e:

        print(
            f"❌ TELEGRAM BOT ERROR: {e}"
        )

    finally:

        print("🔵 Shutting down...")

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
                assistant.stop()
            )

        except Exception:
            pass

        print("🛑 AGNI MUSIC BOT STOPPED.")


# =========================
# RUN
# =========================

if __name__ == "__main__":

    main()