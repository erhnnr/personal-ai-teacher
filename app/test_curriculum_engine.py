from curriculum_engine import (
    get_subject_topics,
    is_topic_available,
    get_next_topic,
    get_previous_topics
)


def test_get_subject_topics():

    topics = get_subject_topics(
        "Matematik",
        9
    )

    assert "Fonksiyonlar" in topics


def test_topic_available():

    result = is_topic_available(
        "Matematik",
        9,
        "Fonksiyonlar"
    )

    assert result is True


def test_topic_not_available():

    result = is_topic_available(
        "Matematik",
        9,
        "Limit"
    )

    assert result is False


def test_get_next_topic():

    result = get_next_topic(
        "Matematik",
        9,
        "Sayılar"
    )

    assert result == "Bölme ve Bölünebilme"


def test_get_previous_topics():

    result = get_previous_topics(
        "Matematik",
        9,
        "Fonksiyonlar"
    )

    assert "Denklemler" in result
    assert "Eşitsizlikler" in result