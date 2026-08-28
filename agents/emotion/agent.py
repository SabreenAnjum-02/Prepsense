from typing import Any, Optional
from agents.shared.base_agent import BaseAgent
from agents.shared.types import EmotionAnalysisResult
from .face_processor import FaceProcessor
from .emotion_detector import EmotionDetector
from .engagement import EngagementAnalyzer
from .validator import EmotionValidator
from .utils import get_logger

logger = get_logger(__name__)


class EmotionAnalysisAgent(BaseAgent):
    """Analyzes visual data to infer emotions, engagement, and confidence."""

    def __init__(
        self,
        processor: Optional[FaceProcessor] = None,
        detector: Optional[EmotionDetector] = None,
        analyzer: Optional[EngagementAnalyzer] = None
    ) -> None:
        self._processor = processor or FaceProcessor()
        self._detector = detector or EmotionDetector()
        self._analyzer = analyzer or EngagementAnalyzer()
        self._validator = EmotionValidator()

    @property
    def name(self) -> str:
        return "EmotionAnalysisAgent"

    async def run(self, input_data: Any) -> Optional[EmotionAnalysisResult]:
        """Execute the emotion analysis pipeline.

        Args:
            input_data: Expected to be a dict with 'video_frames'.

        Returns:
            An EmotionAnalysisResult object, or None if analysis fails.
            
        Raises:
            ValueError: If input_data is invalid.
        """
        logger.info("EmotionAnalysisAgent invoked.")

        if not isinstance(input_data, dict) or "video_frames" not in input_data:
            raise ValueError("EmotionAnalysisAgent requires a dict with 'video_frames'")

        video_frames = input_data["video_frames"]

        if not self._validator.validate_input(video_frames):
            raise ValueError("Invalid video input provided to EmotionAnalysisAgent.")

        try:
            # 1. Process frames
            face_detected, features = self._processor.process_frames(video_frames)

            if not face_detected:
                logger.warning("No face detected in the provided frames.")
                # Return empty/default result if no face
                return EmotionAnalysisResult(
                    primary_emotion="unknown",
                    engagement_score=0.0,
                    confidence_level=0.0,
                    face_detected=False
                )

            # 2. Estimate emotions
            primary_emotion, scores = self._detector.estimate_emotions(features)

            # 3. Analyze engagement and confidence
            engagement, confidence = self._analyzer.analyze_metrics(features)

            # 4. Construct result
            result = EmotionAnalysisResult(
                primary_emotion=primary_emotion,
                emotion_scores=scores,
                engagement_score=engagement,
                confidence_level=confidence,
                face_detected=face_detected
            )

            # 5. Validate output
            if not self._validator.validate_output(result):
                logger.error("Failed to generate a valid EmotionAnalysisResult.")
                return None

            logger.info("Successfully analyzed visual input.")
            return result

        except Exception as e:
            logger.error(f"Error during emotion analysis: {e}")
            raise
