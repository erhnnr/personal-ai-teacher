"""
EID-007 Solution Engine

Purpose:
Retrieve structured solutions for questions.
"""

import json
from pathlib import Path


SOLUTION_DIR = (
    Path(__file__).parent.parent
    / "data"
    / "knowledge"
    / "solutions"
)


def load_solution_file(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)



def find_solution_files():

    if not SOLUTION_DIR.exists():

        return []

    return list(
        SOLUTION_DIR.rglob(
            "solutions.json"
        )
    )



def get_all_solutions():

    solutions = []


    for file in find_solution_files():

        try:

            data = load_solution_file(file)

            solutions.extend(data)


        except Exception:

            continue


    return solutions



def get_solution_by_id(
    solution_id
):

    solutions = get_all_solutions()


    for solution in solutions:

        if solution.get("id") == solution_id:

            return solution


    return None



def get_solution_for_question(
    question
):

    solution_id = question.get(
        "solution_id"
    )


    if not solution_id:

        return None


    return get_solution_by_id(
        solution_id
    )