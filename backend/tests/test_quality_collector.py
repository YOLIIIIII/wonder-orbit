"""No provider access: exercise actual adapter parsing against a fake Chat client."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys

from langchain_core.messages import AIMessage
import pytest

from app.config import Settings
from app import model_adapter

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("quality_collector", ROOT / "evals/collect_quality.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
from check_results import evaluate, prepare_captures  # noqa: E402


def config(**changes):
    return Settings(
        _env_file=None,
        **(
            {
                "mock_mode": False,
                "model_provider": "bailian",
                "model_name": "qwen3.8-flash",
                "model_api_key": "offline-only-placeholder",
                "model_max_retries": 0,
                "model_api_base_url": "https://offline-fixture.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
            }
            | changes
        ),
    )


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def deny(*args, **kwargs):
        pytest.fail("Network forbidden")

    monkeypatch.setattr(socket, "getaddrinfo", deny)
    monkeypatch.setattr(socket.socket, "connect", deny)


@pytest.fixture
def wire(monkeypatch):
    captures = json.loads((ROOT / "evals/sample_public_captures.json").read_text(encoding="utf-8"))
    draft = deepcopy(captures["results"][0]["capture"]["raw_output"])
    proposal = deepcopy(captures["results"][1]["capture"]["raw_output"])
    for p in proposal["proposals"]:
        p["based_on_star_ids"] = [runner.SYNTHETIC_ID]
    state = {"payloads": [], "options": [], "fail_at": None, "invalid_at": None}

    class FakeChat:
        def __init__(self, **kwargs):
            state["options"].append(kwargs)

        def bind_tools(self, tools, tool_choice):
            self.tool = tool_choice
            return self

        def invoke(self, messages):
            payload = json.loads(messages[1].content)
            state["payloads"].append(payload)
            index = len(state["payloads"])
            if state["fail_at"] == index:
                raise TimeoutError("sensitive Authorization fake-key private-host")
            args = deepcopy(draft if self.tool == "create_star_draft" else proposal)
            if state["invalid_at"] == index:
                args = {"illegal": "must not repair"}
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": self.tool,
                        "args": args,
                        "id": "fake-test-only",
                    }
                ],
                usage_metadata={"input_tokens": 11, "output_tokens": 7, "total_tokens": 18},
            )

    monkeypatch.setattr(model_adapter, "ChatOpenAI", FakeChat)
    return state


def test_default_offline_no_runtime_or_private_reads(tmp_path):
    code = r"""
import sys, runpy
def audit(event, args):
    if event.startswith(("socket.", "sqlite3.")):
        raise RuntimeError("forbidden IO")
    if event == "open":
        name = str(args[0]).lower().replace("\\", "/")
        if any(p.startswith(".env") or p == ".cache" for p in name.split("/")) or name.endswith(".db"):
            raise RuntimeError("private read")
    if event == "import" and args[0] in {"app.config", "app.db", "app.model_adapter", "app.workflow"}:
        raise RuntimeError("runtime import")
sys.addaudithook(audit)
sys.argv = ["evals/collect_quality.py"]
runpy.run_path(sys.argv[0], run_name="__main__")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["mode"] == "offline" and data["requests"] == 0
    assert [r["case_id"] for r in data["plan"]] == list(runner.CASE_IDS)


@pytest.mark.parametrize(
    "changes",
    [
        {"mock_mode": True},
        {"model_api_key": ""},
        {"model_name": "other"},
        {"model_max_retries": 1},
        {"model_provider": "openai-compatible"},
    ],
)
def test_config_rejected_before_output_or_requests(tmp_path, wire, changes):
    with pytest.raises(ValueError):
        runner.sample(config(**changes), runner.plan(), tmp_path / "batch/raw.json", allow_live=True)
    assert wire["payloads"] == []
    assert not (tmp_path / "batch").exists()


def test_no_allow_live(tmp_path, wire):
    with pytest.raises(ValueError, match="allow_live"):
        runner.sample(config(), runner.plan(), tmp_path / "batch/raw.json")
    assert wire["payloads"] == []


@pytest.mark.parametrize("mutation", ["order", "extra", "mapping", "version", "content", "prefs"])
def test_plan_context_cannot_drift(tmp_path, wire, mutation):
    records = runner.plan()
    capture = records[2]["capture"]
    if mutation == "order":
        records.reverse()
    elif mutation == "extra":
        records.append(deepcopy(records[0]))
    elif mutation == "mapping":
        capture["id_map"][runner.SYNTHETIC_ID] = "wrong"
    elif mutation == "version":
        capture["generation_versions"]["prompt_version"] = "fake"
    elif mutation == "content":
        capture["retrieved_stars"][0]["original_text"] = "different"
    else:
        capture["preferences"] = {"constraints": ["室内"]}
    with pytest.raises(ValueError):
        runner.sample(config(), records, tmp_path / "batch/raw.json", allow_live=True)
    assert wire["payloads"] == []


