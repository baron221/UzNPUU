import os
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass
import chromadb
from chromadb.utils import embedding_functions
import logging

# Persistent storage for ChromaDB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSIST_DIR = os.path.join(BASE_DIR, "data", "vector_db")

# Use a lightweight local embedding function (all-MiniLM-L6-v2)
# This doesn't require an API key and runs on the server
emb_fn = embedding_functions.DefaultEmbeddingFunction()

_client = None
_collection = None

def get_vector_client():
    global _client, _collection
    if _client is None:
        os.makedirs(PERSIST_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=PERSIST_DIR)
        _collection = _client.get_or_create_collection(
            name="university_kb",
            embedding_function=emb_fn
        )
    return _collection

def add_to_vector_db(pairs: list):
    """
    Adds a list of Q&A pairs to the vector database.
    Each pair is a dict with 'question' and 'answer'.
    """
    collection = get_vector_client()
    
    # Prepare data for ChromaDB
    ids = []
    documents = []
    metadatas = []
    
    for i, pair in enumerate(pairs):
        ids.append(f"qa_{i}_{hash(pair['question'])}")
        # We store the question as the main text for embedding
        # and the answer in the metadata or combined
        documents.append(f"Savol: {pair['question']}\nJavob: {pair['answer']}")
        metadatas.append({"source": "faq", "question": pair['question']})

    if ids:
        # Batch add
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logging.info(f"Indexed {len(ids)} chunks into Vector DB.")

def search_vector_db(query: str, n_results: int = 3):
    """
    Searches for the most semantically similar chunks.
    """
    collection = get_vector_client()
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        # Flatten results
        context_chunks = results['documents'][0] if results['documents'] else []
        return "\n\n---\n\n".join(context_chunks)
    except Exception as e:
        logging.error(f"Vector search error: {e}")
        return ""

def clear_vector_db():
    """
    Clears the collection to allow full re-indexing.
    """
    collection = get_vector_client()
    try:
        data = collection.get()
        if data and data.get('ids'):
            # Delete in chunks if there are many items, but for now simple delete is fine
            collection.delete(ids=data['ids'])
            logging.info(f"Vector DB cleared. Deleted {len(data['ids'])} items.")
    except Exception as e:
        logging.error(f"Error clearing vector DB: {e}")
