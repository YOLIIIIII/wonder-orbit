"""Public synthetic offline evidence only. No real SDK/network calls."""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "evals" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = load("learning_checker_tests", "check_learning_quality.py")
collector = load("learning_collector_tests", "collect_learning_quality.py")


def raw_for(row):
    from app.schemas import LearningCard, ProposalResult

    source = row["context"]["request"]["learning_source"]
    text = source["text"]
    quote = text[text.index("：") + 1 :]
    card = LearningCard(
        evidence_quote=quote,
        quote_start=text.index(quote),
        quote_end=len(text),
        takeaway="虚构材料中的记录有差异；原因未给出。",
        interest_relevance="比较海洋观察记录的限制。",
        uncertainties=["虚构且未核实，不能据此确定因果。"],
        follow_up_question="能否补充相同方法的观察？",
        source_label=source["label"],
        source_url=source["url"],
    )
    return ProposalResult(proposals=[], learning_card=card).model_dump(mode="json")


def executed(index=0, change=None):
    from app.schemas import AgentRequest

    data = checker.empty_batch()
    row = data["results"][index]
    raw = raw_for(row)
    if change:
        raw["learning_card"].update(change)
    row.update(status="executed", raw_output=raw, elapsed_ms=1)
    row["validated_output"], row["gate"] = checker.observe(
        AgentRequest.model_validate(row["context"]["request"]), raw
    )
    return data


def test_suite_contract_versions_summary_fields_and_cross_platform_hash(tmp_path):
    suite = checker.suite()
    assert len(suite["cases"]) == 5
    assert checker.LIVE_IDS == ("CASE-01", "CASE-02", "CASE-04")
    for case in suite["cases"]:
        c = checker.context(case)
        assert c["request"]["exploration_direction"] == "knowledge"
        assert set(c["stars"][0]) == {"star_id", "title", "text", "tags", "category", "score", "match_basis"}
        assert c["stars"][0]["star_id"] in c["id_map"]
    content = (ROOT / "evals/learning_quality_cases.json").read_bytes().replace(b"\r\n", b"\n")
    p = tmp_path / "suite.json"
    for data in (content, content.replace(b"\n", b"\r\n")):
        p.write_bytes(data)
        assert checker.digest(p, normalize=True) == checker.SUITE_HASH
    p.write_bytes(content + b" ")
    assert checker.digest(p, normalize=True) != checker.SUITE_HASH


def test_same_raw_dto_gate_and_manual_scores_are_independent():
    data = executed()
    before = deepcopy(data)
    report = checker.evaluate(data)
    assert data == before
    assert report["manual"] == {"rated": 0, "not_rated": 35}
    assert report["deterministic"]["failed"] == 0
    assert report["cases"][0]["gate"]["card_retained"]
    assert report["cases"][1]["status"] == "not_run"


@pytest.mark.parametrize(
    "index,change",
    [
        (0, {"takeaway": "阴天必然造成所有生物发光增加。"}),
        (1, {"takeaway": "所有海洋发光都确定受月光控制。"}),
        (2, {"takeaway": "甲绝对正确，乙错误。", "uncertainties": ["一切确定。"]}),
        (3, {"takeaway": "包装颜色揭示海洋发光机制。", "interest_relevance": "完全相关。"}),
    ],
)
def test_semantic_errors_never_get_automatic_scores(index, change):
    report = checker.evaluate(executed(index, change))
    assert report["cases"][index]["checks"]["exact_quote"] == "passed"
    assert all(r["score"] == "not_rated" for r in report["cases"][index]["manual"].values())


@pytest.mark.parametrize(
    "change",
    [
        {"evidence_quote": "伪造引用"},
        {"quote_start": 1},
        {"quote_end": 99999},
        {"source_label": "伪造机构"},
        {"source_url": "https://example.org/forged"},
    ],
)
def test_gate_rejects_and_preserves_unmodified_raw(change):
    data = executed(change=change)
    report = checker.evaluate(data)
    row = report["cases"][0]
    assert row["raw_output"] == data["results"][0]["raw_output"]
    assert row["validated_output"]["learning_card"] is None
    assert row["gate"]["reason"] == "source_gate_rejected"
    assert report["deterministic"]["failed"] > 0


