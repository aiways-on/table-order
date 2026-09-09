"""In-memory publish/subscribe event bus backing SSE fan-out.  [NFR-P2]

Single-instance only. For horizontal scale, replace with Redis pub/sub
(see nfr-design scale-out path, RES-08). Subscribers get a per-connection
asyncio queue so a slow client never blocks publishers.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Event:
    topic: str
    data: dict[str, Any]


class EventBus:
    def __init__(self, max_queue: int = 100):
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._max_queue = max_queue
        self._loop: asyncio.AbstractEventLoop | None = None

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Record the serving event loop so sync endpoints can publish safely.

        SSE subscriber queues live on this loop; feeding them from a threadpool
        worker (where sync path operations run) requires call_soon_threadsafe.
        """
        self._loop = loop

    def _deliver(self, topic: str, data: dict[str, Any]) -> None:
        event = Event(topic=topic, data=data)
        for q in list(self._subscribers.get(topic, ())):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Drop for a lagging subscriber rather than block the publisher.
                pass

    async def publish(self, topic: str, data: dict[str, Any]) -> None:
        self._deliver(topic, data)

    def publish_sync(self, topic: str, data: dict[str, Any]) -> None:
        """Thread-safe publish for sync path operations. [NFR-P2]

        No-op if no loop is attached (e.g. service-level unit tests without an
        app). Otherwise the delivery is scheduled on the loop thread so the
        asyncio.Queue operations stay single-threaded.
        """
        loop = self._loop
        if loop is None:
            return
        loop.call_soon_threadsafe(self._deliver, topic, data)

    async def subscribe(self, topic: str) -> AsyncIterator[Event]:
        """Yield events for `topic` until the consumer stops iterating."""
        q: asyncio.Queue = asyncio.Queue(maxsize=self._max_queue)
        self._subscribers[topic].add(q)
        try:
            while True:
                yield await q.get()
        finally:
            self._subscribers[topic].discard(q)

    def subscriber_count(self, topic: str) -> int:
        return len(self._subscribers.get(topic, ()))


# Process-wide singleton.
event_bus = EventBus()
