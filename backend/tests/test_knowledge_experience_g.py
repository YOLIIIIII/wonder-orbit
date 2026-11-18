"""G campaign guards: synthetic SDK transport only, never live network."""

from copy import deepcopy
import json
import shutil
from types import SimpleNamespace

import pytest
from test_learning_quality_evals import load, config, raw_for
from app import model_adapter
from app.model_adapter import ModelAdapter

g = load("knowledge_g_tests", "run_knowledge_experience_g.py")


def install(monkeypatch, root, failure=None, bad_source=False):
    # Synthetic transport regression uses the CURRENT adapter/schema, not a G replay.
    monkeypatch.setattr(g, "validate_production_subject", lambda: None)
    calls = []

    class Fake:
        def __init__(self, **kw):
            assert kw["max_retries"] == 0

        def bind_tools(self, tools, **kw):
            assert kw["tool_choice"] == "generate_quest_proposal"
            return self

        def invoke(self, messages):
            sid = f"G-{len(calls) + 1:02d}"
            assert (root / f".cache/knowledge-experience-g-budget/{sid}.attempt.json").is_file()
            saved = json.loads((root / ".cache/knowledge-experience-g/raw.json").read_text(encoding="utf8"))
            row = saved["results"][len(calls)]
            assert row["status"] == "attempted_unknown" and row["model_messages"]
            assert row["model_payload"] == json.loads(messages[1].content)
            calls.append(sid)
            if failure == "interrupt":
                raise KeyboardInterrupt
            if failure in {"timeout", "rate_limit", "runner"}:
                cls = type(
                    {"timeout": "TimeoutError", "rate_limit": "RateLimitError", "runner": "Error"}[failure],
                    (Exception,),
                    {},
                )
                raise cls("SECRET ERROR")
            raw = raw_for(row)
            if bad_source:
                raw["learning_card"]["source_label"] = "wrong"
            raw["proposals"] = [
                dict(
                    title="synthetic",
                    description="synthetic",
                    estimated_minutes=100,
                    estimated_budget=None,
                    energy_level="high",
                    steps=["synthetic"],
                    based_on_star_ids=["invalid-id"],
                    rationale="synthetic",
                    uncertainties=[],
                )
            ]
            if failure == "invalid_model_output":
                raw["proposals"][0]["estimated_minutes"] = "SECRET VALUE"
                raw["SECRET EXTRA FIELD"] = "SECRET VALUE"
            return SimpleNamespace(
                tool_calls=[
                    dict(
                        name="wrong" if failure == "invalid_tool_call" else "generate_quest_proposal",
                        args=raw,
                    )
                ],
                invalid_tool_calls=[],
                usage_metadata=dict(input_tokens=10, output_tokens=20, total_tokens=30),
            )

    monkeypatch.setattr(model_adapter, "ChatOpenAI", Fake)
    return calls


def test_default_no_config_or_model(monkeypatch, capsys, tmp_path):
    with pytest.raises(ValueError, match="allow_live_required"):
        g.sample(object(), root=tmp_path)
    monkeypatch.setattr(g, "sample", lambda *a, **kw: pytest.fail("offline invoked sampler"))
    assert g.main([]) == 0
    assert json.loads(capsys.readouterr().out)["max_requests"] == 4


def test_fixed_material_and_identical_science():
    rows = g.contexts()
    assert [r["sample_id"] for r in rows] == ["G-01", "G-02", "G-03", "G-04"]
    assert rows[0]["context"] == rows[3]["context"]
    cases = {c["case_id"]: c for c in g.suite()["cases"]}
    assert rows[1]["context"] == g.context(cases["CASE-01"])
    assert rows[2]["context"] == g.context(cases["CASE-04"])


@pytest.mark.parametrize(
    "changes",
    [
        {"mock_mode": True},
        {"model_api_key": ""},
        {"model_name": "other"},
        {"model_max_retries": 1},
        {"model_api_base_url": "https://api.openai.com/v1"},
    ],
)
def test_preflight_rejects_without_reservation(monkeypatch, tmp_path, changes):
    calls = install(monkeypatch, tmp_path)
    with pytest.raises(ValueError):
        g.sample(config(**changes), allow_live=True, root=tmp_path)
    assert not calls and not list(tmp_path.iterdir())


def test_four_slots_source_and_quest_failures_continue(monkeypatch, tmp_path):
    calls = install(monkeypatch, tmp_path, bad_source=True)
    report = g.sample(config(), root=tmp_path, allow_live=True)
    assert len(calls) == len(set(calls)) == report["attempted_requests"] == 4
    for row in report["results"]:
        assert row["status"] == "executed" and row["gate"]["reason"] == "source_gate_rejected"
        assert row["raw_output"]["proposals"] and not row["validated_output"]["proposals"]
        assert row["quest"]["proposals"][0]["constraint_errors"]
        assert not row["quest"]["proposals"][0]["retrieved_star_ids_match"]
        assert row["usage"]["total_tokens"] == 30
        assert all(r["score"] == "not_rated" for r in row["manual"].values())
    assert report["results"][0]["model_messages"] == report["results"][3]["model_messages"]
    shutil.rmtree(tmp_path / ".cache/knowledge-experience-g")
    with pytest.raises(FileExistsError):
        g.sample(config(), root=tmp_path, allow_live=True)
    assert len(calls) == 4


