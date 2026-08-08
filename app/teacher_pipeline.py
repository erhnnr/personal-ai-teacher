"""
EID-008 Teacher Pipeline

Purpose:
Connect student, knowledge, question,
solution and evaluation systems.

This is the orchestration layer.
"""

from knowledge_engine import get_learning_package
from question_engine import get_questions
from solution_engine import get_solution_by_id


def run_lesson(
    subject,
    grade,
    topic
):
    """
    Execute one learning session pipeline.
    """

    # 1. Load verified knowledge package

    knowledge = get_learning_package(
        subject,
        grade,
        topic
    )

    if knowledge is None:
        return None

    # 2. Load questions

    questions = get_questions(
        subject,
        grade,
        topic
    )

    # 3. Prepare solution information

    solutions = []

    for question in questions:

        solution_id = question.get(
            "solution_id"
        )

        if not solution_id:
            continue

        solution = get_solution_by_id(
            solution_id
        )

        if solution:
            solutions.append(
                solution
            )

    # 4. Return lesson package

    return {
        "subject": subject,
        "grade": grade,
        "topic": topic,
        "knowledge": knowledge,
        "questions": questions,
        "solutions": solutions,
    }