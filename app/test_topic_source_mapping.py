"""
Knowledge Factory V2 — Phase 5C topic-source mapping tests.
"""

import sys
from pathlib import Path


TOOLS = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "tools"
)

if str(TOOLS) not in sys.path:
    sys.path.insert(
        0,
        str(TOOLS),
    )

import build_topic_source_mapping as mapper


def test_turkish_normalization_is_stable():
    assert (
        mapper.normalize_text(
            "İntegral Çözümü"
        )
        == "integral cozumu"
    )


def test_token_overlap_full_match_is_high():
    assert (
        mapper.token_overlap_score(
            "Belirsiz İntegral",
            "Belirsiz integral konu özeti",
        )
        == 1.0
    )


def test_ready_topic_is_not_remapped():
    queue = {
        "items": [
            {
                "exam": "AYT",
                "subject": "Matematik",
                "grade": "12",
                "topic": "İntegral",
                "evidence_status": "READY",
            }
        ]
    }

    corpus = {
        "families": [
            {
                "exam": "AYT",
                "subject": "Matematik",
                "family_id": "F1",
                "pages": [],
            }
        ]
    }

    result = mapper.build_mapping(
        queue,
        corpus,
    )

    item = result["items"][0]

    assert (
        item["mapping_status"]
        == "ALREADY_READY"
    )
    assert (
        item["candidates"]
        == []
    )


def test_missing_family_stays_explicit():
    queue = {
        "items": [
            {
                "exam": "TYT",
                "subject": "Din Kültürü",
                "grade": "12",
                "topic": "İnanç",
                "evidence_status": "MISSING",
            }
        ]
    }

    corpus = {
        "families": []
    }

    result = mapper.build_mapping(
        queue,
        corpus,
    )

    item = result["items"][0]

    assert (
        item["mapping_status"]
        == "UNRESOLVED_FAMILY"
    )


def test_high_confidence_candidate_is_auto_candidate():
    queue = {
        "items": [
            {
                "exam": "AYT",
                "subject": "Matematik",
                "grade": "12",
                "topic": "Belirsiz İntegral",
                "evidence_status": "MISSING",
            }
        ]
    }

    corpus = {
        "families": [
            {
                "exam": "AYT",
                "subject": "Matematik",
                "family_id": "F1",
                "pages": [
                    {
                        "page": 89,
                        "url": "https://ogmmateryal.eba.gov.tr/x/page89.html",
                        "title": "Belirsiz İntegral",
                    }
                ],
            }
        ]
    }

    result = mapper.build_mapping(
        queue,
        corpus,
    )

    item = result["items"][0]

    assert (
        item["mapping_status"]
        == "AUTO_CANDIDATE"
    )
    assert (
        item["candidates"][0][
            "confidence"
        ]
        == "HIGH"
    )


def test_no_text_match_requires_corpus_enrichment():
    queue = {
        "items": [
            {
                "exam": "TYT",
                "subject": "Fizik",
                "grade": "12",
                "topic": "Basınç",
                "evidence_status": "MISSING",
            }
        ]
    }

    corpus = {
        "families": [
            {
                "exam": "TYT",
                "subject": "Fizik",
                "family_id": "F1",
                "pages": [
                    {
                        "page": 1,
                        "url": "https://ogmmateryal.eba.gov.tr/x/page1.html",
                    }
                ],
            }
        ]
    }

    result = mapper.build_mapping(
        queue,
        corpus,
    )

    item = result["items"][0]

    assert (
        item["mapping_status"]
        == "UNRESOLVED"
    )
    assert (
        item["next_action"]
        == "ENRICH_CORPUS_TEXT"
    )
