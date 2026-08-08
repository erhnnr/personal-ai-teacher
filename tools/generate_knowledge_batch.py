"""
Batch Knowledge Draft Generator

Purpose:
Generate structured knowledge DRAFTS from the current
TYT/AYT curriculum using the local LM Studio model.

Pipeline:
Curriculum
-> Local LLM Draft
-> Structural Validation
-> Deterministic Math Factual Review
-> DRAFT status report

IMPORTANT:
Generated content is NOT verified knowledge.

Outputs are written to:

data/knowledge/drafts/

They must never be treated as READY merely because
they pass structural or factual checks.
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = PROJECT_ROOT / "app"
TOOLS_PATH = PROJECT_ROOT / "tools"

if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))

if str(TOOLS_PATH) not in sys.path:
    sys.path.insert(0, str(TOOLS_PATH))


from config import MODEL_NAME
from curriculum_engine import load_curriculum_data
from llm import client, check_llm_connection
from validate_knowledge import validate_topic
from review_math_draft import review_draft


DRAFT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "drafts"
)

UNIT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "units"
)


def slugify(value):
    """
    Convert Turkish display text into a stable
    ASCII directory name.
    """

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
        value = value.replace(
            old,
            new,
        )

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
        path.read_text(
            encoding="utf-8"
        )
    )


def write_json(path, data):
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def find_existing_unit(
    subject,
    topic,
):
    """
    Check whether a real knowledge unit already exists.

    Existing verified units are never overwritten.
    """

    if not UNIT_ROOT.exists():
        return None

    for concept_file in UNIT_ROOT.rglob(
        "concept.json"
    ):

        try:
            data = load_json(
                concept_file
            )

        except Exception:
            continue

        if (
            normalize(
                data.get("subject")
            )
            == normalize(subject)
            and
            normalize(
                data.get("topic")
            )
            == normalize(topic)
        ):
            return concept_file.parent

    return None


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


def prepare_draft_for_overwrite(
    draft_path,
    overwrite,
):
    """
    Remove an obsolete generated draft before
    an explicit overwrite attempt.

    Drafts are unverified temporary artifacts.
    If regeneration later fails, no stale draft
    should remain and appear current.
    """

    draft_path = Path(
        draft_path
    )

    if (
        overwrite
        and draft_path.exists()
    ):
        shutil.rmtree(
            draft_path
        )

        return True

    return False


def build_prompt(
    record,
    grade,
):
    """
    Build strict JSON-generation instructions.

    Mathematics examples must include a
    machine-checkable validation block.
    """

    curriculum_json = json.dumps(
        record,
        ensure_ascii=False,
        indent=2,
    )

    math_validation_instruction = ""

    if normalize(record["subject"]) == normalize("Matematik"):
        math_validation_instruction = """
MATEMATİK İÇİN ZORUNLU KURAL:

Her examples öğesinde "validation" alanı bulunmalıdır.

Validation, sorudaki matematiği makinenin bağımsız
olarak kontrol edebileceği biçimde tanımlamalıdır.

Desteklenen validation type değerleri:

- arithmetic
- equation
- inequality
- polynomial_remainder
- function_value
- function_range
- combination
- permutation
- trigonometric_value
- distance_2d
- indefinite_integral
- definite_integral

Matematiksel ifadelerde:
- çarpma için *
- üs için **
- pi için pi
- karekök için sqrt(...)
kullan.

Doğal dildeki question, answer ve validation
aynı matematiksel problemi temsil etmelidir.

Soruyu desteklenen validation tiplerinden biriyle
güvenilir biçimde ifade edemiyorsan o örneği üretme.

ÖRNEK — DENKLEM:

"validation": {
  "type": "equation",
  "expression": "3*x + 5",
  "variable": "x",
  "relation": "=",
  "rhs": 14,
  "expected": 3
}

ÖRNEK — POLİNOM KALANI:

"validation": {
  "type": "polynomial_remainder",
  "polynomial": "3*x**2 + 5*x - 2",
  "variable": "x",
  "divisor_root": 1,
  "expected": 6
}

ÖRNEK — BELİRLİ İNTEGRAL:

"validation": {
  "type": "definite_integral",
  "expression": "2*x",
  "variable": "x",
  "lower": 0,
  "upper": 3,
  "expected": 9
}
""".strip()

    return f"""
Sen YKS için eğitim içerik taslağı hazırlayan bir sistemsin.

GÖREV:
Aşağıdaki müfredat kaydı için yapılandırılmış bir KNOWLEDGE DRAFT üret.

