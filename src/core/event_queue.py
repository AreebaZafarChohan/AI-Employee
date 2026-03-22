"""
Event Queue for AI Employee Backend.
Handles asynchronous processing of events from watchers (Gmail, WhatsApp, etc.).
"""

import asyncio
import logging
from typing import Dict, Any, Callable, Awaitable
from collections import deque

logger = logging.getLogger("event_queue")

class EventQueue:
    def __init__(self, max_size: int = 100):
        self.queue = asyncio.Queue(maxsize=max_size)
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]] = {}
        self._worker_task: Optional[asyncio.Task] = None

    def register_handler(self, source: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Register an async handler for a specific event source."""
        self.handlers[source] = handler
        logger.info(f"Registered handler for event source: {source}")

    async def push_event(self, event_data: Dict[str, Any]):
        """Push an event to the queue for processing."""
        source = event_data.get("source", "unknown")
        logger.info(f"New event received from source: {source}")
        await self.queue.put(event_data)

    async def start_worker(self):
        """Start the background worker to process events."""
        if self._worker_task:
            return
        
        self._worker_task = asyncio.create_task(self._process_loop())
        logger.info("Event queue worker started.")

    async def _process_loop(self):
        """Main loop for processing events."""
        while True:
            event_data = await self.queue.get()
            source = event_data.get("source", "unknown")
            
            handler = self.handlers.get(source) or self.handlers.get("default")
            
            if handler:
                try:
                    logger.info(f"Processing event from {source}...")
                    await handler(event_data)
                except Exception as e:
                    logger.error(f"Error processing event from {source}: {e}", exc_info=True)
            else:
                logger.warning(f"No handler registered for event source: {source}")
            
            self.queue.task_done()

# Global instance
event_queue = EventQueue()
