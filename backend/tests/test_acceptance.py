"""MVP 验收发现的问题回归；不调用真实模型或个人数据库。"""

import pytest
from sqlalchemy import func, select

from app.config import Settings
from app.model_adapter import ModelAdapter, ModelFailure
from app.models import AgentRun, Reflection, Star
from app.schemas import AgentRequest


def test_failed_generation_key_does_not_return_created(client, db, monkeypatch):
    calls = []

    def timeout(self, request):
        calls.append(request.text)
        raise ModelFailure("timeout")

    monkeypatch.setattr(ModelAdapter, "draft", timeout)
    payload = {"request_type": "collect", "text": "海洋"}
    headers = {"Idempotency-Key": "failed-generation"}
    first = client.post("/api/agent/runs", json=payload, headers=headers)
    assert first.status_code == 502
    replay = client.post("/api/agent/runs", json=payload, headers=headers)
    assert replay.status_code == 409
    assert replay.json()["detail"]["run_id"] == first.json()["detail"]["run_id"]
    assert calls == ["海洋"]
    assert db.scalar(select(func.count()).select_from(AgentRun)) == 1
    assert db.scalar(select(func.count()).select_from(Star)) == 0


def test_failed_reflection_key_does_not_claim_saved(client, db, quest):
    payload = {"outcome": "completed", "user_feedback": "真实记录"}
    assert client.post(f"/api/quests/{quest}/reflections", json=payload).status_code == 201
    headers = {"Idempotency-Key": "failed-reflection"}
    first = client.post(f"/api/quests/{quest}/reflections", json=payload, headers=headers)
    assert first.status_code == 409
    failed = client.get("/api/agent/runs").json()[0]
    replay = client.post(f"/api/quests/{quest}/reflections", json=payload, headers=headers)
    assert replay.status_code == 409
    assert replay.json()["detail"]["run_id"] == failed["run_id"]
    assert db.scalar(select(func.count()).select_from(Reflection)) == 1
    assert any(event["status"] == "failed" for event in failed["events"])


@pytest.mark.parametrize(
    "exception_name,expected_kind",
    [
        ("APITimeoutError", "timeout"),
        ("RateLimitError", "rate_limit"),
        ("APIConnectionError", "model_unavailable"),
    ],
)
def test_provider_failure_classification_is_sanitized(monkeypatch, exception_name, expected_kind):
    error_class = type(exception_name, (Exception,), {})

    class FakeModel:
        def __init__(self, **kwargs):
            pass

        def bind_tools(self, *args, **kwargs):
            return self

        def invoke(self, messages):
            raise error_class("credential-like details must not appear in public errors")

    monkeypatch.setattr("app.model_adapter.ChatOpenAI", FakeModel)
    model = ModelAdapter(Settings(mock_mode=False, model_api_key="test-placeholder"))
    with pytest.raises(ModelFailure) as raised:
        model.draft(AgentRequest(request_type="collect", text="海洋"))
    assert raised.value.kind == expected_kind
    assert str(raised.value) == expected_kind
