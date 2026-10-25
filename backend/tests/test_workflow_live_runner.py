"""真实 API/图 + Fake 模型；不联网、不读取 .env、不触及个人库。"""

import importlib.util
import json
from pathlib import Path
import socket
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from app.config import Settings
from app.rules import TEXT_STEPS

spec = importlib.util.spec_from_file_location(
    "workflow_runner", Path(__file__).resolve().parents[2] / "evals/run_workflow_live.py"
)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def config(**changes):
    values = dict(
        _env_file=None,
        mock_mode=False,
        model_provider="bailian",
        model_name="qwen3.8-flash",
        model_max_retries=0,
        model_api_key="offline-workflow-placeholder",
        model_api_base_url="https://offline-fixture.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    )
    return Settings(**(values | changes))


@pytest.fixture(autouse=True)
def no_network_or_private_hash(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("workflow 离线测试禁止真实 HTTP/DNS")

    connect = socket.socket.connect

    def loopback_only(sock, address):
        if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
            return connect(sock, address)
        denied()

    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket.socket, "connect", loopback_only)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(w, "file_hash", lambda path: None)


@pytest.fixture
def fake(monkeypatch):
    state = SimpleNamespace(invokes=[], fault=None)

    class FakeChat:
        def __init__(self, **kwargs):
            assert kwargs["max_retries"] == 0
            assert kwargs["model"] == "qwen3.8-flash"

        def bind_tools(self, tools, tool_choice):
            self.name = tool_choice
            return self

        def invoke(self, messages):
            state.invokes.append(self.name)
            payload = json.loads(messages[1].content)
            if state.fault == "timeout" or (state.fault == "explore_timeout" and self.name == w.TOOLS[1]):
                raise type("APITimeoutError", (Exception,), {})("Authorization: Bearer fake-sensitive-detail")
            if self.name == "create_star_draft":
                args = {
                    "draft": {"title": "深海生物发光", "original_text": w.COLLECT_TEXT},
                    "missing_fields": [
                        "interest_reason",
                        "estimated_minutes",
                        "estimated_budget",
                        "energy_level",
                    ],
                    "questions": [],
                }
                if state.fault == "invented_unknown":
                    args["draft"]["estimated_budget"] = 0
                if state.fault == "topic_as_reason":
                    args["draft"]["interest_reason"] = "一直想了解深海生物为什么会发光"
            else:
                args = {
                    "proposals": [
                        {
                            "title": "记录深海发光问题",
                            "description": "用已有文字记录好奇",
                            "estimated_minutes": 5,
                            "estimated_budget": 0,
                            "energy_level": "low",
                            "steps": TEXT_STEPS,
                            "based_on_star_ids": [payload["stars"][0]["star_id"]],
                            "rationale": "来自真实深海星星",
                            "uncertainties": ["预计时间为估计"],
                        }
                    ],
                    "questions": [],
                }
                if state.fault == "no_candidates":
                    args = {"proposals": [], "questions": ["请补充"]}
                for fault, field, value in [
                    ("unknown_budget", "estimated_budget", None),
                    ("bad_reference", "based_on_star_ids", ["not-real"]),
                    ("over_time", "estimated_minutes", 11),
                    ("over_energy", "energy_level", "high"),
                    ("wrong_steps", "steps", ["外出购买物品"]),
                ]:
                    if state.fault == fault:
                        args["proposals"][0][field] = value
            if state.fault == "invalid_schema":
                args = {"draft": {"title": "missing required original"}}
            calls = [{"id": "offline-call", "name": self.name, "args": args}]
            if state.fault == "no_tool":
                calls = []
            if state.fault == "wrong_tool":
                calls[0]["name"] = "execute_code"
            if state.fault == "multiple_tools":
                calls = calls * 2
            return AIMessage(
                content="",
                tool_calls=calls,
                usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            )

    monkeypatch.setattr(w.adapter_module, "ChatOpenAI", FakeChat)
    monkeypatch.setattr(w, "Settings", lambda **kwargs: config())
    return state


def run_main(monkeypatch, tmp_path):
    monkeypatch.setattr(w.tempfile, "mkdtemp", lambda **kwargs: str(tmp_path))
    code = w.main(["--allow-live"])
    return code, json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))


