"""
main.py — Runs bot + server in same process so they share memory.
This means logs written by bot are instantly visible in server's admin dashboard.
"""
import os
import sys
import threading
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── Pre-load shared modules ────────────────────────────────────────────────────
print("📂 Loading knowledge base...")
from file_loader import load_knowledge_base
from ai_responder import setup_ai, get_answer, parse_qa_pairs
import ai_responder
import logger  # shared between bot and server

knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge"))
clients = setup_ai()
ai_responder._cached_pairs = parse_qa_pairs(knowledge_base)
print(f"✅ Knowledge loaded: {len(ai_responder._cached_pairs)} Q&A pairs")

# ── Start web server in background thread ─────────────────────────────────────
def run_server():
    import json
    from http.server import HTTPServer, BaseHTTPRequestHandler

    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
    PORT = int(os.environ.get("PORT", 8080))

    # Import admin HTML from server.py
    import server as srv

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == '/health':
                self.send_json({"status": "ok", "pairs": len(ai_responder._cached_pairs or []), "logs": len(logger._logs)})
            elif path in ['/admin', '/admin.html']:
                self.send_html(srv.ADMIN_HTML)
            elif path == '/api/stats':
                self.send_json(logger.get_stats())
            elif path == '/api/logs':
                self.send_json({"logs": logger.get_logs()[-50:][::-1]})
            elif path == '/api/files':
                self.handle_list_files()
            else:
                self.send_json({"status": "running", "message": "OʻzMPU Bot API"})

        def do_POST(self):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            path = self.path.split("?")[0]
            if path == '/ask':
                self.handle_ask(body)
            elif path == '/api/auth':
                try:
                    data = json.loads(body)
                    self.send_json({"ok": data.get('password') == ADMIN_PASSWORD})
                except:
                    self.send_json({"ok": False})
            elif path == '/api/delete':
                self.handle_delete(body)
            elif path == '/api/upload':
                self.handle_upload(length, body)
            else:
                self.send_response(404); self.end_headers()

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

        def handle_ask(self, body):
            try:
                data = json.loads(body)
                question = data.get('question', '').strip()
                if not question:
                    self.send_json({"answer": "Savol bo'sh!"}); return
                answer, options, lang, category = get_answer(question, knowledge_base, clients)
                if options:
                    answer = answer + "\n\n" + "\n".join(f"• {o}" for o in options)
                self.send_json({"answer": answer})
            except Exception as e:
                self.send_json({"answer": f"Xatolik: {str(e)}"})

        def handle_list_files(self):
            try:
                folder = os.path.join(BASE_DIR, 'knowledge')
                files = []
                for f in os.listdir(folder):
                    fp = os.path.join(folder, f)
                    if os.path.isfile(fp):
                        files.append({"name": f, "size": round(os.path.getsize(fp)/1024, 1), "ext": os.path.splitext(f)[1].lower()})
                self.send_json({"files": files})
            except Exception as e:
                self.send_json({"files": [], "error": str(e)})

        def handle_delete(self, body):
            try:
                data = json.loads(body)
                filename = os.path.basename(data.get('filename', ''))
                fp = os.path.join(BASE_DIR, 'knowledge', filename)
                if os.path.exists(fp):
                    os.remove(fp)
                    self.send_json({"ok": True})
                else:
                    self.send_json({"ok": False, "error": "File not found"})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)})

        def handle_upload(self, length, body):
            try:
                ct = self.headers.get('Content-Type', '')
                if 'boundary=' not in ct:
                    self.send_json({"ok": False, "error": "Invalid content type"}); return
                boundary = ct.split('boundary=')[1].strip().encode()
                parts = body.split(b'--' + boundary)
                filename = None
                filedata = None
                for part in parts:
                    if b'Content-Disposition' not in part or b'filename=' not in part:
                        continue
                    header_end = part.find(b'\r\n\r\n')
                    if header_end == -1: continue
                    header = part[:header_end].decode('utf-8', errors='ignore')
                    data = part[header_end + 4:]
                    if data.endswith(b'\r\n'): data = data[:-2]
                    for h in header.split('\r\n'):
                        if 'filename=' in h:
                            filename = os.path.basename(h.split('filename=')[1].strip().strip('"'))
                    filedata = data
                if not filename or filedata is None:
                    self.send_json({"ok": False, "error": "No file found"}); return
                allowed = ('.pdf', '.docx', '.txt', '.xlsx', '.md')
                if not filename.lower().endswith(allowed):
                    self.send_json({"ok": False, "error": "File type not allowed"}); return
                save_path = os.path.join(BASE_DIR, 'knowledge', filename)
                with open(save_path, 'wb') as f:
                    f.write(filedata)
                global knowledge_base
                knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, 'knowledge'))
                ai_responder._cached_pairs = parse_qa_pairs(knowledge_base)
                self.send_json({"ok": True, "filename": filename, "pairs": len(ai_responder._cached_pairs)})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)})

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

    print(f"🌐 Web server starting on port {PORT}")
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()


server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
print("🌐 Web server thread started")

# ── Run Telegram bot in main thread ───────────────────────────────────────────
import os as _os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Nizomiy nomidagi OʻzMPU rasmiy botidasiz. Qanday yordam bera olaman? 🎓"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 Savol yozing, masalan:\n\n"
        "• Imtihon jadvali qachon?\n"
        "• HEMIS parolni tiklash\n"
        "• GPA qanday hisoblanadi?\n\n"
        "Rus va ingliz tilida ham sorasangiz boladi! 🌍"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    user = update.message.from_user
    username = user.username or user.first_name or "Talaba"

    await update.message.chat.send_action("typing")
    answer, options, lang, category = get_answer(question, knowledge_base, clients)

    # Log using shared in-memory logger
    logger.log_message(str(user.id), username, question, answer, lang, category)

    if options:
        keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
        await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(answer)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected = query.data
    user = query.from_user
    username = user.username or user.first_name or "Talaba"

    await query.message.reply_text(f"🔍 {selected}")
    answer, options, lang, category = get_answer(selected, knowledge_base, clients)
    logger.log_message(str(user.id), username, selected, answer, lang, category)

    if options:
        keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
        await query.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.message.reply_text(answer)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Buyruq tanilmadi. Savolingizni yozing! 😊")


def main():
    token = _os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN not found!")
    app = (ApplicationBuilder().token(token)
           .connect_timeout(30).read_timeout(30).write_timeout(30).build())
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    print("✅ Bot is live!")
    app.run_polling()


main()