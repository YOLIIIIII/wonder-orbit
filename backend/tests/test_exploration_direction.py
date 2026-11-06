"""AGENT-004-A offline-v1; deterministic contracts, never model quality evidence."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from app.config import Settings
from app.model_adapter import ModelAdapter
from app.rules import DIRECTION_STEPS, TEXT_STEPS
from app.schemas import AgentRequest, Preferences, ProposalArgs


def test_legacy_payload_and_nested_serialization():
    request = AgentRequest(request_type="explore", text="海洋")
    expected = dict(
        request_type="explore",
        text="海洋",
        available_minutes=None,
        budget=None,
        energy_level=None,
        source_type="paste",
        source_reference=None,
    )
    assert request.model_dump() == expected
    assert json.loads(request.model_dump_json()) == expected
    assert AgentRequest(**expected, exploration_direction=None).model_dump() == expected
    assert (
        ProposalArgs(request=request, stars=[], preferences=Preferences()).model_dump()["request"] == expected
    )


@pytest.mark.parametrize("direction", [None, "knowledge", "hands_on", "creative"])
def test_direction_run_and_approval(client, star, direction):
    payload = dict(request_type="explore", text="海洋", available_minutes=10, budget=0, energy_level="low")
    if direction:
        payload["exploration_direction"] = direction
    response = client.post("/api/agent/runs", json=payload, headers={"Idempotency-Key": "direction"})
    assert response.status_code == 201, response.text
    run = response.json()
    assert run["state"]["request"].get("exploration_direction") == direction
    assert client.get(f"/api/agent/runs/{run['run_id']}").json()["state"] == run["state"]
    assert client.get("/api/quests").json() == []
    proposal = run["state"]["proposals"][0]
    assert proposal["steps"] == DIRECTION_STEPS.get(direction, TEXT_STEPS)
    assert "Mock" in proposal["description"]
    assert proposal["based_on_star_ids"] == [star["id"]]
    assert proposal["estimated_budget"] == 0
    assert proposal["energy_level"] == "low"
    assert proposal["estimated_minutes"] <= 10
    replay = client.post("/api/agent/runs", json=payload, headers={"Idempotency-Key": "direction"})
    assert replay.json()["run_id"] == run["run_id"]
    if direction:
        changed = {**payload, "exploration_direction": None}
        assert (
            client.post("/api/agent/runs", json=changed, headers={"Idempotency-Key": "direction"}).status_code
            == 409
        )
    url = f"/api/agent/runs/{run['run_id']}/decision"
    first = client.post(url, json={"approved": True})
    assert first.status_code == 200
    assert client.post(url, json={"approved": True}).json() == first.json()
    assert len(client.get("/api/quests").json()) == 1
    assert client.get("/api/preferences").json()["explicit"]["categories"] == []


def test_enum_and_collect_boundary(client):
    assert (
        client.post(
            "/api/agent/runs", json=dict(request_type="explore", text="海洋", exploration_direction="science")
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/agent/runs",
            json=dict(request_type="collect", text="海洋", exploration_direction="knowledge"),
        ).status_code
        == 422
    )
    run = client.post("/api/agent/runs", json=dict(request_type="collect", text="海洋")).json()
    assert "exploration_direction" not in run["state"]["request"]
    assert run["state"]["draft"]["draft"]["original_text"] == "海洋"


@pytest.mark.parametrize("direction", list(DIRECTION_STEPS))
def test_missing_archived_and_constraints(client, star, direction):
    payload = dict(
        request_type="explore",
        text="海洋",
        exploration_direction=direction,
        available_minutes=1,
        budget=0,
        energy_level="low",
    )
    pref = dict(min_minutes=1, max_minutes=10, constraints=["仅室内", "不购买", "不外出"])
    assert client.put("/api/preferences", json=pref).status_code == 200
    run = client.post("/api/agent/runs", json=payload).json()
    assert run["state"]["validation"] == [{"valid": True, "errors": []}]
    assert run["state"]["proposals"][0]["estimated_minutes"] == 1
    for settings, expected in [
        ({**pref, "constraints": ["不使用纸张"]}, "约束"),
        ({**pref, "min_minutes": 5}, "时间"),
    ]:
        client.put("/api/preferences", json=settings)
        state = client.post("/api/agent/runs", json=payload).json()["state"]
        assert state["proposals"] == []
        assert expected in state["questions"][0]
    client.put("/api/preferences", json=pref)
    archived = {**star, "status": "archived"}
    for key in ("id", "created_at", "updated_at"):
        archived.pop(key)
    assert client.put(f"/api/stars/{star['id']}", json=archived).status_code == 200
    for text in ("海洋", "不存在的主题xyz"):
        state = client.post("/api/agent/runs", json={**payload, "text": text}).json()["state"]
        assert state["proposals"] == []
        assert state["questions"]


@pytest.mark.parametrize("direction", list(DIRECTION_STEPS))
def test_adapter_payload_without_network(direction):
    adapter = ModelAdapter(Settings(mock_mode=False, model_api_key="fake-test-only"))
    request = AgentRequest(request_type="explore", text="海洋", exploration_direction=direction)
    with patch.object(adapter, "request", return_value="sentinel") as fake:
        assert (
            adapter.proposals(request, [{"star_id": "existing"}], Preferences(constraints=["仅室内"]))
            == "sentinel"
        )
    payload = fake.call_args.args[2]
    assert payload["request"]["exploration_direction"] == direction
    assert payload["constraint_template"]["steps"] == DIRECTION_STEPS[direction]


def test_archived_public_baseline_unchanged():
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "archived_baseline_checker", root / "evals/check_results.py"
    )
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    results = json.loads((root / "evals/reviewed_quality_results.json").read_text(encoding="utf-8"))
    report = json.loads((root / "evals/reviewed_quality_report.json").read_text(encoding="utf-8"))
    assert checker.evaluate(results) == report


# AGENT-004-A offline-v2：来自本轮截图文字说明，不含科学答案或外部资料。
SCREENSHOT_TEXTS = [
    "想了解深海生物、找入门书、周末做一件海洋相关的小事。",
    "对海洋生态系统、深海动物如何适应黑暗和高压感兴趣。",
]


def test_screenshot_knowledge_candidates(client):
    ids = []
    for text in SCREENSHOT_TEXTS:
        result = client.post("/api/stars", json={"title": text, "original_text": text})
        assert result.status_code == 201
        ids.append(result.json()["id"])
    payload = dict(
        request_type="explore",
        text="深海发光",
        exploration_direction="knowledge",
        available_minutes=10,
        budget=0,
        energy_level="low",
    )
    run = client.post("/api/agent/runs", json=payload).json()
    proposals = run["state"]["proposals"]
    assert len(proposals) == 2
    assert set(p["based_on_star_ids"][0] for p in proposals) == set(ids)
    assert all(len(p["title"]) <= 20 and "给「" not in p["title"] for p in proposals)
    assert proposals[0]["steps"] != proposals[1]["steps"]
    assert all(
        "相邻兴趣" in p["rationale"] and "未找到本次主题的直接知识依据" in p["rationale"] for p in proposals
    )
    steps = " ".join(step for p in proposals for step in p["steps"])
    assert "作者或机构" in steps
    assert "在‘黑暗’条件下如何适应" in steps
    assert "在‘高压’条件下如何适应" in steps
    assert "没有实际书目或检索结果" in steps
    assert "不预填科学结论" in steps
    assert client.get("/api/quests").json() == []
    assert all(v["valid"] for v in run["state"]["validation"])
    decision_url = f"/api/agent/runs/{run['run_id']}/decision"
    decision = client.post(decision_url, json={"approved": True}).json()
    assert client.post(decision_url, json={"approved": True}).json() == decision
    assert len(client.get("/api/quests").json()) == 1


@pytest.mark.parametrize(
    "texts",
    [
        ["深海" * 100] * 3,
        ["想找深海入门书", "想找另一本深海入门书"],
    ],
)
def test_knowledge_does_not_fill_duplicate_slots(texts):
    stars = [
        dict(star_id=str(i), title=text, text=text, match_basis=["深海"]) for i, text in enumerate(texts)
    ]
    model = ModelAdapter(Settings(mock_mode=True))
    result = model.proposals(
        AgentRequest(request_type="explore", text="深海发光", exploration_direction="knowledge"),
        stars,
        Preferences(),
    )
    assert len(result.proposals) == 1
    assert len(result.proposals[0].title) <= 20
    assert "相邻兴趣" in result.proposals[0].rationale


def test_mock_uses_visible_text_not_unpassed_original():
    model = ModelAdapter(Settings(mock_mode=True))
    request = AgentRequest(request_type="explore", text="深海发光", exploration_direction="knowledge")
    star = dict(
        star_id="real", title="深海", text="深海", original_text="隐藏的找入门书", match_basis=["深海"]
    )
    result = model.proposals(request, [star], Preferences())
    assert result.proposals[0].title == "整理一个待核实的问题"
    assert "隐藏" not in result.model_dump_json()
    direct = {**star, "text": "深海发光"}
    assert (
        "词面匹配，不是科学证据" in model.proposals(request, [direct], Preferences()).proposals[0].rationale
    )
