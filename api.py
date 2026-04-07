import os
import json
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import database as db
import ai_responder
import logger
import auth
from miniapp_html import get_miniapp_html
from admin_html import get_admin_html
from file_loader import load_knowledge_base

app = FastAPI(title="University Bot API")

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
RAILWAY_URL = os.environ.get("RAILWAY_URL", "")
MINIAPP_HTML = get_miniapp_html(RAILWAY_URL)
ADMIN_HTML = get_admin_html()

@app.get("/", response_class=HTMLResponse)
async def index():
    return MINIAPP_HTML

@app.get("/admin", response_class=HTMLResponse)
async def admin():
    return ADMIN_HTML

@app.get("/health")
async def health():
    return {"status": "ok", "pairs": len(ai_responder._cached_pairs or []), "logs": len(logger._logs)}

# ── Public API ────────────────────────────────────────────────────────────────
@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    q = data.get('question', '').strip()
    if not q:
        return {"answer": "Savol bo'sh!"}
    
    # knowledge_base is now in state
    import state
    answer, options, lang, category = ai_responder.get_answer(q, state.knowledge_base, state.clients)
    if options:
        answer += "\n\n" + "\n".join(f"• {o}" for o in options)
    return {"answer": answer}

@app.get("/api/faculties")
async def get_public_faculties():
    return {"faculties": db.get_all_faculties()}

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
    if state.bot_app:
        try:
            msg = f"✨ **Sizning savolingizga javob keldi:**\n\n❓ {question['question']}\n\n✅ {answer}"
            await state.bot_app.bot.send_message(chat_id=question['student_telegram_id'], text=msg, parse_mode='Markdown')
            db.update_question_answer(qid, answer)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": f"Telegram xatosi: {str(e)}"}
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
    save_path = os.path.join(BASE_DIR, 'knowledge', filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    with open(save_path, 'wb') as f:
        f.write(await file.read())
    
    # Reload knowledge base
    import state
    state.knowledge_base = load_knowledge_base(os.path.join(BASE_DIR, "knowledge"))
    ai_responder._cached_pairs = ai_responder.parse_qa_pairs(state.knowledge_base)
    
    return {"ok": True, "filename": filename, "pairs": len(ai_responder._cached_pairs)}

@app.get("/api/stats")
async def get_general_stats():
    return logger.get_stats()

@app.get("/api/logs")
async def get_logs():
    return {"logs": logger.get_logs()[-50:][::-1]}
