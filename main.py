import sys
# Patch sqlite3 with pysqlite3 for ChromaDB on systems with older sqlite3 version (like Oracle Linux 9)
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import threading
import uvicorn
import logging
import time
from dotenv import load_dotenv

# ── Shared State ──────────────────────────────────────────────────────────────
import state
import database as db
from file_loader import load_knowledge_base
from ai_responder import setup_ai, parse_qa_pairs
import ai_responder
import vector_store

# ── Load Env ──────────────────────────────────────────────────────────────────
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Bot Health Tracking ───────────────────────────────────────────────────────
bot_status = {
    "attempts": 0,
    "last_start": None,
    "last_error": None,
    "running": False,
}

# ── Initialize ────────────────────────────────────────────────────────────────
def initialize():
    print("Initializing University Bot...")
    db.init_db()

    # Ensure data/knowledge directory exists for user uploads
    data_kb = os.path.join(BASE_DIR, "data", "knowledge")
    os.makedirs(data_kb, exist_ok=True)

    print("Loading knowledge base...")
    state.knowledge_base = load_knowledge_base(data_kb)
    state.clients = setup_ai()
    ai_responder._cached_pairs = parse_qa_pairs(state.knowledge_base)
    
    # Vector DB Indexing
    print("Indexing Vector DB (ChromaDB)...")
    vector_store.clear_vector_db()
    vector_store.add_to_vector_db(ai_responder._cached_pairs)
    
    print(f"Ready: {len(ai_responder._cached_pairs)} Q&A pairs indexed.")

# ── Web Server (FastAPI) ──────────────────────────────────────────────────────
def run_api():
    from api import app
    port = int(os.environ.get("PORT", 8080))
    print(f"API Server starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

# ── Telegram Bot ──────────────────────────────────────────────────────────────
from telegram.ext import ApplicationBuilder
from bot_logic import setup_bot_handlers


def delete_webhook(token: str):
    """
    Delete any existing Telegram webhook before starting polling.
    CRITICAL: If a webhook is active, Telegram sends all updates there
    and getUpdates (polling) receives NOTHING — bot appears completely silent.
    """
    import urllib.request
    import json
    try:
        url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        with urllib.request.urlopen(url, timeout=10) as r:
            result = json.loads(r.read())
            if result.get("result"):
                logging.info("✅ Webhook deleted (or was not set). Polling is clear.")
            else:
                logging.warning(f"⚠️ deleteWebhook response: {result}")
    except Exception as e:
        logging.error(f"❌ Failed to delete webhook: {e}")


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

    # CRITICAL: delete webhook before polling so Telegram sends updates here
    delete_webhook(token)

    app = (ApplicationBuilder().token(token)
           .connect_timeout(30).read_timeout(30).write_timeout(30).build())

    state.bot_app = app
    setup_bot_handlers(app)

    bot_status["running"] = True
    bot_status["last_start"] = time.strftime("%Y-%m-%d %H:%M:%S")
    bot_status["last_error"] = None
    logging.info("✅ Telegram Bot polling started.")
    app.run_polling(drop_pending_updates=True, stop_signals=False)


def run_bot_with_restart():
    """Watchdog: keeps the bot running by restarting on any crash."""
    delay = 5  # initial retry delay in seconds
    while True:
        bot_status["attempts"] += 1
        bot_status["running"] = False
        try:
            logging.info(f"🤖 Bot attempt #{bot_status['attempts']} starting...")
            run_bot_once()
            # run_polling() returned cleanly — reset delay and restart
            logging.warning("⚠️ Bot polling exited cleanly. Restarting in 5s...")
            delay = 5  # reset backoff after clean exit
        except Exception as e:
            err = str(e)
            bot_status["last_error"] = err
            bot_status["running"] = False
            state.bot_app = None  # Clear so API doesn't send through dead instance
            logging.error(
                f"❌ Bot crashed (attempt #{bot_status['attempts']}): {err}. "
                f"Restarting in {delay}s..."
            )
        time.sleep(delay)
        delay = min(delay * 2, 60)  # Exponential backoff, max 60s


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    initialize()

    # Run Bot watchdog in a separate daemon thread (auto-restarts on crash)
    logging.info("Starting Telegram Bot watchdog thread...")
    bot_thread = threading.Thread(target=run_bot_with_restart, daemon=True)
    bot_thread.start()

    # Run API in the main thread (crucial for Railway health checks)
    run_api()