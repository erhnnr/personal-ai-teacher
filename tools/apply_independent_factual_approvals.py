"""
KNOWLEDGE FACTORY V2 — PHASE 6H
Independent Factual Approval Decision Applier

Consumes:
1) the Phase 6H approval queue
2) an explicit independent reviewer decision manifest

It never invents decisions. Only explicit, complete reviewer decisions
may promote an item to APPROVED_FOR_EVIDENCE_READY candidate status.

Even after approval, final evidence_status remains NOT_READY here.
Actual EVIDENCE_READY promotion belongs to the next release-safe phase.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_QUEUE = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "factual_approval"
    / "biology_independent_factual_approval_queue.json"
)

DEFAULT_DECISIONS = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "factual_approval"
    / "biology_independent_factual_decisions.json"
)

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "factual_approval"
    / "biology_independent_factual_approval_results.json"
)

ALLOWED_DECISIONS = {
    "APPROVED_FOR_EVIDENCE_READY",
    "MANUAL_REVIEW_REQUIRED",
    "REJECTED",
}

ALLOWED_REVIEWER_TYPES = {
    "HUMAN",
    "EXTERNAL_LLM",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def validate_decision(decision):
    errors = []
    record_id = decision.get("record_id", "<unknown>")

    if decision.get("status") not in ALLOWED_DECISIONS:
        errors.append(f"{record_id}: invalid decision status")

    if decision.get("reviewer_type") not in ALLOWED_REVIEWER_TYPES:
        errors.append(f"{record_id}: invalid reviewer_type")

    if not decision.get("reviewer_id"):
        errors.append(f"{record_id}: reviewer_id required")

    if decision.get("factual_support") not in (True, False):
        errors.append(f"{record_id}: factual_support must be boolean")

    if decision.get("outcome_support") not in (True, False):
        errors.append(f"{record_id}: outcome_support must be boolean")

    if decision.get("source_consistency") not in (True, False):
        errors.append(f"{record_id}: source_consistency must be boolean")

    if not str(decision.get("rationale") or "").strip():
        errors.append(f"{record_id}: rationale required")

    if decision.get("status") == "APPROVED_FOR_EVIDENCE_READY":
        if not all(
            (
                decision.get("factual_support") is True,
                decision.get("outcome_support") is True,
                decision.get("source_consistency") is True,
            )
        ):
            errors.append(
                f"{record_id}: approval requires all review booleans true"
            )

    return errors


def apply_decisions(queue, decision_manifest):
    queue_items = {
        item["record_id"]: item
        for item in queue.get("items", [])
    }

    decisions = decision_manifest.get("decisions", [])
    decision_ids = [item.get("record_id") for item in decisions]

    if len(decision_ids) != len(set(decision_ids)):
        raise ValueError("duplicate decision record ids")

    unknown = [
        record_id
        for record_id in decision_ids
        if record_id not in queue_items
    ]
    if unknown:
        raise ValueError(
            "decisions contain unknown record ids: "
            + ", ".join(unknown)
        )

    results = []
    counts = Counter()

    decision_lookup = {
        item["record_id"]: item
        for item in decisions
    }

    for record_id, queue_item in queue_items.items():
        decision = decision_lookup.get(record_id)

        if decision is None:
            status = "PENDING"
            applied = {
                "status": status,
                "reviewer_type": None,
                "reviewer_id": None,
                "factual_support": None,
                "outcome_support": None,
                "source_consistency": None,
                "rationale": None,
            }
        else:
            errors = validate_decision(decision)
            if errors:
                raise ValueError("; ".join(errors))

            status = decision["status"]
            applied = {
                "status": status,
                "reviewer_type": decision["reviewer_type"],
                "reviewer_id": decision["reviewer_id"],
                "factual_support": decision["factual_support"],
                "outcome_support": decision["outcome_support"],
                "source_consistency": decision["source_consistency"],
                "rationale": decision["rationale"],
            }

        counts[status] += 1

        results.append(
            {
                "record_id": record_id,
                "outcome_id": queue_item["outcome_id"],
                "outcome_title": queue_item["outcome_title"],
                "source": queue_item["source"],
                "approval": applied,
                "evidence_status": "NOT_READY",
                "student_visible": False,
            }
        )

    return {
        "version": "1.0",
        "kind": "independent_factual_approval_results",
        "subject": queue.get("subject"),
        "result_count": len(results),
        "status_counts": dict(sorted(counts.items())),
        "results": results,
    }


def validate_results(payload):
    errors = []

    if payload.get("subject") != "Biyoloji":
        errors.append("subject must be Biyoloji")

    results = payload.get("results", [])
    if payload.get("result_count") != len(results):
        errors.append("result_count mismatch")

    for item in results:
        if item.get("evidence_status") != "NOT_READY":
            errors.append(
                f"{item.get('record_id')}: evidence_status must remain NOT_READY"
            )
        if item.get("student_visible") is not False:
            errors.append(
                f"{item.get('record_id')}: student_visible must be false"
            )

    return errors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main():
    args = parse_args()

    queue = load_json(args.queue)
    decisions = load_json(args.decisions)

    payload = apply_decisions(queue, decisions)
    errors = validate_results(payload)

    print("=" * 72)
    print("KNOWLEDGE FACTORY V2 — PHASE 6H FACTUAL APPROVAL RESULTS")
    print("=" * 72)
    print(f"Result records       : {payload['result_count']}")

    for status, count in payload["status_counts"].items():
        print(f"{status:<28}: {count}")

    if errors:
        print("APPROVAL RESULT VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    write_json(args.output, payload)

    print("APPROVAL RESULT VALIDATION: PASS")
    print("Evidence status      : NOT_READY")
    print("Student visible      : False")
    print(f"OUTPUT               | {args.output}")


if __name__ == "__main__":
    main()
