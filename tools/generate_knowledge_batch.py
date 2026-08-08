"""
Batch Knowledge Draft Generator

Purpose:
Generate structured knowledge DRAFTS from the current
TYT/AYT curriculum using the local LM Studio model.

IMPORTANT:
Generated content is NOT verified knowledge.

Outputs are written to:

data/knowledge/drafts/

They must never be treated as READY merely because
they pass structural validation.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


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

    Existing units are never overwritten by this tool.
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


def build_prompt(
    record,
    grade,
):
    """
    Build a strict JSON-generation prompt.

    The model is creating a DRAFT only.
    """

    curriculum_json = json.dumps(
        record,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
Sen YKS için eğitim içerik taslağı hazırlayan bir sistemsin.

GÖREV:
Aşağıdaki müfredat kaydı için yapılandırılmış bir KNOWLEDGE DRAFT üret.

Bu içerik otomatik olarak doğrulanmış kabul edilmeyecek.
Bu nedenle:
- Bilmediğin ayrıntıyı uydurma.
- Tartışmalı veya emin olmadığın bilgiyi ekleme.
- Açık, temel ve YKS seviyesinde kal.
- Yalnızca Türkçe kullan.
- Sayısal örneklerde hesabı kontrol et.
- Öğrenciye öğretilebilir, kısa ve net içerik üret.

MÜFREDAT KAYDI:

{curriculum_json}

ÖĞRENCİ SINIFI:
{grade}

ÇIKTI KURALI:

SADECE geçerli JSON üret.
Markdown kullanma.
Kod bloğu kullanma.
JSON dışında hiçbir açıklama yazma.

JSON TAM OLARAK şu üst yapıda olmalı:

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
        "learning_point": "string"
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
    Save a generated package as DRAFT.
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
        "warning": (
            "Structural validation does not "
            "constitute factual verification."
        ),
    }

    write_json(
        draft_path / "draft_meta.json",
        metadata,
    )

    return draft_path


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

            structurally_valid = (
                validate_topic(
                    draft_path,
                    verbose=False,
                )
            )

            if structurally_valid:

                print(
                    f"DRAFT OK   | {topic} "
                    "| STRUCTURE_VALID"
                )

            else:

                print(
                    f"DRAFT WARN | {topic} "
                    "| STRUCTURE_INVALID"
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
        f"Generated drafts : {generated}"
    )

    print(
        f"Existing units   : {skipped_units}"
    )

    print(
        f"Existing drafts  : {skipped_drafts}"
    )

    print(
        f"Failed           : {failed}"
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "Generated files are DRAFTS."
    )

    print(
        "They are NOT verified and are NOT "
        "available to the student."
    )


if __name__ == "__main__":
    main()