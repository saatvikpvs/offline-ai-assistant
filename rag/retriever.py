import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

DB_DIR = "./chroma_db"

# ---------- CACHED: Load once at startup, reuse forever ----------
print("[RAG] Loading embeddings model (one-time)...")
_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
_db = None
print("[RAG] Embeddings ready.")


def _get_db():
    global _db
    if _db is None:
        _db = Chroma(persist_directory=DB_DIR, embedding_function=_embeddings)
    return _db


def query_db(query_text: str, k: int = 3) -> str:
    """Searches the vector database for relevant information."""
    try:
        db = _get_db()
        results = db.similarity_search(query_text, k=k)

        if not results:
            return "No relevant information found in the database."

        context = "\n\n".join([doc.page_content for doc in results])
        return context

    except Exception as e:
        return f"Error accessing the database: {str(e)}"