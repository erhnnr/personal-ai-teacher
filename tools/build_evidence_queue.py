"""
Knowledge Factory V2 — Phase 5A Bulk Evidence Queue
Fix 1: test-safe evidence path serialization.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = PROJECT_ROOT / "app"
TOOLS_PATH = PROJECT_ROOT / "tools"

for path in (APP_PATH, TOOLS_PATH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from curriculum_engine import load_curriculum_data
from evidence_factory import validate_evidence_package


EVIDENCE_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "evidence"
)

QUEUE_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "work_queue"
)

DEFAULT_QUEUE_PATH = (
    QUEUE_ROOT
    / "evidence_queue.json"
)


def slugify(value):
    value = str(value).strip()

    replacements = {
        "İ": "I",
        "Ç": "C",
        "Ğ": "G",
        "Ö": "O",
        "Ş": "S",
        "Ü": "U",
        "ı": "i",
        "ç": "c",
        "ğ": "g",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = value.lower()
    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    return value.strip("_")


def normalize(value):
    return str(value).strip().casefold()


def load_json(path):
    return json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def evidence_path_for(
    subject,
    grade,
    topic,
):
    return (
        EVIDENCE_ROOT
        / slugify(subject)
        / f"grade{grade}"
        / slugify(topic)
        / "evidence.json"
    )


def display_path(path):
    """
    Prefer a project-relative path in normal runtime.
    During tests or alternate roots, fall back to the absolute path
    instead of raising ValueError.
    """

    path = Path(path)

    try:
        return str(
            path.relative_to(
                PROJECT_ROOT
            )
        )
    except ValueError:
        return str(
            path
        )


def infer_grade(record, default_grade="12"):
    grade = (
        record.get("grade")
        or record.get("class")
        or record.get("sinif")
        or default_grade
    )

    return str(grade)


def source_ids_from_evidence(evidence):
    source_ids = []

    for source in evidence.get(
        "sources",
        [],
    ):
        source_id = source.get(
            "source_id"
        )

        if (
            source_id
            and source_id not in source_ids
        ):
            source_ids.append(
                source_id
            )

    for claim in evidence.get(
        "claims",
        [],
    ):
        for ref in claim.get(
            "source_refs",
            [],
        ):
            source_id = ref.get(
                "source_id"
            )

            if (
                source_id
                and source_id not in source_ids
            ):
                source_ids.append(
                    source_id
                )

    return source_ids


def classify_record(
    record,
    default_grade="12",
):
    exam = record.get("exam")
    subject = record.get("subject")
    topic = record.get("topic")
    grade = infer_grade(
        record,
        default_grade=default_grade,
    )

    path = evidence_path_for(
        subject,
        grade,
        topic,
    )

    item = {
        "exam": exam,
        "subject": subject,
        "grade": grade,
        "topic": topic,
        "priority": record.get(
            "priority"
        ),
        "evidence_status": "MISSING",
        "source_ids": [],
        "evidence_path": display_path(
            path
        ),
        "next_action": "FIND_OFFICIAL_SOURCE",
    }

    if not path.exists():
        return item

    try:
        evidence = load_json(
            path
        )
    except Exception as exc:
        item[
            "evidence_status"
        ] = "DRAFT"
        item[
            "next_action"
        ] = "FIX_EVIDENCE_FILE"
        item[
            "error"
        ] = str(exc)
        return item

    item[
        "source_ids"
    ] = source_ids_from_evidence(
        evidence
    )

    try:
        valid = validate_evidence_package(
            evidence
        )
    except Exception as exc:
        valid = False
        item[
            "error"
        ] = str(exc)

    identity_matches = (
        normalize(
            evidence.get("exam")
        )
        == normalize(exam)
        and normalize(
            evidence.get("subject")
        )
        == normalize(subject)
        and normalize(
            evidence.get("topic")
        )
        == normalize(topic)
        and str(
            evidence.get("grade")
        )
        == grade
    )

    if (
        valid is True
        and identity_matches
        and evidence.get(
            "status"
        )
        == "EVIDENCE_READY"
    ):
        item[
            "evidence_status"
        ] = "READY"
        item[
            "next_action"
        ] = "COMPILE_FACTUAL_DRAFT"
        return item

    item[
        "evidence_status"
    ] = "DRAFT"
    item[
        "next_action"
    ] = (
        "FIX_EVIDENCE_IDENTITY"
        if not identity_matches
        else "REVIEW_EVIDENCE"
    )

    return item


def build_queue(
    records=None,
    default_grade="12",
):
    if records is None:
        records = load_curriculum_data()

    items = [
        classify_record(
            record,
            default_grade=default_grade,
        )
        for record in records
    ]

    status_counts = Counter(
        item[
            "evidence_status"
        ]
        for item in items
    )

    exam_counts = Counter(
        item.get("exam")
        for item in items
    )

    subject_counts = Counter(
        (
            item.get("exam"),
            item.get("subject"),
        )
        for item in items
    )

    queue = {
        "version": "1.0",
        "kind": "EVIDENCE_WORK_QUEUE",
        "total_topics": len(
            items
        ),
        "summary": {
            "ready": status_counts[
                "READY"
            ],
            "draft": status_counts[
                "DRAFT"
            ],
            "missing": status_counts[
                "MISSING"
            ],
        },
        "by_exam": {
            str(exam): count
            for exam, count in sorted(
                exam_counts.items(),
                key=lambda pair: str(
                    pair[0]
                ),
            )
        },
        "by_exam_subject": [
            {
                "exam": exam,
                "subject": subject,
                "count": count,
            }
            for (
                exam,
                subject,
            ), count in sorted(
                subject_counts.items(),
                key=lambda pair: (
                    str(
                        pair[0][0]
                    ),
                    str(
                        pair[0][1]
                    ),
                ),
            )
        ],
        "items": items,
    }

    return queue


def write_queue(
    queue,
    output_path=DEFAULT_QUEUE_PATH,
):
    write_json(
        output_path,
        queue,
    )

    return Path(
        output_path
    )


def print_summary(queue):
    summary = queue[
        "summary"
    ]

    print("=" * 70)
    print(
        "KNOWLEDGE FACTORY V2 — PHASE 5A EVIDENCE QUEUE"
    )
    print("=" * 70)
    print(
        f"Total topics : {queue['total_topics']}"
    )
    print(
        f"READY        : {summary['ready']}"
    )
    print(
        f"DRAFT        : {summary['draft']}"
    )
    print(
        f"MISSING      : {summary['missing']}"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic evidence work queue "
            "from the full curriculum."
        )
    )

    parser.add_argument(
        "--grade",
        default="12",
        help=(
            "Fallback grade when curriculum record "
            "does not contain an explicit grade."
        ),
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_QUEUE_PATH
        ),
    )

    args = parser.parse_args()

    queue = build_queue(
        default_grade=args.grade,
    )

    output_path = write_queue(
        queue,
        args.output,
    )

    print_summary(
        queue
    )

    print(
        "QUEUE        | "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()
