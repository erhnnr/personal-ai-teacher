"""
KNOWLEDGE FACTORY V2 — PHASE 6H.1
Independent Reviewer Packet Builder

Creates a compact reviewer-facing packet from the Phase 6H factual
approval queue. It does NOT create decisions and cannot approve evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_QUEUE = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "factual_approval"
    / "biology_independent_factual_approval_queue.json"
)

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "factual_approval"
    / "biology_independent_factual_reviewer_packet.json"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_packet(queue):
    items = []

    for item in queue.get("items", []):
        source = item["source"]
        pre = item["pre_review"]

        items.append(
            {
                "record_id": item["record_id"],
                "outcome_id": item["outcome_id"],
                "grade": item["grade"],
                "theme_name": item["theme_name"],
                "outcome_title": item["outcome_title"],
                "source_package": source["package_id"],
                "source_page": source["page"],
                "source_anchor": source["source_anchor"],
                "text_sha256": source["text_sha256"],
                "matched_title_tokens": pre.get(
                    "matched_title_tokens",
                    [],
                ),
                "evidence_text": item["evidence_text"],
                "review_questions": {
                    "factual_support": (
                        "Is the factual content in the evidence text correct "
                        "within the official source context?"
                    ),
                    "outcome_support": (
                        "Does this evidence text directly and sufficiently "
                        "support the stated curriculum outcome?"
                    ),
                    "source_consistency": (
                        "Is the evidence text consistent with the cited "
                        "official source page and provenance?"
                    ),
                },
                "required_decision_fields": {
                    "status": (
                        "APPROVED_FOR_EVIDENCE_READY | "
                        "MANUAL_REVIEW_REQUIRED | REJECTED"
                    ),
                    "reviewer_type": "HUMAN | EXTERNAL_LLM",
                    "reviewer_id": "required",
                    "factual_support": "boolean",
                    "outcome_support": "boolean",
                    "source_consistency": "boolean",
                    "rationale": "required",
                },
                "evidence_status": "NOT_READY",
                "student_visible": False,
            }
        )

    return {
        "version": "1.0",
        "kind": "independent_factual_reviewer_packet",
        "subject": queue.get("subject"),
        "packet_count": len(items),
        "instructions": (
            "Review each item independently. Do not approve solely because "
            "a prior deterministic gate passed. APPROVED_FOR_EVIDENCE_READY "
            "requires factual_support=true, outcome_support=true, and "
            "source_consistency=true."
        ),
        "items": items,
    }


def validate_packet(payload):
    errors = []

    if payload.get("subject") != "Biyoloji":
        errors.append("subject must be Biyoloji")

    items = payload.get("items", [])
    if payload.get("packet_count") != len(items):
        errors.append("packet_count mismatch")

    for item in items:
        if item.get("evidence_status") != "NOT_READY":
            errors.append(
                f"{item.get('record_id')}: evidence_status must be NOT_READY"
            )
        if item.get("student_visible") is not False:
            errors.append(
                f"{item.get('record_id')}: student_visible must be false"
            )
        if not item.get("evidence_text", "").strip():
            errors.append(
                f"{item.get('record_id')}: evidence_text missing"
            )

    return errors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main():
    args = parse_args()

    queue = load_json(args.queue)
    payload = build_packet(queue)
    errors = validate_packet(payload)

    print("=" * 72)
    print("KNOWLEDGE FACTORY V2 — PHASE 6H.1 INDEPENDENT REVIEWER PACKET")
    print("=" * 72)
    print(f"Reviewer packet items : {payload['packet_count']}")

    if errors:
        print("REVIEWER PACKET VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    write_json(args.output, payload)

    print("REVIEWER PACKET VALIDATION: PASS")
    print("Evidence status       : NOT_READY")
    print("Student visible       : False")
    print(f"OUTPUT                | {args.output}")


if __name__ == "__main__":
    main()
