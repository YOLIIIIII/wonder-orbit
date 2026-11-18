"""J: explicit new Run, original user evidence, no implicit writes or live SDK."""

from copy import deepcopy
from unittest.mock import patch
import pytest
from app.learning import PUBLIC_SCIENCE_PREVIEW
from app.schemas import ProposalResult
from test_learning_source import payload


def origin(client):
    data = payload()
    data["learning_source"]["text"] = PUBLIC_SCIENCE_PREVIEW
    return client.post("/api/agent/runs", json=data).json()


def continuation(run, **changes):
    return dict(
        request_type="explore",
        exploration_direction="knowledge",
        parent_run_id=run["run_id"],
        text="荧光素酶起什么作用？",
        budget=0,
        available_minutes=10,
        energy_level="low",
        **changes,
    )


def test_continuation_source_history_idempotence_and_no_writes(client, star):
    parent = origin(client)
    before = deepcopy(parent)
    preferences = client.get("/api/preferences").json()
    data = continuation(parent)
    headers = {"Idempotency-Key": "continuation-once"}
    with patch("app.model_adapter.ChatOpenAI", side_effect=AssertionError("no network")):
        response = client.post("/api/agent/runs", json=data, headers=headers)
        assert response.status_code == 201, response.text
        child = response.json()
        assert client.post("/api/agent/runs", json=data, headers=headers).json() == child
    assert child["run_id"] != parent["run_id"] and child["status"] == "succeeded"
    assert child["state"]["request"]["parent_run_id"] == parent["run_id"]
    assert child["state"]["request"]["learning_source"] == parent["state"]["request"]["learning_source"]
    assert child["state"]["request"]["budget"] == 0
    assert child["state"]["related_stars"][0]["star_id"] == star["id"]
    assert "催化剂" in child["state"]["learning_card"]["takeaway"]
    assert child["state"]["proposals"] == []
    assert client.get(f"/api/agent/runs/{parent['run_id']}").json() == before
    assert client.get(f"/api/agent/runs/{child['run_id']}").json() == child
    assert client.get("/api/quests").json() == []
    assert client.get("/api/preferences").json() == preferences
    assert (
        client.post(f"/api/agent/runs/{child['run_id']}/decision", json={"approved": True}).status_code == 409
    )
    assert client.post("/api/agent/runs", json=continuation(child)).status_code == 409
    assert (
        client.post("/api/agent/runs", json={**data, "text": "changed"}, headers=headers).status_code == 409
    )


def test_insufficient_material_is_zero_action(client, star):
    parent = origin(client)
    data = {**continuation(parent), "text": parent["state"]["learning_card"]["follow_up_question"]}
    child = client.post("/api/agent/runs", json=data).json()
    assert child["status"] == "succeeded"
    assert not child["state"]["learning_card"] and not child["state"]["proposals"]
    assert "未解释" in child["state"]["questions"][0]


@pytest.mark.parametrize(
    "change,status",
    [
        ({"parent_run_id": "missing"}, 404),
        ({"exploration_direction": "creative"}, 422),
        ({"request_type": "collect"}, 422),
        ({"text": " "}, 422),
        ({"learning_source": {"text": "上次AI说过的内容"}}, 422),
    ],
)
def test_invalid_parent_and_source_fail_before_model_and_run(client, star, change, status):
    parent = origin(client)
    count = len(client.get("/api/agent/runs").json())
    with patch("app.main.adapter", side_effect=AssertionError("must reject before generation")):
        response = client.post("/api/agent/runs", json={**continuation(parent), **change})
    assert response.status_code == status, response.text
    assert len(client.get("/api/agent/runs").json()) == count


def test_current_source_gate_still_rejects_bad_model_card(client, star):
    parent = origin(client)
    card = deepcopy(parent["state"]["learning_card"])
    card["evidence_quote"] = "not in original material"
    with patch(
        "app.model_adapter.ModelAdapter.proposals",
        return_value=ProposalResult(learning_card=card, proposals=[]),
    ):
        child = client.post("/api/agent/runs", json=continuation(parent)).json()
    assert child["status"] == "succeeded" and not child["state"]["learning_card"]
    assert "校验" in child["state"]["questions"][0]


def test_collect_parent_rejected(client):
    parent = client.post("/api/agent/runs", json={"request_type": "collect", "text": "海洋"}).json()
    assert client.post("/api/agent/runs", json=continuation(parent)).status_code == 409


def test_adapter_receives_original_material_not_previous_ai(client, star):
    parent = origin(client)
    captured = []

    def generate(self, request, stars, preferences):
        captured.append((request.model_dump(mode="json"), stars))
        return ProposalResult(proposals=[], questions=["材料未展开这个问题。"])

    with patch("app.model_adapter.ModelAdapter.proposals", generate):
        client.post("/api/agent/runs", json=continuation(parent))
    request, stars = captured[0]
    assert request["learning_source"]["text"] == PUBLIC_SCIENCE_PREVIEW
    assert "learning_card" not in request
    assert parent["state"]["learning_card"]["takeaway"] not in str(request)
    assert stars[0]["star_id"] == star["id"]


def test_deleted_star_is_not_replaced_by_historical_ai_facts(client, star):
    parent = origin(client)
    assert client.delete(f"/api/stars/{star['id']}").status_code == 204
    with patch("app.model_adapter.ChatOpenAI", side_effect=AssertionError("no request without stars")):
        child = client.post("/api/agent/runs", json=continuation(parent)).json()
    assert child["status"] == "succeeded" and not child["state"]["proposals"]
    assert not child["state"].get("learning_card")


def test_incomplete_historical_request_rejected_without_new_run(client, star, db):
    from app.models import AgentRun

    parent = origin(client)
    saved = db.get(AgentRun, parent["run_id"])
    saved.state = {**saved.state, "request": {"text": "missing request_type"}}
    db.commit()
    before = len(client.get("/api/agent/runs").json())
    assert client.post("/api/agent/runs", json=continuation(parent)).status_code == 409
    assert len(client.get("/api/agent/runs").json()) == before
