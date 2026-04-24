import os
import json
import logging
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import database as db
import ai_responder
import logger
import auth
import notifier
from file_loader import load_knowledge_base

app = FastAPI(title="UzNPUU Bot API")

def reload_kb():
    import state
    from file_loader import load_knowledge_base
    import ai_responder
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    kb_folder = os.path.join(BASE_DIR, "data", "knowledge")

    # Only load files marked as 'trained'
    trained_files = db.get_trained_filenames()

    if trained_files:
        # Load only trained files
        state.knowledge_base = load_knowledge_base(kb_folder, include_files=trained_files)
        logging.info(f"Knowledge Base reloaded: {len(trained_files)} trained files.")
    else:
        # Fallback: load ALL files so the bot is never left empty
        state.knowledge_base = load_knowledge_base(kb_folder)
        logging.warning("No trained files found — loaded ALL knowledge files as fallback.")

    ai_responder._cached_pairs = ai_responder.parse_qa_pairs(state.knowledge_base)

# Serve static assets (favicon, etc.)
import pathlib
STATIC_DIR = pathlib.Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
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

# ── Static Pages ──────────────────────────────────────────────────────────────

@app.get("/", response_class=JSONResponse)
async def index():
    return {
        "status": "online",
        "message": "UzNPUU Bot API is running",
        "mini_app": "https://uz-npuu.vercel.app/student"
    }

@app.get("/admin", response_class=HTMLResponse)
async def admin():
    return """
    <html>
        <head><title>UzNPUU Admin</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>UzNPUU Admin Panel</h1>
            <p>Eski admin panel o'chirildi. Iltimos, yangi <b>Next.js</b> panelidan foydalaning.</p>
            <a href="https://uznpuu-production.up.railway.app" style="color: blue;">Panelni ochish</a>
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
    
    # Metadata for database persistence
    student_tg_id = data.get('student_telegram_id') or data.get('student_tg_id', 'WEB')
    
    # Try to load student context from DB if tg_id is known
    student = db.get_student(student_tg_id)
    student_id = data.get('student_id') or (student.get('student_id') if student else '')
    faculty_id = data.get('faculty_id') or (student.get('faculty_id') if student else None)
    username = data.get('student_username') or (student.get('username') if student else 'WebUser')
    fullname = data.get('student_name') or (student.get('full_name') if student else 'Veb talaba')
    
    import state
    import asyncio
    answer, options, lang, category = ai_responder.get_answer(q, state.knowledge_base, state.clients, faculty_id=faculty_id)
    
    # Save to database
    db.save_question(
        str(student_tg_id), student_id, username, fullname, 
        faculty_id, q, answer, lang, category
    )
    logger.log_message(str(student_tg_id), username, q, answer, lang, category)

    # Real-time Forward to Admin
    asyncio.create_task(notifier.forward_to_admin(fullname, q, answer, student_id, faculty_id))

    return {
        "answer": answer,
        "options": options or [],
        "lang": lang,
        "category": category
    }

@app.post("/api/ask_admin")
async def ask_admin(request: Request):
    data = await request.json()
    q = data.get('question', '').strip()
    student_tg_id = data.get('student_telegram_id') or data.get('student_tg_id', 'WEB')
    
    student = db.get_student(student_tg_id)
    student_id = data.get('student_id') or (student.get('student_id') if student else '')
    faculty_id = data.get('faculty_id') or (student.get('faculty_id') if student else None)
    fullname = data.get('student_name') or (student.get('full_name') if student else 'Veb talaba')
    username = data.get('student_username') or (student.get('username') if student else 'WebUser')

    # Save as manual request in DB
    db.save_question(str(student_tg_id), student_id, username, fullname, faculty_id, q, "Admin javobini kuting...", "uz", "MANUAL")
    
    import asyncio
    asyncio.create_task(notifier.notify_admin_manual(fullname, q, student_id, faculty_id))
    
    return {"ok": True, "message": "Savolingiz adminstratorga yuborildi."}

@app.get("/api/student/history")
async def get_student_history(student_telegram_id: str, limit: int = 30):
    """
    Public endpoint: returns a student's chat history from both
    the Telegram bot and the mini app (same questions table).
    Gated only by knowing your own student_telegram_id.
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

