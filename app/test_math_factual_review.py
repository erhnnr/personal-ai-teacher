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
                        "∫x^2 dx = (1/3)x^3 + C"
                    ),
                },
                {
                    "id": "E2",
                    "question": (
                        "f(x) = 3x + 2 fonksiyonunun "
                        "belirli integralini [1,4] "
                        "aralığında bulun."
                    ),
                    "answer": (
                        "∫[1 to 4] (3x + 2) dx = 28.5"
                    ),
                },
            ],
        },
    )

    report = review_draft(
        tmp_path
    )

    assert (
        report["failed"]
        == 0
    )

    assert (
        report["passed"]
        == 2
    )


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
                }
            ],
        },
    )

    report = review_draft(
        tmp_path
    )

    assert (
        report["status"]
        == "FAIL"
    )

    assert (
        report["failed"]
        == 1
    )

    result = report[
        "results"
    ][0]

    assert (
        result["expected"]
        == "57/2"
    )


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
                }
            ],
        },
    )

    report = review_draft(
        tmp_path
    )

    assert (
        report["status"]
        == "FAIL"
    )

    assert (
        report["failed"]
        == 1
    )