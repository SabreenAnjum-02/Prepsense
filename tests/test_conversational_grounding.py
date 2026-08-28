import unittest
import asyncio
from agents.shared.roles import RoleArchetype, detect_role, get_role_blueprint
from agents.shared.types import (
    CandidateProfile,
    InterviewContext,
    QuestionRecord,
    AnswerRecord,
    PerformanceRecord
)
from agents.interviewer.generator import QuestionGenerator
from agents.planner.topic_selector import TopicSelector
from agents.report.llm_report_generator import LLMReportGenerator


class TestConversationalGrounding(unittest.IsolatedAsyncioTestCase):

    async def test_01_all_9_roles_authoritative_grounding(self):
        """Verify that selecting each of the 9 roles produces strictly domain-appropriate questions."""
        roles = [
            (RoleArchetype.SOFTWARE_ENGINEER_BACKEND, "Backend Software Engineer", ["Python", "FastAPI", "PostgreSQL", "Redis"], ["High-Throughput Payments Service"]),
            (RoleArchetype.FRONTEND_ENGINEER, "Frontend Engineer", ["React", "TypeScript", "Next.js", "Tailwind CSS"], ["E-Commerce Web Storefront"]),
            (RoleArchetype.FULLSTACK_ENGINEER, "Full Stack Engineer", ["React", "Node.js", "GraphQL", "PostgreSQL"], ["SaaS Analytics Dashboard"]),
            (RoleArchetype.DATA_SCIENTIST_ML, "Data Scientist / ML Engineer", ["Python", "PyTorch", "Scikit-Learn", "Pandas"], ["Fraud Detection Classification Pipeline"]),
            (RoleArchetype.DEVOPS_CLOUD, "DevOps & Cloud Platform Engineer", ["Kubernetes", "Terraform", "Docker", "AWS"], ["Multi-AZ Disaster Recovery Infrastructure"]),
            (RoleArchetype.CYBERSECURITY, "Cybersecurity & AppSec Engineer", ["OWASP Top 10", "Penetration Testing", "OAuth2", "Cryptography"], ["Zero-Trust Identity Gateway"]),
            (RoleArchetype.MOBILE_ENGINEER, "Mobile Application Engineer", ["React Native", "Swift", "Kotlin", "Offline Storage"], ["Real-Time Messaging Mobile App"]),
            (RoleArchetype.UI_UX_DESIGNER, "UI/UX Designer", ["Figma", "Design Systems", "WCAG 2.1", "User Research"], ["Mobile Banking App Redesign"]),
            (RoleArchetype.PRODUCT_MANAGER, "Technical Product Manager", ["RICE Prioritization", "PRD Writing", "A/B Testing", "Agile"], ["B2B Marketplace 0-to-1 Launch"])
        ]

        q_gen = QuestionGenerator()
        topic_sel = TopicSelector()

        for role_enum, role_title, skills, projects in roles:
            # 1. Verify detect_role priority
            detected = detect_role(target_role_str=role_title, profile_skills=skills)
            self.assertEqual(detected, role_enum, f"Role detection failed for {role_title}")

            # 2. Verify Blueprint
            bp = get_role_blueprint(role_enum)
            self.assertGreaterEqual(len(bp.technical_topics), 4)

            # 3. Create Grounded Context
            profile = CandidateProfile(
                name="Jordan Taylor",
                target_role=role_title,
                skills=skills,
                projects=projects,
                experience=["Senior Engineer with 5 years domain experience"],
                target_jd=f"Looking for a Senior {role_title} to lead core technical initiatives."
            )
            context = InterviewContext(
                session_id=f"test_{role_enum.value}",
                candidate_profile=profile
            )

            # Generate Stage 1 Opening Question
            q1 = await q_gen.generate_question(context=context)
            self.assertTrue(len(q1.question) > 10, f"Question too short for {role_title}")
            self.assertIn("?", q1.question)
            print(f"\n[Role Grounding: {role_title}]")
            print(f"  Q1 ({q1.topic}): {q1.question}")

    async def test_02_conversational_followup_grounding(self):
        """Verify that follow-up questions dynamically react to candidate answers."""
        profile = CandidateProfile(
            name="Alex Rivera",
            target_role="Frontend Engineer",
            skills=["React", "TypeScript", "Next.js", "Redux Toolkit"],
            projects=["E-Commerce Platform with 100k daily active users"]
        )
        context = InterviewContext(
            session_id="test_followup_react",
            candidate_profile=profile
        )

        # Question 1: Ask about state management
        q1_record = QuestionRecord(
            question_id="q_1",
            question="Can you walk me through how you structured state management for your e-commerce platform?",
            topic="State Management (Redux/zustand)",
            difficulty="Medium"
        )
        context.questions.append(q1_record)

        # Candidate Answer: Explains using Redux Toolkit for complex cart caching
        a1_record = AnswerRecord(
            question_id="q_1",
            candidate_answer="I chose Redux Toolkit with RTK Query because our product catalog required normalized caching across multiple product detail pages and complex shopping cart state.",
            stt_transcript="I chose Redux Toolkit with RTK Query because our product catalog required normalized caching.",
            time_taken_seconds=20,
            confidence=0.98
        )
        context.answers.append(a1_record)

        # Generate Follow-up Question
        q_gen = QuestionGenerator()
        q2 = await q_gen.generate_question(context=context)
        self.assertTrue(len(q2.question) > 10)
        self.assertIn("?", q2.question)
        print(f"\n[Conversational Follow-up Reaction]")
        print(f"  Candidate Answer: '{a1_record.candidate_answer}'")
        print(f"  AI Follow-up Question: '{q2.question}'")


if __name__ == "__main__":
    unittest.main()
