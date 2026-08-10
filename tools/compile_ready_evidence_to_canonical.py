"""
KNOWLEDGE FACTORY V2 — PHASE 6J
READY Evidence -> Canonical Knowledge Compilation

Safety model:
- Input must already be release-safe evidence_status == READY.
- Factual content is copied verbatim; this compiler does not paraphrase.
- No unsupported definitions/rules/examples are invented.
- Canonical packages remain student_ready == False and student_visible == False.
- Teacher integration is a later phase.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_INPUT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "promoted_evidence"
    / "biology_ready_evidence.json"
)

DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "canonical_ready"
    / "biology"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_slug(value: str) -> str:
    value = value.strip()
    value = value.replace("İ", "i").replace("I", "i").replace("ı", "i")
    value = value.lower()
    value = re.sub(r"[^a-z0-9çğıöşü._-]+", "-", value)
    return value.strip("-") or "unit"


def manifest_path(concept_path: Path, output_root: Path) -> str:
    """
    Prefer project-relative paths in real project runs.
    During isolated tests or alternate output roots outside PROJECT_ROOT,
    fall back to a path relative to output_root.
    """
    try:
        return concept_path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return concept_path.relative_to(output_root).as_posix()


def compile_record(record):
    evidence_text = record["evidence_text"]
    source = record["source"]
    approval = record["approval"]

    return {
        "schema_version": "1.0",
        "id": record["outcome_id"],
        "subject": "Biyoloji",
        "grade": record["grade"],
        "theme_number": record["theme_number"],
        "theme_name": record["theme_name"],
        "topic": record["outcome_title"],
        "learning_objectives": [record["outcome_title"]],
        "prerequisites": [],
        "core_concepts": [],
        "definitions": [],
        "rules": [],
        "common_confusions": [],
        "teaching_notes": [],
        "source_grounded_content": {
            "mode": "VERBATIM_OFFICIAL_EVIDENCE",
            "text": evidence_text,
            "text_sha256": sha256_text(evidence_text),
        },
        "provenance": {
            "authority": source["authority"],
            "corpus_family": source["corpus_family"],
            "package_id": source["package_id"],
            "page": source["page"],
            "source_anchor": source["source_anchor"],
            "html_path": source["html_path"],
            "image_path": source["image_path"],
            "source_text_sha256": source["text_sha256"],
            "evidence_record_id": record["record_id"],
            "promotion_policy": record["promotion_policy"],
        },
        "verification": {
            "evidence_status": record["evidence_status"],
            "approval_status": approval["status"],
            "reviewer_type": approval["reviewer_type"],
            "reviewer_id": approval["reviewer_id"],
            "factual_support": approval["factual_support"],
            "outcome_support": approval["outcome_support"],
            "source_consistency": approval["source_consistency"],
        },
        "compiler": {
            "name": "KNOWLEDGE_FACTORY_V2_CANONICAL_VERBATIM_COMPILER",
            "deterministic": True,
            "paraphrase_allowed": False,
            "invented_facts_allowed": False,
        },
        "verified": True,
        "student_ready": False,
        "student_visible": False,
    }


def validate_compiled_unit(unit):
    errors = []
    uid = unit.get("id", "<unknown>")

    if unit.get("subject") != "Biyoloji":
        errors.append(f"{uid}: subject must be Biyoloji")
    if unit.get("verified") is not True:
        errors.append(f"{uid}: verified must be true")
    if unit.get("student_ready") is not False:
        errors.append(f"{uid}: student_ready must remain false")
    if unit.get("student_visible") is not False:
        errors.append(f"{uid}: student_visible must remain false")

    grounded = unit.get("source_grounded_content", {})
    if grounded.get("mode") != "VERBATIM_OFFICIAL_EVIDENCE":
        errors.append(f"{uid}: grounded content must remain verbatim")

    text = grounded.get("text", "")
    if not text.strip():
        errors.append(f"{uid}: source-grounded text missing")
    if sha256_text(text) != grounded.get("text_sha256"):
        errors.append(f"{uid}: grounded text hash mismatch")

    provenance = unit.get("provenance", {})
    if grounded.get("text_sha256") != provenance.get("source_text_sha256"):
        errors.append(f"{uid}: canonical text differs from source evidence hash")

    verification = unit.get("verification", {})
    if verification.get("evidence_status") != "READY":
        errors.append(f"{uid}: input evidence must be READY")
    if verification.get("approval_status") != "APPROVED_FOR_EVIDENCE_READY":
        errors.append(f"{uid}: independent approval required")

    for check in ("factual_support", "outcome_support", "source_consistency"):
        if verification.get(check) is not True:
            errors.append(f"{uid}: {check} must be true")

    compiler = unit.get("compiler", {})
    if compiler.get("deterministic") is not True:
        errors.append(f"{uid}: compiler must be deterministic")
    if compiler.get("paraphrase_allowed") is not False:
        errors.append(f"{uid}: paraphrase must remain disabled")

    return errors


def compile_all(input_payload, output_root: Path):
    records = input_payload.get("records", [])

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    manifest_units = []
    all_errors = []

    for record in records:
        if record.get("evidence_status") != "READY":
            all_errors.append(
                f"{record.get('record_id')}: non-READY record in promoted evidence input"
            )
            continue

        unit = compile_record(record)
        all_errors.extend(validate_compiled_unit(unit))

        slug = safe_slug(record["outcome_id"])
        concept_path = output_root / slug / "concept.json"
        write_json(concept_path, unit)

        manifest_units.append(
            {
                "id": unit["id"],
                "record_id": record["record_id"],
                "path": manifest_path(concept_path, output_root),
                "text_sha256": unit["source_grounded_content"]["text_sha256"],
                "verified": True,
                "student_ready": False,
                "student_visible": False,
            }
        )

    manifest = {
        "version": "1.0",
        "kind": "canonical_ready_knowledge_manifest",
        "subject": "Biyoloji",
        "input_ready_count": len(records),
        "compiled_count": len(manifest_units),
        "units": manifest_units,
        "student_ready": False,
        "student_visible": False,
    }
    write_json(output_root / "manifest.json", manifest)

    return manifest, all_errors


def validate_manifest(manifest):
    errors = []
    units = manifest.get("units", [])

    if manifest.get("subject") != "Biyoloji":
        errors.append("manifest subject must be Biyoloji")
    if manifest.get("compiled_count") != len(units):
        errors.append("manifest compiled_count mismatch")
    if manifest.get("input_ready_count") != len(units):
        errors.append("not every READY record was compiled")
    if manifest.get("student_ready") is not False:
        errors.append("manifest student_ready must remain false")
    if manifest.get("student_visible") is not False:
        errors.append("manifest student_visible must remain false")

    ids = [unit.get("id") for unit in units]
    if len(ids) != len(set(ids)):
        errors.append("duplicate canonical unit ids")

    return errors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = load_json(args.input)

    manifest, errors = compile_all(payload, args.output_root)
    errors.extend(validate_manifest(manifest))

    print("=" * 72)
    print("KNOWLEDGE FACTORY V2 — PHASE 6J CANONICAL KNOWLEDGE COMPILATION")
    print("=" * 72)
    print(f"READY evidence input : {manifest['input_ready_count']}")
    print(f"Canonical compiled   : {manifest['compiled_count']}")

    if errors:
        print("CANONICAL VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("CANONICAL VALIDATION: PASS")
    print("Compiler mode        : VERBATIM / DETERMINISTIC")
    print("Student ready        : False")
    print("Student visible      : False")
    print(f"OUTPUT               | {args.output_root}")


if __name__ == "__main__":
    main()
