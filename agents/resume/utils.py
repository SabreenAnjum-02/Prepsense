import logging

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def clean_text(text: str) -> str:
    """Clean raw extracted text from the resume.

    Args:
        text: Raw text string.

    Returns:
        Cleaned text string.
    """
    if not text:
        return ""
    
    # Normalize line endings
    cleaned = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Collapse multiple consecutive newlines and trim whitespace
    lines = [line.strip() for line in cleaned.split('\n')]
    cleaned = '\n'.join([line for line in lines if line])
    
    return cleaned
