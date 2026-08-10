"""
Knowledge Factory V2 — Phase 5D tests.
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

import enrich_official_corpus as enrich
import build_topic_source_mapping as mapper


def test_html_fingerprint_does_not_persist_raw_prose():
    html = """
    <html>
      <head><title>Belirsiz İntegral</title></head>
      <body>
        <h1>İntegral Alma Kuralları</h1>
        <p>Bir fonksiyonun ters türevini bulma işlemine integral alma denir.</p>
        <script>secret_should_not_appear</script>
      </body>
    </html>
    """

    result = enrich.html_to_fingerprint(
        html
    )

    assert "terms" in result
    assert "visible_text" not in result
    assert "integral" in result["terms"]
    assert "secret_should_not_appear" not in result["terms"]


def test_enriched_page_is_ready_with_terms():
    page = {
        "page": 89,
        "url": (
            "https://ogmmateryal.eba.gov.tr/"
            "x/page89.html"
        ),
    }

    result = enrich.enrich_page(
        page,
        fetcher=lambda url: (
            "<h1>Belirsiz İntegral</h1>"
            "<p>İntegral alma kuralları</p>"
        ),
    )

    assert (
        result["lexical_status"]
        == "READY"
    )

    assert (
        "integral"
        in result["terms"]
    )


def test_mapper_uses_lexical_terms():
    family = {
        "pages": [
            {
                "page": 89,
                "url": "https://ogmmateryal.eba.gov.tr/x/page89.html",
                "terms": [
                    "belirsiz",
                    "integral",
                    "fonksiyon",
                ],
                "title_terms": [],
                "heading_terms": [],
            }
        ]
    }

    candidates = mapper.rank_candidates(
        "Belirsiz İntegral",
        family,
    )

    assert (
        candidates[0]["score"]
        == 1.0
    )

    assert (
        candidates[0]["confidence"]
        == "HIGH"
    )


def test_mapping_keeps_missing_family_explicit():
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

    assert (
        result["items"][0]["mapping_status"]
        == "UNRESOLVED_FAMILY"
    )
