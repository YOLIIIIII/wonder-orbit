"""AGENT-004-G: independent four-slot experience experiment; offline by default."""

# ruff: noqa: E402
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
from check_learning_quality import context, suite, digest, observe, provenance, DIMENSIONS, Rating
from collect_learning_quality_v3 import durable_create, snapshot, quest_diagnostics
from app.schemas import AgentRequest, Preferences, ProposalResult

BASELINE = "aad9ddba7ab7b6c4b0cb6aacb477584344dbb0b0"
SCIENCE_HASH = "f8858622dbe048582169f99cf6308e593e35359fe360029704de1974f7c0ae96"
PLAN = (("G-01", "science"), ("G-02", "CASE-01"), ("G-03", "CASE-04"), ("G-04", "science"))


def contexts():
    cases = {c["case_id"]: c for c in suite()["cases"]}
    path = ROOT / "evals/knowledge_preview_material.json"
    if digest(path, normalize=True) != SCIENCE_HASH:
        raise ValueError("fixed_science_changed")
    material = json.loads(path.read_text(encoding="utf-8"))
    science = context(cases["CASE-01"])
    science["request"]["learning_source"] = {k: material[k] for k in ("text", "label", "url")}
    # Same request wording, public retrieval snapshot and preferences for both science samples.
    return [
        dict(
            sample_id=sid,
            material_version=material["version"] if case == "science" else cases[case]["case_version"],
            material_file_sha256=SCIENCE_HASH
            if case == "science"
            else digest(ROOT / "evals/learning_quality_cases.json", normalize=True),
            context=deepcopy(science) if case == "science" else context(cases[case]),
        )
        for sid, case in PLAN
    ]


def plan():
    return dict(
        format_version="knowledge-experience-g-v1",
        mode="offline_plan",
        model="qwen3.8-flash",
        max_requests=4,
        sdk_retries=0,
        samples=contexts(),
    )


def validate_production_subject():
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != BASELINE:
        raise ValueError("baseline_changed")
    # Experiment must not silently alter its production subject.
    for name in ("model_adapter.py", "learning.py", "schemas.py", "rules.py"):
        path = "backend/app/" + name
        original = subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)
        if original.replace(b"\r\n", b"\n") != (ROOT / path).read_bytes().replace(b"\r\n", b"\n"):
            raise ValueError("production_subject_changed")


def preflight(config):
    from run_live import validate_live_config

    validate_live_config(config)
    if config.model_provider != "bailian" or config.model_name != "qwen3.8-flash":
        raise ValueError("fixed_qwen_required")
    validate_production_subject()
    data = contexts()
    for row in data:
        AgentRequest.model_validate(row["context"]["request"])
        Preferences.model_validate(row["context"]["preferences"])
    if data[0]["context"] != data[3]["context"]:
        raise ValueError("science_context_mismatch")
    return data


def validation_diagnostics(exc):
    """Only schema-known paths/types; extra field names may themselves contain secrets."""
    from pydantic import ValidationError

    cause = exc.__cause__
    if not isinstance(cause, ValidationError):
        return []
    schema = ProposalResult.model_json_schema()
    known = set()

    def walk(node):
        if isinstance(node, dict):
            known.update(node.get("properties", {}))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    return [
        dict(
            path=[x if type(x) is int or x in known else "<unknown_field>" for x in e["loc"]], type=e["type"]
        )
        for e in cause.errors(include_url=False, include_context=False, include_input=False)
    ]