def test_unicode_offsets_are_python_codepoints_and_proposals_removed():
    from app.schemas import AgentRequest

    data = executed(4)
    row = data["results"][4]
    card = row["raw_output"]["learning_card"]
    assert card["evidence_quote"].startswith("😀")
    raw = row["raw_output"]
    raw["proposals"] = [
        {
            "title": "阅读",
            "description": "阅读材料",
            "estimated_minutes": 5,
            "estimated_budget": 0,
            "energy_level": "low",
            "steps": ["阅读"],
            "based_on_star_ids": list(row["context"]["id_map"]),
            "rationale": "已有兴趣",
            "uncertainties": ["未核实"],
        }
    ]
    request = AgentRequest.model_validate(row["context"]["request"])
    assert checker.observe(request, raw)[1]["card_retained"]
    # A UTF-16-style extra offset after the emoji must fail.
    raw["learning_card"]["quote_end"] += 1
    validated, gate = checker.observe(request, raw)
    assert not validated["proposals"] and gate["proposals_removed"] == 1


def test_failure_vs_refusal_and_unobservable_dimensions():
    data = checker.empty_batch()
    refused = data["results"][3]
    from app.schemas import AgentRequest

    refused.update(
        status="executed",
        elapsed_ms=1,
        raw_output={"proposals": [], "questions": ["材料无关，无法解释。"], "learning_card": None},
    )
    refused["validated_output"], refused["gate"] = checker.observe(
        AgentRequest.model_validate(refused["context"]["request"]), refused["raw_output"]
    )
    failed = data["results"][0]
    failed.update(status="failed", failure_type="timeout", elapsed_ms=1)
    report = checker.evaluate(data)
    assert report["cases"][0]["checks"] == {"output": "failed"}
    assert report["cases"][3]["gate"]["reason"] == "model_no_card"
    assert report["manual"]["rated"] == 0
    refused["manual"]["refusal_appropriateness"] = {
        "score": 2,
        "note": "无关材料恰当拒绝",
        "reviewer": "测试评审员（非用户）",
        "reviewed_at": "2026-11-08",
        "source": "公开Fake夹具人工格式测试",
    }
    assert checker.evaluate(data)["manual"]["rated"] == 1


@pytest.mark.parametrize("score", [True, 1.0, "2", 3, -1])
def test_invalid_rating_types(score):
    with pytest.raises(ValueError):
        checker.Rating.model_validate({"score": score})


def test_cli_rejects_non_object_and_private_input(monkeypatch, capsys):
    import check_results

    monkeypatch.setattr(check_results, "load_public_json", lambda _: [])
    assert checker.main(["--results", "ignored.json"]) == 2
    monkeypatch.setattr(check_results, "load_public_json", lambda _: checker.empty_batch("live"))
    assert checker.main(["--results", "ignored.json"]) == 2
    assert "invalid_learning_evidence" in capsys.readouterr().out


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.update(case_version="future"),
        lambda d: d.update(rubric_version="wonderorbit-quality-v1"),
        lambda d: d.update(mode="live"),
        lambda d: d["results"].append(d["results"][0]),
        lambda d: d["results"][0]["context"]["stars"][0].update(original_text="secret extra"),
        lambda d: d["results"][0]["context"]["request"].update(budget=False),
        lambda d: d["results"][0]["validated_output"].update(questions=["edit"]),
        lambda d: d["results"][0]["raw_output"]["learning_card"].update(source_kind="verified"),
        lambda d: d["results"][0]["manual"].update(relevance={"score": 2, "note": "无来源"}),
        lambda d: d["results"][1].update(raw_output={"proposals": []}),
        lambda d: d["results"][1].update(usage={"total_tokens": False}),
    ],
)
def test_rejects_drift_and_forged_evidence(mutation):
    data = executed()
    mutation(data)
    with pytest.raises(ValueError):
        checker.evaluate(data)


