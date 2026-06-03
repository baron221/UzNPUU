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

def naive_uz_stem(text: str) -> list:
    import re
    words = []
    for w in text.split():
        w_clean = re.sub(r'[^\w]', '', w.lower())
        if len(w_clean) > 4:
            words.append(w_clean[:4])
        elif len(w_clean) > 2:
            words.append(w_clean)
    return list(set(words))

def find_relevant_pairs(question: str, pairs: list, client, top_n: int = 5) -> str:
    import vector_store
    
    # 1. Semantic Search using Vector Store (ChromaDB)
    semantic_context = vector_store.search_vector_db(question, n_results=10)
    
    # 2. Keyword Search over 'pairs' (Crucial for UZ text and DB items)
    q_words = naive_uz_stem(question)
    scored_pairs = []
    for p in pairs:
        score = 0
        p_text = (p['question'] + " " + p['answer']).lower()
        for w in q_words:
            if w in p_text:
                score += 1
        if score > 0:
            scored_pairs.append((score, p))
            
    scored_pairs.sort(key=lambda x: x[0], reverse=True)
    keyword_context = "\n\n---\n\n".join(
        f"Savol: {p['question']}\nJavob: {p['answer']}" 
        for score, p in scored_pairs[:5]
    )
    
    combined_context = f"{semantic_context}\n\n---\n\n{keyword_context}"
    
    if not combined_context.strip().replace("---", "").strip():
        return ""

    # 3. AI Re-ranking (Groq)
    try:
        check = safe_completion(
            client,
            messages=[
                {"role": "system", "content": f"You are a search assistant. Below are several document chunks. Return ONLY the {top_n} most relevant chunks as a single concatenated string. If a chunk is not relevant to the user question, ignore it.\n\nCHUNKS:\n{combined_context}"},
                {"role": "user", "content": f"Student question: {question}"}
            ],
            max_tokens=1024,
        )
        return check.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Reranking failed: {e}")
        return combined_context


def safe_completion(client, **kwargs):
    """Attempt a completion with fallback model support."""
    primary_model = "llama-3.3-70b-versatile"
    fallback_model = "llama-3.1-8b-instant"
    
    if 'temperature' not in kwargs:
        kwargs['temperature'] = 0.1
    
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

def transcribe_audio(file_path: str, client) -> str:
    """Uses Groq Whisper API to transcribe audio file to text."""
    with open(file_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(file_path), file.read()),
            model="whisper-large-v3", # or whisper-large-v3-turbo
            response_format="json",
            language="uz", # Helps with Uzbek specifically
        )
        return transcription.text

def classify_question(question: str, client) -> tuple:
    try:
        check = safe_completion(
            client,
            messages=[
                {"role": "system", "content": """Classify into: GENERAL (chit-chat, greeting, general thanks, hello), VAGUE (unclear short words about university, e.g. 'contract', 'exam', 'schedule'), or UNIVERSITY (specific academic/university questions).
Any questions mentioning university schedules, dars jadvali, imtihonlar, to'lovlar, stipendiya, dekanat, yotoqxona should be classified as UNIVERSITY or VAGUE (never GENERAL).
Also provide a 1-word topic for the question (e.g. Imtihon, Kredit, Tolov, Yotoqxona, Boshqa).
Format: CATEGORY|Topic"""},
                {"role": "user", "content": question}
            ],
            max_tokens=20,
        )
        result = check.choices[0].message.content.strip()
        parts = result.split('|')
        cat = parts[0].strip().upper()
        topic = parts[1].strip().capitalize() if len(parts) > 1 else "Boshqa"
        
        if "GENERAL" in cat: return "GENERAL", topic
        if "VAGUE" in cat: return "VAGUE", topic
        return "UNIVERSITY", topic
    except:
        return "UNIVERSITY", "Boshqa"

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
    q_words = naive_uz_stem(question)
    
    if not q_words:
        return []

    scored_matches = []
    for p in pairs:
        p_q_lower = p['question'].lower()
        score = sum(1 for w in q_words if w in p_q_lower)
        if score > 0:
            label = clean_label(p['question'])
            scored_matches.append((score, label))
    
    # Sort by score (descending)
    scored_matches.sort(key=lambda x: x[0], reverse=True)
    
    seen = set()
    options = []
    for score, m in scored_matches:
        if m not in seen:
            seen.add(m)
            options.append(m)
        if len(options) == 6: break # Show up to 6 options
    return options

_cached_pairs = None