def test_fixed_three_actual_inputs_and_review_pipeline(tmp_path, wire):
    raw = tmp_path / "batch/raw.json"
    report = runner.sample(config(), runner.plan(), raw, allow_live=True)
    assert report["attempted_requests"] == len(wire["payloads"]) == 3
    assert all(row["status"] == "schema_valid" for row in report["results"])
    assert [p["text"] for p in wire["payloads"][:2]] == [
        r["capture"]["input"]["text"] for r in runner.plan()[:2]
    ]
    explore = wire["payloads"][2]
    assert explore["stars"] == runner.plan()[2]["capture"]["retrieved_stars"]
    assert explore["preferences"] == runner.Preferences().model_dump()
    assert explore["constraint_template"] is None
    assert explore["effective_limits"] == {"minutes": 10, "budget": 0, "energy": "low"}
    assert report["results"][2]["model_payload"] == explore
    assert all(o["max_retries"] == 0 and o["model"] == "qwen3.8-flash" for o in wire["options"])
    assert report["results"][0]["usage"]["total_tokens"] == 18
    assert all(r["elapsed_ms"] >= 0 for r in report["results"])
    assert report["workflow_executed"] is False and report["public_data"] is False
    public = tmp_path / "reviewed.json"
    runner.export_reviewed(raw, public)
    prepared = prepare_captures(json.loads(public.read_text(encoding="utf-8")))
    checked = evaluate(prepared)
    assert checked["manual"]["rated"] == 0
    assert checked["evidence_type"] == "supplied_live_output_unverified"
    assert all(
        row["capture"]["raw_output"] == old["capture"]["raw_output"]
        for row, old in zip(prepared["results"], report["results"], strict=True)
    )
    with pytest.raises(FileExistsError):
        runner.sample(config(), runner.plan(), raw, allow_live=True)
    assert len(wire["payloads"]) == 3
    # These are test doubles, never share them labelled as provider evidence.
    data = json.loads(public.read_text(encoding="utf-8"))
    data["mode"] = "fake"
    assert evaluate(prepare_captures(data))["evidence_type"] == "tool_self_test"
    report["mode"] = "fake"
    raw.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="not_fixed_live"):
        runner.export_reviewed(raw, tmp_path / "fake.json")


@pytest.mark.parametrize("fail_at", [1, 2, 3])
@pytest.mark.parametrize("invalid", [False, True])
def test_failure_counts_once_stops_and_never_repairs(tmp_path, wire, fail_at, invalid):
    wire["invalid_at" if invalid else "fail_at"] = fail_at
    raw = tmp_path / "batch/raw.json"
    report = runner.sample(config(), runner.plan(), raw, allow_live=True)
    assert report["attempted_requests"] == len(wire["payloads"]) == fail_at
    failed = report["results"][-1]
    assert failed["failure_type"] == ("invalid_model_output" if invalid else "timeout")
    assert failed["capture"]["raw_output"] is None
    assert failed["usage"] == (
        {"input_tokens": 11, "output_tokens": 7, "total_tokens": 18} if invalid else "unknown"
    )
    assert "sensitive" not in raw.read_text(encoding="utf-8")
    public = tmp_path / "reviewed.json"
    runner.export_reviewed(raw, public)
    checked = evaluate(prepare_captures(json.loads(public.read_text(encoding="utf-8"))))
    assert checked["deterministic"]["failed"] >= 1
    checked_row = next(r for r in checked["cases"] if r["case_id"] == failed["case_id"])
    assert checked_row["failure_type"] == failed["failure_type"]
    assert checked["manual"]["rated"] == 0


def test_journal_written_before_invoke_and_no_database_import(tmp_path, wire, monkeypatch):
    raw = tmp_path / "batch/raw.json"
    original = model_adapter.ModelAdapter.request

    def observe(self, *args):
        journal = json.loads(raw.read_text(encoding="utf-8"))
        assert journal["results"][-1]["status"] == "attempted_unknown"
        assert journal["attempted_requests"] == len(journal["results"])
        assert journal["results"][-1]["usage"] == "unknown"
        return original(self, *args)

    monkeypatch.setattr(model_adapter.ModelAdapter, "request", observe)
    runner.sample(config(), runner.plan(), raw, allow_live=True)
    # Runner source has no DB/SQL/API writes; independent subprocess guards the offline path.
    source = (ROOT / "evals/collect_quality.py").read_text(encoding="utf-8")
    assert all(term not in source for term in ("app.db", "app.main", "app.workflow", "sqlalchemy"))