Bu içerik otomatik olarak doğrulanmış kabul edilmeyecek.

KURALLAR:

- Bilmediğin ayrıntıyı uydurma.
- Tartışmalı veya emin olmadığın bilgiyi ekleme.
- Açık, temel ve YKS seviyesinde kal.
- Yalnızca Türkçe kullan.
- Matematiksel hesaplamaları dikkatlice kontrol et.
- Öğrenciye öğretilebilir, kısa ve net içerik üret.
- Sayısal örneklerde sonucu iki kez kontrol et.
- Belirsiz integralde +C sabitini unutma.
- Belirli integral hesaplarında alt ve üst sınırı doğru uygula.
- Matematiksel bir sonuçtan emin değilsen o örneği üretme.

{math_validation_instruction}

MÜFREDAT KAYDI:

{curriculum_json}

ÖĞRENCİ SINIFI:
{grade}

ÇIKTI KURALI:

SADECE geçerli JSON üret.
Markdown kullanma.
Kod bloğu kullanma.
JSON dışında hiçbir açıklama yazma.

JSON üst yapısı:

{{
  "concept": {{
    "id": "string",
    "subject": "{record['subject']}",
    "grade": "{grade}",
    "topic": "{record['topic']}",
    "learning_objectives": ["string"],
    "prerequisites": ["string"],
    "core_concepts": ["string"],
    "definitions": [
      {{
        "term": "string",
        "definition": "string"
      }}
    ],
    "rules": ["string"],
    "common_confusions": ["string"],
    "teaching_notes": ["string"]
  }},
  "examples": {{
    "topic": "{record['topic']}",
    "examples": [
      {{
        "id": "string",
        "level": "basic",
        "type": "concept",
        "question": "string",
        "answer": "string",
        "learning_point": "string",
        "validation": {{
          "type": "supported_validation_type"
        }}
      }}
    ]
  }},
  "mistakes": {{
    "topic": "{record['topic']}",
    "mistakes": [
      {{
        "id": "string",
        "error": "string",
        "explanation": "string",
        "teacher_action": "string"
      }}
    ]
  }},
  "relations": {{
    "topic": "{record['topic']}",
    "prerequisites": [
      {{
        "topic": "string",
        "reason": "string"
      }}
    ],
    "next_topics": [
      {{
        "topic": "string",
        "reason": "string"
      }}
    ],
    "related_topics": [
      {{
        "topic": "string",
        "relation": "string"
      }}
    ]
  }}
}}

EN AZ:

- 3 learning objective
- 3 core concept
- 2 definition
- 3 rule
- 2 common confusion
- 2 teaching note
- 2 example
- 2 mistake

üret.

Example level yalnızca:

basic
intermediate
advanced

değerlerinden biri olabilir.

