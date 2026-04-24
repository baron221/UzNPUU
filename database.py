"""
database.py — SQLite database for users, faculties, and questions
"""
import sqlite3
import os
from datetime import datetime, timedelta
from auth import get_password_hash, verify_password

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Data directory should be persistent (e.g. Railway Volume)
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "university.db")


# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_now_uz():
    """Returns current Tashkent time (UTC+5) as YYYY-MM-DD HH:MM:SS"""
    now_utc = datetime.utcnow()
    now_uz = now_utc + timedelta(hours=5)
    return now_uz.strftime("%Y-%m-%d %H:%M:%S")

def get_conn():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# Removed hash_password in favor of get_password_hash from auth.py


def init_db():
    """Create all tables and default super admin."""
    conn = get_conn()
    c = conn.cursor()

    # Faculties table
    c.execute('''CREATE TABLE IF NOT EXISTS faculties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        telegram_group_id TEXT,
        telegram_group_name TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1
    )''')

    # Service cards for student dashboard
    c.execute('''CREATE TABLE IF NOT EXISTS service_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        icon TEXT,
        link TEXT,
        type TEXT DEFAULT 'message',
        is_active INTEGER DEFAULT 1,
        faculty_id INTEGER,
        sort_order INTEGER DEFAULT 0,
        start_date TEXT,
        end_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # MIGRATIONS (For existing databases)
    # 1. Add student_id to questions
    try:
        c.execute("ALTER TABLE questions ADD COLUMN student_id TEXT")
        conn.commit()
    except Exception: pass 

    # 2. Add category to questions
    try:
        c.execute("ALTER TABLE questions ADD COLUMN category TEXT DEFAULT 'UNIVERSITY'")
        conn.commit()
    except Exception: pass

    # 4. Add admin tracking fields to questions
    for col_sql in [
        "ALTER TABLE questions ADD COLUMN admin_message_id TEXT",
        "ALTER TABLE questions ADD COLUMN admin_chat_id TEXT",
        "ALTER TABLE questions ADD COLUMN answered_by_name TEXT",
    ]:
        try:
            c.execute(col_sql)
            conn.commit()
        except Exception: pass

    # Fix existing cards: set sort_order based on id if still NULL
    try:
        c.execute("UPDATE service_cards SET sort_order=id WHERE sort_order IS NULL")
        conn.commit()
    except Exception: pass

    # Users table (staff/faculty members who answer questions)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT DEFAULT 'staff',
        faculty_id INTEGER,
        telegram_id TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (faculty_id) REFERENCES faculties(id)
    )''')

    # Super admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        full_name TEXT DEFAULT 'Super Admin',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Student registration table
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        telegram_id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        faculty_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (faculty_id) REFERENCES faculties(id)
    )''')



    # Student questions table
    c.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_telegram_id TEXT NOT NULL,
        student_id TEXT,
        student_username TEXT,
        student_name TEXT,
        faculty_id INTEGER,
        question TEXT NOT NULL,
        answer TEXT,
        answered_by INTEGER,
        status TEXT DEFAULT 'pending',
        lang TEXT DEFAULT 'uz',
        category TEXT DEFAULT 'UNIVERSITY',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        answered_at TEXT,
        FOREIGN KEY (faculty_id) REFERENCES faculties(id),
        FOREIGN KEY (answered_by) REFERENCES users(id)
    )''')

    # FAQ documents per faculty
    c.execute('''CREATE TABLE IF NOT EXISTS faq_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        faculty_id INTEGER,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        created_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (faculty_id) REFERENCES faculties(id)
    )''')


    # Chat groups (Telegram group IDs per faculty)
    c.execute('''CREATE TABLE IF NOT EXISTS chat_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        faculty_id INTEGER NOT NULL,
        group_id TEXT NOT NULL,
        group_name TEXT,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (faculty_id) REFERENCES faculties(id)
    )''')

    conn.commit()

    # Create default super admin if not exists
    c.execute("SELECT id FROM admins WHERE username = 'admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO admins (username, password_hash, full_name) VALUES (?, ?, ?)",
            ('admin', get_password_hash('admin123'), 'Super Admin')
        )
        conn.commit()
        print("Default super admin created: admin / admin123")

    # Create default faculties
    default_faculties = [
        ("Pedagogika fakulteti", "Pedagogika va psixologiya yo'nalishlari"),
        ("Tabiiy fanlar fakulteti", "Matematika, fizika, kimyo yo'nalishlari"),
        ("Ijtimoiy fanlar fakulteti", "Tarix, falsafa, huquq yo'nalishlari"),
        ("Til va adabiyot fakulteti", "O'zbek, rus, ingliz tili yo'nalishlari"),
        ("Axborot texnologiyalari", "Informatika va dasturlash yo'nalishlari"),
    ]
    for name, desc in default_faculties:
        try:
            c.execute("INSERT INTO faculties (name, description) VALUES (?, ?)", (name, desc))
        except:
            pass
    conn.commit()
    conn.close()
    print("Database initialized!")