def get_answer(question: str, knowledge_base: str, clients: dict, faculty_id: Optional[int] = None) -> tuple:
    """Returns (answer_text, options_list, lang, category, topic)"""
    global _cached_pairs
    client = clients["groq"]

    # Detect language
    lang = detect_lang(question)

    # NEW: Cross-lingual search support
    # If the question is not in Uzbek, create an internal Uzbek translation for search purposes
    search_query = question
    if lang != 'uz' and len(question.split()) > 1:
        try:
            translation = safe_completion(
                client,
                messages=[
                    {"role": "system", "content": "Translate the user question to UZBEK for internal university database search. Return ONLY the translation, no extra text."},
                    {"role": "user", "content": question}
                ],
                max_tokens=256
            )
            search_query = translation.choices[0].message.content.strip()
            logging.info(f"[CROSS-LINGUAL] Translated '{question[:30]}' to '{search_query[:30]}'")
        except Exception as e:
            logging.error(f"[CROSS-LINGUAL-ERR] {e}")
            pass

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
    # 1. Exact Match Check (to break infinite option loops)
    clean_q_exact = question.strip().lower()
    for pair in all_pairs:
        # Compare against the cleaned label to match the generated options
        if clean_q_exact == clean_label(pair['question']).strip().lower():
            logging.info(f"[EXACT-MATCH][{lang}] {question[:50]}")
            return pair['answer'], [], lang, "UNIVERSITY", "Boshqa"

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
    vague_stems = set()
    for kw in VAGUE_KEYWORDS:
        vague_stems.update(naive_uz_stem(kw))
    
    q_stems = set(naive_uz_stem(question))
    is_short = len(q_words) <= 1
    has_vague_kw = bool(q_stems & vague_stems)

    # Only trigger options if it's a single word OR a 2-word vague phrase
    if is_short or (len(q_words) <= 2 and has_vague_kw):
        options = generate_options(search_query, all_pairs)
        if options:
            logging.info(f"[VAGUE-FAST][{lang}] '{question[:40]}' → {len(options)} options")
            return get_response("clarify", lang), options, lang, "VAGUE", "Boshqa"
        # No options found → fall through to full Groq classification

    category, topic = classify_question(question, client)
    logging.info(f"[{category}][{lang}][FID:{faculty_id}] {question[:50]} (Topic: {topic})")

    # ── GENERAL / CONVERSATIONAL ──────────────────────────────────────────────
    if category == "GENERAL":
        q = question.lower().strip()
        if any(w in q for w in ["assalomu","salom","hello","hi","hey","привет","здравствуйте"]):
            return get_response("greeting", lang), [], lang, "GENERAL", topic
        if any(w in q for w in ["rahmat","tashakkur","спасибо","thanks","thank"]):
            return get_response("thanks", lang), [], lang, "GENERAL", topic
        if any(w in q for w in ["xayr","bye","goodbye","пока"]):
            return get_response("bye", lang), [], lang, "GENERAL", topic
        try:
            completion = safe_completion(
                client,
                messages=[
                    {"role": "system", "content": f"""You are the NPUU University Assistant.
The user is asking a general or conversational question (not a specific academic one).
Reply politely, concisely, and in the student's language ({lang}).
If they want to speak to an admin, tell them you can help with most info from documents, but an admin will reply soon in this chat if needed."""},
                    {"role": "user", "content": question}
                ],
                max_tokens=256,
            )
            return completion.choices[0].message.content.strip(), [], lang, "GENERAL", topic
        except:
            return get_response("error", lang), [], lang, "ERROR", "Boshqa"

    # ── VAGUE (Groq-classified) ───────────────────────────────────────────────
    elif category == "VAGUE":
        options = generate_options(search_query, all_pairs)
        if options:
            return get_response("clarify", lang), options, lang, "VAGUE", topic
        category = "UNIVERSITY"


    # ── UNIVERSITY ────────────────────────────────────────────────────────────
    if category == "UNIVERSITY":
        # 3. AI Search with context
        context = find_relevant_pairs(search_query, all_pairs, client)
        if not context:
            logging.warning(f"[NO-CONTEXT] {question[:50]}")
            return "Hujjatda bunday ma'lumot topilmadi", [], lang, "UNIVERSITY", topic

        logging.info(f"[AI-SEARCH] Context found for: {question[:50]}")
        relevant_context = context

        if not relevant_context.strip():
            # Use standardized polite response when no documents are matched
            return get_response("not_found", lang), [], lang, "UNANSWERED", topic

        # Check if user asked in Cyrillic Uzbek specifically
        has_uz_cyrillic = lang == 'uz' and any('\u0400' <= c <= '\u04ff' for c in question)
        
        if has_uz_cyrillic:
            lang_instruction = "Javobni O'ZBEK tilida, lekin albatta KIRIEL (КИРИЛЛ) alifbosida bering (masalan: лотин эмас, кирилл ҳарфлари билан)."
        else:
            lang_instruction = {
                "uz": "Javobni O'ZBEK tilida bering.",
                "ru": "Отвечайте на РУССКОМ языке.",
                "en": "Answer in ENGLISH."
            }.get(lang, "Answer in Uzbek.")

        try:
            completion = safe_completion(
                client,
                messages=[
                    {"role": "system", "content": f"""You are a strict document-based university assistant for NPUU.
RULES:
1. Answer ONLY using the facts from the DOCUMENTS below. Do NOT use outside knowledge.
2. If the answer is not clearly found in the DOCUMENTS, you MUST reply EXACTLY with: NOT_FOUND
3. {lang_instruction}
4. Be concise and helpful. Use bullet points if appropriate.

=== DOCUMENTS ===
{relevant_context}"""},
                    {"role": "user", "content": f"Student Question: {question}"}
                ],
                max_tokens=1024,
            )
            
            ans = completion.choices[0].message.content.strip()
            
            # Strict fallback check
            if "NOT_FOUND" in ans.upper() or len(ans) < 5:
                return get_response("not_found", lang), [], lang, "UNANSWERED", topic
                
            return ans, [], lang, "UNIVERSITY", topic
        except:
            return get_response("error", lang), [], lang, "ERROR", "Boshqa"

    return get_response("error", lang), [], lang, "ERROR", "Boshqa"
