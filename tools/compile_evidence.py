"""
Knowledge Factory V2 — Phase 4 Evidence Compiler

Purpose:
Compile EVIDENCE_READY claims into a deterministic factual draft
without asking an LLM to rewrite factual content.

Core rule:
Evidence claim text is copied verbatim into the factual draft.
The compiler may route a claim to a canonical field, but it may
not paraphrase, expand, summarize, or invent factual content.

This is a FACTUAL-DRAFT stage, not STUDENT-READY validation.
Examples and topic relations remain empty here and are handled
by separate validated pipelines.
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_PATH = PROJECT_ROOT / "tools"

if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(0, str(TOOLS_PATH))

from evidence_factory import validate_evidence_package


EVIDENCE_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "evidence"
)

DRAFT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "drafts"
)


ALLOWED_KINDS = {
    "objective",
    "core_concept",
    "definition",
    "rule",
    "teaching_note",
}


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
    value = re.sub(r"[^a-z0-9]+", "_", value)

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
    Path(path).write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def get_evidence_path(
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


def get_draft_path(
    subject,
    grade,
    topic,
):
    return (
        DRAFT_ROOT
        / slugify(subject)
        / f"grade{grade}"
        / slugify(topic)
    )


def validate_compiler_claims(
    evidence,
):
    """
    The global evidence schema keeps compilation metadata optional
    for backward compatibility. Phase 4 compilation itself requires it.
    """

    claims = evidence.get(
        "claims",
        [],
    )

    if not claims:
        raise ValueError(
            "Evidence package has no claims."
        )

    seen = set()

    for claim in claims:
        claim_id = claim.get(
            "id"
        )

        if claim_id in seen:
            raise ValueError(
                f"Duplicate claim id: {claim_id}"
            )

        seen.add(
            claim_id
        )

        kind = claim.get(
            "kind"
        )

        if kind not in ALLOWED_KINDS:
            raise ValueError(
                f"Claim {claim_id} has no valid compilation kind."
            )

        if (
            kind == "definition"
            and not str(
                claim.get(
                    "term",
                    ""
                )
            ).strip()
        ):
            raise ValueError(
                f"Definition claim {claim_id} requires term."
            )

    return True


def compile_evidence(
    evidence,
):
    """
    Deterministically route evidence claims into a factual package.

    The claim text itself is copied exactly.
    """

    if evidence.get(
        "status"
    ) != "EVIDENCE_READY":
        raise ValueError(
            "Evidence status must be EVIDENCE_READY."
        )

    validate_compiler_claims(
        evidence
    )

    subject = evidence["subject"]
    grade = str(
        evidence["grade"]
    )
    topic = evidence["topic"]

    concept = {
        "id": (
            f"{slugify(subject)}."
            f"grade{grade}."
            f"{slugify(topic)}"
        ),
        "subject": subject,
        "grade": grade,
        "topic": topic,
        "learning_objectives": [],
        "prerequisites": [],
        "core_concepts": [],
        "definitions": [],
        "rules": [],
        "common_confusions": [],
        "teaching_notes": [],
    }

    provenance_items = []

    for claim in evidence["claims"]:
        claim_id = claim["id"]
        text = claim["text"]
        kind = claim["kind"]

        if kind == "objective":
            index = len(
                concept[
                    "learning_objectives"
                ]
            )
            concept[
                "learning_objectives"
            ].append(
                text
            )
            path = (
                "concept."
                f"learning_objectives[{index}]"
            )

        elif kind == "core_concept":
            index = len(
                concept[
                    "core_concepts"
                ]
            )
            concept[
                "core_concepts"
            ].append(
                text
            )
            path = (
                "concept."
                f"core_concepts[{index}]"
            )

        elif kind == "definition":
            index = len(
                concept[
                    "definitions"
                ]
            )
            concept[
                "definitions"
            ].append(
                {
                    "term": claim["term"],
                    "definition": text,
                }
            )
            path = (
                "concept."
                f"definitions[{index}]"
            )

        elif kind == "rule":
            index = len(
                concept[
                    "rules"
                ]
            )
            concept[
                "rules"
            ].append(
                text
            )
            path = (
                "concept."
                f"rules[{index}]"
            )

        elif kind == "teaching_note":
            index = len(
                concept[
                    "teaching_notes"
                ]
            )
            concept[
                "teaching_notes"
            ].append(
                text
            )
            path = (
                "concept."
                f"teaching_notes[{index}]"
            )

        else:
            raise ValueError(
                f"Unsupported claim kind: {kind}"
            )

        provenance_items.append(
            {
                "path": path,
                "evidence_refs": [
                    claim_id
                ],
                "source_refs": list(
                    claim.get(
                        "source_refs",
                        []
                    )
                ),
                "copy_mode": "VERBATIM",
            }
        )

    package = {
        "concept": concept,
        "examples": {
            "topic": topic,
            "examples": [],
        },
        "mistakes": {
            "topic": topic,
            "mistakes": [],
        },
        "relations": {
            "topic": topic,
            "prerequisites": [],
            "next_topics": [],
            "related_topics": [],
        },
        "_provenance": {
            "version": "2.0",
            "status": "PASS",
            "mode": "DETERMINISTIC_EVIDENCE_COMPILER",
            "evidence_id": evidence["id"],
            "items": provenance_items,
        },
    }

    validate_factual_draft(
        package,
        evidence,
    )

    return package


def _path_value(
    package,
    path,
):
    """
    Resolve only the compiler's own canonical paths.
    """

    match = re.fullmatch(
        r"concept\.([a-z_]+)\[(\d+)\]",
        path,
    )

    if not match:
        raise ValueError(
            f"Unsupported provenance path: {path}"
        )

    field = match.group(1)
    index = int(
        match.group(2)
    )

    value = package[
        "concept"
    ][field][index]

    if field == "definitions":
        return value[
            "definition"
        ]

    return value


def validate_factual_draft(
    package,
    evidence,
):
    """
    Phase-4 factual draft validation.

    This intentionally does NOT run the student-ready validator.
    It checks the invariant that every factual value is copied
    verbatim from one evidence claim and that no LLM-only fields
    were populated.
    """

    claims = {
        claim["id"]: claim
        for claim in evidence[
            "claims"
        ]
    }

    provenance = package.get(
        "_provenance",
        {},
    )

    if (
        provenance.get(
            "mode"
        )
        !=
        "DETERMINISTIC_EVIDENCE_COMPILER"
    ):
        raise ValueError(
            "Invalid compiler provenance mode."
        )

    if (
        provenance.get(
            "evidence_id"
        )
        != evidence.get(
            "id"
        )
    ):
        raise ValueError(
            "Evidence id mismatch."
        )

    for item in provenance.get(
        "items",
        []
    ):
        refs = item.get(
            "evidence_refs",
            []
        )

        if len(refs) != 1:
            raise ValueError(
                "Compiler item must reference exactly one claim."
            )

        claim_id = refs[0]

        if claim_id not in claims:
            raise ValueError(
                f"Unknown evidence claim: {claim_id}"
            )

        compiled_text = _path_value(
            package,
            item["path"],
        )

        if (
            compiled_text
            != claims[
                claim_id
            ]["text"]
        ):
            raise ValueError(
                "Compiled factual text is not a verbatim evidence copy "
                f"at {item['path']}."
            )

        if (
            item.get(
                "copy_mode"
            )
            != "VERBATIM"
        ):
            raise ValueError(
                "Compiler provenance copy_mode must be VERBATIM."
            )

    if package[
        "examples"
    ][
        "examples"
    ]:
        raise ValueError(
            "Factual draft examples must be empty."
        )

    if package[
        "mistakes"
    ][
        "mistakes"
    ]:
        raise ValueError(
            "Factual draft mistakes must be empty."
        )

    relations = package[
        "relations"
    ]

    for field in (
        "prerequisites",
        "next_topics",
        "related_topics",
    ):
        if relations[
            field
        ]:
            raise ValueError(
                f"Factual draft relation {field} must be empty."
            )

    excluded_terms = (
        evidence
        .get(
            "coverage",
            {}
        )
        .get(
            "excluded_terms",
            []
        )
    )

    factual_text = json.dumps(
        package["concept"],
        ensure_ascii=False,
    ).casefold()

    for term in excluded_terms:
        if (
            str(
                term
            ).casefold()
            in factual_text
        ):
            raise ValueError(
                f"Excluded term leaked into factual draft: {term}"
            )

    return True


def save_compiled_draft(
    evidence,
    package,
    overwrite=False,
):
    draft_path = get_draft_path(
        evidence["subject"],
        evidence["grade"],
        evidence["topic"],
    )

    if draft_path.exists():
        if not overwrite:
            raise FileExistsError(
                f"Draft already exists: {draft_path}"
            )

        shutil.rmtree(
            draft_path
        )

    draft_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_json(
        draft_path / "concept.json",
        package["concept"],
    )
    write_json(
        draft_path / "examples.json",
        package["examples"],
    )
    write_json(
        draft_path / "mistakes.json",
        package["mistakes"],
    )
    write_json(
        draft_path / "relations.json",
        package["relations"],
    )
    write_json(
        draft_path / "provenance.json",
        package["_provenance"],
    )

    metadata = {
        "status": "FACTUAL_DRAFT_READY",
        "verified": False,
        "student_ready": False,
        "generated_by": "deterministic_evidence_compiler",
        "generated_at": (
            datetime.now()
            .astimezone()
            .isoformat()
        ),
        "exam": evidence["exam"],
        "subject": evidence["subject"],
        "topic": evidence["topic"],
        "evidence_id": evidence["id"],
        "factual_draft_status": "PASS",
        "structure_status": "FACTUAL_DRAFT",
        "factual_review_status": "EVIDENCE_VERBATIM",
        "warning": (
            "FACTUAL_DRAFT_READY is not STUDENT_READY. "
            "Examples, exercises and pedagogical rendering require "
            "their own validated pipelines."
        ),
    }

    write_json(
        draft_path / "draft_meta.json",
        metadata,
    )

    return draft_path


def compile_topic(
    exam,
    subject,
    grade,
    topic,
    overwrite=False,
):
    evidence_path = get_evidence_path(
        subject,
        grade,
        topic,
    )

    if not evidence_path.exists():
        raise FileNotFoundError(
            f"Evidence not found: {evidence_path}"
        )

    evidence = load_json(
        evidence_path
    )

    valid = validate_evidence_package(
        evidence
    )

    if valid is not True:
        raise ValueError(
            "Evidence package validation failed."
        )

    if (
        normalize(
            evidence.get(
                "exam"
            )
        )
        != normalize(
            exam
        )
    ):
        raise ValueError(
            "Evidence exam mismatch."
        )

    package = compile_evidence(
        evidence
    )

    draft_path = save_compiled_draft(
        evidence,
        package,
        overwrite=overwrite,
    )

    return draft_path


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compile EVIDENCE_READY claims into a "
            "deterministic factual draft."
        )
    )

    parser.add_argument(
        "--exam",
        required=True,
    )
    parser.add_argument(
        "--subject",
        required=True,
    )
    parser.add_argument(
        "--grade",
        required=True,
    )
    parser.add_argument(
        "--topic",
        required=True,
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("KNOWLEDGE FACTORY V2 — PHASE 4 EVIDENCE COMPILER")
    print("=" * 70)

    draft_path = compile_topic(
        exam=args.exam,
        subject=args.subject,
        grade=args.grade,
        topic=args.topic,
        overwrite=args.overwrite,
    )

    print(
        f"COMPILED   | {args.topic}"
    )
    print(
        "FACTUAL    | PASS"
    )
    print(
        "PROVENANCE | PASS"
    )
    print(
        "COPY MODE  | VERBATIM"
    )
    print(
        "STUDENT    | NOT_READY"
    )
    print(
        f"DRAFT PATH | {draft_path}"
    )


if __name__ == "__main__":
    main()
