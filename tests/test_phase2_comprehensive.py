import unittest
import uuid
from agents.shared.types import (
    InterviewContext, 
    InterviewQuestion, 
    AnswerRecord, 
    PerformanceRecord, 
    CandidateProfile,
    InterviewStage
)
from agents.planner.topic_selector import TopicSelector
from agents.planner.decision_engine import DecisionEngine
from agents.planner.difficulty import DifficultyAdjuster
from agents.planner.strategy import InterviewStrategy
from agents.planner.followup import FollowupAnalyzer
from agents.shared.roles import RoleArchetype, get_role_blueprint, detect_role
from agents.evaluator.scoring import ScoringEngine
from agents.shared.types import CriterionEvaluation


class TestPhase2ComprehensiveAssessment(unittest.TestCase):

    def setUp(self):
        self.topic_selector = TopicSelector()
        self.difficulty_adjuster = DifficultyAdjuster()
        self.strategy = InterviewStrategy()
        self.followup_analyzer = FollowupAnalyzer()
        self.decision_engine = DecisionEngine(
            self.topic_selector,
            self.difficulty_adjuster,
            self.strategy,
            self.followup_analyzer
        )

    def _run_simulated_interview(self, role_str: str, candidate_strength: str = "strong"):
        """Simulate an adaptive interview flow for a role and candidate profile."""
        bp = get_role_blueprint(role_str)
        profile = CandidateProfile(
            name="Test Candidate",
            target_role=bp.display_name,
            skills=bp.required_competencies,
            projects=["Production Architecture System"],
            skill_gaps=[bp.technical_topics[0]] if candidate_strength == "struggling" else []
        )
        context = InterviewContext(
            session_id=str(uuid.uuid4()),
            candidate_profile=profile
        )
        
        stages_visited = []
        questions_asked = []
        turn = 0
        while turn < 15:
            stage, topic, q_type, should_end = self.topic_selector.determine_stage_and_topic(
                context, is_followup=False, max_questions=15
            )
            if should_end:
                break
            
            q_id = f"Q_{turn+1}"
            q = InterviewQuestion(
                question_id=q_id,
                question=f"Question for {stage.value} on {topic}?",
                topic=topic,
                estimated_difficulty="Medium",
                question_type=q_type,
                is_followup=False
            )
            context.questions.append(q)
            questions_asked.append(q)
            stages_visited.append(stage)
            
            # Simulate answer and evaluation
            ans_score = 85.0 if candidate_strength == "strong" else (50.0 if turn % 2 == 0 else 75.0)
            a = AnswerRecord(
                question_id=q_id,
                candidate_answer=f"Comprehensive answer on {topic}",
                stt_transcript=f"Comprehensive answer on {topic}",
                time_taken_seconds=30,
                confidence=0.95
            )
            context.answers.append(a)
            
            rec = PerformanceRecord(
                question_id=q_id,
                overall_score=ans_score,
                technical_score=ans_score,
                practical_score=ans_score,
                problem_solving_score=ans_score,
                communication_score=ans_score,
                behavioral_score=ans_score,
                role_fit_score=ans_score,
                role_archetype=bp.role.value
            )
            context.performance.append(rec)
            turn += 1
            
        return context, stages_visited, questions_asked

    def test_frontend_strong_candidate_flow(self):
        """Test Frontend Engineer undergoes a comprehensive 10-11 question assessment."""
        ctx, stages, qs = self._run_simulated_interview("Frontend Engineer", "strong")
        print(f"\n[Frontend Strong Candidate] Total Questions: {len(qs)}")
        for i, (st, q) in enumerate(zip(stages, qs)):
            print(f"  Q{i+1}: [{st.value}] {q.topic}")
        self.assertGreaterEqual(len(qs), 10, "Strong Frontend candidate should receive at least 10 questions")
        self.assertLessEqual(len(qs), 12, "Strong Frontend candidate should finish by 10-12 questions")
        
        # Verify all 5 stages visited in order
        self.assertEqual(stages[0], InterviewStage.INTRODUCTION)
        self.assertTrue(any(s == InterviewStage.TECHNICAL for s in stages))
        self.assertTrue(any(s == InterviewStage.PROJECTS for s in stages))
        self.assertTrue(any(s == InterviewStage.BEHAVIORAL for s in stages))
        self.assertTrue(any(s == InterviewStage.HR for s in stages))

    def test_backend_strong_candidate_flow(self):
        """Test Backend Software Engineer undergoes 10 to 11 questions."""
        ctx, stages, qs = self._run_simulated_interview("Backend Software Engineer", "strong")
        print(f"\n[Backend Strong Candidate] Total Questions: {len(qs)}")
        for i, (st, q) in enumerate(zip(stages, qs)):
            print(f"  Q{i+1}: [{st.value}] {q.topic}")
        self.assertGreaterEqual(len(qs), 10)
        self.assertLessEqual(len(qs), 12)
        self.assertEqual(stages[0], InterviewStage.INTRODUCTION)

    def test_data_ml_strong_candidate_flow(self):
        """Test Data Scientist / ML Engineer interview flow."""
        ctx, stages, qs = self._run_simulated_interview("Data Scientist / ML Engineer", "strong")
        print(f"\n[Data/ML Strong Candidate] Total Questions: {len(qs)}")
        for i, (st, q) in enumerate(zip(stages, qs)):
            print(f"  Q{i+1}: [{st.value}] {q.topic}")
        self.assertGreaterEqual(len(qs), 10)
        self.assertLessEqual(len(qs), 12)

    def test_devops_strong_candidate_flow(self):
        """Test DevOps & Cloud Platform Engineer interview flow."""
        ctx, stages, qs = self._run_simulated_interview("DevOps & Cloud Platform Engineer", "strong")
        print(f"\n[DevOps Strong Candidate] Total Questions: {len(qs)}")
        for i, (st, q) in enumerate(zip(stages, qs)):
            print(f"  Q{i+1}: [{st.value}] {q.topic}")
        self.assertGreaterEqual(len(qs), 10)
        self.assertLessEqual(len(qs), 12)

    def test_struggling_candidate_expanded_questions(self):
        """Test that struggling candidate receives more adaptive questions (12-14)."""
        ctx, stages, qs = self._run_simulated_interview("Backend Software Engineer", "struggling")
        print(f"\n[Backend Struggling Candidate] Total Questions: {len(qs)}")
        for i, (st, q) in enumerate(zip(stages, qs)):
            print(f"  Q{i+1}: [{st.value}] {q.topic}")
        self.assertGreaterEqual(len(qs), 12, "Struggling candidate must receive at least 12 questions")
        self.assertLessEqual(len(qs), 15, "Cannot exceed safety ceiling of 15")

    def test_deterministic_6d_scoring_computation(self):
        """Verify 6D evidence-based scoring works for all stages."""
        evals = [
            CriterionEvaluation(criterion_name="Technical Accuracy", score=85.0, observed_evidence=["Correct explanation"]),
            CriterionEvaluation(criterion_name="Completeness & Coverage", score=80.0, observed_evidence=["Covered all sub-points"]),
            CriterionEvaluation(criterion_name="Reasoning & Problem Solving", score=88.0, observed_evidence=["Sound trade-off rationale"]),
            CriterionEvaluation(criterion_name="Communication Clarity", score=90.0, observed_evidence=["Concise structure"]),
            CriterionEvaluation(criterion_name="Behavioral Alignment", score=85.0, observed_evidence=["Used STAR format"]),
            CriterionEvaluation(criterion_name="Role Fit", score=82.0, observed_evidence=["Good domain alignment"])
        ]
        engine = ScoringEngine()
        scores = engine.calculate_6d_scores_from_evidence(evals)
        print("\n[6D Scores Calculated]")
        for dim, score in scores.items():
            print(f"  {dim}: {score}")
            self.assertGreaterEqual(score, 50.0)
            self.assertLessEqual(score, 100.0)


if __name__ == "__main__":
    unittest.main()
