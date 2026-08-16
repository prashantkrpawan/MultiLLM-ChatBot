"""
Integration tests for the /api/chat endpoint.
All external HTTP calls are mocked — no real API keys required.
Run: cd backend && python -m pytest tests/ -v
"""
from __future__ import annotations

import os
import pytest
import httpx
import respx
from fastapi.testclient import TestClient

# Inject fake API keys before importing the app
os.environ.setdefault("MISTRAL_API_KEY", "fake-mistral-key")
os.environ.setdefault("GEMINI_API_KEY", "fake-gemini-key")
os.environ.setdefault("OPENROUTER_API_KEY", "fake-openrouter-key")
# Disable rate limiting in tests
os.environ.setdefault("RATE_LIMIT_REQUESTS", "1000")
os.environ.setdefault("RATE_LIMIT_WINDOW_SECONDS", "1")

from app.main import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=True)

FAKE_COMPLETION = {
    "choices": [{"message": {"content": "Test response."}}]
}


@respx.mock
def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@respx.mock
def test_providers_list():
    response = client.get("/api/providers")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert len(data["providers"]) == 3
    ids = {p["id"] for p in data["providers"]}
    assert ids == {"mistral", "gemini", "openrouter"}


@respx.mock
def test_chat_all_success():
    respx.post("https://api.mistral.ai/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=FAKE_COMPLETION)
    )
    respx.post("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions").mock(
        return_value=httpx.Response(200, json=FAKE_COMPLETION)
    )
    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=FAKE_COMPLETION)
    )

    response = client.post("/api/chat", json={"message": "What is Python?"})
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert len(data["results"]) == 3
    for result in data["results"]:
        assert result["status"] == "success"
        assert result["response"] == "Test response."


@respx.mock
def test_chat_one_provider_fails_others_succeed():
    """The overall request must still return 200 even when one provider fails."""
    respx.post("https://api.mistral.ai/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=FAKE_COMPLETION)
    )
    respx.post("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions").mock(
        return_value=httpx.Response(200, json=FAKE_COMPLETION)
    )
    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        side_effect=httpx.TimeoutException("timeout")
    )

    response = client.post("/api/chat", json={"message": "Test prompt"})
    assert response.status_code == 200
    data = response.json()
    statuses = {r["provider"]: r["status"] for r in data["results"]}
    assert statuses["mistral"] == "success"
    assert statuses["gemini"] == "success"
    assert statuses["openrouter"] == "timeout"


@respx.mock
def test_chat_empty_message_rejected():
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422


@respx.mock
def test_chat_invalid_attachment_mime():
    response = client.post("/api/chat", json={
        "message": "Look at this",
        "attachment": "aGVsbG8=",
        "attachment_mime": "application/pdf",
    })
    assert response.status_code == 422


@respx.mock
def test_regenerate_single_provider():
    respx.post("https://api.mistral.ai/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=FAKE_COMPLETION)
    )
    response = client.post("/api/chat/regenerate/mistral", json={"message": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mistral"
    assert data["status"] == "success"
