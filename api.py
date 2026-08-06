import os
import json
import logging
from dotenv import load_dotenv
load_dotenv()

from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import database as db
db.init_db()
import ai_responder
import logger
import auth
import notifier
from file_loader import load_knowledge_base

app = FastAPI(title="NPUU Bot API")

def reload_kb():
    import state
    from file_loader import load_knowledge_base
    import ai_responder
    import vector_store
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    kb_folder = os.path.join(BASE_DIR, "data", "knowledge")

    # Load all files in the folder (logic removed for trained/draft)
    state.knowledge_base = load_knowledge_base(kb_folder)
    logging.info("Knowledge Base reloaded from all available files.")

    ai_responder._cached_pairs = ai_responder.parse_qa_pairs(state.knowledge_base)
    
    # Update Vector Store
    vector_store.clear_vector_db()
    vector_store.add_to_vector_db(ai_responder._cached_pairs)

# Serve static assets (favicon, etc.)
import pathlib
STATIC_DIR = pathlib.Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import FileResponse
    path = os.path.join(os.path.dirname(__file__), "static", "bot-icon.png")
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=False,  # Cannot combine wildcard origin with credentials
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_admin(token: str = Depends(oauth2_scheme)):
    payload = auth.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def check_permission(current_user: dict, required_permission: str):
    role = current_user.get("role")
    if role == "admin":
        return True
    
    perms = current_user.get("permissions") or ""
    perms_list = [p.strip().lower() for p in perms.split(",") if p.strip()]
    if required_permission.lower() in perms_list:
        return True
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Sizda ushbu amalni bajarish uchun yetarli huquqlar yo'q."
    )

# ── Static Pages ──────────────────────────────────────────────────────────────

@app.get("/", response_class=JSONResponse)
async def index():
    return {
        "status": "online",
        "message": "NPUU Bot API is running",
        "mini_app": "https://uz-npuu.vercel.app/student"
    }

