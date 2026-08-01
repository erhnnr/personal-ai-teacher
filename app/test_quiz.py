from quiz import create_quiz, add_question


def test_create_quiz():

    quiz = create_quiz(
        "Fonksiyonlar"
    )

    assert quiz.topic == "Fonksiyonlar"

    assert quiz.questions == []


def test_add_question():

    quiz = create_quiz(
        "Fonksiyonlar"
    )

    add_question(
        quiz,
        "f(x)=2x+1 için x=3 kaçtır?",
        "7"
    )

    assert len(quiz.questions) == 1

    assert quiz.answers[0] == "7"