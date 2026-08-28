from typing import List
from .models import Document, DocumentChunk
from .utils import get_logger, generate_id

logger = get_logger(__name__)

class DocumentSplitter:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, documents: List[Document]) -> List[DocumentChunk]:
        chunks = []
        for doc in documents:
            text = doc.content
            start = 0
            text_length = len(text)
            
            while start < text_length:
                end = start + self.chunk_size
                chunk_text = text[start:end]
                
                chunk_id = generate_id(f"{doc.id}_{start}_{end}")
                chunk = DocumentChunk(
                    id=chunk_id,
                    document_id=doc.id,
                    content=chunk_text,
                    metadata=doc.metadata.copy()
                )
                chunks.append(chunk)
                
                start += self.chunk_size - self.overlap
                
        logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks.")
        return chunks
