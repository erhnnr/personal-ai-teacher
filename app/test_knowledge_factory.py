import json
from pathlib import Path
import subprocess
import sys


def test_create_topic():

    topic_path = Path(
        "data/knowledge/units/test_subject/grade12/test_topic"
    )

    if topic_path.exists():
        for file in topic_path.iterdir():
            file.unlink()
        topic_path.rmdir()

    result = subprocess.run(
        [
            sys.executable,
            "tools/create_topic.py",
            "test_subject",
            "grade12",
            "test_topic"
        ],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

    assert topic_path.exists()

    required_files = [
        "concept.json",
        "examples.json",
        "mistakes.json",
        "relations.json"
    ]

    for filename in required_files:
        assert (topic_path / filename).exists()


def test_validate_created_topic():

    topic_path = (
        "data/knowledge/units/"
        "test_subject/"
        "grade12/"
        "test_topic"
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/validate_knowledge.py",
            topic_path
        ],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

    assert "Knowledge package is valid" in result.stdout


def test_check_links():

    topic_path = (
        "data/knowledge/units/"
        "test_subject/"
        "grade12/"
        "test_topic"
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/check_links.py",
            topic_path
        ],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

    assert "Relations are valid" in result.stdout