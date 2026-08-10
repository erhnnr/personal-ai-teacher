import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

import canonical_release_gate as gate
import teacher


def released_unit():
    return {
        "id": "BİY.12.1.3",
        "subject": "Biyoloji",
        "grade": 12,
        "topic": (
            "Hücredeki genetik materyalin "
            "organizasyonunu çözümleyebilme"
        ),
        "learning_objectives": [],
        "source_grounded_content": {
            "text": "official",
            "text_sha256": "x",
        },
        "provenance": {
            "source_text_sha256": "x",
        },
        "verification": {},
        "verified": True,
        "student_ready": False,
        "student_visible": False,
    }


def test_raw_question_exact_outcome_resolves_even_if_planner_is_wrong(monkeypatch):
    monkeypatch.setattr(
        gate,
        "released_units",
        lambda: [released_unit()],
    )

    result = gate.match_released_unit_from_question(
        "Hücredeki genetik materyalin organizasyonunu "
        "çözümleyebilme konusunu anlat."
    )

    assert result["id"] == "BİY.12.1.3"


def test_unrelated_question_does_not_resolve(monkeypatch):
    monkeypatch.setattr(
        gate,
        "released_units",
        lambda: [released_unit()],
    )

    assert gate.match_released_unit_from_question(
        "Sinir sistemi konusunu anlat."
    ) is None


def test_question_context_uses_raw_question_before_bad_plan(monkeypatch):
    monkeypatch.setattr(
        gate,
        "released_units",
        lambda: [released_unit()],
    )

    class BadPlan:
        subject = "Fizik"
        grade = "12"
        topic = "Hücre"

    context = gate.build_teacher_context_for_question(
        "Hücredeki genetik materyalin organizasyonunu "
        "çözümleyebilme konusunu anlat.",
        BadPlan(),
    )

    payload = json.loads(context)

    assert payload["unit_id"] == "BİY.12.1.3"
    assert payload["subject"] == "Biyoloji"


def test_teacher_question_helper_passes_raw_question(monkeypatch):
    class Plan:
        subject = "Biyoloji"
        grade = "12"
        topic = "Hücre"

    captured = {}

    def fake(question, plan):
        captured["question"] = question
        captured["plan"] = plan
        return "canonical"

    monkeypatch.setattr(
        teacher,
        "build_teacher_context_for_question",
        fake,
    )

    result = teacher.build_verified_context_for_question(
        Plan(),
        "Genetik materyali anlat.",
    )

    assert result == "canonical"
    assert captured["question"] == "Genetik materyali anlat."


def test_teacher_question_helper_falls_back_to_legacy_api(monkeypatch):
    class Plan:
        subject = "Matematik"
        grade = "12"
        topic = "Limit"

    monkeypatch.setattr(
        teacher,
        "build_teacher_context_for_question",
        lambda question, plan: None,
    )

    monkeypatch.setattr(
        teacher,
        "build_verified_context",
        lambda plan: "legacy verified",
    )

    assert (
        teacher.build_verified_context_for_question(
            Plan(),
            "Limit nedir?",
        )
        == "legacy verified"
    )
