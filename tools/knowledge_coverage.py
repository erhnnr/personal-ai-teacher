"""
Knowledge Coverage Scanner

Purpose:
Compare the current TYT/AYT curriculum map with
verified knowledge packages.

Statuses:
READY
NOT_READY
MISSING
"""

from collections import defaultdict
from pathlib import Path

import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = PROJECT_ROOT / "app"

if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))


from curriculum_engine import load_curriculum_data  # noqa: E402


UNITS_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "units"
)


def normalize_text(value):
    return str(value).strip().casefold()


def load_validator():
    """
    Import validator from tools directory.
    """

    tools_path = PROJECT_ROOT / "tools"

    if str(tools_path) not in sys.path:
        sys.path.insert(0, str(tools_path))

    from validate_knowledge import validate_topic

    return validate_topic


def find_topic_package(
    subject,
    topic,
):
    """
    Locate an existing knowledge package by reading
    concept.json identity rather than assuming a
    directory name.
    """

    if not UNITS_ROOT.exists():
        return None

    for concept_file in UNITS_ROOT.rglob(
        "concept.json"
    ):

        try:
            import json

            concept = json.loads(
                concept_file.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:
            continue

        if (
            normalize_text(
                concept.get("subject")
            )
            == normalize_text(subject)
            and
            normalize_text(
                concept.get("topic")
            )
            == normalize_text(topic)
        ):
            return concept_file.parent

    return None


def determine_status(
    subject,
    topic,
):
    """
    Determine curriculum topic status.
    """

    topic_path = find_topic_package(
        subject,
        topic,
    )

    if topic_path is None:
        return "MISSING", None

    validate_topic = load_validator()

    if validate_topic(
        topic_path,
        verbose=False,
    ):
        return "READY", topic_path

    return "NOT_READY", topic_path


def scan_coverage():
    """
    Scan all curriculum records.

    Returns:
        list of dictionaries
    """

    curriculum = load_curriculum_data()

    results = []

    for record in curriculum:

        status, path = determine_status(
            record["subject"],
            record["topic"],
        )

        results.append(
            {
                "exam": record["exam"],
                "subject": record["subject"],
                "topic": record["topic"],
                "priority": record.get(
                    "priority"
                ),
                "status": status,
                "path": (
                    str(path)
                    if path
                    else None
                ),
            }
        )

    return results


def summarize(
    results,
):
    """
    Produce global and exam/subject summaries.
    """

    totals = {
        "READY": 0,
        "NOT_READY": 0,
        "MISSING": 0,
    }

    grouped = defaultdict(
        lambda: {
            "READY": 0,
            "NOT_READY": 0,
            "MISSING": 0,
            "TOTAL": 0,
        }
    )

    for result in results:

        status = result["status"]

        totals[status] += 1

        key = (
            result["exam"],
            result["subject"],
        )

        grouped[key][status] += 1
        grouped[key]["TOTAL"] += 1

    totals["TOTAL"] = len(results)

    return totals, grouped


def print_report(
    results,
):
    """
    Print human-readable coverage report.
    """

    totals, grouped = summarize(
        results
    )

    print(
        "=" * 64
    )

    print(
        "KNOWLEDGE COVERAGE REPORT"
    )

    print(
        "=" * 64
    )

    print()

    print(
        f"TOTAL      {totals['TOTAL']}"
    )

    print(
        f"READY      {totals['READY']}"
    )

    print(
        f"NOT_READY  {totals['NOT_READY']}"
    )

    print(
        f"MISSING    {totals['MISSING']}"
    )

    print()

    print(
        "-" * 64
    )

    print(
        "BY EXAM / SUBJECT"
    )

    print(
        "-" * 64
    )

    for key in sorted(
        grouped
    ):

        exam, subject = key

        data = grouped[key]

        print(
            f"{exam:<4} | "
            f"{subject:<15} | "
            f"READY {data['READY']:>3} / "
            f"{data['TOTAL']:<3} | "
            f"NOT_READY {data['NOT_READY']:>3} | "
            f"MISSING {data['MISSING']:>3}"
        )

    print()

    print(
        "-" * 64
    )

    print(
        "READY TOPICS"
    )

    print(
        "-" * 64
    )

    ready_topics = [
        result
        for result in results
        if result["status"] == "READY"
    ]

    if not ready_topics:

        print(
            "None"
        )

    else:

        for result in ready_topics:

            print(
                f"{result['exam']} | "
                f"{result['subject']} | "
                f"{result['topic']}"
            )

    print()

    print(
        "-" * 64
    )

    print(
        "HIGH-PRIORITY MISSING TOPICS"
    )

    print(
        "-" * 64
    )

    priority_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        None: 4,
    }

    missing = [
        result
        for result in results
        if result["status"] != "READY"
    ]

    missing.sort(
        key=lambda item: (
            priority_order.get(
                item["priority"],
                4,
            ),
            item["exam"],
            item["subject"],
            item["topic"],
        )
    )

    for result in missing[:30]:

        print(
            f"{result['status']:<9} | "
            f"{str(result['priority']):<8} | "
            f"{result['exam']} | "
            f"{result['subject']} | "
            f"{result['topic']}"
        )


def main():

    results = scan_coverage()

    print_report(
        results
    )


if __name__ == "__main__":
    main()