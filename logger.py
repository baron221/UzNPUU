"""
logger.py — In-memory log store shared between bot and server.
Works on Railway where bot and server run in the same process via main.py.
"""
import os
import json
from datetime import datetime, date, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "logs", "chat_logs.json")

# In-memory store — shared when running via main.py
_logs = []
_loaded = False


def _load_from_file():
    global _logs, _loaded
    if _loaded:
        return
    _loaded = True
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                _logs = json.load(f)
            print(f"📂 Loaded {len(_logs)} existing logs")
    except Exception as e:
        print(f"⚠️ Could not load logs: {e}")
        _logs = []


def _save_to_file():
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(_logs[-1000:], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save logs: {e}")


def log_message(user_id, username, question, answer, lang, category):
    global _logs
    _load_from_file()

    _logs.append({
        "id": len(_logs) + 1,
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "user_id": str(user_id),
        "username": username or "Anonymous",
        "question": question,
        "answer": answer,
        "lang": lang,
        "category": category,
        "answered": "topilmadi" not in answer.lower() and "not found" not in answer.lower()
    })

    # Keep last 1000
    if len(_logs) > 1000:
        _logs = _logs[-1000:]

    _save_to_file()
    print(f"📝 Logged [{lang}]: {question[:40]}...")


def get_logs():
    _load_from_file()
    return _logs


def get_stats():
    _load_from_file()
    logs = _logs

    if not logs:
        return {
            "total": 0, "answered": 0, "unanswered": 0,
            "users": 0, "langs": {}, "categories": {}, "daily": {}
        }

    answered = sum(1 for l in logs if l.get("answered", True))
    users = len(set(l["user_id"] for l in logs))

    langs = {}
    for l in logs:
        lg = l.get("lang", "uz")
        langs[lg] = langs.get(lg, 0) + 1

    categories = {}
    for l in logs:
        cat = l.get("category", "UNIVERSITY")
        categories[cat] = categories.get(cat, 0) + 1

    daily = {}
    for l in logs:
        d = l.get("date", "")
        if d:
            daily[d] = daily.get(d, 0) + 1

    last7 = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    daily_chart = {d: daily.get(d, 0) for d in last7}

    return {
        "total": len(logs),
        "answered": answered,
        "unanswered": len(logs) - answered,
        "users": users,
        "langs": langs,
        "categories": categories,
        "daily": daily_chart,
        "recent": logs[-10:][::-1]
    }