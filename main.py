"""
main.py — Runs both the Telegram bot and web server together
in the same process so they share the same logs/ folder.
"""
import threading
import os
from dotenv import load_dotenv

load_dotenv()

# Start web server in background thread
def run_server():
    import server
    from http.server import HTTPServer
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Web server starting on port {port}")
    HTTPServer(('0.0.0.0', port), server.Handler).serve_forever()

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# Run Telegram bot in main thread
print("🤖 Starting Telegram bot...")
import bot
bot.main()
