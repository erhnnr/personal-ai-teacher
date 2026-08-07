"""
EID-009A Student Session

Purpose:
Run a complete student learning session.
"""


from teacher_pipeline import run_lesson
from evaluator import evaluate_quiz



def start_session(
    subject,
    grade,
    topic
):

    lesson = run_lesson(
        subject,
        grade,
        topic
    )


    if lesson is None:

        return None



    return {

        "topic": topic,

        "questions":
            lesson["questions"],

        "solutions":
            lesson["solutions"],

        "knowledge":
            lesson["knowledge"]

    }