def test_second_request_in_same_case_blocked(tmp_path, wire, monkeypatch):
    original = model_adapter.ModelAdapter.draft

    def double(self, request):
        original(self, request)
        return original(self, request)

    monkeypatch.setattr(model_adapter.ModelAdapter, "draft", double)
    report = runner.sample(config(), runner.plan(), tmp_path / "batch/raw.json", allow_live=True)
    assert len(wire["payloads"]) == report["attempted_requests"] == 1
    assert report["results"][0]["failure_type"] == "request_budget_exceeded"


@pytest.mark.parametrize("field", ["model_payload", "id_map", "version", "fake"])
def test_export_rejects_drift(tmp_path, wire, field):
    raw = tmp_path / "batch/raw.json"
    report = runner.sample(config(), runner.plan(), raw, allow_live=True)
    if field == "model_payload":
        report["results"][2][field]["stars"][0]["tags"] = []
    elif field == "id_map":
        report["results"][2]["capture"][field] = {runner.SYNTHETIC_ID: "wrong"}
    elif field == "version":
        report["prompt_version"] = "wrong"
    else:
        report["mode"] = "fake"
    raw.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError):
        runner.export_reviewed(raw, tmp_path / "public.json")
    assert not (tmp_path / "public.json").exists()


def test_sampling_subprocess_forbids_db_private_config_and_network(tmp_path):
    code = r"""
import sys, runpy
from pathlib import Path
def audit(event, args):
    if event.startswith(("socket.", "sqlite3.")):
        raise RuntimeError("forbidden IO")
    if event == "open":
        name = str(args[0]).lower().replace("\\", "/")
        if any(p.startswith(".env") for p in name.split("/")) or name.endswith((".db", ".sqlite")):
            raise RuntimeError("private read")
    if event == "import" and args[0] in {"app.db", "app.main", "app.workflow", "sqlalchemy"}:
        raise RuntimeError("DB or workflow import")
sys.addaudithook(audit)
runner = runpy.run_path("evals/collect_quality.py")
from app.config import Settings
from app import model_adapter
class FakeChat:
    def __init__(self, **options): pass
    def bind_tools(self, *args, **kwargs): return self
    def invoke(self, messages): raise TimeoutError("never saved private-host Authorization")
model_adapter.ChatOpenAI = FakeChat
config = Settings(_env_file=None, mock_mode=False, model_provider="bailian",
    model_name="qwen3.8-flash", model_api_key="offline-only-placeholder", model_max_retries=0,
    model_api_base_url="https://offline-fixture.cn-beijing.maas.aliyuncs.com/compatible-mode/v1")
report = runner["sample"](config, runner["plan"](), Path(sys.argv[1]), allow_live=True)
assert report["attempted_requests"] == 1
assert report["results"][0]["failure_type"] == "timeout"
assert report["results"][0]["usage"] == "unknown"
assert "offline-only-placeholder" not in str(report) and "Authorization" not in str(report)
print("fake-only-no-db-no-config-no-network")
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path / "batch/raw.json")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "fake-only-no-db-no-config-no-network"


def test_interrupted_attempt_remains_unknown(tmp_path, wire):
    raw = tmp_path / "batch/raw.json"
    wire["fail_at"] = 1
    report = runner.sample(config(), runner.plan(), raw, allow_live=True)
    row = report["results"][0]
    row["status"] = "attempted_unknown"
    row["elapsed_ms"] = None
    row.pop("failure_type")
    raw.write_text(json.dumps(report), encoding="utf-8")
    public = tmp_path / "reviewed.json"
    runner.export_reviewed(raw, public)
    data = json.loads(public.read_text(encoding="utf-8"))
    assert data["results"][0]["failure_type"] == "interrupted_unknown"
    assert data["sampling"]["attempts"][0]["usage"] == "unknown"
    assert data["sampling"]["attempts"][0]["elapsed_ms"] is None
    assert evaluate(prepare_captures(data))["manual"]["rated"] == 0


def test_suite_hash_drift_rejected(monkeypatch):
    monkeypatch.setattr(runner, "file_hash", lambda _: "wrong-version")
    with pytest.raises(ValueError, match="fixed_suite_changed"):
        runner.plan()
