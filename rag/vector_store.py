import chromadb
from typing import List, Dict, Any, Tuple
from .models import DocumentChunk
from .utils import get_logger

logger = get_logger(__name__)

class VectorStore:
    def __init__(self, persist_directory: str = "rag/db", collection_name: str = "prepsense_knowledge"):
        logger.info(f"Initializing VectorStore at {persist_directory} with collection {collection_name}")
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        if not chunks:
            return
            
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        logger.info(f"Adding {len(chunks)} chunks to vector store.")
        
        # Ensure metadata values are strings, ints, floats, or bools for ChromaDB
        sanitized_metadatas = []
        for meta in metadatas:
            sanitized = {k: (str(v) if not isinstance(v, (str, int, float, bool)) else v) for k, v in meta.items()}
            # Also embed document_id to allow filtering later if needed
            if "document_id" not in sanitized:
                 sanitized["document_id"] = chunks[metadatas.index(meta)].document_id
            sanitized_metadatas.append(sanitized)
            
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=sanitized_metadatas
        )
        logger.info(f"Successfully added chunks to vector store.")
        
    def search(self, query_embedding: List[float], top_k: int = 5) -> Tuple[List[str], List[float], List[str], List[Dict[str, Any]]]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Extract the results from the first (and only) query
        ids = results['ids'][0] if results['ids'] else []
        distances = results['distances'][0] if results['distances'] else []
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        
        return ids, distances, documents, metadatas
