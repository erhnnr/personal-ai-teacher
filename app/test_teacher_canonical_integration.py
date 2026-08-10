import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

import teacher


class Plan:
    def __init__(self, subject, grade, topic):
        self.subject = subject
        self.grade = grade
        self.topic = topic


def test_biology_uses_released_canonical_context(monkeypatch):
    plan = Plan("Biyoloji", 10, "Ekolojik ayak izi")

    expected = json.dumps(
        {
            "source": "KNOWLEDGE_FACTORY_V2_RELEASED_CANONICAL",
            "unit_id": "BİY.10.2.7",
        }
    )

    monkeypatch.setattr(
        teacher,
        "build_teacher_context",
        lambda supplied_plan: expected,
    )

    monkeypatch.setattr(
        teacher,
        "run_lesson",
        lambda *args: (_ for _ in ()).throw(
            AssertionError("legacy pipeline must not be used")
        ),
    )

    assert teacher.build_verified_context(plan) == expected


def test_unreleased_biology_never_falls_back_to_legacy(monkeypatch):
    plan = Plan("Biyoloji", 11, "Sinir sistemi")

    monkeypatch.setattr(
        teacher,
        "build_teacher_context",
        lambda supplied_plan: None,
    )

    monkeypatch.setattr(
        teacher,
        "run_lesson",
        lambda *args: {
            "subject": "Biyoloji",
            "grade": 11,
            "topic": "Sinir sistemi",
            "knowledge": {"unsafe_legacy": True},
        },
    )

    assert teacher.build_verified_context(plan) is None


def test_other_subjects_keep_legacy_verified_pipeline(monkeypatch):
    plan = Plan("Matematik", 12, "Limit")

    monkeypatch.setattr(
        teacher,
        "build_teacher_context",
        lambda supplied_plan: None,
    )

    monkeypatch.setattr(
        teacher,
        "run_lesson",
        lambda *args: {
            "subject": "Matematik",
            "grade": 12,
            "topic": "Limit",
            "knowledge": {"definitions": [{"term": "Limit"}]},
        },
    )

    context = json.loads(
        teacher.build_verified_context(plan)
    )

    assert context["source"] == "LEGACY_VERIFIED_KNOWLEDGE"
    assert context["subject"] == "Matematik"
    assert context["topic"] == "Limit"


def test_biology_release_gate_exception_fails_closed(monkeypatch):
    plan = Plan("Biyoloji", 10, "Ekoloji")

    def fail(_):
        raise RuntimeError("release manifest corrupted")

    monkeypatch.setattr(
        teacher,
        "build_teacher_context",
        fail,
    )

    monkeypatch.setattr(
        teacher,
        "run_lesson",
        lambda *args: {
            "knowledge": {"unsafe_legacy": True}
        },
    )

    assert teacher.build_verified_context(plan) is None


def test_teacher_prompt_receives_canonical_source_marker(monkeypatch):
    plan = Plan("Biyoloji", 10, "Ekolojik ayak izi")

    canonical = json.dumps(
        {
            "source": "KNOWLEDGE_FACTORY_V2_RELEASED_CANONICAL",
            "unit_id": "BİY.10.2.7",
            "knowledge": {
                "source_grounded_content": {
                    "text": "official evidence"
                }
            },
        },
        ensure_ascii=False,
    )

    monkeypatch.setattr(
        teacher,
        "build_teacher_context",
        lambda supplied_plan: canonical,
    )

    context = teacher.build_verified_context(plan)

    assert "KNOWLEDGE_FACTORY_V2_RELEASED_CANONICAL" in context
    assert "official evidence" in context
