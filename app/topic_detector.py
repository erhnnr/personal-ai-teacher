"""
Topic Detector

Purpose:
Detect curriculum topics from natural-language
student questions.

Primary source:
curriculum/data/*.json

Legacy curriculum is used only for:
- backward compatibility
- grade metadata when available
"""

import re
import unicodedata

from curriculum_engine import load_curriculum_data

try:
    from topics import CURRICULUM
except ImportError:
    CURRICULUM = {}


def normalize_text(text):
    """
    Normalize Turkish text for reliable topic matching.
    """

    if text is None:
        return ""

    text = str(text).strip()

    replacements = {
        "İ": "i",
        "I": "ı",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.casefold()

    text = unicodedata.normalize(
        "NFC",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def find_legacy_grade(
    subject,
    topic
):
    """
    Return grade metadata from the legacy curriculum
    when the same subject/topic exists there.

    The legacy curriculum is not used as the primary
    topic source.
    """

    normalized_subject = normalize_text(
        subject
    )

    normalized_topic = normalize_text(
        topic
    )

    for legacy_subject in CURRICULUM:

        if (
            normalize_text(legacy_subject)
            != normalized_subject
        ):
            continue

        for grade in CURRICULUM[
            legacy_subject
        ]:

            for legacy_topic in CURRICULUM[
                legacy_subject
            ][grade]:

                if (
                    normalize_text(legacy_topic)
                    == normalized_topic
                ):
                    return str(
                        grade
                    )

    return None


def detect_from_current_curriculum(
    question
):
    """
    Detect topics from the current JSON curriculum.
    """

    normalized_question = normalize_text(
        question
    )

    try:
        records = load_curriculum_data()

    except Exception:
        return None

    candidates = []

    for record in records:

        topic = record.get(
            "topic"
        )

        if not topic:
            continue

        normalized_topic = normalize_text(
            topic
        )

        if (
            normalized_topic
            in normalized_question
        ):

            candidates.append(
                (
                    len(normalized_topic),
                    record,
                )
            )

    if not candidates:
        return None

    # Prefer the longest topic match.
    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    record = candidates[0][1]

    subject = record.get(
        "subject"
    )

    topic = record.get(
        "topic"
    )

    grade = find_legacy_grade(
        subject,
        topic,
    )

    return {
        "subject": subject,
        "topic": topic,
        "grade": grade,
        "exam": record.get("exam"),
    }


def detect_from_legacy_curriculum(
    question
):
    """
    Backward-compatible detector for the old
    hardcoded curriculum structure.
    """

    normalized_question = normalize_text(
        question
    )

    candidates = []

    for subject in CURRICULUM:

        for grade in CURRICULUM[
            subject
        ]:

            for topic in CURRICULUM[
                subject
            ][grade]:

                normalized_topic = normalize_text(
                    topic
                )

                if (
                    normalized_topic
                    in normalized_question
                ):

                    candidates.append(
                        (
                            len(normalized_topic),
                            subject,
                            grade,
                            topic,
                        )
                    )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    _, subject, grade, topic = (
        candidates[0]
    )

    return {
        "subject": subject,
        "topic": topic,
        "grade": str(grade),
        "exam": None,
    }


def detect_topic(question):

    if not question:

        return {
            "subject": None,
            "topic": None,
            "grade": None,
            "exam": None,
        }

    result = detect_from_current_curriculum(
        question
    )

    if result:
        return result

    result = detect_from_legacy_curriculum(
        question
    )

    if result:
        return result

    return {
        "subject": None,
        "topic": None,
        "grade": None,
        "exam": None,
    }