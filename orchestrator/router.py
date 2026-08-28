import logging
from typing import Dict, Any
from agents.shared.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class AgentRouter:
    """Registry and dispatcher for all AI agents."""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """Register an agent by name."""
        self._agents[name] = agent
        logger.info(f"AgentRouter: Registered agent '{name}'")

    async def dispatch(self, agent_name: str, payload: Any) -> Any:
        """Route a payload to a specific agent and await its result."""
        if agent_name not in self._agents:
            logger.error(f"AgentRouter: Agent '{agent_name}' not found.")
            raise ValueError(f"Agent '{agent_name}' is not registered.")
        
        logger.info(f"AgentRouter: Dispatching payload to '{agent_name}'")
        agent = self._agents[agent_name]
        try:
            return await agent.run(payload)
        except Exception as e:
            logger.error(f"AgentRouter: Agent '{agent_name}' execution failed: {e}")
            raise
