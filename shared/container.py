import logging
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)

class DIContainer:
    """A lightweight Dependency Injection container supporting lazy initialization and singletons."""
    
    def __init__(self):
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._is_singleton: Dict[str, bool] = {}

    def register(self, name: str, factory: Callable[[], Any], singleton: bool = True) -> None:
        """Register a dependency factory by name."""
        self._factories[name] = factory
        self._is_singleton[name] = singleton
        logger.debug(f"DIContainer: Registered '{name}' (singleton={singleton})")

    def resolve(self, name: str) -> Any:
        """Resolve a dependency, lazily initializing it if required."""
        if name not in self._factories:
            raise ValueError(f"Dependency '{name}' not found in container.")
            
        if self._is_singleton[name]:
            if name not in self._singletons:
                logger.debug(f"DIContainer: Lazily initializing singleton '{name}'")
                self._singletons[name] = self._factories[name]()
            return self._singletons[name]
            
        logger.debug(f"DIContainer: Creating new transient instance of '{name}'")
        return self._factories[name]()

# Global container instance
container = DIContainer()

def setup_container() -> None:
    """Bootstrap function to register all project dependencies."""
    # Import locally to avoid circular dependencies during initial module load
    from agents.resume.agent import ResumeAgent
    from agents.memory.agent import MemoryAgent
    from agents.planner.agent import PlannerAgent
    from agents.interviewer.agent import InterviewerAgent
    from agents.evaluator.agent import EvaluatorAgent
    from agents.report.agent import ReportAgent
    from rag.service import RAGService

    from services.resume_service import ResumeService
    from services.interview_service import InterviewService
    from services.evaluation_service import EvaluationService
    from services.report_service import ReportService
    
    from database.storage import StorageAdapter
    from database.repository import SessionRepository, ReportRepository

    # Database layer
    container.register("storage_adapter", lambda: StorageAdapter(), singleton=True)
    container.register("session_repository", lambda: SessionRepository(container.resolve("storage_adapter")), singleton=True)
    container.register("report_repository", lambda: ReportRepository(container.resolve("storage_adapter")), singleton=True)

    # RAG module
    container.register("rag_service", lambda: RAGService(knowledge_dir="knowledge", db_dir="rag/db"), singleton=True)

    # Voice module
    from shared.config import config as app_config
    from voice.service import VoiceService
    container.register("voice_service", lambda: VoiceService(config=app_config.voice), singleton=True)

    # Agent layer
    container.register("resume_agent", lambda: ResumeAgent(), singleton=True)
    container.register("memory_agent", lambda: MemoryAgent(), singleton=True)
    container.register("planner_agent", lambda: PlannerAgent(rag_service=container.resolve("rag_service")), singleton=True)
    container.register("interviewer_agent", lambda: InterviewerAgent(rag_service=container.resolve("rag_service")), singleton=True)
    container.register("evaluator_agent", lambda: EvaluatorAgent(rag_service=container.resolve("rag_service")), singleton=True)
    container.register("report_agent", lambda: ReportAgent(), singleton=True)

    # Service layer (injects agents)
    container.register("resume_service", lambda: ResumeService(container.resolve("resume_agent")), singleton=True)
    container.register("interview_service", lambda: InterviewService(
        container.resolve("planner_agent"), 
        container.resolve("interviewer_agent"), 
        container.resolve("memory_agent")
    ), singleton=True)
    container.register("evaluation_service", lambda: EvaluationService(
        container.resolve("evaluator_agent"), 
        container.resolve("memory_agent")
    ), singleton=True)
    container.register("report_service", lambda: ReportService(
        container.resolve("report_agent"), 
        container.resolve("memory_agent")
    ), singleton=True)

    logger.info("DIContainer: Application dependencies registered.")
