from typing import Callable, Any
from .events import BaseEvent
import logging

logger = logging.getLogger(__name__)

# A handler is simply a callable that takes an event and returns nothing
EventHandler = Callable[[BaseEvent], Any]

class HandlerRegistry:
    """Stores the mapping of events to their respective handlers."""
    
    def __init__(self):
        # Maps event type (class) to a list of handler functions
        self._registry = {}

    def register(self, event_type: type, handler: EventHandler) -> None:
        if event_type not in self._registry:
            self._registry[event_type] = []
        self._registry[event_type].append(handler)
        logger.info(f"Registered handler {handler.__name__} for event {event_type.__name__}")

    def get_handlers(self, event_type: type) -> list[EventHandler]:
        return self._registry.get(event_type, [])
