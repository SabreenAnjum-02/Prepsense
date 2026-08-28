import json
import time
from typing import Optional, Any
from agents.shared.types import InterviewContext, InterviewPlan, InterviewQuestion, InterviewStage
from agents.planner.topic_selector import TopicSelector
from agents.planner.difficulty import DifficultyAdjuster
from agents.planner.followup import FollowupAnalyzer
from agents.planner.strategy import InterviewStrategy
from shared.llm.client import OllamaClient
from shared.llm.models import LLMRequest
from shared.error_handler import with_retry
from .utils import get_logger
from pydantic import ValidationError

logger = get_logger(__name__)


class QuestionGenerator:
    """Uses deterministic planning logic + a focused LLM call to generate interview questions.
    
    Deterministic decisions (topic, difficulty, follow-up, termination) are made
    by reusing the existing Planner components (TopicSelector, DifficultyAdjuster,
    FollowupAnalyzer, InterviewStrategy) before calling the LLM.
    
    The LLM is responsible ONLY for generating natural conversational text:
    a conversational_filler and a question.
    """

    def __init__(self, rag_service: Any = None) -> None:
        self.llm_client = OllamaClient()
        self.rag_service = rag_service
        
        # Reuse existing deterministic Planner components
        self._topic_selector = TopicSelector()
        self._difficulty_adjuster = DifficultyAdjuster()
        self._followup_analyzer = FollowupAnalyzer()
        self._strategy = InterviewStrategy()

    def _determine_interview_state(self, context: InterviewContext) -> dict:
        """Make all interview decisions deterministically using structured stage progression."""
        import os
        num_questions = len(context.questions)
        max_questions = int(os.getenv("PREPSENSE_MAX_QUESTIONS", "15"))
        
        # Termination check
        if num_questions >= max_questions:
            return {"should_end_interview": True, "reason": f"Maximum question limit ({max_questions}) reached."}
        
        # Determine current topic
        current_topic = context.questions[-1].topic if context.questions else None
        
        # Should we change topic?
        should_change = self._topic_selector.should_change_topic(context, current_topic)
        
        # Follow-up decision
        is_followup = False
        if not should_change and current_topic:
            is_followup = self._followup_analyzer.needs_followup(context)
        
        # Stage, Topic, and Question Type selection from competency state machine
        stage, next_topic, question_type, should_end = self._topic_selector.determine_stage_and_topic(
            context,
            is_followup=is_followup,
            max_questions=max_questions
        )
        
        # Difficulty
        difficulty = self._difficulty_adjuster.select_difficulty(context, is_followup)
        
        return {
            "should_end_interview": should_end,
            "topic": next_topic,
            "difficulty": difficulty,
            "question_type": question_type,
            "is_followup": is_followup,
            "stage": stage.value,
        }

    @with_retry(max_retries=2, delay=1.0)
    async def generate_question(
        self,
        context: InterviewContext,
        plan: Optional[InterviewPlan] = None,
        on_event: Optional[Any] = None,
        attempt: int = 0
    ) -> InterviewQuestion:
        t_total_start = time.perf_counter()
        logger.info(f"Generating question using deterministic planning + streaming LLM (attempt {attempt+1}).")
        
        # ── 1. Deterministic decisions ──
        t_decision_start = time.perf_counter()
        state = self._determine_interview_state(context)
        t_decision_end = time.perf_counter()
        decision_latency = t_decision_end - t_decision_start
        
        if state["should_end_interview"]:
            logger.info(f"Interview ending: {state.get('reason', 'done')}")
            return InterviewQuestion(
                question="",
                topic="",
                estimated_difficulty="",
                question_type="",
                is_followup=False,
                should_end_interview=True
            )
        
        topic = state["topic"]
        difficulty = state["difficulty"]
        question_type = state["question_type"]
        is_followup = state["is_followup"]
        stage = state.get("stage", "TECHNICAL")
        
        # ── 2. Build minimal history for conversational context ──
        t_prompt_start = time.perf_counter()
        
        last_qa = ""
        candidate_struggled = False
        if context.questions and context.answers:
            last_q = context.questions[-1]
            last_a = next((a for a in context.answers if a.question_id == last_q.question_id), None)
            if last_a:
                ans_text = last_a.candidate_answer.strip()
                last_qa = f"Last question asked: {last_q.question}\nCandidate's answer: {ans_text}\n\n"
                low_ans = ans_text.lower()
                if any(phrase in low_ans for phrase in ["don't know", "dont know", "lack of knowledge", "no idea", "never had", "not sure", "sorry", "cannot", "can't"]):
                    candidate_struggled = True
        
        # Build full previous questions list to prevent repetitions
        prev_questions = [q.question for q in context.questions if q.question]
        prev_q_str = ""
        if prev_questions:
            prev_q_str = "FORBIDDEN QUESTIONS (ALREADY ASKED - DO NOT REPEAT OR REPHRASE):\n"
            for pq in prev_questions:
                prev_q_str += f"- {pq}\n"
            prev_q_str += "\n"

        # Stage-specific guidance
        stage_guidance = ""
        if stage == "INTRODUCTION":
            stage_guidance = (
                "Ask the classic opening interview question: invite the candidate to introduce themselves, "
                "walk through their professional journey, and highlight their background with the technologies on their resume."
            )
        elif stage == "TECHNICAL":
            stage_guidance = f"Focus strictly on core technical concepts, syntax, internals, performance, or practical coding in {topic}."
        elif stage == "PROJECTS":
            stage_guidance = f"Focus on high-level architecture, system design, scalability, database design, caching, microservices, and trade-offs for {topic}. Do NOT ask basic syntax questions."
        elif stage == "BEHAVIORAL":
            stage_guidance = "Ask a STAR-method behavioral question about collaboration, overcoming technical challenges, tight deadlines, or conflict resolution."
        elif stage == "HR":
            stage_guidance = "Ask about career aspirations, team fit, work environment preferences, or project impact."

        followup_guidance = ""
        if is_followup:
            if candidate_struggled:
                followup_guidance = "Candidate struggled with the previous question. Pivot to an alternative fundamental concept or practical question within this topic."
            else:
                followup_guidance = "Dig deeper into the specific trade-offs or technical details mentioned in the candidate's last answer."

        # ── 3. RAG retrieval ──
        t_rag_start = time.perf_counter()
        rag_context_str = ""
        if self.rag_service:
            query = f"Interview topics and guidelines for {topic}"
            logger.info(f"Interviewer querying RAG: '{query}'")
            
            from shared.monitor import monitor
            results = self.rag_service.query(query, top_k=2)
            if context.session_id:
                monitor.record_agent_latency(context.session_id, "RAG_LATENCY", time.perf_counter() - t_rag_start)
            
            if results:
                rag_context_str = "Reference material:\n"
                for res in results:
                    rag_context_str += f"- {res.chunk.content}\n"
                rag_context_str += "\n"
        
        t_rag_end = time.perf_counter()
        rag_latency = t_rag_end - t_rag_start
        
        # ── 4. Build focused LLM prompt with rich Resume, JD and Conversation grounding ──
        candidate_name = context.candidate_profile.name if context.candidate_profile else "the candidate"
        cand = context.candidate_profile
        role_title = cand.target_role if cand and cand.target_role else "Software Engineer"
        
        # Build candidate resume & JD evidence context
        skills_str = ", ".join(cand.skills) if cand and cand.skills else "General technical skills"
        projects_str = "; ".join(cand.projects) if cand and cand.projects else "Engineering projects"
        exp_str = "; ".join(cand.experience) if cand and cand.experience else "Professional experience"
        jd_str = cand.target_jd if cand and cand.target_jd else "Standard role competencies"

        candidate_profile_block = (
            "CANDIDATE RESUME & ROLE CONTEXT:\n"
            f"- Candidate Name: {candidate_name}\n"
            f"- Target Role: {role_title}\n"
            f"- Resume Skills & Stack: {skills_str}\n"
            f"- Projects on Resume: {projects_str}\n"
            f"- Experience Summary: {exp_str}\n"
            f"- Job Description Focus: {jd_str[:300]}\n\n"
        )

        filler_examples = "'Got it, let us build on that.', 'Thanks for that context.', 'Understood, moving forward.'"
        if stage == "INTRODUCTION":
            filler_examples = "'Welcome to your interview today.', 'Glad to meet you today.', 'Welcome, let us get started.'"

        prompt = (
            f"You are a Senior Principal Interviewer conducting an authentic, conversational technical interview with {candidate_name} for the position of {role_title}.\n\n"
            f"{candidate_profile_block}"
            f"INTERVIEW STATE:\n"
            f"- Current Stage: {stage}\n"
            f"- Specific Topic: {topic}\n"
            f"- Target Difficulty: {difficulty}\n"
            f"- Stage Guidance: {stage_guidance}\n"
            f"{f'- Follow-up Directives: {followup_guidance}' if followup_guidance else ''}\n\n"
            f"{last_qa}"
            f"{prev_q_str}"
            f"{rag_context_str}"
            "CRITICAL CONVERSATIONAL INTERVIEWER RULES:\n"
            "1. NEVER ask basic textbook definition trivia (e.g. DO NOT ask 'What is X?', 'Define Y', 'What is Virtual DOM/CSS?').\n"
            "2. Ground your question in the candidate's actual resume skills, projects, and target role responsibilities.\n"
            "3. Ask realistic scenario-based, architecture, trade-off, debugging, or scaling questions that an authentic hiring manager would ask.\n"
            "4. If the candidate answered previously, naturally connect your question to what they said and probe their architectural decisions or trade-offs.\n"
            f"5. 'conversational_filler': A short, natural conversational transition phrase (e.g. {filler_examples}). Maximum 7 words, NO questions, NO question marks.\n"
            "6. 'question': Exactly ONE clear, compelling interview question ending with '?'. Must NOT repeat any forbidden questions.\n\n"
            "Return ONLY this JSON format:\n"
            '{"conversational_filler": "...", "question": "..."}\n'
        )
        
        # Dynamically increase temperature on retry attempts to prevent identical generation
        temp = min(0.4 + attempt * 0.25, 0.90)
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt="You are an expert, authentic technical interviewer. Return ONLY valid JSON with conversational_filler and question.",
            temperature=temp,
            max_tokens=180,
            require_json=True
        )
        
        t_prompt_end = time.perf_counter()
        prompt_construction_latency = (t_prompt_end - t_prompt_start) - rag_latency
        
        # ── 5. LLM streaming call ──
        response = await self.llm_client.generate_stream(request, on_event=on_event)
        
        if not response.parsed_json:
            logger.error("LLM failed to return valid JSON.")
            raise ValueError("Invalid JSON from LLM")
        
        # ── 6. Build InterviewQuestion deterministically ──
        t_val_start = time.perf_counter()
        
        llm_output = response.parsed_json
        
        filler = str(llm_output.get("conversational_filler", "")).strip()
        gen_q = str(llm_output.get("question", "")).strip()
        
        if "?" in filler:
            logger.warning("LLM generated question mark in filler; trimming.")
            filler = filler.split("?", 1)[0].strip()
            if filler:
                filler += "."
                
        try:
            question = InterviewQuestion(
                conversational_filler=filler,
                question=gen_q,
                topic=topic,
                estimated_difficulty=difficulty,
                question_type=question_type,
                is_followup=is_followup,
                follow_up_questions=[],
                expected_topics=[topic],
                should_end_interview=False
            )
        except ValidationError as e:
            logger.error(f"Interviewer output failed validation: {e}")
            raise ValueError(f"Validation failed: {e}")
        
        t_val_end = time.perf_counter()
        validation_latency = t_val_end - t_val_start
        
        t_total_end = time.perf_counter()
        total_interviewer_latency = t_total_end - t_total_start
        
        # ── 7. Record SessionMonitor metrics ──
        meta = response.metadata
        from shared.monitor import monitor
        if context.session_id:
            if meta.get("ttft") is not None:
                monitor.record_agent_latency(context.session_id, "STREAM_TTFT", meta["ttft"])
            if meta.get("t_filler_complete") is not None:
                monitor.record_agent_latency(context.session_id, "STREAM_FILLER_LATENCY", meta["t_filler_complete"])
            if meta.get("t_question_complete") is not None:
                monitor.record_agent_latency(context.session_id, "STREAM_QUESTION_LATENCY", meta["t_question_complete"])
            if meta.get("t_total") is not None:
                monitor.record_agent_latency(context.session_id, "STREAM_TOTAL_LATENCY", meta["t_total"])
        
        return question