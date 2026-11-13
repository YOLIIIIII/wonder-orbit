"""Offline adapter DTO and source-gate evidence; never infer semantic scores."""
# ruff: noqa: E402

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.learning import resolve_learning_offsets, validate_learning_result
from app.schemas import AgentRequest, Preferences, ProposalResult
from pydantic import BaseModel, ConfigDict, StrictInt, model_validator

CASE_VERSION = "wonderorbit-learning-cases-v1"
RUBRIC_VERSION = "wonderorbit-learning-quality-v1"
SUITE_HASH = "8d390e8d4425b9849351a11ddd82916899efeea52a5368887627b2297ea96a4f"
LIVE_IDS = ("CASE-01", "CASE-02", "CASE-04")
DIMENSIONS = (
    "evidence_faithfulness",
    "qualifier_preservation",
    "relevance",
    "learning_value",
    "uncertainty",
    "follow_up_value",
    "refusal_appropriateness",
)
FAILURES = {
    "invalid_tool_call",
    "invalid_model_output",
    "timeout",
    "rate_limit",
    "model_unavailable",
    "runner_error",
    "request_budget_exceeded",
}
SOURCES = (
    "backend/app/model_adapter.py",
    "backend/app/schemas.py",
    "backend/app/learning.py",
    "backend/app/rules.py",
    "backend/app/retrieval.py",
    "evals/check_learning_quality.py",
    "evals/collect_learning_quality.py",
    "evals/run_live.py",
    "evals/LEARNING_QUALITY_RUBRIC.md",
)


def digest(path, *, normalize=False):
    data = path.read_bytes()
    return hashlib.sha256(data.replace(b"\r\n", b"\n") if normalize else data).hexdigest()


def same(left, right):
    # JSON equality also distinguishes False/0, integers/floats and missing/null.
    return json.dumps(left, sort_keys=True, ensure_ascii=False, allow_nan=False) == json.dumps(
        right, sort_keys=True, ensure_ascii=False, allow_nan=False
    )


def suite():
    path = ROOT / "evals/learning_quality_cases.json"
    if digest(path, normalize=True) != SUITE_HASH:
        raise ValueError("fixed_suite_changed")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["version"] != CASE_VERSION or data["rubric_version"] != RUBRIC_VERSION:
        raise ValueError("suite_version")
    return data


def context(case):
    return {
        "request": AgentRequest.model_validate(case["input"]).model_dump(mode="json"),
        "stars": deepcopy(case["retrieved_stars"]),
        "preferences": Preferences.model_validate(case["preferences"]).model_dump(mode="json"),
        "id_map": deepcopy(case["id_map"]),
    }


def provenance(mode):
    return {
        "observation_layer": "adapter_dto",
        "workflow": "not_executed",
        "approval": "not_observed",
        "database": "not_accessed",
        "suite_sha256": SUITE_HASH,
        "suite_hash_normalization": "crlf-to-lf",
        "source_hashes": {p: digest(ROOT / p) for p in SOURCES},
        "model_config": {
            "mode": mode,
            "provider": "bailian" if mode == "live" else mode,
            "model": "qwen3.8-flash" if mode == "live" else mode,
            "sdk_retries": 0,
            "max_requests": 3,
            "max_output_tokens": None,
            "timeout_seconds": None,
            "enable_thinking": False,
        },
    }


def empty_batch(mode="fake"):
    if mode not in {"fake", "mock", "live"}:
        raise ValueError("mode")
    return {
        "format_version": "learning-captures-v2",
        "case_version": CASE_VERSION,
        "rubric_version": RUBRIC_VERSION,
        "public_data": mode != "live",
        "mode": mode,
        "provenance": provenance(mode),
        "results": [
            {
                "case_id": c["case_id"],
                "context": context(c),
                "status": "not_run",
                "raw_output": None,
                "validated_output": None,
                "gate": None,
                "failure_type": None,
                "usage": "unknown",
                "elapsed_ms": None,
                "manual": {},
            }
            for c in suite()["cases"]
        ],
    }


