"""H offline product contracts; no inference of semantic correctness."""

from unittest.mock import patch
import pytest
from pydantic import ValidationError
from app.schemas import Discovery, ProposalResult, Proposal, AgentRequest
from app.learning import mock_learning_card
from test_learning_source import payload


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"question": " ", "reveal": "答案"},
        {"question": 1, "reveal": "a"},
        {"question": "q", "reveal": "a", "score": 1},
        {"question": "q", "reveal": "x" * 1001},
    ],
)
def test_strict_discovery(value):
    with pytest.raises(ValidationError):
        Discovery.model_validate(value)


def test_legacy_approval_edit_idempotence(client, star, db):
    from app.models import AgentRun
    from sqlalchemy import select

    card = mock_learning_card(AgentRequest(**payload()))
    proposal = Proposal(
        title="持续观察",
        description="观察已有文字记录的变化",
        steps=["观察文字记录"],
        rationale="海洋兴趣",
        estimated_minutes=8,
        estimated_budget=0,
        energy_level="low",
        based_on_star_ids=[star["id"]],
    )
    with patch(
        "app.model_adapter.ModelAdapter.proposals",
        return_value=ProposalResult(proposals=[proposal], learning_card=card),
    ):
        run = client.post("/api/agent/runs", json=payload()).json()
    assert run["status"] == "awaiting_decision"
    # Simulate persisted pre-H JSON (no discovery field), without migrating any DB.
    stored = db.scalar(select(AgentRun).where(AgentRun.run_id == run["run_id"]))
    state = dict(stored.state)
    state["learning_card"] = dict(state["learning_card"])
    state["learning_card"].pop("discovery", None)
    stored.state = state
    db.commit()
    assert "discovery" not in client.get(f"/api/agent/runs/{run['run_id']}").json()["state"]["learning_card"]
    decision = {"approved": True, "edited_proposal": {**proposal.model_dump(), "title": "自愿观察"}}
    url = f"/api/agent/runs/{run['run_id']}/decision"
    result = client.post(url, json=decision)
    assert result.status_code == 200, result.text
    assert client.post(url, json=decision).json() == result.json()
    assert len(client.get("/api/quests").json()) == 1
    assert client.get("/api/quests").json()[0]["title"] == "自愿观察"


def test_null_card_preserves_explanation_and_zero_action(client, star):
    result = ProposalResult(proposals=[], questions=["这份面包材料无法回答海洋发光问题。"])
    with patch("app.model_adapter.ModelAdapter.proposals", return_value=result):
        run = client.post("/api/agent/runs", json=payload("B")).json()
    assert run["status"] == "succeeded"
    assert run["state"]["questions"] == result.questions
    assert not run["state"]["proposals"] and not run["decisions"]
    assert (
        client.post(f"/api/agent/runs/{run['run_id']}/decision", json={"approved": True}).status_code == 409
    )
