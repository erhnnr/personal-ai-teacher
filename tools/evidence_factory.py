"""
Knowledge Factory V2 - Evidence Factory

Registered Source -> Evidence Package -> Knowledge Draft
"""

import argparse
import json
import re
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = PROJECT_ROOT / "data" / "knowledge" / "sources" / "source_registry.json"
EVIDENCE_ROOT = PROJECT_ROOT / "data" / "knowledge" / "evidence"
EVIDENCE_SCHEMA_PATH = PROJECT_ROOT / "data" / "knowledge" / "schemas" / "evidence_package.schema.json"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def slugify(value):
    value = str(value).strip()
    replacements = {
        "İ": "I", "Ç": "C", "Ğ": "G",
        "Ö": "O", "Ş": "S", "Ü": "U",
        "ı": "i", "ç": "c", "ğ": "g",
        "ö": "o", "ş": "s", "ü": "u",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def load_registry():
    registry = load_json(REGISTRY_PATH)
    if not isinstance(registry.get("sources"), list):
        raise ValueError("Source registry has no valid sources list.")
    return registry


def validate_registry(registry):
    seen = set()

    for index, source in enumerate(registry.get("sources", []), start=1):
        if not isinstance(source, dict):
            raise ValueError(f"Source #{index} is not an object.")

        source_id = str(source.get("id", "")).strip()

        if not source_id:
            raise ValueError(f"Source #{index} has no id.")

        if source_id in seen:
            raise ValueError(f"Duplicate source id: {source_id}")

        seen.add(source_id)

        if not source.get("publisher"):
            raise ValueError(f"Source '{source_id}' has no publisher.")

        if not source.get("title"):
            raise ValueError(f"Source '{source_id}' has no title.")

        if not (source.get("url") or source.get("local_path")):
            raise ValueError(
                f"Source '{source_id}' needs url or local_path."
            )

    return True


def source_ids(registry):
    return {source["id"] for source in registry.get("sources", [])}


def validate_evidence_package(package, registry=None):
    schema = load_json(EVIDENCE_SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(package),
        key=lambda error: list(error.path),
    )

    if errors:
        first = errors[0]
        location = ".".join(str(item) for item in first.path)
        if location:
            location = f" at '{location}'"
        raise ValueError(
            f"Evidence package schema failed{location}: {first.message}"
        )

    if registry is None:
        registry = load_registry()

    validate_registry(registry)
    known_sources = source_ids(registry)
    referenced = set()

    for source in package["sources"]:
        referenced.add(source["source_id"])

    for claim in package["claims"]:
        for source_ref in claim["source_refs"]:
            referenced.add(source_ref["source_id"])

    unknown = sorted(referenced - known_sources)

    if unknown:
        raise ValueError(
            "Evidence package references unregistered sources: "
            + ", ".join(unknown)
        )

    package_source_ids = {
        source["source_id"] for source in package["sources"]
    }

    for claim in package["claims"]:
        for source_ref in claim["source_refs"]:
            if source_ref["source_id"] not in package_source_ids:
                raise ValueError(
                    f"Claim '{claim['id']}' references a source "
                    "not declared in package sources: "
                    f"{source_ref['source_id']}"
                )

    return True


def evidence_path(subject, grade, topic):
    return (
        EVIDENCE_ROOT
        / slugify(subject)
        / f"grade{grade}"
        / slugify(topic)
        / "evidence.json"
    )


def create_empty_package(exam, subject, grade, topic):
    package_id = (
        f"{slugify(subject)}."
        f"grade{grade}."
        f"{slugify(topic)}"
    )

    return {
        "id": package_id,
        "exam": exam,
        "subject": subject,
        "grade": str(grade),
        "topic": topic,
        "status": "EVIDENCE_DRAFT",
        "sources": [],
        "claims": [],
        "coverage": {
            "curriculum_objectives": [],
            "notes": [],
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create a Knowledge Factory V2 evidence package skeleton."
    )
    parser.add_argument("--exam", required=True, choices=["TYT", "AYT"])
    parser.add_argument("--subject", required=True)
    parser.add_argument("--grade", default="12")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    registry = load_registry()
    validate_registry(registry)

    target = evidence_path(
        args.subject,
        args.grade,
        args.topic,
    )

    if target.exists() and not args.force:
        print(f"EXISTS: {target}")
        sys.exit(1)

    package = create_empty_package(
        args.exam,
        args.subject,
        args.grade,
        args.topic,
    )

    write_json(target, package)

    print(f"CREATED: {target}")
    print("STATUS: EVIDENCE_DRAFT")
    print(
        "NEXT: register sources, add claims, "
        "then validate before generation."
    )


if __name__ == "__main__":
    main()
