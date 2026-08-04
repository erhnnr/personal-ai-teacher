from diagnostic import check_topic_readiness
from student import load_student, save_student


def test_limit_readiness():

    student = load_student()

    student.weak_topics = [
        "Fonksiyonlar"
    ]

    save_student(student)


    result = check_topic_readiness(
        "Limit"
    )


    assert result["ready"] is False

    assert "Fonksiyonlar" in result["missing"]