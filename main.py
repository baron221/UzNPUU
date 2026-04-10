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
    print("🚀 Initializing University Bot...")
    db.init_db()
    
    print("📂 Loading knowledge base...")
    state.knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge"))
    state.clients = setup_ai()
    ai_responder._cached_pairs = parse_qa_pairs(state.knowledge_base)
    print(f"✅ Ready: {len(ai_responder._cached_pairs)} Q&A pairs")

# ── Web Server (FastAPI) ──────────────────────────────────────────────────────
def run_api():
    from api import app
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 API Server starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

# ── Telegram Bot ──────────────────────────────────────────────────────────────
from telegram.ext import ApplicationBuilder
from bot_logic import setup_bot_handlers

def run_bot():
    import asyncio
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
        
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN not found!")
    
    app = (ApplicationBuilder().token(token)
           .connect_timeout(30).read_timeout(30).write_timeout(30).build())
    
    state.bot_app = app  # Store the Application instance for the API
    setup_bot_handlers(app)
    
    print("✅ Telegram Bot is live!")
    app.run_polling(drop_pending_updates=True)

# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
    
    initialize()
    
    # Run API in a separate thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Run Bot in the main thread
    run_bot()