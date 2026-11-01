"""Public fixtures verify the checker, never a model quality baseline."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("offline_checker", ROOT / "evals/check_results.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def sample():
    return json.loads((ROOT / "evals/sample_fake_results.json").read_text(encoding="utf-8"))


def explore(case_id="grounded-explore"):
    data = sample()
    data["results"] = [
        {
            "case_id": case_id,
            "status": "executed",
            "output": {
                "proposals": [
                    {
                        "title": "记录发光问题",
                        "description": "围绕发光记录问题",
                        "estimated_minutes": 10,
                        "estimated_budget": 0,
                        "energy_level": "low",
                        "steps": ["写下想了解的发光问题"],
                        "based_on_star_ids": ["public-star-ocean"],
                        "rationale": "来自收藏的发光兴趣",
                        "uncertainties": ["不保证解答科学问题"],
                    }
                ],
                "questions": [],
            },
        }
    ]
    return data


def statuses(report):
    return {c["name"]: c["status"] for row in report["cases"] for c in row["checks"]}


def test_correct_and_missing_manual_are_separate():
    report = checker.evaluate(sample())
    assert report["deterministic"]["failed"] == 0
    assert report["deterministic"]["not_run"] == 9
    assert report["manual"] == {"rated": 0, "not_rated": 60}
    assert statuses(report)["approval_boundary"] == "not_rated"
    assert report["metadata"]["prompt_version"] == "not_recorded"
    data = sample()
    data["results"][0]["manual"] = {"topic": {"score": 2, "note": "主题与公开原文一致"}}
    assert checker.evaluate(data)["manual"]["rated"] == 1


@pytest.mark.parametrize(
    "field,value,check",
    [
        ("based_on_star_ids", ["invented-id"], "retrieved_star_ids"),
        ("estimated_minutes", 11, "time"),
        ("estimated_budget", 1, "budget"),
        ("estimated_budget", None, "budget"),
        ("energy_level", "high", "energy"),
        ("estimated_minutes", -1, "output_schema"),
        ("steps", [], "output_schema"),
    ],
)
def test_invalid_proposal(field, value, check):
    data = explore()
    data["results"][0]["output"]["proposals"][0][field] = value
    report = checker.evaluate(data)
    assert any(
        c["name"].endswith(check) and c["status"] == "failed"
        for row in report["cases"]
        for c in row["checks"]
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("interest_reason", "热爱自然"),
        ("estimated_minutes", 10),
        ("estimated_budget", 0),
        ("energy_level", "low"),
        ("original_text", "篡改原文"),
        ("source_reference", "https://example.org/wrong"),
    ],
)
def test_invented_unknown_or_source(field, value):
    data = sample()
    data["results"][0]["output"]["draft"][field] = value
    assert checker.evaluate(data)["deterministic"]["failed"] > 0


@pytest.mark.parametrize("case_id", ["empty-history", "unsupported-constraint"])
def test_no_proposal_policy(case_id):
    data = explore(case_id)
    assert checker.evaluate(data)["deterministic"]["failed"] > 0
    data["results"][0]["output"] = {"proposals": [], "questions": ["请补充可支持的兴趣或约束"]}
    assert checker.evaluate(data)["deterministic"]["failed"] == 0


def test_legal_vague_output_does_not_receive_quality_score():
    data = explore("vague-but-legal")
    data["results"][0]["output"]["proposals"][0]["steps"] = ["想一想"]
    report = checker.evaluate(data)
    assert report["deterministic"]["failed"] == 0
    assert report["manual"]["rated"] == 0


@pytest.mark.parametrize("decision,delta", [("approved", 1), ("rejected", 0), ("none", 0)])
def test_observed_approval_boundary(decision, delta):
    data = explore("approval-lifecycle")
    evidence = dict(
        before=0,
        after_generation=0,
        after_decision=delta,
        after_repeat=delta,
        decision=decision,
        authorization="isolated_test_simulation",
    )
    data["results"][0]["approval"] = evidence
    assert statuses(checker.evaluate(data))["approval_boundary"] == "passed"
    evidence["after_generation"] = 1
    assert statuses(checker.evaluate(data))["approval_boundary"] == "failed"
    evidence["after_generation"] = 0
    evidence["after_repeat"] = delta + 1
    assert statuses(checker.evaluate(data))["approval_boundary"] == "failed"


@pytest.mark.parametrize(
    "mode,evidence",
    [("fake", "tool_self_test"), ("mock", "application_mock"), ("live", "supplied_live_output_unverified")],
)
def test_evidence_type_and_versions(mode, evidence):
    data = sample()
    data.update(mode=mode, prompt_version="p1", workflow_version="w1", retrieval_version="r1")
    a = checker.evaluate(data)
    data["prompt_version"] = "p2"
    b = checker.evaluate(data)
    assert a["evidence_type"] == evidence
    assert a["metadata"] != b["metadata"]
    for field in ["case_version", "rubric_version"]:
        bad = deepcopy(data)
        bad[field] = "v-future"
        with pytest.raises(ValueError):
            checker.evaluate(bad)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.pop("mode"),
        lambda d: d.update(results="bad"),
        lambda d: d["results"].append(d["results"][0]),
        lambda d: d["results"][0].update(case_id="unknown"),
        lambda d: d["results"][0].update(manual={"topic": {"score": 3}}),
        lambda d: d["results"][0].update(manual={"topic": {"score": 2}}),
        lambda d: d["results"][0].update(status="not_run"),
        lambda d: d.update(public_data=False),
    ],
)
def test_bad_envelope(mutation):
    data = sample()
    mutation(data)
    with pytest.raises(ValueError):
        checker.evaluate(data)


def test_cli_malformed_and_missing_output(tmp_path, capsys, monkeypatch):
    # pytest temp lives under .cache; isolate JSON/exit-code handling from path policy.
    monkeypatch.setattr(checker, "load_public_json", lambda p: json.loads(p.read_text(encoding="utf-8")))
    path = tmp_path / "public.json"
    path.write_text('{"secret": malformed}', encoding="utf-8")
    assert checker.main(["--results", str(path)]) == 2
    assert "secret" not in capsys.readouterr().out
    data = sample()
    data["results"][0].pop("output")
    path.write_text(json.dumps(data), encoding="utf-8")
    assert checker.main(["--results", str(path)]) == 1


def test_standalone_no_network_private_config_or_database():
    # Fresh interpreter: conftest's app imports cannot hide runtime dependencies.
    code = """
