"""v3 sampling protection tests: synthetic DTOs only; no model network."""

from copy import deepcopy
import json
import shutil

import pytest
from test_learning_quality_evals import load, config, raw_for, checker
from app.model_adapter import ModelAdapter, ModelFailure
from app.schemas import AgentRequest, Preferences, Proposal, ProposalResult
from app.rules import quest_constraint_errors

v3 = load("learning_v3_tests", "collect_learning_quality_v3.py")


def install(monkeypatch, root, failure=None, bad_source=False, budget=0):
    calls = []

    def fake(self, tool, schema, payload):
        sid = f"{checker.LIVE_IDS[len(calls) % 3]}-S{len(calls) // 3 + 1:02d}"
        ledger = root / ".cache/learning-quality-v3-budget"
        assert (ledger / f"{sid}.attempt.json").exists()
        batch = len(calls) // 3 + 1
        saved = json.loads(
            (root / f".cache/learning-quality-v3/batch-{batch}/raw.json").read_text(encoding="utf-8")
        )
        row = next(r for r in saved["results"] if r["sample_id"] == sid)
        assert row["status"] == "attempted_unknown" and row["model_payload"] == payload
        assert self.config.model_max_retries == 0
        calls.append(sid)
        if failure:
            if failure == "interrupt":
                raise KeyboardInterrupt()
            if failure == "runner":
                raise RuntimeError("sensitive response must not be saved")
            raise ModelFailure(failure)
        raw = raw_for(row)
        if bad_source:
            raw["learning_card"]["source_label"] = "wrong"
        raw["proposals"] = [proposal(estimated_budget=budget).model_dump(mode="json")]
        self.last_usage = {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}
        return schema.model_validate(raw)

    monkeypatch.setattr(ModelAdapter, "request", fake)
    import app.model_adapter as adapter

    monkeypatch.setattr(adapter, "ChatOpenAI", lambda **kw: pytest.fail("network forbidden"))
    return calls


def proposal(**changes):
    return Proposal.model_validate(
        dict(
            title="阅读现有文字",
            description="只比较材料中的两次记录",
            estimated_minutes=8,
            estimated_budget=0,
            energy_level="low",
            steps=["读已有文字并记录差异"],
            based_on_star_ids=["STAR-OCEAN"],
            rationale="已有兴趣",
            uncertainties=["未独立核实"],
        )
        | changes
    )


def test_authorization_and_default_cli(tmp_path, monkeypatch, capsys):
    class Poison:
        def __getattribute__(self, name):
            pytest.fail("config accessed without authorization")

    with pytest.raises(ValueError, match="allow_live_required"):
        v3.sample(Poison(), root=tmp_path)
    monkeypatch.setattr(v3, "sample", lambda *a, **kw: pytest.fail("offline called sampler"))
    assert v3.main([]) == 0
    assert json.loads(capsys.readouterr().out)["max_requests"] == 6
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "changes",
    [{"model_max_retries": 1}, {"model_name": "other"}, {"model_api_key": ""}, {"model_provider": "other"}],
)
def test_invalid_config_no_reservation(tmp_path, monkeypatch, changes):
    calls = install(monkeypatch, tmp_path)
    with pytest.raises(ValueError):
        v3.sample(config(**changes), root=tmp_path, allow_live=True)
    assert calls == [] and not list(tmp_path.iterdir())


def test_six_slots_two_per_case_source_failure_continues_and_no_replay(tmp_path, monkeypatch):
    calls = install(monkeypatch, tmp_path, bad_source=True, budget=None)
    reports = [v3.sample(config(), batch=b, root=tmp_path, allow_live=True) for b in (1, 2)]
    assert len(calls) == len(set(calls)) == 6
    assert all(sum(s.startswith(c) for s in calls) == 2 for c in checker.LIVE_IDS)
    for report in reports:
        assert report["attempted_requests"] == 3
        for row in report["results"]:
            assert row["status"] == "executed" and row["gate"]["reason"] == "source_gate_rejected"
            assert row["raw_output"]["proposals"] and not row["validated_output"]["proposals"]
            assert "预算未知或超过上限" in row["quest"]["proposals"][0]["constraint_errors"]
            assert row["usage"]["total_tokens"] == 30 and row["elapsed_ms"] >= 0
            assert row["gate"]["offset_resolution"]
            assert all(r["score"] == "not_rated" for r in row["manual"].values())
    # Deleting only report directories does not reset the independent ledger.
    shutil.rmtree(tmp_path / ".cache/learning-quality-v3")
    for b in (1, 2):
        with pytest.raises(FileExistsError):
            v3.sample(config(), batch=b, root=tmp_path, allow_live=True)
    assert len(calls) == 6