# ── Admin Auth ────────────────────────────────────────────────────────────────
@app.post("/api/admin/auth")
async def admin_auth(request: Request):
    data = await request.json()
    username = data.get('username', '')
    password = data.get('password', '')
    admin_user = db.verify_admin(username, password)
    if admin_user:
        access_token = auth.create_access_token(data={"sub": username, "role": "admin"})
        return {"ok": True, "token": access_token}
    return {"ok": False, "error": "Invalid credentials"}

# ── Protected Admin API ───────────────────────────────────────────────────────
@app.get("/api/admin/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_admin)):
    return db.get_stats_db()

@app.get("/api/admin/faculties")
async def get_admin_faculties(current_user: dict = Depends(get_current_admin)):
    return {"faculties": db.get_all_faculties()}

@app.post("/api/admin/faculties")
async def create_faculty(request: Request, current_user: dict = Depends(get_current_admin)):
    data = await request.json()
    ok, msg = db.create_faculty(data.get('name',''), data.get('description',''),
                                data.get('group_id',''), data.get('group_name',''))
    return {"ok": ok, "error": msg if not ok else None}

@app.put("/api/admin/faculties/{fid}")
async def update_faculty(fid: int, request: Request, current_user: dict = Depends(get_current_admin)):
    data = await request.json()
    if data.get('update_group_only'):
        faculty = db.get_faculty(fid)
        if faculty:
            db.update_faculty(fid, faculty['name'], faculty.get('description',''),
                             data.get('group_id',''), data.get('group_name',''))
    else:
        db.update_faculty(fid, data.get('name',''), data.get('description',''),
                         data.get('group_id',''), data.get('group_name',''))
    return {"ok": True}

@app.delete("/api/admin/faculties/{fid}")
async def delete_faculty(fid: int, current_user: dict = Depends(get_current_admin)):
    db.delete_faculty(fid)
    return {"ok": True}

@app.get("/api/admin/users")
async def get_admin_users(current_user: dict = Depends(get_current_admin)):
    return {"users": db.get_all_users()}

@app.post("/api/admin/users")
async def create_user(request: Request, current_user: dict = Depends(get_current_admin)):
    data = await request.json()
    ok, msg = db.create_user(data.get('phone',''), data.get('password',''),
                             data.get('full_name',''), data.get('faculty_id') or None,
                             data.get('role','staff'))
    return {"ok": ok, "error": msg if not ok else None}

@app.delete("/api/admin/users/{uid}")
async def delete_user(uid: int, current_user: dict = Depends(get_current_admin)):
    db.delete_user(uid)
    return {"ok": True}

@app.get("/api/admin/questions")
async def get_admin_questions(faculty_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50, current_user: dict = Depends(get_current_admin)):
    questions = db.get_questions(faculty_id=faculty_id, status=status, limit=limit)
    return {"questions": questions}

@app.post("/api/admin/questions/{qid}/answer")
async def answer_question(qid: int, request: Request, current_user: dict = Depends(get_current_admin)):
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

    if state.bot_app:
        try:
            # Use HTML parse mode (same as notifier.py) to avoid Markdown parse errors
            # caused by special characters like *, _, `, [ in question/answer text
            if question['question'] in ["Adminstruatordan xabari", "__ADMIN_FOLLOW_UP__"]:
                msg = f"👤 <b>Adminstrator:</b>\n\n{esc_html(answer)}"
            else:
                msg = (
                    f"✨ <b>Sizning savolingizga javob keldi:</b>\n\n"
                    f"❓ {esc_html(question['question'])}\n\n"
                    f"✅ {esc_html(answer)}"
                )

            await state.bot_app.bot.send_message(
                chat_id=question['student_telegram_id'],
                text=msg,
                parse_mode='HTML'
            )

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

                # Immediately mark the NEW manual follow-up as answered so it shows up in CRM
                new_q = db_lib.get_conn().execute(
                    "SELECT id FROM questions WHERE student_telegram_id=? AND question='__ADMIN_FOLLOW_UP__' ORDER BY id DESC LIMIT 1",
                    (str(question['student_telegram_id']),)
                ).fetchone()
                if new_q:
                    db.update_question_answer(new_q['id'], answer, current_user.get('sub', 'admin'))
            else:
                db.update_question_answer(qid, answer, current_user.get('sub', 'admin'))

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
    return {"items": db.get_faq_items(faculty_id=faculty_id)}

@app.post("/api/admin/faq")
async def create_faq(request: Request, current_user: dict = Depends(get_current_admin)):
    data = await request.json()
    db.add_faq_item(data.get('faculty_id') or None, data.get('question',''), data.get('answer',''))
    return {"ok": True}

@app.delete("/api/admin/faq/{iid}")
async def delete_faq(iid: int, current_user: dict = Depends(get_current_admin)):
    db.delete_faq_item(iid)
    return {"ok": True}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_admin)):
    filename = file.filename
    if not filename.lower().endswith(('.pdf','.docx','.txt','.xlsx','.md')):
        return {"ok": False, "error": "Type not allowed"}

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    kb_folder = os.path.join(BASE_DIR, 'data', 'knowledge')
    os.makedirs(kb_folder, exist_ok=True)
    save_path = os.path.join(kb_folder, filename)

    # Write binary (works for PDF, DOCX, XLSX, TXT)
    content_bytes = await file.read()
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

    db.upsert_file_status(filename, status='trained', pairs=pair_count)

    # Reload KB (new file is trained so it will be active immediately)
    reload_kb()

    return {"ok": True, "filename": filename, "pairs": pair_count}


