from typing import List
from agents.shared.types import PerformanceRecord, TopicTracking, InterviewCoverage, InterviewStage
from agents.shared.types import QuestionRecord
from .utils import get_logger

logger = get_logger(__name__)


class PerformanceMemory:
    """Tracks candidate performance and topic proficiency throughout the interview."""

    def __init__(self) -> None:
        self._records: List[PerformanceRecord] = []
        self._topics: TopicTracking = TopicTracking()
        
        # Initialize default coverage categories based on InterviewStage
        default_categories = [stage.value for stage in InterviewStage]
        self._coverage = InterviewCoverage(
            categories_remaining=default_categories.copy(),
            categories_covered=[],
            questions_per_category={category: 0 for category in default_categories},
            current_topic_follow_up_count=0,
            overall_progress=0.0
        )

    def add_record(self, record: PerformanceRecord) -> None:
        """Add a performance record for a specific question."""
        self._records.append(record)
        logger.info(f"Added performance record for question ID: {record.question_id}")

    def get_records(self) -> List[PerformanceRecord]:
        """Retrieve all performance records."""
        return list(self._records)
        
    def track_question(self, question: QuestionRecord) -> None:
        """Update coverage tracking when a new question is asked."""
        topic = question.topic
        
        if question.is_followup:
            self._coverage.current_topic_follow_up_count += 1
        else:
            self._coverage.current_topic_follow_up_count = 0
            
        if topic not in self._coverage.categories_covered:
            self._coverage.categories_covered.append(topic)
            if topic in self._coverage.categories_remaining:
                self._coverage.categories_remaining.remove(topic)
                
        self._coverage.questions_per_category[topic] = self._coverage.questions_per_category.get(topic, 0) + 1
        
        # Update overall progress
        total_cats = len(self._coverage.categories_covered) + len(self._coverage.categories_remaining)
        if total_cats > 0:
            self._coverage.overall_progress = round(len(self._coverage.categories_covered) / total_cats, 2)

    def update_topic_tracking(self, topic: str, is_strong: bool) -> None:
        """Update the topic tracking based on candidate performance.

        Args:
            topic: The topic name.
            is_strong: True if the candidate showed strength, False if weakness.
        """
        if topic not in self._topics.covered_topics:
            self._topics.covered_topics.append(topic)
            if topic in self._topics.pending_topics:
                self._topics.pending_topics.remove(topic)

        if is_strong and topic not in self._topics.strong_topics:
            self._topics.strong_topics.append(topic)
            # Remove from weak topics if they improved
            if topic in self._topics.weak_topics:
                self._topics.weak_topics.remove(topic)
        elif not is_strong and topic not in self._topics.weak_topics:
            self._topics.weak_topics.append(topic)
            # Remove from strong topics if they regressed
            if topic in self._topics.strong_topics:
                self._topics.strong_topics.remove(topic)

    def get_topic_tracking(self) -> TopicTracking:
        """Retrieve the current state of topic tracking."""
        return self._topics
        
    def get_coverage(self) -> InterviewCoverage:
        """Retrieve the current state of interview coverage."""
        return self._coverage

    def clear(self) -> None:
        """Clear performance records and topic tracking."""
        self._records.clear()
        self._topics = TopicTracking()
        default_categories = [stage.value for stage in InterviewStage]
        self._coverage = InterviewCoverage(
            categories_remaining=default_categories.copy(),
            categories_covered=[],
            questions_per_category={category: 0 for category in default_categories},
            current_topic_follow_up_count=0,
            overall_progress=0.0
        )
