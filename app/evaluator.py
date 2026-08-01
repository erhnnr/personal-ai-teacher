"""
EIE-018 Evaluator Engine

Purpose:
Evaluate quiz answers.
"""


from dataclasses import dataclass, field


@dataclass
class EvaluationResult:

    total_questions: int

    correct_answers: int

    wrong_answers: int

    score: float

    weak_topics: list = field(default_factory=list)



def evaluate_quiz(quiz, student_answers):

    total = len(quiz.questions)

    correct = 0

    wrong = 0


    for index, answer in enumerate(student_answers):

        if index < len(quiz.answers):

            if answer == quiz.answers[index]:

                correct += 1

            else:

                wrong += 1


    score = 0

    if total > 0:

        score = (correct / total) * 100


    return EvaluationResult(

        total_questions=total,

        correct_answers=correct,

        wrong_answers=wrong,

        score=score

    )