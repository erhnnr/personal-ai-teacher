from planner import create_plan


def test_create_math_plan():

    plan = create_plan(
        "Fonksiyonlar konusunu anlat."
    )

    assert plan.subject == "Matematik"
    assert plan.topic == "Fonksiyonlar"


def test_limit_grade_rule():

    plan = create_plan(
        "Limit konusunu anlat."
    )

    assert plan.subject == "Matematik"