from agents.shared.types import CandidateProfile
from .utils import get_logger

logger = get_logger(__name__)


class ProfileValidator:
    """Validates the constructed CandidateProfile for completeness and correctness."""

    def validate(self, profile: CandidateProfile) -> bool:
        """Validate the structured profile.

        Args:
            profile: The CandidateProfile object to validate.

        Returns:
            True if the profile meets minimum validity requirements, False otherwise.
        """
        logger.info("Validating extracted CandidateProfile.")
        
        # A basic validation rule: candidate must have a name.
        if not profile.name:
            logger.warning("Validation failed: Missing candidate name.")
            return False
            
        # Add more validation rules as needed (e.g., must have some skills or experience)
        
        logger.info("CandidateProfile validation successful.")
        return True
