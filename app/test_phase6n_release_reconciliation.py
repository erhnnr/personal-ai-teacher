import copy
import hashlib
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
TOOLS = APP.parent / "tools"

if str(APP) not in sys.path:
    sys.path.insert(
        0,
        str(APP),
    )

if str(TOOLS) not in sys.path:
    sys.path.insert(
        0,
        str(TOOLS),
    )

import canonical_release_gate as gate
from reconcile_biology_release import (
    reconcile_manifest,
)


TEXT = "official released evidence"
HASH = hashlib.sha256(
    TEXT.encode("utf-8")
).hexdigest()

RECORD_ID = (
    "BİY.10.2.7::"
    "MEBI-TYT-BIYOLOJI::p166"
)


def unit():
    return {
        "id": "BİY.10.2.7",
        "subject": "Biyoloji",
        "grade": 10,
        "topic": (
            "Ekolojik ayak izini küçültebilme "
            "yollarını sorgulayabilme"
        ),
        "learning_objectives": [
            (
                "Ekolojik ayak izini küçültebilme "
                "yollarını sorgulayabilme"
            )
        ],
        "source_grounded_content": {
            "mode": "VERBATIM_OFFICIAL_EVIDENCE",
            "text": TEXT,
            "text_sha256": HASH,
        },
        "provenance": {
            "source_text_sha256": HASH,
        },
        "verification": {
            "evidence_status": "READY",
            "approval_status": (
                "APPROVED_FOR_EVIDENCE_READY"
            ),
            "factual_support": True,
            "outcome_support": True,
            "source_consistency": True,
        },
        "verified": True,
        "student_ready": False,
        "student_visible": False,
    }


def entry():
    return {
        "unit_id": "BİY.10.2.7",
        "record_id": RECORD_ID,
        "canonical_text_sha256": HASH,
        "status": "RELEASED",
        "student_ready": True,
        "student_visible": True,
    }


def review_result(
    *,
    reviewer_type="HUMAN",
    status="APPROVED_FOR_EVIDENCE_READY",
    reviewed_hash=HASH,
    factual=True,
    outcome=True,
    source=True,
):
    return {
        "record_id": RECORD_ID,
        "reviewed_text_sha256": reviewed_hash,
        "review_packet_sha256": "a" * 64,
        "status": status,
        "reviewer_type": reviewer_type,
        "reviewer_id": "reviewer-1",
        "factual_support": factual,
        "outcome_support": outcome,
        "source_consistency": source,
        "rationale": "Reviewed.",
        "student_ready": False,
        "student_visible": False,
    }


def review_document(result):
    return {
        "schema_version": "2.0-hash-bound",
        "student_ready": False,
        "student_visible": False,
        "results": [result],
    }


def test_external_llm_approval_is_not_child_release_eligible(
    monkeypatch,
):
    monkeypatch.setattr(
        gate,
        "load_hash_bound_review_results",
        lambda: review_document(
            review_result(
                reviewer_type="EXTERNAL_LLM"
            )
        ),
    )

    errors = gate.validate_human_hash_bound_release(
        entry(),
        unit(),
    )

    assert (
        "child release requires HUMAN factual review"
        in errors
    )


def test_human_hash_bound_approval_is_release_eligible(
    monkeypatch,
):
    monkeypatch.setattr(
        gate,
        "load_hash_bound_review_results",
        lambda: review_document(
            review_result()
        ),
    )

    assert (
        gate.validate_human_hash_bound_release(
            entry(),
            unit(),
        )
        == []
    )


def test_wrong_reviewed_text_hash_is_blocked(
    monkeypatch,
):
    monkeypatch.setattr(
        gate,
        "load_hash_bound_review_results",
        lambda: review_document(
            review_result(
                reviewed_hash="f" * 64
            )
        ),
    )

    errors = gate.validate_human_hash_bound_release(
        entry(),
        unit(),
    )

    assert any(
        "reviewed text hash"
        in error
        for error in errors
    )


def test_manual_review_status_is_blocked(
    monkeypatch,
):
    monkeypatch.setattr(
        gate,
        "load_hash_bound_review_results",
        lambda: review_document(
            review_result(
                status="MANUAL_REVIEW_REQUIRED"
            )
        ),
    )

    errors = gate.validate_human_hash_bound_release(
        entry(),
        unit(),
    )

    assert any(
        "not approved"
        in error
        for error in errors
    )


def test_reconciliation_suspends_external_llm_only_release():
    manifest = {
        "version": "1.0",
        "kind": "student_release_manifest",
        "subject": "Biyoloji",
        "release_count": 1,
        "units": [entry()],
    }

    review_results = review_document(
        review_result(
            reviewer_type="EXTERNAL_LLM"
        )
    )

    result = reconcile_manifest(
        manifest,
        review_results,
    )

    assert result["release_count"] == 0
    assert (
        result["units"][0]["status"]
        == "SUSPENDED_PENDING_HUMAN_REVIEW"
    )
    assert (
        result["units"][0]["student_ready"]
        is False
    )
    assert (
        result["units"][0]["student_visible"]
        is False
    )


def test_reconciliation_preserves_human_approved_release():
    manifest = {
        "version": "1.0",
        "kind": "student_release_manifest",
        "subject": "Biyoloji",
        "release_count": 1,
        "units": [entry()],
    }

    result = reconcile_manifest(
        manifest,
        review_document(
            review_result()
        ),
    )

    assert result["release_count"] == 1
    assert (
        result["units"][0]["status"]
        == "RELEASED"
    )
    assert (
        result["units"][0]["student_visible"]
        is True
    )
