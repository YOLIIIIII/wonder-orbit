"""Fixed future learning sampling; default invocation only prints an offline plan."""
# ruff: noqa: E402

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
from check_learning_quality import LIVE_IDS, empty_batch, evaluate, observe

RAW = ROOT / ".cache/learning-quality-v1/raw.json"


def sample(config, output=RAW, *, allow_live=False):
    if not allow_live:
        raise ValueError("allow_live_required")
    # Imports that read config or can construct SDK clients are behind the explicit gate.
    from run_live import validate_live_config
    from app.model_adapter import ModelAdapter, ModelFailure
    from app.schemas import AgentRequest, Preferences
    from collect_quality import save

    validate_live_config(config)
    if config.model_provider != "bailian" or config.model_name != "qwen3.8-flash":
        raise ValueError("fixed_qwen_required")
    report = empty_batch("live")
    report["provenance"]["model_config"].update(
        max_output_tokens=config.model_max_tokens, timeout_seconds=config.model_timeout
    )
    import subprocess
    from datetime import datetime, timezone

    report.update(
        started_at=datetime.now(timezone.utc).isoformat(),
        git_sha=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        working_tree_dirty=bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
        attempted_requests=0,
    )
    # Atomic directory reservation. Interrupted, failed and completed batches all block replay.
    output.parent.mkdir(parents=True, exist_ok=False)
    save(output, report)
    attempted = set()

    class BoundedAdapter(ModelAdapter):
        def request(self, tool_name, schema, payload):
            if (
                report["attempted_requests"] >= 3
                or item["case_id"] in attempted
                or tool_name != "generate_quest_proposal"
            ):
                raise ModelFailure("request_budget_exceeded")
            attempted.add(item["case_id"])
            report["attempted_requests"] += 1
            item.update(status="attempted_unknown", model_payload=deepcopy(payload))
            save(output, report)
            from langsmith import tracing_context

            with tracing_context(enabled=False):
                return super().request(tool_name, schema, payload)

    model = BoundedAdapter(config)
    for case_id in LIVE_IDS:
        item = next(r for r in report["results"] if r["case_id"] == case_id)
        inputs = item["context"]
        request = AgentRequest.model_validate(inputs["request"])
        start = perf_counter()
        try:
            dto = model.proposals(
                request, deepcopy(inputs["stars"]), Preferences.model_validate(inputs["preferences"])
            )
            if item["status"] != "attempted_unknown":
                raise ModelFailure("runner_error")
            # Save the adapter DTO before any system validation; never repair or re-request it.
            item["raw_output"] = dto.model_dump(mode="json")
            save(output, report)
            item["validated_output"], item["gate"] = observe(request, item["raw_output"])
            item["status"] = "executed"
        except ModelFailure as exc:
            item.update(status="failed", failure_type=exc.kind)
        except Exception:
            # A gate/persistence failure after a DTO exists leaves the raw evidence on disk.
            # Do not invent an empty DTO or claim model refusal.
            item.update(status="failed", failure_type="runner_error")
        finally:
            item["usage"] = model.last_usage or "unknown"
            item["elapsed_ms"] = round((perf_counter() - start) * 1000)
            save(output, report)
        if item["status"] == "failed" or (item["gate"] and item["gate"]["reason"] == "source_gate_rejected"):
            break
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_live:
        print(
            json.dumps(
                {
                    "mode": "offline_plan",
                    "selected_cases": LIVE_IDS,
                    "max_requests": 3,
                    "sdk_retries": 0,
                    "batch": empty_batch(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    try:
        from app.config import Settings

        report = sample(Settings(), allow_live=True)
        # Private raw file requires manual review; no automatic export or upload.
        return int(evaluate(report)["deterministic"]["failed"] > 0)
    except Exception:
        print('{"error":"learning_sampling_stopped"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
