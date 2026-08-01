from quiz_generator import generate_quiz


def test_generate_quiz():

    quiz = generate_quiz(
        "Fonksiyonlar"
    )

    assert quiz.topic == "Fonksiyonlar"

    assert len(quiz.questions) == 3

    assert len(quiz.answers) == 3