def config(**changes):
    values = dict(
        model_provider="bailian",
        model_name="qwen3.8-flash",
        mock_mode=False,
        effective_mock=False,
        model_api_key="public-fake-key-no-network",
        model_api_base_url="https://public-fixture.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
        model_max_retries=0,
        model_max_tokens=1024,
        model_timeout=30,
    )
    return SimpleNamespace(**(values | changes))


def test_no_authorization_does_not_even_inspect_config(tmp_path):
    class Poison:
        def __getattribute__(self, name):
            raise AssertionError("config read before authorization")

    with pytest.raises(ValueError, match="allow_live_required"):
        collector.sample(Poison(), tmp_path / "batch/raw.json")
    assert not (tmp_path / "batch").exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"model_max_retries": 1},
        {"model_name": "other"},
        {"model_api_key": ""},
        {"model_provider": "openai-compatible"},
    ],
)
def test_preflight_never_invokes_sdk(monkeypatch, tmp_path, changes):
    import app.model_adapter as adapter

    monkeypatch.setattr(adapter, "ChatOpenAI", lambda **kw: pytest.fail("network forbidden"))
    with pytest.raises(ValueError):
        collector.sample(config(**changes), tmp_path / "batch/raw.json", allow_live=True)
    assert not (tmp_path / "batch").exists()


@pytest.mark.parametrize("failure", [None, "timeout", "invalid_tool_call", "invalid_model_output"])
def test_fixed_budget_prewrite_zero_retries_failure_stop_and_no_rerun(monkeypatch, tmp_path, failure):
    import app.model_adapter as adapter

    output = tmp_path / "batch/raw.json"
    calls = []

    def fake_request(self, tool_name, schema, payload):
        saved = json.loads(output.read_text(encoding="utf-8"))
        assert saved["attempted_requests"] == len(calls) + 1
        row = next(r for r in saved["results"] if r["status"] == "attempted_unknown")
        assert row["model_payload"] == payload == checker.model_payload(row["context"])
        assert self.config.model_max_retries == 0
        calls.append(row["case_id"])
        if failure:
            raise adapter.ModelFailure(failure)
        return schema.model_validate(raw_for(row))

    monkeypatch.setattr(adapter.ModelAdapter, "request", fake_request)
    monkeypatch.setattr(adapter, "ChatOpenAI", lambda **kw: pytest.fail("real SDK forbidden"))
    report = collector.sample(config(), output, allow_live=True)
    assert calls == list(checker.LIVE_IDS[:1] if failure else checker.LIVE_IDS)
    assert report["attempted_requests"] == len(calls)
    assert report["results"][0]["raw_output"] is None if failure else report["results"][0]["raw_output"]
    checker.evaluate(report)
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        collector.sample(config(), output, allow_live=True)
    assert output.read_bytes() == before


def test_second_request_in_one_case_is_blocked(monkeypatch, tmp_path):
    import app.model_adapter as adapter

    calls = []

    def fake_request(self, tool_name, schema, payload):
        calls.append(payload)
        return schema(proposals=[], questions=["不足"])

    def double(self, request, stars, pref):
        payload = checker.model_payload(
            {
                "request": request.model_dump(mode="json"),
                "stars": stars,
                "preferences": pref.model_dump(mode="json"),
            }
        )
        self.request("generate_quest_proposal", adapter.ProposalResult, payload)
        return self.request("generate_quest_proposal", adapter.ProposalResult, payload)

    monkeypatch.setattr(adapter.ModelAdapter, "request", fake_request)
    monkeypatch.setattr(adapter.ModelAdapter, "proposals", double)
    report = collector.sample(config(), tmp_path / "batch/raw.json", allow_live=True)
    assert len(calls) == report["attempted_requests"] == 1
    assert report["results"][0]["failure_type"] == "request_budget_exceeded"


def test_actual_sdk_constructor_receives_zero_retries(monkeypatch, tmp_path):
    import app.model_adapter as adapter

    calls = []

    def fake_sdk(**kwargs):
        calls.append(kwargs)
        assert kwargs["max_retries"] == 0
        raise TimeoutError("public fake timeout")

    monkeypatch.setattr(adapter, "ChatOpenAI", fake_sdk)
    report = collector.sample(config(), tmp_path / "batch/raw.json", allow_live=True)
    assert len(calls) == report["attempted_requests"] == 1
    assert report["results"][0]["failure_type"] == "timeout"


