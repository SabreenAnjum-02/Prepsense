import hashlib
import logging

def generate_id(content: str) -> str:
    """Generates a stable ID based on content hash."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def get_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
