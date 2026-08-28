from typing import List
from .models import DocumentChunk, SearchResult
from .embeddings import EmbeddingService
from .vector_store import VectorStore
from .utils import get_logger

logger = get_logger(__name__)

class Retriever:
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        
    def retrieve(self, query: str, top_k: int = 5) -> List[SearchResult]:
        logger.info(f"Retrieving top {top_k} results for query: '{query}'")
        
        query_embedding = self.embedding_service.embed_query(query)
        ids, distances, documents, metadatas = self.vector_store.search(query_embedding, top_k=top_k)
        
        results = []
        for i in range(len(ids)):
            chunk = DocumentChunk(
                id=ids[i],
                document_id=metadatas[i].get("document_id", "unknown"),
                content=documents[i],
                metadata=metadatas[i]
            )
            
            # ChromaDB uses distance (lower is better for some metrics), but we'll store the raw score
            result = SearchResult(chunk=chunk, score=distances[i])
            results.append(result)
            
        return results
