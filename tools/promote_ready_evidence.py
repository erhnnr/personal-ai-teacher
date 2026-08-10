"""
KNOWLEDGE FACTORY V2 — PHASE 6I
Release-Safe Evidence Promotion Gate

Only independently approved records may be promoted from NOT_READY to READY.

Promotion requirements:
- approval.status == APPROVED_FOR_EVIDENCE_READY
- reviewer_type is explicitly allowed
- factual_support == True
- outcome_support == True
- source_consistency == True
- original source-backed evidence record still exists
- source authority is MEB
- provenance fields are present and unchanged
- evidence_text SHA-256 matches source.text_sha256
- approval-result source SHA-256 matches original source SHA-256

Safety:
- student_visible remains False
- rejected/manual/pending records can never be promoted
- this phase promotes evidence only; it does not create student teaching content
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_APPROVAL_RESULTS = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "factual_approval"
    / "biology_independent_factual_approval_results.json"
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
    / "promoted_evidence"
    / "biology_ready_evidence.json"
)

ALLOWED_REVIEWER_TYPES = {
    "HUMAN",
    "EXTERNAL_LLM",
}

REQUIRED_SOURCE_FIELDS = (
    "authority",
    "corpus_family",
    "package_id",
    "page",
    "source_anchor",
    "html_path",
    "image_path",
    "text_sha256",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def evidence_lookup(payload):
    return {
        item["record_id"]: item
        for item in payload.get("records", [])
    }


def source_provenance_complete(source):
    return all(source.get(field) not in (None, "") for field in REQUIRED_SOURCE_FIELDS)


def source_unchanged(result_source, original_source):
    for field in REQUIRED_SOURCE_FIELDS:
        if result_source.get(field) != original_source.get(field):
            return False
    return True


def evaluate_promotion(result, original):
    checks = {
        "approved_status": (
            result.get("approval", {}).get("status")
            == "APPROVED_FOR_EVIDENCE_READY"
        ),
        "allowed_reviewer_type": (
            result.get("approval", {}).get("reviewer_type")
            in ALLOWED_REVIEWER_TYPES
        ),
        "factual_support": (
            result.get("approval", {}).get("factual_support") is True
        ),
        "outcome_support": (
            result.get("approval", {}).get("outcome_support") is True
        ),
        "source_consistency": (
            result.get("approval", {}).get("source_consistency") is True
        ),
        "source_authority_meb": (
            original.get("source", {}).get("authority") == "MEB"
        ),
        "provenance_complete": source_provenance_complete(
            original.get("source", {})
        ),
        "source_unchanged": source_unchanged(
            result.get("source", {}),
            original.get("source", {}),
        ),
        "evidence_hash_matches_source": (
            sha256_text(original.get("evidence_text", ""))
            == original.get("source", {}).get("text_sha256")
        ),
        "original_evidence_not_student_visible": (
            original.get("student_visible") is False
        ),
    }

    return checks, all(checks.values())


def build_promoted_payload(approval_results, evidence_records):
    originals = evidence_lookup(evidence_records)
    promoted = []
    blocked = []
    status_counts = Counter()

    for result in approval_results.get("results", []):
        record_id = result["record_id"]
        original = originals.get(record_id)

        if original is None:
            blocked.append(
                {
                    "record_id": record_id,
                    "promotion_status": "BLOCKED",
                    "reason": "ORIGINAL_EVIDENCE_RECORD_MISSING",
                    "evidence_status": "NOT_READY",
                    "student_visible": False,
                }
            )
            status_counts["BLOCKED"] += 1
            continue

        checks, promotable = evaluate_promotion(result, original)

        if promotable:
            promoted.append(
                {
                    "record_id": record_id,
                    "outcome_id": original["outcome_id"],
                    "grade": original["grade"],
                    "theme_number": original["theme_number"],
                    "theme_name": original["theme_name"],
                    "outcome_title": original["outcome_title"],
                    "source": original["source"],
                    "verification": original.get("verification", {}),
                    "approval": result["approval"],
                    "promotion_checks": checks,
                    "evidence_text": original["evidence_text"],
                    "evidence_status": "READY",
                    "student_visible": False,
                    "promotion_policy": "RELEASE_SAFE_INDEPENDENT_APPROVAL_GATE",
                }
            )
            status_counts["READY"] += 1
        else:
            blocked.append(
                {
                    "record_id": record_id,
                    "approval_status": result.get("approval", {}).get("status"),
                    "promotion_status": "BLOCKED",
                    "promotion_checks": checks,
                    "evidence_status": "NOT_READY",
                    "student_visible": False,
                }
            )
            status_counts["BLOCKED"] += 1

    return {
        "version": "1.0",
        "kind": "release_safe_ready_evidence",
        "subject": "Biyoloji",
        "promotion_policy": (
            "Only independently approved records with intact provenance "
            "and exact evidence SHA-256 may become READY."
        ),
        "input_result_count": len(approval_results.get("results", [])),
        "ready_count": len(promoted),
        "blocked_count": len(blocked),
        "status_counts": dict(sorted(status_counts.items())),
        "records": promoted,
        "blocked": blocked,
        "student_visible": False,
    }


def validate_payload(payload):
    errors = []

    if payload.get("subject") != "Biyoloji":
        errors.append("subject must be Biyoloji")

    records = payload.get("records", [])
    blocked = payload.get("blocked", [])

    if payload.get("ready_count") != len(records):
        errors.append("ready_count mismatch")

    if payload.get("blocked_count") != len(blocked):
        errors.append("blocked_count mismatch")

    if payload.get("input_result_count") != len(records) + len(blocked):
        errors.append("input result accounting mismatch")

    if payload.get("student_visible") is not False:
        errors.append("top-level student_visible must be false")

    ids = [item.get("record_id") for item in records]
    if len(ids) != len(set(ids)):
        errors.append("duplicate READY record ids")

    for item in records:
        if item.get("evidence_status") != "READY":
            errors.append(
                f"{item.get('record_id')}: promoted evidence must be READY"
            )
        if item.get("student_visible") is not False:
            errors.append(
                f"{item.get('record_id')}: student_visible must remain false"
            )
        if (
            item.get("approval", {}).get("status")
            != "APPROVED_FOR_EVIDENCE_READY"
        ):
            errors.append(
                f"{item.get('record_id')}: READY without independent approval"
            )
        if not all(item.get("promotion_checks", {}).values()):
            errors.append(
                f"{item.get('record_id')}: READY with failed promotion check"
            )

    for item in blocked:
        if item.get("evidence_status") != "NOT_READY":
            errors.append(
                f"{item.get('record_id')}: blocked evidence must remain NOT_READY"
            )
        if item.get("student_visible") is not False:
            errors.append(
                f"{item.get('record_id')}: blocked evidence student_visible must be false"
            )

    return errors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--approval-results",
        type=Path,
        default=DEFAULT_APPROVAL_RESULTS,
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

    approval_results = load_json(args.approval_results)
    evidence_records = load_json(args.evidence_records)

    payload = build_promoted_payload(
        approval_results,
        evidence_records,
    )
    errors = validate_payload(payload)

    print("=" * 72)
    print("KNOWLEDGE FACTORY V2 — PHASE 6I RELEASE-SAFE EVIDENCE PROMOTION")
    print("=" * 72)
    print(f"Input approval results : {payload['input_result_count']}")
    print(f"READY                  : {payload['ready_count']}")
    print(f"BLOCKED                : {payload['blocked_count']}")

    if errors:
        print("PROMOTION VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    write_json(args.output, payload)

    print("PROMOTION VALIDATION: PASS")
    print("Student visible        : False")
    print(f"OUTPUT                 | {args.output}")


if __name__ == "__main__":
    main()
