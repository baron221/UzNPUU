import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "logs", "chat_logs.json")

def ensure_log_file():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)

def log_message(user_id: str, username: str, question: str, answer: str, lang: str, category: str):
    ensure_log_file()
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except:
        logs = []

    logs.append({
        "id": len(logs) + 1,
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

    logs = logs[-1000:]
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
    print(f"📝 Logged: {question[:40]}...")

def get_logs():
    ensure_log_file()
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def get_stats():
    logs = get_logs()
    if not logs:
        return {"total": 0, "answered": 0, "unanswered": 0, "users": 0, "langs": {}, "categories": {}, "daily": {}}

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

    from datetime import date, timedelta
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