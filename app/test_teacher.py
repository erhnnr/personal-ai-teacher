from planner import create_plan
from prompt_builder import build_prompt


def test_teacher_pipeline():

    question = "Fonksiyonlar konusunu anlat."

    plan = create_plan(question)

    prompt = build_prompt(
        question,
        plan
    )

    assert plan is not None

    assert prompt is not None

    assert "Fonksiyonlar" in prompt