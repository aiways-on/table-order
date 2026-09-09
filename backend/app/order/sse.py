"""Server-Sent Events stream generator backing real-time order updates.  [NFR-P2]

SSE endpoints are async (they run on the serving event loop), so they can await
the in-memory event bus' per-connection asyncio.Queue directly — unlike the sync
CRUD endpoints. A periodic keep-alive comment holds the connection open through
proxies; on client disconnect the generator's finally clause releases the
subscription and updates metrics. Clients re-fetch via REST on reconnect. [RES-10]
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from app.core.events import event_bus
from app.core.metrics import metrics

_KEEPALIVE_SECONDS = 15

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # disable proxy buffering (nginx)
}


async def event_stream(topic: str) -> AsyncIterator[bytes]:
    metrics.sse_connected()
    subscription = event_bus.subscribe(topic)
    try:
        yield b": connected\n\n"  # open the stream immediately
        while True:
            try:
                event = await asyncio.wait_for(
                    subscription.__anext__(), timeout=_KEEPALIVE_SECONDS
                )
            except asyncio.TimeoutError:
                yield b": ping\n\n"  # keep-alive
                continue
            except StopAsyncIteration:
                break
            payload = json.dumps(event.data, default=str)
            yield f"data: {payload}\n\n".encode()
    finally:
        await subscription.aclose()
        metrics.sse_disconnected()
