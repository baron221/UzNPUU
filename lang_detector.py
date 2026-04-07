"""
lang_detector.py — Detects language of student message.
Supports: Uzbek (uz), Russian (ru), English (en)
"""

UZ_WORDS = ["qanday","qachon","nima","kim","necha","qayerda","uchun","bilan","yoki","ham","va","lekin","salom","assalomu","rahmat","xayr","talaba","imtihon","jadval","stipendiya","grant","kredit","hemis","dars","kontrakt","tolov","fakultet"]
RU_WORDS = ["как","когда","что","кто","сколько","где","для","привет","спасибо","пока","студент","экзамен","расписание","стипендия","грант","кредит","договор","оплата","факультет","здравствуйте","можно","нужно","хочу"]
EN_WORDS = ["how","when","what","who","where","why","hello","hi","thanks","bye","student","exam","schedule","stipend","grant","credit","contract","payment","faculty","please","need","want","can"]

def detect_lang(text: str) -> str:
    text_lower = text.lower()
    words = text_lower.split()

    uz_score = sum(1 for w in words if w in UZ_WORDS)
    ru_score = sum(1 for w in words if w in RU_WORDS)
    en_score = sum(1 for w in words if w in EN_WORDS)

    # Check Cyrillic script → likely Russian
    cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
    # Check Latin script → likely Uzbek or English
    latin = sum(1 for c in text if c.isalpha() and c.isascii())

    if ru_score > uz_score and ru_score > en_score:
        return "ru"
    if en_score > uz_score and en_score > ru_score:
        return "en"
    if cyrillic > latin * 0.5:
        return "ru"
    return "uz"  # default to Uzbek


# ── Language-specific responses ───────────────────────────────────────────────
RESPONSES = {
    "not_found": {
        "uz": "Kechirasiz, bu savol bo'yicha hujjatlarimda ma'lumot topilmadi. Iltimos, universitet ofisiga murojaat qiling. 🏫",
        "ru": "Извините, информация по этому вопросу не найдена в наших документах. Пожалуйста, обратитесь в офис университета. 🏫",
        "en": "Sorry, I couldn't find information about this in our documents. Please contact the university office. 🏫"
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
        "uz": "Vaalaykum assalom! 😊 UzNPUU botiga xush kelibsiz. Savolingizni yozing!",
        "ru": "Здравствуйте! 😊 Добро пожаловать в бот UzNPUU. Задайте ваш вопрос!",
        "en": "Hello! 😊 Welcome to the UzNPUU bot. Type your question!"
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
        "uz": "Men UzNPUU rasmiy yordamchi botiman! 🎓\n\n• 📅 Imtihon va dars jadvallari\n• 📚 HEMIS tizimi\n• 📋 Akademik ta'til va ko'chirish\n• 💰 To'lov va stipendiya\n• 🎓 Grant va GPA",
        "ru": "Я официальный бот-помощник UzNPUU! 🎓\n\n• 📅 Расписание экзаменов и занятий\n• 📚 Система HEMIS\n• 📋 Академический отпуск и перевод\n• 💰 Оплата и стипендия\n• 🎓 Гранты и GPA",
        "en": "I'm the official UzNPUU assistant bot! 🎓\n\n• 📅 Exam and class schedules\n• 📚 HEMIS system\n• 📋 Academic leave and transfers\n• 💰 Payments and scholarships\n• 🎓 Grants and GPA"
    },
    "howru": {
        "uz": "Yaxshi, rahmat! 😊 Sizga qanday yordam bera olaman?",
        "ru": "Хорошо, спасибо! 😊 Чем могу помочь?",
        "en": "I'm doing great, thanks! 😊 How can I help you?"
    },
    "error": {
        "uz": "Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
        "ru": "Произошла ошибка. Пожалуйста, попробуйте снова.",
        "en": "An error occurred. Please try again."
    }
}

def get_response(key: str, lang: str) -> str:
    return RESPONSES.get(key, {}).get(lang, RESPONSES.get(key, {}).get("uz", ""))
