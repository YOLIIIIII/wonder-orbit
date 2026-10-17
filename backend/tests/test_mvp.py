import json
from pathlib import Path
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select
from app.config import Settings
from app.model_adapter import ModelAdapter, ModelFailure
from app.models import AgentRun, Quest, Reflection, Star
from app.schemas import AgentRequest, Proposal, StarInput
from app.tools import ToolRegistry
from conftest import proposal_run


def test_crud_and_filters(client, star):
    assert client.get(f"/api/stars/{star['id']}").json()["original_text"] == star["original_text"]
    body = {k: v for k, v in star.items() if k not in {"id", "created_at", "updated_at"}}
    body.update(title="海洋发光", status="archived")
    assert client.put(f"/api/stars/{star['id']}", json=body).status_code == 200
    assert len(client.get("/api/stars?category=自然&status=archived").json()) == 1
    assert client.get("/api/stars?category=宇宙").json() == []
    assert client.get("/api/stats").json()["stars"] == 1
    assert client.delete(f"/api/stars/{star['id']}").status_code == 204
    assert client.get(f"/api/stars/{star['id']}").status_code == 404


def test_draft_confirmation_no_automatic_write(client, db):
    raw = "我一直想了解海洋和星空"
    run = client.post("/api/agent/runs", json={"request_type": "collect", "text": raw}).json()
    assert run["mode"] == "mock"
    assert run["state"]["draft"]["draft"]["interest_reason"] is None
    assert db.scalar(select(func.count()).select_from(Star)) == 0
    edited = run["state"]["draft"]["draft"]
    edited.update(title="自己的标题", interest_reason="我喜欢自然", original_text="尝试改原文")
    decision = {"approved": True, "edited_star": edited}
    approved = client.post(f"/api/agent/runs/{run['run_id']}/decision", json=decision).json()
    stored = client.get(f"/api/stars/{approved['star_id']}").json()
    assert stored["title"] == "自己的标题"
    assert stored["original_text"] == raw
    assert client.post(f"/api/agent/runs/{run['run_id']}/decision", json=decision).json() == approved
    assert db.scalar(select(func.count()).select_from(Star)) == 1


def test_rejection_leaves_no_star(client):
    run = client.post("/api/agent/runs", json={"request_type": "collect", "text": "音乐"}).json()
    assert (
        client.post(f"/api/agent/runs/{run['run_id']}/decision", json={"approved": False}).status_code == 200
    )
    assert client.get("/api/stars").json() == []
    assert (
        client.post(f"/api/agent/runs/{run['run_id']}/decision", json={"approved": True}).status_code == 409
    )


@pytest.mark.parametrize("text", ["", "  "])
def test_empty_request_rejected(client, text):
    assert client.post("/api/agent/runs", json={"request_type": "collect", "text": text}).status_code == 422


def test_search_matches_grounded_records(client, star):
    results = client.get("/api/search?q=海洋").json()
    assert results[0]["star_id"] == star["id"]
    assert "海洋" in results[0]["match_basis"]
    assert client.get("/api/search?q=火箭").json() == []
    assert client.get("/api/stars?q=深海").json()[0]["id"] == star["id"]


def test_relations_are_actual_tags_or_category(client, star):
    client.post(
        "/api/stars", json={"title": "海边", "original_text": "看海", "category": "生活", "tags": ["海洋"]}
    )
    edges = client.get("/api/relations").json()
    assert len(edges) == 1
    assert edges[0]["reasons"] == ["共同标签：海洋"]
    assert star["id"] in [edges[0]["from_id"], edges[0]["to_id"]]


def test_langgraph_steps_tools_and_approval(client, star, db):
    run = proposal_run(client)
    nodes = [e["name"] for e in run["events"] if e["kind"] == "node"]
    assert nodes == [
        "understand_request",
        "retrieve_related_stars",
        "load_preferences",
        "generate_suggestions",
        "validate_suggestions",
        "await_user_decision",
    ]
    tools = [e["name"] for e in run["events"] if e["kind"] == "tool"]
    assert "get_star_details" in tools and "validate_quest_proposal" in tools
    assert run["state"]["proposals"][0]["based_on_star_ids"] == [star["id"]]
    assert db.scalar(select(func.count()).select_from(Quest)) == 0
    result = client.post(f"/api/agent/runs/{run['run_id']}/decision", json={"approved": True})
    assert result.status_code == 200
    assert db.scalar(select(func.count()).select_from(Quest)) == 1
    again = client.post(f"/api/agent/runs/{run['run_id']}/decision", json={"approved": True})
    assert again.json() == result.json()


