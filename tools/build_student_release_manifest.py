"""
KNOWLEDGE FACTORY V2 — PHASE 6K
Build Student Release Manifest

This creates a release manifest for the canonical READY Biology units.
It does not mutate canonical concept.json files.

Release is explicit, hash-bound, auditable, and reversible by removing
an entry from the release manifest.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CANONICAL_MANIFEST = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "canonical_ready"
    / "biology"
    / "manifest.json"
)

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "student_release"
    / "biology_release_manifest.json"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_release_manifest(canonical_manifest):
    units = []

    for item in canonical_manifest.get("units", []):
        if item.get("verified") is not True:
            continue

        # Canonical artifacts intentionally remain immutable/not visible.
        if item.get("student_ready") is not False:
            continue
        if item.get("student_visible") is not False:
            continue

        units.append(
            {
                "unit_id": item["id"],
                "record_id": item["record_id"],
                "canonical_path": item["path"],
                "canonical_text_sha256": item["text_sha256"],
                "status": "RELEASED",
                "student_ready": True,
                "student_visible": True,
                "release_policy": (
                    "HASH_BOUND_CANONICAL_STUDENT_RELEASE"
                ),
            }
        )

    return {
        "version": "1.0",
        "kind": "student_release_manifest",
        "subject": "Biyoloji",
        "release_count": len(units),
        "units": units,
    }


def validate_release_manifest(payload):
    errors = []
    units = payload.get("units", [])

    if payload.get("subject") != "Biyoloji":
        errors.append("subject must be Biyoloji")

    if payload.get("release_count") != len(units):
        errors.append("release_count mismatch")

    ids = [u.get("unit_id") for u in units]
    if len(ids) != len(set(ids)):
        errors.append("duplicate released unit ids")

    for item in units:
        if item.get("status") != "RELEASED":
            errors.append(
                f"{item.get('unit_id')}: status must be RELEASED"
            )
        if item.get("student_ready") is not True:
            errors.append(
                f"{item.get('unit_id')}: student_ready must be true"
            )
        if item.get("student_visible") is not True:
            errors.append(
                f"{item.get('unit_id')}: student_visible must be true"
            )
        if not item.get("canonical_text_sha256"):
            errors.append(
                f"{item.get('unit_id')}: canonical hash missing"
            )

    return errors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--canonical-manifest",
        type=Path,
        default=DEFAULT_CANONICAL_MANIFEST,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    return parser.parse_args()


def main():
    args = parse_args()

    canonical = load_json(args.canonical_manifest)
    payload = build_release_manifest(canonical)
    errors = validate_release_manifest(payload)

    print("=" * 72)
    print("KNOWLEDGE FACTORY V2 — PHASE 6K STUDENT RELEASE GATE")
    print("=" * 72)
    print(f"Canonical input : {len(canonical.get('units', []))}")
    print(f"Released        : {payload['release_count']}")

    if errors:
        print("STUDENT RELEASE VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    write_json(args.output, payload)

    print("STUDENT RELEASE VALIDATION: PASS")
    print("Release policy  : HASH-BOUND")
    print("Student ready   : True (release manifest only)")
    print("Student visible : True (release manifest only)")
    print(f"OUTPUT          | {args.output}")


if __name__ == "__main__":
    main()
