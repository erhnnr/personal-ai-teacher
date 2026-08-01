from session import LearningSession


def test_learning_session():


    session = LearningSession(
        "Fonksiyonlar konusunu anlat."
    )


    session.start()


    assert session.plan is not None

    assert session.quiz is not None



def test_session_complete():


    session = LearningSession(
        "Fonksiyonlar konusunu anlat."
    )


    session.start()


    session.quiz.answers = [
        "4",
        "6"
    ]

    session.quiz.questions = [
        "2+2 kaçtır?",
        "3+3 kaçtır?"
    ]


    result = session.complete(
        [
            "4",
            "5"
        ]
    )


    assert result.total_questions == 2

    assert result.correct_answers == 1

    assert result.wrong_answers == 1

    assert result.score == 50