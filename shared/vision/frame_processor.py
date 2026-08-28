from typing import Any
from .utils import get_logger

logger = get_logger(__name__)

class FrameProcessor:
    """Pre-processes raw frames before detection tasks."""

    def process(self, raw_frame: Any) -> Any:
        """Placeholder for resizing, grayscale conversion, and normalization.
        
        Args:
            raw_frame: The raw video frame.
            
        Returns:
            The processed frame.
        """
        logger.info("Processing raw video frame (resizing/normalization).")
        return raw_frame
