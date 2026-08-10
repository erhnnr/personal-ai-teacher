import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_independent_factual_approval_queue as queue_builder
import apply_independent_factual_approvals as applier


def evidence_record():
    return {
        "record_id": "BİY.12.2.2::MEBI-AYT-BIYOLOJI::p170",
        "outcome_id": "BİY.12.2.2",
        "grade": 12,
        "theme_number": 2,
        "theme_name": "Gen",
        "outcome_title": "DNA replikasyonunun bilimsel modelini oluşturabilme",
        "source": {
            "authority": "MEB",
            "package_id": "MEBI-AYT-BIYOLOJI",
            "page": 170,
            "source_anchor": "index.html#p=170",
            "html_path": "files/basic-html/page170.html",
            "image_path": "files/thumb/170.jpg",
            "text_sha256": "a" * 64,
        },
        "evidence_text": "DNA replikasyonu hakkında resmi kaynak metni.",
    }


def review_pass():
    return {
        "record_id": evidence_record()["record_id"],
        "outcome_id": "BİY.12.2.2",
        "grade": 12,
        "theme_number": 2,
        "theme_name": "Gen",
        "outcome_title": "DNA replikasyonunun bilimsel modelini oluşturabilme",
        "review_gate_status": "REVIEW_PASS_CANDIDATE",
        "gate_checks": {"title_support_ok": True},
        "matched_title_tokens": ["dna", "replikasyonunun", "modelini"],
    }


def queue_payload():
    return queue_builder.build_queue(
        {
            "reviews": [review_pass()],
        },
        {
            "records": [evidence_record()],
        },
    )


def test_queue_contains_only_review_pass_candidates():
    failed = dict(review_pass())
    failed["record_id"] = "failed"
    failed["review_gate_status"] = "MANUAL_REVIEW_REQUIRED"

    payload = queue_builder.build_queue(
        {"reviews": [review_pass(), failed]},
        {"records": [evidence_record()]},
    )

    assert payload["queue_count"] == 1


def test_queue_starts_pending_and_not_ready():
    payload = queue_payload()
    item = payload["items"][0]
    assert item["approval"]["status"] == "PENDING"
    assert item["evidence_status"] == "NOT_READY"
    assert item["student_visible"] is False


def test_approval_requires_explicit_reviewer():
    decision = {
        "record_id": evidence_record()["record_id"],
        "status": "APPROVED_FOR_EVIDENCE_READY",
        "reviewer_type": "HUMAN",
        "reviewer_id": "",
        "factual_support": True,
        "outcome_support": True,
        "source_consistency": True,
        "rationale": "checked",
    }
    errors = applier.validate_decision(decision)
    assert any("reviewer_id" in error for error in errors)


def test_approval_requires_all_boolean_checks_true():
    decision = {
        "record_id": evidence_record()["record_id"],
        "status": "APPROVED_FOR_EVIDENCE_READY",
        "reviewer_type": "EXTERNAL_LLM",
        "reviewer_id": "reviewer-1",
        "factual_support": True,
        "outcome_support": False,
        "source_consistency": True,
        "rationale": "outcome not sufficiently supported",
    }
    errors = applier.validate_decision(decision)
    assert errors


def test_valid_explicit_approval_is_applied_but_not_promoted():
    queue = queue_payload()
    decisions = {
        "decisions": [
            {
                "record_id": evidence_record()["record_id"],
                "status": "APPROVED_FOR_EVIDENCE_READY",
                "reviewer_type": "HUMAN",
                "reviewer_id": "reviewer-1",
                "factual_support": True,
                "outcome_support": True,
                "source_consistency": True,
                "rationale": "source and outcome checked independently",
            }
        ]
    }

    payload = applier.apply_decisions(queue, decisions)
    result = payload["results"][0]

    assert result["approval"]["status"] == "APPROVED_FOR_EVIDENCE_READY"
    assert result["evidence_status"] == "NOT_READY"
    assert result["student_visible"] is False


def test_missing_decision_remains_pending():
    payload = applier.apply_decisions(
        queue_payload(),
        {"decisions": []},
    )
    assert payload["results"][0]["approval"]["status"] == "PENDING"


def test_queue_validation_protects_release_state():
    payload = queue_payload()
    payload["items"][0]["student_visible"] = True
    errors = queue_builder.validate_queue(payload)
    assert errors
