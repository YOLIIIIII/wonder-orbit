"""AGENT-004-B offline contracts; synthetic fixtures are not scientific evidence."""

from unittest.mock import patch
import pytest
from pydantic import ValidationError
from app.learning import MOCK_SOURCES, mock_learning_card, validate_learning_result
from app.schemas import AgentRequest, LearningCard, ProposalResult


def payload(key="A"):
    return dict(
        request_type="explore",
        text="海洋",
        exploration_direction="knowledge",
        available_minutes=10,
        budget=0,
        energy_level="low",
        learning_source=dict(
            text=MOCK_SOURCES[key], label="公开虚构测试材料", url="https://example.org/test"
        ),
    )


@pytest.mark.parametrize("direction", [None, "hands_on", "creative"])
def test_direction_rejects_material(client, direction):
    assert (
        client.post("/api/agent/runs", json={**payload(), "exploration_direction": direction}).status_code
        == 422
    )
    assert client.post("/api/agent/runs", json={**payload(), "request_type": "collect"}).status_code == 422


@pytest.mark.parametrize(
    "source",
    [
        dict(text=""),
        dict(text="  "),
        dict(text="x" * 5001),
        dict(text=12),
        dict(text="a", label="x" * 201),
        dict(text="a", url="x" * 2001),
        dict(text="a", url="file:///private"),
        dict(text="a", label=[]),
        dict(text="a", url=12),
    ],
)
def test_source_validation(client, source):
    assert client.post("/api/agent/runs", json={**payload(), "learning_source": source}).status_code == 422


@pytest.mark.parametrize("key", list(MOCK_SOURCES))
def test_run_persistence_approval_and_mock_no_network(client, star, key):
    with patch("app.model_adapter.ChatOpenAI", side_effect=AssertionError("network forbidden")):
        data = payload(key)
        result = client.post("/api/agent/runs", json=data, headers={"Idempotency-Key": "learning"})
    assert result.status_code == 201, result.text
    run = result.json()
    state = run["state"]
    assert state["request"]["learning_source"] == data["learning_source"]
    assert state["request"]["exploration_direction"] == "knowledge"
    assert client.get(f"/api/agent/runs/{run['run_id']}").json()["state"] == state
    assert client.get("/api/quests").json() == []
    assert len(client.get("/api/stars").json()) == 1
    assert client.get("/api/preferences").json()["candidates"] == []
    assert not any(e["name"] == "persist_approved_quest" for e in run["events"])
    changed = {**data, "learning_source": dict(text="different")}
    assert (
        client.post("/api/agent/runs", json=changed, headers={"Idempotency-Key": "learning"}).status_code
        == 409
    )
    if key in {"B", "E"}:
        assert state["learning_card"] is None and not state["proposals"]
        return
    card = state["learning_card"]
    assert card["evidence_quote"] == MOCK_SOURCES[key][card["quote_start"] : card["quote_end"]]
    if key == "C":
        assert "部分" in card["takeaway"] and "可能" in card["takeaway"]
    if key == "D":
        assert any("冲突" in u for u in card["uncertainties"])
    assert state["proposals"][0]["based_on_star_ids"] == [star["id"]]
    url = f"/api/agent/runs/{run['run_id']}/decision"
    approved = client.post(url, json={"approved": True})
    assert approved.status_code == 200
    assert client.post(url, json={"approved": True}).json() == approved.json()
    quests = client.get("/api/quests").json()
    assert len(quests) == 1 and "learning_card" not in quests[0]


@pytest.mark.parametrize(
    "change",
    [
        dict(evidence_quote="伪造"),
        dict(evidence_quote=" "),
        dict(quote_start=1),
        dict(quote_end=99999),
        dict(source_label="伪造机构"),
        dict(source_url="https://fake.example"),
    ],
)
def test_fail_closed(change):
    request = AgentRequest(**payload())
    card = mock_learning_card(request).model_copy(update=change)
    result = validate_learning_result(request, ProposalResult(proposals=[], learning_card=card))
    assert result.learning_card is None and result.questions and not result.proposals


def test_exact_original_unicode_and_invalid_kind():
    source = "  😀测试材料原文  "
    request = AgentRequest(**{**payload(), "learning_source": dict(text=source)})
    card = LearningCard(
        evidence_quote="😀测试材料原文",
        quote_start=2,
        quote_end=10,
        takeaway="解释",
        interest_relevance="相关",
        follow_up_question="问题？",
        uncertainties=["未核实"],
    )
    assert request.model_dump()["learning_source"]["text"] == source
    card.quote_end = source.index("文") + 1
    assert (
        validate_learning_result(request, ProposalResult(proposals=[], learning_card=card)).learning_card
        == card
    )
    with pytest.raises(ValidationError):
        LearningCard(**{**card.model_dump(), "source_kind": "verified"})


def test_invalid_adapter_result_never_reaches_state(client, star):
    request = AgentRequest(**payload())
    result = ProposalResult(proposals=[], learning_card=mock_learning_card(request))
    result.learning_card.evidence_quote = "fabricated"
    with patch("app.model_adapter.ModelAdapter.proposals", return_value=result):
        run = client.post("/api/agent/runs", json=payload()).json()
    assert run["state"]["learning_card"] is None
    assert run["state"]["questions"]