def test_default_refuses_before_settings(monkeypatch):
    def denied(**kwargs):
        pytest.fail("无授权不得读取 Settings")

    monkeypatch.setattr(w, "Settings", denied)
    with pytest.raises(SystemExit) as raised:
        w.main([])
    assert raised.value.code == 2


def test_fake_full_api_graph_and_migrated_database(monkeypatch, tmp_path, fake):
    import os
    from app import db
    from app.main import app

    environment = dict(os.environ)
    previous_engine, previous_factory = db.engine, db.SessionLocal
    previous_overrides = dict(app.dependency_overrides)
    code, report = run_main(monkeypatch, tmp_path)
    assert code == 0 and report["status"] == "passed"
    assert fake.invokes == list(w.TOOLS)
    assert report["adapter_requests"] == len(report["calls"]) == 2
    assert report["isolation"]["alembic_revision"] == "0001"
    assert report["counts"]["initial"] == {"stars": 0, "quests": 0, "reflections": 0}
    assert report["counts"]["collect_before_approval"] == report["counts"]["initial"]
    assert report["counts"]["final"] == {"stars": 1, "quests": 1, "reflections": 0}
    assert report["environment_restored"] and dict(os.environ) == environment
    assert db.engine is previous_engine and db.SessionLocal is previous_factory
    assert app.dependency_overrides == previous_overrides
    for kind in ("collect", "explore"):
        stage = report["stages"][kind]
        assert stage["run"]["mode"] == "live"
        assert stage["approval_idempotent"]
        assert stage["test_decision"]["actor"] == "isolated_test_simulation"
        assert stage["status"] == "passed"
    assert all(c["usage"]["total_tokens"] == 15 for c in report["calls"])


@pytest.mark.parametrize(
    "fault,calls,expected",
    [
        ("timeout", 1, "failed"),
        ("explore_timeout", 2, "failed"),
        ("no_tool", 1, "failed"),
        ("wrong_tool", 1, "failed"),
        ("multiple_tools", 1, "failed"),
        ("invalid_schema", 1, "failed"),
        ("invented_unknown", 1, "failed"),
        ("no_candidates", 2, "partial"),
        ("unknown_budget", 2, "partial"),
        ("bad_reference", 2, "partial"),
        ("over_time", 2, "partial"),
        ("over_energy", 2, "partial"),
        ("wrong_steps", 2, "partial"),
    ],
)
def test_failure_stops_and_never_manufactures_quest(monkeypatch, tmp_path, fake, fault, calls, expected):
    fake.fault = fault
    code, report = run_main(monkeypatch, tmp_path)
    assert code == 1 and report["status"] == expected
    assert len(fake.invokes) == len(report["calls"]) == calls
    assert not (report["counts"].get("final") or {}).get("quests")
    assert "fake-sensitive-detail" not in json.dumps(report)
    assert report["counts"]["on_exit"] == {"stars": int(calls == 2), "quests": 0, "reflections": 0}

    if fault == "timeout":
        assert report["stages"]["collect"]["run"]["status"] == "failed"
        assert report["stages"]["collect"]["run"]["error_type"] == "timeout"
        assert report["calls"][0]["usage"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {"model_api_key": ""},
        {"model_api_base_url": "https://["},
        {"model_api_base_url": "https://example.com/v1"},
        {"model_provider": "openai-compatible"},
        {"model_name": "qwen-max"},
        {"mock_mode": True},
        {"model_max_retries": 1},
    ],
)
def test_preflight_failure_zero_invokes(monkeypatch, tmp_path, fake, changes):
    monkeypatch.setattr(w, "Settings", lambda **kwargs: config(**changes))
    code, report = run_main(monkeypatch, tmp_path)
    assert code == 1 and report["status"] == "not_run"
    assert report["calls"] == fake.invokes == []
    assert not (tmp_path / "workflow.db").exists()


