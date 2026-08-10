"""
KNOWLEDGE FACTORY V2 — PHASE 6H
Independent Factual Approval Queue Builder

This phase does NOT auto-approve facts.

It converts Phase 6G REVIEW_PASS_CANDIDATE records into a controlled,
auditable approval queue. Every item remains NOT_READY until an explicit
independent reviewer decision is supplied.

Allowed reviewer decisions:
- APPROVED_FOR_EVIDENCE_READY
- MANUAL_REVIEW_REQUIRED
- REJECTED
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_REVIEW_GATE = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "review_gate"
    / "biology_semantic_factual_review_gate.json"
)

DEFAULT_EVIDENCE_RECORDS = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "evidence_records"
    / "biology_source_backed_evidence.json"
)

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "factual_approval"
    / "biology_independent_factual_approval_queue.json"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_record_lookup(evidence_payload):
    return {
        item["record_id"]: item
        for item in evidence_payload.get("records", [])
    }


def build_queue(review_gate, evidence_payload):
    evidence_lookup = build_record_lookup(evidence_payload)
    items = []

    for review in review_gate.get("reviews", []):
        if review.get("review_gate_status") != "REVIEW_PASS_CANDIDATE":
            continue

        record_id = review["record_id"]
        evidence = evidence_lookup.get(record_id)
        if evidence is None:
            raise ValueError(
                f"{record_id}: evidence record missing"
            )

        items.append(
            {
                "record_id": record_id,
                "outcome_id": review["outcome_id"],
                "grade": review["grade"],
                "theme_number": review["theme_number"],
                "theme_name": review["theme_name"],
                "outcome_title": review["outcome_title"],
                "source": evidence["source"],
                "evidence_text": evidence["evidence_text"],
                "pre_review": {
                    "status": review["review_gate_status"],
                    "gate_checks": review["gate_checks"],
                    "matched_title_tokens": review.get(
                        "matched_title_tokens",
                        [],
                    ),
                },
                "approval": {
                    "status": "PENDING",
                    "reviewer_type": None,
                    "reviewer_id": None,
                    "factual_support": None,
                    "outcome_support": None,
                    "source_consistency": None,
                    "rationale": None,
                },
                "evidence_status": "NOT_READY",
                "student_visible": False,
                "independent_reviewer_required": True,
            }
        )

    return {
        "version": "1.0",
        "kind": "independent_factual_approval_queue",
        "subject": "Biyoloji",
        "approval_semantics": (
            "No automatic factual approval. A separate reviewer must make "
            "an explicit decision for every item."
        ),
        "allowed_decisions": [
            "APPROVED_FOR_EVIDENCE_READY",
            "MANUAL_REVIEW_REQUIRED",
            "REJECTED",
        ],
        "queue_count": len(items),
        "items": items,
    }


def validate_queue(payload):
    errors = []

    if payload.get("subject") != "Biyoloji":
        errors.append("subject must be Biyoloji")

    items = payload.get("items", [])
    if payload.get("queue_count") != len(items):
        errors.append("queue_count mismatch")

    ids = [item.get("record_id") for item in items]
    if len(ids) != len(set(ids)):
        errors.append("duplicate record ids")

    for item in items:
        approval = item.get("approval", {})

        if approval.get("status") != "PENDING":
            errors.append(
                f"{item.get('record_id')}: initial approval must be PENDING"
            )

        if item.get("evidence_status") != "NOT_READY":
            errors.append(
                f"{item.get('record_id')}: evidence_status must be NOT_READY"
            )

        if item.get("student_visible") is not False:
            errors.append(
                f"{item.get('record_id')}: student_visible must be false"
            )

        if item.get("independent_reviewer_required") is not True:
            errors.append(
                f"{item.get('record_id')}: independent reviewer must remain required"
            )

        if not item.get("evidence_text", "").strip():
            errors.append(
                f"{item.get('record_id')}: evidence_text missing"
            )

        source = item.get("source", {})
        for key in (
            "authority",
            "package_id",
            "page",
            "source_anchor",
            "html_path",
            "image_path",
            "text_sha256",
        ):
            if not source.get(key):
                errors.append(
                    f"{item.get('record_id')}: missing source field {key}"
                )

    return errors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--review-gate",
        type=Path,
        default=DEFAULT_REVIEW_GATE,
    )
    parser.add_argument(
        "--evidence-records",
        type=Path,
        default=DEFAULT_EVIDENCE_RECORDS,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    return parser.parse_args()


def main():
    args = parse_args()

    review_gate = load_json(args.review_gate)
    evidence_payload = load_json(args.evidence_records)

    payload = build_queue(review_gate, evidence_payload)
    errors = validate_queue(payload)

    print("=" * 72)
    print("KNOWLEDGE FACTORY V2 — PHASE 6H INDEPENDENT FACTUAL APPROVAL QUEUE")
    print("=" * 72)
    print(f"Approval queue items : {payload['queue_count']}")

    if errors:
        print("APPROVAL QUEUE VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    write_json(args.output, payload)

    print("APPROVAL QUEUE VALIDATION: PASS")
    print("Approval status      : PENDING")
    print("Evidence status      : NOT_READY")
    print("Student visible      : False")
    print("Independent reviewer : REQUIRED")
    print(f"OUTPUT               | {args.output}")


if __name__ == "__main__":
    main()
