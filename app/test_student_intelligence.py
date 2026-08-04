from student_intelligence import (
    create_student_insight
)


def test_student_intelligence():


    logs = [

        {
            "topic": "Fonksiyonlar",
            "duration": 60,
            "score": 50
        },

        {
            "topic": "Sayılar",
            "duration": 45,
            "score": 90
        }

    ]


    insight = create_student_insight(
        logs
    )


    assert "Fonksiyonlar" in insight.weak_topics

    assert "Sayılar" in insight.strong_topics

    assert insight.total_study_time == 105