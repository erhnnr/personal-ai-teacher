"""
Module:
EIE-009 Teacher Engine

Purpose:
Communicate with the local LLM through LM Studio.

Architecture:
Knowledge First -> Prompt -> Local LLM Generation
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
    complete a local LLM request.
    """


def build_verified_context(plan):
    """
    Load the verified knowledge package for
    the lesson topic.

    Returns None when no detailed knowledge
    package exists.
    """

    try:

        lesson = run_lesson(
            plan.subject,
            plan.grade,
            plan.topic
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
        indent=2
    )


def ask_teacher(question):

    if not isinstance(question, str):

        raise TeacherError(
            "Question must be a string."
        )

    question = question.strip()

    if not question:

        raise TeacherError(
            "Question cannot be empty."
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

        plan = create_plan(
            question
        )

        verified_context = build_verified_context(
            plan
        )

        prompt = build_prompt(
            question,
            plan,
            verified_context=verified_context
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

        return content.strip()

    except TeacherError:
        raise

    except Exception as exc:

        raise TeacherError(
            f"Local teacher request failed: {exc}"
        ) from exc