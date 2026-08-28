from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Base class for all agents in the PrepSense AI system.

    Concrete agents should inherit from this class and implement the
    ``name`` property and the asynchronous ``run`` method.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the agent."""
        ...

    @abstractmethod
    async def run(self, input_data: Any) -> Any:
        """Execute the agent's core logic.

        Args:
            input_data: Arbitrary input specific to the agent.

        Returns:
            The result produced by the agent.
        """
        ...
