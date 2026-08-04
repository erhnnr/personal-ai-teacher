from student import Student
from exam_strategy import create_exam_strategy
from daily_planner import create_daily_plan, update_daily_plan



def test_daily_plan():


    student = Student()


    strategy = create_exam_strategy(student)


    plan = create_daily_plan(
        student,
        strategy
    )


    assert len(plan.tasks) > 0

    assert plan.flexibility == "high"



def test_daily_update():


    student = Student()


    strategy = create_exam_strategy(student)


    plan = create_daily_plan(
        student,
        strategy
    )


    result = update_daily_plan(

        plan,

        [
            {
                "topic":
                "Mevcut zayıf konular"
            }
        ]

    )


    assert result is not None