def observe(request, raw, *, format_version="learning-captures-v2"):
    if format_version not in {"learning-captures-v1", "learning-captures-v2"}:
        raise ValueError("format_version")
    resolve = format_version == "learning-captures-v2"
    dto = ProposalResult.model_validate(raw)
    validated = validate_learning_result(
        request, dto.model_copy(deep=True), resolve_offsets=resolve
    ).model_dump(mode="json")
    card = dto.learning_card
    source = request.learning_source
    offsets = resolve_learning_offsets(source, card) if resolve and source and card else None
    if offsets and offsets["status"] != "rejected":
        card = card.model_copy(
            update={"quote_start": offsets["resolved_start"], "quote_end": offsets["resolved_end"]}
        )
    gate = {
        "exact_quote": None
        if card is None
        else (
            card.quote_start < card.quote_end <= len(source.text)
            and source.text[card.quote_start : card.quote_end] == card.evidence_quote
            and bool(card.evidence_quote.strip())
        ),
        "metadata_match": None
        if card is None
        else (
            card.source_kind == "user_supplied_unverified"
            and card.source_label == source.label
            and card.source_url == source.url
        ),
        "card_retained": validated["learning_card"] is not None,
        "proposals_removed": len(dto.proposals) - len(validated["proposals"]),
        "reason": "retained"
        if validated["learning_card"]
        else "model_no_card"
        if card is None
        else "source_gate_rejected",
        "system_questions": validated["questions"],
    }
    if resolve:
        gate["offset_resolution"] = offsets
    return validated, gate


def model_payload(inputs):
    request, pref = inputs["request"], inputs["preferences"]
    # Fixed suite has no constraints. Mirror the current proposals payload, not star_details.
    budgets = [b for b in (request["budget"], pref["max_budget"]) if b is not None]
    return {
        "request": inputs["request"],
        "stars": inputs["stars"],
        "preferences": pref,
        "effective_limits": {
            "minutes": min(request["available_minutes"] or pref["max_minutes"], pref["max_minutes"]),
            "budget": min(budgets) if budgets else None,
            "energy": "low",
        },
        "constraint_template": None,
    }