def test_reuse_of_database_is_refused_before_model(monkeypatch, tmp_path, fake):
    (tmp_path / "workflow.db").write_bytes(b"existing-fixture")
    code, report = run_main(monkeypatch, tmp_path)
    assert code == 1 and report["error_type"] == "database_must_be_new"
    assert fake.invokes == []
    assert (tmp_path / "workflow.db").read_bytes() == b"existing-fixture"


def test_wrong_actual_engine_refused(monkeypatch, tmp_path, fake):
    from app import db

    make_engine = db.make_engine
    monkeypatch.setattr(
        db, "make_engine", lambda url: make_engine("sqlite:///" + (tmp_path / "wrong.db").as_posix())
    )
    code, report = run_main(monkeypatch, tmp_path)
    assert code == 1 and report["error_type"] == "actual_engine_mismatch"
    assert fake.invokes == []
    assert not (tmp_path / "wrong.db").exists()


def test_nonzero_initial_database_stops_before_model(monkeypatch, tmp_path, fake):
    from alembic import command
    from app import db
    from app.models import Star

    upgrade = command.upgrade

    def seed_after_migration(*args):
        upgrade(*args)
        with db.SessionLocal() as session:
            session.add(
                Star(
                    title="fixture",
                    original_text="public",
                    description="",
                    category="自然",
                    tags=[],
                    source_type="paste",
                    status="collected",
                )
            )
            session.commit()

    monkeypatch.setattr(command, "upgrade", seed_after_migration)
    code, report = run_main(monkeypatch, tmp_path)
    assert code == 1 and report["error_type"] == "initial"
    assert fake.invokes == []


def test_budget_counts_failure_and_rejects_third_invoke():
    report = {"calls": []}
    saves = []
    budget = w.CallBudget(report, lambda: saves.append(len(report["calls"])), lambda: None)

    class Inner:
        def invoke(self, messages):
            raise RuntimeError("offline failed attempt")

    for name in w.TOOLS:
        budget.enter_request(name)
        with pytest.raises(RuntimeError):
            budget.invoke(Inner(), name, [])
    with pytest.raises(w.CheckFailure):
        budget.enter_request(w.TOOLS[0])
    with pytest.raises(w.CheckFailure):
        budget.invoke(Inner(), w.TOOLS[0], [])
    assert len(report["calls"]) == 2
    assert saves[0] == 1 and saves[2] == 2
    assert all(c["usage"] is None for c in report["calls"])


def test_report_redacts_key_and_private_host(tmp_path):
    cfg = config()
    report = {"public_output": cfg.model_api_key + " " + cfg.model_api_base_url}
    w.write_report(tmp_path / "report.json", report, cfg)
    output = (tmp_path / "report.json").read_text(encoding="utf-8")
    assert cfg.model_api_key not in output and "offline-fixture.cn-beijing" not in output
    assert "[redacted]" in output


def test_historical_topic_reason_is_cleared_before_any_approval(fake, client, monkeypatch):
    from app import main as main_module
    from app.model_adapter import ModelAdapter

    fake.fault = "topic_as_reason"
    monkeypatch.setattr(main_module, "settings", config)
    monkeypatch.setattr(main_module, "adapter", lambda: ModelAdapter(config()))
    response = client.post("/api/agent/runs", json={"request_type": "collect", "text": w.COLLECT_TEXT})
    assert response.status_code == 201
    run = response.json()
    assert run["mode"] == "live" and run["status"] == "awaiting_decision"
    draft = run["state"]["draft"]
    assert draft["draft"]["interest_reason"] is None
    assert "interest_reason" in draft["missing_fields"]
    assert all(
        draft["draft"][name] is None for name in ("estimated_minutes", "estimated_budget", "energy_level")
    )
    assert client.get("/api/stars").json() == [] and client.get("/api/quests").json() == []
    assert fake.invokes == ["create_star_draft"]
    assert run["decisions"] == {}
