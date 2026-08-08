from curriculum_engine import (
    get_topic_info,
    load_curriculum_data,
)


def test_curriculum_intelligence():

    topic = get_topic_info(
        "AYT",
        "Matematik",
        "Limit"
    )

    assert topic is not None

    assert topic["topic"] == "Limit"

    assert "Türev" in topic["next_topics"]

    assert topic["priority"] == "critical"


def test_tyt_matematik_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "TYT"
        and item.get("subject") == "Matematik"
    ]

    assert len(topics) == 15


def test_tyt_matematik_topic_metadata():

    topic = get_topic_info(
        "TYT",
        "Matematik",
        "Problemler"
    )

    assert topic is not None

    assert topic["topic"] == "Problemler"

    assert topic["priority"] == "critical"

    assert topic["difficulty"] == "hard"

    assert "Hareket problemleri" in topic["subtopics"]

    assert (
        "Denklemler ve Eşitsizlikler"
        in topic["dependencies"]
    )