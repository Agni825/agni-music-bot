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
import pyrogram.errors


# =========================================================
# PYROGRAM / PYTG_CALLS COMPATIBILITY FIX
# =========================================================

if not hasattr(pyrogram.errors, "GroupcallForbidden"):
    from pyrogram.errors import BadRequest

    class GroupcallForbidden(BadRequest):
        pass

    pyrogram.errors.GroupcallForbidden = GroupcallForbidden


if not hasattr(pyrogram.errors, "GroupcallInvalid"):
    from pyrogram.errors import BadRequest

    class GroupcallInvalid(BadRequest):
        pass

    pyrogram.errors.GroupcallInvalid = GroupcallInvalid


from pytgcalls import PyTgCalls


# =========================================================
# RENDER HEALTH SERVER
# =========================================================

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

    server.serve_forever()


# =========================================================
# BASIC BOT COMMANDS
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Hello!\n\n"
        "🎵 Agni Music Bot is online!\n"
        "🤖 Assistant system is connected."
    )


async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🏓 Pong!\n\n"
        "✅ Bot is online!"
    )


# =========================================================
# ASSISTANT
# =========================================================

async def start_assistant():

    api_id = int(
        os.environ["API_ID"]
    )

    api_hash = os.environ["API_HASH"]

    session_string = os.environ[
        "SESSION_STRING"
    ]

    assistant = Client(
        "agni_assistant",
        api_id=api_id,
        api_hash=api_hash,
        session_string=session_string
    )

    await assistant.start()

    me = await assistant.get_me()

    print(
        "✅ ASSISTANT CONNECTED: "
        f"{me.first_name} "
        f"(@{me.username})"
    )

    # =====================================================
    # PYTG_CALLS
    # =====================================================

    voice = PyTgCalls(
        assistant
    )

    await voice.start()

    print(
        "✅ PYTGCALLS CONNECTED!"
    )

    return assistant, voice


# =========================================================
# MAIN
# =========================================================

def main():

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

    # =====================================================
    # RENDER HEALTH SERVER
    # =====================================================

    Thread(
        target=run_server,
        daemon=True
    ).start()

    # =====================================================
    # ASYNCIO LOOP
    # =====================================================

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(
        loop
    )

    # =====================================================
    # START ASSISTANT
    # =====================================================

    try:

        assistant, voice = (
            loop.run_until_complete(
                start_assistant()
            )
        )

    except Exception as e:

        print(
            f"❌ ASSISTANT ERROR: {e}"
        )

        return

    # =====================================================
    # TELEGRAM BOT
    # =====================================================

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
        "ASSISTANT IS RUNNING!"
    )

    # =====================================================
    # START TELEGRAM APPLICATION
    # =====================================================

    loop.run_until_complete(
        app.initialize()
    )

    loop.run_until_complete(
        app.start()
    )

    loop.run_until_complete(
        app.updater.start_polling()
    )

    try:

        loop.run_forever()

    except KeyboardInterrupt:

        pass

    finally:

        loop.run_until_complete(
            app.updater.stop()
        )

        loop.run_until_complete(
            app.stop()
        )

        loop.run_until_complete(
            app.shutdown()
        )

        loop.run_until_complete(
            assistant.stop()
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()