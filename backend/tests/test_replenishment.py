"""K: new user evidence uses the root Explore contract; J remains strict."""

from copy import deepcopy
from unittest.mock import patch
import pytest
from app.schemas import ProposalResult
from test_learning_source import payload
from test_continuation import origin, continuation


@pytest.mark.parametrize("failure", ["insufficient", "source_gate", "no_source"])
@pytest.mark.parametrize("budget", [None, 0])
def test_replenishment_is_new_root_and_preserves_old_run(client, star, failure, budget):
    data = payload()
    if failure == "no_source":
        data.pop("learning_source")
    result = ProposalResult(proposals=[], questions=["材料不足"])
    if failure == "source_gate":
        parent = origin(client)
        card = deepcopy(parent["state"]["learning_card"])
        card["evidence_quote"] = "不存在的引文"
        result = ProposalResult(learning_card=card, proposals=[])
    with patch("app.model_adapter.ModelAdapter.proposals", return_value=result):
        original = client.post("/api/agent/runs", json=data).json()
    assert not original["state"]["learning_card"]
    before = deepcopy(original)
    submitted = {
        **payload(),
        "text": "海洋新问题",
        "budget": budget,
        "learning_source": {"text": "新提交的原始材料", "label": "新来源", "url": None},
    }
    captured = []

    def generate(self, request, stars, preferences):
        captured.append(request.model_dump(mode="json"))
        return ProposalResult(proposals=[], questions=["仍不足，不承诺必然回答"])

    headers = {"Idempotency-Key": "replenish-once"}
    with patch("app.model_adapter.ModelAdapter.proposals", generate):
        response = client.post("/api/agent/runs", json=submitted, headers=headers)
        assert response.status_code == 201
        new = response.json()
        assert client.post("/api/agent/runs", json=submitted, headers=headers).json() == new
    assert len(captured) == 1
    assert captured[0]["learning_source"] == submitted["learning_source"]
    assert captured[0]["text"] == submitted["text"]
    assert captured[0]["budget"] == budget
    assert "parent_run_id" not in captured[0]
    assert "learning_card" not in captured[0]
    assert new["run_id"] != original["run_id"]
    assert "parent_run_id" not in new["state"]["request"]
    assert client.get(f"/api/agent/runs/{original['run_id']}").json() == before
    assert client.get("/api/quests").json() == []
    assert (
        client.post(f"/api/agent/runs/{new['run_id']}/decision", json={"approved": True}).status_code == 409
    )
    # K must never relax J's replacement prohibition, even with valid new material.
    parent = origin(client)
    assert (
        client.post(
            "/api/agent/runs", json={**continuation(parent), "learning_source": submitted["learning_source"]}
        ).status_code
        == 422
    )
