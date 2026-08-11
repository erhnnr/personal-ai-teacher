from types import SimpleNamespace

import pytest

import teacher

from planner import create_plan
from prompt_builder import build_prompt

from teacher import (
    TeacherError,
    KnowledgeNotReadyError,
    LanguageSafetyError,
)


def test_teacher_prompt_pipeline():

    question = "Fonksiyonlar konusunu anlat."

    plan = create_plan(
        question
    )

    prompt = build_prompt(
        question,
        plan
    )

    assert plan is not None
    assert prompt is not None
    assert "Fonksiyonlar" in prompt
    assert "Yalnızca Türkçe yanıt ver" in prompt


def test_teacher_rejects_empty_question():

    with pytest.raises(
        TeacherError
    ):
        teacher.ask_teacher(
            "   "
        )


def test_teacher_blocks_unverified_knowledge(
    monkeypatch
):

    monkeypatch.setattr(
        teacher,
        "build_verified_context",
        lambda plan: None
    )

    monkeypatch.setattr(
        teacher,
        "build_model1_official_context",
        lambda question, plan: None
    )

    with pytest.raises(
        KnowledgeNotReadyError
    ) as exc_info:

        teacher.ask_teacher(
            "Sinir Sistemi konusunu anlat."
        )

    assert (
    "doğrulanmış veya resmî kaynak-temelli ders bağlamı bulunamadı"
    in str(exc_info.value)
)


def test_teacher_handles_offline_llm(
    monkeypatch
):

    monkeypatch.setattr(
        teacher,
        "build_verified_context",
        lambda plan: "Verified knowledge"
    )

    monkeypatch.setattr(
        teacher,
        "check_llm_connection",
        lambda: {
            "connected": False,
            "models": [],
            "error": "Connection error.",
        }
    )

    with pytest.raises(
        TeacherError
    ) as exc_info:

        teacher.ask_teacher(
            "Limit nedir?"
        )

    assert (
        "LM Studio connection is not available"
        in str(exc_info.value)
    )


def test_teacher_rejects_missing_model(
    monkeypatch
):

    monkeypatch.setattr(
        teacher,
        "build_verified_context",
        lambda plan: "Verified knowledge"
    )

    monkeypatch.setattr(
        teacher,
        "check_llm_connection",
        lambda: {
            "connected": True,
            "models": [
                "another-model"
            ],
            "error": None,
        }
    )

    with pytest.raises(
        TeacherError
    ) as exc_info:

        teacher.ask_teacher(
            "Limit nedir?"
        )

    assert (
        "is not available in LM Studio"
        in str(exc_info.value)
    )


def test_teacher_generates_response(
    monkeypatch
):

    monkeypatch.setattr(
        teacher,
        "build_verified_context",
        lambda plan: (
            "Verified limit knowledge"
        )
    )

    monkeypatch.setattr(
        teacher,
        "check_llm_connection",
        lambda: {
            "connected": True,
            "models": [
                teacher.MODEL_NAME
            ],
            "error": None,
        }
    )

    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=(
                        "Limit, bir fonksiyonun "
                        "yaklaşma davranışını inceler."
                    )
                )
            )
        ]
    )

    def fake_create(**kwargs):

        assert (
            kwargs["model"]
            == teacher.MODEL_NAME
        )

        assert (
            kwargs["temperature"]
            == teacher.LLM_TEMPERATURE
        )

        messages = kwargs[
            "messages"
        ]

        assert len(messages) == 2

        assert (
            "Verified limit knowledge"
            in messages[0]["content"]
        )

        return fake_response

    monkeypatch.setattr(
        teacher.client.chat.completions,
        "create",
        fake_create,
    )

    result = teacher.ask_teacher(
        "Limit nedir?"
    )

    assert result == (
        "Limit, bir fonksiyonun "
        "yaklaşma davranışını inceler."
    )


def test_teacher_rejects_empty_model_response(
    monkeypatch
):

    monkeypatch.setattr(
        teacher,
        "build_verified_context",
        lambda plan: "Verified knowledge"
    )

    monkeypatch.setattr(
        teacher,
        "check_llm_connection",
        lambda: {
            "connected": True,
            "models": [
                teacher.MODEL_NAME
            ],
            "error": None,
        }
    )

    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=""
                )
            )
        ]
    )

    monkeypatch.setattr(
        teacher.client.chat.completions,
        "create",
        lambda **kwargs: fake_response,
    )

    with pytest.raises(
        TeacherError
    ) as exc_info:

        teacher.ask_teacher(
            "Limit nedir?"
        )

    assert (
        "empty response"
        in str(exc_info.value)
    )


def test_disallowed_script_detector():

    assert (
        teacher.contains_disallowed_script(
            "Limit, yaklaşma davranışını inceler."
        )
        is False
    )

    assert (
        teacher.contains_disallowed_script(
            "Limit kavramı şöyle açıklanır: 想象一下"
        )
        is True
    )


def test_teacher_blocks_foreign_script_response(
    monkeypatch
):

    monkeypatch.setattr(
        teacher,
        "build_verified_context",
        lambda plan: "Verified knowledge"
    )

    monkeypatch.setattr(
        teacher,
        "check_llm_connection",
        lambda: {
            "connected": True,
            "models": [
                teacher.MODEL_NAME
            ],
            "error": None,
        }
    )

    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=(
                        "Limit yaklaşma davranışıdır. "
                        "想象一下"
                    )
                )
            )
        ]
    )

    monkeypatch.setattr(
        teacher.client.chat.completions,
        "create",
        lambda **kwargs: fake_response,
    )

    with pytest.raises(
        LanguageSafetyError
    ) as exc_info:

        teacher.ask_teacher(
            "Limit nedir?"
        )

    assert (
        "Türkçe dışı bir yazı sistemi"
        in str(exc_info.value)
    )