def test_no_matching_history_asks_question(client):
    run = proposal_run(client)
    assert run["state"]["proposals"] == []
    assert run["state"]["questions"]
    assert (
        client.post(f"/api/agent/runs/{run['run_id']}/decision", json={"approved": True}).status_code == 422
    )


def test_request_idempotency_and_conflicts(client, star):
    first = proposal_run(client, "fixed-key")
    assert proposal_run(client, "fixed-key")["run_id"] == first["run_id"]
    assert (
        client.post(
            "/api/agent/runs",
            json={"request_type": "collect", "text": "音乐"},
            headers={"Idempotency-Key": "fixed-key"},
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("estimated_minutes", 11),
        ("estimated_budget", 1),
        ("estimated_budget", None),
        ("energy_level", "high"),
        ("based_on_star_ids", ["made-up-id"]),
    ],
)
def test_edited_proposal_validates_again(client, star, field, value):
    run = proposal_run(client)
    proposal = run["state"]["proposals"][0]
    proposal[field] = value
    response = client.post(
        f"/api/agent/runs/{run['run_id']}/decision", json={"approved": True, "edited_proposal": proposal}
    )
    assert response.status_code == 422
    assert client.get("/api/quests").json() == []


def test_deleted_basis_cannot_be_approved(client, star):
    run = proposal_run(client)
    client.delete(f"/api/stars/{star['id']}")
    assert (
        client.post(f"/api/agent/runs/{run['run_id']}/decision", json={"approved": True}).status_code == 422
    )


def test_current_preferences_revalidated_at_approval(client, star):
    run = proposal_run(client)
    assert client.put("/api/preferences", json={"max_minutes": 1}).status_code == 200
    assert (
        client.post(f"/api/agent/runs/{run['run_id']}/decision", json={"approved": True}).status_code == 422
    )


@pytest.mark.parametrize("budget,cap", [(None, 5), (0, 0), (3, 3), (8, 5)])
def test_request_budget_and_preference_use_stricter_cap(client, star, budget, cap):
    assert client.put("/api/preferences", json={"max_budget": 5}).status_code == 200
    response = client.post(
        "/api/agent/runs", json={"request_type": "explore", "text": "深海", "budget": budget}
    )
    assert response.status_code == 201
    run = response.json()
    proposal = run["state"]["proposals"][0]
    url = f"/api/agent/runs/{run['run_id']}/decision"
    for cost in [None, cap + 1]:
        proposal["estimated_budget"] = cost
        rejected = client.post(url, json={"approved": True, "edited_proposal": proposal})
        assert rejected.status_code == 422
        assert client.get("/api/quests").json() == []
    proposal["estimated_budget"] = cap
    assert client.post(url, json={"approved": True, "edited_proposal": proposal}).status_code == 200
    assert client.get("/api/quests").json()[0]["estimated_budget"] == cap


def test_no_budget_caps_allows_unknown_cost(client, star):
    response = client.post("/api/agent/runs", json={"request_type": "explore", "text": "深海"})
    assert response.status_code == 201
    run = response.json()
    proposal = run["state"]["proposals"][0]
    proposal["estimated_budget"] = None
    assert (
        client.post(
            f"/api/agent/runs/{run['run_id']}/decision",
            json={"approved": True, "edited_proposal": proposal},
        ).status_code
        == 200
    )
    assert client.get("/api/quests").json()[0]["estimated_budget"] is None


@pytest.mark.parametrize("constraints,expected", [(["仅室内", "不购买"], True), (["不要使用纸笔"], False)])
def test_constraint_support_and_clarification(client, star, constraints, expected):
    client.put("/api/preferences", json={"constraints": constraints})
    run = proposal_run(client)
    assert bool(run["state"]["proposals"]) is expected
    if not expected:
        assert run["state"]["questions"]


def test_time_preference_conflict_asks_question(client, star):
    client.put("/api/preferences", json={"min_minutes": 15, "max_minutes": 30})
    run = proposal_run(client)
    assert run["state"]["proposals"] == []
    assert run["state"]["questions"]