@app.get("/api/admin/files")
async def get_admin_files(current_user: dict = Depends(get_current_admin)):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(BASE_DIR, "data", "knowledge")
    if not os.path.exists(folder): return {"files": []}
    
    statuses = db.get_file_statuses()
    files = []
    for f in os.listdir(folder):
        path = os.path.join(folder, f)
        if os.path.isfile(path):
            stat = os.stat(path)
            s = statuses.get(f, {'status': 'draft', 'pairs': 0})
            files.append({
                "name": f,
                "size": stat.st_size,
                "created_at": stat.st_mtime,
                "status": s['status'],
                "pairs": s['pairs']
            })
    return {"files": sorted(files, key=lambda x: x['created_at'], reverse=True)}

@app.put("/api/admin/files/{filename}/status")
async def update_file_status(filename: str, request: Request, current_user: dict = Depends(get_current_admin)):
    data = await request.json()
    new_status = data.get('status')
    if new_status not in ['draft', 'trained']:
        return {"ok": False, "error": "Invalid status"}
    
    # Update pairs count while at it
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(BASE_DIR, 'data', 'knowledge', filename)
    if os.path.exists(path):
        # We need to reload just this text to count pairs if we don't have it
        pairs_count = 0
        try:
             # Just use the existing loader logic indirectly
             temp_kb = load_knowledge_base(None, include_files=[filename])
             pairs_count = len(ai_responder.parse_qa_pairs(temp_kb))
        except: pass
        
        db.upsert_file_status(filename, status=new_status, pairs=pairs_count)
        reload_kb()
        return {"ok": True}
    return {"ok": False, "error": "File not found"}

@app.delete("/api/admin/files/{filename}")
async def delete_admin_file(filename: str, current_user: dict = Depends(get_current_admin)):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Basic protection against directory traversal
    safe_filename = os.path.basename(filename)
    path = os.path.join(BASE_DIR, 'data', 'knowledge', safe_filename)
    
    if os.path.exists(path):
        os.remove(path)
        db.delete_file_status(safe_filename)
        reload_kb()
        return {"ok": True}
    return {"ok": False, "error": "File not found"}

@app.get("/api/stats")
async def get_general_stats():
    return logger.get_stats()

@app.get("/api/logs")
async def get_logs():
    return {"logs": logger.get_logs()[-50:][::-1]}

# ── Admin Cards Management ────────────────────────────────────────────────────
@app.get("/api/admin/cards")
async def get_admin_cards(current_user: dict = Depends(get_current_admin)):
    return {"cards": db.get_service_cards(only_active=False)}

@app.post("/api/admin/cards")
async def create_card(request: Request, current_user: dict = Depends(get_current_admin)):
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
    data = await request.json()
    direction = data.get('direction', 'up')
    db.reorder_service_card(cid, direction)
    return {"ok": True}

@app.delete("/api/admin/cards/{cid}")
async def delete_card(cid: int, current_user: dict = Depends(get_current_admin)):
    db.delete_service_card(cid)
    return {"ok": True}
