import asyncio
import logging
from rag import RAGService

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RAGVerifier")

def main():
    logger.info("Initializing RAG Service...")
    # This will load documents from knowledge/ and store them in rag/db/
    rag_service = RAGService(knowledge_dir="knowledge", db_dir="rag/db")
    
    logger.info("Indexing Knowledge Base...")
    rag_service.index_knowledge_base()
    
    logger.info("--- Testing Queries ---")
    
    queries = [
        "Tell me about a time you failed",
        "How do decorators work?",
        "Dealing with team conflict"
    ]
    
    for query in queries:
        logger.info(f"\nQuerying for: '{query}'")
        results = rag_service.query(query, top_k=2)
        
        for idx, result in enumerate(results):
            logger.info(f"Result {idx+1}: Score: {result.score:.4f}")
            logger.info(f"Source: {result.chunk.metadata.get('filename')}")
            logger.info(f"Content snippet: {result.chunk.content[:100]}...\n")

    print("\nRAG infrastructure verified successfully and ready for agent integration.")

if __name__ == "__main__":
    main()
