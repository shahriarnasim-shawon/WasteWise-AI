"""
In-process Event Bus using asyncio queues.
Designed with decoupled interfaces so Redis Pub/Sub could easily replace it in production.
"""

import asyncio
import json
from typing import Dict, Any, Set
from datetime import datetime


class EventBus:
    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue:
        """Register a new live subscriber queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue):
        """Unregister a subscriber queue."""
        async with self._lock:
            self._subscribers.discard(queue)

    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event payload to all active subscriber queues."""
        message = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        async with self._lock:
            dead_queues = []
            for queue in self._subscribers:
                try:
                    queue.put_nowait(message)
                except asyncio.QueueFull:
                    # Drop slow client or pop oldest
                    try:
                        queue.get_nowait()
                        queue.put_nowait(message)
                    except Exception:
                        dead_queues.append(queue)
            for dead in dead_queues:
                self._subscribers.discard(dead)

    def publish_sync(self, event_type: str, data: Dict[str, Any]):
        """Publish from synchronous contexts."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.publish(event_type, data), loop)
            else:
                loop.run_until_complete(self.publish(event_type, data))
        except RuntimeError:
            pass


event_bus = EventBus()

