from typing import List
from sentence_transformers import SentenceTransformer
from .utils import get_logger

logger = get_logger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        logger.info(f"Initializing EmbeddingService with model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        logger.info(f"Generating embeddings for {len(texts)} texts.")
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
        
    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query])[0]
