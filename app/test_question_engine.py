from question_engine import (
    get_all_questions,
    get_questions,
    get_question_by_id
)


def test_load_questions():

    questions = get_all_questions()

    assert len(questions) > 0



def test_get_limit_questions():

    result = get_questions(
        "Matematik",
        12,
        "Limit"
    )

    assert len(result) > 0

    assert result[0]["topic"] == "Limit"



def test_filter_difficulty():

    result = get_questions(
        "Matematik",
        12,
        "Limit",
        "basic"
    )

    assert len(result) >= 1



def test_get_question_id():

    result = get_question_by_id(
        "MAT12-LIMIT-Q001"
    )

    assert result is not None

    assert result["answer"] == "B"