from student import Student
from student_intelligence import create_student_insight
from learning_decision import decide_learning_action



def test_prerequisite_decision():


    student = Student()


    student.weak_topics = [
        "Fonksiyonlar"
    ]


    insight = create_student_insight([])


    result = decide_learning_action(

        "Limit anlat",

        student,

        insight

    )


    assert result.action == "review_prerequisite"

    assert result.topic == "Fonksiyonlar"



def test_normal_teach():


    student = Student()


    insight = create_student_insight([])


    result = decide_learning_action(

        "Sayılar anlat",

        student,

        insight

    )


    assert result.action == "teach"