"""
Knowledge Factory V2 — Topic -> Official Source Mapping

Backward-compatible mapper for both:
- pre-enrichment corpus pages with title/text metadata
- Phase 5D lexical fingerprint pages with terms/title_terms/heading_terms

This stage only produces source candidates.
It never creates claims and never marks evidence READY.
"""

import argparse
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

QUEUE_PATH = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "work_queue"
    / "evidence_queue.json"
)

LEXICAL_CORPUS_PATH = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "corpus"
    / "official_corpus_lexical_index.json"
)

PLAIN_CORPUS_PATH = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "corpus"
    / "official_corpus_index.json"
)

DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "work_queue"
    / "topic_source_mapping.json"
)

STOPWORDS = {
    "ve",
    "veya",
    "ile",
    "bir",
    "bu",
    "icin",
    "gibi",
    "olan",
    "olarak",
    "konusu",
    "konulari",
    "temel",
    "genel",
}


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


def normalize_text(value):
    value = str(
        value or ""
    )

    value = (
        value.replace("İ", "I")
        .replace("ı", "i")
    )

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(
            char
        )
    )

    return value.casefold()


def tokens(value):
    found = re.findall(
        r"[a-z0-9]+",
        normalize_text(
            value
        ),
    )

    return [
        token
        for token in found
        if (
            len(token) >= 3
            and token not in STOPWORDS
        )
    ]


def normalize_page_terms(value):
    """
    Backward compatibility:
    - str -> tokenize text
    - list/tuple/set -> normalize tokens
    - everything else -> empty set
    """

    if isinstance(
        value,
        str,
    ):
        return set(
            tokens(
                value
            )
        )

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        normalized = set()

        for item in value:
            normalized.update(
                tokens(
                    item
                )
            )

        return normalized

    return set()


def token_overlap_score(
    topic,
    page_terms_value,
):
    topic_tokens = set(
        tokens(
            topic
        )
    )

    if not topic_tokens:
        return 0.0

    page_tokens = normalize_page_terms(
        page_terms_value
    )

    if not page_tokens:
        return 0.0

    matched = (
        topic_tokens
        & page_tokens
    )

    return round(
        len(matched)
        / len(topic_tokens),
        4,
    )


def confidence_label(
    score,
):
    if score >= 0.99:
        return "HIGH"
    if score >= 0.67:
        return "MEDIUM"
    if score > 0:
        return "LOW"
    return "NONE"


def family_lookup(
    corpus_index,
):
    lookup = {}

    for family in corpus_index.get(
        "families",
        [],
    ):
        lookup[
            (
                family.get(
                    "exam"
                ),
                family.get(
                    "subject"
                ),
            )
        ] = family

    return lookup


def page_terms(
    page,
):
    """
    Prefer Phase 5D structured lexical fields.
    Fall back to legacy title/text metadata so old unit tests and
    pre-enrichment corpora remain valid.
    """

    combined = []

    structured_present = False

    for field in (
        "title_terms",
        "heading_terms",
        "terms",
    ):
        values = page.get(
            field
        )

        if isinstance(
            values,
            list,
        ):
            structured_present = True

            for value in values:
                combined.extend(
                    tokens(
                        value
                    )
                )

    if combined:
        return combined

    legacy_parts = [
        page.get(
            "title",
            ""
        ),
        page.get(
            "text",
            ""
        ),
    ]

    legacy_text = " ".join(
        str(part)
        for part in legacy_parts
        if part
    )

    if legacy_text:
        return tokens(
            legacy_text
        )

    return []


def family_has_lexical_enrichment(
    family,
):
    for page in family.get(
        "pages",
        [],
    ):
        if any(
            field in page
            for field in (
                "terms",
                "title_terms",
                "heading_terms",
                "lexical_status",
            )
        ):
            return True

    return False


def rank_candidates(
    topic,
    family,
    limit=5,
):
    scored = []

    for page in family.get(
        "pages",
        [],
    ):
        score = token_overlap_score(
            topic,
            page_terms(
                page
            ),
        )

        scored.append(
            {
                "page": page.get(
                    "page"
                ),
                "url": page.get(
                    "url"
                ),
                "score": score,
                "confidence": confidence_label(
                    score
                ),
            }
        )

    scored.sort(
        key=lambda item: (
            -item[
                "score"
            ],
            item[
                "page"
            ]
            if isinstance(
                item[
                    "page"
                ],
                int,
            )
            else math.inf,
        )
    )

    return scored[
        :limit
    ]