import sys, runpy
def guard(event, args):
    if event.startswith(('socket.', 'sqlite3.')):
        raise AssertionError('network/database access')
    if event == 'open':
        path = str(args[0]).replace('\\\\', '/').lower()
        if '/.env' in path or path.endswith(('.db', '.sqlite')) or '/.cache/' in path:
            raise AssertionError('private read')
    if event == 'import' and args[0] in {'app.config','app.db','app.model_adapter','app.tools','app.workflow'}:
        raise AssertionError('runtime import')
sys.addaudithook(guard)
sys.argv=['check_results.py','--results','evals/sample_fake_results.json']
runpy.run_path('evals/check_results.py',run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", code], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["evidence_type"] == "tool_self_test"


@pytest.mark.parametrize("path", [".cache/report.json", ".env.json", "wonder.db"])
def test_private_paths_rejected_before_open(path):
    with pytest.raises(ValueError):
        checker.load_public_json(ROOT / path)


@pytest.mark.parametrize("value", [True, 1.0, "1"])
def test_rating_types(value):
    with pytest.raises(ValueError):
        checker.Rating.model_validate({"score": value, "note": "依据"})


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"estimated_minutes": 11},
        {"estimated_budget": None},
        {"energy_level": "high"},
        {"based_on_star_ids": ["bad"]},
    ],
)
def test_offline_constraints_match_existing_tool(changes):
    # The checker cannot import the DB-bound tool. Compare against its existing
    # validator here using an in-memory lookup, without creating a database.
    from types import SimpleNamespace
    from app.schemas import ValidateArgs
    from app.tools import ToolRegistry

    data = explore()
    proposal = data["results"][0]["output"]["proposals"][0]
    proposal.update(changes)
    case = next(
        c
        for c in json.loads((ROOT / "evals/quality_cases.json").read_text(encoding="utf-8"))["cases"]
        if c["id"] == "grounded-explore"
    )
    args = ValidateArgs.model_validate(
        {
            "proposal": proposal,
            "request": case["input"],
            "preferences": {},
            "allowed_ids": case["retrieved_star_ids"],
        }
    )
    tool = SimpleNamespace(session=SimpleNamespace(get=lambda *_: True))
    expected = ToolRegistry.validate_quest_proposal(tool, args)["valid"]
    assert (checker.evaluate(data)["deterministic"]["failed"] == 0) == expected


def captures():
    return json.loads((ROOT / "evals/sample_public_captures.json").read_text(encoding="utf-8"))


