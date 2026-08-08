import json
import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

TOOLS_PATH = (
    PROJECT_ROOT
    / "tools"
)

if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(
        0,
        str(TOOLS_PATH),
    )


from review_math_draft import review_draft


def write_json(
    path,
    data,
):
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_correct_integrals_pass(
    tmp_path,
):

    write_json(
        tmp_path / "examples.json",
        {
            "topic": "İntegral",
            "examples": [
                {
                    "id": "E1",
                    "question": (
                        "f(x) = x^2 fonksiyonunun "
                        "belirsiz integralini bulun."
                    ),
                    "answer": (
                        "∫x^2 dx = x^3/3 + C"
                    ),
                    "validation": {
                        "type": "indefinite_integral",
                        "expression": "x**2",
                        "variable": "x",
                        "expected": "x**3/3",
                    },
                },
                {
                    "id": "E2",
                    "question": (
                        "f(x) = 3x + 2 fonksiyonunun "
                        "belirli integralini [1,4] "
                        "aralığında bulun."
                    ),
                    "answer": (
                        "∫[1 to 4] (3x + 2) dx = 57/2"
                    ),
                    "validation": {
                        "type": "definite_integral",
                        "expression": "3*x + 2",
                        "variable": "x",
                        "lower": 1,
                        "upper": 4,
                        "expected": "57/2",
                    },
                },
            ],
        },
    )

    report = review_draft(
        tmp_path
    )

    assert report["status"] == "PASS"
    assert report["passed"] == 2
    assert report["failed"] == 0
    assert report["unverified"] == 0


def test_wrong_definite_integral_fails(
    tmp_path,
):

    write_json(
        tmp_path / "examples.json",
        {
            "topic": "İntegral",
            "examples": [
                {
                    "id": "BAD-E1",
                    "question": (
                        "f(x) = 3x + 2 fonksiyonunun "
                        "belirli integralini [1,4] "
                        "aralığında bulun."
                    ),
                    "answer": (
                        "∫[1 to 4] (3x + 2) dx = 15"
                    ),
                    "validation": {
                        "type": "definite_integral",
                        "expression": "3*x + 2",
                        "variable": "x",
                        "lower": 1,
                        "upper": 4,
                        "expected": 15,
                    },
                }
            ],
        },
    )

    report = review_draft(
        tmp_path
    )

    assert report["status"] == "FAIL"
    assert report["failed"] == 1

    result = report["results"][0]

    assert result["computed"] == "57/2"
    assert result["expected"] == "15"


def test_wrong_antiderivative_fails(
    tmp_path,
):

    write_json(
        tmp_path / "examples.json",
        {
            "topic": "İntegral",
            "examples": [
                {
                    "id": "BAD-E2",
                    "question": (
                        "f(x) = x^2 fonksiyonunun "
                        "belirsiz integralini bulun."
                    ),
                    "answer": (
                        "∫x^2 dx = x^2 + C"
                    ),
                    "validation": {
                        "type": "indefinite_integral",
                        "expression": "x**2",
                        "variable": "x",
                        "expected": "x**2",
                    },
                }
            ],
        },
    )

    report = review_draft(
        tmp_path
    )

    assert report["status"] == "FAIL"
    assert report["failed"] == 1


def test_equation_validation(
    tmp_path,
):

    write_json(
        tmp_path / "examples.json",
        {
            "topic": "Denklemler",
            "examples": [
                {
                    "id": "EQ1",
                    "question": (
                        "3x + 5 = 14 denklemini çözünüz."
                    ),
                    "answer": "x = 3",
                    "validation": {
                        "type": "equation",
                        "expression": "3*x + 5",
                        "variable": "x",
                        "relation": "=",
                        "rhs": 14,
                        "expected": 3,
                    },
                }
            ],
        },
    )

    report = review_draft(
        tmp_path
    )

    assert report["status"] == "PASS"
    assert report["passed"] == 1


def test_polynomial_wrong_remainder_fails(
    tmp_path,
):

    write_json(
        tmp_path / "examples.json",
        {
            "topic": "Polinomlar",
            "examples": [
                {
                    "id": "POL1",
                    "question": (
                        "3x^2 + 5x - 2 polinomunun "
                        "(x - 1) ile bölümünden "
                        "kalanı bulunuz."
                    ),
                    "answer": "-4",
                    "validation": {
                        "type": "polynomial_remainder",
                        "polynomial": "3*x**2 + 5*x - 2",
                        "variable": "x",
                        "divisor_root": 1,
                        "expected": -4,
                    },
                }
            ],
        },
    )

    report = review_draft(
        tmp_path
    )

    assert report["status"] == "FAIL"

    result = report["results"][0]

    assert result["computed"] == "6"
    assert result["expected"] == "-4"