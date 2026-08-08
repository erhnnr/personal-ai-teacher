import json
from pathlib import Path
import subprocess
import sys


def run_create_topic(
    base_path,
):
    return subprocess.run(
        [
            sys.executable,
            "tools/create_topic.py",
            "Matematik",
            "12",
            "Test Konusu",
            str(base_path),
        ],
        capture_output=True,
        text=True,
    )


def get_topic_path(
    base_path,
):
    return (
        Path(base_path)
        / "matematik"
        / "grade12"
        / "test_konusu"
    )


def write_json(
    path,
    data,
):
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def populate_valid_topic(
    topic_path,
):

    write_json(
        topic_path / "concept.json",
        {
            "id": (
                "matematik.grade12."
                "test_konusu"
            ),
            "subject": "Matematik",
            "grade": "12",
            "topic": "Test Konusu",
            "learning_objectives": [
                "Temel kavramı açıklayabilme"
            ],
            "prerequisites": [
                "Temel Matematik"
            ],
            "core_concepts": [
                "Test kavramı"
            ],
            "definitions": [
                {
                    "term": "Test Kavramı",
                    "definition": (
                        "Doğrulama amacıyla "
                        "kullanılan örnek kavramdır."
                    ),
                }
            ],
            "rules": [
                "Temel doğrulama kuralı."
            ],
            "common_confusions": [
                "Örnek karışıklık"
            ],
            "teaching_notes": [
                "Önce temel mantık anlatılır."
            ],
        },
    )

    write_json(
        topic_path / "examples.json",
        {
            "topic": "Test Konusu",
            "examples": [
                {
                    "id": "TEST-E001",
                    "level": "basic",
                    "type": "concept",
                    "question": (
                        "Test kavramı nedir?"
                    ),
                    "answer": (
                        "Doğrulama için kullanılan "
                        "örnek kavramdır."
                    ),
                    "learning_point": (
                        "Temel kavramı tanımak."
                    ),
                }
            ],
        },
    )

    write_json(
        topic_path / "mistakes.json",
        {
            "topic": "Test Konusu",
            "mistakes": [
                {
                    "id": "TEST-M001",
                    "error": (
                        "Kavramı yanlış yorumlamak"
                    ),
                    "explanation": (
                        "Kavramın amacı "
                        "karıştırılmıştır."
                    ),
                    "teacher_action": (
                        "Temel tanımı tekrar açıkla."
                    ),
                }
            ],
        },
    )

    write_json(
        topic_path / "relations.json",
        {
            "topic": "Test Konusu",
            "prerequisites": [
                {
                    "topic": "Temel Matematik",
                    "reason": (
                        "Ön bilgi gerektirir."
                    ),
                }
            ],
            "next_topics": [
                {
                    "topic": "İleri Test Konusu",
                    "reason": (
                        "Bir sonraki öğrenme adımıdır."
                    ),
                }
            ],
            "related_topics": [
                {
                    "topic": "Benzer Konu",
                    "relation": (
                        "Yakın kavram"
                    ),
                }
            ],
        },
    )


def test_create_topic_creates_canonical_files(
    tmp_path,
):

    result = run_create_topic(
        tmp_path
    )

    assert result.returncode == 0

    topic_path = get_topic_path(
        tmp_path
    )

    assert topic_path.exists()

    required_files = (
        "concept.json",
        "examples.json",
        "mistakes.json",
        "relations.json",
    )

    for filename in required_files:

        assert (
            topic_path / filename
        ).exists()


def test_new_topic_is_not_ready(
    tmp_path,
):

    result = run_create_topic(
        tmp_path
    )

    assert result.returncode == 0

    topic_path = get_topic_path(
        tmp_path
    )

    validation = subprocess.run(
        [
            sys.executable,
            "tools/validate_knowledge.py",
            str(topic_path),
        ],
        capture_output=True,
        text=True,
    )

    assert (
        validation.returncode != 0
    )

    assert (
        "STATUS: NOT_READY"
        in validation.stdout
    )


def test_completed_topic_is_ready(
    tmp_path,
):

    result = run_create_topic(
        tmp_path
    )

    assert result.returncode == 0

    topic_path = get_topic_path(
        tmp_path
    )

    populate_valid_topic(
        topic_path
    )

    validation = subprocess.run(
        [
            sys.executable,
            "tools/validate_knowledge.py",
            str(topic_path),
        ],
        capture_output=True,
        text=True,
    )

    assert (
        validation.returncode == 0
    )

    assert (
        "STATUS: READY"
        in validation.stdout
    )


def test_validator_rejects_topic_mismatch(
    tmp_path,
):

    result = run_create_topic(
        tmp_path
    )

    assert result.returncode == 0

    topic_path = get_topic_path(
        tmp_path
    )

    populate_valid_topic(
        topic_path
    )

    examples_path = (
        topic_path
        / "examples.json"
    )

    examples = json.loads(
        examples_path.read_text(
            encoding="utf-8"
        )
    )

    examples["topic"] = (
        "Yanlış Konu"
    )

    write_json(
        examples_path,
        examples,
    )

    validation = subprocess.run(
        [
            sys.executable,
            "tools/validate_knowledge.py",
            str(topic_path),
        ],
        capture_output=True,
        text=True,
    )

    assert (
        validation.returncode != 0
    )

    assert (
        "topic does not match"
        in validation.stdout
    )