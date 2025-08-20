import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import importlib
import pytest
from fastapi.testclient import TestClient

# Ensure repo root is on sys.path so `import backend.app` works regardless of CWD
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

backend_app = importlib.import_module("backend.app")
app = backend_app.app
ModeEnum = backend_app.ModeEnum


@pytest.fixture(autouse=True)
def _configure_env(monkeypatch):
    # Lower rate limits for tests
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "3")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SEC", "5")
    # Fake OpenAI config (calls will be monkeypatched)
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("SUMMARIZE_PROMPT_ID", "pmpt_sum")
    monkeypatch.setenv("REPHRASE_PROMPT_ID", "pmpt_rewrite")
    monkeypatch.setenv("EXTRACT_JSON_PROMPT_ID", "pmpt_json")
    monkeypatch.setenv("CLASSIFY_SENTIMENT_PROMPT_ID", "pmpt_cls")
    # Reset in-memory rate limit buckets between tests
    try:
        backend_app.RATE_BUCKETS.clear()
    except Exception:
        pass


@pytest.fixture
def client():
    return TestClient(app)


def mock_responses_create_ok(payload_text: str, prompt_tokens: int = 10, completion_tokens: int = 20):
    class Usage:
        def __init__(self):
            self.input_tokens = prompt_tokens
            self.output_tokens = completion_tokens
            self.total_tokens = prompt_tokens + completion_tokens

    class Resp:
        def __init__(self, text: str):
            self.output_text = text
            self.usage = Usage()

        def dict(self):
            return {"text": self.output_text}

    return Resp(payload_text)


def test_summarize_returns_200_and_non_empty(monkeypatch, client):
    def fake_create(*args, **kwargs):
        prompt = kwargs.get("prompt") or (len(args) > 1 and args[1])
        if isinstance(prompt, dict):
            assert prompt.get("id") == os.getenv("SUMMARIZE_PROMPT_ID")
        return mock_responses_create_ok("summary text")

    monkeypatch.setattr(backend_app, "OpenAI", lambda api_key=None: type("C", (), {"responses": type("R", (), {"create": staticmethod(fake_create)})})())

    r = client.post("/api/run", json={"mode": "summarize", "text": "hello world"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["result"], str)
    assert data["result"]


def test_rephrase_without_tone_returns_400(client):
    r = client.post("/api/run", json={"mode": "rephrase", "text": "hello"})
    assert r.status_code == 400


def test_classify_returns_allowed_label(monkeypatch, client):
    def fake_create(*args, **kwargs):
        return mock_responses_create_ok("positive")

    monkeypatch.setattr(backend_app, "OpenAI", lambda api_key=None: type("C", (), {"responses": type("R", (), {"create": staticmethod(fake_create)})})())

    r = client.post("/api/run", json={"mode": "classify", "text": "i love it"})
    assert r.status_code == 200
    data = r.json()
    assert data["result"] in ["positive", "neutral", "negative"]


def test_extract_json_returns_valid_json(monkeypatch, client):
    def fake_create(*args, **kwargs):
        return mock_responses_create_ok(json.dumps({"date": "2025-06-18", "time": "09:00", "participants": ["A", "B"]}))

    monkeypatch.setattr(backend_app, "OpenAI", lambda api_key=None: type("C", (), {"responses": type("R", (), {"create": staticmethod(fake_create)})})())

    r = client.post("/api/run", json={"mode": "extract_json", "text": "msg"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["result"], dict)
    for key in ["date", "time", "participants"]:
        assert key in data["result"], f"missing {key}"


def test_rate_limit_returns_429(monkeypatch, client):
    def fake_create(*args, **kwargs):
        return mock_responses_create_ok("ok")

    monkeypatch.setattr(backend_app, "OpenAI", lambda api_key=None: type("C", (), {"responses": type("R", (), {"create": staticmethod(fake_create)})})())

    # First 3 within window OK
    for _ in range(3):
        r = client.post("/api/run", json={"mode": "summarize", "text": "x"})
        assert r.status_code == 200

    # Fourth should 429
    r = client.post("/api/run", json={"mode": "summarize", "text": "x"})
    assert r.status_code == 429
