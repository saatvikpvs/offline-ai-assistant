import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

DB_DIR = "./chroma_db"
DATA_DIR = "./data"


def ingest_documents():
    print("Loading documents from /data folder...")

    # Load text files
    loader = DirectoryLoader(DATA_DIR, glob="**/*.txt", loader_cls=TextLoader)
    documents = loader.load()

    if not documents:
        print("No documents found. Please add .txt files to the 'data' folder.")
        return

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    texts = text_splitter.split_documents(documents)

    print("Initializing offline embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    print("Creating Vector DB...")

    db = Chroma.from_documents(
        texts,
        embeddings,
        persist_directory=DB_DIR
    )

    db.persist()

    print("Done! Vector database populated and saved locally in /chroma_db")


if __name__ == "__main__":
    ingest_documents()