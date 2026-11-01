"""Offline public-result checker. Imports DTOs/constants only; stdout report, no application runtime."""

import argparse
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


class Result(Record):
    case_id: str
    status: Literal["executed", "not_run"]
    output: dict | None = None
    manual: dict[str, Rating] = Field(default_factory=dict)
    approval: ApprovalEvidence | None = None


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


def evaluate(data):
    batch = Results.model_validate(data)
    suite = json.loads(Path(__file__).with_name("quality_cases.json").read_text(encoding="utf-8"))
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
            if result and (result.output is not None or result.approval or result.manual):
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
        rows.append({"case_id": case_id, "checks": checks, "manual": manual})
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
    parser.add_argument(
        "--results", type=Path, required=True, help="Explicit public JSON; never a private cache"
    )
    args = parser.parse_args(argv)
    try:
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
