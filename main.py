import os
import sys
import json
import threading
import logging as pylogging
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Init DB ────────────────────────────────────────────────────────────────────
import database as db
db.init_db()

# ── Load AI ────────────────────────────────────────────────────────────────────
print("📂 Loading knowledge base...")
from file_loader import load_knowledge_base
from ai_responder import setup_ai, get_answer, parse_qa_pairs
import ai_responder
import logger

knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge"))
clients = setup_ai()
ai_responder._cached_pairs = parse_qa_pairs(knowledge_base)
print(f"✅ Ready: {len(ai_responder._cached_pairs)} Q&A pairs")

# ── Load HTML ──────────────────────────────────────────────────────────────────
RAILWAY_URL = os.environ.get("RAILWAY_URL", "")
from miniapp_html import get_miniapp_html
from admin_html import get_admin_html
MINIAPP_HTML = get_miniapp_html(RAILWAY_URL)
ADMIN_HTML = get_admin_html()

# ── Web Server ─────────────────────────────────────────────────────────────────
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        path = self.path.split("?")[0]
        params = {}
        if "?" in self.path:
            for p in self.path.split("?")[1].split("&"):
                if "=" in p:
                    k, v = p.split("=", 1)
                    params[k] = v

        if path in ['/', '/index.html']:
            self.send_html(MINIAPP_HTML)
        elif path in ['/admin', '/admin.html']:
            self.send_html(ADMIN_HTML)
        elif path == '/health':
            self.send_json({"status": "ok", "pairs": len(ai_responder._cached_pairs or []), "logs": len(logger._logs)})
        elif path == '/api/admin/stats':
            self.send_json(db.get_stats_db())
        elif path == '/api/admin/faculties':
            self.send_json({"faculties": db.get_all_faculties()})
        elif path == '/api/admin/users':
            self.send_json({"users": db.get_all_users()})
        elif path == '/api/admin/questions':
            fid = params.get('faculty_id')
            status = params.get('status')
            limit = int(params.get('limit', 50))
            questions = db.get_questions(faculty_id=fid, status=status, limit=limit)
            self.send_json({"questions": questions})
        elif path == '/api/admin/faq':
            fid = params.get('faculty_id')
            self.send_json({"items": db.get_faq_items(faculty_id=fid)})
        elif path == '/api/stats':
            self.send_json(logger.get_stats())
        elif path == '/api/logs':
            self.send_json({"logs": logger.get_logs()[-50:][::-1]})
        elif path == '/api/faculties':
            self.send_json({"faculties": db.get_all_faculties()})
        else:
            self.send_json({"status": "running"})

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        path = self.path.split("?")[0]

        if path == '/ask':
            self.handle_ask(body)
        elif path == '/api/admin/auth':
            self.handle_admin_auth(body)
        elif path == '/api/admin/faculties':
            self.handle_create_faculty(body)
        elif path == '/api/admin/users':
            self.handle_create_user(body)
        elif path == '/api/admin/faq':
            self.handle_create_faq(body)
        elif path == '/api/upload':
            self.handle_upload(length, body)
        else:
            self.send_response(404); self.end_headers()

    def do_PUT(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        path = self.path.split("?")[0]
        parts = path.split("/")

        if len(parts) >= 5 and parts[3] == 'faculties':
            fid = int(parts[4])
            data = json.loads(body)
            if data.get('update_group_only'):
                faculty = db.get_faculty(fid)
                if faculty:
                    db.update_faculty(fid, faculty['name'], faculty.get('description',''),
                                     data.get('group_id',''), data.get('group_name',''))
            else:
                db.update_faculty(fid, data.get('name',''), data.get('description',''),
                                 data.get('group_id',''), data.get('group_name',''))
            self.send_json({"ok": True})
        else:
            self.send_response(404); self.end_headers()

    def do_DELETE(self):
        path = self.path.split("?")[0]
        parts = path.split("/")

        if len(parts) >= 5 and parts[3] == 'faculties':
            db.delete_faculty(int(parts[4]))
            self.send_json({"ok": True})
        elif len(parts) >= 5 and parts[3] == 'users':
            db.delete_user(int(parts[4]))
            self.send_json({"ok": True})
        elif len(parts) >= 5 and parts[3] == 'faq':
            db.delete_faq_item(int(parts[4]))
            self.send_json({"ok": True})
        else:
            self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def handle_ask(self, body):
        try:
            data = json.loads(body)
            q = data.get('question', '').strip()
            if not q:
                self.send_json({"answer": "Savol bo'sh!"}); return
            answer, options, lang, category = get_answer(q, knowledge_base, clients)
            if options:
                answer += "\n\n" + "\n".join(f"• {o}" for o in options)
            self.send_json({"answer": answer})
        except Exception as e:
            self.send_json({"answer": str(e)})

    def handle_admin_auth(self, body):
        try:
            data = json.loads(body)
            result = db.verify_admin(data.get('username', ''), data.get('password', ''))
            self.send_json({"ok": bool(result)})
        except:
            self.send_json({"ok": False})

    def handle_create_faculty(self, body):
        try:
            data = json.loads(body)
            ok, msg = db.create_faculty(data.get('name',''), data.get('description',''),
                                        data.get('group_id',''), data.get('group_name',''))
            self.send_json({"ok": ok, "error": msg if not ok else None})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)})

    def handle_create_user(self, body):
        try:
            data = json.loads(body)
            ok, msg = db.create_user(data.get('phone',''), data.get('password',''),
                                     data.get('full_name',''), data.get('faculty_id') or None,
                                     data.get('role','staff'))
            self.send_json({"ok": ok, "error": msg if not ok else None})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)})

    def handle_create_faq(self, body):
        try:
            data = json.loads(body)
            db.add_faq_item(data.get('faculty_id') or None, data.get('question',''), data.get('answer',''))
            self.send_json({"ok": True})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)})

    def handle_upload(self, length, body):
        try:
            ct = self.headers.get('Content-Type', '')
            if 'boundary=' not in ct:
                self.send_json({"ok": False, "error": "Invalid"}); return
            boundary = ct.split('boundary=')[1].strip().encode()
            parts = body.split(b'--' + boundary)
            filename = None; filedata = None
            for part in parts:
                if b'Content-Disposition' not in part or b'filename=' not in part: continue
                he = part.find(b'\r\n\r\n')
                if he == -1: continue
                header = part[:he].decode('utf-8', errors='ignore')
                data = part[he + 4:]
                if data.endswith(b'\r\n'): data = data[:-2]
                for h in header.split('\r\n'):
                    if 'filename=' in h:
                        filename = os.path.basename(h.split('filename=')[1].strip().strip('"'))
                filedata = data
            if not filename or filedata is None:
                self.send_json({"ok": False, "error": "No file"}); return
            if not filename.lower().endswith(('.pdf','.docx','.txt','.xlsx','.md')):
                self.send_json({"ok": False, "error": "Type not allowed"}); return
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


