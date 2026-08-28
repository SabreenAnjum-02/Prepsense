from typing import Any, Optional
from agents.shared.base_agent import BaseAgent
from agents.shared.types import VoiceAnalysisResult
from .audio_processor import AudioProcessor
from .feature_extractor import FeatureExtractor
from .confidence import ConfidenceAnalyzer
from .speech_metrics import SpeechMetricsCalculator
from .validator import VoiceValidator
from .utils import get_logger

logger = get_logger(__name__)


class VoiceAnalysisAgent(BaseAgent):
    """Analyzes raw audio to measure vocal metrics and confidence."""

    def __init__(
        self,
        processor: Optional[AudioProcessor] = None,
        extractor: Optional[FeatureExtractor] = None,
        confidence: Optional[ConfidenceAnalyzer] = None,
        metrics: Optional[SpeechMetricsCalculator] = None
    ) -> None:
        self._processor = processor or AudioProcessor()
        self._extractor = extractor or FeatureExtractor()
        self._confidence = confidence or ConfidenceAnalyzer()
        self._metrics = metrics or SpeechMetricsCalculator()
        self._validator = VoiceValidator()

    @property
    def name(self) -> str:
        return "VoiceAnalysisAgent"

    async def run(self, input_data: Any) -> Optional[VoiceAnalysisResult]:
        """Execute the voice analysis pipeline.

        Args:
            input_data: Expected to be a dict with 'audio_data'.

        Returns:
            A VoiceAnalysisResult object, or None if analysis fails.
            
        Raises:
            ValueError: If input_data is invalid.
        """
        logger.info("VoiceAnalysisAgent invoked.")

        if not isinstance(input_data, dict) or "audio_data" not in input_data:
            raise ValueError("VoiceAnalysisAgent requires a dict with 'audio_data'")

        audio_data = input_data["audio_data"]

        if not self._validator.validate_input(audio_data):
            raise ValueError("Invalid audio input provided to VoiceAnalysisAgent.")

        try:
            # 1. Process raw audio
            processed = self._processor.process(audio_data)
            duration = processed.get("duration", 0.0)

            # 2. Extract acoustic features
            speed, pauses = self._extractor.extract_features(processed)

            # 3. Calculate derived metrics
            fluency = self._metrics.calculate_fluency(speed, pauses)
            consistency = self._metrics.calculate_consistency(speed)
            confidence = self._confidence.analyze_confidence(speed, pauses, duration)

            # 4. Construct result
            result = VoiceAnalysisResult(
                speaking_speed=speed,
                pause_count=pauses,
                fluency_score=fluency,
                consistency_score=consistency,
                confidence_score=confidence,
                duration_seconds=duration
            )

            # 5. Validate output
            if not self._validator.validate_output(result):
                logger.error("Failed to generate a valid VoiceAnalysisResult.")
                return None

            logger.info("Successfully analyzed audio input.")
            return result

        except Exception as e:
            logger.error(f"Error during voice analysis: {e}")
            raise
