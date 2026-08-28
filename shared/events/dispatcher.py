import logging
from typing import Any
from .events import BaseEvent
from .handlers import HandlerRegistry

logger = logging.getLogger(__name__)

class EventDispatcher:
    """Dispatches events to all registered handlers synchronously or asynchronously."""
    
    def __init__(self, registry: HandlerRegistry):
        self._registry = registry

    async def dispatch(self, event: BaseEvent) -> None:
        """Dispatches an event to all interested handlers."""
        event_type = type(event)
        handlers = self._registry.get_handlers(event_type)
        
        if not handlers:
            logger.debug(f"EventDispatcher: No handlers registered for {event_type.__name__}")
            return

        logger.info(f"EventDispatcher: Dispatching {event_type.__name__} to {len(handlers)} handlers.")
        for handler in handlers:
            try:
                # Assuming handlers might be async; in a robust system we'd check asyncio.iscoroutinefunction
                await handler(event)
            except Exception as e:
                logger.error(f"EventDispatcher: Error in handler {handler.__name__} for {event_type.__name__}: {e}")
