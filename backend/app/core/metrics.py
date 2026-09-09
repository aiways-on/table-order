"""Lightweight in-process metrics (request count/latency/errors/SSE).  [RES-05][NFR-O2]

Exposed via /metrics as JSON. For a full stack, swap for a Prometheus exporter
(scale-out path, RES-08).
"""
from __future__ import annotations

import threading


class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.request_count = 0
        self.error_count = 0
        self.total_latency = 0.0
        self.sse_active = 0

    def observe_request(self, path: str, latency: float, is_error: bool = False) -> None:
        with self._lock:
            self.request_count += 1
            self.total_latency += latency
            if is_error:
                self.error_count += 1

    def sse_connected(self) -> None:
        with self._lock:
            self.sse_active += 1

    def sse_disconnected(self) -> None:
        with self._lock:
            self.sse_active = max(0, self.sse_active - 1)

    def snapshot(self) -> dict:
        with self._lock:
            avg = self.total_latency / self.request_count if self.request_count else 0.0
            return {
                "request_count": self.request_count,
                "error_count": self.error_count,
                "avg_latency_seconds": round(avg, 6),
                "sse_active_connections": self.sse_active,
            }


metrics = Metrics()