def test_tool_allowlist_and_parameter_validation(db):
    run = AgentRun(events=[], state={})
    tools = ToolRegistry(db, ModelAdapter(Settings()), run)
    with pytest.raises(HTTPException) as unknown:
        tools.call("execute_sql", {"sql": "DROP TABLE stars"})
    assert unknown.value.status_code == 400
    with pytest.raises(ValidationError):
        tools.call("search_stars", {"query": "海洋", "arbitrary": True})
    with pytest.raises(HTTPException) as denied:
        tools.call(
            "record_reflection",
            {"quest_id": "missing", "reflection": {"outcome": "completed", "user_feedback": "x"}},
        )
    assert denied.value.status_code == 403
    assert all(event["status"] == "failed" for event in run.events)


def test_unapproved_quest_tool_denied(client, db, star):
    run = proposal_run(client)
    tools = ToolRegistry(db, ModelAdapter(Settings()), AgentRun(events=[], state={}))
    with pytest.raises(HTTPException) as denied:
        tools.call(
            "persist_approved_quest", {"proposal": run["state"]["proposals"][0], "proposal_key": "fake"}
        )
    assert denied.value.status_code == 403


@pytest.mark.parametrize("outcome", ["completed", "skipped"])
def test_reflection_persisted_candidates_need_confirmation(client, db, quest, outcome):
    payload = {
        "outcome": outcome,
        "user_feedback": "真实反馈",
        "liked_aspects": ["自然观察"],
        "disliked_aspects": ["太短"],
    }
    response = client.post(
        f"/api/quests/{quest}/reflections", json=payload, headers={"Idempotency-Key": "feedback-key"}
    )
    assert response.status_code == 201, response.text
    repeated = client.post(
        f"/api/quests/{quest}/reflections", json=payload, headers={"Idempotency-Key": "feedback-key"}
    )
    assert repeated.json()["run_id"] == response.json()["run_id"]
    assert db.scalar(select(func.count()).select_from(Reflection)) == 1
    stored = client.get("/api/quests").json()[0]
    assert stored["status"] == outcome
    assert stored["reflection"]["user_feedback"] == "真实反馈"
    pref = client.get("/api/preferences").json()
    assert pref["explicit"]["categories"] == []
    candidate = pref["candidates"][0]
    assert candidate["reflection_id"] == stored["reflection"]["id"]
    assert client.post(f"/api/preferences/candidates/{candidate['id']}/confirm").status_code == 200
    assert client.get("/api/preferences").json()["explicit"]["categories"] == ["自然观察"]
    assert client.delete("/api/preferences").status_code == 204


def test_cannot_delete_star_used_by_quest(client, star, quest):
    assert client.delete(f"/api/stars/{star['id']}").status_code == 409


def test_second_feedback_rejected_with_audit(client, quest):
    payload = {"outcome": "skipped", "user_feedback": "这次没有时间"}
    assert client.post(f"/api/quests/{quest}/reflections", json=payload).status_code == 201
    assert client.post(f"/api/quests/{quest}/reflections", json=payload).status_code == 409
    run = client.get("/api/agent/runs").json()[0]
    assert run["status"] == "failed"
    assert any(e["status"] == "failed" for e in run["events"])


def test_model_failure_audited_and_retry(client, monkeypatch):
    original = ModelAdapter.draft

    def fail(self, request):
        raise ModelFailure("timeout")

    monkeypatch.setattr(ModelAdapter, "draft", fail)
    response = client.post("/api/agent/runs", json={"request_type": "collect", "text": "星空"})
    assert response.status_code == 502
    run_id = response.json()["detail"]["run_id"]
    run = client.get(f"/api/agent/runs/{run_id}").json()
    assert run["error_type"] == "timeout"
    assert run["status"] == "failed"
    assert any(e["status"] == "failed" for e in run["events"])
    assert client.get("/api/stars").json() == []
    monkeypatch.setattr(ModelAdapter, "draft", original)
    retry = client.post(f"/api/agent/runs/{run_id}/retry")
    assert retry.status_code == 200
    assert retry.json()["run_id"] != run_id
    assert retry.json()["status"] == "awaiting_decision"


