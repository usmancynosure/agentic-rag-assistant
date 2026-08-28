"""Smoke tests for the health/readiness endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_health_ok() -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"


def test_ready_reports_checks() -> None:
    resp = client.get("/api/v1/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert "checks" in body
    assert set(body["checks"]) == {"anthropic_key", "voyage_key", "pinecone_key"}
