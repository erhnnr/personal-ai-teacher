"""
Knowledge Factory V2 — Phase 6A
Official Curriculum Registry Pilot — Biology

Converts an official MEB Biology curriculum PDF into a deterministic,
machine-readable registry.

Pilot scope:
- Subject: Biyoloji
- Grades: 9, 10, 11, 12
- Extracts:
  grade
  theme number/name
  learning outcome id/title
  content framework
  key concepts

The extractor does NOT invent missing curriculum information.
It only records text explicitly present in the PDF.

Dependency:
    pip install pymupdf

Example:
    py tools\build_official_curriculum_registry.py ^
      --pdf 2024programbiy9101112Onayli.pdf
"""

import argparse
import json
import re
from collections import OrderedDict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "curriculum_registry"
    / "biology_9_12.json"
)

EXPECTED_OUTCOME_COUNTS = {
    9: 15,
    10: 19,
    11: 22,
    12: 22,
}

EXPECTED_THEMES = {
    9: {
        1: "Yaşam",
        2: "Organizasyon",
    },
    10: {
        1: "Enerji",
        2: "Ekoloji",
    },
    11: {
        1: "Tepki",
        2: "Homeostazi",
    },
    12: {
        1: "Üreme",
        2: "Gen",
    },
}

OUTCOME_PATTERN = re.compile(
    r"BİY\.\s*(9|10|11|12)\.\s*(1|2)\.\s*(\d+)\.",
    flags=re.IGNORECASE,
)

THEME_PATTERN = re.compile(
    r"(?m)^\s*([12])\.\s*TEMA:\s*([^\n]+)"
)

SECTION_STOP_HEADERS = (
    "ÖĞRENME KANITLARI",
    "ÖĞRENME-ÖĞRETME",
    "FARKLILAŞTIRMA",
    "ÖĞRETMEN YANSITMALARI",
)


def normalize_pdf_text(text):
    """
    Normalize PDF extraction artifacts without rewriting curriculum wording.
    """

    text = str(text or "")

    text = text.replace(
        "\u00ad",
        "",
    )

    # Join words broken by PDF line wrapping:
    # "devamlı-\nlığı" -> "devamlılığı"
    text = re.sub(
        r"([A-Za-zÇĞİÖŞÜçğıöşü])-\s*\n\s*"
        r"([A-Za-zÇĞİÖŞÜçğıöşü])",
        r"\1\2",
        text,
    )

    text = text.replace(
        "\r\n",
        "\n",
    ).replace(
        "\r",
        "\n",
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def read_pdf_text(pdf_path):
    try:
        import pymupdf as fitz
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required. Install with: "
            "py -m pip install pymupdf"
        ) from exc

    pdf_path = Path(
        pdf_path
    )

    if not pdf_path.exists():
        raise FileNotFoundError(
            pdf_path
        )

    document = fitz.open(
        pdf_path
    )

    pages = []

    for page_number, page in enumerate(
        document,
        start=1,
    ):
        pages.append(
            {
                "page": page_number,
                "text": normalize_pdf_text(
                    page.get_text(
                        "text"
                    )
                ),
            }
        )

    return pages


def build_full_text(pages):
    parts = []

    for page in pages:
        parts.append(
            f"\n[[PAGE:{page['page']}]]\n"
        )
        parts.append(
            page[
                "text"
            ]
        )

    return "\n".join(
        parts
    )


def page_number_at(full_text, position):
    prefix = full_text[
        :position
    ]

    matches = list(
        re.finditer(
            r"\[\[PAGE:(\d+)\]\]",
            prefix,
        )
    )

    if not matches:
        return None

    return int(
        matches[
            -1
        ].group(
            1
        )
    )


def clean_multiline(value):
    value = str(
        value or ""
    )

    value = re.sub(
        r"\[\[PAGE:\d+\]\]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip(
        " \n\t:-"
    )


def extract_outcome_title(block):
    match = OUTCOME_PATTERN.search(
        block
    )

    if not match:
        return ""

    tail = block[
        match.end():
    ]

    # Outcome title ends before the first process component a), b), ...
    component = re.search(
        r"(?m)^\s*a\)\s+",
        tail,
    )

    if component:
        tail = tail[
            :component.start()
        ]

    # Defensive stop if the PDF omits component formatting.
    for header in (
        "İÇERİK ÇERÇEVESİ",
        "Anahtar Kavramlar",
    ):
        idx = tail.find(
            header
        )

        if idx >= 0:
            tail = tail[
                :idx
            ]

    return clean_multiline(
        tail
    )


