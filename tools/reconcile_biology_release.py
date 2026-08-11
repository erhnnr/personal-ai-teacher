"""
Phase 6N — reconcile the Biology student release manifest with the
hash-bound factual review state.

Policy:
- EXTERNAL_LLM approval is not sufficient for child release.
- Until an exact-text HUMAN approval exists, every Biology release
  entry is suspended and student visibility is revoked.
- Historical entries are preserved; canonical artifacts are untouched.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

MANIFEST_PATH = (
    ROOT
    / "data"
    / "knowledge"
    / "student_release"
    / "biology_release_manifest.json"
)

REVIEW_RESULTS_PATH = (
    ROOT
    / "data"
    / "knowledge"
    / "factual_approval"
    / "biology_hash_bound_review_results.json"
)


def read_json(path: Path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def write_json(path: Path, value):
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def human_approved_record_ids(
    review_results,
):
    approved = set()

    for result in review_results.get(
        "results",
        [],
    ):
        if (
            result.get("status")
            == "APPROVED_FOR_EVIDENCE_READY"
            and result.get("reviewer_type")
            == "HUMAN"
            and result.get("factual_support")
            is True
            and result.get("outcome_support")
            is True
            and result.get("source_consistency")
            is True
            and result.get("reviewed_text_sha256")
            and result.get("review_packet_sha256")
        ):
            approved.add(
                result.get("record_id")
            )

    return approved


def reconcile_manifest(
    manifest,
    review_results,
):
    approved_ids = human_approved_record_ids(
        review_results
    )

    units = []

    for original in manifest.get(
        "units",
        [],
    ):
        entry = dict(original)

        if (
            entry.get("record_id")
            in approved_ids
        ):
            # A future human-approved item remains eligible only if
            # the release gate also validates the exact canonical hash.
            entry["status"] = "RELEASED"
            entry["student_ready"] = True
            entry["student_visible"] = True
            entry[
                "release_policy"
            ] = (
                "HASH_BOUND_CANONICAL_"
                "PLUS_HUMAN_REVIEW_RELEASE"
            )
        else:
            entry[
                "status"
            ] = (
                "SUSPENDED_PENDING_HUMAN_REVIEW"
            )
            entry["student_ready"] = False
            entry["student_visible"] = False
            entry[
                "release_policy"
            ] = (
                "FAIL_CLOSED_PENDING_"
                "HASH_BOUND_HUMAN_REVIEW"
            )

        units.append(entry)

    released_count = sum(
        1
        for entry in units
        if (
            entry.get("status")
            == "RELEASED"
            and entry.get(
                "student_ready"
            )
            is True
            and entry.get(
                "student_visible"
            )
            is True
        )
    )

    return {
        "version": "2.0",
        "kind": "student_release_manifest",
        "subject": manifest.get(
            "subject",
            "Biyoloji",
        ),
        "release_count": released_count,
        "release_policy": (
            "HASH_BOUND_HUMAN_REVIEW_REQUIRED"
        ),
        "review_results_source": (
            "data/knowledge/factual_approval/"
            "biology_hash_bound_review_results.json"
        ),
        "units": units,
    }


def main():
    if not MANIFEST_PATH.exists():
        raise SystemExit(
            "Biology release manifest not found."
        )

    if not REVIEW_RESULTS_PATH.exists():
        raise SystemExit(
            "Hash-bound review results not found."
        )

    manifest = read_json(
        MANIFEST_PATH
    )
    review_results = read_json(
        REVIEW_RESULTS_PATH
    )

    reconciled = reconcile_manifest(
        manifest,
        review_results,
    )

    write_json(
        MANIFEST_PATH,
        reconciled,
    )

    suspended = sum(
        1
        for entry in reconciled["units"]
        if entry["status"]
        == "SUSPENDED_PENDING_HUMAN_REVIEW"
    )

    print(
        "KNOWLEDGE FACTORY V2 — PHASE 6N RELEASE RECONCILIATION"
    )
    print(
        "Policy                 : HUMAN HASH-BOUND REVIEW REQUIRED"
    )
    print(
        f"Released               : {reconciled['release_count']}"
    )
    print(
        f"Suspended              : {suspended}"
    )
    print(
        "Student Biology access : FAIL-CLOSED"
    )
    print(
        f"MANIFEST | {MANIFEST_PATH}"
    )


if __name__ == "__main__":
    main()
