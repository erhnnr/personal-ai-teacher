import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_independent_reviewer_packet as builder


def queue():
    return {
        "subject": "Biyoloji",
        "items": [
            {
                "record_id": "R1",
                "outcome_id": "BİY.12.2.2",
                "grade": 12,
                "theme_name": "Gen",
                "outcome_title": "DNA replikasyonu",
                "source": {
                    "package_id": "MEBI-AYT-BIYOLOJI",
                    "page": 170,
                    "source_anchor": "index.html#p=170",
                    "text_sha256": "a" * 64,
                },
                "pre_review": {
                    "matched_title_tokens": ["dna", "replikasyonu"]
                },
                "evidence_text": "DNA replikasyonu hakkında resmi metin.",
            }
        ],
    }


def test_packet_preserves_not_ready_state():
    payload = builder.build_packet(queue())
    item = payload["items"][0]
    assert item["evidence_status"] == "NOT_READY"
    assert item["student_visible"] is False


def test_packet_does_not_contain_approval_decision():
    payload = builder.build_packet(queue())
    item = payload["items"][0]
    assert "approval" not in item


def test_packet_has_required_review_questions():
    payload = builder.build_packet(queue())
    questions = payload["items"][0]["review_questions"]
    assert set(questions) == {
        "factual_support",
        "outcome_support",
        "source_consistency",
    }


def test_validation_accepts_valid_packet():
    payload = builder.build_packet(queue())
    assert builder.validate_packet(payload) == []


def test_validation_rejects_student_visible_true():
    payload = builder.build_packet(queue())
    payload["items"][0]["student_visible"] = True
    assert builder.validate_packet(payload)