def test_capture_roundtrip_keeps_original_ids_dtos_and_unrated_scores():
    data = captures()
    before = deepcopy(data)
    prepared = checker.prepare_captures(data)
    assert data == before
    row = prepared["results"][1]
    assert row["capture"]["raw_output"] == data["results"][1]["capture"]["raw_output"]
    assert row["output"]["proposals"][0]["based_on_star_ids"] == ["public-star-ocean"]
    report = checker.evaluate(prepared)
    assert report["deterministic"]["failed"] == 0
    assert report["manual"] == {"rated": 0, "not_rated": 60}
    assert report["evidence_type"] == "tool_self_test"
    assert report["cases"][5]["capture"]["id_map"] == row["capture"]["id_map"]
    assert prepared["results"][0]["output"] == data["results"][0]["capture"]["raw_output"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d["results"][0].pop("capture"),
        lambda d: d["results"].append(deepcopy(d["results"][0])),
        lambda d: d.update(case_version="future"),
        lambda d: d.update(rubric_version="future"),
        lambda d: d.update(prompt_version="other"),
        lambda d: d["results"][0]["capture"]["generation_versions"].update(workflow_version="unknown"),
        lambda d: d["results"][0]["capture"]["input"].update(text="different input"),
        lambda d: d["results"][1]["capture"]["input"].update(budget=False),
        lambda d: d["results"][0]["capture"]["input"].update(source_reference="https://example.org/wrong"),
        lambda d: d["results"][0]["capture"]["generation_versions"].update(prompt_version=" unknown "),
        lambda d: d["results"][1]["capture"].update(preferences={"max_budget": 1}),
        lambda d: d["results"][1]["capture"].update(id_map={}),
        lambda d: d["results"][1]["capture"]["id_map"].update(duplicate="public-star-ocean"),
        lambda d: d["results"][1]["capture"]["retrieved_stars"][0].update(original_text="different source"),
        lambda d: d["results"][1]["capture"]["retrieved_stars"][0].pop("tags"),
        lambda d: d["results"][1]["capture"]["retrieved_stars"].append(
            deepcopy(d["results"][1]["capture"]["retrieved_stars"][0])
        ),
        lambda d: d["results"][1]["capture"]["raw_output"]["proposals"][0].update(
            based_on_star_ids=["unmapped"]
        ),
        lambda d: d["results"][0].update(manual={"imagined": {"score": "not_rated"}}),
        lambda d: d["results"][0].update(manual={"topic": {"score": "unknown"}}),
        lambda d: d["results"][0].update(status="not_run"),
        lambda d: d["results"][0].update(output={"draft": {}}),
        lambda d: d.update(public_data=False),
    ],
)
def test_capture_rejects_unverifiable_context_and_invalid_metadata(mutation):
    data = captures()
    mutation(data)
    with pytest.raises(ValueError):
        checker.prepare_captures(data)


@pytest.mark.parametrize("output", [None, {"draft": {}}, {"proposals": "invalid"}])
def test_capture_missing_or_bad_dto_is_not_invented_or_repaired(output):
    data = captures()
    data["results"][1]["capture"]["raw_output"] = output
    prepared = checker.prepare_captures(data)
    assert prepared["results"][1].get("output") == output
    assert checker.evaluate(prepared)["deterministic"]["failed"] > 0


def test_prepared_output_and_provenance_cannot_drift():
    prepared = checker.prepare_captures(captures())
    prepared["results"][1]["output"]["proposals"][0]["title"] = "edited after preparation"
    with pytest.raises(ValueError):
        checker.evaluate(prepared)


def test_explicit_not_run_and_manual_observations_are_kept():
    data = captures()
    data["results"][0]["manual"] = {"topic": {"score": "not_rated", "note": "尚未人工复核"}}
    data["results"].append({"case_id": "empty-history", "status": "not_run"})
    report = checker.evaluate(checker.prepare_captures(data))
    assert report["cases"][0]["manual"]["topic"]["score"] == "not_rated"
    assert report["cases"][6]["checks"] == [{"name": "output", "status": "not_run"}]


def test_preparation_cli_never_imports_runtime_or_reads_private_paths():
    code = r"""
import sys, runpy

def guard(event, args):
    if event.startswith(('socket.', 'sqlite3.')):
        raise AssertionError('network/database access')
    if event == 'open':
        path = str(args[0]).replace('\\', '/').lower()
        if '/.env' in path or '/.cache/' in path or path.endswith(('.db', '.sqlite')):
            raise AssertionError('private read')
    if event == 'import' and args[0] in {'app.config','app.db','app.model_adapter','app.tools','app.workflow'}:
        raise AssertionError('runtime import')
sys.addaudithook(guard)
sys.argv=['check_results.py','--prepare-captures','evals/sample_public_captures.json']
runpy.run_path('evals/check_results.py',run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", code], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["format_version"] == "offline-results-v1"


def test_preparation_cli_refuses_cache_and_old_runner_format(capsys):
    assert checker.main(["--prepare-captures", ".cache/private-report.json"]) == 2
    assert checker.main(["--prepare-captures", "evals/sample_fake_results.json"]) == 2
    assert "private-report" not in capsys.readouterr().out