def classify_mapping(
    family,
    candidates,
):
    if family is None:
        return (
            "UNRESOLVED_FAMILY",
            "RESOLVE_OFFICIAL_CORPUS_FAMILY",
        )

    if not candidates:
        return (
            "UNRESOLVED",
            (
                "REVIEW_CORPUS"
                if family_has_lexical_enrichment(
                    family
                )
                else "ENRICH_CORPUS_TEXT"
            ),
        )

    best = candidates[
        0
    ]

    if best[
        "confidence"
    ] == "HIGH":
        return (
            "AUTO_CANDIDATE",
            "REVIEW_AND_INGEST_SOURCE",
        )

    if best[
        "confidence"
    ] in {
        "MEDIUM",
        "LOW",
    }:
        return (
            "REVIEW_REQUIRED",
            "REVIEW_CANDIDATES",
        )

    return (
        "UNRESOLVED",
        (
            "REVIEW_CORPUS"
            if family_has_lexical_enrichment(
                family
            )
            else "ENRICH_CORPUS_TEXT"
        ),
    )


def build_mapping(
    queue,
    corpus_index,
):
    families = family_lookup(
        corpus_index
    )

    mappings = []

    for item in queue.get(
        "items",
        [],
    ):
        family = families.get(
            (
                item.get(
                    "exam"
                ),
                item.get(
                    "subject"
                ),
            )
        )

        if (
            item.get(
                "evidence_status"
            )
            == "READY"
        ):
            mappings.append(
                {
                    "exam": item.get(
                        "exam"
                    ),
                    "subject": item.get(
                        "subject"
                    ),
                    "grade": item.get(
                        "grade"
                    ),
                    "topic": item.get(
                        "topic"
                    ),
                    "evidence_status": "READY",
                    "mapping_status": "ALREADY_READY",
                    "next_action": "NONE",
                    "family_id": (
                        family.get(
                            "family_id"
                        )
                        if family
                        else None
                    ),
                    "candidates": [],
                }
            )
            continue

        candidates = (
            rank_candidates(
                item.get(
                    "topic"
                ),
                family,
            )
            if family
            else []
        )

        (
            mapping_status,
            next_action,
        ) = classify_mapping(
            family,
            candidates,
        )

        mappings.append(
            {
                "exam": item.get(
                    "exam"
                ),
                "subject": item.get(
                    "subject"
                ),
                "grade": item.get(
                    "grade"
                ),
                "topic": item.get(
                    "topic"
                ),
                "evidence_status": item.get(
                    "evidence_status"
                ),
                "mapping_status": mapping_status,
                "next_action": next_action,
                "family_id": (
                    family.get(
                        "family_id"
                    )
                    if family
                    else None
                ),
                "candidates": candidates,
            }
        )

    counts = Counter(
        item[
            "mapping_status"
        ]
        for item in mappings
    )

    return {
        "version": "1.2",
        "kind": "TOPIC_OFFICIAL_SOURCE_MAPPING",
        "corpus_kind": corpus_index.get(
            "kind"
        ),
        "total_topics": len(
            mappings
        ),
        "summary": dict(
            sorted(
                counts.items()
            )
        ),
        "items": mappings,
    }


def print_summary(
    mapping,
):
    print("=" * 70)
    print(
        "KNOWLEDGE FACTORY V2 — "
        "TOPIC SOURCE MAPPING"
    )
    print("=" * 70)

    print(
        f"Total topics       : "
        f"{mapping['total_topics']}"
    )

    for key, value in mapping.get(
        "summary",
        {}
    ).items():
        print(
            f"{key:<18}: {value}"
        )


def resolve_default_corpus_path():
    if LEXICAL_CORPUS_PATH.exists():
        return LEXICAL_CORPUS_PATH

    return PLAIN_CORPUS_PATH


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--queue",
        default=str(
            QUEUE_PATH
        ),
    )

    parser.add_argument(
        "--corpus",
        default=str(
            resolve_default_corpus_path()
        ),
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_OUTPUT_PATH
        ),
    )

    args = parser.parse_args()

    queue = load_json(
        args.queue
    )

    corpus_index = load_json(
        args.corpus
    )

    mapping = build_mapping(
        queue,
        corpus_index,
    )

    write_json(
        args.output,
        mapping,
    )

    print_summary(
        mapping
    )

    print(
        f"MAPPING            | {args.output}"
    )


if __name__ == "__main__":
    main()
