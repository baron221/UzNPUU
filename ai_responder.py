import os
import re
import logging
from typing import Optional
from groq import Groq
from lang_detector import detect_lang, get_response
import database as db

def setup_ai():
    api_key = os.environ.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not found! Available env vars:", list(os.environ.keys()))
        raise ValueError("GROQ_API_KEY not found! Please set it in Railway Variables tab.")
    client = Groq(api_key=api_key)
    print("Groq AI ready (Llama 3.3-70b) -- Free!")
    return {"groq": client}

def chunk_knowledge_base(knowledge_base: str, chunk_size: int = 500) -> list:
    chunks = []
    overlap = 100
    start = 0
    while start < len(knowledge_base):
        end = start + chunk_size
        chunk = knowledge_base[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def parse_qa_pairs(knowledge_base: str) -> list:
    pairs = []
    blocks = re.split(
        r'(?=\d+[\.\)]\s*(?:Savol|savol)?[:.\s])|(?=(?:Savol|SAVOL)\s*[:.\n])',
        knowledge_base
    )
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        match = re.split(r'(?:Javob|JAVOB|javob)\s*[:.\n]', block, maxsplit=1)
        if len(match) == 2:
            question_part = re.sub(r'^\d+[\.\)]\s*(?:Savol|savol)?\s*[:.\n]?', '', match[0]).strip()
            answer_part = match[1].strip()
            if question_part and answer_part:
                pairs.append({"question": question_part, "answer": answer_part})
        else:
            if len(block) > 30:
                pairs.append({"question": block[:200], "answer": block})
    print(f"Parsed {len(pairs)} Q&A pairs from documents")
    return pairs

def find_relevant_chunks(question: str, chunks: list, client, top_n: int = 5) -> str:
    if not chunks:
        return ""
    index = "\n".join(f"[{i}] {chunk[:120].strip().replace(chr(10), ' ')}..." for i, chunk in enumerate(chunks))
    check = safe_completion(
        client,
        messages=[
            {"role": "system", "content": f"Return ONLY the {top_n} most relevant chunk numbers as comma-separated. Example: 2,7,12\nCHUNKS:\n{index}"},
            {"role": "user", "content": f"Question: {question}"}
        ],
        max_tokens=30,
    )
    raw = check.choices[0].message.content.strip()
    try:
        indices = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
        return "\n\n".join(chunks[i] for i in indices if i < len(chunks))
    except:
        return "\n\n".join(chunks[:top_n])

def find_relevant_pairs(question: str, pairs: list, client, top_n: int = 5) -> str:
    if not pairs:
        return ""
    q_lower = question.lower()
    q_words = [w for w in q_lower.split() if len(w) > 2]
    
    # Pre-filter by keyword match
    pre_filtered = []
    if q_words:
        pre_filtered = [(i, p) for i, p in enumerate(pairs)
            if any(word in p['question'].lower() or word in p['answer'].lower()
                   for word in q_words)]
    
    # If we found ANY matches, use them. If not, fallback to all pairs.
    working_pairs = pre_filtered if pre_filtered else list(enumerate(pairs))
    if not working_pairs:
        return ""
        
    # Include both question and a small snippet of the answer so Groq can see context
    filtered_index_lines = []
    for orig_i, p in working_pairs[:80]:
        q_text = p['question'].replace('\n', ' ')[:100]
        a_text = p['answer'].replace('\n', ' ')[:50]
        filtered_index_lines.append(f"[{orig_i}] Q: {q_text} | A: {a_text}...")
        
    filtered_index = "\n".join(filtered_index_lines)
    
    check = safe_completion(
        client,
        messages=[
            {"role": "system", "content": f"Return ONLY the {top_n} most relevant index numbers as comma-separated. If many look relevant, pick the best variety.\nFAQ:\n{filtered_index}"},
            {"role": "user", "content": f"Student question: {question}"}
        ],
        max_tokens=60,
    )
    raw = check.choices[0].message.content.strip()
    try:
        indices = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
        selected = [f"Savol: {pairs[i]['question']}\nJavob: {pairs[i]['answer']}" for i in indices if i < len(pairs)]
        if not selected:
            raise ValueError("No valid indices parsed")
        return "\n\n---\n\n".join(selected)
    except:
        # Fallback if Groq fails parsing
        return "\n\n---\n\n".join(f"Savol: {p['question']}\nJavob: {p['answer']}" for _, p in working_pairs[:top_n])


def safe_completion(client, **kwargs):
    """Attempt a completion with fallback model support."""
    primary_model = "llama-3.3-70b-versatile"
    fallback_model = "llama-3.1-8b-instant"
    
    try:
        kwargs['model'] = primary_model
        return client.chat.completions.create(**kwargs)
    except Exception as e:
        print(f"Primary model ({primary_model}) failed: {e}. Trying fallback...")
        try:
            kwargs['model'] = fallback_model
            return client.chat.completions.create(**kwargs)
        except Exception as e2:
            print(f"Fallback model ({fallback_model}) also failed: {e2}")
            raise e2

def classify_question(question: str, client) -> str:
    try:
        check = safe_completion(
            client,
            messages=[
                {"role": "system", "content": """Classify into: GENERAL, VAGUE, or UNIVERSITY.
GENERAL: greetings, thanks, bye, casual chat, bot questions
VAGUE: single keyword about university (to'lov, imtihon, jadval, stipendiya, HEMIS, оплата, расписание, payment, schedule)
UNIVERSITY: complete question about university
Reply ONE word only."""},
                {"role": "user", "content": question}
            ],
            max_tokens=5,
        )
        result = check.choices[0].message.content.strip().upper()
        if "GENERAL" in result: return "GENERAL"
        if "VAGUE" in result: return "VAGUE"
    except:
        pass
    return "UNIVERSITY"

def clean_label(text: str) -> str:
    """Removes 'Savol:', 'Question:', 'Вопрос:', leading numbers, and dots."""
    # Remove leading numbering like "1.", "1)", etc.
    text = re.sub(r'^\d+[\.\)]\s*', '', text)
    
    # Remove common question prefixes case-insensitively
    prefixes = [
        r'^(?:Savol|SAVOL)\s*[:.\s-]*',
        r'^(?:Question|QUESTION)\s*[:.\s-]*',
        r'^(?:Вопрос|ВОПРОС)\s*[:.\s-]*'
    ]
    for p in prefixes:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
    
    return text.strip()

def generate_options(question: str, pairs: list) -> list:
    q_lower = question.lower().strip()
    matched = []
    for p in pairs:
        if any(word in p['question'].lower() for word in q_lower.split() if len(word) > 2):
            label = clean_label(p['question'])
            if len(label) > 60: label = label[:57] + "..."
            matched.append(label)
    seen = set()
    options = []
    for m in matched:
        if m not in seen:
            seen.add(m)
            options.append(m)
        if len(options) == 4: break
    return options

_cached_pairs = None

def get_answer(question: str, knowledge_base: str, clients: dict, faculty_id: Optional[int] = None) -> tuple:
    """Returns (answer_text, options_list, lang, category)"""
    global _cached_pairs
    client = clients["groq"]

    # Detect language
    lang = detect_lang(question)

    if _cached_pairs is None:
        _cached_pairs = parse_qa_pairs(knowledge_base)

    # Fetch DB FAQ items for CURRENT faculty (plus general if needed)
    db_items = db.get_faq_items(faculty_id)
    # If student is in a specific faculty, also get general FAQ items (where faculty_id is NULL)
    if faculty_id:
        general_items = db.get_faq_items(None)
        # Filter general_items to only those with faculty_id IS NULL 
        # (db.get_faq_items(None) currently returns all active FAQ items, let's refine this if needed)
        # For now, let's just use what we get.
        db_items.extend([i for i in general_items if i.get('faculty_id') is None])

    # Combine document pairs with dynamic DB pairs
    all_pairs = _cached_pairs + [{"question": i['question'], "answer": i['answer']} for i in db_items]

    # ── EXACT MATCH PRE-CHECK (Option button tapped) ──────────────────────────
    # If the question exactly matches a known KB question, answer it directly.
    # This breaks the infinite loop where an option containing a "vague" keyword
    # triggers generate_options() again instead of answering.
    clean_q_exact = question.strip().lower()
    for pair in all_pairs:
        if clean_q_exact == pair['question'].strip().lower():
            logging.info(f"[EXACT-MATCH][{lang}] {question[:50]}")
            return pair['answer'], [], lang, "UNIVERSITY"

    # ── SHORT QUESTION PRE-CHECK (bypass Groq for speed + accuracy) ─────────────
    # If ≤3 words or matches known university keywords → treat as VAGUE first.
    # This prevents Groq from mis-classifying Uzbek/Russian single keywords.
    q_words = question.strip().split()
    VAGUE_KEYWORDS = {
        # Uzbek
        "to'lov", "tolov", "imtihon", "jadval", "stipendiya", "grant", "hemis",
        "kontrakt", "shartnoma", "diplom", "kvitansiya", "gpa", "kredit",
        "dekanat", "rektor", "registrator", "talaba", "kitobxona", "yotoqxona",
        "sport", "kutubxona", "fakultet", "kafedra", "amaliyot", "kurs",
        # Russian
        "оплата", "расписание", "стипендия", "контракт", "диплом", "гпа",
        "общежитие", "библиотека", "факультет", "экзамен", "зачёт",
        # English
        "payment", "schedule", "scholarship", "contract", "diploma", "dormitory",
        "library", "faculty", "exam",
    }
    q_lower_words = set(w.lower().strip(".,!?:;\"'") for w in q_words)
    is_short = len(q_words) <= 3
    has_vague_kw = bool(q_lower_words & VAGUE_KEYWORDS)

    if is_short or has_vague_kw:
        options = generate_options(question, all_pairs)
        if options:
            logging.info(f"[VAGUE-FAST][{lang}] '{question[:40]}' → {len(options)} options")
            return get_response("clarify", lang), options, lang, "VAGUE"
        # No options found → fall through to full Groq classification

    category = classify_question(question, client)
    logging.info(f"[{category}][{lang}][FID:{faculty_id}] {question[:50]}")

    # ── GENERAL / CONVERSATIONAL ──────────────────────────────────────────────
    if category == "GENERAL":
        q = question.lower().strip()
        if any(w in q for w in ["assalomu","salom","hello","hi","hey","привет","здравствуйте"]):
            return get_response("greeting", lang), [], lang, "GENERAL"
        if any(w in q for w in ["rahmat","tashakkur","спасибо","thanks","thank"]):
            return get_response("thanks", lang), [], lang, "GENERAL"
        if any(w in q for w in ["xayr","bye","goodbye","пока"]):
            return get_response("bye", lang), [], lang, "GENERAL"
        try:
            completion = safe_completion(
                client,
                messages=[
                    {"role": "system", "content": f"""You are the UzNPUU University Assistant.
The user is asking a general or conversational question (not a specific academic one).
Reply politely, concisely, and in the student's language ({lang}).
If they want to speak to an admin, tell them you can help with most info from documents, but an admin will reply soon in this chat if needed."""},
                    {"role": "user", "content": question}
                ],
                max_tokens=256,
            )
            return completion.choices[0].message.content.strip(), [], lang, "GENERAL"
        except:
            return get_response("error", lang), [], lang, "ERROR"

    # ── VAGUE (Groq-classified) ───────────────────────────────────────────────
    elif category == "VAGUE":
        options = generate_options(question, all_pairs)
        if options:
            return get_response("clarify", lang), options, lang, "VAGUE"
        category = "UNIVERSITY"


    # ── UNIVERSITY ────────────────────────────────────────────────────────────
    if category == "UNIVERSITY":
        relevant_context = find_relevant_pairs(question, all_pairs, client, top_n=5)
        print(f"Context relevance tokens info used")

        if not relevant_context.strip():
            # Use standardized polite response when no documents are matched
            return get_response("not_found", lang), [], lang, "UNANSWERED"

        lang_instruction = {
            "uz": "Javobni O'ZBEK tilida bering.",
            "ru": "Отвечайте на РУССКОМ языке.",
            "en": "Answer in ENGLISH."
        }.get(lang, "Answer in Uzbek.")

        try:
            completion = safe_completion(
                client,
                messages=[
                    {"role": "system", "content": f"""You are a strict document-based university assistant for UzNPUU.
RULES:
1. Answer ONLY using the documents below. No extra info.
2. If not found: respond with the not-found message.
3. {lang_instruction}
4. Be concise. Use bullet points for lists.

=== DOCUMENTS ===
{relevant_context}"""},
                    {"role": "user", "content": question}
                ],
                max_tokens=1024,
            )
            return completion.choices[0].message.content.strip(), [], lang, "UNIVERSITY"
        except:
            return get_response("error", lang), [], lang, "ERROR"

    return get_response("error", lang), [], lang, "ERROR"
