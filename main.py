import os
import threading
import uvicorn
import logging
from dotenv import load_dotenv

# ── Shared State ──────────────────────────────────────────────────────────────
import state
import database as db
from file_loader import load_knowledge_base
from ai_responder import setup_ai, parse_qa_pairs
import ai_responder

# ── Load Env ──────────────────────────────────────────────────────────────────
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Initialize ─────────────────────────────────────────────────────────────────
def initialize():
    print("Initializing University Bot...")
    db.init_db()
    
    print("Loading knowledge base...")
    state.knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge"))
    state.clients = setup_ai()
    ai_responder._cached_pairs = parse_qa_pairs(state.knowledge_base)
    print(f"Ready: {len(ai_responder._cached_pairs)} Q&A pairs")

# ── Web Server (FastAPI) ──────────────────────────────────────────────────────
def run_api():
    from api import app
    port = int(os.environ.get("PORT", 8080))
    print(f"API Server starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

# ── Telegram Bot ──────────────────────────────────────────────────────────────
from telegram.ext import ApplicationBuilder
from bot_logic import setup_bot_handlers

def run_bot_once():
    """Start the bot polling. Raises on failure so the watchdog can retry."""
    import asyncio
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not found in environment!")

    app = (ApplicationBuilder().token(token)
           .connect_timeout(30).read_timeout(30).write_timeout(30).build())

    state.bot_app = app
    setup_bot_handlers(app)

    logging.info("✅ Telegram Bot polling started.")
    app.run_polling(drop_pending_updates=True, stop_signals=False)


def run_bot_with_restart():
    """Watchdog: keeps the bot running by restarting on any crash."""
    import time
    delay = 5  # initial retry delay in seconds
    attempt = 0
    while True:
        attempt += 1
        try:
            logging.info(f"🤖 Bot attempt #{attempt} starting...")
            run_bot_once()
            # run_polling() returned cleanly — still restart it
            logging.warning("⚠️ Bot polling exited cleanly. Restarting in 5s...")
        except Exception as e:
            logging.error(f"❌ Bot crashed (attempt #{attempt}): {e}. Restarting in {delay}s...")
            state.bot_app = None  # Clear so API doesn't use dead instance
        time.sleep(delay)
        delay = min(delay * 2, 60)  # Exponential backoff, max 60s


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

    initialize()

    # Run Bot watchdog in a separate daemon thread (auto-restarts on crash)
    logging.info("Starting Telegram Bot watchdog thread...")
    bot_thread = threading.Thread(target=run_bot_with_restart, daemon=True)
    bot_thread.start()

    # Run API in the main thread (crucial for Railway health checks)
    run_api()