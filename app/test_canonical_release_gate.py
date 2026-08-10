import hashlib
import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

import canonical_release_gate as gate


TEXT = "official released evidence"
HASH = hashlib.sha256(TEXT.encode("utf-8")).hexdigest()


def unit():
    return {
        "id": "BİY.10.2.7",
        "subject": "Biyoloji",
        "grade": 10,
        "topic": "Ekolojik ayak izini küçültebilme yollarını sorgulayabilme",
        "learning_objectives": [
            "Ekolojik ayak izini küçültebilme yollarını sorgulayabilme"
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
            "approval_status": "APPROVED_FOR_EVIDENCE_READY",
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
        "canonical_text_sha256": HASH,
        "status": "RELEASED",
        "student_ready": True,
        "student_visible": True,
    }


def test_valid_canonical_unit_passes_validation():
    assert gate.validate_canonical_unit(unit()) == []


def test_release_entry_must_match_hash():
    bad = entry()
    bad["canonical_text_sha256"] = "wrong"
    assert gate.validate_release_entry(bad, unit())


def test_release_entry_requires_student_visibility():
    bad = entry()
    bad["student_visible"] = False
    assert gate.validate_release_entry(bad, unit())


def test_canonical_artifact_cannot_self_release():
    bad = unit()
    bad["student_visible"] = True
    assert gate.validate_canonical_unit(bad)


def test_match_requires_subject_and_grade(monkeypatch):
    monkeypatch.setattr(gate, "released_units", lambda: [unit()])
    assert gate.match_released_unit(
        "Biyoloji",
        11,
        "Ekolojik ayak izi",
    ) is None


def test_conservative_topic_overlap_can_resolve(monkeypatch):
    monkeypatch.setattr(gate, "released_units", lambda: [unit()])
    result = gate.match_released_unit(
        "Biyoloji",
        10,
        "Ekolojik ayak izi",
    )
    assert result["id"] == "BİY.10.2.7"


def test_ambiguous_topic_overlap_is_blocked(monkeypatch):
    second = dict(unit())
    second["id"] = "BİY.10.2.X"
    second["topic"] = "Ekolojik ayak izi hakkında değerlendirme yapabilme"

    monkeypatch.setattr(
        gate,
        "released_units",
        lambda: [unit(), second],
    )

    assert gate.match_released_unit(
        "Biyoloji",
        10,
        "Ekolojik ayak izi",
    ) is None


def test_teacher_context_contains_only_released_canonical(monkeypatch):
    class Plan:
        subject = "Biyoloji"
        grade = 10
        topic = "Ekolojik ayak izi"

    monkeypatch.setattr(
        gate,
        "match_released_unit",
        lambda *args: unit(),
    )

    payload = json.loads(gate.build_teacher_context(Plan()))

    assert payload["source"] == "KNOWLEDGE_FACTORY_V2_RELEASED_CANONICAL"
    assert payload["unit_id"] == "BİY.10.2.7"
    assert payload["knowledge"]["source_grounded_content"]["text"] == TEXT
