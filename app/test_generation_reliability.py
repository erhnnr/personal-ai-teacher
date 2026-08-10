"""
Knowledge Factory V2 Phase 3.2:
generation reliability tests.
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
    sys.path.insert(
        0,
        str(TOOLS_PATH),
    )

import generate_knowledge_batch as generator


def test_retry_feedback_is_injected():
    evidence = {
        "id": "matematik.grade12.integral",
        "sources": [],
        "claims": [
            {
                "id": "C1",
                "text": "Belirsiz integral açıklanır.",
                "source_refs": [],
            }
        ],
        "coverage": {
            "curriculum_objectives": []
        },
    }

    prompt = generator.build_prompt(
        {
            "exam": "AYT",
            "subject": "Matematik",
            "topic": "İntegral",
        },
        "12",
        evidence=evidence,
        generation_feedback=(
            "definitions must be non-empty"
        ),
    )

    assert "ÖNCEKİ DENEME REDDEDİLDİ" in prompt
    assert "definitions must be non-empty" in prompt


def test_retry_passes_previous_error(
    monkeypatch,
):
    calls = []

    def fake_generate_one(
        record,
        grade,
        evidence=None,
        generation_feedback=None,
    ):
        calls.append(
            generation_feedback
        )

        if len(calls) == 1:
            raise ValueError(
                "first contract error"
            )

        return {
            "concept": {},
            "examples": {},
            "mistakes": {},
            "relations": {},
        }

    monkeypatch.setattr(
        generator,
        "generate_one",
        fake_generate_one,
    )

    _package, attempts = (
        generator.generate_with_retry(
            {
                "topic": "İntegral"
            },
            "12",
            max_attempts=2,
            evidence={},
        )
    )

    assert attempts == 2
    assert calls == [
        None,
        "first contract error",
    ]


def test_terminal_retry_error_exposes_attempt_count(
    monkeypatch,
):
    def always_fail(
        record,
        grade,
        evidence=None,
        generation_feedback=None,
    ):
        raise ValueError(
            "bad json"
        )

    monkeypatch.setattr(
        generator,
        "generate_one",
        always_fail,
    )

    with pytest.raises(
        RuntimeError
    ) as exc_info:
        generator.generate_with_retry(
            {
                "topic": "İntegral"
            },
            "12",
            max_attempts=3,
            evidence={},
        )

    assert (
        exc_info.value.attempts_used
        == 3
    )
