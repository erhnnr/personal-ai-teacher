"""
Deterministic Mathematics Draft Reviewer

Purpose:
Perform factual checks on mathematical examples
inside generated knowledge drafts.

Current scope:
- indefinite polynomial/algebraic integrals
- definite polynomial/algebraic integrals

Important:
PASS means that supported machine-checkable examples passed.
It does NOT mean the entire educational package is factually verified.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import sympy as sp

from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    standard_transformations,
    parse_expr,
)


TRANSFORMATIONS = (
    standard_transformations
    + (
        implicit_multiplication_application,
    )
)

X = sp.Symbol("x")


def load_json(path):
    return json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )


def normalize_math_text(text):
    """
    Normalize common mathematical notation
    before sending it to SymPy.
    """

    text = str(text).strip()

    text = text.replace(
        "^",
        "**",
    )

    text = text.replace(
        "−",
        "-",
    )

    text = text.replace(
        "–",
        "-",
    )

    return text


def parse_math_expression(text):
    """
    Parse a basic algebraic expression.
    """

    text = normalize_math_text(
        text
    )

    return parse_expr(
        text,
        local_dict={
            "x": X,
        },
        transformations=TRANSFORMATIONS,
        evaluate=True,
    )


def extract_function_expression(question):
    """
    Extract expression after forms such as:

    f(x) = x^2
    f(x)=3x+2
    """

    match = re.search(
        r"f\s*\(\s*x\s*\)\s*=\s*(.+?)(?:\s+fonksiyonunun|\s*$)",
        question,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    expression = (
        match
        .group(1)
        .strip()
    )

    return expression


def extract_bounds(question):
    """
    Extract bounds such as:

    [1,4]
    [1, 4]
    """

    match = re.search(
        r"\[\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*\]",
        question,
    )

    if not match:
        return None

    lower = sp.Rational(
        match.group(1)
    )

    upper = sp.Rational(
        match.group(2)
    )

    return lower, upper


def extract_last_numeric_result(answer):
    """
    Read the final numeric expression after
    the last '=' sign.

    Examples:

    ... = 28.5
    ... = 57/2
    """

    if "=" not in answer:
        return None

    final_part = (
        answer
        .rsplit(
            "=",
            1,
        )[1]
        .strip()
    )

    final_part = final_part.rstrip(
        "."
    )

    try:
        return parse_math_expression(
            final_part
        )

    except Exception:
        return None


def extract_indefinite_antiderivative(answer):
    """
    Extract the right-hand side of an
    indefinite-integral answer.

    Example:

    ∫x^2 dx = (1/3)x^3 + C

    returns:
    (1/3)x^3
    """

    if "=" not in answer:
        return None

    rhs = (
        answer
        .rsplit(
            "=",
            1,
        )[1]
        .strip()
    )

    rhs = re.sub(
        r"\+\s*C\s*$",
        "",
        rhs,
        flags=re.IGNORECASE,
    )

    rhs = rhs.strip()

    try:
        return parse_math_expression(
            rhs
        )

    except Exception:
        return None


def is_definite_integral_question(question):
    lowered = question.casefold()

    return (
        "belirli integral" in lowered
        and extract_bounds(question)
        is not None
    )


def is_indefinite_integral_question(question):
    lowered = question.casefold()

    return (
        "belirsiz integral"
        in lowered
    )


def review_definite_integral(
    example,
):
    """
    Deterministically validate one definite
    integral example.
    """

    question = example.get(
        "question",
        "",
    )

    answer = example.get(
        "answer",
        "",
    )

    expression_text = (
        extract_function_expression(
            question
        )
    )

    bounds = extract_bounds(
        question
    )

    student_result = (
        extract_last_numeric_result(
            answer
        )
    )

    if (
        expression_text is None
        or bounds is None
        or student_result is None
    ):
        return {
            "status": "UNVERIFIED",
            "reason": (
                "Definite integral example "
                "could not be parsed safely."
            ),
        }

    try:

        expression = (
            parse_math_expression(
                expression_text
            )
        )

        lower, upper = bounds

        expected = sp.integrate(
            expression,
            (
                X,
                lower,
                upper,
            ),
        )

        difference = sp.simplify(
            expected
            - student_result
        )

    except Exception as exc:

        return {
            "status": "UNVERIFIED",
            "reason": (
                "SymPy evaluation failed: "
                f"{exc}"
            ),
        }

    if difference == 0:

        return {
            "status": "PASS",
            "expected": str(expected),
            "reported": str(
                student_result
            ),
        }

    return {
        "status": "FAIL",
        "reason": (
            "Definite integral result "
            "is mathematically incorrect."
        ),
        "expected": str(expected),
        "reported": str(
            student_result
        ),
    }


def review_indefinite_integral(
    example,
):
    """
    Validate an antiderivative by differentiating
    the proposed result.
    """

    question = example.get(
        "question",
        "",
    )

    answer = example.get(
        "answer",
        "",
    )

    expression_text = (
        extract_function_expression(
            question
        )
    )

    antiderivative = (
        extract_indefinite_antiderivative(
            answer
        )
    )

    if (
        expression_text is None
        or antiderivative is None
    ):
        return {
            "status": "UNVERIFIED",
            "reason": (
                "Indefinite integral example "
                "could not be parsed safely."
            ),
        }

    try:

        expression = (
            parse_math_expression(
                expression_text
            )
        )

        derived = sp.diff(
            antiderivative,
            X,
        )

        difference = sp.simplify(
            derived
            - expression
        )

    except Exception as exc:

        return {
            "status": "UNVERIFIED",
            "reason": (
                "SymPy evaluation failed: "
                f"{exc}"
            ),
        }

    if difference == 0:

        return {
            "status": "PASS",
            "expected_integrand": str(
                expression
            ),
            "derived_integrand": str(
                derived
            ),
        }

    return {
        "status": "FAIL",
        "reason": (
            "Proposed antiderivative does "
            "not differentiate to the "
            "original function."
        ),
        "expected_integrand": str(
            expression
        ),
        "derived_integrand": str(
            derived
        ),
    }


def review_example(
    example,
):
    question = example.get(
        "question",
        "",
    )

    if is_definite_integral_question(
        question
    ):
        return review_definite_integral(
            example
        )

    if is_indefinite_integral_question(
        question
    ):
        return review_indefinite_integral(
            example
        )

    return {
        "status": "UNVERIFIED",
        "reason": (
            "Example type is outside the "
            "current deterministic reviewer scope."
        ),
    }


def review_draft(
    draft_path,
):
    """
    Review machine-checkable examples from
    one knowledge draft.
    """

    draft_path = Path(
        draft_path
    )

    examples_path = (
        draft_path
        / "examples.json"
    )

    if not examples_path.exists():

        return {
            "status": "FAIL",
            "reviewed": 0,
            "passed": 0,
            "failed": 1,
            "unverified": 0,
            "results": [],
            "error": (
                "examples.json not found"
            ),
        }

    data = load_json(
        examples_path
    )

    examples = data.get(
        "examples",
        [],
    )

    results = []

    for example in examples:

        result = review_example(
            example
        )

        results.append(
            {
                "id": example.get(
                    "id"
                ),
                "question": example.get(
                    "question"
                ),
                **result,
            }
        )

    passed = sum(
        1
        for result in results
        if result["status"]
        == "PASS"
    )

    failed = sum(
        1
        for result in results
        if result["status"]
        == "FAIL"
    )

    unverified = sum(
        1
        for result in results
        if result["status"]
        == "UNVERIFIED"
    )

    reviewed = len(
        results
    )

    if failed > 0:
        overall = "FAIL"

    elif passed > 0:
        overall = "PASS_WITH_LIMITED_SCOPE"

    else:
        overall = "UNVERIFIED"

    return {
        "status": overall,
        "reviewed": reviewed,
        "passed": passed,
        "failed": failed,
        "unverified": unverified,
        "results": results,
    }


def print_report(
    report,
):
    print(
        "=" * 70
    )

    print(
        "DETERMINISTIC MATH FACTUAL REVIEW"
    )

    print(
        "=" * 70
    )

    print(
        f"STATUS     : "
        f"{report['status']}"
    )

    print(
        f"REVIEWED   : "
        f"{report['reviewed']}"
    )

    print(
        f"PASS       : "
        f"{report['passed']}"
    )

    print(
        f"FAIL       : "
        f"{report['failed']}"
    )

    print(
        f"UNVERIFIED : "
        f"{report['unverified']}"
    )

    print()

    for result in report[
        "results"
    ]:

        print(
            f"{result['status']:<10} | "
            f"{result.get('id')}"
        )

        if result.get(
            "reason"
        ):
            print(
                f"  {result['reason']}"
            )

        if (
            "expected"
            in result
        ):
            print(
                f"  Expected: "
                f"{result['expected']}"
            )

            print(
                f"  Reported: "
                f"{result['reported']}"
            )

    print()

    print(
        "NOTE:"
    )

    print(
        "This reviewer validates only supported "
        "machine-checkable mathematics."
    )

    print(
        "It does not by itself make a draft VERIFIED."
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "draft_path",
        help=(
            "Path to knowledge draft"
        ),
    )

    args = parser.parse_args()

    report = review_draft(
        args.draft_path
    )

    print_report(
        report
    )

    if report[
        "status"
    ] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()