import os
import re
import logging

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIR = os.path.join(BASE_DIR, "data", "vector_db")

_client = None
_collection = None

def get_vector_client():
    global _client, _collection
    if _client is None:
        import chromadb
        try:
            os.makedirs(PERSIST_DIR, exist_ok=True)
            _client = chromadb.PersistentClient(path=PERSIST_DIR)
        except Exception as e:
            logging.warning(f"Persistent ChromaDB client failed ({e}), falling back to EphemeralClient.")
            _client = chromadb.EphemeralClient()
            
        _collection = _client.get_or_create_collection(name="university_kb")
    return _collection

def add_to_vector_db(pairs: list):
    try:
        collection = get_vector_client()
        ids = []
        documents = []
        metadatas = []
        for i, pair in enumerate(pairs):
            ids.append(f"qa_{i}_{abs(hash(pair['question']))}")
            documents.append(f"Savol: {pair['question']}\nJavob: {pair['answer']}")
            metadatas.append({"source": "faq", "question": pair['question']})

        if ids:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            logging.info(f"Indexed {len(ids)} chunks into Vector DB.")
    except Exception as e:
        logging.warning(f"Vector DB indexing skipped (smart fallback active): {e}")

def search_vector_db(query: str, n_results: int = 3):
    try:
        collection = get_vector_client()
        results = collection.query(query_texts=[query], n_results=n_results)
        context_chunks = results['documents'][0] if results['documents'] else []
        if context_chunks:
            return "\n\n---\n\n".join(context_chunks)
    except Exception as e:
        logging.warning(f"Vector search fallback: {e}")

    # Fallback to smart keyword search over cached pairs
    import ai_responder
    pairs = getattr(ai_responder, '_cached_pairs', []) or []
    if not pairs or not query:
        return ""

    query_words = set(re.findall(r'\w+', query.lower()))
    scored = []
    for pair in pairs:
        text = f"{pair.get('question','')} {pair.get('answer','')}".lower()
        score = sum(1 for w in query_words if len(w) > 2 and w in text)
        if score > 0:
            scored.append((score, f"Savol: {pair['question']}\nJavob: {pair['answer']}"))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_matches = [doc for s, doc in scored[:n_results]]
    return "\n\n---\n\n".join(top_matches)

def clear_vector_db():
    try:
        collection = get_vector_client()
        data = collection.get()
        if data and data.get('ids'):
            collection.delete(ids=data['ids'])
            logging.info(f"Vector DB cleared. Deleted {len(data['ids'])} items.")
    except Exception as e:
        logging.warning(f"Clear vector DB skipped: {e}")
