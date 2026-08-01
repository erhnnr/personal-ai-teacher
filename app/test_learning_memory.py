from session import LearningSession

from memory import load_memory

from progress import load_progress



def test_learning_updates_memory_and_progress():


    session = LearningSession(
        "Fonksiyonlar konusunu anlat."
    )


    session.start()


    session.quiz.questions = [
        "2+2 kaçtır?",
        "3+3 kaçtır?"
    ]


    session.quiz.answers = [
        "4",
        "6"
    ]


    result = session.complete(
        [
            "4",
            "5"
        ]
    )


    assert result.score == 50


    memory = load_memory()


    assert memory["last_topic"] != ""

    assert len(memory["quiz_history"]) > 0


    progress = load_progress()


    assert len(progress["topics"]) > 0