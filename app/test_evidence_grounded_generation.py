"""
Knowledge Factory V2 evidence-grounded generation tests.
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
    sys.path.insert(0, str(TOOLS_PATH))

import generate_knowledge_batch as generator


def _record():
    return {
        "exam": "AYT",
        "subject": "Matematik",
        "topic": "Limit",
        "priority": "high",
    }


def _evidence(status="EVIDENCE_READY"):
    return {
        "id": "matematik.grade12.limit",
        "exam": "AYT",
        "subject": "Matematik",
        "grade": "12",
        "topic": "Limit",
        "status": status,
        "sources": [
            {
                "source_id": "SRC-1",
                "locations": [
                    {
                        "locator": "p. 1"
                    }
                ],
            }
        ],
        "claims": [
            {
                "id": "C1",
                "text": "Bir fonksiyonun bir noktadaki limiti incelenir.",
                "source_refs": [
                    {
                        "source_id": "SRC-1",
                        "locator": "p. 1",
                    }
                ],
            }
        ],
        "coverage": {
            "curriculum_objectives": [
                "Limit kavramını açıklar."
            ]
        },
    }


def test_load_ready_evidence_rejects_missing_file(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        generator,
        "EVIDENCE_ROOT",
        tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="evidence file is missing",
    ):
        generator.load_ready_evidence(
            _record(),
            "12",
        )


def test_load_ready_evidence_rejects_not_ready(
    tmp_path,
    monkeypatch,
):
    path = (
        tmp_path
        / "matematik"
        / "grade12"
        / "limit"
        / "evidence.json"
    )
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            _evidence(
                status="EVIDENCE_DRAFT"
            ),
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        generator,
        "EVIDENCE_ROOT",
        tmp_path,
    )
    monkeypatch.setattr(
        generator,
        "validate_evidence_package",
        lambda evidence: True,
    )

    with pytest.raises(
        ValueError,
        match="not EVIDENCE_READY",
    ):
        generator.load_ready_evidence(
            _record(),
            "12",
        )


def test_ready_evidence_is_injected_into_prompt():
    evidence = _evidence()

    prompt = generator.build_prompt(
        _record(),
        "12",
        evidence=evidence,
    )

    assert "EVIDENCE PACKAGE:" in prompt
    assert "SRC-1" in prompt
    assert evidence["claims"][0]["text"] in prompt
    assert (
        "Model hafızasından yeni tanım"
        in prompt
    )


def test_save_draft_records_grounding_metadata(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        generator,
        "DRAFT_ROOT",
        tmp_path,
    )

    package = {
        "concept": {},
        "examples": {},
        "mistakes": {},
        "relations": {},
    }

    path = generator.save_draft(
        _record(),
        "12",
        package,
        evidence=_evidence(),
    )

    metadata = json.loads(
        (
            path
            / "draft_meta.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        metadata["source_grounded"]
        is True
    )
    assert (
        metadata["evidence_id"]
        == "matematik.grade12.limit"
    )
    assert (
        metadata["evidence_sources"]
        == ["SRC-1"]
    )