def sample(config, *, allow_live=False, root=ROOT):
    if not allow_live:
        raise ValueError("allow_live_required")
    rows = preflight(config)
    from app import model_adapter as module
    from app.model_adapter import ModelAdapter, ModelFailure

    ledger = root / ".cache/knowledge-experience-g-budget"
    output = root / ".cache/knowledge-experience-g/raw.json"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.mkdir(exist_ok=False)
    durable_create(ledger / "plan.json", plan())
    output.parent.mkdir(parents=True, exist_ok=False)
    report = dict(
        format_version="knowledge-experience-g-v1",
        git_sha=BASELINE,
        working_tree_dirty=bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
        provenance=provenance("live"),
        attempted_requests=0,
        started_at=datetime.now(timezone.utc).isoformat(),
        results=[],
    )
    report["provenance"]["model_config"].update(
        max_requests=4, max_output_tokens=config.model_max_tokens, timeout_seconds=config.model_timeout
    )
    report["provenance"]["source_hashes"]["evals/run_knowledge_experience_g.py"] = digest(Path(__file__))
    for row in rows:
        row.update(
            status="not_run",
            raw_output=None,
            validated_output=None,
            gate=None,
            quest=None,
            usage="unknown",
            elapsed_ms=None,
            failure_type=None,
            manual={d: Rating().model_dump() for d in DIMENSIONS},
        )
        report["results"].append(row)
    snapshot(output, report)

    class BoundedAdapter(ModelAdapter):
        def request(self, tool_name, schema, payload):
            if (
                tool_name != "generate_quest_proposal"
                or schema is not ProposalResult
                or item["status"] != "not_run"
                or report["attempted_requests"] >= 4
                or len(list(ledger.glob("*.attempt.json"))) >= 4
            ):
                raise ModelFailure("request_budget_exceeded")
            durable_create(
                ledger / f"{item['sample_id']}.attempt.json",
                dict(sample_id=item["sample_id"], attempted_at=datetime.now(timezone.utc).isoformat()),
            )
            report["attempted_requests"] += 1
            item.update(status="attempted_unknown", model_payload=deepcopy(payload))
            snapshot(output, report)
            factory = module.ChatOpenAI

            class CaptureClient:
                def __init__(self, **kwargs):
                    self.client = factory(**kwargs)

                def bind_tools(self, tools, **kwargs):
                    item["tool_schema"] = deepcopy(tools)
                    self.bound = self.client.bind_tools(tools, **kwargs)
                    return self

                def invoke(self, messages):
                    item["model_messages"] = [dict(role=m.type, content=m.content) for m in messages]
                    snapshot(output, report)
                    return self.bound.invoke(messages)

            from langsmith import tracing_context

            with tracing_context(enabled=False), patch.object(module, "ChatOpenAI", CaptureClient):
                return super().request(tool_name, schema, payload)

    model = BoundedAdapter(config)
    for item in report["results"]:
        start = perf_counter()
        model.last_usage = None
        try:
            inputs = item["context"]
            dto = model.proposals(
                AgentRequest.model_validate(inputs["request"]),
                deepcopy(inputs["stars"]),
                Preferences.model_validate(inputs["preferences"]),
            )
            if item["status"] != "attempted_unknown":
                raise ModelFailure("runner_error")
            item["raw_output"] = dto.model_dump(mode="json")
            snapshot(output, report)
            item["quest"] = quest_diagnostics(inputs, item["raw_output"])
            item["validated_output"], item["gate"] = observe(
                AgentRequest.model_validate(inputs["request"]), item["raw_output"]
            )
            item["status"] = "executed"
        except ModelFailure as exc:
            item.update(status="failed", failure_type=exc.kind)
            if exc.kind == "invalid_model_output":
                item["validation_errors"] = validation_diagnostics(exc)
        except Exception:
            item.update(status="failed", failure_type="runner_error")
        finally:
            item["usage"] = model.last_usage or "unknown"
            item["elapsed_ms"] = round((perf_counter() - start) * 1000)
            snapshot(output, report)
            durable_create(ledger / f"{item['sample_id']}.result.json", item)
        if item["status"] != "executed":
            break
    if all(r["status"] == "executed" for r in report["results"]):
        durable_create(ledger / "complete.json", dict(completed=True))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_live:
        print(json.dumps(plan(), ensure_ascii=False, indent=2))
        return 0
    try:
        from app.config import Settings

        report = sample(Settings(), allow_live=True)
        print(
            json.dumps(
                dict(
                    attempted_requests=report["attempted_requests"],
                    results=[
                        {k: r[k] for k in ("sample_id", "status", "failure_type", "usage")}
                        for r in report["results"]
                    ],
                )
            )
        )
        return int(any(r["status"] != "executed" for r in report["results"]))
    except Exception:
        print('{"error":"knowledge_experience_g_stopped"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
