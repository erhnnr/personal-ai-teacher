"""
EIE-015 Quiz Engine

Purpose:
Create and manage quizzes from lesson plans.
"""


from dataclasses import dataclass, field


@dataclass
class Quiz:

    topic: str

    difficulty: str = "normal"

    questions: list = field(default_factory=list)

    answers: list = field(default_factory=list)



def create_quiz(topic, difficulty="normal"):

    return Quiz(
        topic=topic,
        difficulty=difficulty
    )



def create_quiz_from_plan(plan):

    topic = plan.topic

    if not topic:

        topic = plan.topics[0] if plan.topics else "Genel"


    return Quiz(
        topic=topic,
        difficulty="normal"
    )



def add_question(quiz, question, answer=""):

    quiz.questions.append(question)

    quiz.answers.append(answer)

    return quiz