@pytest.mark.parametrize(
    "failure",
    [
        "timeout",
        "rate_limit",
        "model_unavailable",
        "invalid_tool_call",
        "invalid_model_output",
        "runner",
        "interrupt",
    ],
)
def test_infrastructure_failure_stops_and_blocks_second_batch(tmp_path, monkeypatch, failure):
    calls = install(monkeypatch, tmp_path, failure=failure)
    if failure == "interrupt":
        with pytest.raises(KeyboardInterrupt):
            v3.sample(config(), root=tmp_path, allow_live=True)
    else:
        report = v3.sample(config(), root=tmp_path, allow_live=True)
        assert report["results"][0]["status"] == "failed"
        assert report["results"][1]["status"] == "not_run"
        assert "sensitive" not in json.dumps(report)
    with pytest.raises(ValueError, match="first_batch_not_complete"):
        v3.sample(config(), batch=2, root=tmp_path, allow_live=True)
    with pytest.raises(FileExistsError):
        v3.sample(config(), root=tmp_path, allow_live=True)
    assert len(calls) == 1
    assert len(list((tmp_path / ".cache/learning-quality-v3-budget").glob("*.attempt.json"))) == 1


def test_double_request_and_illegal_tool_blocked(tmp_path, monkeypatch):
    calls = install(monkeypatch, tmp_path)

    def double(self, req, stars, prefs):
        payload = checker.model_payload(
            dict(request=req.model_dump(mode="json"), stars=stars, preferences=prefs.model_dump(mode="json"))
        )
        self.request("generate_quest_proposal", ProposalResult, payload)
        return self.request("generate_quest_proposal", ProposalResult, payload)

    monkeypatch.setattr(ModelAdapter, "proposals", double)
    report = v3.sample(config(), root=tmp_path, allow_live=True)
    assert len(calls) == 1
    assert report["results"][0]["failure_type"] == "request_budget_exceeded"


@pytest.mark.parametrize("budget", [None, 0, 1])
def test_budget_and_readonly_diagnostics(budget):
    inputs = checker.empty_batch()["results"][0]["context"]
    p = proposal(estimated_budget=budget, based_on_star_ids=[inputs["stars"][0]["star_id"]])
    raw = ProposalResult(proposals=[p]).model_dump(mode="json")
    before = deepcopy(raw)
    report = v3.quest_diagnostics(inputs, raw)
    assert raw == before
    assert report["database_star_existence"] == "not_observed"
    assert report["proposals"][0]["retrieved_star_ids_match"]
    assert ("预算未知或超过上限" in report["proposals"][0]["constraint_errors"]) == (budget != 0)


@pytest.mark.parametrize(
    "change,expected",
    [({"estimated_minutes": 100}, "超过时间上限"), ({"energy_level": "high"}, "超过精力上限")],
)
def test_shared_rules(change, expected):
    inputs = checker.empty_batch()["results"][0]["context"]
    assert expected in quest_constraint_errors(
        proposal(**change),
        AgentRequest.model_validate(inputs["request"]),
        Preferences.model_validate(inputs["preferences"]),
    )


