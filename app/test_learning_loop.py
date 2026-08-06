from learning_loop import analyze_result
from evaluator import EvaluationResult



def test_learning_loop():


    result = EvaluationResult(

        total_questions=10,

        correct_answers=5,

        wrong_answers=5,

        score=50,

        mastery_level="developing"

    )


    decision = analyze_result(
        result,
        "Limit"
    )


    assert decision.topic == "Limit"

    assert decision.status == "developing"

    assert len(decision.mistakes) > 0