import os
import time
import uuid
import asyncio
import logging
import traceback
from typing import Any, Optional, List
from .router import AgentRouter
from .state import OrchestratorState
from shared.container import container
from shared.monitor import monitor
from agents.shared.types import AnswerRecord, QuestionRecord, PerformanceRecord, EvaluationResult

logger = logging.getLogger(__name__)

class InterviewPipeline:
    """Executes the core interview workflow using registered agents."""

    def __init__(self, router: AgentRouter, state: OrchestratorState):
        self.router = router
        self.state = state

    async def execute(self, resume_path: str, target_role: Optional[str] = None, target_jd: Optional[str] = None) -> Any:
        """Runs the entire end-to-end interview pipeline."""
        try:
            logger.info("Pipeline: Starting execution.")
            
            # 1. Resume Agent
            logger.info("Pipeline: Calling Resume Agent")
            profile = await self.router.dispatch("resume", {
                "file_path": resume_path,
                "target_role": target_role,
                "target_jd": target_jd
            })
            
            # 2. Memory Agent (Init Session)
            logger.info("Pipeline: Calling Memory Agent to init session")
            session_id = str(uuid.uuid4())
            await self.router.dispatch("memory", {"action": "initialize_session", "session_id": session_id})
            self.state.start_session(session_id)
            
            monitor.start_session(session_id)
            
            # 3. Memory Agent (Update Profile)
            await self.router.dispatch("memory", {
                "action": "store_candidate_profile",
                "session_id": session_id,
                "payload": profile
            })

            # Interview Loop
            interview_active = True
            question_count = 0
            
            eval_results: List[EvaluationResult] = []
            evaluation_tasks: List[asyncio.Task] = []
            pending_eval = None
            
            async def background_evaluate(q, ans, ctx, prof, session):
                t_eval_start = time.perf_counter()
                logger.info(f"[PIPELINE_TIMING] Evaluation started for question {q.question_id} at {time.strftime('%H:%M:%S')}")
                try:
                    eval_res = await self.router.dispatch("evaluator", {
                        "question": q,
                        "answer": ans,
                        "context": ctx,
                        "profile": prof
                    })
                    
                    t_eval = time.perf_counter() - t_eval_start
                    monitor.record_agent_latency(session, "EVALUATOR_LATENCY", t_eval)
                    logger.info(f"[PIPELINE_TIMING] Evaluation completed for question {q.question_id} in {t_eval:.2f}s at {time.strftime('%H:%M:%S')}")
                    
                    if eval_res and isinstance(eval_res, EvaluationResult):
                        eval_results.append(eval_res)
                        
                        perf_record = PerformanceRecord(
                            question_id=eval_res.question_id,
                            technical_score=eval_res.technical_score,
                            practical_score=eval_res.practical_score,
                            problem_solving_score=eval_res.problem_solving_score,
                            communication_score=eval_res.communication_score,
                            behavioral_score=eval_res.behavioral_score,
                            role_fit_score=eval_res.role_fit_score,
                            confidence_score=eval_res.confidence_score,
                            emotion_score=0.0,
                            overall_score=eval_res.overall_score
                        )
                        
                        logger.info("Background Evaluator: Updating Memory Agent")
                        
                        t_mem_start = time.perf_counter()
                        await self.router.dispatch("memory", {
                            "action": "update_scores",
                            "session_id": session,
                            "payload": perf_record
                        })
                        t_mem = time.perf_counter() - t_mem_start
                        monitor.record_agent_latency(session, "MEMORY_LATENCY", t_mem)
                    else:
                        logger.error(f"Background Evaluator: Evaluator returned invalid result for question {q.question_id}: {eval_res}")
                    
                except Exception as e:
                    logger.error(f"Background Evaluator failed for question {q.question_id}: {e}\n{traceback.format_exc()}")

            max_questions = int(os.getenv("PREPSENSE_MAX_QUESTIONS", "15"))
            
            class StreamingSpeechCoordinator:
                """Coordinates sequential speech of filler and question without audio overlap."""
                def __init__(self, voice_svc: Any, sess_id: str, mon: Any):
                    self.voice_service = voice_svc
                    self.session_id = sess_id
                    self.monitor = mon
                    self._lock = asyncio.Lock()
                    self.speech_tasks: list = []
                    self.t_stt_finish: Optional[float] = None
                    self.first_speech_latency: Optional[float] = None
                    self.filler_spoken = False
                    self.question_spoken = False

                async def speak_filler(self, filler_text: str):
                    async with self._lock:
                        if not filler_text or not filler_text.strip():
                            return
                        t_ready = time.perf_counter()
                        if self.t_stt_finish:
                            logger.info(f"[INTERVIEW_STREAM] filler_ready: {t_ready - self.t_stt_finish:.2f} sec")
                        
                        logger.info("[INTERVIEW_STREAM] filler_tts_started")
                        t0 = time.perf_counter()
                        if self.t_stt_finish and self.first_speech_latency is None:
                            self.first_speech_latency = t0 - self.t_stt_finish
                            logger.info(f"[INTERVIEW_STREAM] total_answer_to_first_speech_latency: {self.first_speech_latency:.2f} sec")

                        try:
                            await self.voice_service.speak(filler_text)
                            self.filler_spoken = True
                            logger.info("[INTERVIEW_STREAM] filler_tts_completed")
                        except Exception as e:
                            logger.error(f"[INTERVIEW_STREAM] Filler TTS failed: {e}")

                        tts_syn = getattr(self.voice_service.tts, "last_synthesis_latency", 0.0)
                        if self.session_id:
                            self.monitor.record_agent_latency(self.session_id, "FILLER_TTS_LATENCY", tts_syn)
                            if self.t_stt_finish:
                                total_next_q_lat = (t0 - self.t_stt_finish) + tts_syn
                                self.monitor.record_agent_latency(self.session_id, "TOTAL_NEXT_QUESTION_LATENCY", total_next_q_lat)
                                logger.info(f"TOTAL_NEXT_QUESTION_LATENCY: {total_next_q_lat:.2f} seconds")

                async def speak_question(self, question_text: str):
                    async with self._lock:
                        if not question_text or not question_text.strip():
                            return
                        t_ready = time.perf_counter()
                        if self.t_stt_finish:
                            logger.info(f"[INTERVIEW_STREAM] question_ready: {t_ready - self.t_stt_finish:.2f} sec")
                            
                        logger.info("[INTERVIEW_STREAM] question_tts_started")
                        t0 = time.perf_counter()
                        if self.t_stt_finish and self.first_speech_latency is None:
                            self.first_speech_latency = t0 - self.t_stt_finish
                            logger.info(f"[INTERVIEW_STREAM] total_answer_to_first_speech_latency: {self.first_speech_latency:.2f} sec")

                        try:
                            await self.voice_service.speak(question_text)
                            self.question_spoken = True
                            logger.info("[INTERVIEW_STREAM] question_tts_completed")
                        except Exception as e:
                            logger.error(f"[INTERVIEW_STREAM] Question TTS failed: {e}")

                        tts_syn = getattr(self.voice_service.tts, "last_synthesis_latency", 0.0)
                        if self.session_id:
                            self.monitor.record_agent_latency(self.session_id, "QUESTION_TTS_LATENCY", tts_syn)

                def enqueue_filler(self, filler_text: str):
                    task = asyncio.create_task(self.speak_filler(filler_text))
                    self.speech_tasks.append(task)

                def enqueue_question(self, question_text: str):
                    task = asyncio.create_task(self.speak_question(question_text))
                    self.speech_tasks.append(task)

                async def wait_for_speech_completion(self):
                    if self.speech_tasks:
                        await asyncio.gather(*self.speech_tasks, return_exceptions=True)

            latency_start_time = None

            while interview_active and question_count < max_questions: # Safety limit
                logger.info(f"Pipeline: --- Interview Loop {question_count+1} ---")
                
                # Fetch context
                t0 = time.perf_counter()
                context = await self.router.dispatch("memory", {
                    "action": "get_context",
                    "session_id": session_id
                })
                self.state.update_context(context)
                monitor.record_agent_latency(session_id, "MEMORY_LATENCY", time.perf_counter() - t0)

                # Setup Streaming Voice & Interviewer Agent
                voice_service = container.resolve("voice_service")
                speech_coordinator = StreamingSpeechCoordinator(voice_service, session_id, monitor)
                speech_coordinator.t_stt_finish = latency_start_time

                async def on_stream_event(event: Any):
                    if event.event_type == "filler_complete" and event.text:
                        speech_coordinator.enqueue_filler(event.text)
                    elif event.event_type == "stream_complete":
                        logger.info("[INTERVIEW_STREAM] stream_completed")

                # Interviewer Agent (Combined Decision + Streaming Generation)
                logger.info(f"[PIPELINE_TIMING] Next question generation started at {time.strftime('%H:%M:%S')}")
                logger.info("Pipeline: Calling Conversational Interviewer Agent")
                logger.info("[INTERVIEW_STREAM] stream_started")
                
                t0 = time.perf_counter()
                question = await self.router.dispatch("interviewer", {
                    "context": context,
                    "on_event": on_stream_event
                })
                t_interviewer = time.perf_counter() - t0
                monitor.record_agent_latency(session_id, "INTERVIEWER_LATENCY", t_interviewer)
                logger.info(f"[PIPELINE_TIMING] Next question ready in {t_interviewer:.2f}s at {time.strftime('%H:%M:%S')}")
                
                # If the interviewer decided to end the interview
                if not question or question.should_end_interview:
                    logger.info("Pipeline: Interviewer signaled to end interview.")
                    await speech_coordinator.wait_for_speech_completion()
                    break

                # Enqueue the verified, non-duplicate question for TTS
                speech_coordinator.enqueue_question(question.question)
                
                # --- Decoupled Evaluation Execution ---
                # Now that Interviewer LLM generation is complete and Kokoro/TTS is speaking the new question,
                # Ollama is completely idle. Spawn the background evaluation of the previous question NOW!
                if pending_eval:
                    prev_q = pending_eval[0]
                    logger.info(f"[PIPELINE_TIMING] Spawning background evaluation for previous question {prev_q.question_id}")
                    eval_task = asyncio.create_task(background_evaluate(*pending_eval))
                    evaluation_tasks.append(eval_task)
                    pending_eval = None
                    
                # Store Question in Memory
                q_record = QuestionRecord(
                    question_id=question.question_id,
                    question=question.question,
                    topic=question.topic,
                    difficulty=question.estimated_difficulty,
                    is_followup=question.is_followup
                )
                t0 = time.perf_counter()
                await self.router.dispatch("memory", {
                    "action": "add_question",
                    "session_id": session_id,
                    "payload": q_record
                })
                monitor.record_agent_latency(session_id, "MEMORY_LATENCY", time.perf_counter() - t0)
                
                # --- VoiceService Integration Fallback / Completion ---
                await speech_coordinator.wait_for_speech_completion()

                if not speech_coordinator.question_spoken:
                    spoken_text = question.question
                    if question.conversational_filler and not speech_coordinator.filler_spoken:
                        spoken_text = f"{question.conversational_filler} {question.question}"
                    t0 = time.perf_counter()
                    await voice_service.speak(spoken_text)
                    tts_synthesis = getattr(voice_service.tts, "last_synthesis_latency", 0.0)
                    monitor.record_agent_latency(session_id, "TTS_LATENCY", tts_synthesis)
                    if latency_start_time and speech_coordinator.first_speech_latency is None:
                        total_latency = (t0 - latency_start_time) + tts_synthesis
                        monitor.record_agent_latency(session_id, "TOTAL_NEXT_QUESTION_LATENCY", total_latency)
                        logger.info(f"TOTAL_NEXT_QUESTION_LATENCY: {total_latency:.2f} seconds")

                # 2. Automatically listen and transcribe the candidate's response
                logger.info("Pipeline: Listening for Candidate Response...")
                voice_result = await voice_service.listen_and_transcribe()
                
                if not voice_result.success:
                    logger.warning(f"Voice capture failed or was empty: {voice_result.error_message}. Skipping evaluation.")
                    continue
                    
                # Log STT Latency (STT is measured inside listen_and_transcribe and stored in processing_time)
                monitor.record_agent_latency(session_id, "STT_LATENCY", voice_result.processing_time)
                
                # Start measuring latency for the NEXT question right after STT finishes
                latency_start_time = time.perf_counter()
                
                logger.info(f"[PIPELINE_TIMING] Candidate answer received at {time.strftime('%H:%M:%S')}: {voice_result.transcript}")
                
                # 3. Map VoiceResult to AnswerRecord
                real_answer = AnswerRecord(
                    question_id=question.question_id,
                    candidate_answer=voice_result.transcript,
                    stt_transcript=voice_result.transcript,
                    time_taken_seconds=int(voice_result.audio_duration),
                    confidence=voice_result.confidence
                )
                
                # Store Answer in Memory
                t0 = time.perf_counter()
                await self.router.dispatch("memory", {
                    "action": "add_answer",
                    "session_id": session_id,
                    "payload": real_answer
                })
                monitor.record_agent_latency(session_id, "MEMORY_LATENCY", time.perf_counter() - t0)

                # 4. Queue evaluation to be executed as soon as next question generation starts
                pending_eval = (question, real_answer, context, profile, session_id)
                question_count += 1
            
            # If the last question's evaluation is still pending, spawn it now
            if pending_eval:
                prev_q = pending_eval[0]
                logger.info(f"[PIPELINE_TIMING] Spawning background evaluation for final question {prev_q.question_id}")
                eval_task = asyncio.create_task(background_evaluate(*pending_eval))
                evaluation_tasks.append(eval_task)
                pending_eval = None

            # Wait for all background evaluations to finish before generating the final report
            if evaluation_tasks:
                logger.info(f"Pipeline: Waiting for {len(evaluation_tasks)} pending background evaluations to complete...")
                for task in evaluation_tasks:
                    try:
                        await task
                    except Exception as e:
                        logger.error(f"Evaluation task exception: {e}")
            
            logger.info(f"Pipeline: Total evaluations collected: {len(eval_results)}")
            
            # 5. Report Agent
            logger.info("Pipeline: Interview loop finished. Calling Report Agent.")
            final_context = await self.router.dispatch("memory", {
                "action": "get_context",
                "session_id": session_id
            })
            
            report = await self.router.dispatch("report", {
                "context": final_context,
                "evaluations": eval_results
            })
            
            self.state.terminate()
            logger.info("Pipeline: Execution complete.")
            return report

        except Exception as e:
            logger.error(f"Pipeline: Execution failed - {e}")
            self.state.error_count += 1
            self.state.terminate()
            raise
