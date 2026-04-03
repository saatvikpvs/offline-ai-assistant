from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

DB_DIR = "./chroma_db"

def query_db(query_text: str, k: int = 3) -> str:
    """Searches the vector database for relevant information."""
    # Must use the exact same embedding model used in ingest.py
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    try:
        db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        results = db.similarity_search(query_text, k=k)
        
        if not results:
            return "No relevant information found in the database."

        # Combine the retrieved chunks into a single string
        context = "\n\n".join([doc.page_content for doc in results])
        return context
    
    except Exception as e:
        return f"Error accessing the database: {str(e)}"