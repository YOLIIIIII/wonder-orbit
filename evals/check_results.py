"""Offline public-result checker. Imports DTOs/constants only; stdout report, no application runtime."""

import argparse
from copy import deepcopy
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.rules import SUPPORTED_CONSTRAINTS, TEXT_STEPS  # noqa: E402
from app.schemas import AgentRequest, DraftResult, Preferences, ProposalResult  # noqa: E402

VERSION = "wonderorbit-quality-v1"
METRICS = {
    "collect": ["topic", "title", "category", "tags", "description", "motivation", "clarification"],
    "explore": ["relevance", "feasibility", "steps", "uncertainty", "exploration_value"],
}


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Rating(Record):
    score: Literal[0, 1, 2, "not_rated"] = "not_rated"
    note: str = Field(default="", max_length=1000)

    @field_validator("score", mode="before")
    @classmethod
    def integer_score(cls, value):
        if type(value) is not int and value != "not_rated":
            raise ValueError("integer_score_required")
        return value


class ApprovalEvidence(Record):
    # Explicit observations supplied by a test harness, never inferred from model text.
    before: int = Field(ge=0)
    after_generation: int = Field(ge=0)
    after_decision: int = Field(ge=0)
    after_repeat: int = Field(ge=0)
    decision: Literal["approved", "rejected", "none"]
    authorization: Literal["user_api", "isolated_test_simulation", "none"]


class Capture(Record):
    # Explicitly reviewed public data only. Never load a runner report or DB here.
    observation_layer: Literal["adapter_dto", "workflow_dto"]
    generation_versions: dict[str, str]
    input: dict
    preferences: dict = Field(default_factory=dict)
    retrieved_stars: list[dict] = Field(default_factory=list)
    id_map: dict[str, str] = Field(default_factory=dict)  # runtime ID -> public fixture ID
    raw_output: dict | None = None


class Result(Record):
    case_id: str
    status: Literal["executed", "not_run"]
    output: dict | None = None
    manual: dict[str, Rating] = Field(default_factory=dict)
    approval: ApprovalEvidence | None = None
    capture: Capture | None = None


class Results(Record):
    format_version: Literal["offline-results-v1"]
    public_data: Literal[True]
    case_version: str
    rubric_version: str
    prompt_version: str = "not_recorded"
    workflow_version: str = "not_recorded"
    retrieval_version: str = "not_recorded"
    model: str = "unknown"
    mode: Literal["fake", "mock", "live"]
    results: list[Result]


def load_public_json(path):
    path = Path(path).resolve()
    if path.suffix.lower() != ".json" or any(
        part.lower() in {".cache", ".git"} or part.lower().startswith(".env") for part in path.parts
    ):
        raise ValueError("public_json_path_required")
    # No discovery, includes, environment loading, or fallback paths.
    return json.loads(
        path.read_text(encoding="utf-8"),
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non_finite_json")),
    )


def load_suite():
    return json.loads(Path(__file__).with_name("quality_cases.json").read_text(encoding="utf-8"))


def normalize_capture(capture, case, batch):
    versions = {k: getattr(batch, k) for k in ("prompt_version", "workflow_version", "retrieval_version")}
    if capture.generation_versions != versions or any(
        not v.strip() or v.strip().lower() in {"unknown", "not_recorded"} for v in versions.values()
    ):
        raise ValueError("capture_version_mismatch")
    AgentRequest.model_validate(capture.input, strict=True)
    Preferences.model_validate(capture.preferences, strict=True)
    # Exact case context, not title-only matching or an inference from model text.
    if capture.input != case["input"] or capture.preferences != case.get("preferences", {}):
        raise ValueError("capture_context_mismatch")
    expected = {star["star_id"]: star for star in case.get("retrieved_stars", [])}
    mapping = capture.id_map
    if (
        len(set(mapping.values())) != len(mapping)
        or set(mapping.values()) != set(expected)
        or any(not key.strip() for key in mapping)
    ):
        raise ValueError("capture_mapping_not_bijective")
    actual = {}
    for star in capture.retrieved_stars:
        runtime_id = star.get("star_id")
        if not isinstance(runtime_id, str) or runtime_id not in mapping or runtime_id in actual:
            raise ValueError("capture_retrieval_mismatch")
        public_id = mapping[runtime_id]
        if {**star, "star_id": public_id} != expected[public_id]:
            raise ValueError("capture_star_content_mismatch")
        actual[runtime_id] = star
    if set(actual) != set(mapping):
        raise ValueError("capture_retrieval_missing")
    output = deepcopy(capture.raw_output)
    if case["input"]["request_type"] == "explore" and output is not None:
        try:
            ProposalResult.model_validate(output, strict=True)
        except ValidationError:
            # Keep malformed DTO unchanged so the existing checker reports schema failure.
            return output
        for proposal in output["proposals"]:
            ids = proposal["based_on_star_ids"]
            if any(star_id not in mapping for star_id in ids):
                raise ValueError("capture_output_source_mismatch")
            proposal["based_on_star_ids"] = [mapping[star_id] for star_id in ids]
    return output


