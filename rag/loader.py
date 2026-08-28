import os
from pathlib import Path
from typing import List
from .models import Document
from .utils import get_logger, generate_id

logger = get_logger(__name__)

class DocumentLoader:
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        
    def load_all(self) -> List[Document]:
        documents = []
        if not self.knowledge_dir.exists():
            logger.warning(f"Knowledge directory not found: {self.knowledge_dir}")
            return documents
            
        for root, _, files in os.walk(self.knowledge_dir):
            for file in files:
                if file.endswith(('.txt', '.md')):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        doc_id = generate_id(content)
                        doc = Document(
                            id=doc_id,
                            content=content,
                            metadata={"source": str(file_path), "filename": file}
                        )
                        documents.append(doc)
                        logger.info(f"Loaded document: {file}")
                    except Exception as e:
                        logger.error(f"Error loading {file}: {e}")
        return documents