Konu Matematik ise her örnekte "validation" ZORUNLUDUR.
""".strip()


def extract_json(text):
    """
    Parse model output defensively.
    """

    if not text:
        raise ValueError(
            "Model returned empty content."
        )

    text = text.strip()

    if text.startswith("```"):

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

    try:
        return json.loads(
            text
        )

    except json.JSONDecodeError:

        start = text.find("{")
        end = text.rfind("}")

        if (
            start == -1
            or end == -1
            or end <= start
        ):
            raise

        return json.loads(
            text[start:end + 1]
        )


def enforce_identity(
    package,
    record,
    grade,
):
    """
    Never trust the model for canonical identity fields.
    """

    subject = record["subject"]
    topic = record["topic"]

    subject_slug = slugify(
        subject
    )

    topic_slug = slugify(
        topic
    )

    concept = package.setdefault(
        "concept",
        {}
    )

    concept["id"] = (
        f"{subject_slug}."
        f"grade{grade}."
        f"{topic_slug}"
    )

    concept["subject"] = subject
    concept["grade"] = str(grade)
    concept["topic"] = topic

    for section_name in (
        "examples",
        "mistakes",
        "relations",
    ):

        section = package.setdefault(
            section_name,
            {}
        )

        section["topic"] = topic

    return package


def save_draft(
    record,
    grade,
    package,
):
    """
    Save generated package as DRAFT.
    """

    draft_path = get_draft_path(
        record["subject"],
        grade,
        record["topic"],
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

    metadata = {
        "status": "DRAFT",
        "verified": False,
        "generated_by": "local_llm",
        "model": MODEL_NAME,
        "generated_at": (
            datetime.now()
            .astimezone()
            .isoformat()
        ),
        "exam": record.get("exam"),
        "subject": record.get("subject"),
        "topic": record.get("topic"),
        "priority": record.get("priority"),
        "structure_status": None,
        "factual_review_status": None,
        "warning": (
            "Structural or deterministic validation "
            "does not constitute full factual verification."
        ),
    }

    write_json(
        draft_path / "draft_meta.json",
        metadata,
    )

    return draft_path


def update_draft_metadata(
    draft_path,
    structure_status,
    factual_review_status,
):
    """
    Persist automated review results into draft metadata.
    """

    meta_path = (
        draft_path
        / "draft_meta.json"
    )

    metadata = load_json(
        meta_path
    )

    metadata[
        "structure_status"
    ] = structure_status

    metadata[
        "factual_review_status"
    ] = factual_review_status

    metadata[
        "verified"
    ] = False

    write_json(
        meta_path,
        metadata,
    )


def validate_generated_math_package(
    package,
    subject,
):
    """
    Enforce machine-checkable validation blocks
    before a generated Mathematics draft is saved.

    This validates the validation contract itself.

    It does not establish factual correctness.
    """

    if normalize(subject) != normalize("Matematik"):
        return

    examples_section = package.get(
        "examples"
    )

    if not isinstance(
        examples_section,
        dict,
    ):
        raise ValueError(
            "Mathematics draft has no valid examples section."
        )

    examples = examples_section.get(
        "examples"
    )

    if not isinstance(
        examples,
        list,
    ) or not examples:
        raise ValueError(
            "Mathematics draft must contain examples."
        )

    schema_path = (
        PROJECT_ROOT
        / "data"
        / "knowledge"
        / "schemas"
        / "math_example_validation.schema.json"
    )

    schema = load_json(
        schema_path
    )

    validator = Draft202012Validator(
        schema
    )

    for index, example in enumerate(
        examples,
        start=1,
    ):
        if not isinstance(
            example,
            dict,
        ):
            raise ValueError(
                f"Mathematics example {index} is invalid."
            )

        validation = example.get(
            "validation"
        )

        if not isinstance(
            validation,
            dict,
        ):
            raise ValueError(
                f"Mathematics example {index} "
                f"is missing validation."
            )

        errors = sorted(
            validator.iter_errors(
                validation
            ),
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
                location = (
                    f" at '{location}'"
                )

            raise ValueError(
                f"Mathematics example {index} "
                f"validation contract failed"
                f"{location}: "
                f"{first.message}"
            )


def generate_one(
    record,
    grade,
):
    prompt = build_prompt(
        record,
        grade,
    )

    response = (
        client
        .chat
        .completions
        .create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Yalnızca geçerli JSON üret. "
                        "Markdown veya açıklama yazma."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )
    )

    if not response.choices:
        raise RuntimeError(
            "Model returned no choices."
        )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    package = extract_json(
        content
    )

    package = enforce_identity(
        package,
        record,
        grade,
    )

    validate_generated_math_package(
        package,
        record["subject"],
    )

    return package


def select_records(
    exam,
    subject,
    topic=None,
):
    curriculum = load_curriculum_data()

    selected = []

    for record in curriculum:

        if (
            normalize(
                record.get("exam")
            )
            != normalize(exam)
        ):
            continue

        if (
            normalize(
                record.get("subject")
            )
            != normalize(subject)
        ):
            continue

        if (
            topic
            and normalize(
                record.get("topic")
            )
            != normalize(topic)
        ):
            continue

        selected.append(
            record
        )

    return selected


def run_automated_reviews(
    draft_path,
    subject,
):
    """
    Run structural and deterministic factual checks.

    Returns:
        structure_status
        factual_review_status
    """

    structure_valid = validate_topic(
        draft_path,
        verbose=False,
    )

    structure_status = (
        "PASS"
        if structure_valid
        else "FAIL"
    )

    factual_review_status = (
        "NOT_APPLICABLE"
    )

    if normalize(subject) == normalize(
        "Matematik"
    ):

        factual_report = review_draft(
            draft_path
        )

        factual_review_status = (
            factual_report["status"]
        )

    update_draft_metadata(
        draft_path,
        structure_status,
        factual_review_status,
    )

    return (
        structure_status,
        factual_review_status,
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate local-LLM knowledge drafts "
            "from curriculum records."
        )
    )

    parser.add_argument(
        "--exam",
        required=True,
        help="TYT or AYT",
    )

    parser.add_argument(
        "--subject",
        required=True,
        help="Curriculum subject name",
    )

    parser.add_argument(
        "--grade",
        default="12",
        help="Student release grade. Default: 12",
    )

    parser.add_argument(
        "--topic",
        default=None,
        help="Generate only one exact topic",
    )

    parser.add_argument(
        "--max-topics",
        type=int,
        default=None,
        help="Maximum number of topics to generate",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing draft",
    )

    args = parser.parse_args()

    connection = check_llm_connection()

    if not connection["connected"]:

        print(
            "ERROR: LM Studio is not available."
        )

        print(
            connection["error"]
        )

        sys.exit(1)

    if MODEL_NAME not in connection["models"]:

        print(
            f"ERROR: Model '{MODEL_NAME}' "
            "is not loaded."
        )

        sys.exit(1)

    records = select_records(
        args.exam,
        args.subject,
        topic=args.topic,
    )

    if not records:

        print(
            "No curriculum records matched."
        )

        sys.exit(1)

    generated = 0
    skipped_units = 0
    skipped_drafts = 0
    failed = 0

    structure_pass = 0
    structure_fail = 0

    factual_pass = 0
    factual_fail = 0
    factual_unverified = 0
    factual_not_applicable = 0

    print(
        "=" * 70
    )

    print(
        "KNOWLEDGE DRAFT BATCH GENERATOR"
    )

    print(
        "=" * 70
    )

    print(
        f"Exam: {args.exam}"
    )

    print(
        f"Subject: {args.subject}"
    )

    print(
        f"Model: {MODEL_NAME}"
    )

    print(
        f"Matched curriculum topics: "
        f"{len(records)}"
    )

    print()

    for record in records:

        if (
            args.max_topics is not None
            and generated >= args.max_topics
        ):
            break

        topic = record["topic"]

        existing_unit = find_existing_unit(
            record["subject"],
            topic,
        )

        if existing_unit is not None:

            print(
                f"SKIP UNIT  | {topic}"
            )

            skipped_units += 1
            continue

        draft_path = get_draft_path(
            record["subject"],
            args.grade,
            topic,
        )

        if (
            draft_path.exists()
            and not args.overwrite
        ):

            print(
                f"SKIP DRAFT | {topic}"
            )

            skipped_drafts += 1
            continue

        removed_old_draft = (
            prepare_draft_for_overwrite(
                draft_path,
                args.overwrite,
            )
        )

        if removed_old_draft:
            print(
                f"REMOVE OLD | {topic}"
            )

        print(
            f"GENERATING | {topic}"
        )

        try:

            package = generate_one(
                record,
                args.grade,
            )

            draft_path = save_draft(
                record,
                args.grade,
                package,
            )

            (
                structure_status,
                factual_status,
            ) = run_automated_reviews(
                draft_path,
                record["subject"],
            )

            if structure_status == "PASS":

                structure_pass += 1

            else:

                structure_fail += 1

            if factual_status == "FAIL":

                factual_fail += 1

            elif factual_status in (
                "PASS",
                "PASS_WITH_LIMITED_SCOPE",
            ):

                factual_pass += 1

            elif factual_status == "UNVERIFIED":

                factual_unverified += 1

            else:

                factual_not_applicable += 1

            print(
                f"DRAFT      | {topic}"
            )

            print(
                f"  STRUCTURE: "
                f"{structure_status}"
            )

            print(
                f"  FACTUAL  : "
                f"{factual_status}"
            )

            generated += 1

        except Exception as exc:

            print(
                f"FAILED     | {topic} "
                f"| {exc}"
            )

            failed += 1

    print()

    print(
        "=" * 70
    )

    print(
        "BATCH SUMMARY"
    )

    print(
        "=" * 70
    )

    print(
        f"Generated drafts       : {generated}"
    )

    print(
        f"Existing units         : {skipped_units}"
    )

    print(
        f"Existing drafts        : {skipped_drafts}"
    )

    print(
        f"Generation failures    : {failed}"
    )

    print()

    print(
        f"Structure PASS         : {structure_pass}"
    )

    print(
        f"Structure FAIL         : {structure_fail}"
    )

    print()

    print(
        f"Factual PASS           : {factual_pass}"
    )

    print(
        f"Factual FAIL           : {factual_fail}"
    )

    print(
        f"Factual UNVERIFIED     : {factual_unverified}"
    )

    print(
        f"Factual NOT_APPLICABLE : {factual_not_applicable}"
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "Generated files are still DRAFTS."
    )

    print(
        "Automated PASS does NOT mean VERIFIED."
    )

    print(
        "Student access remains disabled until "
        "a draft is explicitly promoted."
    )


if __name__ == "__main__":
    main()