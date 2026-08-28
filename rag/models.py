from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Document(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentChunk(BaseModel):
    id: str
    document_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float
