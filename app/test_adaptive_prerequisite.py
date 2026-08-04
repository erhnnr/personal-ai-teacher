from adaptive_planner import check_prerequisite
from student import Student


def test_limit_requires_function():

    student = Student()

    student.weak_topics = [
        "Fonksiyonlar"
    ]


    result = check_prerequisite(
        "Limit",
        student
    )


    assert result == "Fonksiyonlar"