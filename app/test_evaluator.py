from quiz import create_quiz, add_question
from evaluator import evaluate_quiz


def test_evaluator():

    quiz = create_quiz(
        "Fonksiyonlar"
    )

    add_question(
        quiz,
        "2+2 kaçtır?",
        "4"
    )

    add_question(
        quiz,
        "3+3 kaçtır?",
        "6"
    )


    result = evaluate_quiz(
        quiz,
        [
            "4",
            "5"
        ]
    )


    assert result.total_questions == 2

    assert result.correct_answers == 1

    assert result.wrong_answers == 1

    assert result.score == 50