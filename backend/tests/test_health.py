"""Tests for GET /health endpoint and application startup."""

import pytest
from fastapi.testclient import TestClient


def test_app_startup_and_health(client: TestClient) -> None:
    """Verify application starts and GET /health returns 200 with detector readiness."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["detector_loaded"] is True
    assert "lettucedect" in data["model_name"]
    assert "nli_loaded" in data
    assert "hybrid_ready" in data
    assert data["device"] == "cpu"
    assert "version" in data
    assert isinstance(data["supabase_configured"], bool)


def test_root_endpoint(client: TestClient) -> None:
    """Verify GET / returns basic status and links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"

