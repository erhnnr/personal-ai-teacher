"""
Knowledge Factory V2 Phase 3.3.3:
scope guard field-boundary tests.
"""

import sys
from pathlib import Path

import pytest


TOOLS_PATH = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "tools"
)

if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(0, str(TOOLS_PATH))

import generate_knowledge_batch as generator


def evidence():
    return {
        "id": "matematik.grade12.integral",
        "exam": "AYT",
        "subject": "Matematik",
        "grade": "12",
        "topic": "İntegral",
        "status": "EVIDENCE_READY",
        "sources": [],
        "claims": [
            {
                "id": "C4",
                "text": (
                    "F'(x)=f(x) olmak üzere f(x) fonksiyonunun "
                    "belirsiz integrali F(x)+c biçimindedir ve "
                    "c sabit sayısına integral sabiti denir."
                ),
                "source_refs": [],
            }
        ],
        "coverage": {
            "curriculum_objectives": [],
            "excluded_terms": ["belirli integral"],
        },
    }


def package():
    return {
        "concept": {
            "id": "matematik.grade12.integral",
            "subject": "Matematik",
            "grade": "12",
            "topic": "İntegral",
            "learning_objectives": [
                {
                    "text": "Belirsiz integral kavramını açıklar.",
                    "evidence_refs": ["C4"],
                }
            ],
            "prerequisites": [],
            "core_concepts": [
                {
                    "text": "Belirsiz integral",
                    "evidence_refs": ["C4"],
                }
            ],
            "definitions": [
                {
                    "term": "Belirsiz integral",
                    "definition": (
                        "F'(x)=f(x) ise F(x)+c biçiminde yazılır."
                    ),
                    "evidence_refs": ["C4"],
                }
            ],
            "rules": [
                {
                    "text": "İntegral sabiti kullanılır.",
                    "evidence_refs": ["C4"],
                }
            ],
            "common_confusions": [
                {
                    "text": "Öğrenci integral sabitini unutabilir.",
                    "evidence_refs": ["C4"],
                }
            ],
            "teaching_notes": [
                {
                    "text": "Öğrenciye kısa bir hatırlatma yap.",
                    "evidence_refs": ["C4"],
                }
            ],
        },
        "examples": {
            "topic": "İntegral",
            "examples": [
                {
                    "id": "E1",
                    "level": "basic",
                    "type": "concept",
                    "question": "Belirsiz integral nedir?",
                    "answer": "F(x)+c biçiminde yazılır.",
                    "learning_point": "Belirsiz integral",
                    "evidence_refs": ["C4"],
                }
            ],
        },
        "mistakes": {
            "topic": "İntegral",
            "mistakes": [
                {
                    "id": "M1",
                    "error": "İntegral sabitini unutmak.",
                    "explanation": (
                        "Bu hata öğrencinin sabiti yazmamasıdır."
                    ),
                    "teacher_action": "Sabiti hatırlat.",
                    "evidence_refs": ["C4"],
                }
            ],
        },
        "relations": {
            "topic": "İntegral",
            "prerequisites": [],
            "next_topics": [],
            "related_topics": [],
        },
    }


def test_pedagogical_meta_language_does_not_fail_scope_guard():
    assert (
        generator.validate_claim_vocabulary_scope(
            package(),
            evidence(),
        )
        is True
    )


def test_core_factual_scope_escape_is_still_rejected():
    data = package()

    data["concept"]["core_concepts"][0]["text"] = (
        "Belirli integral ve belirsiz integral"
    )

    with pytest.raises(
        ValueError,
        match="Evidence scope exclusion failed",
    ):
        generator.validate_claim_vocabulary_scope(
            data,
            evidence(),
        )
