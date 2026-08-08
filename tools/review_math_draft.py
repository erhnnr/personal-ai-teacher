"""
Deterministic Mathematics Draft Reviewer

Purpose:
Validate machine-checkable mathematical examples
inside generated knowledge drafts.

Preferred format:
Each mathematical example contains a "validation"
object governed by:

data/knowledge/schemas/math_example_validation.schema.json

Important:
- The LLM's expected value is NOT trusted.
- SymPy or Python computes the real result.
- PASS means only the supported mathematical claim passed.
- PASS does NOT make the whole knowledge unit VERIFIED.
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

import sympy as sp

from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


TRANSFORMATIONS = (
    standard_transformations
    + (
        implicit_multiplication_application,
    )
)


def load_json(path):
    return json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )


def normalize_math_text(value):
    value = str(value).strip()

    replacements = {
        "^": "**",
        "−": "-",
        "–": "-",
        "π": "pi",
        "√": "sqrt",
    }

    for old, new in replacements.items():
        value = value.replace(
            old,
            new,
        )

    return value


def validate_expression_text(text):
    """
    Reject obviously unsafe or non-mathematical input
    before parse_expr is used.
    """

    text = str(text)

    banned = (
        "__",
        "import",
        "exec",
        "eval",
        "open(",
        "os.",
        "sys.",
        "subprocess",
        "lambda",
    )

    lowered = text.lower()

    for item in banned:
        if item in lowered:
            raise ValueError(
                "Unsafe mathematical expression."
            )


def parse_value(
    value,
    variables=None,
):
    if isinstance(
        value,
        (int, float),
    ):
        return sp.sympify(
            value
        )

    text = normalize_math_text(
        value
    )

    validate_expression_text(
        text
    )

    local_dict = {
        "pi": sp.pi,
        "sqrt": sp.sqrt,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "E": sp.E,
        "I": sp.I,
        "i": sp.I,
    }

    if variables:
        for name in variables:
            local_dict[name] = sp.Symbol(
                name,
                real=True,
            )

    return parse_expr(
        text,
        local_dict=local_dict,
        transformations=TRANSFORMATIONS,
        evaluate=True,
    )


def equivalent(
    actual,
    expected,
):
    try:
        difference = sp.simplify(
            actual
            - expected
        )

        return difference == 0

    except Exception:
        return False


def result_pass(
    actual,
    expected,
    extra=None,
):
    result = {
        "status": "PASS",
        "computed": str(actual),
        "expected": str(expected),
    }

    if extra:
        result.update(
            extra
        )

    return result


def result_fail(
    actual,
    expected,
    reason,
    extra=None,
):
    result = {
        "status": "FAIL",
        "reason": reason,
        "computed": str(actual),
        "expected": str(expected),
    }

    if extra:
        result.update(
            extra
        )

    return result


def result_unverified(
    reason,
):
    return {
        "status": "UNVERIFIED",
        "reason": reason,
    }


def get_variable(
    validation,
):
    name = validation.get(
        "variable",
        "x",
    )

    if not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_]*",
        name,
    ):
        raise ValueError(
            "Invalid variable name."
        )

    return sp.Symbol(
        name,
        real=True,
    )


def review_arithmetic(
    validation,
):
    expression = parse_value(
        validation["expression"]
    )

    expected = parse_value(
        validation["expected"]
    )

    actual = sp.simplify(
        expression
    )

    if equivalent(
        actual,
        expected,
    ):
        return result_pass(
            actual,
            expected,
        )

    return result_fail(
        actual,
        expected,
        "Arithmetic result is incorrect.",
    )


def review_equation(
    validation,
):
    variable = get_variable(
        validation
    )

    variable_name = str(
        variable
    )

    lhs = parse_value(
        validation["expression"],
        [variable_name],
    )

    rhs = parse_value(
        validation["rhs"],
        [variable_name],
    )

    solutions = sp.solve(
        sp.Eq(
            lhs,
            rhs,
        ),
        variable,
    )

    expected_raw = validation[
        "expected"
    ]

    if isinstance(
        expected_raw,
        list,
    ):
        expected = [
            parse_value(
                item,
                [variable_name],
            )
            for item in expected_raw
        ]

    else:
        expected = [
            parse_value(
                expected_raw,
                [variable_name],
            )
        ]

    solutions = sorted(
        solutions,
        key=str,
    )

    expected = sorted(
        expected,
        key=str,
    )

    if (
        len(solutions)
        == len(expected)
        and all(
            equivalent(
                a,
                b,
            )
            for a, b in zip(
                solutions,
                expected,
            )
        )
    ):
        return {
            "status": "PASS",
            "computed": [
                str(item)
                for item in solutions
            ],
            "expected": [
                str(item)
                for item in expected
            ],
        }

    return {
        "status": "FAIL",
        "reason": (
            "Equation solution is incorrect."
        ),
        "computed": [
            str(item)
            for item in solutions
        ],
        "expected": [
            str(item)
            for item in expected
        ],
    }


def review_inequality(
    validation,
):
    """
    Inequality output formats can vary substantially.
    We do not claim deterministic verification until
    the expected solution-set contract is stricter.
    """

    return result_unverified(
        "Inequality validation requires a structured "
        "solution-set contract."
    )


def review_polynomial_remainder(
    validation,
):
    variable = get_variable(
        validation
    )

    variable_name = str(
        variable
    )

    polynomial = parse_value(
        validation["polynomial"],
        [variable_name],
    )

    root = parse_value(
        validation["divisor_root"],
        [variable_name],
    )

    expected = parse_value(
        validation["expected"],
        [variable_name],
    )

    actual = sp.simplify(
        polynomial.subs(
            variable,
            root,
        )
    )

    if equivalent(
        actual,
        expected,
    ):
        return result_pass(
            actual,
            expected,
        )

    return result_fail(
        actual,
        expected,
        "Polynomial remainder is incorrect.",
    )


def review_function_value(
    validation,
):
    variable = get_variable(
        validation
    )

    variable_name = str(
        variable
    )

    function = parse_value(
        validation["function"],
        [variable_name],
    )

    input_value = parse_value(
        validation["input"],
        [variable_name],
    )

    expected = parse_value(
        validation["expected"],
        [variable_name],
    )

    actual = sp.simplify(
        function.subs(
            variable,
            input_value,
        )
    )

    if equivalent(
        actual,
        expected,
    ):
        return result_pass(
            actual,
            expected,
        )

    return result_fail(
        actual,
        expected,
        "Function value is incorrect.",
    )


def parse_interval_expected(
    expected,
):
    if (
        not isinstance(
            expected,
            list,
        )
        or len(expected) != 2
    ):
        raise ValueError(
            "Function range expected value "
            "must be [minimum, maximum]."
        )

    return (
        parse_value(
            expected[0]
        ),
        parse_value(
            expected[1]
        ),
    )


def review_function_range(
    validation,
):
    variable = get_variable(
        validation
    )

    variable_name = str(
        variable
    )

    function = parse_value(
        validation["function"],
        [variable_name],
    )

    domain = validation[
        "domain"
    ]

    if (
        not isinstance(
            domain,
            list,
        )
        or len(domain) != 2
    ):
        return result_unverified(
            "Function domain must be [lower, upper]."
        )

    lower = parse_value(
        domain[0],
        [variable_name],
    )

    upper = parse_value(
        domain[1],
        [variable_name],
    )

    expected_min, expected_max = (
        parse_interval_expected(
            validation["expected"]
        )
    )

    derivative = sp.diff(
        function,
        variable,
    )

    critical_points = sp.solve(
        sp.Eq(
            derivative,
            0,
        ),
        variable,
    )

    candidates = [
        lower,
        upper,
    ]

    for point in critical_points:

        try:
            inside = (
                sp.simplify(
                    point >= lower
                )
                and
                sp.simplify(
                    point <= upper
                )
            )

        except Exception:
            inside = False

        if inside:
            candidates.append(
                point
            )

    values = [
        sp.simplify(
            function.subs(
                variable,
                point,
            )
        )
        for point in candidates
    ]

    actual_min = min(
        values,
        key=lambda value: float(
            sp.N(value)
        ),
    )

    actual_max = max(
        values,
        key=lambda value: float(
            sp.N(value)
        ),
    )

    correct = (
        equivalent(
            actual_min,
            expected_min,
        )
        and
        equivalent(
            actual_max,
            expected_max,
        )
    )

    if correct:
        return {
            "status": "PASS",
            "computed": [
                str(actual_min),
                str(actual_max),
            ],
            "expected": [
                str(expected_min),
                str(expected_max),
            ],
        }

    return {
        "status": "FAIL",
        "reason": (
            "Function range is incorrect."
        ),
        "computed": [
            str(actual_min),
            str(actual_max),
        ],
        "expected": [
            str(expected_min),
            str(expected_max),
        ],
    }


def review_combination(
    validation,
):
    n = int(
        validation["n"]
    )

    r = int(
        validation["r"]
    )

    expected = parse_value(
        validation["expected"]
    )

    actual = sp.Integer(
        math.comb(
            n,
            r,
        )
    )

    if equivalent(
        actual,
        expected,
    ):
        return result_pass(
            actual,
            expected,
        )

    return result_fail(
        actual,
        expected,
        "Combination result is incorrect.",
    )


def review_permutation(
    validation,
):
    n = int(
        validation["n"]
    )

    r = int(
        validation["r"]
    )

    actual = sp.Integer(
        math.factorial(n)
        //
        math.factorial(
            n - r
        )
    )

    expected = parse_value(
        validation["expected"]
    )

    if equivalent(
        actual,
        expected,
    ):
        return result_pass(
            actual,
            expected,
        )

    return result_fail(
        actual,
        expected,
        "Permutation result is incorrect.",
    )


def review_trigonometric_value(
    validation,
):
    function_name = validation[
        "trig_function"
    ]

    angle = parse_value(
        validation["angle"]
    )

    unit = validation[
        "angle_unit"
    ]

    expected = parse_value(
        validation["expected"]
    )

    if unit == "degree":
        angle = (
            angle
            * sp.pi
            / 180
        )

    functions = {
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
    }

    function = functions[
        function_name
    ]

    actual = sp.simplify(
        function(
            angle
        )
    )

    if equivalent(
        actual,
        expected,
    ):
        return result_pass(
            actual,
            expected,
        )

    return result_fail(
        actual,
        expected,
        "Trigonometric value is incorrect.",
    )


def review_distance_2d(
    validation,
):
    point_a = validation[
        "point_a"
    ]

    point_b = validation[
        "point_b"
    ]

    ax = parse_value(
        point_a[0]
    )

    ay = parse_value(
        point_a[1]
    )

    bx = parse_value(
        point_b[0]
    )

    by = parse_value(
        point_b[1]
    )

    expected = parse_value(
        validation["expected"]
    )

    actual = sp.simplify(
        sp.sqrt(
            (bx - ax) ** 2
            + (by - ay) ** 2
        )
    )

    if equivalent(
        actual,
        expected,
    ):
        return result_pass(
            actual,
            expected,
        )

    return result_fail(
        actual,
        expected,
        "2D distance result is incorrect.",
    )


def review_indefinite_integral(
    validation,
):
    variable = get_variable(
        validation
    )

    variable_name = str(
        variable
    )

    expression = parse_value(
        validation["expression"],
        [variable_name],
    )

    expected_raw = validation.get(
        "expected"
    )

    if expected_raw is None:
        return result_unverified(
            "Indefinite integral requires an expected "
            "antiderivative in machine-checkable mode."
        )

    expected = parse_value(
        expected_raw,
        [variable_name],
    )

    derivative = sp.simplify(
        sp.diff(
            expected,
            variable,
        )
    )

    if equivalent(
        derivative,
        expression,
    ):
        return {
            "status": "PASS",
            "computed_derivative": str(
                derivative
            ),
            "expected_integrand": str(
                expression
            ),
        }

    return {
        "status": "FAIL",
        "reason": (
            "Expected antiderivative does not "
            "differentiate to the integrand."
        ),
        "computed_derivative": str(
            derivative
        ),
        "expected_integrand": str(
            expression
        ),
    }


def review_definite_integral(
    validation,
):
    variable = get_variable(
        validation
    )

    variable_name = str(
        variable
    )

    expression = parse_value(
        validation["expression"],
        [variable_name],
    )

    lower = parse_value(
        validation["lower"],
        [variable_name],
    )

    upper = parse_value(
        validation["upper"],
        [variable_name],
    )

    expected = parse_value(
        validation["expected"],
        [variable_name],
    )

    actual = sp.simplify(
        sp.integrate(
            expression,
            (
                variable,
                lower,
                upper,
            ),
        )
    )

    if equivalent(
        actual,
        expected,
    ):
        return result_pass(
            actual,
            expected,
        )

    return result_fail(
        actual,
        expected,
        "Definite integral result is incorrect.",
    )


REVIEWERS = {
    "arithmetic": review_arithmetic,
    "equation": review_equation,
    "inequality": review_inequality,
    "polynomial_remainder": (
        review_polynomial_remainder
    ),
    "function_value": review_function_value,
    "function_range": review_function_range,
    "combination": review_combination,
    "permutation": review_permutation,
    "trigonometric_value": (
        review_trigonometric_value
    ),
    "distance_2d": review_distance_2d,
    "indefinite_integral": (
        review_indefinite_integral
    ),
    "definite_integral": (
        review_definite_integral
    ),
}


def review_validation(
    validation,
):
    if not isinstance(
        validation,
        dict,
    ):
        return result_unverified(
            "Validation block is missing or invalid."
        )

    validation_type = validation.get(
        "type"
    )

    if not validation_type:
        return result_unverified(
            "Validation type is missing."
        )

    reviewer = REVIEWERS.get(
        validation_type
    )

    if reviewer is None:
        return result_unverified(
            f"Unsupported validation type: "
            f"{validation_type}"
        )

    try:
        return reviewer(
            validation
        )

    except KeyError as exc:
        return result_unverified(
            f"Required validation field missing: "
            f"{exc}"
        )

    except Exception as exc:
        return result_unverified(
            f"Deterministic validation failed safely: "
            f"{exc}"
        )


def review_example(
    example,
):
    validation = example.get(
        "validation"
    )

    if validation is None:
        return result_unverified(
            "Example has no machine-checkable "
            "validation block."
        )

    return review_validation(
        validation
    )


def review_draft(
    draft_path,
):
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
            "error": "examples.json not found",
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
        result["status"] == "PASS"
        for result in results
    )

    failed = sum(
        result["status"] == "FAIL"
        for result in results
    )

    unverified = sum(
        result["status"] == "UNVERIFIED"
        for result in results
    )

    reviewed = len(
        results
    )

    if failed > 0:
        overall = "FAIL"

    elif (
        passed > 0
        and unverified == 0
    ):
        overall = "PASS"

    elif passed > 0:
        overall = (
            "PASS_WITH_LIMITED_SCOPE"
        )

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
        f"STATUS     : {report['status']}"
    )

    print(
        f"REVIEWED   : {report['reviewed']}"
    )

    print(
        f"PASS       : {report['passed']}"
    )

    print(
        f"FAIL       : {report['failed']}"
    )

    print(
        f"UNVERIFIED : {report['unverified']}"
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

        if "computed" in result:
            print(
                f"  Computed: "
                f"{result['computed']}"
            )

        if "expected" in result:
            print(
                f"  Expected: "
                f"{result['expected']}"
            )

    print()

    print(
        "NOTE:"
    )

    print(
        "PASS validates only supported "
        "machine-checkable mathematics."
    )

    print(
        "It does not make the draft VERIFIED."
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "draft_path",
        help="Path to knowledge draft",
    )

    args = parser.parse_args()

    report = review_draft(
        args.draft_path
    )

    print_report(
        report
    )

    if report["status"] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()