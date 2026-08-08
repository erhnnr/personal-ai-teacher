"""
Knowledge Topic Factory

Purpose:
Create the canonical directory and JSON files
for one educational knowledge topic.

Important:
Creating the files does NOT make the topic READY.

A newly created package is intentionally incomplete
and must pass validate_knowledge.py before it can be
treated as verified teaching knowledge.
"""

from pathlib import Path
import json
import re
import sys


DEFAULT_BASE_PATH = Path(
    "data/knowledge/units"
)


def slugify(value):
    """
    Convert Turkish display text into a stable
    ASCII directory name.
    """

    value = str(value).strip()

    replacements = {
        "İ": "I",
        "Ç": "C",
        "Ğ": "G",
        "Ö": "O",
        "Ş": "S",
        "Ü": "U",
        "ı": "i",
        "ç": "c",
        "ğ": "g",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    return value.strip("_")

def normalize_grade(grade):
    """
    Normalize grades such as:
    12
    grade12
    Grade12

    into:
    12
    """

    grade = str(
        grade
    ).strip().lower()

    if grade.startswith(
        "grade"
    ):
        grade = grade[5:]

    return grade.strip()


def create_topic(
    subject,
    grade,
    topic,
    base_path=None,
):
    """
    Create an empty canonical knowledge package.

    Returns:
        Path of the created topic directory.
    """

    if base_path is None:
        base_path = DEFAULT_BASE_PATH

    base_path = Path(
        base_path
    )

    normalized_grade = normalize_grade(
        grade
    )

    subject_slug = slugify(
        subject
    )

    topic_slug = slugify(
        topic
    )

    grade_slug = (
        f"grade{normalized_grade}"
    )

    topic_path = (
        base_path
        / subject_slug
        / grade_slug
        / topic_slug
    )

    topic_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    topic_id = (
        f"{subject_slug}."
        f"grade{normalized_grade}."
        f"{topic_slug}"
    )

    files = {
        "concept.json": {
            "id": topic_id,
            "subject": subject,
            "grade": normalized_grade,
            "topic": topic,
            "learning_objectives": [],
            "prerequisites": [],
            "core_concepts": [],
            "definitions": [],
            "rules": [],
            "common_confusions": [],
            "teaching_notes": [],
        },
        "examples.json": {
            "topic": topic,
            "examples": [],
        },
        "mistakes.json": {
            "topic": topic,
            "mistakes": [],
        },
        "relations.json": {
            "topic": topic,
            "prerequisites": [],
            "next_topics": [],
            "related_topics": [],
        },
    }

    for filename, content in files.items():

        file_path = (
            topic_path
            / filename
        )

        if not file_path.exists():

            file_path.write_text(
                json.dumps(
                    content,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

    print(
        "Knowledge package created:"
    )

    print(
        topic_path
    )

    print(
        "STATUS: NOT_READY"
    )

    print(
        "Fill the educational content and "
        "run validate_knowledge.py."
    )

    return topic_path


if __name__ == "__main__":

    if len(sys.argv) not in (
        4,
        5,
    ):

        print(
            "Usage: "
            "python create_topic.py "
            "<subject> <grade> <topic> "
            "[base_path]"
        )

        sys.exit(1)

    base_path = None

    if len(sys.argv) == 5:
        base_path = sys.argv[4]

    create_topic(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        base_path=base_path,
    )