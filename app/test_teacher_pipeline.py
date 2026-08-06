from teacher_pipeline import run_lesson



def test_teacher_pipeline():

    result = run_lesson(
        "Matematik",
        12,
        "Limit"
    )


    assert result is not None

    assert result["topic"] == "Limit"

    assert len(result["questions"]) > 0
