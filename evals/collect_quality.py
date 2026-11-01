"""Fixed adapter DTO baseline. Offline by default; no database or workflow imports."""
# ruff: noqa: E402

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "evals"))
from check_results import Capture, Results, load_suite, normalize_capture, prepare_captures
from app.schemas import AgentRequest, Preferences

CASE_IDS = ("explicit-motivation", "unknown-motivation", "grounded-explore")
SUITE_HASH = "f4e90c1783d0cf4168f5f833ac2e87d5e2b29aebb990e95fb74392337488dea4"
RAW = ROOT / ".cache/quality-baseline-v1/raw.json"
PUBLIC = ROOT / "evals/reviewed_quality_captures.json"
SYNTHETIC_ID = "00000000-0000-4000-8000-000000000001"


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def suite_hash(path):
    """Fixed public JSON only: CRLF -> LF; preserve every other byte."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def versions():
    return {
        "prompt_version": "sha256:" + file_hash(ROOT / "backend/app/model_adapter.py"),
        "workflow_version": "not_executed:adapter_dto",
        "retrieval_version": "fixed-public-snapshot:sha256:" + SUITE_HASH,
    }


def plan():
    if suite_hash(ROOT / "evals/quality_cases.json") != SUITE_HASH:
        raise ValueError("fixed_suite_changed")
    suite = load_suite()
    cases = {c["id"]: c for c in suite["cases"]}
    captures = []
    for case_id in CASE_IDS:
        case = cases[case_id]
        stars = deepcopy(case.get("retrieved_stars", []))
        mapping = {}
        if stars:
            mapping[SYNTHETIC_ID] = stars[0]["star_id"]
            stars[0]["star_id"] = SYNTHETIC_ID
        captures.append(
            {
                "case_id": case_id,
                "status": "executed",
                "manual": {},
                "capture": {
                    "observation_layer": "adapter_dto",
                    "generation_versions": versions(),
                    "input": case["input"],
                    "preferences": case.get("preferences", {}),
                    "retrieved_stars": stars,
                    "id_map": mapping,
                    "raw_output": None,
                },
            }
        )
    return captures


def adapter_inputs(capture):
    # Save defaults too: these are the actual arguments supplied to the adapter.
    return {
        "request": AgentRequest.model_validate(capture["input"]).model_dump(mode="json"),
        "stars": deepcopy(capture["retrieved_stars"]),
        "preferences": Preferences.model_validate(capture["preferences"]).model_dump(mode="json"),
    }


def validate_plan(records):
    expected = plan()
    if len(records) != 3:
        raise ValueError("fixed_order_required")
    for record, reference in zip(records, expected, strict=True):
        if record != reference:
            raise ValueError("fixed_context_or_versions_changed")


def save(path, report):
    # Flush before every attempted request; an interrupted attempt stays unknown.
    import os

    with path.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def sample(config, records, output, *, allow_live=False):
    if not allow_live:
        raise ValueError("allow_live_required")
    # Lazy imports: offline planning/export never reads Settings or constructs SDK clients.
    from run_live import validate_live_config
    from app.model_adapter import ModelAdapter, ModelFailure

    validate_live_config(config)
    if config.model_provider != "bailian" or config.model_name != "qwen3.8-flash":
        raise ValueError("fixed_qwen_required")
    validate_plan(records)
    # An existing directory blocks reruns, including after a crash. No resume/overwrite switch.
    output.parent.mkdir(parents=True, exist_ok=False)
    hashes = {
        p: suite_hash(ROOT / p) if p == "evals/quality_cases.json" else file_hash(ROOT / p)
        for p in (
            "backend/app/model_adapter.py",
            "backend/app/schemas.py",
            "backend/app/rules.py",
            "evals/collect_quality.py",
            "evals/run_live.py",
            "evals/quality_cases.json",
            "evals/QUALITY_RUBRIC.md",
            "evals/check_results.py",
        )
    }
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True))
    report = {
        "format_version": "private-quality-sampling-v1",
        "public_data": False,
        "mode": "live",
        "model": config.model_name,
        "provider": "bailian",
        "case_version": load_suite()["version"],
        "rubric_version": load_suite()["rubric_version"],
        **versions(),
        "git_sha": git_sha,
        "working_tree_dirty": dirty,
        "source_hashes": hashes,
        "suite_hash_normalization": "crlf-to-lf",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "workflow_executed": False,
        "approval_observation": "not_observed:adapter_only",
        "synthetic_ids": True,
        "max_requests": 3,
        "sdk_retries": 0,
        "max_output_tokens": config.model_max_tokens,
        "timeout_seconds": config.model_timeout,
        "enable_thinking": False,
        "attempted_requests": 0,
        "results": [],
    }
    save(output, report)

    class BoundedAdapter(ModelAdapter):
        def request(self, tool_name, schema, payload):
            if report["attempted_requests"] >= 3 or item["status"] != "not_attempted":
                raise ModelFailure("request_budget_exceeded")
            report["attempted_requests"] += 1
            item["status"] = "attempted_unknown"
            item["model_payload"] = deepcopy(payload)
            save(output, report)  # Count before invoke, even if it times out or the process dies.
            from langsmith import tracing_context

            with tracing_context(enabled=False):
                return super().request(tool_name, schema, payload)

    model = BoundedAdapter(config)
    for record in records:
        item = deepcopy(record)
        item.update(
            status="not_attempted",
            usage="unknown",
            elapsed_ms=None,
            adapter_inputs=adapter_inputs(item["capture"]),
        )
        report["results"].append(item)
        inputs = item["adapter_inputs"]
        start = perf_counter()
        try:
            request = AgentRequest.model_validate(inputs["request"])
            if request.request_type == "collect":
                dto = model.draft(request)
            else:
                dto = model.proposals(
                    request, deepcopy(inputs["stars"]), Preferences.model_validate(inputs["preferences"])
                )
            if item["status"] != "attempted_unknown":
                raise ModelFailure("no_model_request")
            item["capture"]["raw_output"] = dto.model_dump(mode="json")
            case = next(c for c in load_suite()["cases"] if c["id"] == item["case_id"])
            normalize_capture(
                Capture.model_validate(item["capture"]),
                case,
                Results.model_validate(
                    {
                        **{
                            k: report[k]
                            for k in (
                                "case_version",
                                "rubric_version",
                                "prompt_version",
                                "workflow_version",
                                "retrieval_version",
                                "mode",
                                "model",
                            )
                        },
                        "format_version": "offline-results-v1",
                        "public_data": True,
                        "results": [],
                    }
                ),
            )
            item["status"] = "schema_valid"
        except Exception as exc:
            # Never serialize exceptions, responses, headers or hidden reasoning.
            allowed = {
                "timeout",
                "rate_limit",
                "model_unavailable",
                "invalid_tool_call",
                "invalid_model_output",
                "no_model_request",
                "request_budget_exceeded",
            }
            kind = getattr(exc, "kind", None)
            item.update(status="failed", failure_type=kind if kind in allowed else "runner_error")
        item["usage"] = model.last_usage if model.last_usage is not None else "unknown"
        item["elapsed_ms"] = round((perf_counter() - start) * 1000)
        save(output, report)
        if item["status"] == "failed":
            break
    return report


def export_reviewed(raw, destination):
    """Only invoked after explicit human public-content review; no model calls."""
    data = json.loads(raw.read_text(encoding="utf-8"))
    if (
        data.get("format_version") != "private-quality-sampling-v1"
        or data.get("mode") != "live"
        or data.get("model") != "qwen3.8-flash"
        or data.get("provider") != "bailian"
        or data.get("public_data") is not False
        or data.get("workflow_executed") is not False
        or data.get("sdk_retries") != 0
        or data.get("max_requests") != 3
    ):
        raise ValueError("not_fixed_live_sampling")
    rows = data["results"]
    hashes = data.get("source_hashes", {})
    if (
        data.get("prompt_version") != "sha256:" + hashes.get("backend/app/model_adapter.py", "")
        or data.get("retrieval_version") != versions()["retrieval_version"]
        or data.get("workflow_version") != "not_executed:adapter_dto"
        or hashes.get("evals/quality_cases.json") != SUITE_HASH
        or suite_hash(ROOT / "evals/quality_cases.json") != SUITE_HASH
        or len(data.get("git_sha", "")) != 40
        or data.get("attempted_requests") != len(rows)
    ):
        raise ValueError("sampling_provenance_mismatch")
    if not 1 <= len(rows) <= 3 or [r["case_id"] for r in rows] != list(CASE_IDS[: len(rows)]):
        raise ValueError("invalid_attempt_order")
    batch = {
        k: data[k]
        for k in (
            "case_version",
            "rubric_version",
            "prompt_version",
            "workflow_version",
            "retrieval_version",
            "mode",
            "model",
        )
    }
    batch.update(format_version="public-captures-v1", public_data=True, results=[])
    for index, row in enumerate(rows):
        if row["status"] not in {"schema_valid", "failed", "attempted_unknown"}:
            raise ValueError("unrecognized_attempt")
        if row["status"] != "schema_valid" and index != len(rows) - 1:
            raise ValueError("failure_did_not_stop")
        if row["adapter_inputs"] != adapter_inputs(row["capture"]):
            raise ValueError("adapter_context_changed")
        inputs = row["adapter_inputs"]
        expected_payload = inputs["request"]
        if inputs["request"]["request_type"] == "explore":
            expected_payload = {
                **inputs,
                "effective_limits": {"minutes": 10, "budget": 0, "energy": "low"},
                "constraint_template": None,
            }
        if row["model_payload"] != expected_payload:
            raise ValueError("model_payload_context_changed")
        result = {k: row[k] for k in ("case_id", "capture", "manual")}
        result["status"] = "executed"
        if row["status"] != "schema_valid":
            result["failure_type"] = row.get("failure_type", "interrupted_unknown")
        batch["results"].append(result)
    batch["sampling"] = {k: v for k, v in data.items() if k not in {"results", "public_data"}}
    batch["sampling"]["attempts"] = [
        {k: v for k, v in row.items() if k not in {"capture", "manual"}} for row in rows
    ]
    # Keep exact existing context/version/ID rules, including rejection of unknown source IDs.
    prepare_captures(batch)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(batch, stream, ensure_ascii=False, indent=2, allow_nan=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--allow-live", action="store_true")
    group.add_argument("--export-reviewed-public", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.export_reviewed_public:
            export_reviewed(RAW, PUBLIC)
            print("Exported reviewed public captures: evals/reviewed_quality_captures.json")
        elif args.allow_live:
            from app.config import Settings

            report = sample(Settings(), plan(), RAW, allow_live=True)
            print("Private sampling record: .cache/quality-baseline-v1/raw.json; review before export")
            return int(any(r["status"] != "schema_valid" for r in report["results"]))
        else:
            print(
                json.dumps({"mode": "offline", "requests": 0, "plan": plan()}, ensure_ascii=False, indent=2)
            )
        return 0
    except Exception:
        print("Stopped: configuration, fixed context, existing batch or evidence validation failed.")
        return 2  # No raw errors, config values, paths or provider bodies.


if __name__ == "__main__":
    raise SystemExit(main())