def prepare_captures(data):
    # Produces the existing result envelope plus lossless, revalidated provenance.
    if not isinstance(data, dict) or data.get("format_version") != "public-captures-v1":
        raise ValueError("capture_format_required")
    batch = Results.model_validate({**data, "format_version": "offline-results-v1"})
    suite = load_suite()
    if batch.case_version != suite["version"] or batch.rubric_version != VERSION:
        raise ValueError("version_mismatch")
    cases = {case["id"]: case for case in suite["cases"]}
    ids = [result.case_id for result in batch.results]
    if len(ids) != len(set(ids)) or set(ids) - cases.keys():
        raise ValueError("duplicate_or_unknown_case")
    for result in batch.results:
        if result.output is not None:
            raise ValueError("capture_cannot_supply_normalized_output")
        if result.status == "executed":
            if result.capture is None:
                raise ValueError("capture_required")
            result.output = normalize_capture(result.capture, cases[result.case_id], batch)
        elif result.capture is not None:
            raise ValueError("not_run_has_capture")
    prepared = batch.model_dump(mode="json", exclude_none=True)
    # Reuse all existing manual/approval/envelope validation without duplicating the rubric.
    evaluate(prepared)
    return prepared


def evaluate(data):
    batch = Results.model_validate(data)
    suite = load_suite()
    cases = {case["id"]: case for case in suite["cases"]}
    if batch.case_version != suite["version"] or batch.rubric_version != VERSION:
        raise ValueError("version_mismatch")
    ids = [r.case_id for r in batch.results]
    if len(ids) != len(set(ids)) or set(ids) - cases.keys():
        raise ValueError("duplicate_or_unknown_case")
    rows = []
    for case_id, case in cases.items():
        result = next((r for r in batch.results if r.case_id == case_id), None)
        kind = case["input"]["request_type"]
        checks = []
        if result and result.capture is not None:
            if result.status != "executed" or result.output != normalize_capture(result.capture, case, batch):
                raise ValueError("capture_output_changed")

        def check(name, ok=None):
            checks.append(
                {"name": name, "status": "not_rated" if ok is None else "passed" if ok else "failed"}
            )

        manual = {metric: Rating().model_dump() for metric in METRICS[kind]}
        if result:
            if result.manual.keys() - manual.keys():
                raise ValueError("unknown_manual_metric")
            for metric, rating in result.manual.items():
                if isinstance(rating.score, bool) or (
                    rating.score != "not_rated" and not rating.note.strip()
                ):
                    raise ValueError("rating_requires_score_and_note")
                manual[metric] = rating.model_dump()
        if not result or result.status == "not_run":
            if result and (result.output is not None or result.approval or result.manual or result.capture):
                raise ValueError("not_run_has_evidence")
            checks.append({"name": "output", "status": "not_run"})
        elif result.output is None:
            check("output_present", False)
        else:
            request = AgentRequest.model_validate(case["input"])
            try:
                output = (DraftResult if kind == "collect" else ProposalResult).model_validate(
                    result.output, strict=True
                )
            except ValidationError:
                check("output_schema", False)
            else:
                check("output_schema", True)
                if kind == "collect":
                    draft = output.draft
                    check(
                        "original_and_source",
                        draft.original_text == request.text
                        and draft.source_type == request.source_type
                        and draft.source_reference == request.source_reference,
                    )
                    for field, expected in case["expected_fields"].items():
                        check(field, getattr(draft, field) == expected)
                    check(
                        "reason_missing_consistency",
                        ("interest_reason" in output.missing_fields) == (draft.interest_reason is None),
                    )
                else:
                    pref = Preferences.model_validate(case.get("preferences", {}))
                    proposals = output.proposals
                    check(
                        "proposal_policy",
                        bool(proposals)
                        if case["expect_proposal"]
                        else not proposals and bool(output.questions),
                    )
                    for i, proposal in enumerate(proposals):
                        prefix = f"proposal_{i}:"
                        check(
                            prefix + "retrieved_star_ids",
                            set(proposal.based_on_star_ids).issubset(case["retrieved_star_ids"]),
                        )
                        check(
                            prefix + "time",
                            pref.min_minutes
                            <= proposal.estimated_minutes
                            <= min(request.available_minutes or pref.max_minutes, pref.max_minutes),
                        )
                        budgets = [v for v in [request.budget, pref.max_budget] if v is not None]
                        check(
                            prefix + "budget",
                            not budgets
                            or proposal.estimated_budget is not None
                            and proposal.estimated_budget <= min(budgets),
                        )
                        levels = {"low": 1, "medium": 2, "high": 3}
                        check(
                            prefix + "energy",
                            all(
                                levels[proposal.energy_level] <= levels[e]
                                for e in [request.energy_level, pref.energy_level]
                                if e
                            ),
                        )
                        check(
                            prefix + "constraints",
                            not pref.constraints
                            or all(c in SUPPORTED_CONSTRAINTS for c in pref.constraints)
                            and proposal.steps == TEXT_STEPS
                            and proposal.estimated_budget == 0,
                        )
            if result.approval:
                a = result.approval
                delta = 1 if a.decision == "approved" else 0
                check(
                    "approval_boundary",
                    a.after_generation == a.before
                    and a.after_decision == a.before + delta
                    and a.after_repeat == a.after_decision
                    and (not delta or a.authorization != "none"),
                )
            else:
                check("approval_boundary")
        rows.append(
            {
                "case_id": case_id,
                "checks": checks,
                "manual": manual,
                "capture": result.capture.model_dump(mode="json") if result and result.capture else None,
            }
        )
    counts = Counter(c["status"] for row in rows for c in row["checks"])
    return {
        "report_version": "offline-report-v1",
        "metadata": batch.model_dump(exclude={"results"}),
        "evidence_type": {
            "fake": "tool_self_test",
            "mock": "application_mock",
            "live": "supplied_live_output_unverified",
        }[batch.mode],
        "provenance": "caller_supplied; no provider or database verification",
        "deterministic": {s: counts[s] for s in ["passed", "failed", "not_run", "not_rated"]},
        "manual": {
            "rated": sum(r["score"] != "not_rated" for row in rows for r in row["manual"].values()),
            "not_rated": sum(r["score"] == "not_rated" for row in rows for r in row["manual"].values()),
        },
        "cases": rows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--results", type=Path, help="Explicit public JSON; never a private cache")
    group.add_argument(
        "--prepare-captures", type=Path, help="Reviewed public captures -> result JSON on stdout"
    )
    args = parser.parse_args(argv)
    try:
        if args.prepare_captures:
            prepared = prepare_captures(load_public_json(args.prepare_captures))
            print(json.dumps(prepared, ensure_ascii=False, indent=2))
            return 0  # Conversion success; run --results separately to assess the output.
        report = evaluate(load_public_json(args.results))
    except (ValueError, OSError):
        # Do not echo input, raw validation errors, filesystem paths, or private content.
        print(
            json.dumps(
                {
                    "report_version": "offline-report-v1",
                    "error": "invalid_input_or_version",
                    "deterministic": {"passed": 0, "failed": 1, "not_run": 0, "not_rated": 0},
                }
            )
        )
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["deterministic"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
