import fitz  # PyMuPDF
from .utils import get_logger

logger = get_logger(__name__)


class ResumeParser:
    """Extracts raw text from PDF resume files."""

    def parse_pdf(self, file_path: str) -> str:
        """Extract text from the given PDF file.

        Args:
            file_path: Absolute or relative path to the PDF resume.

        Returns:
            The extracted raw text as a string.
            
        Raises:
            ValueError: If parsing fails or the file is invalid.
        """
        logger.info(f"Parsing PDF file: {file_path}")
        text_blocks = []
        try:
            with fitz.open(file_path) as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text_blocks.append(page.get_text())
            return "\n".join(text_blocks)
        except Exception as pdf_err:
            logger.warning(f"Failed to parse as PDF, attempting text fallback: {pdf_err}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to parse PDF and text fallback failed: {e}")
                raise ValueError(f"Failed to parse resume {file_path}: {e}") from e