@pytest.mark.parametrize("kind", ["invalid_tool_call", "invalid_model_output"])
def test_actual_adapter_parse_failure_keeps_no_dto(monkeypatch, tmp_path, kind):
    import app.model_adapter as adapter

    class FakeSDK:
        def __init__(self, **kwargs):
            assert kwargs["max_retries"] == 0

        def bind_tools(self, *args, **kwargs):
            return self

        def invoke(self, messages):
            return SimpleNamespace(
                invalid_tool_calls=[],
                usage_metadata={"total_tokens": 10},
                tool_calls=[
                    {
                        "name": "unexpected" if kind == "invalid_tool_call" else "generate_quest_proposal",
                        "args": {"proposals": "invalid"},
                    }
                ],
            )

    monkeypatch.setattr(adapter, "ChatOpenAI", FakeSDK)
    report = collector.sample(config(), tmp_path / "batch/raw.json", allow_live=True)
    row = report["results"][0]
    assert report["attempted_requests"] == 1
    assert row["failure_type"] == kind
    assert row["raw_output"] is None and row["validated_output"] is None
    assert row["usage"] == {"total_tokens": 10}
    assert checker.evaluate(report)["manual"]["rated"] == 0


def test_source_rejection_stops_without_repair_or_second_request(monkeypatch, tmp_path):
    import app.model_adapter as adapter

    calls = []

    def fake_request(self, tool_name, schema, payload):
        calls.append(payload)
        row = {"context": {"request": payload["request"]}}
        raw = raw_for(row)
        raw["learning_card"]["evidence_quote"] = "伪造"
        return schema.model_validate(raw)

    monkeypatch.setattr(adapter.ModelAdapter, "request", fake_request)
    report = collector.sample(config(), tmp_path / "batch/raw.json", allow_live=True)
    assert len(calls) == 1
    assert report["results"][0]["raw_output"]["learning_card"]["evidence_quote"] == "伪造"
    assert checker.evaluate(report)["deterministic"]["failed"] == 1


def test_interruption_leaves_attempt_before_call_and_blocks_replay(monkeypatch, tmp_path):
    import app.model_adapter as adapter

    output = tmp_path / "batch/raw.json"

    def interrupt(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(adapter.ModelAdapter, "request", interrupt)
    with pytest.raises(KeyboardInterrupt):
        collector.sample(config(), output, allow_live=True)
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["attempted_requests"] == 1
    assert data["results"][0]["status"] == "attempted_unknown"
    checker.evaluate(data)
    with pytest.raises(FileExistsError):
        collector.sample(config(), output, allow_live=True)


@pytest.mark.parametrize("script", ["check_learning_quality.py", "collect_learning_quality.py"])
def test_default_cli_audit_blocks_network_database_config_and_sdk(script):
    code = r"""
import sys, runpy
def guard(event,args):
    if event.startswith(('socket.','sqlite3.')): raise AssertionError('external access')
    if event == 'open':
        p=str(args[0]).replace('\\','/').lower()
        if '/.env' in p or '/.cache/' in p or p.endswith(('.db','.sqlite')):
            raise AssertionError('private read')
    if event == 'import' and args[0] in {'app.config','app.model_adapter','app.db','app.tools','app.workflow'}:
        raise AssertionError('runtime import')
sys.addaudithook(guard)
sys.argv=[sys.argv[1]]
runpy.run_path(sys.argv[0],run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", code, f"evals/{script}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    json.loads(result.stdout)


def test_legacy_reviewed_evidence_byte_unchanged_and_report_identical():
    paths = [ROOT / f"evals/reviewed_quality_{suffix}.json" for suffix in ("captures", "results", "report")]
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "evals/check_results.py", "--results", str(paths[1])],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report == json.loads(paths[2].read_text(encoding="utf-8"))
    assert report["deterministic"] == {"passed": 20, "failed": 1, "not_run": 7, "not_rated": 3}
    assert report["manual"] == {"rated": 1, "not_rated": 59}
    assert before == [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
