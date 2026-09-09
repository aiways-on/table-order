"""Health + security-header smoke tests.  [RES-06][SEC-04]"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_health_shallow_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_security_headers_present():
    resp = client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in resp.headers


def test_correlation_id_echoed():
    resp = client.get("/health")
    assert "X-Correlation-ID" in resp.headers


def test_metrics_endpoint():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert "request_count" in body
    assert "sse_active_connections" in body
