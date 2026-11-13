"""Learning captures v3: fixed two batches, durable six-slot budget, offline by default."""
# ruff: noqa: E402

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
from check_learning_quality import LIVE_IDS, context, observe, provenance, suite, DIMENSIONS, Rating, digest
from app.rules import quest_constraint_errors, SUPPORTED_CONSTRAINTS
from app.schemas import AgentRequest, Preferences, ProposalResult

FORMAT = "learning-captures-v3"
PLAN = tuple((batch, case, f"{case}-S{batch:02d}") for batch in (1, 2) for case in LIVE_IDS)


def durable_create(path, value):
    """Exclusive, fsynced evidence. Partial writes conservatively block reuse."""
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def snapshot(path, value):
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def plan():
    return {
        "format_version": FORMAT,
        "mode": "offline_plan",
        "model": "qwen3.8-flash",
        "sdk_retries": 0,
        "max_requests": 6,
        "max_per_batch": 3,
        "max_per_case": 2,
        "samples": [{"batch": b, "case_id": c, "sample_id": s} for b, c, s in PLAN],
    }


def quest_diagnostics(inputs, raw):
    """Read-only DTO checks reuse production rules; never claim DB/workflow acceptance."""
    request = AgentRequest.model_validate(inputs["request"])
    pref = Preferences.model_validate(inputs["preferences"])
    dto = ProposalResult.model_validate(raw)
    allowed = {s["star_id"] for s in inputs["stars"]}
    return {
        "database_star_existence": "not_observed",
        "workflow": "not_executed",
        "execution_conditions": "not_observed_requires_manual_review",
        "unsupported_constraints": [c for c in pref.constraints if c not in SUPPORTED_CONSTRAINTS],
        "proposals": [
            {
                "index": i,
                "retrieved_star_ids_match": set(p.based_on_star_ids) <= allowed,
                "estimated_minutes": p.estimated_minutes,
                "estimated_budget": p.estimated_budget,
                "energy_level": p.energy_level,
                "minutes_within_limits": not any(
                    e in quest_constraint_errors(p, request, pref)
                    for e in ("超过时间上限", "少于偏好的最短时间")
                ),
                "budget_within_limit": "预算未知或超过上限" not in quest_constraint_errors(p, request, pref),
                "energy_within_limit": "超过精力上限" not in quest_constraint_errors(p, request, pref),
                "constraint_errors": quest_constraint_errors(p, request, pref),
                "rule_checks_passed": set(p.based_on_star_ids) <= allowed
                and not quest_constraint_errors(p, request, pref),
            }
            for i, p in enumerate(dto.proposals)
        ],
        "empty_proposals": not dto.proposals,
    }