def test_invalid_real_output_and_wrong_tool(monkeypatch):
    class FakeResponse:
        tool_calls = [{"name": "create_star_draft", "args": {"draft": {"title": "invented"}}}]

    class FakeModel:
        def __init__(self, **kwargs):
            pass

        def bind_tools(self, *args, **kwargs):
            return self

        def invoke(self, messages):
            return FakeResponse()

    monkeypatch.setattr("app.model_adapter.ChatOpenAI", FakeModel)
    model = ModelAdapter(Settings(mock_mode=False, model_api_key="test-placeholder"))
    with pytest.raises(ModelFailure) as invalid:
        model.draft(AgentRequest(request_type="collect", text="海洋"))
    assert invalid.value.kind == "invalid_model_output"
    FakeResponse.tool_calls = [{"name": "execute_code", "args": {}}]
    with pytest.raises(ModelFailure) as unknown:
        model.draft(AgentRequest(request_type="collect", text="海洋"))
    assert unknown.value.kind == "invalid_tool_call"


def test_fallback_mock_without_key():
    assert Settings(mock_mode=False, model_api_key="").effective_mock is True


@pytest.mark.parametrize(
    "invalid",
    [
        {"source_reference": "javascript:alert(1)"},
        {"estimated_budget": -1},
        {"estimated_minutes": 0},
        {"energy_level": "super"},
        {"tags": [""]},
    ],
)
def test_star_invalid_fields(invalid):
    with pytest.raises(ValidationError):
        StarInput(title="星空", original_text="星空", **invalid)


def test_fixed_extraction_eval_cases():
    cases = json.loads((Path(__file__).parents[2] / "evals/cases.json").read_text(encoding="utf-8"))
    model = ModelAdapter(Settings(mock_mode=True))
    for case in cases["extraction"]:
        output = model.draft(AgentRequest(request_type="collect", text=case["text"]))
        assert output.draft.original_text == case["text"]
        assert output.draft.tags == case["expected_mock_tags"]
        assert output.draft.interest_reason is None


def test_preferences_range_and_candidate_deletion(client, quest):
    assert client.put("/api/preferences", json={"min_minutes": 30, "max_minutes": 10}).status_code == 422
    client.post(f"/api/quests/{quest}/reflections", json={"outcome": "completed", "liked_aspects": ["写作"]})
    candidate = client.get("/api/preferences").json()["candidates"][0]
    assert client.delete(f"/api/preferences/candidates/{candidate['id']}").status_code == 204
    assert client.get("/api/preferences").json()["candidates"] == []


def test_quest_edit_keeps_approved_state_and_constraints(client, quest):
    stored = client.get("/api/quests").json()[0]
    proposal = Proposal.model_validate(
        {k: v for k, v in stored.items() if k in Proposal.model_fields}
    ).model_dump()
    proposal["title"] = "新的轻量标题"
    assert client.put(f"/api/quests/{quest}", json=proposal).status_code == 200
    proposal["estimated_budget"] = 99
    assert client.put(f"/api/quests/{quest}", json=proposal).status_code == 422
    assert client.get("/api/quests").json()[0]["status"] == "accepted"


def test_category_preferences_rank_true_matches(client):
    for title, category in [("海洋音乐", "艺术"), ("海洋动物", "自然")]:
        client.post(
            "/api/stars",
            json={"title": title, "original_text": title, "category": category, "tags": ["海洋"]},
        )
    client.put("/api/preferences", json={"categories": ["自然"]})
    run = proposal_run(client)
    assert "海洋动物" in run["state"]["proposals"][0]["title"]


def test_archived_stars_searchable_but_not_recommended(client, star):
    body = {k: v for k, v in star.items() if k in StarInput.model_fields}
    client.put(f"/api/stars/{star['id']}", json={**body, "status": "archived"})
    assert client.get("/api/search?q=海洋").json()[0]["star_id"] == star["id"]
    assert proposal_run(client)["state"]["proposals"] == []


def test_api_timestamps_have_utc_timezone(client, star):
    assert client.get(f"/api/stars/{star['id']}").json()["created_at"].endswith(("Z", "+00:00"))
    run = proposal_run(client)
    assert run["started_at"].endswith(("Z", "+00:00"))
    decision = client.post(f"/api/agent/runs/{run['run_id']}/decision", json={"approved": True}).json()
    assert decision["decided_at"].endswith("+00:00")


def test_blank_steps_and_feedback_tags_rejected(client, quest):
    proposal = {
        "title": "x",
        "description": "x",
        "estimated_minutes": 5,
        "energy_level": "low",
        "steps": [" "],
        "based_on_star_ids": ["id"],
        "rationale": "x",
    }
    with pytest.raises(ValidationError):
        Proposal.model_validate(proposal)
    assert (
        client.post(
            f"/api/quests/{quest}/reflections", json={"outcome": "completed", "liked_aspects": [" "]}
        ).status_code
        == 422
    )