class Rating(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: StrictInt | str = "not_rated"
    note: str = "尚未人工评价"
    reviewer: str | None = None
    reviewed_at: str | None = None
    source: str | None = None

    @model_validator(mode="after")
    def valid(self):
        if self.score not in (0, 1, 2, "not_rated"):
            raise ValueError("rating_score")
        if self.score != "not_rated":
            from datetime import date

            if not all(
                isinstance(v, str) and v.strip()
                for v in (self.note, self.reviewer, self.reviewed_at, self.source)
            ):
                raise ValueError("human_rating_provenance_required")
            date.fromisoformat(self.reviewed_at)
        return self


def evaluate(data):
    if not isinstance(data, dict):
        raise ValueError("envelope_object_required")
    if (
        data.get("format_version") not in {"learning-captures-v1", "learning-captures-v2"}
        or data.get("case_version") != CASE_VERSION
        or data.get("rubric_version") != RUBRIC_VERSION
        or data.get("mode") not in {"fake", "mock", "live"}
        or type(data.get("public_data")) is not bool
    ):
        raise ValueError("envelope")
    mode = data["mode"]
    p = data["provenance"]
    if not isinstance(p, dict):
        raise ValueError("provenance_object_required")
    expected = provenance(mode)
    for key in expected.keys() - {"source_hashes", "model_config"}:
        if not same(p.get(key), expected[key]):
            raise ValueError("observation_or_suite_changed")
    hashes = p["source_hashes"]
    if (
        not isinstance(hashes, dict)
        or set(hashes) != set(SOURCES)
        or any(
            not isinstance(h, str) or len(h) != 64 or any(c not in "0123456789abcdef" for c in h)
            for h in hashes.values()
        )
    ):
        raise ValueError("source_hashes")
    config = p["model_config"]
    if not isinstance(config, dict):
        raise ValueError("model_config_object_required")
    for key in expected["model_config"].keys() - {"max_output_tokens", "timeout_seconds"}:
        if not same(config.get(key), expected["model_config"][key]):
            raise ValueError("model_config")
    if mode == "live" and not (
        type(config.get("max_output_tokens")) is int
        and 256 <= config["max_output_tokens"] <= 8192
        and type(config.get("timeout_seconds")) in {int, float}
        and 0 < config["timeout_seconds"] <= 300
    ):
        raise ValueError("model_limits")
    cases = suite()["cases"]
    rows = data["results"]
    if not isinstance(rows, list) or [r["case_id"] for r in rows] != [c["case_id"] for c in cases]:
        raise ValueError("fixed_cases_required")
    report = []
    for row, case in zip(rows, cases, strict=True):
        if not same(row["context"], context(case)):
            raise ValueError("context_changed")
        status = row["status"]
        if status not in {"executed", "failed", "attempted_unknown", "not_run"}:
            raise ValueError("execution_status")
        if mode == "live" and status != "not_run" and row["case_id"] not in LIVE_IDS:
            raise ValueError("live_case_not_selected")
        if (
            mode == "live"
            and status != "not_run"
            and not same(row.get("model_payload"), model_payload(row["context"]))
        ):
            raise ValueError("actual_model_payload_changed")
        if row["usage"] != "unknown" and not (
            isinstance(row["usage"], dict)
            and bool(row["usage"])
            and set(row["usage"]) <= {"input_tokens", "output_tokens", "total_tokens"}
            and all(type(v) is int and v >= 0 for v in row["usage"].values())
        ):
            raise ValueError("usage")
        elapsed = row["elapsed_ms"]
        if elapsed is not None and (type(elapsed) is not int or elapsed < 0):
            raise ValueError("elapsed")
        checks = {}
        raw = row["raw_output"]
        if status == "executed":
            if raw is None or row["failure_type"] is not None or elapsed is None:
                raise ValueError("executed_without_dto")
            validated, gate = observe(
                AgentRequest.model_validate(case["input"]), raw, format_version=data["format_version"]
            )
            if not same(row["validated_output"], validated) or not same(row["gate"], gate):
                raise ValueError("gate_evidence_changed")
            allowed = set(case["id_map"])
            checks = {
                "schema": "passed",
                "gate_replay": "passed",
                "exact_quote": "not_rated"
                if gate["exact_quote"] is None
                else "passed"
                if gate["exact_quote"]
                else "failed",
                "source_metadata": "not_rated"
                if gate["metadata_match"] is None
                else "passed"
                if gate["metadata_match"]
                else "failed",
                "star_references": "passed"
                if all(set(x["based_on_star_ids"]) <= allowed for x in raw["proposals"])
                else "failed",
            }
        else:
            if raw is not None and (
                status == "attempted_unknown"
                or (status == "failed" and row["failure_type"] == "runner_error")
            ):
                ProposalResult.model_validate(raw)
                checks["raw_schema"] = "passed"
            elif raw is not None:
                raise ValueError("no_dto_observed")
            if row["validated_output"] is not None or row["gate"] is not None:
                raise ValueError("no_gate_observed")
            if status == "failed" and row["failure_type"] not in FAILURES:
                raise ValueError("failure_type")
            if status != "failed" and row["failure_type"] is not None:
                raise ValueError("failure_type")
            if status == "not_run" and (elapsed is not None or row["usage"] != "unknown"):
                raise ValueError("not_run_has_observation")
            checks["output"] = "failed" if status == "failed" else "not_run"
        manual = row["manual"]
        if not isinstance(manual, dict) or set(manual) - set(DIMENSIONS):
            raise ValueError("manual_dimensions")
        ratings = {d: Rating.model_validate(manual.get(d, {})).model_dump() for d in DIMENSIONS}
        if status != "executed" and any(r["score"] != "not_rated" for r in ratings.values()):
            raise ValueError("no_output_to_rate")
        report.append({**deepcopy(row), "checks": checks, "manual": ratings})
    return {
        "capture_format_version": data["format_version"],
        "case_version": CASE_VERSION,
        "rubric_version": RUBRIC_VERSION,
        "evidence_type": {
            "fake": "tool_self_test",
            "mock": "application_mock",
            "live": "supplied_live_output_unverified",
        }[mode],
        "provenance": deepcopy(p),
        "source_matches_current": hashes == expected["source_hashes"],
        "deterministic": {
            s: sum(v == s for r in report for v in r["checks"].values())
            for s in ("passed", "failed", "not_run", "not_rated")
        },
        "manual": {
            "rated": sum(v["score"] != "not_rated" for r in report for v in r["manual"].values()),
            "not_rated": sum(v["score"] == "not_rated" for r in report for v in r["manual"].values()),
        },
        "cases": report,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.results:
            # Reuse existing public-only path policy; never auto-export private captures.
            sys.path.insert(0, str(ROOT / "evals"))
            from check_results import load_public_json

            data = load_public_json(args.results)
            if not isinstance(data, dict) or data.get("public_data") is not True:
                raise ValueError("public_review_required")
            report = evaluate(data)
        else:
            report = evaluate(empty_batch())
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
        return int(report["deterministic"]["failed"] > 0)
    except (ValueError, KeyError, TypeError, OSError):
        print('{"error":"invalid_learning_evidence"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
