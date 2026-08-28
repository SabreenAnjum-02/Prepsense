import os
from typing import Optional, Tuple, Any, Set
from agents.shared.types import InterviewContext, InterviewStage
from .utils import get_logger

logger = get_logger(__name__)

class TopicSelector:
    """Decides which stage and topic to cover next based on candidate profile, stage competency satisfaction, and adaptive state."""

    def should_change_topic(self, context: InterviewContext, current_topic: Optional[str]) -> bool:
        """Determine if enough evidence has been collected for the current topic."""
        if not current_topic:
            return True
            
        count = sum(1 for q in context.questions if q.topic == current_topic)
        # Change topic if 2 or more questions have been asked on this specific topic
        if count >= 2:
            logger.info(f"TopicSelector: Enough evidence collected for topic '{current_topic}' ({count} questions). Suggesting change.")
            return True
            
        return False

    def determine_stage_and_topic(
        self,
        context: InterviewContext,
        is_followup: bool = False,
        max_questions: int = 15
    ) -> Tuple[InterviewStage, str, str, bool]:
        """Deterministically evaluate competency satisfaction across 5 stages and select next stage/topic.
        
        Returns:
            Tuple of (stage, topic, question_type, should_end_interview)
        """
        num_q = len(context.questions)
        current_q = context.questions[-1] if context.questions else None
        current_topic = current_q.topic if current_q else None
        
        # If this is an adaptive follow-up and we have a current topic, preserve topic & stage
        if is_followup and current_topic:
            stage = self._infer_stage(current_topic, context)
            logger.info(f"TopicSelector: Follow-up on current topic '{current_topic}' in stage '{stage.value}'")
            return stage, current_topic, "Follow-up", False

        candidate = context.candidate_profile
        target_role = candidate.target_role if candidate and candidate.target_role else None
        target_jd = candidate.target_jd if candidate and candidate.target_jd else None
        profile_skills = candidate.skills if candidate and candidate.skills else []
        profile_exp = candidate.experience if candidate and candidate.experience else []
        skill_gaps = candidate.skill_gaps if candidate and candidate.skill_gaps else []

        from agents.shared.roles import detect_role, get_role_blueprint, RoleBlueprint
        role_enum = detect_role(
            target_role_str=target_role,
            jd_text=target_jd,
            profile_skills=profile_skills,
            profile_experience=profile_exp
        )
        blueprint: RoleBlueprint = get_role_blueprint(role_enum)

        # Count questions and performance per stage
        stage_counts = {
            InterviewStage.INTRODUCTION: 0,
            InterviewStage.TECHNICAL: 0,
            InterviewStage.PROJECTS: 0,
            InterviewStage.BEHAVIORAL: 0,
            InterviewStage.HR: 0
        }
        
        covered_topics = set()
        for idx, q in enumerate(context.questions):
            covered_topics.add(q.topic)
            q_stage = self._infer_stage_for_question(q, idx, blueprint)
            stage_counts[q_stage] = stage_counts.get(q_stage, 0) + 1

        # Check performance history for competency evaluation
        recent_scores = [p.overall_score for p in context.performance] if context.performance else []

        # ── STAGE 1: INTRODUCTION (Self-Introduction & Background) ──
        # Requirement: Exactly 1 opening introduction question
        if stage_counts[InterviewStage.INTRODUCTION] < 1:
            return InterviewStage.INTRODUCTION, "Self-Introduction & Background", "Introduction", False

        # ── STAGE 2: TECHNICAL (Domain Core Fundamentals & Syntax / Internals) ──
        # Requirement: Minimum 4 core domain competencies evaluated.
        # Prioritizes JD skill gaps, followed by blueprint technical topics.
        tech_topics_pool = list(blueprint.technical_topics)
        for gap in skill_gaps:
            if gap not in tech_topics_pool:
                tech_topics_pool.insert(0, gap)
        for sk in profile_skills:
            if sk not in tech_topics_pool and len(tech_topics_pool) < 8:
                tech_topics_pool.append(sk)

        tech_q_count = stage_counts[InterviewStage.TECHNICAL]
        min_tech_req = blueprint.minimum_technical_evidence  # 4
        
        tech_covered = [t for t in tech_topics_pool if t in covered_topics]
        strong_tech_scores = [s for s in recent_scores[-tech_q_count:] if s >= 70.0] if tech_q_count > 0 else []
        
        # Advance when candidate has answered at least 4 technical competencies with sufficient evidence (or up to 6 if struggling)
        tech_satisfied = (
            (len(tech_covered) >= min_tech_req and len(strong_tech_scores) >= 3 and tech_q_count >= 4)
            or (tech_q_count >= 6)
        )
        
        if not tech_satisfied:
            uncovered = [t for t in tech_topics_pool if t not in covered_topics]
            topic = uncovered[0] if uncovered else tech_topics_pool[tech_q_count % len(tech_topics_pool)]
            return InterviewStage.TECHNICAL, topic, "Technical", False

        # ── STAGE 3: PROJECTS / SYSTEM DESIGN (Architecture, Scale & Trade-offs) ──
        # Requirement: Minimum 2-3 distinct architecture scenarios evaluated.
        proj_topics_pool = list(blueprint.project_topics)
        proj_q_count = stage_counts[InterviewStage.PROJECTS]
        min_proj_req = blueprint.minimum_project_evidence  # 2

        proj_covered = [p for p in proj_topics_pool if p in covered_topics]
        proj_satisfied = (
            (len(proj_covered) >= min_proj_req and proj_q_count >= 2 and (not recent_scores or recent_scores[-1] >= 60.0))
            or (proj_q_count >= 4)
        )
        
        if not proj_satisfied:
            uncovered_proj = [p for p in proj_topics_pool if p not in covered_topics]
            topic = uncovered_proj[0] if uncovered_proj else proj_topics_pool[proj_q_count % len(proj_topics_pool)]
            return InterviewStage.PROJECTS, topic, "Technical", False

        # ── STAGE 4: BEHAVIORAL (STAR Collaboration, Leadership & Pressure) ──
        # Requirement: Minimum 2 behavioral topics evaluated.
        behav_topics_pool = list(blueprint.behavioral_topics)
        behav_q_count = stage_counts[InterviewStage.BEHAVIORAL]
        min_behav_req = blueprint.minimum_behavioral_evidence  # 2

        behav_covered = [b for b in behav_topics_pool if b in covered_topics]
        behav_satisfied = (
            (len(behav_covered) >= min_behav_req and behav_q_count >= 2)
            or (behav_q_count >= 3)
        )
        
        if not behav_satisfied:
            uncovered_behav = [b for b in behav_topics_pool if b not in covered_topics]
            topic = uncovered_behav[0] if uncovered_behav else behav_topics_pool[behav_q_count % len(behav_topics_pool)]
            return InterviewStage.BEHAVIORAL, topic, "Behavioural", False

        # ── STAGE 5: HR / CLOSING (Workplace Culture & Continuous Growth) ──
        # Requirement: Exactly 1 question
        hr_topics_pool = list(blueprint.hr_topics) if blueprint.hr_topics else ["Workplace Culture & Continuous Growth", "Career Goals & Engineering Philosophy"]
        hr_q_count = stage_counts[InterviewStage.HR]
        if hr_q_count < 1:
            uncovered_hr = [h for h in hr_topics_pool if h not in covered_topics]
            topic = uncovered_hr[0] if uncovered_hr else hr_topics_pool[0]
            return InterviewStage.HR, topic, "HR", False

        # ── ALL 5 STAGES SATISFIED ──
        logger.info(f"TopicSelector: All 5 interview stages satisfied after {num_q} questions. Signaling interview completion.")
        return InterviewStage.CLOSING, "Closing", "Closing", True

    def _infer_stage_for_question(self, q: Any, idx: int, blueprint: Optional[Any] = None) -> InterviewStage:
        """Infer stage for a specific question record based on index and topic."""
        if idx == 0:
            return InterviewStage.INTRODUCTION
        return self._infer_stage(q.topic, blueprint=blueprint)

    def _infer_stage(self, topic: str, context: Optional[InterviewContext] = None, blueprint: Optional[Any] = None) -> InterviewStage:
        """Infer the InterviewStage for a given topic."""
        t_low = topic.lower()
        if any(k in t_low for k in ["intro", "introduction", "background", "about yourself", "journey"]):
            return InterviewStage.INTRODUCTION
            
        if blueprint:
            if topic in blueprint.technical_topics:
                return InterviewStage.TECHNICAL
            if topic in blueprint.project_topics:
                return InterviewStage.PROJECTS
            if topic in blueprint.behavioral_topics:
                return InterviewStage.BEHAVIORAL
            if topic in blueprint.hr_topics:
                return InterviewStage.HR

        if any(k in t_low for k in ["team", "conflict", "behavioral", "leadership", "pressure", "stakeholder", "disagreement", "postmortem"]):
            return InterviewStage.BEHAVIORAL
        if any(k in t_low for k in ["culture", "goal", "salary", "hr", "growth", "closing", "philosophy", "aspirations"]):
            return InterviewStage.HR
        if any(k in t_low for k in ["system design", "distributed system", "microservices", "sharding", "high availability", "pipeline architecture", "zero trust architecture", "0-to-1 mvp"]):
            return InterviewStage.PROJECTS
            
        return InterviewStage.TECHNICAL

    def select_topic(self, context: InterviewContext) -> Optional[str]:
        """Backward-compatible topic selector."""
        max_q = int(os.getenv("PREPSENSE_MAX_QUESTIONS", "15"))
        _, topic, _, should_end = self.determine_stage_and_topic(context, max_questions=max_q)
        if should_end:
            return None
        return topic
