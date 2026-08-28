from typing import Optional
from agents.shared.types import CandidateProfile
from .utils import get_logger

logger = get_logger(__name__)


class CandidateMemory:
    """Stores and manages the candidate's profile in the interview session."""

    def __init__(self) -> None:
        self._profile: Optional[CandidateProfile] = None

    def store_profile(self, profile: CandidateProfile) -> None:
        """Store the candidate's profile.

        Args:
            profile: A validated CandidateProfile object.
        """
        self._profile = profile
        logger.info(f"Stored candidate profile for: {profile.name}")

    def get_profile(self) -> Optional[CandidateProfile]:
        """Retrieve the stored candidate profile."""
        return self._profile

    def clear(self) -> None:
        """Clear the stored profile."""
        self._profile = None
