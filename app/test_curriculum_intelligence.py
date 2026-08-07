from curriculum_engine import get_topic_info



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