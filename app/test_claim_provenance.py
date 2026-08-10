"""
Knowledge Factory V2 Phase 3.1:
claim-level provenance enforcement tests.
"""

import json
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
    sys.path.insert(
        0,
        str(TOOLS_PATH),
    )

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
                    "Bir fonksiyonun belirsiz integralini "
                    "açıklayarak integral alma kurallarını oluşturur."
                ),
                "source_refs": [],
            },
            {
                "id": "C2",
                "text": (
                    "F'(x)=f(x) ise F(x), f(x) fonksiyonunun "
                    "ters türevi veya belirsiz integrali olarak ele alınır."
                ),
                "source_refs": [],
            },
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
                    "text": (
                        "Belirsiz integral kavramını açıklar."
                    ),
                    "evidence_refs": ["C1"],
                }
            ],
            "prerequisites": [],
            "core_concepts": [
                {
                    "text": "Belirsiz integral",
                    "evidence_refs": ["C1"],
                }
            ],
            "definitions": [
                {
                    "term": "Belirsiz integral",
                    "definition": (
                        "F'(x)=f(x) ise F(x), f(x) "
                        "fonksiyonunun belirsiz integralidir."
                    ),
                    "evidence_refs": ["C2"],
                }
            ],
            "rules": [
                {
                    "text": "İntegral alma kurallarını uygular.",
                    "evidence_refs": ["C1"],
                }
            ],
            "common_confusions": [],
            "teaching_notes": [],
        },
        "examples": {
            "topic": "İntegral",
            "examples": [
                {
                    "id": "E1",
                    "level": "basic",
                    "type": "concept",
                    "question": "Belirsiz integral nedir?",
                    "answer": "Ters türev ile ilişkilidir.",
                    "learning_point": "Belirsiz integral",
                    "evidence_refs": ["C2"],
                }
            ],
        },
        "mistakes": {
            "topic": "İntegral",
            "mistakes": [
                {
                    "id": "M1",
                    "error": "Belirsiz integrali yanlış yorumlamak.",
                    "explanation": (
                        "Belirsiz integral ters türev ile ilişkilidir."
                    ),
                    "teacher_action": "Ters türev ilişkisini açıkla.",
                    "evidence_refs": ["C2"],
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


def test_unknown_claim_reference_is_rejected():
    data = package()

    data["concept"][
        "core_concepts"
    ][0]["evidence_refs"] = [
        "C999"
    ]

    with pytest.raises(
        ValueError,
        match="Unknown evidence claim",
    ):
        generator.validate_claim_level_provenance(
            data,
            evidence(),
        )


def test_previous_belirli_integral_escape_is_rejected():
    data = package()

    data["concept"][
        "learning_objectives"
    ][0]["text"] = (
        "Belirsiz integralin ve belirli integralin "
        "tanımını anlar."
    )

    with pytest.raises(
        ValueError,
        match="Evidence scope exclusion failed",
    ):
        generator.validate_claim_vocabulary_scope(
            data,
            evidence(),
        )


def test_canonicalization_strips_refs_and_keeps_map():
    data = package()

    canonical = (
        generator
        .canonicalize_grounded_package(
            data,
            evidence(),
        )
    )

    assert canonical[
        "concept"
    ][
        "learning_objectives"
    ] == [
        "Belirsiz integral kavramını açıklar."
    ]

    assert (
        "evidence_refs"
        not in canonical[
            "concept"
        ][
            "definitions"
        ][0]
    )

    provenance = canonical[
        "_provenance"
    ]

    assert (
        provenance["status"]
        == "PASS"
    )

    assert (
        provenance["evidence_id"]
        == "matematik.grade12.integral"
    )

    assert any(
        item["path"]
        == "concept.definitions[0]"
        for item in provenance[
            "items"
        ]
    )


def test_save_draft_writes_provenance_file(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        generator,
        "DRAFT_ROOT",
        tmp_path,
    )

    canonical = (
        generator
        .canonicalize_grounded_package(
            package(),
            evidence(),
        )
    )

    path = generator.save_draft(
        {
            "exam": "AYT",
            "subject": "Matematik",
            "topic": "İntegral",
            "priority": "critical",
        },
        "12",
        canonical,
        evidence=evidence(),
    )

    provenance_path = (
        path
        / "provenance.json"
    )

    assert provenance_path.exists()

    metadata = json.loads(
        (
            path
            / "draft_meta.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        metadata[
            "claim_provenance_status"
        ]
        == "PASS"
    )

    assert (
        metadata[
            "provenance_file"
        ]
        == "provenance.json"
    )
