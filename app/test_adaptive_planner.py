from adaptive_planner import (
    AdaptivePlan,
    create_adaptive_plan
)


class MockStudent:

    current_topic = "Fonksiyonlar"

    weak_topics = [
        "Fonksiyonlar"
    ]

    grade = 9



def test_adaptive_plan_model():

    plan = AdaptivePlan(
        action="review",
        topic="Fonksiyonlar",
        reason="Başarı düşük"
    )

    assert plan.action == "review"
    assert plan.topic == "Fonksiyonlar"



def test_weak_topic_returns_review():

    student = MockStudent()

    plan = create_adaptive_plan(
        student,
        {},
        {},
        {}
    )

    assert plan.action == "review"
    assert plan.topic == "Fonksiyonlar"



def test_low_score_returns_review():

    student = MockStudent()

    student.weak_topics = []


    progress = {

        "topics": {

            "Fonksiyonlar": {

                "best_score": 50

            }

        }

    }


    plan = create_adaptive_plan(
        student,
        progress,
        {},
        {}
    )


    assert plan.action == "review"



def test_high_score_returns_next_topic():

    class Student:

        current_topic = "Sayılar"

        weak_topics = []

        grade = 9


    progress = {

        "topics": {

            "Sayılar": {

                "best_score": 90

            }

        }

    }


    class Curriculum:

        def get_next_topic(
            self,
            subject,
            grade,
            topic
        ):

            return "Bölme ve Bölünebilme"



    student = Student()


    plan = create_adaptive_plan(
        student,
        progress,
        {},
        Curriculum()
    )


    assert plan.action == "next_topic"
    assert plan.topic == "Bölme ve Bölünebilme"