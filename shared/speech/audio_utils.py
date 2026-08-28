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

def normalize_audio(audio_data: bytes) -> bytes:
    """Placeholder for audio normalization (e.g., volume leveling, sample rate conversion)."""
    logger = get_logger(__name__)
    logger.info("Normalizing audio data.")
    return audio_data
