"""
Knowledge Factory V2 - Source Ingestion

Registers authoritative sources in:
data/knowledge/sources/source_registry.json

This module does NOT generate teaching content.
It only creates traceable source records.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent

REGISTRY_PATH = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "sources"
    / "source_registry.json"
)

SOURCE_SCHEMA_PATH = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "schemas"
    / "source_record.schema.json"
)


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


def sha256_file(path):
    digest = hashlib.sha256()

    with Path(path).open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def normalize_values(values):
    result = []
    seen = set()

    for value in values or []:
        normalized = str(value).strip()

        if not normalized:
            continue

        if normalized in seen:
            continue

        seen.add(normalized)
        result.append(normalized)

    return result


def validate_source_record(record):
    schema = load_json(
        SOURCE_SCHEMA_PATH
    )

    validator = Draft202012Validator(
        schema
    )

    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: list(
            error.path
        ),
    )

    if errors:
        first = errors[0]

        location = ".".join(
            str(item)
            for item in first.path
        )

        if location:
            location = f" at '{location}'"

        raise ValueError(
            "Source record schema failed"
            f"{location}: {first.message}"
        )

    if (
        record.get("local_path")
        and not record.get("sha256")
    ):
        raise ValueError(
            "Local source must include sha256."
        )

    return True


def build_source_record(
    source_id,
    publisher,
    title,
    source_type,
    authority_tier,
    url=None,
    local_path=None,
    exam_scope=None,
    subject_scope=None,
    grade_scope=None,
    topic_scope=None,
    notes=None,
):
    record = {
        "id": str(source_id).strip(),
        "publisher": str(publisher).strip(),
        "title": str(title).strip(),
        "source_type": str(source_type).strip(),
        "authority_tier": str(
            authority_tier
        ).strip(),
        "exam_scope": normalize_values(
            exam_scope
        ),
        "subject_scope": normalize_values(
            subject_scope
        ),
        "grade_scope": normalize_values(
            grade_scope
        ),
        "topic_scope": normalize_values(
            topic_scope
        ),
        "notes": normalize_values(
            notes
        ),
    }

    if url:
        record["url"] = str(
            url
        ).strip()

    if local_path:
        local_path = Path(
            local_path
        )

        if not local_path.is_absolute():
            local_path = (
                PROJECT_ROOT
                / local_path
            )

        if not local_path.exists():
            raise FileNotFoundError(
                f"Local source not found: "
                f"{local_path}"
            )

        record["local_path"] = str(
            local_path.relative_to(
                PROJECT_ROOT
            )
        ).replace("\\", "/")

        record["sha256"] = sha256_file(
            local_path
        )

    validate_source_record(
        record
    )

    return record


def load_registry():
    registry = load_json(
        REGISTRY_PATH
    )

    if not isinstance(
        registry.get("sources"),
        list,
    ):
        raise ValueError(
            "Source registry has no valid sources list."
        )

    return registry


def register_source(
    record,
    registry_path=None,
):
    validate_source_record(
        record
    )

    path = (
        Path(registry_path)
        if registry_path
        else REGISTRY_PATH
    )

    registry = load_json(
        path
    )

    sources = registry.get(
        "sources"
    )

    if not isinstance(
        sources,
        list,
    ):
        raise ValueError(
            "Source registry has no valid sources list."
        )

    existing_ids = {
        source.get("id")
        for source in sources
        if isinstance(source, dict)
    }

    if record["id"] in existing_ids:
        raise ValueError(
            f"Duplicate source id: "
            f"{record['id']}"
        )

    sources.append(
        record
    )

    write_json(
        path,
        registry,
    )

    return record


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Register an authoritative source "
            "for Knowledge Factory V2."
        )
    )

    parser.add_argument(
        "--id",
        required=True,
        dest="source_id",
    )

    parser.add_argument(
        "--publisher",
        required=True,
    )

    parser.add_argument(
        "--title",
        required=True,
    )

    parser.add_argument(
        "--source-type",
        required=True,
        choices=[
            "curriculum",
            "textbook",
            "activity_book",
            "question_bank",
            "exam",
            "guide",
            "other",
        ],
    )

    parser.add_argument(
        "--authority-tier",
        required=True,
        choices=[
            "primary_official",
            "official_support",
            "supplementary",
        ],
    )

    parser.add_argument(
        "--url",
    )

    parser.add_argument(
        "--local-path",
    )

    parser.add_argument(
        "--exam",
        action="append",
        default=[],
        choices=["TYT", "AYT"],
    )

    parser.add_argument(
        "--subject",
        action="append",
        default=[],
    )

    parser.add_argument(
        "--grade",
        action="append",
        default=[],
    )

    parser.add_argument(
        "--topic",
        action="append",
        default=[],
    )

    parser.add_argument(
        "--note",
        action="append",
        default=[],
    )

    return parser.parse_args()


def main():
    args = parse_args()

    try:
        record = build_source_record(
            source_id=args.source_id,
            publisher=args.publisher,
            title=args.title,
            source_type=args.source_type,
            authority_tier=args.authority_tier,
            url=args.url,
            local_path=args.local_path,
            exam_scope=args.exam,
            subject_scope=args.subject,
            grade_scope=args.grade,
            topic_scope=args.topic,
            notes=args.note,
        )

        register_source(
            record
        )

    except (
        ValueError,
        FileNotFoundError,
    ) as exc:
        print(
            f"ERROR: {exc}"
        )
        sys.exit(1)

    print(
        f"REGISTERED: {record['id']}"
    )

    print(
        f"PUBLISHER: {record['publisher']}"
    )

    print(
        f"TYPE: {record['source_type']}"
    )

    print(
        f"AUTHORITY: {record['authority_tier']}"
    )

    if record.get("url"):
        print(
            f"URL: {record['url']}"
        )

    if record.get("local_path"):
        print(
            f"LOCAL: {record['local_path']}"
        )

        print(
            f"SHA256: {record['sha256']}"
        )


if __name__ == "__main__":
    main()
