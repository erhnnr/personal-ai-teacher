"""
EID-006 Question Engine

Purpose:
Retrieve structured questions from knowledge base.
"""

import json
from pathlib import Path


QUESTION_DIR = (
    Path(__file__).parent.parent
    / "data"
    / "knowledge"
    / "questions"
)



def load_questions_file(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)



def find_question_files():

    if not QUESTION_DIR.exists():

        return []



    return list(
        QUESTION_DIR.rglob(
            "questions.json"
        )
    )



def get_all_questions():

    questions = []


    for file in find_question_files():

        try:

            data = load_questions_file(file)

            questions.extend(data)


        except Exception:

            continue


    return questions



def get_questions(
    subject,
    grade,
    topic,
    difficulty=None
):

    questions = get_all_questions()

    result = []


    difficulty_map = {
        "basic": [
            "basic",
            "easy"
        ],
        "easy": [
            "basic",
            "easy"
        ],
        "medium": [
            "medium",
            "intermediate"
        ],
        "hard": [
            "hard",
            "advanced"
        ]
    }


    allowed_difficulties = None


    if difficulty:

        allowed_difficulties = difficulty_map.get(
            difficulty,
            [difficulty]
        )


    for question in questions:


        if question.get("subject") != subject:
            continue


        if question.get("grade") != grade:
            continue


        if question.get("topic") != topic:
            continue


        if allowed_difficulties:

            if question.get("difficulty") not in allowed_difficulties:
                continue


        result.append(question)


    return result


def get_question_by_id(
    question_id
):

    questions = get_all_questions()


    for question in questions:

        if question.get("id") == question_id:

            return question


    return None