# ── FACULTY CRUD ──────────────────────────────────────────────────────────────
def get_all_faculties():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM faculties ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_faculty(faculty_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM faculties WHERE id=?", (faculty_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_faculty(name, description="", group_id="", group_name=""):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO faculties (name, description, telegram_group_id, telegram_group_name) VALUES (?,?,?,?)",
            (name, description, group_id, group_name)
        )
        conn.commit()
        return True, "Faculty yaratildi"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_faculty(faculty_id, name, description, group_id, group_name):
    conn = get_conn()
    conn.execute(
        "UPDATE faculties SET name=?, description=?, telegram_group_id=?, telegram_group_name=? WHERE id=?",
        (name, description, group_id, group_name, faculty_id)
    )
    conn.commit()
    conn.close()

def delete_faculty(faculty_id):
    conn = get_conn()
    conn.execute("UPDATE faculties SET is_active=0 WHERE id=?", (faculty_id,))
    conn.commit()
    conn.close()


# ── USER CRUD ─────────────────────────────────────────────────────────────────
def get_all_users():
    conn = get_conn()
    rows = conn.execute("""
        SELECT u.*, f.name as faculty_name
        FROM users u LEFT JOIN faculties f ON u.faculty_id=f.id
        ORDER BY u.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_by_phone(phone):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE phone=? AND is_active=1", (phone,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_user(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(phone, password, full_name, faculty_id, role='staff'):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (phone, password_hash, full_name, faculty_id, role) VALUES (?,?,?,?,?)",
            (phone, get_password_hash(password), full_name, faculty_id, role)
        )
        conn.commit()
        return True, "Foydalanuvchi yaratildi"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def update_user(user_id, full_name, faculty_id, role, is_active):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET full_name=?, faculty_id=?, role=?, is_active=? WHERE id=?",
        (full_name, faculty_id, role, is_active, user_id)
    )
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = get_conn()
    conn.execute("UPDATE users SET is_active=0 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def verify_user(phone, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE phone=? AND is_active=1",
        (phone,)
    ).fetchone()
    conn.close()
    if row and verify_password(password, row['password_hash']):
        return dict(row)
    return None


# ── ADMIN AUTH ────────────────────────────────────────────────────────────────
def verify_admin(username, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM admins WHERE username=?",
        (username,)
    ).fetchone()
    conn.close()
    if row and verify_password(password, row['password_hash']):
        return dict(row)
    return None


# ── STUDENTS ──────────────────────────────────────────────────────────────────
def get_student(tg_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM students WHERE telegram_id=?", (str(tg_id),)).fetchone()
    conn.close()
    return dict(row) if row else None

def register_student(tg_id, student_id, faculty_id=None):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO students (telegram_id, student_id, faculty_id, created_at) VALUES (?,?,?,?)",
            (str(tg_id), str(student_id), faculty_id, get_now_uz())
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# ── QUESTIONS ─────────────────────────────────────────────────────────────────
def save_question(student_tg_id, student_id, student_username, student_name, faculty_id, question, answer, lang, category):
    conn = get_conn()
    is_wait = "javobini kuting" in answer.lower() or "murojaat qiling" in answer.lower()
    is_not_found = "topilmadi" in answer.lower() or "not found" in answer.lower()
    
    # It's only 'answered' if it's NOT a wait message AND NOT a 'not found' message
    status = 'unanswered' if (is_wait or is_not_found or category == "MANUAL") else 'answered'

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO questions
        (student_telegram_id, student_id, student_username, student_name, faculty_id, question, answer, status, lang, category, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        str(student_tg_id), student_id, student_username, student_name, faculty_id,
        question, answer, status, lang, category, get_now_uz()
    ))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_questions(faculty_id=None, status=None, limit=50):
    conn = get_conn()
    query = """
        SELECT q.*, f.name as faculty_name
        FROM questions q LEFT JOIN faculties f ON q.faculty_id=f.id
        WHERE 1=1
    """
    params = []
    if faculty_id:
        query += " AND q.faculty_id=?"
        params.append(faculty_id)
    if status:
        query += " AND q.status=?"
        params.append(status)
    query += " ORDER BY q.created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_question(qid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_question_answer(qid, answer, answered_by=None):
    conn = get_conn()
    conn.execute("""
        UPDATE questions 
        SET answer=?, status='answered', answered_by=?, answered_at=CURRENT_TIMESTAMP 
        WHERE id=?
    """, (answer, answered_by, qid))
    conn.commit()
    conn.close()

def get_stats_db():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    answered = conn.execute("SELECT COUNT(*) FROM questions WHERE status='answered'").fetchone()[0]
    unanswered = conn.execute("SELECT COUNT(*) FROM questions WHERE status='unanswered'").fetchone()[0]
    users = conn.execute("SELECT COUNT(DISTINCT student_telegram_id) FROM questions").fetchone()[0]
    faculties = conn.execute("SELECT COUNT(*) FROM faculties WHERE is_active=1").fetchone()[0]
    staff = conn.execute("SELECT COUNT(*) FROM users WHERE is_active=1").fetchone()[0]

    # Daily stats last 7 days
    rows = conn.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as cnt
        FROM questions
        WHERE created_at >= DATE('now', '-7 days')
        GROUP BY day ORDER BY day
    """).fetchall()
    daily = {r['day']: r['cnt'] for r in rows}

    # Lang stats
    rows2 = conn.execute("SELECT lang, COUNT(*) as cnt FROM questions GROUP BY lang").fetchall()
    langs = {r['lang']: r['cnt'] for r in rows2}

    # Category stats
    rows3 = conn.execute("SELECT category, COUNT(*) as cnt FROM questions GROUP BY category").fetchall()
    cats = {r['category']: r['cnt'] for r in rows3}

    conn.close()
    return {
        "total": total, "answered": answered, "unanswered": unanswered,
        "users": users, "faculties": faculties, "staff": staff,
        "daily": daily, "langs": langs, "categories": cats
    }