@pytest.mark.parametrize("response_budget", [None, 0, 2])
def test_prompt_free_is_explicit_but_unknown_and_costly_are_not_rewritten(monkeypatch, response_budget):
    import app.model_adapter as adapter

    messages = []

    class Fake:
        def __init__(self, **kw):
            assert kw["max_retries"] == 0

        def bind_tools(self, *a, **kw):
            return self

        def invoke(self, value):
            from types import SimpleNamespace

            messages.append(value)
            return SimpleNamespace(
                tool_calls=[
                    {
                        "name": "generate_quest_proposal",
                        "args": ProposalResult(
                            proposals=[proposal(estimated_budget=response_budget)]
                        ).model_dump(),
                    }
                ]
            )

    monkeypatch.setattr(adapter, "ChatOpenAI", Fake)
    inputs = checker.empty_batch()["results"][0]["context"]
    result = ModelAdapter(config()).proposals(
        AgentRequest.model_validate(inputs["request"]),
        inputs["stars"],
        Preferences.model_validate(inputs["preferences"]),
    )
    text = messages[0][0].content
    assert adapter.ZERO_BUDGET_KNOWLEDGE_INSTRUCTION in text
    assert all(
        word in text for word in ["外部工具", "设备", "有成本", "仍填 null", "空 proposals", "未独立核实"]
    )
    assert result.proposals[0].estimated_budget == response_budget
    assert json.loads(messages[0][1].content)["effective_limits"]["budget"] == 0


@pytest.mark.parametrize("limit", ["global", "case", "illegal"])
def test_guard_enforces_slot_counts_even_with_extra_existing_evidence(tmp_path, monkeypatch, limit):
    calls = install(monkeypatch, tmp_path)
    original = ModelAdapter.proposals

    def guarded(self, req, stars, prefs):
        ledger = tmp_path / ".cache/learning-quality-v3-budget"
        if limit == "global":
            for i in range(6):
                v3.durable_create(ledger / f"extra-{i}.attempt.json", {})
        elif limit == "case":
            for i in range(2):
                v3.durable_create(ledger / f"CASE-01-SX{i}.attempt.json", {})
        else:
            return self.request("persist_approved_quest", ProposalResult, {})
        return original(self, req, stars, prefs)

    monkeypatch.setattr(ModelAdapter, "proposals", guarded)
    report = v3.sample(config(), root=tmp_path, allow_live=True)
    assert calls == [] and report["attempted_requests"] == 0
    assert report["results"][0]["failure_type"] == "request_budget_exceeded"


def test_unknown_execution_conditions_and_unsupported_constraints_are_honest():
    inputs = deepcopy(checker.empty_batch()["results"][0]["context"])
    inputs["preferences"]["constraints"] = ["无噪音"]
    raw = ProposalResult(proposals=[proposal()]).model_dump(mode="json")
    result = v3.quest_diagnostics(inputs, raw)
    assert result["unsupported_constraints"] == ["无噪音"]
    assert result["execution_conditions"] == "not_observed_requires_manual_review"
    assert not result["proposals"][0]["rule_checks_passed"]
    inputs["preferences"]["constraints"] = ["不购买"]
    assert (
        "约束要求可验证的免费室内文字记录步骤"
        in v3.quest_diagnostics(inputs, raw)["proposals"][0]["constraint_errors"]
    )


@pytest.mark.parametrize(
    "claim", ["随机波动解释了记录差异", "没有对照组所以天气导致发光变化", "天气导致发光变化"]
)
def test_unsupported_explanations_remain_manual_not_rated(tmp_path, monkeypatch, claim):
    install(monkeypatch, tmp_path)
    original = v3.observe

    def inspect(req, raw):
        before = deepcopy(raw)
        result = original(req, raw)
        assert raw == before
        return result

    monkeypatch.setattr(v3, "observe", inspect)
    # Pure source checks do not certify any of these unsupported claims.
    inputs = checker.empty_batch()["results"][0]["context"]
    raw = raw_for({"context": inputs})
    raw["learning_card"]["takeaway"] = claim
    _, gate = v3.observe(AgentRequest.model_validate(inputs["request"]), raw)
    assert gate["card_retained"]
    assert all(
        r["score"] == "not_rated" for r in {d: v3.Rating().model_dump() for d in v3.DIMENSIONS}.values()
    )
