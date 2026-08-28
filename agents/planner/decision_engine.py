from typing import Optional
from agents.shared.types import InterviewContext, InterviewPlan
from .topic_selector import TopicSelector
from .difficulty import DifficultyAdjuster
from .strategy import InterviewStrategy
from .followup import FollowupAnalyzer
from .utils import get_logger

logger = get_logger(__name__)

class DecisionEngine:
    """Core engine evaluating the context and generating the interview plan."""

    def __init__(
        self,
        topic_selector: TopicSelector,
        difficulty_adjuster: DifficultyAdjuster,
        strategy: InterviewStrategy,
        followup: FollowupAnalyzer
    ) -> None:
        self._topic = topic_selector
        self._diff = difficulty_adjuster
        self._strat = strategy
        self._followup = followup

    def should_finish_interview(self, context: InterviewContext) -> bool:
        """Evaluate whether the interview should terminate based on competency satisfaction or safety ceiling."""
        import os
        max_questions = int(os.getenv("PREPSENSE_MAX_QUESTIONS", "15"))
        
        # 1. Safety ceiling reached
        if len(context.questions) >= max_questions:
            logger.info(f"Safety ceiling of {max_questions} questions reached. Ending interview.")
            return True

        # 2. Minimum questions check: Do not end prematurely before comprehensive competency sample (at least 9 questions)
        if len(context.questions) < 9:
            return False

        # 3. Check if TopicSelector determined that all 5 stages are satisfied
        _, _, _, all_stages_satisfied = self._topic.determine_stage_and_topic(
            context,
            is_followup=False,
            max_questions=max_questions
        )
        
        if all_stages_satisfied:
            logger.info("All 5 competency stages satisfied. Concluding interview.")
            return True

        return False

    def generate_plan(self, context: InterviewContext) -> InterviewPlan:
        """Create the next plan of action for the interviewer.

        Args:
            context: The current interview context.

        Returns:
            An InterviewPlan object.
        """
        logger.info(f"Generating interview plan for session {context.session_id}")

        if self.should_finish_interview(context):
            return InterviewPlan(
                session_id=context.session_id,
                should_end_interview=True,
                reasoning="Time/Question limit reached."
            )

        # Evaluate current state
        current_topic: Optional[str] = None
        if context.questions:
            current_topic = context.questions[-1].topic

        should_change = self._topic.should_change_topic(context, current_topic)
        is_followup = False

        if not should_change:
            is_followup = self._followup.needs_followup(context)

        # Select next topic
        next_topic = current_topic
        if should_change or not current_topic:
            next_topic = self._topic.select_topic(context)

        if not next_topic:
            # No more topics to discuss
            return InterviewPlan(
                session_id=context.session_id,
                should_end_interview=True,
                reasoning="No more topics to discuss."
            )

        # Determine difficulty and question type
        difficulty = self._diff.select_difficulty(context, is_followup)
        q_type = self._strat.select_question_type(context, next_topic, is_followup)

        plan = InterviewPlan(
            session_id=context.session_id,
            next_topic=next_topic,
            difficulty=difficulty,
            question_type=q_type,
            is_followup=is_followup,
            should_change_topic=should_change,
            should_end_interview=False,
            reasoning="Generated based on current performance and history."
        )

        logger.info(f"Generated plan: Topic={next_topic}, Difficulty={difficulty}, Type={q_type}")
        return plan