@app.get("/admin", response_class=HTMLResponse)
async def admin():
    return """
    <html>
        <head><title>NPUU Admin</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>NPUU Admin Panel</h1>
            <p>Eski admin panel o'chirildi. Iltimos, yangi <b>Next.js</b> panelidan foydalaning.</p>
            <a href="https://npuu-production.up.railway.app" style="color: blue;">Panelni ochish</a>
        </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "ok", "pairs": len(ai_responder._cached_pairs or []), "logs": len(logger._logs)}

@app.get("/api/ping")
async def ping():
    return {"ping": "pong"}

@app.get("/api/bot/status")
async def bot_status_endpoint():
    """Diagnostic: check if the Telegram bot polling thread is alive."""
    import main as main_module
    import state
    s = main_module.bot_status
    return {
        "bot_running": s.get("running", False),
        "bot_app_set": state.bot_app is not None,
        "attempts": s.get("attempts", 0),
        "last_start": s.get("last_start"),
        "last_error": s.get("last_error"),
        "kb_loaded": bool(state.knowledge_base),
        "ai_ready": bool(state.clients),
        "kb_pairs": len(getattr(__import__('ai_responder'), '_cached_pairs') or []),
    }

# ── Public API ────────────────────────────────────────────────────────────────
@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    q = data.get('question', '').strip()
    if not q:
        return {"answer": "Savol bo'sh!"}
    
    # Check working hours
    is_working, offline_msg = db.is_within_working_hours()
    if not is_working:
        return {"answer": offline_msg}
    
    # Metadata for database persistence
    student_tg_id = data.get('student_telegram_id') or data.get('student_tg_id', 'WEB')
    
    import state
    max_req = int(db.get_setting("rate_limit_requests", "2"))
    win_sec = int(db.get_setting("rate_limit_window", "120"))
    
    is_allowed, wait_time = state.check_rate_limit(str(student_tg_id), max_requests=max_req, window_seconds=win_sec)
    if not is_allowed:
        minutes = wait_time // 60
        seconds = wait_time % 60
        return {
            "answer": f"⏳ Siz qisqa vaqt ichida ko'p savol berdingiz. Iltimos {minutes} daqiqa va {seconds} soniya kuting.",
            "rate_limited": True,
            "wait_time": wait_time
        }
    
    # Try to load student context from DB if tg_id is known
    student = db.get_student(student_tg_id)
    student_id = data.get('student_id') or (student.get('student_id') if student else '')
    faculty_id = data.get('faculty_id') or (student.get('faculty_id') if student else None)
    username = data.get('student_username') or (student.get('username') if student else 'WebUser')
    fullname = data.get('student_name') or (student.get('full_name') if student else 'Veb talaba')
    
    import state
    import asyncio
    answer, options, lang, category, topic = ai_responder.get_answer(q, state.knowledge_base, state.clients, faculty_id=faculty_id)
    
    # Save to database
    db.save_question(
        str(student_tg_id), student_id, username, fullname, 
        faculty_id, q, answer, lang, category
    )
    logger.log_message(str(student_tg_id), username, q, answer, lang, category)

    # Real-time Forward to Admin (Disabled: now only forwards when 'Ask Admin' is clicked)
    # asyncio.create_task(notifier.forward_to_admin(fullname, q, answer, student_id, faculty_id))

    return {
        "answer": answer,
        "options": options or [],
        "lang": lang,
        "category": category
    }

@app.post("/api/ask_admin")
async def ask_admin(request: Request):
    data = await request.json()
    
    is_working, offline_msg = db.is_within_working_hours()
    if not is_working:
        return {"ok": False, "message": offline_msg}
        
    q = data.get('question', '').strip()
    student_tg_id = data.get('student_telegram_id') or data.get('student_tg_id', 'WEB')
    
    import state
    max_req = int(db.get_setting("rate_limit_requests", "2"))
    win_sec = int(db.get_setting("rate_limit_window", "120"))
    
    is_allowed, wait_time = state.check_rate_limit(str(student_tg_id), max_requests=max_req, window_seconds=win_sec)
    if not is_allowed:
        minutes = wait_time // 60
        seconds = wait_time % 60
        return {"ok": False, "message": f"⏳ Iltimos {minutes} daqiqa va {seconds} soniya kuting."}
    
    student = db.get_student(student_tg_id)
    student_id = data.get('student_id') or (student.get('student_id') if student else '')
    faculty_id = data.get('faculty_id') or (student.get('faculty_id') if student else None)
    fullname = data.get('student_name') or (student.get('full_name') if student else 'Veb talaba')
    username = data.get('student_username') or (student.get('username') if student else 'WebUser')

    # Save as manual request in DB
    db.save_question(str(student_tg_id), student_id, username, fullname, faculty_id, q, "Admin javobini kuting...", "uz", "MANUAL")
    
    import asyncio
    asyncio.create_task(notifier.notify_admin_manual(fullname, q, student_id, faculty_id, student_tg_id=str(student_tg_id)))
    
    return {"ok": True, "message": "Savolingiz administratorga yuborildi."}

@app.get("/api/student/history")
async def get_student_history(student_telegram_id: str, limit: int = 30, current_user: dict = Depends(get_current_admin)):
    """
    Admin-only endpoint: returns a student's chat history.
    """
    if not student_telegram_id or student_telegram_id in ("WEB", ""):
        return {"history": []}
    items = db.get_student_history(student_telegram_id, limit=min(limit, 50))
    return {"history": items}

@app.get("/api/faculties")
async def get_public_faculties():
    return {"faculties": db.get_all_faculties()}

@app.get("/api/cards")
async def get_public_cards(faculty_id: Optional[int] = None):
    try:
        return {"cards": db.get_service_cards(only_active=True, faculty_id=faculty_id)}
    except Exception as e:
        logger.log_message("SYSTEM", "API", f"Cards Error: {str(e)}", "ERROR", "SYSTEM", "ERROR")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/faq")
async def get_public_faq(faculty_id: Optional[int] = None):
    try:
        return {"items": db.get_faq_items(faculty_id=faculty_id)}
    except Exception as e:
        logger.log_message("SYSTEM", "API", f"FAQ Error: {str(e)}", "ERROR", "SYSTEM", "ERROR")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/public/files")
async def get_public_files():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(BASE_DIR, "data", "knowledge")
    if not os.path.exists(folder): return {"files": []}
    files = []
    for f in os.listdir(folder):
        if os.path.isfile(os.path.join(folder, f)):
            files.append({"name": f, "url": f"/api/public/files/{f}"})
    return {"files": files}

@app.get("/api/public/files/{filename:path}")
async def download_public_file(filename: str):
    import urllib.parse
    from fastapi.responses import FileResponse
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    safe_filename = os.path.basename(urllib.parse.unquote(filename))
    path = os.path.join(BASE_DIR, "data", "knowledge", safe_filename)
    if os.path.exists(path):
        return FileResponse(path, filename=safe_filename)
    raise HTTPException(status_code=404, detail="File not found")

# ── Admin Auth ────────────────────────────────────────────────────────────────
@app.post("/api/admin/auth")
async def admin_auth(request: Request):
    try:
        data = await request.json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Try Super Admin login
        admin_user = db.verify_admin(username, password)
        if admin_user:
            access_token = auth.create_access_token(data={"sub": username, "role": "admin", "full_name": admin_user.get("full_name", "Super Admin"), "permissions": "all"})
            return {"ok": True, "token": access_token}
            
        # Try Staff User login (username input is user's phone)
        user = db.verify_user(username, password)
        if user:
            access_token = auth.create_access_token(data={
                "sub": user['phone'],
                "role": user['role'],
                "full_name": user.get('full_name', 'Xodim'),
                "faculty_id": user['faculty_id'],
                "user_id": user['id'],
                "permissions": user.get('permissions') or ""
            })
            return {"ok": True, "token": access_token}
            
        return JSONResponse(status_code=401, content={"ok": False, "error": "Foydalanuvchi nomi yoki parol noto'g'ri"})
    except Exception as e:
        logging.error(f"Auth error: {e}")
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

# ── Protected Admin API ───────────────────────────────────────────────────────
@app.get("/api/admin/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_admin)):
    return db.get_stats_db()

@app.get("/api/admin/settings")
async def get_admin_settings(current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Ushbu amalni bajarish uchun sizda yetarli huquqlar yo'q.")
    return {
        "bot_start_time": db.get_setting("bot_start_time", "09:00"),
        "bot_end_time": db.get_setting("bot_end_time", "18:00"),
        "bot_work_days": db.get_setting("bot_work_days", "0,1,2,3,4"),
        "bot_offline_message": db.get_setting("bot_offline_message", "Bot hozirda dam olish rejimida. Iltimos, ish vaqtida murojaat qiling."),
        "rate_limit_requests": db.get_setting("rate_limit_requests", "2"),
        "rate_limit_window": db.get_setting("rate_limit_window", "120")
    }

@app.post("/api/admin/settings")
async def update_admin_settings(request: Request, current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Ushbu amalni bajarish uchun sizda yetarli huquqlar yo'q.")
    data = await request.json()
    allowed_keys = ["bot_start_time", "bot_end_time", "bot_work_days", "bot_offline_message", "rate_limit_requests", "rate_limit_window"]
    for key in allowed_keys:
        if key in data:
            db.set_setting(key, str(data[key]))
    return {"ok": True}

@app.get("/api/admin/faculties")
async def get_admin_faculties(current_user: dict = Depends(get_current_admin)):
    return {"faculties": db.get_all_faculties()}

@app.post("/api/admin/faculties")
async def create_faculty(request: Request, current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Ushbu amalni bajarish uchun sizda yetarli huquqlar yo'q.")
    data = await request.json()
    ok, msg = db.create_faculty(data.get('name',''), data.get('description',''),
                                data.get('telegram_group_id','') or data.get('group_id',''), 
                                data.get('telegram_group_name','') or data.get('group_name',''))
    return {"ok": ok, "error": msg if not ok else None}

@app.put("/api/admin/faculties/{fid}")
async def update_faculty(fid: int, request: Request, current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Ushbu amalni bajarish uchun sizda yetarli huquqlar yo'q.")
    data = await request.json()
    if data.get('update_group_only'):
        faculty = db.get_faculty(fid)
        if faculty:
            db.update_faculty(fid, faculty['name'], faculty.get('description',''),
                             data.get('telegram_group_id','') or data.get('group_id',''), 
                             data.get('telegram_group_name','') or data.get('group_name',''))
    else:
        db.update_faculty(fid, data.get('name',''), data.get('description',''),
                         data.get('telegram_group_id','') or data.get('group_id',''), 
                         data.get('telegram_group_name','') or data.get('group_name',''))
    return {"ok": True}

@app.delete("/api/admin/faculties/{fid}")
async def delete_faculty(fid: int, current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Ushbu amalni bajarish uchun sizda yetarli huquqlar yo'q.")
    db.delete_faculty(fid)
    return {"ok": True}

@app.get("/api/admin/users")
async def get_admin_users(current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Ushbu amalni bajarish uchun sizda yetarli huquqlar yo'q.")
    return {"users": db.get_all_users()}

@app.post("/api/admin/users")
async def create_user(request: Request, current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Ushbu amalni bajarish uchun sizda yetarli huquqlar yo'q.")
    data = await request.json()
    permissions = data.get('permissions', '')
    if isinstance(permissions, list):
        permissions = ",".join(permissions)
    ok, msg = db.create_user(data.get('phone',''), data.get('password',''),
                             data.get('full_name',''), data.get('faculty_id') or None,
                             data.get('role','staff'), permissions=permissions)
    return {"ok": ok, "error": msg if not ok else None}

@app.delete("/api/admin/users/{uid}")
async def delete_user(uid: int, current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Ushbu amalni bajarish uchun sizda yetarli huquqlar yo'q.")
    db.delete_user(uid)
    return {"ok": True}

@app.get("/api/admin/questions")
async def get_admin_questions(faculty_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50, current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'chat')
    if current_user.get('role') in ('admin', 'superadmin'):
        # Admin can view all, keeping any faculty_id filter if passed
        pass
    elif current_user.get('faculty_id'):
        faculty_id = current_user.get('faculty_id')
    questions = db.get_questions(faculty_id=faculty_id, status=status, limit=limit)
    return {"questions": questions}

@app.post("/api/admin/questions/{qid}/answer")
async def answer_question(qid: int, request: Request, current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'chat')
    data = await request.json()
    answer = data.get('answer', '').strip()
    if not answer:
        return {"ok": False, "error": "Javob bo'sh!"}
    
    question = db.get_question(qid)
    if not question:
        return {"ok": False, "error": "Savol topilmadi"}

    import state
    import html as html_lib

    def esc_html(text):
        """Escape text for Telegram HTML parse mode."""
        if not text:
            return ""
        return html_lib.escape(str(text))

    def clean_question_preview(q):
        if not q:
            return ""
        import re
        cleaned = re.sub(r'\[(?:IMAGE|FILE):\s*(https?://[^\s\]]+)\]', '', q, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        if not cleaned:
            if "[IMAGE:" in q:
                return "(Yuborilgan rasm)"
            elif "[FILE:" in q:
                return "(Yuborilgan fayl)"
            return "(Yuborilgan media)"
        return cleaned

    if state.bot_app:
        try:
            conn = db.get_conn()
            admin_row = conn.execute("SELECT full_name FROM admins WHERE username=?", (current_user.get('sub'),)).fetchone()
            if not admin_row:
                admin_row = conn.execute("SELECT full_name FROM users WHERE phone=?", (current_user.get('sub'),)).fetchone()
            conn.close()
            admin_name = admin_row['full_name'] if admin_row and admin_row['full_name'] else current_user.get('sub', 'Adminstrator')

            # Use HTML parse mode (same as notifier.py) to avoid Markdown parse errors
            # caused by special characters like *, _, `, [ in question/answer text
            if question['question'] in ["Adminstruatordan xabari", "__ADMIN_FOLLOW_UP__"]:
                msg = f"👤 <b>{esc_html(admin_name)}:</b>\n\n{esc_html(answer)}"
            else:
                msg = (
                    f"✨ <b>Sizning savolingizga javob keldi:</b>\n\n"
                    f"❓ {esc_html(clean_question_preview(question['question']))}\n\n"
                    f"✅ 👤 <b>{esc_html(admin_name)} javobi:</b>\n{esc_html(answer)}"
                )

            await state.bot_app.bot.send_message(
                chat_id=question['student_telegram_id'],
                text=msg,
                parse_mode='HTML'
            )

            # Also notify the faculty Telegram group
            import asyncio as _asyncio
            import notifier
            _asyncio.create_task(notifier.notify_group_admin_reply(
                admin_name=admin_name,
                question_text=question.get('question', ''),
                answer_text=answer,
                sid=question.get('student_id') or question.get('student_telegram_id'),
                fid=question.get('faculty_id')
            ))

            # If already answered, create a NEW row instead of overwriting
            if question['status'] == 'answered':
                import database as db_lib
                db_lib.save_question(
                    question['student_telegram_id'],
                    question.get('student_id'),
                    question.get('student_username'),
                    question.get('student_name'),
                    question.get('faculty_id'),
                    "__ADMIN_FOLLOW_UP__",
                    answer,
                    question.get('lang', 'uz'),
                    "MANUAL"
                )

                # Immediately mark the NEW manual follow-up as answered
                import database as db_lib
                _conn = db_lib.get_conn()
                try:
                    new_q = _conn.execute(
                        "SELECT id FROM questions WHERE student_telegram_id=? AND question='__ADMIN_FOLLOW_UP__' ORDER BY id DESC LIMIT 1",
                        (str(question['student_telegram_id']),)
                    ).fetchone()
                    if new_q:
                        db.update_question_answer(new_q['id'], answer, current_user.get('sub', 'admin'), current_user.get('full_name') or 'Administrator')
                finally:
                    _conn.close()
            else:
                db.update_question_answer(qid, answer, current_user.get('sub', 'admin'), current_user.get('full_name') or 'Administrator')

            return {"ok": True}
        except Exception as e:
            # Use repr(e) to get the full exception type + message, not just str(e)
            error_detail = getattr(e, 'message', None) or repr(e)
            logging.error(f"❌ Telegram send error for qid={qid}: {error_detail}")
            return {"ok": False, "error": f"Telegram xatosi: {error_detail}"}
    else:
        return {"ok": False, "error": "Bot faol emas"}

@app.get("/api/admin/faq")
async def get_admin_faq(faculty_id: Optional[int] = None, current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'faq')
    if current_user.get('role') in ('admin', 'superadmin'):
        pass
    elif current_user.get('faculty_id'):
        faculty_id = current_user.get('faculty_id')
    return {"items": db.get_faq_items(faculty_id=faculty_id)}

@app.post("/api/admin/faq")
async def create_faq(request: Request, current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'faq')
    data = await request.json()
    faculty_id = data.get('faculty_id') or None
    if current_user.get('role') not in ('admin', 'superadmin') and current_user.get('faculty_id'):
        faculty_id = current_user.get('faculty_id')
    db.add_faq_item(faculty_id, data.get('question',''), data.get('answer',''))
    return {"ok": True}

@app.delete("/api/admin/faq/{iid}")
async def delete_faq(iid: int, current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'faq')
    db.delete_faq_item(iid)
    return {"ok": True}

@app.put("/api/admin/faq/{iid}")
async def update_faq(iid: int, request: Request, current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'faq')
    data = await request.json()
    faculty_id = data.get('faculty_id') or None
    if current_user.get('role') not in ('admin', 'superadmin') and current_user.get('faculty_id'):
        faculty_id = current_user.get('faculty_id')
    db.update_faq_item(iid, faculty_id, data.get('question',''), data.get('answer',''))
    return {"ok": True}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'upload')
    filename = file.filename
    if not filename.lower().endswith(('.pdf','.docx','.txt','.xlsx','.md')):
        return {"ok": False, "error": "Type not allowed"}

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    kb_folder = os.path.join(BASE_DIR, 'data', 'knowledge')
    os.makedirs(kb_folder, exist_ok=True)
    save_path = os.path.join(kb_folder, filename)

    # File size limit: 10 MB
    MAX_FILE_SIZE = 10 * 1024 * 1024
    content_bytes = await file.read()
    if len(content_bytes) > MAX_FILE_SIZE:
        return {"ok": False, "error": "Fayl hajmi 10 MB dan oshmasligi kerak."}
    with open(save_path, 'wb') as f:
        f.write(content_bytes)

    # Count Q&A pairs using the proper file loader (handles PDF/DOCX/XLSX/TXT)
    try:
        temp_text = load_knowledge_base(kb_folder, include_files=[filename])
        temp_pairs = ai_responder.parse_qa_pairs(temp_text)
        pair_count = len(temp_pairs)
    except Exception as e:
        logging.warning(f"Pair count failed for {filename}: {e}")
        pair_count = 0



    # Reload KB safely (new file is trained so it will be active immediately)
    try:
        reload_kb()
    except Exception as e:
        logging.warning(f"Reload KB warning: {e}")

    return {"ok": True, "filename": filename, "pairs": pair_count}


@app.get("/api/admin/files")
async def get_admin_files(current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'upload')
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(BASE_DIR, "data", "knowledge")
    if not os.path.exists(folder): return {"files": []}
    
    files = []
    for f in os.listdir(folder):
        path = os.path.join(folder, f)
        if os.path.isfile(path):
            stat = os.stat(path)
            files.append({
                "name": f,
                "size": stat.st_size,
                "created_at": stat.st_mtime,
                "status": "active",
                "pairs": "N/A"
            })
    return {"files": sorted(files, key=lambda x: x['created_at'], reverse=True)}

@app.put("/api/admin/files/{filename}/status")
async def dummy_status(filename: str, current_user: dict = Depends(get_current_admin)):
    # Dummy endpoint to prevent 404s for old front-end code
    return {"ok": True}



@app.delete("/api/admin/files/{filename:path}")
async def delete_admin_file(filename: str, current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'upload')
    import urllib.parse
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    safe_filename = os.path.basename(urllib.parse.unquote(filename))
    path = os.path.join(BASE_DIR, 'data', 'knowledge', safe_filename)
    
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            logging.warning(f"File remove error: {e}")
        try:
            reload_kb()
        except Exception as e:
            logging.warning(f"Reload KB warning on delete: {e}")
        return {"ok": True}
    return {"ok": True}

@app.get("/api/stats")
async def get_general_stats(current_user: dict = Depends(get_current_admin)):
    return logger.get_stats()

@app.get("/api/logs")
async def get_logs(current_user: dict = Depends(get_current_admin)):
    return {"logs": logger.get_logs()[-50:][::-1]}

# ── Admin Cards Management ────────────────────────────────────────────────────
@app.get("/api/admin/cards")
async def get_admin_cards(current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'cards')
    return {"cards": db.get_service_cards(only_active=False)}

@app.post("/api/admin/cards")
async def create_card(request: Request, current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'cards')
    data = await request.json()
    db.add_service_card(
        data.get('title',''), data.get('description',''),
        data.get('icon',''), data.get('link',''),
        data.get('type','message'),
        data.get('faculty_id') or None,
        data.get('sort_order', 0),
        data.get('start_date') or None,
        data.get('end_date') or None,
    )
    return {"ok": True}

@app.put("/api/admin/cards/{cid}")
async def update_card(cid: int, request: Request, current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'cards')
    data = await request.json()
    db.update_service_card(
        cid, data.get('title',''), data.get('description',''),
        data.get('icon',''), data.get('link',''),
        data.get('type','message'), data.get('is_active', 1),
        data.get('faculty_id') or None,
        data.get('sort_order', 0),
        data.get('start_date') or None,
        data.get('end_date') or None,
    )
    return {"ok": True}

@app.post("/api/admin/cards/{cid}/reorder")
async def reorder_card(cid: int, request: Request, current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'cards')
    data = await request.json()
    direction = data.get('direction', 'up')
    db.reorder_service_card(cid, direction)
    return {"ok": True}

@app.delete("/api/admin/cards/{cid}")
async def delete_card(cid: int, current_user: dict = Depends(get_current_admin)):
    check_permission(current_user, 'cards')
    db.delete_service_card(cid)
    return {"ok": True}

@app.get("/api/admin/analytics")
async def get_analytics(current_user: dict = Depends(get_current_admin)):
    return db.get_analytics_stats()

# ─── ALLOWED STUDENTS API ───────────────────────────────────────────────────────
import openpyxl
import io

@app.get("/api/admin/allowed-students")
async def api_get_allowed_students(current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Faqat adminlar ruxsat etilgan talabalarni ko'ra oladi")
    students = db.get_allowed_students()
    return {"students": students}

@app.post("/api/admin/allowed-students/upload")
async def api_upload_allowed_students(file: UploadFile = File(...), current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Faqat adminlar fayl yuklay oladi")
    
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Faqat .xlsx fayllar qabul qilinadi")
        
    try:
        contents = await file.read()
        wb = openpyxl.load_workbook(io.BytesIO(contents), data_only=True)
        sheet = wb.active
        
        # Find column indices
        headers = [str(c.value).strip().lower() if c.value else '' for c in sheet[1]]
        
        id_col = -1
        name_col = -1
        
        for i, h in enumerate(headers):
            if 'id' in h or 'pinfl' in h or 'passport' in h or 'raqam' in h:
                id_col = i
            elif any(w in h for w in ['name', 'ism', 'f.i.o', 'fio', 'fish', 'familiya', 'sharif']):
                name_col = i
                
        if id_col == -1:
            # Fallback: assume column 0 is ID and column 1 is Name
            id_col = 0
            name_col = 1
            
        if name_col == -1 and len(headers) > 1:
            # If we found ID but couldn't find Name, just pick the other column if there's only 2, 
            # or default to column 1 if ID is column 0
            name_col = 1 if id_col == 0 else 0
            
        students_list = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row or len(row) <= id_col: continue
            sid = str(row[id_col]).strip() if row[id_col] else ''
            if not sid or sid == 'None': continue
            
            sname = ''
            if name_col != -1 and len(row) > name_col:
                sname = str(row[name_col]).strip() if row[name_col] else ''
                if sname == 'None': sname = ''
                
            students_list.append({'student_id': sid, 'full_name': sname})
            
        if not students_list:
            return {"ok": False, "error": "Fayldan hech qanday talaba topilmadi"}
            
        db.clear_and_insert_allowed_students(students_list)
        return {"ok": True, "count": len(students_list)}
        
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/admin/questions/user/{tg_id}/read")
async def mark_user_questions_read(tg_id: str, current_user: dict = Depends(get_current_admin)):
    import database as db_lib
    conn = db_lib.get_conn()
    conn.execute("UPDATE questions SET status='answered' WHERE student_telegram_id=? AND status='unanswered'", (tg_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

