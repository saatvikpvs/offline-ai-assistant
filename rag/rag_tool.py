from crewai.tools import tool  # <-- Changed this from langchain.tools
from rag.retriever import query_db

@tool("Search Offline Knowledge Base")
def search_knowledge_base(query: str) -> str:
    """
    Useful for searching the internal, offline knowledge base for specific facts, 
    documents, or historical information provided by the user.
    """
    return query_db(query)