from student_intelligence_v2 import analyze_topic_result



def test_weak_topic_detection():

    result = analyze_topic_result(
        "Limit",
        45,
        2
    )


    assert result["status"] == "weak"

    assert result["review_needed"] is True



def test_mastered_topic_detection():

    result = analyze_topic_result(
        "Fonksiyonlar",
        90,
        3
    )


    assert result["status"] == "mastered"

    assert result["review_needed"] is False