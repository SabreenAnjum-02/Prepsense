import os
import uuid
import pytest
import pytest_asyncio
import asyncio

from database.connection import db_manager, redis_manager
from database.models import Base
from database.repository import (
    CandidateRepository,
    SessionRepository,
    TurnRepository,
    EvaluationRepository,
    PracticalRepository,
    ReportRepository
)
from database.redis_store import redis_store
from database.session_recovery import SessionReconstructionManager
from api.session_manager import SessionManager
from agents.shared.types import InterviewContext, CandidateProfile, QuestionRecord, AnswerRecord


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Initialize fresh test database tables before each test."""
    await db_manager.init_tables()
    yield
    # Cleanup


@pytest.mark.asyncio
async def test_candidate_creation_and_retrieval():
    """Test durable candidate profile creation in PostgreSQL."""
    async with db_manager.session() as sess:
        repo = CandidateRepository(sess)
        cand = await repo.create(
            name="Alice Smith",
            email="alice@example.com",
            target_role="Frontend Engineer",
            experience_years=4,
            skills=["React", "TypeScript", "Next.js"],
            projects=["E-Commerce Storefront"],
            experience=["4 years at TechCorp"],
            target_jd="Senior Frontend Engineer"
        )
        cand_id = cand.id

    async with db_manager.session() as sess:
        repo = CandidateRepository(sess)
        fetched = await repo.get_by_id(cand_id)
        assert fetched is not None
        assert fetched.name == "Alice Smith"
        assert fetched.email == "alice@example.com"
        assert "React" in fetched.skills
        assert "E-Commerce Storefront" in fetched.projects


@pytest.mark.asyncio
async def test_session_lifecycle_persistence():
    """Test full multi-turn interview persistence in PostgreSQL."""
    session_id = str(uuid.uuid4())
    candidate_id = str(uuid.uuid4())

    async with db_manager.session() as sess:
        cand_repo = CandidateRepository(sess)
        cand = await cand_repo.create(
            name="Bob Jones",
            email="bob@example.com",
            target_role="Backend Software Engineer",
            skills=["Python", "FastAPI", "PostgreSQL"]
        )
        candidate_id = cand.id

        sess_repo = SessionRepository(sess)
        await sess_repo.create(
            session_id=session_id,
            candidate_id=candidate_id,
            target_role="Backend Software Engineer"
        )

        turn_repo = TurnRepository(sess)
        await turn_repo.add_turn(
            session_id=session_id,
            turn_index=1,
            question_id="q_1",
            question_text="How do you handle connection pooling in FastAPI?",
            topic="Database Architecture",
            difficulty="Medium",
            stage="TECHNICAL"
        )

        await turn_repo.update_answer(
            session_id=session_id,
            question_id="q_1",
            answer_text="We use asyncpg with SQLAlchemy connection pooling and max_overflow=20.",
            time_taken_seconds=22.5
        )

        eval_repo = EvaluationRepository(sess)
        await eval_repo.add_evaluation(
            session_id=session_id,
            question_id="q_1",
            technical_score=90.0,
            practical_score=88.0,
            problem_solving_score=85.0,
            communication_score=92.0,
            behavioral_score=85.0,
            role_fit_score=90.0,
            overall_score=88.5,
            strengths=["Accurate understanding of SQLAlchemy connection pool mechanics"],
            feedback="Strong response."
        )

    # Verify retrieval
    async with db_manager.session() as sess:
        sess_repo = SessionRepository(sess)
        session_orm = await sess_repo.get_by_id(session_id, include_relations=True)
        assert session_orm is not None
        assert session_orm.candidate.name == "Bob Jones"
        assert len(session_orm.turns) == 1
        assert session_orm.turns[0].candidate_answer is not None
        assert "asyncpg" in session_orm.turns[0].candidate_answer
        assert len(session_orm.evaluations) == 1
        assert session_orm.evaluations[0].technical_score == 90.0


@pytest.mark.asyncio
async def test_practical_and_report_persistence():
    """Test practical evaluation and final report persistence."""
    session_id = str(uuid.uuid4())

    async with db_manager.session() as sess:
        cand_repo = CandidateRepository(sess)
        cand = await cand_repo.create(
            name="Charlie Dev",
            email="charlie@example.com",
            target_role="Full Stack Engineer"
        )

        sess_repo = SessionRepository(sess)
        await sess_repo.create(session_id=session_id, candidate_id=cand.id, target_role="Full Stack Engineer")

        pe_repo = PracticalRepository(sess)
        await pe_repo.save_evaluation(
            session_id=session_id,
            task_id="task_fullstack_01",
            task_title="REST API Endpoint Implementation",
            role_archetype="Full Stack Engineer",
            language="python",
            tests_passed=5,
            total_tests=5,
            hidden_tests_passed=3,
            total_hidden_tests=3,
            correctness_score=100.0,
            edge_case_score=95.0,
            complexity_score=90.0,
            code_quality_score=92.0,
            overall_practical_score=95.0,
            time_complexity="O(N)",
            space_complexity="O(1)",
            feedback="Clean, correct solution."
        )

        rep_repo = ReportRepository(sess)
        await rep_repo.save_report(
            session_id=session_id,
            candidate_id=cand.id,
            overall_summary="Candidate demonstrated solid full-stack competency.",
            technical_assessment="Strong technical grasp of APIs and databases.",
            communication_assessment="Clear communication throughout.",
            hiring_recommendation="STRONG HIRE",
            confidence_level="HIGH",
            final_score=92.0,
            dimension_scores={
                "technical": 92.0,
                "practical": 95.0,
                "problem_solving": 90.0,
                "communication": 92.0,
                "behavioral": 88.0,
                "role_fit": 94.0,
                "overall": 92.0
            }
        )

    # Verify retrieval
    async with db_manager.session() as sess:
        pe_repo = PracticalRepository(sess)
        pe = await pe_repo.get_by_session_id(session_id)
        assert pe is not None
        assert pe.tests_passed == 5
        assert pe.overall_practical_score == 95.0

        rep_repo = ReportRepository(sess)
        rep = await rep_repo.get_by_session_id(session_id)
        assert rep is not None
        assert rep.hiring_recommendation == "STRONG HIRE"
        assert rep.final_score == 92.0


@pytest.mark.asyncio
async def test_redis_active_state_and_context_caching():
    """Test Redis session caching with TTL."""
    session_id = str(uuid.uuid4())
    profile = CandidateProfile(
        name="Diana Prince",
        email="diana@example.com",
        target_role="DevOps & Cloud Platform Engineer",
        skills=["Kubernetes", "Terraform", "AWS"]
    )
    context = InterviewContext(session_id=session_id, candidate_profile=profile)

    # Test save context
    saved = await redis_store.save_context(session_id, context)
    # If Redis is available, verify read
    if saved:
        loaded = await redis_store.get_context(session_id)
        assert loaded is not None
        assert loaded.candidate_profile.name == "Diana Prince"
        assert "Kubernetes" in loaded.candidate_profile.skills

        # Test active state
        await redis_store.save_active_state(session_id, {"stage": "TECHNICAL", "count": 3})
        state = await redis_store.get_active_state(session_id)
        assert state is not None
        assert state.get("stage") == "TECHNICAL"


@pytest.mark.asyncio
async def test_multi_node_restart_recovery():
    """
    CRITICAL INTEGRATION TEST:
    Simulates Node A creating a session, starting Q1, and answering Q1.
    Node A process terminates (in-memory state wiped).
    Node B retrieves the session from PostgreSQL, verifies all historical evidence,
    and successfully generates Q2 and receives Answer 2.
    """
    # === SIMULATE NODE A ===
    node_a = SessionManager()
    session_id = await node_a.create_session(
        candidate_name="Evan Wright",
        candidate_email="evan@example.com",
        target_role="Backend Software Engineer",
        skills=["Python", "FastAPI", "PostgreSQL", "Redis"],
        projects=["High-throughput payment gateway"],
        experience=["Senior Backend Engineer for 5 years"],
        job_description="Senior Backend Engineer with distributed systems expertise"
    )

    q1_data = await node_a.start_interview(session_id)
    assert q1_data.question_id is not None
    assert len(q1_data.question_text) > 5

    res1 = await node_a.submit_answer(
        session_id=session_id,
        answer_text="In our payment gateway project, we structured database transactions with optimistic locking to prevent race conditions."
    )
    assert res1.answer_acknowledged is True
    assert res1.next_question is not None

    # === SIMULATE NODE A CRASH / TERMINATION (Kill Node A's memory) ===
    del node_a

    # === SIMULATE NODE B (Completely new worker instance with fresh empty memory) ===
    node_b = SessionManager()
    assert session_id not in node_b._sessions

    # Node B queries session state
    recovered_session = await node_b.get_or_restore_session(session_id)
    assert recovered_session is not None
    assert recovered_session["profile"].name == "Evan Wright"
    assert recovered_session["profile"].target_role == "Backend Software Engineer"
    assert "payment gateway" in recovered_session["profile"].projects[0]

    # Verify historical turns and answers preserved
    context: InterviewContext = recovered_session["context"]
    assert len(context.questions) >= 2  # Q1 + Q2
    assert len(context.answers) == 1   # A1
    assert "optimistic locking" in context.answers[0].candidate_answer
    assert len(recovered_session["evaluations"]) == 1

    # Node B continues interview with Question 2
    res2 = await node_b.submit_answer(
        session_id=session_id,
        answer_text="For caching, we placed Redis in front of PostgreSQL with a 15-minute write-through TTL."
    )
    assert res2.answer_acknowledged is True
    assert len(context.answers) == 2

    # Node B completes practical task
    practical_task = node_b.get_practical_task(session_id)
    assert practical_task.title is not None

    practical_res = await node_b.submit_practical(
        session_id=session_id,
        submission_code="def solution(input_data):\n    return input_data\n"
    )
    assert practical_res.overall_practical_score is not None

    # Node B generates final report
    report_res = await node_b.generate_final_report(session_id)
    assert report_res.hiring_recommendation.upper() in ["STRONG HIRE", "HIRE", "BORDERLINE", "NO HIRE"]
    assert report_res.dimension_scores.overall > 0


@pytest.mark.asyncio
async def test_session_security_and_isolation():
    """Verify session isolation and unpredictable UUIDs."""
    mgr = SessionManager()
    s1 = await mgr.create_session(
        candidate_name="Candidate 1",
        candidate_email="c1@example.com",
        target_role="Frontend Engineer",
        skills=["React"]
    )
    s2 = await mgr.create_session(
        candidate_name="Candidate 2",
        candidate_email="c2@example.com",
        target_role="Data Scientist / ML Engineer",
        skills=["PyTorch"]
    )

    # Cryptographically unpredictable UUID4
    assert len(s1) == 36 and s1.count("-") == 4
    assert len(s2) == 36 and s2.count("-") == 4
    assert s1 != s2

    sess1 = await mgr.get_or_restore_session(s1)
    sess2 = await mgr.get_or_restore_session(s2)

    assert sess1["profile"].name == "Candidate 1"
    assert sess2["profile"].name == "Candidate 2"
    assert sess1["profile"].target_role != sess2["profile"].target_role

    # Non-existent session
    bad_id = str(uuid.uuid4())
    bad_sess = await mgr.get_or_restore_session(bad_id)
    assert bad_sess is None
