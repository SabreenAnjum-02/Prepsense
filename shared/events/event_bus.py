import logging
from typing import Any
from .events import BaseEvent
from .handlers import HandlerRegistry, EventHandler
from .dispatcher import EventDispatcher

logger = logging.getLogger(__name__)

class EventBus:
    """The central message bus for decoupling component communication."""
    
    def __init__(self):
        self._registry = HandlerRegistry()
        self._dispatcher = EventDispatcher(self._registry)

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Subscribe a handler function to a specific event type."""
        self._registry.register(event_type, handler)

    async def publish(self, event: BaseEvent) -> None:
        """Publish an event to the bus."""
        logger.info(f"EventBus: Publishing event {type(event).__name__}")
        await self._dispatcher.dispatch(event)

# Global default bus instance (optional, depending on dependency injection preference)
default_bus = EventBus()
