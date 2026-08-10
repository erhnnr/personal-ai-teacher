"""
Knowledge Factory V2 Phase 3.4 semantic scope tests.
"""

import sys
from pathlib import Path

import pytest

TOOLS_PATH = Path(__file__).resolve().parent.parent / "tools"
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
                "id": "C1",
                "text": (
                    "Bir fonksiyonun belirsiz integralini açıklamayı "
                    "ve integral alma kurallarını oluşturmayı kapsar."
                ),
                "source_refs": [],
            },
            {
                "id": "C4",
                "text": (
                    "F'(x)=f(x) olmak üzere f(x) fonksiyonunun "
                    "belirsiz integrali F(x)+c biçimindedir ve "
                    "c sabit sayısına integral sabiti denir."
                ),
                "source_refs": [],
            },
        ],
        "coverage": {
            "curriculum_objectives": [],
            "excluded_terms": ["belirli integral"],
        },
    }


def package(core_text="Belirsiz integral genellikle F(x)+c şeklinde tanımlanır."):
    return {
        "concept": {
            "id": "matematik.grade12.integral",
            "subject": "Matematik",
            "grade": "12",
            "topic": "İntegral",
            "learning_objectives": [
                {"text": "Belirsiz integral kavramını açıklar ve kural oluşturur.", "evidence_refs": ["C1"]}
            ],
            "prerequisites": [],
            "core_concepts": [
                {"text": core_text, "evidence_refs": ["C4"]}
            ],
            "definitions": [
                {"term": "Belirsiz integral", "definition": "F(x)+c biçiminde yazılır.", "evidence_refs": ["C4"]}
            ],
            "rules": [],
            "common_confusions": [],
            "teaching_notes": [],
        },
        "examples": {"topic": "İntegral", "examples": []},
        "mistakes": {"topic": "İntegral", "mistakes": []},
        "relations": {"topic": "İntegral", "prerequisites": [], "next_topics": [], "related_topics": []},
    }


def test_natural_extra_words_are_not_rejected():
    assert generator.validate_claim_vocabulary_scope(package(), evidence()) is True


def test_explicit_excluded_term_is_rejected():
    with pytest.raises(ValueError, match="Evidence scope exclusion failed"):
        generator.validate_claim_vocabulary_scope(
            package("Belirli integral ve belirsiz integral birlikte ele alınır."),
            evidence(),
        )


def test_unrelated_core_claim_anchor_is_rejected():
    with pytest.raises(ValueError, match="Evidence claim-anchor failed"):
        generator.validate_claim_vocabulary_scope(
            package("Dünya'nın eksen eğikliği mevsimleri etkiler."),
            evidence(),
        )


def test_definite_integral_validation_type_is_rejected_when_excluded():
    data = package()
    data["examples"]["examples"] = [
        {
            "id": "E1",
            "level": "basic",
            "type": "calculation",
            "question": "Bir örnek",
            "answer": "1",
            "learning_point": "İntegral",
            "evidence_refs": ["C4"],
            "validation": {"type": "definite_integral"},
        }
    ]
    with pytest.raises(ValueError, match="Evidence scope exclusion failed"):
        generator.validate_claim_vocabulary_scope(data, evidence())
