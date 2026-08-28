from typing import List
from .models import SearchResult
from .utils import get_logger

logger = get_logger(__name__)

class RetrievalValidator:
    def __init__(self, max_distance: float = 1.5):
        # ChromaDB default L2 distance - smaller means more similar
        self.max_distance = max_distance
        
    def filter_results(self, results: List[SearchResult]) -> List[SearchResult]:
        filtered = []
        for res in results:
            if res.score <= self.max_distance:
                filtered.append(res)
            else:
                logger.debug(f"Filtered out chunk {res.chunk.id} due to low relevance score: {res.score}")
                
        logger.info(f"Validator kept {len(filtered)} out of {len(results)} results.")
        return filtered