@pytest.mark.parametrize(
    "failure", ["timeout", "rate_limit", "runner", "invalid_tool_call", "invalid_model_output", "interrupt"]
)
def test_failure_stops_no_replay(monkeypatch, tmp_path, failure):
    calls = install(monkeypatch, tmp_path, failure)
    if failure == "interrupt":
        with pytest.raises(KeyboardInterrupt):
            g.sample(config(), root=tmp_path, allow_live=True)
        report = json.loads((tmp_path / ".cache/knowledge-experience-g/raw.json").read_text(encoding="utf8"))
        assert report["results"][0]["status"] == "attempted_unknown"
    else:
        report = g.sample(config(), root=tmp_path, allow_live=True)
        assert report["results"][0]["status"] == "failed"
    assert report["results"][1]["status"] == "not_run" and len(calls) == 1
    assert "SECRET" not in json.dumps(report)
    if failure == "invalid_model_output":
        assert report["results"][0]["validation_errors"] == [
            dict(path=["proposals", 0, "estimated_minutes"], type="int_parsing"),
            dict(path=["<unknown_field>"], type="extra_forbidden"),
        ]
    with pytest.raises(FileExistsError):
        g.sample(config(), root=tmp_path, allow_live=True)


def test_double_request_blocked(monkeypatch, tmp_path):
    calls = install(monkeypatch, tmp_path)
    original = ModelAdapter.proposals

    def double(self, *args):
        original(self, *args)
        return original(self, *args)

    monkeypatch.setattr(ModelAdapter, "proposals", double)
    report = g.sample(config(), root=tmp_path, allow_live=True)
    assert len(calls) == 1
    assert report["results"][0]["failure_type"] == "request_budget_exceeded"


def test_storage_failure_never_calls_or_restarts(monkeypatch, tmp_path):
    calls = install(monkeypatch, tmp_path)

    def fail(*a):
        raise OSError("SECRET STORAGE")

    monkeypatch.setattr(g, "snapshot", fail)
    with pytest.raises(OSError):
        g.sample(config(), root=tmp_path, allow_live=True)
    assert not calls
    with pytest.raises(FileExistsError):
        g.sample(config(), root=tmp_path, allow_live=True)


def test_raw_unchanged_by_diagnostics():
    row = g.contexts()[0]
    raw = raw_for(row)
    before = deepcopy(raw)
    g.quest_diagnostics(row["context"], raw)
    g.observe(g.AgentRequest.model_validate(row["context"]["request"]), raw)
    assert raw == before


def test_offline_subprocess_audit():
    import subprocess
    import sys

    script = r"""
import sys,runpy

def audit(event,args):
    if event.startswith('socket.') or event.startswith('sqlite3.'):
        raise RuntimeError('offline access forbidden')
    if event == 'open':
        name=str(args[0]).replace(chr(92),'/')
        if name.endswith('/.env') or name == '.env' or '/.cache/' in name:
            raise RuntimeError('private file forbidden')
sys.addaudithook(audit)
sys.argv=['evals/run_knowledge_experience_g.py']
runpy.run_path(sys.argv[0],run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", script],
        cwd=g.ROOT,
        capture_output=True,
        text=True,
        encoding="utf8",
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["mode"] == "offline_plan"


def test_attempt_storage_failure_stops(monkeypatch, tmp_path):
    calls = install(monkeypatch, tmp_path)
    create = g.durable_create

    def fail_attempt(path, value):
        if path.name.endswith(".attempt.json"):
            raise OSError("SECRET STORAGE")
        return create(path, value)

    monkeypatch.setattr(g, "durable_create", fail_attempt)
    report = g.sample(config(), root=tmp_path, allow_live=True)
    assert not calls and report["results"][0]["status"] == "failed"
    assert report["results"][1]["status"] == "not_run"


def test_persisted_global_slots_block(monkeypatch, tmp_path):
    calls = install(monkeypatch, tmp_path)
    create = g.durable_create

    def prefill(path, value):
        create(path, value)
        if path.name == "plan.json":
            for i in range(4):
                create(path.parent / f"occupied-{i}.attempt.json", {})

    monkeypatch.setattr(g, "durable_create", prefill)
    report = g.sample(config(), root=tmp_path, allow_live=True)
    assert not calls and report["results"][0]["failure_type"] == "request_budget_exceeded"


def test_production_subject_guard_rejects_changed_source(monkeypatch, tmp_path):
    # Exercise the real historical gate independently of synthetic SDK tests.
    monkeypatch.setattr(g, "ROOT", tmp_path)
    app = tmp_path / "backend/app"
    app.mkdir(parents=True)
    for name in ("model_adapter.py", "learning.py", "schemas.py", "rules.py"):
        (app / name).write_bytes(b"baseline\n")
    monkeypatch.setattr(
        g.subprocess,
        "check_output",
        lambda args, **kw: g.BASELINE if args[1] == "rev-parse" else b"baseline\n",
    )
    g.validate_production_subject()
    (app / "learning.py").write_bytes(b"future implementation\n")
    with pytest.raises(ValueError, match="production_subject_changed"):
        g.validate_production_subject()
    monkeypatch.setattr(g.subprocess, "check_output", lambda *a, **kw: "other-head")
    with pytest.raises(ValueError, match="baseline_changed"):
        g.validate_production_subject()
