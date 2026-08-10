import hashlib
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import promote_ready_evidence as promotion


TEXT = "official evidence text"
HASH = hashlib.sha256(TEXT.encode("utf-8")).hexdigest()


def original():
    return {
        "record_id": "R1",
        "outcome_id": "BİY.12.2.1",
        "grade": 12,
        "theme_number": 2,
        "theme_name": "Gen",
        "outcome_title": "Nükleik asitler",
        "source": {
            "authority": "MEB",
            "corpus_family": "MEBI_OFFICIAL_LOCAL_CORPUS",
            "package_id": "MEBI-AYT-BIYOLOJI",
            "page": 151,
            "source_anchor": "ayt-biyoloji/index.html#p=151",
            "html_path": "files/basic-html/page151.html",
            "image_path": "files/thumb/151.jpg",
            "text_sha256": HASH,
        },
        "verification": {"status": "VERIFIED_SUPPORT_CANDIDATE"},
        "evidence_text": TEXT,
        "evidence_status": "NOT_READY",
        "student_visible": False,
    }


def approved_result():
    return {
        "record_id": "R1",
        "source": dict(original()["source"]),
        "approval": {
            "status": "APPROVED_FOR_EVIDENCE_READY",
            "reviewer_type": "EXTERNAL_LLM",
            "reviewer_id": "reviewer-1",
            "factual_support": True,
            "outcome_support": True,
            "source_consistency": True,
            "rationale": "independently checked",
        },
        "evidence_status": "NOT_READY",
        "student_visible": False,
    }


def build(result=None, orig=None):
    return promotion.build_promoted_payload(
        {"results": [result or approved_result()]},
        {"records": [orig or original()]},
    )


def test_valid_independent_approval_promotes_to_ready():
    payload = build()
    assert payload["ready_count"] == 1
    assert payload["blocked_count"] == 0
    assert payload["records"][0]["evidence_status"] == "READY"


def test_student_visibility_remains_false_after_promotion():
    payload = build()
    assert payload["records"][0]["student_visible"] is False
    assert payload["student_visible"] is False


def test_manual_review_cannot_promote():
    result = approved_result()
    result["approval"]["status"] = "MANUAL_REVIEW_REQUIRED"
    payload = build(result=result)
    assert payload["ready_count"] == 0
    assert payload["blocked_count"] == 1


def test_rejected_record_cannot_promote():
    result = approved_result()
    result["approval"]["status"] = "REJECTED"
    payload = build(result=result)
    assert payload["ready_count"] == 0
    assert payload["blocked_count"] == 1


def test_failed_factual_support_cannot_promote():
    result = approved_result()
    result["approval"]["factual_support"] = False
    payload = build(result=result)
    assert payload["ready_count"] == 0


def test_hash_mismatch_blocks_promotion():
    orig = original()
    orig["evidence_text"] = "tampered evidence"
    payload = build(orig=orig)
    assert payload["ready_count"] == 0
    checks = payload["blocked"][0]["promotion_checks"]
    assert checks["evidence_hash_matches_source"] is False


def test_changed_provenance_blocks_promotion():
    result = approved_result()
    result["source"]["page"] = 999
    payload = build(result=result)
    assert payload["ready_count"] == 0
    checks = payload["blocked"][0]["promotion_checks"]
    assert checks["source_unchanged"] is False


def test_missing_original_record_is_blocked():
    payload = promotion.build_promoted_payload(
        {"results": [approved_result()]},
        {"records": []},
    )
    assert payload["ready_count"] == 0
    assert payload["blocked_count"] == 1
    assert payload["blocked"][0]["reason"] == "ORIGINAL_EVIDENCE_RECORD_MISSING"


def test_validation_rejects_student_visible_ready_record():
    payload = build()
    payload["records"][0]["student_visible"] = True
    assert promotion.validate_payload(payload)
