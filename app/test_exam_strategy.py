from student import Student
from exam_strategy import create_exam_strategy



def test_exam_strategy():


    student = Student()


    strategy = create_exam_strategy(
        student
    )


    assert strategy.priority == "foundation"

    assert "Matematik" in strategy.focus_subjects

    assert len(strategy.daily_plan) > 0