"""
lang_detector.py — Detects language of student message.
Supports: Uzbek (uz), Russian (ru), English (en)
"""

UZ_WORDS = [
    "qanday","qachon","nima","kim","necha","qayerda","uchun","bilan","yoki","ham","va","lekin","salom","assalomu","rahmat","xayr","talaba","imtihon","jadval","stipendiya","grant","kredit","hemis","dars","kontrakt","tolov","fakultet",
    # Uzbek Cyrillic equivalents
    "кандай","қачон","нима","ким","неча","қаерда","учун","билан","ёки","ҳам","ва","лекин","салом","ассалому","раҳмат","хайр","талаба","имтиҳон","жадвал","стипендия","грант","кредит","ҳемис","дарс","контракт","тўлов","факультет"
]
RU_WORDS = ["как","когда","что","кто","сколько","где","для","привет","спасибо","пока","студент","экзамен","расписание","стипендия","грант","кредит","договор","оплата","факультет","здравствуйте","можно","нужно","хочу"]
EN_WORDS = ["how","when","what","who","where","why","hello","hi","thanks","bye","student","exam","schedule","stipend","grant","credit","contract","payment","faculty","please","need","want","can"]

def detect_lang(text: str) -> str:
    text_lower = text.lower()
    words = text_lower.split()

    uz_score = sum(1 for w in words if w in UZ_WORDS)
    ru_score = sum(1 for w in words if w in RU_WORDS)
    en_score = sum(1 for w in words if w in EN_WORDS)

    # Check Cyrillic script
    cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
    # Check Latin script
    latin = sum(1 for c in text if c.isalpha() and c.isascii())

    if ru_score > uz_score and ru_score > en_score:
        return "ru"
    if en_score > uz_score and en_score > ru_score:
        return "en"
    if uz_score > ru_score:
        return "uz"
    if cyrillic > latin * 0.5:
        # If Cyrillic but we have Uzbek Cyrillic words, it's Uzbek
        if uz_score >= 1:
            return "uz"
        return "ru"
    return "uz"  # default to Uzbek


# ── Language-specific responses ───────────────────────────────────────────────
RESPONSES = {
    "not_found": {
        "uz": "Kechirasiz, bu savol bo'yicha ma'lumot topilmadi. Iltimos, admin javobini kuting... ⏳",
        "ru": "Извините, информация по этому вопросу не найдена. Пожалуйста, ожидайте ответ администратора... ⏳",
        "en": "Sorry, I couldn't find information about this. Please wait for the administrator's reply... ⏳"
    },
    "searching": {
        "uz": "🔍 Hujjatlarimizdan qidirilmoqda...",
        "ru": "🔍 Поиск в наших документах...",
        "en": "🔍 Searching our documents..."
    },
    "clarify": {
        "uz": "Qaysi birini nazarda tutyapsiz? Iltimos, tanlang:",
        "ru": "Что именно вы имеете в виду? Пожалуйста, выберите:",
        "en": "What do you mean exactly? Please choose:"
    },
    "greeting": {
        "uz": "Vaalaykum assalom! 😊 NPUU botiga xush kelibsiz. Savolingizni yozing!",
        "ru": "Здравствуйте! 😊 Добро пожаловать в бот NPUU. Задайте ваш вопрос!",
        "en": "Hello! 😊 Welcome to the NPUU bot. Type your question!"
    },
    "thanks": {
        "uz": "Arzimaydi! 😊 Yana savollaringiz bo'lsa, yozing.",
        "ru": "Пожалуйста! 😊 Если есть ещё вопросы, пишите.",
        "en": "You're welcome! 😊 Feel free to ask more questions."
    },
    "bye": {
        "uz": "Xayr! 👋 Yana murojaat qilishingiz mumkin.",
        "ru": "До свидания! 👋 Обращайтесь в любое время.",
        "en": "Goodbye! 👋 Feel free to come back anytime."
    },
    "whoami": {
        "uz": "Men NPUU rasmiy yordamchi botiman! 🎓\n\n• 📅 Imtihon va dars jadvallari\n• 📚 HEMIS tizimi\n• 📋 Akademik ta'til va ko'chirish\n• 💰 To'lov va stipendiya\n• 🎓 Grant va GPA",
        "ru": "Я официальный бот-помощник NPUU! 🎓\n\n• 📅 Расписание экзаменов и занятий\n• 📚 Система HEMIS\n• 📋 Академический отпуск и перевод\n• 💰 Оплата и стипендия\n• 🎓 Гранты и GPA",
        "en": "I'm the official NPUU assistant bot! 🎓\n\n• 📅 Exam and class schedules\n• 📚 HEMIS system\n• 📋 Academic leave and transfers\n• 💰 Payments and scholarships\n• 🎓 Grants and GPA"
    },
    "howru": {
        "uz": "Yaxshi, rahmat! 😊 Sizga qanday yordam bera olaman?",
        "ru": "Хорошо, спасибо! 😊 Чем могу помочь?",
        "en": "I'm doing great, thanks! 😊 How can I help you?"
    },
    "error": {
        "uz": "Kechirasiz, tizimda vaqtinchalik texnik cheklov yuz berdi. Savolingizni administratorga yuborishingiz mumkin:",
        "ru": "Извините, произошел временный технический сбой. Вы можете отправить свой вопрос администратору:",
        "en": "Sorry, a temporary technical limitation occurred. You can forward your question to the administrator:"
    }
}

def get_response(key: str, lang: str) -> str:
    return RESPONSES.get(key, {}).get(lang, RESPONSES.get(key, {}).get("uz", ""))
