from typing import List, Dict, Any, Optional
from .models import Document, DocumentChunk, SearchResult
from .loader import DocumentLoader
from .splitter import DocumentSplitter
from .embeddings import EmbeddingService
from .vector_store import VectorStore
from .retriever import Retriever
from .validator import RetrievalValidator
from .utils import get_logger

logger = get_logger(__name__)

class RAGService:
    def __init__(self, knowledge_dir: str = "knowledge", db_dir: str = "rag/db"):
        logger.info("Initializing RAG Service")
        self.loader = DocumentLoader(knowledge_dir=knowledge_dir)
        self.splitter = DocumentSplitter(chunk_size=500, overlap=100)
        
        # Initialize embeddings model (might take a moment to load weights)
        self.embedding_service = EmbeddingService()
        
        # Initialize local database
        self.vector_store = VectorStore(persist_directory=db_dir)
        
        # Initialize high-level retriever and validator
        self.retriever = Retriever(self.embedding_service, self.vector_store)
        self.validator = RetrievalValidator(max_distance=1.8)
        
    def index_knowledge_base(self):
        """Loads all documents, splits them, and stores embeddings in the vector DB."""
        logger.info("Starting knowledge base indexing process.")
        
        # 1. Load
        documents = self.loader.load_all()
        if not documents:
            logger.warning("No documents found to index.")
            return
            
        # 2. Split
        chunks = self.splitter.split(documents)
        
        # 3. Embed
        texts_to_embed = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.embed_texts(texts_to_embed)
        
        # 4. Store
        self.vector_store.add_chunks(chunks, embeddings)
        logger.info("Knowledge base indexing complete.")
        
    def query(self, query_text: str, top_k: int = 3) -> List[SearchResult]:
        """Queries the vector DB and returns the most relevant chunks."""
        logger.info(f"RAG query initiated: '{query_text}'")
        
        # 1. Retrieve
        results = self.retriever.retrieve(query=query_text, top_k=top_k)
        
        # 2. Validate
        valid_results = self.validator.filter_results(results)
        
        logger.info(f"RAG query returned {len(valid_results)} validated results.")
        return valid_results