def extract_named_section(
    block,
    start_header,
    end_headers,
):
    start = block.find(
        start_header
    )

    if start < 0:
        return ""

    start += len(
        start_header
    )

    tail = block[
        start:
    ]

    end_positions = []

    for header in end_headers:
        position = tail.find(
            header
        )

        if position >= 0:
            end_positions.append(
                position
            )

    if end_positions:
        tail = tail[
            :min(
                end_positions
            )
        ]

    return clean_multiline(
        tail
    )


def extract_content_framework(block):
    return extract_named_section(
        block,
        "İÇERİK ÇERÇEVESİ",
        (
            "Anahtar Kavramlar",
            *SECTION_STOP_HEADERS,
        ),
    )


def extract_theme_content_framework(full_text, grade, theme_number):
    """Extract theme-scoped MEB content framework."""
    theme_outcome_pattern = re.compile(
        rf"BİY\.\s*{grade}\.\s*{theme_number}\.\s*\d+\.",
        flags=re.IGNORECASE,
    )
    matches = list(theme_outcome_pattern.finditer(full_text))
    if not matches:
        return ""

    start = matches[0].start()

    if theme_number == 1:
        next_theme_pattern = re.compile(
            rf"BİY\.\s*{grade}\.\s*2\.\s*1\.",
            flags=re.IGNORECASE,
        )
    else:
        if grade >= 12:
            next_theme_pattern = None
        else:
            next_theme_pattern = re.compile(
                rf"BİY\.\s*{grade + 1}\.\s*1\.\s*1\.",
                flags=re.IGNORECASE,
            )

    next_match = (
        next_theme_pattern.search(full_text, pos=matches[-1].end())
        if next_theme_pattern
        else None
    )
    end = next_match.start() if next_match else len(full_text)
    theme_block = full_text[start:end]
    return extract_content_framework(theme_block)


def extract_key_concepts(block):
    return extract_named_section(
        block,
        "Anahtar Kavramlar",
        SECTION_STOP_HEADERS,
    )


def split_outcome_blocks(full_text):
    matches = list(
        OUTCOME_PATTERN.finditer(
            full_text
        )
    )

    if not matches:
        raise ValueError(
            "No BİY learning outcome identifiers found."
        )

    candidates = {}

    for index, match in enumerate(
        matches
    ):
        end = (
            matches[
                index + 1
            ].start()
            if index + 1 < len(
                matches
            )
            else len(
                full_text
            )
        )

        block = full_text[
            match.start():
            end
        ]

        grade = int(
            match.group(
                1
            )
        )

        theme_number = int(
            match.group(
                2
            )
        )

        outcome_number = int(
            match.group(
                3
            )
        )

        outcome_id = (
            f"BİY.{grade}."
            f"{theme_number}."
            f"{outcome_number}"
        )

        candidate = {
            "id": outcome_id,
            "grade": grade,
            "theme_number": theme_number,
            "outcome_number": outcome_number,
            "title": extract_outcome_title(
                block
            ),
            "content_framework": extract_content_framework(
                block
            ),
            "key_concepts": extract_key_concepts(
                block
            ),
            "source_page": page_number_at(
                full_text,
                match.start(),
            ),
        }

        # The document contains one schematic example before the real grade
        # section. If the same outcome appears twice, keep the richer record.
        richness = sum(
            len(
                str(
                    candidate[
                        field
                    ]
                )
            )
            for field in (
                "title",
                "content_framework",
                "key_concepts",
            )
        )

        existing = candidates.get(
            outcome_id
        )

        if (
            existing is None
            or richness
            > existing[
                "_richness"
            ]
        ):
            candidate[
                "_richness"
            ] = richness

            candidates[
                outcome_id
            ] = candidate

    results = []

    for outcome in candidates.values():
        outcome.pop(
            "_richness",
            None,
        )

        results.append(
            outcome
        )

    results.sort(
        key=lambda item: (
            item[
                "grade"
            ],
            item[
                "theme_number"
            ],
            item[
                "outcome_number"
            ],
        )
    )

    return results


