from topic_detector import detect_topic


def test_detect_math_topic():

    result = detect_topic(
        "Fonksiyonlar konusu"
    )

    assert result["subject"] == "Matematik"
    assert result["topic"] == "Fonksiyonlar"


def test_detect_grade():

    result = detect_topic(
        "Limit çalışalım"
    )

    assert result["grade"] == "12"


def test_unknown_topic():

    result = detect_topic(
        "Uzay teknolojileri"
    )


def test_uppercase_topic():

    result = detect_topic(
        "FONKSİYONLAR çalışalım"
    )

    assert result["topic"] == "Fonksiyonlar"


def test_turkish_character_topic():

    result = detect_topic(
        "İNTEGRAL konusu"
    )

    assert result["topic"] == "İntegral"


def test_empty_input():

    result = detect_topic("")

    
    assert result["topic"] is None