def run_web():
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Web server on port {port}")
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()


# ── Telegram Bot ───────────────────────────────────────────────────────────────
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

pylogging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=pylogging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faculties = [f for f in db.get_all_faculties() if f['is_active']]
    if not faculties:
        await update.message.reply_text(
            "Assalomu alaykum! OʻzMPU botiga xush kelibsiz! 🎓\n\nSavolingizni yozing:"
        )
        return
    keyboard = [[InlineKeyboardButton(f['name'], callback_data=f"fac_{f['id']}")] for f in faculties]
    await update.message.reply_text(
        "Assalomu alaykum! OʻzMPU botiga xush kelibsiz! 🎓\n\n"
        "Qaysi fakultet bo'yicha savol berasiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fname = context.user_data.get('faculty_name', 'tanlanmagan')
    await update.message.reply_text(
        f"💡 Yordam:\n\n• Savolingizni yozing\n• /faculty — fakultet o'zgartirish\n• /start — qayta boshlash\n\n🏫 Fakultet: {fname}"
    )


async def change_faculty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faculties = [f for f in db.get_all_faculties() if f['is_active']]
    keyboard = [[InlineKeyboardButton(f['name'], callback_data=f"fac_{f['id']}")] for f in faculties]
    await update.message.reply_text("Fakultetni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("fac_"):
        fid = int(data.replace("fac_", ""))
        faculty = db.get_faculty(fid)
        if faculty:
            context.user_data['faculty_id'] = fid
            context.user_data['faculty_name'] = faculty['name']
            await query.message.reply_text(
                f"✅ {faculty['name']} tanlandi!\n\nSavolingizni yozing 📚"
            )

    elif data.startswith("opt_"):
        selected = data.replace("opt_", "")
        user = query.from_user
        username = user.username or user.first_name or "Talaba"
        fid = context.user_data.get('faculty_id')
        await query.message.reply_text(f"🔍 {selected}")
        answer, options, lang, category = get_answer(selected, knowledge_base, clients)
        db.save_question(str(user.id), username, user.full_name or username, fid, selected, answer, lang, category)
        logger.log_message(str(user.id), username, selected, answer, lang, category)
        if options:
            kb = [[InlineKeyboardButton(o, callback_data=f"opt_{o[:40]}")] for o in options]
            await query.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await query.message.reply_text(answer)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    user = update.message.from_user
    username = user.username or user.first_name or "Talaba"
    fid = context.user_data.get('faculty_id')

    await update.message.chat.send_action("typing")
    answer, options, lang, category = get_answer(question, knowledge_base, clients)

    db.save_question(str(user.id), username, user.full_name or username, fid, question, answer, lang, category)
    logger.log_message(str(user.id), username, question, answer, lang, category)

    # Forward to faculty Telegram group
    if fid:
        faculty = db.get_faculty(fid)
        if faculty and faculty.get('telegram_group_id'):
            try:
                msg = (f"📨 Yangi savol!\n👤 {user.full_name or username}\n"
                       f"🏫 {faculty['name']}\n❓ {question}\n🤖 {answer[:300]}")
                await update.message.get_bot().send_message(chat_id=faculty['telegram_group_id'], text=msg)
            except Exception as e:
                print(f"⚠️ Group send error: {e}")

    if options:
        kb = [[InlineKeyboardButton(o, callback_data=f"opt_{o[:40]}")] for o in options]
        await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(answer)


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
    app.add_handler(CommandHandler("faculty", change_faculty))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    print("✅ Bot is live!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    run_bot()