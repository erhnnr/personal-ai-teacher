from solution_engine import (
    get_all_solutions,
    get_solution_by_id,
    get_solution_for_question
)



def test_load_solutions():

    data = get_all_solutions()

    assert len(data) > 0



def test_get_solution_id():

    data = get_solution_by_id(
        "MAT12-LIMIT-S001"
    )

    assert data is not None

    assert data["final_answer"] == "B"



def test_question_solution_link():

    question = {

        "solution_id":
        "MAT12-LIMIT-S001"

    }


    solution = get_solution_for_question(
        question
    )


    assert solution is not None