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
                if len(block) > 800:
                    chunks = chunk_knowledge_base(block, chunk_size=500)
                    for chunk in chunks:
                        pairs.append({"question": chunk[:200], "answer": chunk})
                else:
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
    semantic_context = vector_store.search_vector_db(question, n_results=3)
    
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
        for score, p in scored_pairs[:3]
    )
    
    combined_context = f"{semantic_context}\n\n---\n\n{keyword_context}"
    
    # Truncate context if it is extremely large to prevent exceeding Groq TPM limits
    if len(combined_context) > 6000:
        combined_context = combined_context[:6000] + "\n... (matn kesib tashlandi)"
        
    if not combined_context.strip().replace("---", "").replace("... (matn kesib tashlandi)", "").strip():
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

def strip_greeting(text: str) -> str:
    # Patterns for greetings at the beginning of the text
    patterns = [
        r'^(?:assalomu\s+alaykum(?:\s+va\s+rahmatullohi\s+va\s+barakatuh)?|assalomualaykum|assalom\s+alaykum|assalomalekum|assalom|salom|salam)\b[,\s!.]*',
        r'^(?:va\s+alaykum\s+assalom|valaykum\s+assalom|vaalaykum\s+assalom|valaykumassalom)\b[,\s!.]*',
        r'^(?:hello|hi|hey|привет|здравствуйте|добрый\s+день|доброе\s+утро|добрый\s+вечер)\b[,\s!.]*'
    ]
    cleaned = text.strip()
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def analyze_user_query(question: str, client) -> dict:
    try:
        check = safe_completion(
            client,
            messages=[
                {"role": "system", "content": """You are an advanced query analysis assistant for a Uzbek university bot.
Analyze the user's message and output a JSON object with:
1. "category": GENERAL (chit-chat, greeting, general thanks), VAGUE (unclear short words about university, e.g. 'contract', 'exam'), or UNIVERSITY (specific academic/university questions).
2. "topic": A 1-word topic (e.g. Imtihon, Kredit, Tolov, Yotoqxona, Boshqa).
3. "search_query": The core academic search query in UZBEK, removing conversational fluff, greetings, personal intros ("men 1-kursman", etc.). If it's already a simple search term, keep it.

Example 1: "Assalomu alaykum, men 1-kurs talabasiman, dars jadvalini qayerdan topsam bo'ladi?"
Output: {"category": "UNIVERSITY", "topic": "Jadval", "search_query": "dars jadvali"}

Example 2: "kontrakt"
Output: {"category": "VAGUE", "topic": "Tolov", "search_query": "kontrakt"}

Example 3: "rahmat kattakon"
Output: {"category": "GENERAL", "topic": "Boshqa", "search_query": "rahmat"}

Respond ONLY with the JSON object."""},
                {"role": "user", "content": question}
            ],
            max_tokens=150,
            response_format={"type": "json_object"}
        )
        import json
        res = json.loads(check.choices[0].message.content.strip())
        return {
            "category": res.get("category", "UNIVERSITY").strip().upper(),
            "topic": res.get("topic", "Boshqa").strip().capitalize(),
            "search_query": res.get("search_query", question).strip()
        }
    except Exception as e:
        logging.error(f"Error in analyze_user_query: {e}")
        # Fallback
        return {
            "category": "UNIVERSITY",
            "topic": "Boshqa",
            "search_query": question
        }

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

    # 1. Clean greeting prefixes from the question
    cleaned_question = strip_greeting(question)
    if not cleaned_question:
        # It's a pure greeting
        return get_response("greeting", lang), [], lang, "GENERAL", "Boshqa"

    # 2. Check if it's conversational thanks/bye
    q_lower = cleaned_question.lower()
    if any(w in q_lower for w in ["rahmat","tashakkur","спасибо","thanks","thank"]):
        return get_response("thanks", lang), [], lang, "GENERAL", "Boshqa"
    if any(w in q_lower for w in ["xayr","bye","goodbye","пока"]):
        return get_response("bye", lang), [], lang, "GENERAL", "Boshqa"

    if _cached_pairs is None:
        _cached_pairs = parse_qa_pairs(knowledge_base)

    # Fetch DB FAQ items for CURRENT faculty (plus general if needed)
    db_items = db.get_faq_items(faculty_id)
    if faculty_id:
        general_items = db.get_faq_items(None)
        db_items.extend([i for i in general_items if i.get('faculty_id') is None])

    # Combine document pairs with dynamic DB pairs
    all_pairs = _cached_pairs + [{"question": i['question'], "answer": i['answer']} for i in db_items]

    # ── EXACT MATCH PRE-CHECK (Option button tapped) ──────────────────────────
    clean_q_exact = question.strip().lower()
    for pair in all_pairs:
        if clean_q_exact == clean_label(pair['question']).strip().lower():
            logging.info(f"[EXACT-MATCH][{lang}] {question[:50]}")
            return pair['answer'], [], lang, "UNIVERSITY", "Boshqa"

    # ── SHORT QUESTION PRE-CHECK (bypass Groq for speed + accuracy) ─────────────
    q_words = cleaned_question.strip().split()
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
    
    q_stems = set(naive_uz_stem(cleaned_question))
    is_short = len(q_words) <= 1
    has_vague_kw = bool(q_stems & vague_stems)

    search_query = cleaned_question

    if is_short or (len(q_words) <= 2 and has_vague_kw):
        options = generate_options(search_query, all_pairs)
        if options:
            logging.info(f"[VAGUE-FAST][{lang}] '{question[:40]}' → {len(options)} options")
            return get_response("clarify", lang), options, lang, "VAGUE", "Boshqa"

    # ── LLM QUERY ANALYSIS (For longer/conversational queries) ──────────────────
    analysis = analyze_user_query(cleaned_question, client)
    category = analysis["category"]
    topic = analysis["topic"]
    search_query = analysis["search_query"]

    logging.info(f"[QUERY-ANALYSIS] Original: '{question[:40]}' | Cleaned: '{cleaned_question[:40]}' -> Category: {category}, Topic: {topic}, Search Query: '{search_query[:40]}'")

    # ── GENERAL / CONVERSATIONAL ──────────────────────────────────────────────
    if category == "GENERAL":
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
        context = find_relevant_pairs(search_query, all_pairs, client)
        if not context:
            logging.warning(f"[NO-CONTEXT] {question[:50]}")
            return "Hujjatda bunday ma'lumot topilmadi", [], lang, "UNIVERSITY", topic

        logging.info(f"[AI-SEARCH] Context found for: {question[:50]}")
        relevant_context = context

        if not relevant_context.strip():
            return get_response("not_found", lang), [], lang, "UNANSWERED", topic

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
            
            if "NOT_FOUND" in ans.upper() or len(ans) < 5:
                return get_response("not_found", lang), [], lang, "UNANSWERED", topic
                
            return ans, [], lang, "UNIVERSITY", topic
        except Exception as e:
            import traceback
            logging.error(f"Error in UNIVERSITY answer generation: {e}\n{traceback.format_exc()}")
            return get_response("error", lang), [], lang, "ERROR", "Boshqa"

    return get_response("error", lang), [], lang, "ERROR", "Boshqa"
