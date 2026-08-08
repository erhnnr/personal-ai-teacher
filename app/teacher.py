"""
Module:
EIE-009 Teacher Engine

Purpose:
Communicate with the local LLM through LM Studio.

Architecture:
Verified Knowledge -> Prompt -> Local LLM Generation

Safety rules:
- No verified knowledge -> no teaching.
- Unexpected foreign writing systems -> response rejected.
"""

import json

from config import (
    MODEL_NAME,
    LLM_TEMPERATURE,
)

from llm import (
    client,
    check_llm_connection,
)

from planner import create_plan
from prompt_builder import build_prompt
from teacher_pipeline import run_lesson


class TeacherError(Exception):
    """
    Raised when the teacher engine cannot
    complete a safe local LLM request.
    """


class KnowledgeNotReadyError(TeacherError):
    """
    Raised when a curriculum topic exists but
    its verified teaching content is not ready.
    """


class LanguageSafetyError(TeacherError):
    """
    Raised when the local model produces text
    containing an unexpected writing system.
    """


def contains_disallowed_script(text):
    """
    Detect writing systems that should never
    appear in a Turkish student-facing answer.

    Mathematical symbols and Latin characters
    are intentionally not restricted.
    """

    if not text:
        return False

    disallowed_ranges = (
        # Cyrillic
        (0x0400, 0x052F),

        # Hebrew
        (0x0590, 0x05FF),

        # Arabic
        (0x0600, 0x06FF),
        (0x0750, 0x077F),

        # Japanese Hiragana
        (0x3040, 0x309F),

        # Japanese Katakana
        (0x30A0, 0x30FF),

        # CJK Unified Ideographs
        (0x3400, 0x4DBF),
        (0x4E00, 0x9FFF),

        # Korean Hangul
        (0xAC00, 0xD7AF),
    )

    for character in text:

        code_point = ord(
            character
        )

        for start, end in disallowed_ranges:

            if start <= code_point <= end:
                return True

    return False


def build_verified_context(plan):
    """
    Load the verified knowledge package for
    the planned lesson topic.

    Returns:
        JSON string when verified knowledge exists.
        None when verified knowledge is unavailable.
    """

    try:
        lesson = run_lesson(
            plan.subject,
            plan.grade,
            plan.topic,
        )

    except Exception:
        return None

    if not lesson:
        return None

    knowledge = lesson.get(
        "knowledge"
    )

    if not knowledge:
        return None

    verified_package = {
        "subject": lesson.get("subject"),
        "grade": lesson.get("grade"),
        "topic": lesson.get("topic"),
        "knowledge": knowledge,
    }

    return json.dumps(
        verified_package,
        ensure_ascii=False,
        indent=2,
    )


def ask_teacher(question):
    """
    Answer a student question using verified educational
    knowledge and the local LM Studio model.
    """

    if not isinstance(question, str):
        raise TeacherError(
            "Question must be a string."
        )

    question = question.strip()

    if not question:
        raise TeacherError(
            "Question cannot be empty."
        )

    plan = create_plan(
        question
    )

    verified_context = build_verified_context(
        plan
    )

    if verified_context is None:
        raise KnowledgeNotReadyError(
            f"'{plan.topic}' konusu için doğrulanmış "
            "ders içeriği henüz hazır değil. "
            "Bu nedenle yerel AI modeli bu konuyu "
            "kendi bilgisinden anlatmayacak."
        )

    connection = check_llm_connection()

    if not connection["connected"]:
        raise TeacherError(
            "LM Studio connection is not available. "
            f"Details: {connection['error']}"
        )

    available_models = connection["models"]

    if MODEL_NAME not in available_models:
        raise TeacherError(
            f"Configured model '{MODEL_NAME}' "
            "is not available in LM Studio."
        )

    try:
        prompt = build_prompt(
            question,
            plan,
            verified_context=verified_context,
        )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            temperature=LLM_TEMPERATURE,
        )

        if not response.choices:
            raise TeacherError(
                "The local model returned no response."
            )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:
            raise TeacherError(
                "The local model returned an empty response."
            )

        content = content.strip()

        if contains_disallowed_script(
            content
        ):
            raise LanguageSafetyError(
                "Yerel model Türkçe dışı bir yazı sistemi "
                "kullandı. Yanıt güvenlik nedeniyle "
                "öğrenciye gösterilmedi."
            )

        return content

    except TeacherError:
        raise

    except Exception as exc:
        raise TeacherError(
            f"Local teacher request failed: {exc}"
        ) from exc