def sample(config, *, batch=1, allow_live=False, root=ROOT):
    if not allow_live:
        raise ValueError("allow_live_required")
    if type(batch) is not int or batch not in (1, 2):
        raise ValueError("fixed_batch_required")
    from run_live import validate_live_config
    from app.model_adapter import ModelAdapter, ModelFailure

    validate_live_config(config)
    if config.model_provider != "bailian" or config.model_name != "qwen3.8-flash":
        raise ValueError("fixed_qwen_required")
    # No output-directory flag: production always shares this campaign ledger.
    ledger = root / ".cache/learning-quality-v3-budget"
    output = root / f".cache/learning-quality-v3/batch-{batch}/raw.json"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    if batch == 1:
        ledger.mkdir(exist_ok=False)
        durable_create(ledger / "plan.json", plan())
    elif json.loads((ledger / "plan.json").read_text(encoding="utf-8")) != plan():
        raise ValueError("campaign_plan_changed")
    if batch == 2:
        # Failed/unknown first batch cannot unlock more calls, nor be supplemented.
        if not (ledger / "batch-1-complete.json").is_file():
            raise ValueError("first_batch_not_complete")
        for _, _, sid in PLAN[:3]:
            if not (ledger / f"{sid}.result.json").is_file():
                raise ValueError("first_batch_evidence_missing")
    durable_create(ledger / f"batch-{batch}-reserved.json", {"batch": batch})
    output.parent.mkdir(parents=True, exist_ok=False)
    cases = {c["case_id"]: c for c in suite()["cases"]}
    report = {
        "format_version": FORMAT,
        "batch": batch,
        "plan": plan(),
        "provenance": provenance("live"),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "working_tree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
        "attempted_requests": 0,
        "results": [
            {
                "case_id": c,
                "sample_id": s,
                "context": context(cases[c]),
                "status": "not_run",
                "raw_output": None,
                "validated_output": None,
                "gate": None,
                "quest": None,
                "usage": "unknown",
                "elapsed_ms": None,
                "failure_type": None,
                "manual": {d: Rating().model_dump() for d in DIMENSIONS},
            }
            for b, c, s in PLAN
            if b == batch
        ],
    }
    report["provenance"]["model_config"].update(
        max_requests=6,
        max_per_batch=3,
        max_per_case=2,
        max_output_tokens=config.model_max_tokens,
        timeout_seconds=config.model_timeout,
    )
    report["provenance"]["source_hashes"]["evals/collect_learning_quality_v3.py"] = digest(Path(__file__))
    snapshot(output, report)

    class BoundedAdapter(ModelAdapter):
        def request(self, tool_name, schema, payload):
            sid = item["sample_id"]
            attempts = list(ledger.glob("*.attempt.json"))
            case_attempts = list(ledger.glob(f"{item['case_id']}-S*.attempt.json"))
            if (
                tool_name != "generate_quest_proposal"
                or schema is not ProposalResult
                or report["attempted_requests"] >= 3
                or len(attempts) >= 6
                or len(case_attempts) >= 2
                or item["status"] != "not_run"
            ):
                raise ModelFailure("request_budget_exceeded")
            # Exclusive slot reservation precedes every network attempt. Never removed.
            durable_create(
                ledger / f"{sid}.attempt.json",
                {
                    "sample_id": sid,
                    "case_id": item["case_id"],
                    "batch": batch,
                    "attempted_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            report["attempted_requests"] += 1
            item.update(status="attempted_unknown", model_payload=deepcopy(payload))
            snapshot(output, report)
            from langsmith import tracing_context

            with tracing_context(enabled=False):
                return super().request(tool_name, schema, payload)

    model = BoundedAdapter(config)
    for item in report["results"]:
        inputs = item["context"]
        start = perf_counter()
        model.last_usage = None
        try:
            dto = model.proposals(
                AgentRequest.model_validate(inputs["request"]),
                deepcopy(inputs["stars"]),
                Preferences.model_validate(inputs["preferences"]),
            )
            if item["status"] != "attempted_unknown":
                raise ModelFailure("runner_error")
            item["raw_output"] = dto.model_dump(mode="json")
            snapshot(output, report)
            # Diagnose raw proposals even when source gating subsequently removes them.
            item["quest"] = quest_diagnostics(inputs, item["raw_output"])
            item["validated_output"], item["gate"] = observe(
                AgentRequest.model_validate(inputs["request"]), item["raw_output"]
            )
            item["status"] = "executed"
        except ModelFailure as exc:
            item.update(status="failed", failure_type=exc.kind)
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
        durable_create(ledger / f"batch-{batch}-complete.json", {"batch": batch})
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--batch", type=int, choices=(1, 2), default=1)
    args = parser.parse_args(argv)
    if not args.allow_live:
        print(json.dumps(plan(), ensure_ascii=False, indent=2))
        return 0
    try:
        from app.config import Settings

        report = sample(Settings(), batch=args.batch, allow_live=True)
        return int(any(r["status"] != "executed" for r in report["results"]))
    except Exception:
        print('{"error":"learning_v3_sampling_stopped"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