def build_registry(
    pages,
    source_name,
):
    full_text = build_full_text(
        pages
    )

    outcomes = split_outcome_blocks(
        full_text
    )

    grades = []

    for grade in (
        9,
        10,
        11,
        12,
    ):
        grade_outcomes = [
            item
            for item in outcomes
            if item[
                "grade"
            ] == grade
        ]

        themes = []

        for theme_number in (
            1,
            2,
        ):
            theme_outcomes = [
                item
                for item in grade_outcomes
                if item[
                    "theme_number"
                ] == theme_number
            ]

            theme_framework = extract_theme_content_framework(
                full_text,
                grade,
                theme_number,
            )

            themes.append(
                {
                    "theme_number": theme_number,
                    "theme_name": EXPECTED_THEMES[
                        grade
                    ][
                        theme_number
                    ],
                    "content_framework": theme_framework,
                    "learning_outcome_count": len(
                        theme_outcomes
                    ),
                    "learning_outcomes": theme_outcomes,
                }
            )

        grades.append(
            {
                "grade": grade,
                "learning_outcome_count": len(
                    grade_outcomes
                ),
                "themes": themes,
            }
        )

    return {
        "version": "1.0",
        "kind": "OFFICIAL_CURRICULUM_REGISTRY",
        "authority": "Millî Eğitim Bakanlığı",
        "curriculum_model": (
            "Türkiye Yüzyılı Maarif Modeli 2024"
        ),
        "subject": "Biyoloji",
        "grades": [
            9,
            10,
            11,
            12,
        ],
        "source_document": source_name,
        "source_page_count": len(
            pages
        ),
        "total_learning_outcomes": len(
            outcomes
        ),
        "grade_records": grades,
    }


def validate_registry(
    registry,
):
    errors = []

    if registry.get(
        "subject"
    ) != "Biyoloji":
        errors.append(
            "subject must be Biyoloji"
        )

    if registry.get(
        "total_learning_outcomes"
    ) != 78:
        errors.append(
            "expected 78 unique learning outcomes"
        )

    grade_records = {
        item[
            "grade"
        ]: item
        for item in registry.get(
            "grade_records",
            []
        )
    }

    for grade, expected_count in EXPECTED_OUTCOME_COUNTS.items():
        record = grade_records.get(
            grade
        )

        if record is None:
            errors.append(
                f"missing grade {grade}"
            )
            continue

        actual = record.get(
            "learning_outcome_count"
        )

        if actual != expected_count:
            errors.append(
                f"grade {grade}: expected "
                f"{expected_count}, got {actual}"
            )

        theme_names = {
            theme[
                "theme_number"
            ]: theme[
                "theme_name"
            ]
            for theme in record.get(
                "themes",
                []
            )
        }

        if theme_names != EXPECTED_THEMES[
            grade
        ]:
            errors.append(
                f"grade {grade}: theme map mismatch"
            )

        for theme in record.get(
            "themes",
            []
        ):
            if not theme.get(
                "content_framework"
            ):
                errors.append(
                    f"grade {grade} theme "
                    f"{theme['theme_number']}: "
                    "missing content framework"
                )

            for outcome in theme.get(
                "learning_outcomes",
                []
            ):
                if not outcome.get(
                    "title"
                ):
                    errors.append(
                        f"{outcome['id']}: missing title"
                    )

                if outcome.get(
                    "source_page"
                ) is None:
                    errors.append(
                        f"{outcome['id']}: missing source page"
                    )

    return errors


def write_json(
    path,
    data,
):
    path = Path(
        path
    )

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


def print_summary(
    registry,
):
    print("=" * 72)
    print(
        "KNOWLEDGE FACTORY V2 — "
        "PHASE 6A OFFICIAL CURRICULUM REGISTRY"
    )
    print("=" * 72)

    print(
        f"Subject            : "
        f"{registry['subject']}"
    )

    print(
        f"Source pages       : "
        f"{registry['source_page_count']}"
    )

    print(
        f"Learning outcomes  : "
        f"{registry['total_learning_outcomes']}"
    )

    for grade in registry[
        "grade_records"
    ]:
        themes = ", ".join(
            (
                f"{theme['theme_name']}="
                f"{theme['learning_outcome_count']}"
            )
            for theme in grade[
                "themes"
            ]
        )

        print(
            f"Grade {grade['grade']:<2}           : "
            f"{grade['learning_outcome_count']} "
            f"({themes})"
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--pdf",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_OUTPUT
        ),
    )

    args = parser.parse_args()

    pages = read_pdf_text(
        args.pdf
    )

    registry = build_registry(
        pages,
        source_name=Path(
            args.pdf
        ).name,
    )

    errors = validate_registry(
        registry
    )

    if errors:
        print(
            "REGISTRY VALIDATION: FAIL"
        )

        for error in errors:
            print(
                f"  - {error}"
            )

        raise SystemExit(
            2
        )

    write_json(
        args.output,
        registry,
    )

    print_summary(
        registry
    )

    print(
        "REGISTRY VALIDATION: PASS"
    )

    print(
        f"REGISTRY           | {args.output}"
    )


if __name__ == "__main__":
    main()
