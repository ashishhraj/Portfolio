import chromadb
from chromadb.config import Settings
import os, logging

logger = logging.getLogger(__name__)
chroma_client = None
portfolio_collection = None

def init_chroma():
    global chroma_client, portfolio_collection
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")
    chroma_client = chromadb.PersistentClient(path=persist_dir)
    portfolio_collection = chroma_client.get_or_create_collection(
        name="portfolio_data",
        metadata={"hnsw:space": "cosine"}
    )
    logger.info("✅ ChromaDB initialized")

def get_collection():
    return portfolio_collection

def upsert_document(doc_id: str, text: str, metadata: dict):
    """Add or update a document in ChromaDB for semantic search."""
    portfolio_collection.upsert(
        documents=[text],
        metadatas=[metadata],
        ids=[doc_id]
    )

def delete_document(doc_id: str):
    try:
        portfolio_collection.delete(ids=[doc_id])
    except Exception:
        pass

def query_similar(query_text: str, n_results: int = 5):
    """Find semantically similar documents."""
    results = portfolio_collection.query(
        query_texts=[query_text],
        n_results=min(n_results, portfolio_collection.count() or 1)
    )
    return results
