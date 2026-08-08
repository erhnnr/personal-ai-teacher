import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_PATH = PROJECT_ROOT / "tools"

if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(
        0,
        str(TOOLS_PATH),
    )


import knowledge_coverage


def test_coverage_total_matches_curriculum():

    results = (
        knowledge_coverage
        .scan_coverage()
    )

    assert len(results) == 165


def test_coverage_status_values():

    results = (
        knowledge_coverage
        .scan_coverage()
    )

    allowed = {
        "READY",
        "NOT_READY",
        "MISSING",
    }

    assert all(
        result["status"] in allowed
        for result in results
    )


def test_limit_is_ready():

    results = (
        knowledge_coverage
        .scan_coverage()
    )

    matches = [
        result
        for result in results
        if (
            result["subject"]
            == "Matematik"
            and
            result["topic"]
            == "Limit"
            and
            result["exam"]
            == "AYT"
        )
    ]

    assert len(matches) == 1

    assert (
        matches[0]["status"]
        == "READY"
    )


def test_sinir_sistemi_is_not_ready():

    results = (
        knowledge_coverage
        .scan_coverage()
    )

    matches = [
        result
        for result in results
        if (
            result["subject"]
            == "Biyoloji"
            and
            result["topic"]
            == "Sinir Sistemi"
            and
            result["exam"]
            == "AYT"
        )
    ]

    assert len(matches) == 1

    assert (
        matches[0]["status"]
        in {
            "MISSING",
            "NOT_READY",
        }
    )


def test_summary_total():

    results = (
        knowledge_coverage
        .scan_coverage()
    )

    totals, grouped = (
        knowledge_coverage
        .summarize(results)
    )

    assert totals["TOTAL"] == 165

    assert (
        totals["READY"]
        + totals["NOT_READY"]
        + totals["MISSING"]
        == 165
    )

    assert grouped