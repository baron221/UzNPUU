import os
import sys
import json
import threading
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Load AI once ───────────────────────────────────────────────────────────────
print("📂 Loading knowledge base...")
from file_loader import load_knowledge_base
from ai_responder import setup_ai, get_answer, parse_qa_pairs
import ai_responder
import logger

knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge"))
clients = setup_ai()
ai_responder._cached_pairs = parse_qa_pairs(knowledge_base)
print(f"✅ Ready: {len(ai_responder._cached_pairs)} Q&A pairs")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# ── Import admin HTML ──────────────────────────────────────────────────────────
try:
    import server as srv
    ADMIN_HTML = srv.ADMIN_HTML
except:
    ADMIN_HTML = "<h1>Admin HTML not found</h1>"

# ── Web Server ─────────────────────────────────────────────────────────────────
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == '/health':
            self.send_json({"status": "ok", "pairs": len(ai_responder._cached_pairs or []), "logs": len(logger._logs)})
        elif path in ['/admin', '/admin.html']:
            self.send_html(ADMIN_HTML)
        elif path == '/api/stats':
            self.send_json(logger.get_stats())
        elif path == '/api/logs':
            self.send_json({"logs": logger.get_logs()[-50:][::-1]})
        elif path == '/api/files':
            try:
                folder = os.path.join(BASE_DIR, 'knowledge')
                files = [{"name": f, "size": round(os.path.getsize(os.path.join(folder,f))/1024,1), "ext": os.path.splitext(f)[1].lower()} for f in os.listdir(folder) if os.path.isfile(os.path.join(folder,f))]
                self.send_json({"files": files})
            except Exception as e:
                self.send_json({"files": [], "error": str(e)})
        else:
            self.send_json({"status": "running"})

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        path = self.path.split("?")[0]
        if path == '/ask':
            try:
                data = json.loads(body)
                q = data.get('question','').strip()
                if not q:
                    self.send_json({"answer": "Savol bosh!"}); return
                answer, options, lang, category = get_answer(q, knowledge_base, clients)
                if options:
                    answer += "\n\n" + "\n".join(f"• {o}" for o in options)
                self.send_json({"answer": answer})
            except Exception as e:
                self.send_json({"answer": str(e)})
        elif path == '/api/auth':
            try:
                data = json.loads(body)
                self.send_json({"ok": data.get('password') == ADMIN_PASSWORD})
            except:
                self.send_json({"ok": False})
        else:
            self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_html(self, html):
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)


def run_web():
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Web server on port {port}")
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()


# ── Telegram Bot ───────────────────────────────────────────────────────────────
import asyncio
import logging as pylogging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

pylogging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=pylogging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Nizomiy nomidagi OʻzMPU rasmiy botidasiz. Qanday yordam bera olaman? 🎓"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 Savol yozing, masalan:\n• Imtihon jadvali qachon?\n• GPA qanday hisoblanadi?\n• HEMIS parolni tiklash"
    )

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    user = update.message.from_user
    username = user.username or user.first_name or "Talaba"
    await update.message.chat.send_action("typing")
    answer, options, lang, category = get_answer(question, knowledge_base, clients)
    logger.log_message(str(user.id), username, question, answer, lang, category)
    if options:
        kb = [[InlineKeyboardButton(o, callback_data=o)] for o in options]
        await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(answer)

async def handle_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected = query.data
    user = query.from_user
    username = user.username or user.first_name or "Talaba"
    await query.message.reply_text(f"🔍 {selected}")
    answer, options, lang, category = get_answer(selected, knowledge_base, clients)
    logger.log_message(str(user.id), username, selected, answer, lang, category)
    if options:
        kb = [[InlineKeyboardButton(o, callback_data=o)] for o in options]
        await query.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await query.message.reply_text(answer)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Savolingizni yozing! 😊")


def run_bot():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN not found!")
    app = (ApplicationBuilder().token(token)
           .connect_timeout(30).read_timeout(30).write_timeout(30).build())
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(handle_btn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    print("✅ Bot is live!")
    app.run_polling(drop_pending_updates=True)


# ── Start both ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Start web server in background thread
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()

    # Run bot in main thread
    run_bot()