# ── FAQ ITEMS ─────────────────────────────────────────────────────────────────
def get_faq_items(faculty_id=None):
    conn = get_conn()
    if faculty_id:
        rows = conn.execute(
            "SELECT * FROM faq_items WHERE faculty_id=? AND is_active=1 ORDER BY id DESC", (faculty_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT f.*, fc.name as faculty_name FROM faq_items f LEFT JOIN faculties fc ON f.faculty_id=fc.id WHERE f.is_active=1 ORDER BY f.id DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_faq_item(faculty_id, question, answer):
    conn = get_conn()
    conn.execute(
        "INSERT INTO faq_items (faculty_id, question, answer, created_at) VALUES (?,?,?,?)",
        (faculty_id, question, answer, get_now_uz())
    )
    conn.commit()
    conn.close()

def delete_faq_item(item_id):
    conn = get_conn()
    conn.execute("UPDATE faq_items SET is_active=0 WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


# ── SERVICE CARDS ─────────────────────────────────────────────────────────────
def get_service_cards(only_active=True, faculty_id=None):
    """Get cards filtered by active status, faculty, and date range."""
    conn = get_conn()
    from datetime import date
    today = date.today().isoformat()
    conditions = []
    params = []

    if only_active:
        conditions.append("sc.is_active=1")
        # Date range filter: show if no dates set, or today is within range
        conditions.append("(sc.start_date IS NULL OR sc.start_date <= ?)")
        params.append(today)
        conditions.append("(sc.end_date IS NULL OR sc.end_date >= ?)")
        params.append(today)

    if faculty_id is not None:
        conditions.append("(sc.faculty_id IS NULL OR sc.faculty_id=?)")
        params.append(faculty_id)

    q = "SELECT sc.*, f.name as faculty_name FROM service_cards sc LEFT JOIN faculties f ON sc.faculty_id=f.id"
    if conditions:
        q += " WHERE " + " AND ".join(conditions)
    q += " ORDER BY COALESCE(sort_order, 0) ASC, sc.id DESC"

    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_service_card(title, description, icon, link, type='message',
                     faculty_id=None, sort_order=0, start_date=None, end_date=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO service_cards (title, description, icon, link, type, faculty_id, sort_order, start_date, end_date, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (title, description, icon, link, type, faculty_id, sort_order, start_date, end_date, get_now_uz())
    )
    conn.commit()
    conn.close()

def update_service_card(card_id, title, description, icon, link, type, is_active,
                        faculty_id=None, sort_order=0, start_date=None, end_date=None):
    conn = get_conn()
    conn.execute("""
        UPDATE service_cards
        SET title=?, description=?, icon=?, link=?, type=?, is_active=?,
            faculty_id=?, sort_order=?, start_date=?, end_date=?
        WHERE id=?
    """, (title, description, icon, link, type, is_active,
           faculty_id or None, sort_order or 0, start_date or None, end_date or None, card_id))
    conn.commit()
    conn.close()

def reorder_service_card(card_id, direction):
    """Move card up or down by swapping sort_order with neighbor."""
    conn = get_conn()
    current = conn.execute("SELECT sort_order FROM service_cards WHERE id=?", (card_id,)).fetchone()
    if not current:
        conn.close()
        return
    cur_order = current['sort_order'] or 0
    if direction == 'up':
        neighbor = conn.execute(
            "SELECT id, sort_order FROM service_cards WHERE sort_order < ? ORDER BY sort_order DESC LIMIT 1",
            (cur_order,)
        ).fetchone()
    else:
        neighbor = conn.execute(
            "SELECT id, sort_order FROM service_cards WHERE sort_order > ? ORDER BY sort_order ASC LIMIT 1",
            (cur_order,)
        ).fetchone()
    if neighbor:
        conn.execute("UPDATE service_cards SET sort_order=? WHERE id=?", (neighbor['sort_order'], card_id))
        conn.execute("UPDATE service_cards SET sort_order=? WHERE id=?", (cur_order, neighbor['id']))
        conn.commit()
    conn.close()

def delete_service_card(card_id):
    conn = get_conn()
    conn.execute("DELETE FROM service_cards WHERE id=?", (card_id,))
    conn.commit()
    conn.close()

def link_admin_message(qid, chat_id, message_id):
    conn = get_conn()
    conn.execute("UPDATE questions SET admin_chat_id=?, admin_message_id=? WHERE id=?", 
                 (str(chat_id), str(message_id), qid))
    conn.commit()
    conn.close()

def get_student_history(student_tg_id, limit=30):
    """
    Returns a student's past Q&A history ordered oldest→newest.
    Excludes internal __ADMIN_FOLLOW_UP__ placeholder rows.
    Used by the mini app chat to show unified history across bot + web.
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, question, answer, status, category, lang, created_at, answered_at
        FROM questions
        WHERE student_telegram_id = ?
          AND question != '__ADMIN_FOLLOW_UP__'
        ORDER BY created_at ASC
        LIMIT ?
    """, (str(student_tg_id), limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_question_by_admin_message(chat_id, message_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM questions WHERE admin_chat_id=? AND admin_message_id=?", 
                       (str(chat_id), str(message_id))).fetchone()
    conn.close()
    return dict(row) if row else None

def update_question_answer_tg(qid, answer, tg_id, tg_name):
    conn = get_conn()
    conn.execute("""
        UPDATE questions 
        SET answer=?, status='answered', answered_by=?, answered_by_name=?, answered_at=CURRENT_TIMESTAMP 
        WHERE id=?
    """, (answer, f"TG:{tg_id}", tg_name, qid))
    conn.commit()
    conn.close()




if __name__ == "__main__":
    init_db()
