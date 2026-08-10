"""
Knowledge Factory V2 — Phase 5C Topic -> Official Source Mapping

Purpose:
Map curriculum topics in the evidence work queue to candidate pages from the
official MEB/OGM corpus index.

This phase is deterministic and conservative:
- it does not create claims,
- it does not mark evidence READY,
- it does not guess when confidence is weak,
- it ranks candidate pages only within the same exam+subject corpus family.

The mapping result is a review artifact used by later source ingestion.
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

CORPUS_INDEX_PATH = (
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


def token_overlap_score(
    topic,
    page_text,
):
    """
    Conservative lexical score.

    1.0 means every meaningful topic token appears in the page text.
    Partial overlap scales proportionally. Extra page terms are not penalized
    because official pages are expected to contain more context than a topic name.
    """

    topic_tokens = set(
        tokens(
            topic
        )
    )

    if not topic_tokens:
        return 0.0

    page_tokens = set(
        tokens(
            page_text
        )
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


def confidence_label(score):
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
        key = (
            family.get("exam"),
            family.get("subject"),
        )

        lookup[
            key
        ] = family

    return lookup


def page_search_text(page):
    """
    Phase 5C currently has URL/page-number metadata only.
    Search text therefore uses URL metadata and any future optional title/text
    fields when present. Later phases may enrich pages with extracted text.
    """

    parts = [
        page.get(
            "title",
            ""
        ),
        page.get(
            "text",
            ""
        ),
        page.get(
            "url",
            ""
        ),
        str(
            page.get(
                "page",
                ""
            )
        ),
    ]

    return " ".join(
        str(part)
        for part in parts
        if part is not None
    )


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
            page_search_text(
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
            -item["score"],
            item["page"]
            if isinstance(
                item["page"],
                int,
            )
            else math.inf,
        )
    )

    return scored[
        :limit
    ]


def classify_mapping(
    item,
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
            "REVIEW_CORPUS",
        )

    best = candidates[0]

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
        "ENRICH_CORPUS_TEXT",
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
        key = (
            item.get("exam"),
            item.get("subject"),
        )

        family = families.get(
            key
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
            item,
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
        "version": "1.0",
        "kind": "TOPIC_OFFICIAL_SOURCE_MAPPING",
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


def print_summary(mapping):
    print("=" * 70)
    print(
        "KNOWLEDGE FACTORY V2 — PHASE 5C TOPIC SOURCE MAPPING"
    )
    print("=" * 70)
    print(
        f"Total topics       : {mapping['total_topics']}"
    )

    for key, value in mapping.get(
        "summary",
        {}
    ).items():
        print(
            f"{key:<18}: {value}"
        )


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
            CORPUS_INDEX_PATH
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
